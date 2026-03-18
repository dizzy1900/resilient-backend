"""Coastal prediction endpoints — runup and flood risk."""

from __future__ import annotations

import pickle
import sys
from typing import Dict, Any, Optional

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from auth import get_current_user
from models import User
from gee_connector import get_coastal_params
from coastal_engine import analyze_flood_risk, analyze_urban_impact
from lifespan_depreciation import (
    coastal_lifespan_penalty, apply_lifespan_depreciation,
    coastal_has_intervention_rescue,
)
from routers._shared import legacy_error, has_opex_intervention

router = APIRouter(tags=["Coastal"])

# ---------------------------------------------------------------------------
# ML model
# ---------------------------------------------------------------------------

_COASTAL_MODEL_PATH = "coastal_surrogate.pkl"
coastal_pkl_model = None

try:
    with open(_COASTAL_MODEL_PATH, "rb") as _f:
        coastal_pkl_model = pickle.load(_f)
    print(f"Coastal model loaded successfully from {_COASTAL_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Coastal model file '{_COASTAL_MODEL_PATH}' not found.")
except Exception as _e:
    print(f"Warning: Failed to load coastal model: {_e}")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class PredictCoastalRunupRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    mangrove_width: float = Field(..., description="Mangrove buffer width in meters")
    initial_lifespan_years: int = Field(30, ge=1, le=200)
    sea_level_rise: float = Field(0.0, description="Sea level rise in meters")
    intervention: str = Field("", description="e.g. 'Sea Wall', 'Drainage Upgrade', 'Sponge City'")
    base_annual_opex: float = Field(25000.0, description="Base annual OPEX in USD")
    daily_revenue: float = Field(0.0)
    expected_downtime_days: int = Field(0, ge=0)
    green_roofs: Optional[bool] = Field(None)
    drainage_upgrade: Optional[bool] = Field(None)


class PredictCoastalFloodRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    slr_projection: float
    include_surge: bool = False
    initial_lifespan_years: int = 30
    intervention: Optional[str] = ""
    intervention_params: Optional[Dict[str, Any]] = None
    infrastructure_params: Optional[Dict[str, Any]] = None
    social_params: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/predict-coastal")
async def predict_coastal(req: PredictCoastalRunupRequest, user: User = Depends(get_current_user)):
    """Predict coastal runup elevation with and without mangrove protection."""
    if coastal_pkl_model is None:
        return legacy_error(500, "Coastal model file not found. Ensure coastal_surrogate.pkl exists.", "MODEL_NOT_FOUND")

    try:
        lat, lon = req.lat, req.lon
        mangrove_width = req.mangrove_width
        initial_lifespan_years = req.initial_lifespan_years
        sea_level_rise = req.sea_level_rise
        intervention = req.intervention.strip()
        daily_revenue = req.daily_revenue
        expected_downtime_days = req.expected_downtime_days

        raw_penalty = coastal_lifespan_penalty(sea_level_rise)
        has_intervention_rescue = coastal_has_intervention_rescue(intervention)
        adjusted_lifespan, lifespan_penalty = apply_lifespan_depreciation(initial_lifespan_years, raw_penalty, has_intervention_rescue)

        if 0 < mangrove_width < 10:
            mangrove_width = 10

        coastal_data = await run_in_threadpool(get_coastal_params, lat, lon)
        slope = coastal_data["slope_pct"]
        wave_height = coastal_data["max_wave_height"]

        scenario_a_df = pd.DataFrame({"wave_height": [wave_height], "slope": [slope], "mangrove_width_m": [0.0]})
        scenario_b_df = pd.DataFrame({"wave_height": [wave_height], "slope": [slope], "mangrove_width_m": [mangrove_width]})

        runup_a = float(coastal_pkl_model.predict(scenario_a_df)[0])
        runup_b = float(coastal_pkl_model.predict(scenario_b_df)[0])

        avoided_runup = runup_a - runup_b
        DAMAGE_COST_PER_METER = 10000
        NUM_PROPERTIES = 100
        avoided_damage_usd = avoided_runup * DAMAGE_COST_PER_METER * NUM_PROPERTIES
        percentage_improvement = (avoided_runup / runup_a * 100) if runup_a > 0 else 0

        from infrastructure_engine import calculate_avoided_business_interruption
        has_intervention = mangrove_width > 0
        interruption = calculate_avoided_business_interruption(daily_revenue=daily_revenue, expected_downtime_days=expected_downtime_days, has_intervention=has_intervention)

        base_annual_opex: float = float(req.base_annual_opex)
        if sea_level_rise > 1.0:
            opex_penalty_pct = 0.30
        elif sea_level_rise > 0.5:
            opex_penalty_pct = 0.15
        else:
            opex_penalty_pct = 0.0
        opex_climate_penalty: float = base_annual_opex * opex_penalty_pct
        if has_opex_intervention(intervention):
            opex_climate_penalty *= 0.15
        adjusted_opex: float = base_annual_opex + opex_climate_penalty

        return {
            "status": "success",
            "data": {
                "input_conditions": {"lat": lat, "lon": lon, "mangrove_width_m": mangrove_width, "initial_lifespan_years": initial_lifespan_years, "sea_level_rise_m": sea_level_rise, "intervention": intervention or None, "base_annual_opex": base_annual_opex, "daily_revenue": daily_revenue, "expected_downtime_days": expected_downtime_days},
                "coastal_params": {"detected_slope_pct": round(slope, 2), "storm_wave_height": round(wave_height, 2)},
                "predictions": {"baseline_runup": round(runup_a, 4), "protected_runup": round(runup_b, 4)},
                "analysis": {"avoided_loss": round(avoided_damage_usd, 2), "avoided_runup_m": round(avoided_runup, 4), "percentage_improvement": round(percentage_improvement, 2), "recommendation": "with_mangroves" if avoided_runup > 0 else "baseline", "avoided_business_interruption": interruption["avoided_business_interruption"]},
                "asset_depreciation": {"adjusted_lifespan": adjusted_lifespan, "lifespan_penalty": lifespan_penalty},
                "material_degradation_opex": {"adjusted_opex": round(adjusted_opex, 2), "opex_climate_penalty": round(opex_climate_penalty, 2)},
                "economic_assumptions": {"damage_cost_per_meter": DAMAGE_COST_PER_METER, "num_properties": NUM_PROPERTIES, "total_value_basis": "USD per meter of flood reduction \u00d7 properties affected"},
                "slope": round(slope / 100, 4), "storm_wave": round(wave_height, 2),
                "avoided_loss": round(avoided_damage_usd, 2), "avoided_business_interruption": interruption["avoided_business_interruption"],
                "adjusted_opex": round(adjusted_opex, 2), "opex_climate_penalty": round(opex_climate_penalty, 2),
            },
        }

    except ValueError:
        return legacy_error(400, "Invalid numeric values for lat/lon/mangrove_width", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return legacy_error(500, f"Prediction failed: {str(e)}", "PREDICTION_ERROR")


@router.post("/predict-coastal-flood")
def predict_coastal_flood(req: PredictCoastalFloodRequest):
    """Predict coastal flood risk based on sea level rise and storm surge."""
    try:
        lat, lon = req.lat, req.lon
        slr_projection = req.slr_projection
        include_surge = req.include_surge
        initial_lifespan_years = req.initial_lifespan_years

        intervention_raw = ((req.intervention_params or {}).get("type")) or req.intervention or ""
        intervention_str = str(intervention_raw).strip() if intervention_raw else ""

        raw_penalty = coastal_lifespan_penalty(slr_projection)
        has_intervention_rescue = coastal_has_intervention_rescue(intervention_str)
        adjusted_lifespan, lifespan_penalty = apply_lifespan_depreciation(initial_lifespan_years, raw_penalty, has_intervention_rescue)

        if slr_projection < 0:
            return legacy_error(400, "Sea level rise projection must be non-negative", "INVALID_SLR_PROJECTION")

        surge_m = 2.5 if include_surge else 0.0
        total_water_level = slr_projection + surge_m

        flood_risk = analyze_flood_risk(lat, lon, slr_projection, surge_m)

        spatial_analysis = None
        try:
            spatial_analysis = analyze_urban_impact(lat, lon, total_water_level)
        except Exception as spatial_error:
            print(f"Spatial analysis error: {spatial_error}", file=sys.stderr, flush=True)

        response_data: Dict[str, Any] = {
            "input_conditions": {"lat": lat, "lon": lon, "slr_projection_m": slr_projection, "include_surge": include_surge, "surge_m": surge_m, "total_water_level_m": total_water_level, "initial_lifespan_years": initial_lifespan_years, "intervention": intervention_str or None},
            "flood_risk": flood_risk,
            "asset_depreciation": {"adjusted_lifespan": adjusted_lifespan, "lifespan_penalty": lifespan_penalty},
        }

        if spatial_analysis is not None:
            response_data["spatial_analysis"] = spatial_analysis

        infrastructure_roi = None
        if req.infrastructure_params and req.intervention_params:
            try:
                from infrastructure_engine import calculate_infrastructure_roi
                infra_params = req.infrastructure_params
                intervention_params = req.intervention_params
                asset_value = float(infra_params.get("asset_value", 0))
                daily_revenue = float(infra_params.get("daily_revenue", 0))
                capex = float(intervention_params.get("capex", 0))
                opex = float(intervention_params.get("opex", 0))
                intervention_type = intervention_params.get("type", "sea_wall")
                flood_depth = flood_risk.get("flood_depth_m", 0.0)

                if asset_value > 0 and flood_depth > 0:
                    infrastructure_roi = calculate_infrastructure_roi(flood_depth_m=flood_depth, asset_value=asset_value, daily_revenue=daily_revenue, project_capex=capex, project_opex=opex, intervention_type=intervention_type, analysis_years=20, discount_rate=0.10, wall_height_m=intervention_params.get("wall_height_m", 2.0), drainage_reduction_m=intervention_params.get("drainage_reduction_m", 0.3))
            except Exception as roi_error:
                print(f"Infrastructure ROI error: {roi_error}", file=sys.stderr, flush=True)

        if infrastructure_roi is not None:
            response_data["infrastructure_roi"] = infrastructure_roi

        impact_metrics = None
        if req.social_params or infrastructure_roi is not None:
            try:
                from social_impact_engine import analyze_beneficiaries, calculate_nature_value, calculate_social_metrics
                buffer_km = 5.0
                beneficiaries = analyze_beneficiaries(lat, lon, buffer_km, flood_mask=None)
                nature_value = None
                if req.social_params:
                    social_params = req.social_params
                    s_intervention_type = social_params.get("intervention_type", "")
                    area_hectares = float(social_params.get("area_hectares", 0))
                    if area_hectares > 0:
                        nature_value = calculate_nature_value(s_intervention_type, area_hectares)
                social_metrics = None
                if infrastructure_roi is not None:
                    intervention_cost = infrastructure_roi["financial_analysis"]["project_capex"]
                    social_metrics = calculate_social_metrics(people_at_risk=beneficiaries["people_at_risk"], households_at_risk=beneficiaries["households_at_risk"], intervention_cost=intervention_cost, nature_value=nature_value)
                impact_metrics: Dict[str, Any] = {"beneficiaries": beneficiaries}
                if nature_value is not None:
                    impact_metrics["nature_value"] = nature_value
                if social_metrics is not None:
                    impact_metrics["social_metrics"] = social_metrics
            except Exception as social_error:
                print(f"Social impact analysis error: {social_error}", file=sys.stderr, flush=True)

        if impact_metrics is not None:
            response_data["impact_metrics"] = impact_metrics

        return {"status": "success", "data": response_data}

    except ValueError:
        return legacy_error(400, "Invalid numeric values for lat/lon/slr_projection", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return legacy_error(500, f"Flood risk analysis failed: {str(e)}", "FLOOD_RISK_ERROR")
