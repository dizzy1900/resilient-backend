"""Flood prediction endpoints — flash flood and urban flood."""

from __future__ import annotations

import pickle
import sys
from typing import Dict, Any, Optional

import pandas as pd
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from auth import get_current_user
from models import User
from flood_engine import analyze_flash_flood, calculate_rainfall_frequency, analyze_infrastructure_risk
from lifespan_depreciation import flood_lifespan_penalty, apply_lifespan_depreciation, flood_has_intervention_rescue
from routers._shared import legacy_error, has_opex_intervention

router = APIRouter(prefix="/api/v1/flood", tags=["Flood"])

# ---------------------------------------------------------------------------
# ML model
# ---------------------------------------------------------------------------

_FLOOD_MODEL_PATH = "flood_surrogate.pkl"
flood_pkl_model = None

try:
    with open(_FLOOD_MODEL_PATH, "rb") as _f:
        flood_pkl_model = pickle.load(_f)
    print(f"Flood model loaded successfully from {_FLOOD_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Flood model file '{_FLOOD_MODEL_PATH}' not found.")
except Exception as _e:
    print(f"Warning: Failed to load flood model: {_e}")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class PredictFlashFloodRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    rain_intensity_pct: float = Field(..., ge=0)
    infrastructure_params: Optional[Dict[str, Any]] = None
    intervention_params: Optional[Dict[str, Any]] = None
    social_params: Optional[Dict[str, Any]] = None


class PredictUrbanFloodRequest(BaseModel):
    rain_intensity: float = Field(..., description="Rainfall intensity mm/hr")
    current_imperviousness: float = Field(..., ge=0.0, le=1.0)
    intervention_type: str = Field(...)
    slope_pct: float = Field(2.0, ge=0.1, le=10.0)
    building_value: float = Field(750000.0)
    num_buildings: int = Field(1, ge=1)
    initial_lifespan_years: int = Field(30, ge=1, le=200)
    global_warming: float = Field(0.0)
    base_annual_opex: float = Field(25000.0)
    daily_revenue: float = Field(0.0)
    expected_downtime_days: int = Field(0, ge=0)
    green_roofs: Optional[bool] = Field(None)
    drainage_upgrade: Optional[bool] = Field(None)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/predict-flash")
def predict_flash_flood(req: PredictFlashFloodRequest):
    """Predict flash flood risk using Topographic Wetness Index (TWI) model."""
    try:
        lat, lon = req.lat, req.lon
        rain_intensity_pct = req.rain_intensity_pct

        flash_flood_analysis = analyze_flash_flood(lat, lon, rain_intensity_pct)
        rainfall_frequency = calculate_rainfall_frequency(rain_intensity_pct)

        spatial_analysis = None
        try:
            spatial_analysis = analyze_infrastructure_risk(lat, lon, rain_intensity_pct)
        except Exception as spatial_error:
            print(f"Infrastructure risk analysis error: {spatial_error}", file=sys.stderr, flush=True)

        response_data: Dict[str, Any] = {
            "input_conditions": {"lat": lat, "lon": lon, "rain_intensity_increase_pct": rain_intensity_pct},
            "flash_flood_analysis": flash_flood_analysis,
            "analytics": rainfall_frequency,
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
                intervention_type = intervention_params.get("type", "drainage")
                baseline_area = flash_flood_analysis.get("baseline_flood_area_km2", 0.0)
                estimated_flood_depth = 0.5 if baseline_area > 0 else 0.0
                if asset_value > 0 and estimated_flood_depth > 0:
                    infrastructure_roi = calculate_infrastructure_roi(flood_depth_m=estimated_flood_depth, asset_value=asset_value, daily_revenue=daily_revenue, project_capex=capex, project_opex=opex, intervention_type=intervention_type, analysis_years=20, discount_rate=0.10, wall_height_m=intervention_params.get("wall_height_m", 2.0), drainage_reduction_m=intervention_params.get("drainage_reduction_m", 0.3))
            except Exception as roi_error:
                print(f"Infrastructure ROI error: {roi_error}", file=sys.stderr, flush=True)

        if infrastructure_roi is not None:
            response_data["infrastructure_roi"] = infrastructure_roi

        impact_metrics = None
        if req.social_params or infrastructure_roi is not None:
            try:
                from social_impact_engine import analyze_beneficiaries, calculate_nature_value, calculate_social_metrics
                buffer_km = 50.0
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
        return legacy_error(400, "Invalid numeric values for lat/lon/rain_intensity_pct", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return legacy_error(500, f"Flash flood analysis failed: {str(e)}", "FLASH_FLOOD_ERROR")


@router.post("/predict")
def predict_flood(req: PredictUrbanFloodRequest, user: User = Depends(get_current_user)):
    """Predict urban flood depth with and without green infrastructure intervention."""
    if flood_pkl_model is None:
        return legacy_error(500, "Flood model file not found. Ensure flood_surrogate.pkl exists.", "MODEL_NOT_FOUND")

    try:
        rain_intensity = req.rain_intensity
        current_imperviousness = req.current_imperviousness
        intervention_type = req.intervention_type.lower()
        slope_pct = req.slope_pct
        building_value = req.building_value
        num_buildings = req.num_buildings
        initial_lifespan_years = req.initial_lifespan_years
        global_warming = req.global_warming
        daily_revenue = req.daily_revenue
        expected_downtime_days = req.expected_downtime_days

        raw_penalty = flood_lifespan_penalty(global_warming)
        has_intervention_rescue = flood_has_intervention_rescue(intervention_type)
        adjusted_lifespan, lifespan_penalty = apply_lifespan_depreciation(initial_lifespan_years, raw_penalty, has_intervention_rescue)

        base_annual_opex: float = float(req.base_annual_opex)
        if global_warming > 2.0:
            opex_penalty_pct = 0.25
        elif global_warming > 1.5:
            opex_penalty_pct = 0.12
        else:
            opex_penalty_pct = 0.0
        opex_climate_penalty: float = base_annual_opex * opex_penalty_pct
        if has_opex_intervention(intervention_type):
            opex_climate_penalty *= 0.15
        adjusted_opex: float = base_annual_opex + opex_climate_penalty

        if not (10 <= rain_intensity <= 150):
            return legacy_error(400, "Rain intensity must be between 10 and 150 mm/hr", "INVALID_RAIN_INTENSITY")
        if not (0.0 <= current_imperviousness <= 1.0):
            return legacy_error(400, "Current imperviousness must be between 0.0 and 1.0", "INVALID_IMPERVIOUSNESS")
        if not (0.1 <= slope_pct <= 10.0):
            return legacy_error(400, "Slope must be between 0.1 and 10.0 percent", "INVALID_SLOPE")

        INTERVENTION_FACTORS = {"green_roof": 0.30, "permeable_pavement": 0.40, "bioswales": 0.25, "rain_gardens": 0.20, "sponge_city": 0.35, "sponge city": 0.35, "none": 0.0}

        if intervention_type not in INTERVENTION_FACTORS:
            return legacy_error(400, f"Invalid intervention type. Must be one of: {', '.join(INTERVENTION_FACTORS.keys())}", "INVALID_INTERVENTION_TYPE")

        baseline_df = pd.DataFrame({"rain_intensity_mm_hr": [rain_intensity], "impervious_pct": [current_imperviousness], "slope_pct": [slope_pct]})
        reduction_factor = INTERVENTION_FACTORS[intervention_type]
        intervention_imperviousness = max(0.0, current_imperviousness - reduction_factor)
        intervention_df = pd.DataFrame({"rain_intensity_mm_hr": [rain_intensity], "impervious_pct": [intervention_imperviousness], "slope_pct": [slope_pct]})

        depth_baseline = float(flood_pkl_model.predict(baseline_df)[0])
        depth_intervention = float(flood_pkl_model.predict(intervention_df)[0])

        avoided_depth_cm = depth_baseline - depth_intervention
        percentage_improvement = (avoided_depth_cm / depth_baseline * 100) if depth_baseline > 0 else 0

        def _flood_damage_pct(depth_cm: float) -> float:
            if depth_cm <= 0: return 0.0
            if depth_cm < 5: return (depth_cm / 5.0) * 2.0
            if depth_cm < 15: return 2.0 + 6.0 * ((depth_cm - 5) / 10.0)
            if depth_cm < 30: return 8.0 + 12.0 * ((depth_cm - 15) / 15.0)
            if depth_cm < 60: return 20.0 + 20.0 * ((depth_cm - 30) / 30.0)
            return min(40.0 + 30.0 * min((depth_cm - 60) / 60.0, 1.0), 70.0)

        baseline_damage_pct = _flood_damage_pct(depth_baseline)
        intervention_damage_pct = _flood_damage_pct(depth_intervention)
        avoided_damage_pct = baseline_damage_pct - intervention_damage_pct
        avoided_damage_usd = (avoided_damage_pct / 100) * num_buildings * building_value

        from infrastructure_engine import calculate_avoided_business_interruption
        has_intervention = intervention_type != "none"
        interruption = calculate_avoided_business_interruption(daily_revenue=daily_revenue, expected_downtime_days=expected_downtime_days, has_intervention=has_intervention)

        return {
            "status": "success",
            "data": {
                "input_conditions": {"rain_intensity_mm_hr": rain_intensity, "current_imperviousness": current_imperviousness, "intervention_type": intervention_type, "slope_pct": slope_pct, "building_value": building_value, "num_buildings": num_buildings, "initial_lifespan_years": initial_lifespan_years, "global_warming_c": global_warming, "base_annual_opex": base_annual_opex, "daily_revenue": daily_revenue, "expected_downtime_days": expected_downtime_days},
                "asset_depreciation": {"adjusted_lifespan": adjusted_lifespan, "lifespan_penalty": lifespan_penalty},
                "material_degradation_opex": {"adjusted_opex": round(adjusted_opex, 2), "opex_climate_penalty": round(opex_climate_penalty, 2)},
                "imperviousness_change": {"baseline": round(current_imperviousness, 3), "intervention": round(intervention_imperviousness, 3), "reduction_factor": reduction_factor, "absolute_reduction": round(current_imperviousness - intervention_imperviousness, 3)},
                "predictions": {"baseline_depth_cm": round(depth_baseline, 2), "intervention_depth_cm": round(depth_intervention, 2)},
                "analysis": {"avoided_depth_cm": round(avoided_depth_cm, 2), "percentage_improvement": round(percentage_improvement, 2), "baseline_damage_pct": round(baseline_damage_pct, 2), "intervention_damage_pct": round(intervention_damage_pct, 2), "avoided_damage_pct": round(avoided_damage_pct, 2), "avoided_loss": round(avoided_damage_usd, 2), "recommendation": intervention_type if avoided_depth_cm > 0 else "none", "avoided_business_interruption": interruption["avoided_business_interruption"]},
                "economic_assumptions": {"num_buildings": num_buildings, "avg_building_value": building_value, "total_value_at_risk": num_buildings * building_value, "damage_function": "Urban Flood Damage (Huizinga et al., 2017)", "total_value_basis": "Avoided structural damage across affected buildings"},
                "depth_baseline": round(depth_baseline, 2), "depth_intervention": round(depth_intervention, 2),
                "avoided_loss": round(avoided_damage_usd, 2), "avoided_business_interruption": interruption["avoided_business_interruption"],
                "adjusted_opex": round(adjusted_opex, 2), "opex_climate_penalty": round(opex_climate_penalty, 2),
            },
        }

    except ValueError as ve:
        return legacy_error(400, f"Invalid numeric values: {str(ve)}", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return legacy_error(500, f"Prediction failed: {str(e)}", "PREDICTION_ERROR")
