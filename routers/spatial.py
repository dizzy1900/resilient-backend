"""Spatial endpoints — NDVI time-series and climate timelapse tiles."""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from typing import Dict

import ee
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from gee_connector import get_ndvi_timeseries
from gee_credentials import load_gee_credentials

router = APIRouter(tags=["Spatial"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TimelapseResponse(BaseModel):
    hazard: str
    layers: Dict[str, str]


# ---------------------------------------------------------------------------
# NDVI mock fallback
# ---------------------------------------------------------------------------


def _ndvi_mock_series() -> list[dict]:
    base = [0.32, 0.35, 0.42, 0.55, 0.68, 0.74, 0.76, 0.72, 0.63, 0.50, 0.38, 0.33]
    now = datetime.now()
    return [
        {"month": f"{(now - timedelta(days=30 * (12 - i))).strftime('%Y-%m')}", "value": round(v + random.uniform(-0.02, 0.02), 4)}
        for i, v in enumerate(base)
    ]


# ---------------------------------------------------------------------------
# Timelapse cache + GEE helpers
# ---------------------------------------------------------------------------

_TIMELAPSE_CACHE: Dict[str, dict] = {}


def _authenticate_gee_timelapse():
    credentials_dict = load_gee_credentials()
    if not credentials_dict:
        raise ValueError("Google Earth Engine credentials not found")
    credentials_json = json.dumps(credentials_dict)
    credentials = ee.ServiceAccountCredentials(credentials_dict["client_email"], key_data=credentials_json)
    ee.Initialize(credentials)


def calculate_climate_timelapse(hazard_type: str) -> Dict[str, str]:
    """Generate Mapbox-compatible XYZ tile URLs for climate projections."""
    cache_key = hazard_type
    if cache_key in _TIMELAPSE_CACHE:
        cached = _TIMELAPSE_CACHE[cache_key]
        cache_age_hours = (datetime.now() - cached["timestamp"]).total_seconds() / 3600
        if cache_age_hours < 24:
            print(f"[Timelapse {hazard_type}] Using cached data (age: {cache_age_hours:.1f} hours)")
            return cached["data"]

    print(f"[Timelapse {hazard_type}] Computing fresh tile URLs via GEE...")

    try:
        _authenticate_gee_timelapse()

        PROJECTION_YEARS = [2026, 2030, 2040, 2050]

        if hazard_type == "heat":
            baseline_year = 2020
            baseline_temp = (
                ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY")
                .filterDate(f"{baseline_year}-01-01", f"{baseline_year}-12-31")
                .select("temperature_2m")
                .mean()
                .subtract(273.15)
            )
            vis_params = {"min": 28, "max": 45, "palette": ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"]}

            layers = {}
            for year in PROJECTION_YEARS:
                warming_offset = (year - baseline_year) * 0.2
                projected_temp = baseline_temp.add(warming_offset)
                masked_temp = projected_temp.updateMask(projected_temp.gte(vis_params["min"]))
                map_id = masked_temp.getMapId(vis_params)
                tile_url = map_id["tile_fetcher"].url_format
                layers[str(year)] = tile_url
                print(f"[Timelapse heat] Generated masked tile URL for {year}")

        elif hazard_type == "flood":
            base_flood = ee.Image("JRC/GSW1_4/GlobalSurfaceWater").select("occurrence")
            vis_params = {"min": 10, "max": 100, "palette": ["#c6dbef", "#6baed6", "#2171b5", "#08519c", "#08306b"]}

            layers = {}
            for year in PROJECTION_YEARS:
                flood_increase = (year - 2020) * 1.0
                projected_flood = base_flood.add(flood_increase).clamp(0, 100)
                masked_flood = projected_flood.updateMask(projected_flood.gte(vis_params["min"]))
                map_id = masked_flood.getMapId(vis_params)
                tile_url = map_id["tile_fetcher"].url_format
                layers[str(year)] = tile_url
                print(f"[Timelapse flood] Generated masked tile URL for {year}")

        else:
            raise ValueError(f"Unsupported hazard type: {hazard_type}. Supported: 'heat', 'flood'")

        _TIMELAPSE_CACHE[cache_key] = {"data": layers, "timestamp": datetime.now()}
        print(f"[Timelapse {hazard_type}] Generated {len(layers)} tile layers")
        return layers

    except Exception as e:
        print(f"[Timelapse {hazard_type}] GEE computation failed: {e}")
        raise


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/api/v1/eo/ndvi")
def eo_ndvi(lat: float, lon: float):
    """Return a 12-month NDVI time-series from MODIS via Google Earth Engine."""
    try:
        series = get_ndvi_timeseries(lat, lon)
        return {"status": "success", "source": "gee", "data": series}
    except Exception as exc:
        print(f"[EO/NDVI] GEE request failed for lat={lat}, lon={lon}: {exc}", flush=True)
        return JSONResponse(
            status_code=500,
            content={"status": "fallback", "message": "GEE unavailable – returning mock NDVI data", "source": "mock", "data": _ndvi_mock_series()},
        )


@router.get("/api/v1/spatial/timelapse/{hazard_type}", response_model=TimelapseResponse)
def get_climate_timelapse(hazard_type: str) -> dict:
    """Get global climate projection tile URLs for time-lapse visualization."""
    try:
        valid_hazards = ["heat", "flood"]
        if hazard_type not in valid_hazards:
            raise HTTPException(status_code=400, detail=f"Invalid hazard type: {hazard_type}. Supported: {', '.join(valid_hazards)}")

        tile_layers = calculate_climate_timelapse(hazard_type)
        return {"hazard": hazard_type, "layers": tile_layers}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Climate timelapse calculation failed: {str(e)}") from e
