"""OSINT feed endpoint — aggregates live disaster alerts from ReliefWeb
and internal system events into a unified alert stream.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/osint", tags=["OSINT"])

_RELIEFWEB_URL = (
    "https://api.reliefweb.int/v1/disasters"
    "?appname=resilient&profile=list&limit=5&sort[]=date:desc"
)

# Urgency mapping from ReliefWeb disaster status field
_HIGH_URGENCY_STATUSES = {"current", "alert"}

_now = datetime.now(timezone.utc)

_SYSTEM_ALERTS: List[Dict[str, Any]] = [
    {
        "id": "sys-001",
        "source": "System",
        "title": "GEE Model Training Complete — West Africa Cocoa Belt",
        "urgency": "Normal",
        "timestamp": (_now - timedelta(hours=1)).isoformat(),
    },
    {
        "id": "sys-002",
        "source": "System",
        "title": "Sentinel-2 Pass: West Africa — Imagery Updated",
        "urgency": "Normal",
        "timestamp": (_now - timedelta(hours=3)).isoformat(),
    },
    {
        "id": "sys-003",
        "source": "System",
        "title": "Monte Carlo Batch Run Complete — 10,000 Scenarios Processed",
        "urgency": "Normal",
        "timestamp": (_now - timedelta(hours=6)).isoformat(),
    },
]


@router.get("/feed")
async def get_osint_feed() -> List[Dict[str, Any]]:
    """Return a merged feed of live ReliefWeb disaster alerts and internal system events.

    ReliefWeb entries are fetched live; system alerts are static placeholders.
    All entries are sorted by timestamp descending.
    """
    reliefweb_alerts: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(_RELIEFWEB_URL)
            response.raise_for_status()
            payload = response.json()

        for item in payload.get("data", []):
            fields = item.get("fields", {})
            name = fields.get("name", "Unknown Disaster")
            status = fields.get("status", "")

            # ReliefWeb date is nested: fields.date.created
            date_obj = fields.get("date", {})
            raw_date = date_obj.get("created", "") if isinstance(date_obj, dict) else ""

            # Normalise to an ISO timestamp; fall back to epoch so sort still works
            try:
                ts = datetime.fromisoformat(raw_date).isoformat()
            except (ValueError, TypeError):
                ts = datetime(1970, 1, 1, tzinfo=timezone.utc).isoformat()

            reliefweb_alerts.append(
                {
                    "id": f"rw-{item.get('id', 'unknown')}",
                    "source": "ReliefWeb",
                    "title": name,
                    "urgency": "High" if status in _HIGH_URGENCY_STATUSES else "Normal",
                    "timestamp": ts,
                }
            )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ReliefWeb API returned {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach ReliefWeb API: {exc}",
        ) from exc

    combined = reliefweb_alerts + _SYSTEM_ALERTS
    combined.sort(key=lambda x: x["timestamp"], reverse=True)

    return combined
