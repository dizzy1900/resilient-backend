"""Macro endpoints — sovereign climate risk via GEE."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Any, List

import ee
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from gee_credentials import load_gee_credentials

router = APIRouter(prefix="/api/v1/macro", tags=["Macro"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class SovereignRiskCountry(BaseModel):
    country_code: str = Field(..., min_length=3, max_length=3)
    country_name: str
    risk_score: int = Field(..., ge=0, le=100)
    primary_vulnerability: str


class SovereignRiskResponse(BaseModel):
    countries: List[SovereignRiskCountry]


# ---------------------------------------------------------------------------
# In-Memory Cache (24-hour expiration)
# ---------------------------------------------------------------------------

_SOVEREIGN_RISK_CACHE: Dict[str, Any] = {
    "data": None,
    "timestamp": None,
    "ttl_hours": 24,
}


# ---------------------------------------------------------------------------
# GEE helpers
# ---------------------------------------------------------------------------


def _authenticate_gee_sovereign():
    credentials_dict = load_gee_credentials()
    if not credentials_dict:
        raise ValueError("Google Earth Engine credentials not found")
    credentials_json = json.dumps(credentials_dict)
    credentials = ee.ServiceAccountCredentials(credentials_dict["client_email"], key_data=credentials_json)
    ee.Initialize(credentials)


def _map_fao_to_iso(fao_code: int, country_name: str) -> str:
    fao_to_iso = {
        1: "AFG", 2: "ALB", 4: "DZA", 7: "AGO", 10: "ARG", 11: "ARM", 12: "AUS",
        14: "AUT", 16: "BGD", 19: "BLR", 20: "BEL", 23: "BOL", 25: "BRA",
        31: "KHM", 32: "CMR", 33: "CAN", 39: "TCD", 40: "CHL", 41: "CHN",
        44: "COL", 49: "COD", 53: "CRI", 55: "HRV", 56: "CUB", 59: "CZE",
        60: "DNK", 63: "ECU", 65: "EGY", 68: "ETH", 73: "FIN", 75: "FRA",
        79: "DEU", 82: "GHA", 84: "GRC", 90: "HND", 91: "HUN", 93: "IND",
        94: "IDN", 95: "IRN", 96: "IRQ", 97: "IRL", 98: "ISR", 99: "ITA",
        101: "JAM", 102: "JPN", 103: "JOR", 106: "KEN", 110: "KOR", 115: "LBN",
        122: "MYS", 133: "MEX", 143: "MAR", 144: "MOZ", 145: "MMR", 147: "NPL",
        149: "NLD", 153: "NZL", 155: "NGA", 162: "NOR", 165: "PAK", 170: "PER",
        171: "PHL", 173: "POL", 174: "PRT", 177: "ROU", 178: "RUS", 183: "SAU",
        189: "SGP", 197: "ZAF", 203: "ESP", 206: "SDN", 209: "SWE", 210: "CHE",
        211: "SYR", 217: "THA", 222: "TUR", 226: "UGA", 230: "UKR", 231: "ARE",
        232: "GBR", 236: "USA", 238: "VEN", 240: "VNM", 245: "YEM", 246: "ZMB",
        247: "ZWE",
    }
    if fao_code in fao_to_iso:
        return fao_to_iso[fao_code]
    return country_name[:3].upper().replace(" ", "")


def calculate_global_sovereign_risk() -> List[Dict[str, Any]]:
    """Calculate climate risk scores for all countries using GEE."""
    if _SOVEREIGN_RISK_CACHE["data"] is not None and _SOVEREIGN_RISK_CACHE["timestamp"] is not None:
        cache_age_hours = (datetime.now() - _SOVEREIGN_RISK_CACHE["timestamp"]).total_seconds() / 3600
        if cache_age_hours < _SOVEREIGN_RISK_CACHE["ttl_hours"]:
            print(f"[Sovereign Risk] Using cached data (age: {cache_age_hours:.1f} hours)")
            return _SOVEREIGN_RISK_CACHE["data"]

    print("[Sovereign Risk] Computing fresh global risk scores via GEE...")

    try:
        _authenticate_gee_sovereign()

        countries = ee.FeatureCollection("FAO/GAUL/2015/level0")
        flood_hazard = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")

        country_stats = flood_hazard.reduceRegions(
            collection=countries,
            reducer=ee.Reducer.mean(),
            scale=50000,
            crs="EPSG:4326",
        )

        features = country_stats.getInfo()["features"]

        country_risk_data: List[Dict[str, Any]] = []

        for feature in features:
            props = feature["properties"]
            country_name = props.get("ADM0_NAME", "Unknown")
            country_code = props.get("ADM0_CODE")

            if not country_code:
                continue

            flood_occurrence = props.get("mean", 0)
            if flood_occurrence is None:
                flood_occurrence = 0

            risk_score = min(100, int(flood_occurrence * 1.5 + 20))

            if risk_score >= 70:
                primary_vulnerability = "Coastal Flooding"
            elif risk_score >= 50:
                primary_vulnerability = "Riverine Flooding"
            elif risk_score >= 30:
                primary_vulnerability = "Agricultural Yield"
            else:
                primary_vulnerability = "Extreme Heat"

            iso_code = _map_fao_to_iso(country_code, country_name)

            country_risk_data.append({
                "country_code": iso_code,
                "country_name": country_name,
                "risk_score": risk_score,
                "primary_vulnerability": primary_vulnerability,
            })

        country_risk_data.sort(key=lambda x: x["risk_score"], reverse=True)

        _SOVEREIGN_RISK_CACHE["data"] = country_risk_data
        _SOVEREIGN_RISK_CACHE["timestamp"] = datetime.now()

        print(f"[Sovereign Risk] Computed risk for {len(country_risk_data)} countries")
        return country_risk_data

    except Exception as e:
        print(f"[Sovereign Risk] GEE computation failed: {e}")
        raise


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/sovereign-risk", response_model=SovereignRiskResponse)
def get_sovereign_risk() -> dict:
    """Get global sovereign climate risk scores for 3D globe visualization."""
    try:
        country_data = calculate_global_sovereign_risk()
        return {"countries": country_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sovereign risk calculation failed: {str(e)}") from e
