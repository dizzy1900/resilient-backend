"""General prediction endpoints — ML model inference, hazard lookup, portfolio, batch."""

from __future__ import annotations

import pickle
import random
import statistics
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import joblib
import numpy as np
from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from auth import get_current_user
from models import User
from physics_engine import calculate_yield, calculate_volatility
from financial_engine import calculate_npv, calculate_payback_period
from gee_connector import (
    get_weather_data, get_monthly_data, analyze_spatial_viability, get_terrain_data,
)
from batch_processor import run_batch_job
from routers._shared import legacy_error

router = APIRouter(prefix="/api/v1/prediction", tags=["Prediction"])

# ---------------------------------------------------------------------------
# In-process ML models
# ---------------------------------------------------------------------------

_AG_MODEL_PATH = "ag_surrogate.pkl"
_COFFEE_MODEL_PATH = "coffee_model.pkl"

ag_pkl_model = None
coffee_pkl_model = None

try:
    with open(_AG_MODEL_PATH, "rb") as _f:
        ag_pkl_model = pickle.load(_f)
    print(f"Model loaded successfully from {_AG_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Model file '{_AG_MODEL_PATH}' not found.")
except Exception as _e:
    print(f"Warning: Failed to load model: {_e}")

try:
    coffee_pkl_model = joblib.load(_COFFEE_MODEL_PATH)
    print(f"Coffee model loaded successfully from {_COFFEE_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Coffee model file '{_COFFEE_MODEL_PATH}' not found.")
except Exception as _e:
    print(f"Warning: Failed to load coffee model: {_e}")

SEED_TYPES = {"standard": 0, "resilient": 1}

FALLBACK_WEATHER = {
    "max_temp_celsius": 28.5,
    "total_rain_mm": 520.0,
    "period": "last_12_months",
}

FALLBACK_TERRAIN = {
    "elevation_m": 500.0,
    "soil_ph": 6.5,
}

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class GetHazardRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class PredictRequest(BaseModel):
    """Crop yield prediction — accepts (lat, lon) for GEE lookup OR (temp, rain) for manual mode."""
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    temp: Optional[float] = None
    rain: Optional[float] = None
    crop_type: str = "maize"
    temp_increase: float = 0.0
    rain_change: float = 0.0
    elevation: Optional[float] = None
    elevation_m: Optional[float] = None
    soil_ph: Optional[float] = None
    project_params: Optional[Dict[str, Any]] = None


class PredictPortfolioLocation(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class PredictPortfolioRequest(BaseModel):
    locations: List[PredictPortfolioLocation] = Field(..., min_length=1)
    crop_type: str = "maize"


class StartBatchRequest(BaseModel):
    job_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/get-hazard")
async def get_hazard(req: GetHazardRequest):
    """Get climate hazard data for a location using GEE."""
    try:
        lat = req.lat
        lon = req.lon

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        try:
            weather_data = await run_in_threadpool(
                get_weather_data,
                lat=lat, lon=lon,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )
            hazard_metrics = {
                "max_temp_celsius": weather_data["max_temp_celsius"],
                "total_rain_mm": weather_data["total_precip_mm"],
                "period": "growing_season_peak",
            }
        except Exception as gee_error:
            print(f"GEE error, using fallback: {gee_error}", file=sys.stderr, flush=True)
            hazard_metrics = FALLBACK_WEATHER.copy()

        try:
            terrain_data = await run_in_threadpool(get_terrain_data, lat=lat, lon=lon)
            hazard_metrics["elevation_m"] = terrain_data["elevation_m"]
            hazard_metrics["soil_ph"] = terrain_data["soil_ph"]
        except Exception as terrain_error:
            print(f"Terrain data error, using fallback: {terrain_error}", file=sys.stderr, flush=True)
            hazard_metrics["elevation_m"] = FALLBACK_TERRAIN["elevation_m"]
            hazard_metrics["soil_ph"] = FALLBACK_TERRAIN["soil_ph"]

        return {
            "status": "success",
            "data": {
                "location": {"lat": lat, "lon": lon},
                "hazard_metrics": hazard_metrics,
            },
        }

    except ValueError:
        return legacy_error(400, "Invalid numeric values for lat/lon", "INVALID_NUMERIC_VALUE")


@router.post("/predict")
async def predict(req: PredictRequest, user: User = Depends(get_current_user)):
    """Predict crop yield and calculate avoided loss."""
    try:
        crop_type = req.crop_type.lower()

        if crop_type not in ("maize", "cocoa", "coffee"):
            return legacy_error(400, f"Unsupported crop_type: {crop_type}. Supported crops: 'maize', 'cocoa', 'coffee'", "INVALID_CROP_TYPE")

        if crop_type == "coffee" and coffee_pkl_model is None:
            return legacy_error(500, "Coffee model file not found. Ensure coffee_model.pkl exists.", "MODEL_NOT_FOUND")

        monthly_data = None
        has_location = False
        location_lat = 0.0
        location_lon = 0.0

        if req.lat is not None and req.lon is not None:
            lat = float(req.lat)
            lon = float(req.lon)

            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                weather_data = await run_in_threadpool(get_weather_data, lat=lat, lon=lon, start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))
                base_temp = weather_data["max_temp_celsius"]
                base_rain = weather_data["total_precip_mm"]
                data_source = "gee_auto_lookup"

                try:
                    monthly_data = await run_in_threadpool(get_monthly_data, lat, lon)
                except Exception as monthly_error:
                    print(f"Monthly data error: {monthly_error}", file=sys.stderr, flush=True)

                has_location = True
                location_lat = lat
                location_lon = lon

            except Exception as gee_error:
                print(f"GEE error, using fallback: {gee_error}", file=sys.stderr, flush=True)
                base_temp = FALLBACK_WEATHER["max_temp_celsius"]
                base_rain = FALLBACK_WEATHER["total_rain_mm"]
                data_source = "fallback"

        elif req.temp is not None and req.rain is not None:
            base_temp = float(req.temp)
            base_rain = float(req.rain)
            data_source = "manual"
        else:
            return legacy_error(400, "Missing required fields: provide either (lat, lon) or (temp, rain)", "MISSING_FIELDS")

        temp_increase = float(req.temp_increase)
        rain_change = float(req.rain_change)
        final_simulated_temp = base_temp + temp_increase
        rain_modifier = 1.0 + (rain_change / 100.0)
        final_simulated_rain = max(0.0, base_rain * rain_modifier)

        # === COFFEE MODEL PREDICTION ===
        if crop_type == "coffee":
            elevation = float(req.elevation if req.elevation is not None else (req.elevation_m if req.elevation_m is not None else 1200.0))
            soil_ph = float(req.soil_ph if req.soil_ph is not None else 6.0)

            if has_location and req.elevation is None and req.elevation_m is None:
                try:
                    terrain_data = await run_in_threadpool(get_terrain_data, lat=location_lat, lon=location_lon)
                    elevation = terrain_data["elevation_m"] if terrain_data["elevation_m"] else 1200.0
                    soil_ph = terrain_data["soil_ph"] if terrain_data["soil_ph"] else 6.0
                except Exception as terrain_error:
                    print(f"Terrain fetch error for coffee prediction: {terrain_error}", file=sys.stderr, flush=True)

            baseline_temp_c = base_temp
            temp_anomaly_c = temp_increase
            rainfall_mm = base_rain
            rain_anomaly_mm = (rain_change / 100.0) * base_rain

            features = np.array([[baseline_temp_c, temp_anomaly_c, rainfall_mm, rain_anomaly_mm, elevation, soil_ph]])
            yield_impact = float(coffee_pkl_model.predict(features)[0])

            return {
                "status": "success",
                "data": {
                    "input_conditions": {
                        "baseline_temp_c": round(baseline_temp_c, 2), "temp_anomaly_c": round(temp_anomaly_c, 2),
                        "rainfall_mm": round(rainfall_mm, 2), "rain_anomaly_mm": round(rain_anomaly_mm, 2),
                        "elevation_m": round(elevation, 2), "soil_ph": round(soil_ph, 2),
                        "data_source": data_source, "crop_type": crop_type,
                    },
                    "prediction": {
                        "yield_impact_pct": round(yield_impact, 4),
                        "yield_impact_category": (
                            "optimal" if yield_impact >= 0.8 else "good" if yield_impact >= 0.6 else
                            "moderate" if yield_impact >= 0.4 else "poor" if yield_impact >= 0.2 else "critical"
                        ),
                    },
                    "interpretation": {
                        "description": f"Under current conditions, expected yield is {yield_impact * 100:.1f}% of maximum potential.",
                        "risk_factors": [],
                    },
                },
            }

        # === MAIZE/COCOA PREDICTION ===
        standard_yield = calculate_yield(temp=base_temp, rain=base_rain, seed_type=SEED_TYPES["standard"], crop_type=crop_type, temp_delta=temp_increase, rain_pct_change=rain_change)
        resilient_yield = calculate_yield(temp=base_temp, rain=base_rain, seed_type=SEED_TYPES["resilient"], crop_type=crop_type, temp_delta=temp_increase, rain_pct_change=rain_change)

        avoided_loss = resilient_yield - standard_yield
        percentage_improvement = (avoided_loss / standard_yield) * 100 if standard_yield > 0 else 0.0

        project_params = req.project_params or {}
        capex = float(project_params.get("capex", 2000))
        opex = float(project_params.get("opex", 425))
        yield_benefit_pct = float(project_params.get("yield_benefit_pct", 30.0))
        price_per_ton = float(project_params.get("price_per_ton", 4800))
        analysis_years = 10
        discount_rate = 0.10

        predicted_yield_tons = standard_yield
        incremental_cash_flows: list[float] = []
        cumulative_cash_flow_array: list[float] = []
        cumulative = 0.0

        for year in range(analysis_years + 1):
            revenue_bau = predicted_yield_tons * price_per_ton
            yield_project = resilient_yield * (1 + (yield_benefit_pct / 100))
            revenue_project = yield_project * price_per_ton
            cost_project = capex if year == 0 else opex
            net_project = revenue_project - cost_project
            incremental = -capex if year == 0 else (net_project - revenue_bau)
            incremental_cash_flows.append(round(incremental, 2))
            cumulative += incremental
            cumulative_cash_flow_array.append(round(cumulative, 2))

        npv = calculate_npv(incremental_cash_flows, discount_rate)
        payback_years = calculate_payback_period(incremental_cash_flows)

        roi_analysis = {
            "npv": round(npv, 2),
            "payback_years": round(payback_years, 2) if payback_years is not None else None,
            "cumulative_cash_flow": cumulative_cash_flow_array,
            "incremental_cash_flows": incremental_cash_flows,
            "assumptions": {"capex": capex, "opex": opex, "yield_benefit_pct": yield_benefit_pct, "price_per_ton": price_per_ton, "discount_rate_pct": discount_rate * 100, "analysis_years": analysis_years},
        }

        spatial_analysis = None
        if has_location and temp_increase != 0.0:
            try:
                print(f"[SPATIAL] Running spatial analysis for lat={location_lat}, lon={location_lon}, temp_increase={temp_increase}", file=sys.stderr, flush=True)
                spatial_analysis = await run_in_threadpool(analyze_spatial_viability, location_lat, location_lon, temp_increase)
            except Exception as spatial_error:
                print(f"Spatial analysis error: {spatial_error}", file=sys.stderr, flush=True)

        chart_data = None
        if monthly_data is not None:
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            rainfall_baseline = monthly_data["rainfall_monthly_mm"]
            soil_moisture_baseline = monthly_data["soil_moisture_monthly"]
            rainfall_projected = []
            for i, baseline_value in enumerate(rainfall_baseline):
                projected_value = baseline_value * (1 + rain_change / 100)
                if rain_change < 0 and i in (5, 6, 7):
                    additional_penalty = abs(rain_change) / 100
                    projected_value = projected_value * (1 - additional_penalty)
                rainfall_projected.append(round(projected_value, 2))
            chart_data = {
                "months": months,
                "rainfall_baseline": [round(v, 2) for v in rainfall_baseline],
                "rainfall_projected": rainfall_projected,
                "soil_moisture_baseline": [round(v, 4) for v in soil_moisture_baseline],
            }

        response_data: Dict[str, Any] = {
            "input_conditions": {"max_temp_celsius": base_temp, "total_rain_mm": base_rain, "data_source": data_source, "crop_type": crop_type},
            "predictions": {
                "standard_seed": {"type_code": SEED_TYPES["standard"], "predicted_yield": round(standard_yield, 2)},
                "resilient_seed": {"type_code": SEED_TYPES["resilient"], "predicted_yield": round(resilient_yield, 2)},
            },
            "analysis": {"avoided_loss": round(avoided_loss, 2), "percentage_improvement": round(percentage_improvement, 2), "recommendation": "resilient" if avoided_loss > 0 else "standard"},
            "simulation_debug": {"raw_temp": round(base_temp, 2), "perturbation_added": round(temp_increase, 2), "final_simulated_temp": round(final_simulated_temp, 2), "raw_rain": round(base_rain, 2), "rain_modifier": round(rain_change, 2), "final_simulated_rain": round(final_simulated_rain, 2)},
        }

        if chart_data is not None:
            response_data["chart_data"] = chart_data
        if spatial_analysis is not None:
            response_data["spatial_analysis"] = spatial_analysis
        if roi_analysis is not None:
            response_data["roi_analysis"] = roi_analysis

        return {"status": "success", "data": response_data}

    except ValueError:
        return legacy_error(400, "Invalid numeric values for temp/rain", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return legacy_error(500, f"Prediction failed: {str(e)}", "PREDICTION_ERROR")


@router.post("/start-batch")
def start_batch(req: StartBatchRequest, user: User = Depends(get_current_user)):
    """Start a background batch processing job for portfolio assets."""
    try:
        job_id = req.job_id
        run_batch_job.delay(job_id)
        print(f"[API] Queued batch job {job_id} via Celery", file=sys.stderr, flush=True)
        return JSONResponse(status_code=202, content={"status": "started", "job_id": job_id, "message": "Batch processing queued via Celery. Check batch_jobs table for status."})
    except Exception as e:
        return legacy_error(500, f"Failed to start batch job: {str(e)}", "BATCH_START_ERROR")


@router.post("/predict-portfolio")
async def predict_portfolio(req: PredictPortfolioRequest, user: User = Depends(get_current_user)):
    """Analyze portfolio diversification across multiple locations."""
    try:
        locations = req.locations
        crop_type = req.crop_type.lower()

        if crop_type not in ("maize", "cocoa"):
            return legacy_error(400, f"Unsupported crop_type: {crop_type}. Supported crops: 'maize', 'cocoa'", "INVALID_CROP_TYPE")

        all_location_cvs: list[float] = []
        total_tonnage = 0.0
        location_results: list[dict] = []

        for idx, loc in enumerate(locations):
            lat = loc.lat
            lon = loc.lon

            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                weather_data = await run_in_threadpool(get_weather_data, lat=lat, lon=lon, start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))
                base_temp = weather_data["max_temp_celsius"]
                base_rain = weather_data["total_precip_mm"]
            except Exception as weather_error:
                return legacy_error(500, f"Failed to fetch weather data for location {idx}: {str(weather_error)}", "WEATHER_DATA_ERROR")

            years = 10
            annual_yields: list[float] = []

            for _ in range(years):
                temp_variation = random.uniform(-2.0, 2.0)
                rain_variation = random.uniform(-15.0, 15.0)
                year_yield = calculate_yield(temp=base_temp, rain=base_rain, seed_type=SEED_TYPES["resilient"], crop_type=crop_type, temp_delta=temp_variation, rain_pct_change=rain_variation)
                annual_yields.append(year_yield)

            mean_yield = statistics.mean(annual_yields)
            location_cv = calculate_volatility(annual_yields)

            max_potential_tons = 10.0
            location_tonnage = (mean_yield / 100.0) * max_potential_tons
            total_tonnage += location_tonnage
            all_location_cvs.append(location_cv)

            location_results.append({"location_index": idx, "lat": lat, "lon": lon, "mean_yield_pct": round(mean_yield, 2), "volatility_cv_pct": location_cv, "tonnage": round(location_tonnage, 2)})

        portfolio_volatility = statistics.mean(all_location_cvs) if all_location_cvs else 0.0
        risk_rating = "Low" if portfolio_volatility < 10.0 else "Medium" if portfolio_volatility < 20.0 else "High" if portfolio_volatility < 30.0 else "Very High"

        return {
            "status": "success",
            "data": {
                "portfolio_summary": {"total_tonnage": round(total_tonnage, 2), "portfolio_volatility_pct": round(portfolio_volatility, 2), "risk_rating": risk_rating, "num_locations": len(locations), "crop_type": crop_type},
                "locations": location_results,
                "risk_interpretation": {"low": "0-10% CV: Very stable production", "medium": "10-20% CV: Moderate variation", "high": "20-30% CV: Significant variation", "very_high": "30%+ CV: Highly volatile"},
            },
        }

    except ValueError as ve:
        return legacy_error(400, f"Invalid numeric values: {str(ve)}", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return legacy_error(500, f"Portfolio analysis failed: {str(e)}", "PORTFOLIO_ERROR")
