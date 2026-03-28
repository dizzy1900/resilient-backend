"""Temporal forecast endpoint — wraps time_travel_engine for single-location forecasts."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from time_travel_engine import process_location

router = APIRouter(prefix="/api/v1/forecast", tags=["Forecast"])


class TemporalForecastRequest(BaseModel):
    lat: float
    lon: float
    crop_type: str = "maize"
    project_type: str = "agriculture"
    location_name: str = "Unknown Location"


def _credit_rating(default_prob: float) -> str:
    """Map a default probability (0.0–1.0) to a credit rating."""
    if default_prob < 0.01:
        return "AAA"
    if default_prob < 0.05:
        return "AA"
    if default_prob < 0.10:
        return "A"
    if default_prob < 0.20:
        return "BBB"
    if default_prob < 0.35:
        return "BB"
    if default_prob < 0.50:
        return "B"
    return "C"


@router.post("/temporal")
def temporal_forecast(req: TemporalForecastRequest) -> dict:
    """Run a multi-decade temporal climate forecast for a single location.

    Calls time_travel_engine.process_location across 2030, 2040, and 2050,
    returning NPV trajectory, default probability, credit rating, and
    stranded asset detection.
    """
    try:
        location_dict = {
            "location": {"lat": req.lat, "lon": req.lon},
            "project_type": req.project_type,
            "target": {"name": req.location_name, "crop_type": req.crop_type},
            "crop_analysis": {"crop_type": req.crop_type},
        }

        result = process_location(location_dict)

        temporal = result.get("temporal_analysis", {})
        history = temporal.get("history", [])
        stranded_year = temporal.get("stranded_asset_year")

        if stranded_year and stranded_year <= 2040:
            outlook = "Negative Watch"
        elif not stranded_year:
            outlook = "Stable"
        else:
            outlook = "Monitor"

        return {
            "location_name": req.location_name,
            "project_type": req.project_type,
            "forecast": [
                {
                    "year": item["year"],
                    "npv": item["npv"],
                    "default_probability": item["default_prob"],
                    "credit_rating": _credit_rating(item["default_prob"]),
                }
                for item in history
            ],
            "stranded_asset_year": stranded_year,
            "is_stranded": stranded_year is not None,
            "outlook": outlook,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
