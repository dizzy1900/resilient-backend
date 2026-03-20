"""Simulation endpoints — headless-runner based."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Dict, Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from models import User
from physics_engine import calculate_yield
from spatial_engine import process_polygon_request
from lifespan_depreciation import (
    coastal_lifespan_penalty,
    flood_lifespan_penalty,
    apply_lifespan_depreciation,
    coastal_has_intervention_rescue,
    flood_has_intervention_rescue,
)

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

CropType = Literal["maize", "cocoa"]


class SimulationRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    crop_type: CropType = Field(..., description="Supported: maize, cocoa")

    # Optional overrides (if omitted, we use simple fallback values)
    temp_c: Optional[float] = Field(None, description="Temperature (°C)")
    rain_mm: Optional[float] = Field(None, description="Rainfall (mm)")

    # Physics-engine knobs
    seed_type: int = Field(0, ge=0, le=1, description="0=standard, 1=resilient")
    temp_delta: float = 0.0
    rain_pct_change: float = 0.0


class CoastalRequest(BaseModel):
    """Request for coastal flood risk simulation."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    scenario_year: int = Field(2050, ge=2024, le=2100)
    slr_projection: float = Field(0.0, description="Sea level rise in meters")
    mangrove_width: float = Field(0.0, description="Mangrove buffer width in meters")
    initial_lifespan_years: int = Field(30, ge=1, le=200, description="Asset initial lifespan for depreciation (default 30)")
    intervention: Optional[str] = Field("", description="e.g. 'Sea Wall' for 80% lifespan penalty reduction")
    daily_revenue: float = Field(0.0, description="Daily revenue (USD) for business interruption")
    expected_downtime_days: int = Field(0, ge=0, description="Expected infrastructure downtime days without intervention")


class FloodRequest(BaseModel):
    """Request for flash flood risk simulation."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    scenario_year: int = Field(2050, ge=2024, le=2100)
    rain_intensity: float = Field(0.0, description="Rainfall intensity increase percentage")
    initial_lifespan_years: int = Field(30, ge=1, le=200, description="Asset initial lifespan for depreciation (default 30)")
    global_warming: float = Field(0.0, description="Global warming in °C for lifespan penalty (e.g. 1.5, 2.0)")
    intervention_type: Optional[str] = Field("", description="e.g. 'sponge_city' for 80% lifespan penalty reduction")
    daily_revenue: float = Field(0.0, description="Daily revenue (USD) for business interruption")
    expected_downtime_days: int = Field(0, ge=0, description="Expected infrastructure downtime days without intervention")


class PolygonRequest(BaseModel):
    """Request for polygon-based Digital Twin risk analysis."""
    geojson: Dict[str, Any] = Field(..., description="GeoJSON Feature or Geometry object")
    risk_type: str = Field(..., description="Type of risk: flood, coastal, heat, drought, agriculture")
    scenario_year: int = Field(2050, ge=2024, le=2100, description="Future year for projections")
    asset_value_usd: float = Field(5_000_000.0, description="Total asset value in USD")
    flood_depth_m: Optional[float] = Field(None, description="Flood depth in meters")
    slr_m: Optional[float] = Field(None, description="Sea level rise in meters")
    temp_delta: Optional[float] = Field(None, description="Temperature increase in °C")
    damage_factor: float = Field(1.0, ge=0.0, le=1.0, description="Expected damage ratio (0-1)")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/run")
def run_simulation(req: SimulationRequest, user: User = Depends(get_current_user)) -> dict:
    """Run a single yield simulation."""
    try:
        temp_c = 30.0 if req.temp_c is None else float(req.temp_c)
        rain_mm = 1000.0 if req.rain_mm is None else float(req.rain_mm)

        yield_pct = calculate_yield(
            temp=temp_c,
            rain=rain_mm,
            seed_type=int(req.seed_type),
            crop_type=req.crop_type,
            temp_delta=float(req.temp_delta),
            rain_pct_change=float(req.rain_pct_change),
        )

        return {
            "status": "success",
            "location": {"lat": req.lat, "lon": req.lon},
            "crop_type": req.crop_type,
            "yield_projection": round(float(yield_pct), 2),
            "risk_score": "High" if yield_pct < 50 else "Low",
            "deal_ticket": {
                "principal": 2000,
                "rating": "BBB" if yield_pct > 70 else "B",
            },
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/coastal")
def run_coastal_simulation(req: CoastalRequest) -> dict:
    """Run coastal flood risk simulation. Includes dynamic asset depreciation from SLR and intervention."""
    try:
        cmd = [
            "python",
            "headless_runner.py",
            "--lat", str(req.lat),
            "--lon", str(req.lon),
            "--scenario_year", str(req.scenario_year),
            "--project_type", "coastal",
            "--slr_projection", str(req.slr_projection),
            "--mangrove_width", str(req.mangrove_width),
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Simulation failed: {result.stderr}")

        output = json.loads(result.stdout)
        raw_penalty = coastal_lifespan_penalty(req.slr_projection)
        has_rescue = coastal_has_intervention_rescue(req.intervention or "")
        adjusted_lifespan, lifespan_penalty = apply_lifespan_depreciation(
            req.initial_lifespan_years, raw_penalty, has_rescue
        )
        output["asset_depreciation"] = {
            "adjusted_lifespan": adjusted_lifespan,
            "lifespan_penalty": lifespan_penalty,
        }
        return output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/flood")
def run_flood_simulation(req: FloodRequest) -> dict:
    """Run flash flood risk simulation. Includes dynamic asset depreciation from global warming and intervention."""
    try:
        cmd = [
            "python",
            "headless_runner.py",
            "--lat", str(req.lat),
            "--lon", str(req.lon),
            "--scenario_year", str(req.scenario_year),
            "--project_type", "flood",
            "--rain_intensity", str(req.rain_intensity),
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Simulation failed: {result.stderr}")

        output = json.loads(result.stdout)
        raw_penalty = flood_lifespan_penalty(req.global_warming)
        has_rescue = flood_has_intervention_rescue(req.intervention_type or "")
        adjusted_lifespan, lifespan_penalty = apply_lifespan_depreciation(
            req.initial_lifespan_years, raw_penalty, has_rescue
        )
        output["asset_depreciation"] = {
            "adjusted_lifespan": adjusted_lifespan,
            "lifespan_penalty": lifespan_penalty,
        }
        return output

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/polygon")
def run_polygon_simulation(req: PolygonRequest) -> dict:
    """Run polygon-based Digital Twin risk analysis."""
    try:
        scenario_params = {'damage_factor': req.damage_factor}
        if req.flood_depth_m is not None:
            scenario_params['flood_depth_m'] = req.flood_depth_m
        if req.slr_m is not None:
            scenario_params['slr_m'] = req.slr_m
        if req.temp_delta is not None:
            scenario_params['temp_delta'] = req.temp_delta

        result = process_polygon_request(
            geojson=req.geojson,
            risk_type=req.risk_type,
            asset_value_usd=req.asset_value_usd,
            scenario_params=scenario_params
        )
        result['scenario_year'] = req.scenario_year
        result['status'] = 'success'
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid GeoJSON or parameters: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Polygon simulation failed: {str(e)}") from e
