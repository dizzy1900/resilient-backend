#!/usr/bin/env python3
"""FastAPI Simulation Service

This is a standalone API entrypoint (separate from the legacy Flask app in
`main.py`). It exposes a minimal /simulate endpoint for yield projections.

Run locally:
  uvicorn api:app --reload --port 8000

Or:
  python api.py
"""

from __future__ import annotations

import os
import subprocess
import json
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from physics_engine import calculate_yield


CropType = Literal["maize", "cocoa"]


class FinancialOverrides(BaseModel):
    """Optional financial parameters for ROI calculations."""
    capex_budget: float = Field(2000.0, description="Initial capital expenditure in USD")
    opex_annual: float = Field(425.0, description="Annual operating expenses in USD")
    discount_rate_pct: float = Field(10.0, description="Discount rate as percentage")
    asset_lifespan_years: int = Field(10, ge=1, le=50, description="Asset lifespan in years")


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


class AgricultureRequest(BaseModel):
    """Request for agriculture simulation with financial overrides."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    scenario_year: int = Field(2050, ge=2024, le=2100, description="Future year for projections")
    crop_type: str = Field("maize", description="Crop type: maize, cocoa, rice, soy, wheat")
    temp_delta: float = Field(0.0, description="Temperature increase in °C")
    rain_pct_change: float = Field(0.0, description="Rainfall change as percentage")
    financial_overrides: Optional[FinancialOverrides] = Field(None, description="Custom financial parameters")


class CoastalRequest(BaseModel):
    """Request for coastal flood risk simulation."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    scenario_year: int = Field(2050, ge=2024, le=2100)
    slr_projection: float = Field(0.0, description="Sea level rise in meters")
    mangrove_width: float = Field(0.0, description="Mangrove buffer width in meters")


class FloodRequest(BaseModel):
    """Request for flash flood risk simulation."""
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    scenario_year: int = Field(2050, ge=2024, le=2100)
    rain_intensity: float = Field(0.0, description="Rainfall intensity increase percentage")


app = FastAPI(title="AdaptMetric Simulation API", version="0.1.0")

# Match the permissive CORS behavior of the Flask app.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/simulate")
def run_simulation(req: SimulationRequest) -> dict:
    """Run a single yield simulation.

    Weather retrieval is intentionally simplified for now (fallback values) so the
    endpoint remains fast and credential-free.
    """

    try:
        # Fallback weather inputs (replace with GEE / real historical lookup later).
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
        # e.g. unsupported crop_type (defensive)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/simulate/agriculture")
def run_agriculture_simulation(req: AgricultureRequest) -> dict:
    """Run agriculture simulation with optional financial overrides.
    
    This endpoint calls the headless_runner with custom financial parameters
    and returns the complete analysis including NPV and ROI calculations.
    """
    try:
        # Build command for headless_runner
        cmd = [
            "python",
            "headless_runner.py",
            "--lat", str(req.lat),
            "--lon", str(req.lon),
            "--scenario_year", str(req.scenario_year),
            "--project_type", "agriculture",
            "--crop_type", req.crop_type,
            "--temp_delta", str(req.temp_delta),
            "--rain_pct_change", str(req.rain_pct_change),
        ]
        
        # Add financial overrides as environment variables
        env = os.environ.copy()
        if req.financial_overrides:
            env["FINANCIAL_CAPEX"] = str(req.financial_overrides.capex_budget)
            env["FINANCIAL_OPEX"] = str(req.financial_overrides.opex_annual)
            env["FINANCIAL_DISCOUNT_RATE"] = str(req.financial_overrides.discount_rate_pct / 100.0)
            env["FINANCIAL_YEARS"] = str(req.financial_overrides.asset_lifespan_years)
        
        # Run the headless_runner
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Simulation failed: {result.stderr}"
            )
        
        # Parse the JSON output
        output = json.loads(result.stdout)
        return output
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse simulation output: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/simulate/coastal")
def run_coastal_simulation(req: CoastalRequest) -> dict:
    """Run coastal flood risk simulation."""
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
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Simulation failed: {result.stderr}"
            )
        
        output = json.loads(result.stdout)
        return output
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/simulate/flood")
def run_flood_simulation(req: FloodRequest) -> dict:
    """Run flash flood risk simulation."""
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
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Simulation failed: {result.stderr}"
            )
        
        output = json.loads(result.stdout)
        return output
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


def main() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
