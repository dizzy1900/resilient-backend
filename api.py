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

import io
import os
import subprocess
import json
import asyncio
from typing import Literal, Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd

from io import BytesIO

from physics_engine import calculate_yield
from spatial_engine import process_polygon_request


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


class PolygonRequest(BaseModel):
    """Request for polygon-based Digital Twin risk analysis.
    
    Accepts a GeoJSON Feature or Geometry object representing the area of interest.
    Calculates fractional exposure and scales financial risk accordingly.
    """
    geojson: Dict[str, Any] = Field(..., description="GeoJSON Feature or Geometry object")
    risk_type: str = Field(..., description="Type of risk: flood, coastal, heat, drought, agriculture")
    scenario_year: int = Field(2050, ge=2024, le=2100, description="Future year for projections")
    asset_value_usd: float = Field(5_000_000.0, description="Total asset value in USD")
    
    # Scenario parameters
    flood_depth_m: Optional[float] = Field(None, description="Flood depth in meters")
    slr_m: Optional[float] = Field(None, description="Sea level rise in meters")
    temp_delta: Optional[float] = Field(None, description="Temperature increase in °C")
    damage_factor: float = Field(1.0, ge=0.0, le=1.0, description="Expected damage ratio (0-1)")


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


@app.post("/simulate/polygon")
def run_polygon_simulation(req: PolygonRequest) -> dict:
    """Run polygon-based Digital Twin risk analysis.
    
    This endpoint processes GeoJSON polygons to calculate:
    - Polygon area in square kilometers
    - Fractional exposure to climate risks
    - Scaled financial risk based on exposure
    
    Returns spatial analysis with total_area_sqkm and fractional_exposure_pct.
    """
    try:
        # Build scenario parameters dictionary
        scenario_params = {
            'damage_factor': req.damage_factor
        }
        
        if req.flood_depth_m is not None:
            scenario_params['flood_depth_m'] = req.flood_depth_m
        if req.slr_m is not None:
            scenario_params['slr_m'] = req.slr_m
        if req.temp_delta is not None:
            scenario_params['temp_delta'] = req.temp_delta
        
        # Process the polygon request using spatial_engine
        result = process_polygon_request(
            geojson=req.geojson,
            risk_type=req.risk_type,
            asset_value_usd=req.asset_value_usd,
            scenario_params=scenario_params
        )
        
        # Add metadata
        result['scenario_year'] = req.scenario_year
        result['status'] = 'success'
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid GeoJSON or parameters: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Polygon simulation failed: {str(e)}"
        ) from e


async def process_single_asset(row_data: dict, row_index: int) -> dict:
    """Process a single portfolio asset asynchronously.
    
    Args:
        row_data: Dictionary containing asset data (lat, lon, crop_type, asset_value)
        row_index: Index of the row in the original DataFrame
    
    Returns:
        Dictionary with simulation results or error information
    """
    try:
        # Extract parameters from row
        lat = float(row_data['lat'])
        lon = float(row_data['lon'])
        crop_type = str(row_data['crop_type'])
        asset_value = float(row_data['asset_value'])
        
        # Optional parameters with defaults
        scenario_year = int(row_data.get('scenario_year', 2050))
        temp_delta = float(row_data.get('temp_delta', 0.0))
        rain_pct_change = float(row_data.get('rain_pct_change', 0.0))
        
        # Build command for headless_runner
        cmd = [
            "python",
            "headless_runner.py",
            "--lat", str(lat),
            "--lon", str(lon),
            "--scenario_year", str(scenario_year),
            "--project_type", "agriculture",
            "--crop_type", crop_type,
            "--temp_delta", str(temp_delta),
            "--rain_pct_change", str(rain_pct_change),
        ]
        
        # Override financial parameters with asset value
        env = os.environ.copy()
        env["FINANCIAL_CAPEX"] = str(asset_value)
        env["FINANCIAL_OPEX"] = str(asset_value * 0.1)  # 10% of asset value as annual opex
        env["FINANCIAL_DISCOUNT_RATE"] = "0.10"
        env["FINANCIAL_YEARS"] = "10"
        
        # Run simulation asynchronously
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return {
                "row_index": row_index,
                "status": "error",
                "error": f"Simulation failed: {stderr.decode()}",
                "input": row_data
            }
        
        # Parse simulation output
        result = json.loads(stdout.decode())
        result["row_index"] = row_index
        result["status"] = "success"
        result["input"] = row_data
        
        return result
        
    except json.JSONDecodeError as e:
        return {
            "row_index": row_index,
            "status": "error",
            "error": f"Failed to parse simulation output: {str(e)}",
            "input": row_data
        }
    except (ValueError, KeyError) as e:
        return {
            "row_index": row_index,
            "status": "error",
            "error": f"Invalid row data: {str(e)}",
            "input": row_data
        }
    except Exception as e:
        return {
            "row_index": row_index,
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "input": row_data
        }


@app.post("/api/v1/analyze-portfolio")
async def analyze_portfolio(file: UploadFile = File(...)) -> dict:
    """Analyze a CSV portfolio upload with concurrent processing.
    
    Accepts a CSV file with portfolio data containing the following required columns:
    - lat: Latitude coordinate
    - lon: Longitude coordinate
    - asset_value: Asset value in USD
    - crop_type: Type of crop (e.g., maize, cocoa, rice, soy, wheat)
    
    Optional columns:
    - scenario_year: Future year for projections (default: 2050)
    - temp_delta: Temperature increase in °C (default: 0.0)
    - rain_pct_change: Rainfall change percentage (default: 0.0)
    
    Processes each asset concurrently and returns aggregated results.
    """
    try:
        # Read file contents asynchronously
        contents = await file.read()
        
        # Parse CSV into DataFrame
        df = pd.read_csv(io.BytesIO(contents))
        
        # Strip whitespace and make lowercase for all column names
        df.columns = df.columns.astype(str).str.strip().str.lower()
        # Map the columns dynamically
        lat_col = next((c for c in df.columns if 'lat' in c), 'lat')
        lon_col = next((c for c in df.columns if 'lon' in c or 'lng' in c), 'lon')
        val_col = next((c for c in df.columns if 'val' in c), 'asset_value')
        crop_col = next((c for c in df.columns if 'crop' in c), 'crop_type')
        
        df.dropna(how='all', inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        
        # Validate required columns
        required_columns = [lat_col, lon_col, val_col, crop_col]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. "
                       f"Detected columns: {list(df.columns)}"
            )
        
        # Build records using dynamic column names (bulletproof parsing)
        records = []
        for idx, row in df.iterrows():
            record = {
                "lat": float(row.get(lat_col, 0)),
                "lon": float(row.get(lon_col, 0)),
                "asset_value": float(row.get(val_col, 0)),
                "crop_type": str(row.get(crop_col, "")),
            }
            for col in df.columns:
                if col not in (lat_col, lon_col, val_col, crop_col):
                    record[col] = row.get(col)
            records.append(record)
        
        # Create async tasks for concurrent processing
        tasks = [process_single_asset(row, idx) for idx, row in enumerate(records)]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Separate successful and failed results
        successful = [r for r in results if r.get('status') == 'success']
        failed = [r for r in results if r.get('status') == 'error']
        
        # Calculate portfolio-level aggregates from successful results
        total_portfolio_value = sum(r['input']['asset_value'] for r in results)
        
        # Extract financial and risk metrics from successful simulations
        total_value_at_risk = 0.0
        resilience_scores = []
        total_npv = 0.0
        total_expected_loss = 0.0
        
        for result in successful:
            # Extract VaR from monte carlo simulation (if available)
            monte_carlo = result.get('monte_carlo', {})
            var_95 = monte_carlo.get('var_95', 0.0)
            if var_95:
                total_value_at_risk += abs(float(var_95))
            
            # Extract resilience score (if available)
            resilience_score = result.get('resilience_score')
            if resilience_score is not None:
                try:
                    resilience_scores.append(float(resilience_score))
                except (ValueError, TypeError):
                    pass
            
            # Extract NPV from financial analysis
            financial = result.get('financial', {})
            npv = financial.get('npv_usd', 0.0)
            if npv:
                total_npv += float(npv)
            
            # Extract expected loss from risk analysis
            risk = result.get('risk', {})
            expected_loss = risk.get('expected_loss_usd', 0.0)
            if expected_loss:
                total_expected_loss += float(expected_loss)
        
        # Calculate averages
        average_resilience_score = (
            sum(resilience_scores) / len(resilience_scores)
            if resilience_scores else 0.0
        )
        
        # Structure the final response (no wrapper; return data directly)
        portfolio_summary = {
            "total_assets": len(records),
            "successful_simulations": len(successful),
            "failed_simulations": len(failed),
            "total_portfolio_value_usd": round(float(total_portfolio_value), 2),
            "total_value_at_risk_usd": round(float(total_value_at_risk), 2),
            "average_resilience_score": round(float(average_resilience_score), 2),
            "total_npv_usd": round(float(total_npv), 2),
            "total_expected_loss_usd": round(float(total_expected_loss), 2),
            "risk_exposure_pct": round(
                (total_value_at_risk / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0,
                2
            ),
            "crop_distribution": df[crop_col].value_counts().to_dict()
        }
        return {"portfolio_summary": portfolio_summary, "asset_results": results}
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV file is empty"
        )
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV file: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio analysis failed: {str(e)}"
        ) from e


def main() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
