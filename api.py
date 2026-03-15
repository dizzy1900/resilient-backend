#!/usr/bin/env python3
"""FastAPI Simulation Service — AdaptMetric Climate Resilience Engine

Full production API serving both the /simulate family (headless-runner driven)
and the /predict family (in-process model inference).

Run locally:
  uvicorn api:app --reload --port 8000

Or:
  python api.py
"""

from __future__ import annotations

import io
import os
import re
import subprocess
import json
import asyncio
from typing import Literal, Optional, Dict, Any, List, Tuple

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np

from io import BytesIO

from datetime import datetime, timedelta

from physics_engine import calculate_yield
from spatial_engine import process_polygon_request
from lifespan_depreciation import (
    coastal_lifespan_penalty,
    flood_lifespan_penalty,
    apply_lifespan_depreciation,
    coastal_has_intervention_rescue,
    flood_has_intervention_rescue,
)
from price_shock_engine import calculate_price_shock
from nlg_engine import generate_deterministic_summary

import math
import pickle
import random
import statistics
import sys
import threading

import joblib
from fastapi.responses import JSONResponse

from gee_connector import (
    get_weather_data, get_coastal_params, get_monthly_data,
    analyze_spatial_viability, get_terrain_data, get_ndvi_timeseries,
    analyze_route_flood_risk,
)
import ee
from gee_credentials import load_gee_credentials
from batch_processor import run_batch_job
from coastal_engine import analyze_flood_risk, analyze_urban_impact
from flood_engine import (
    analyze_flash_flood, calculate_rainfall_frequency,
    analyze_infrastructure_risk,
)
from financial_engine import calculate_roi_metrics, calculate_npv, calculate_payback_period

from auth import router as auth_router
from database import Base, engine

# ---------------------------------------------------------------------------
# In-process ML models (ported from Flask)
# ---------------------------------------------------------------------------
_AG_MODEL_PATH = "ag_surrogate.pkl"
_COASTAL_MODEL_PATH = "coastal_surrogate.pkl"
_FLOOD_MODEL_PATH = "flood_surrogate.pkl"
_COFFEE_MODEL_PATH = "coffee_model.pkl"

ag_pkl_model = None
coastal_pkl_model = None
flood_pkl_model = None
coffee_pkl_model = None

try:
    with open(_AG_MODEL_PATH, "rb") as _f:
        ag_pkl_model = pickle.load(_f)
    print(f"Model loaded successfully from {_AG_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Model file '{_AG_MODEL_PATH}' not found. Run start.sh or download manually.")
except Exception as _e:
    print(f"Warning: Failed to load model: {_e}")

try:
    with open(_COASTAL_MODEL_PATH, "rb") as _f:
        coastal_pkl_model = pickle.load(_f)
    print(f"Coastal model loaded successfully from {_COASTAL_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Coastal model file '{_COASTAL_MODEL_PATH}' not found.")
except Exception as _e:
    print(f"Warning: Failed to load coastal model: {_e}")

try:
    with open(_FLOOD_MODEL_PATH, "rb") as _f:
        flood_pkl_model = pickle.load(_f)
    print(f"Flood model loaded successfully from {_FLOOD_MODEL_PATH}")
except FileNotFoundError:
    print(f"Warning: Flood model file '{_FLOOD_MODEL_PATH}' not found.")
except Exception as _e:
    print(f"Warning: Failed to load flood model: {_e}")

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


# ---------------------------------------------------------------------------
# Crop Switching What-If Engine (Agriculture module)
# ---------------------------------------------------------------------------

# Drought index: 0.0 = no drought, 1.0 = severe. "High" stress threshold used in logic.
DROUGHT_INDEX_HIGH_THRESHOLD = 0.6
GLOBAL_WARMING_STRESS_THRESHOLD = 1.5

# Yield penalty (fraction of baseline lost) by current crop under climate stress.
CLIMATE_PENALTY_BY_CROP: Dict[str, float] = {
    "maize": 0.30,
    "Maize": 0.30,
    "wheat": 0.40,
    "Wheat": 0.40,
}

# Default penalty for unlisted current crops under stress.
DEFAULT_CLIMATE_PENALTY = 0.25

# Proposed crop: (capex_per_hectare_usd, yield_penalty_under_stress_fraction)
PROPOSED_CROP_ECONOMICS: Dict[str, Tuple[float, float]] = {
    "Drought-Resistant Sorghum": (400.0, 0.05),
    "Heat-Tolerant Wheat": (350.0, 0.10),
}


class PredictAgriRequest(BaseModel):
    """Request for Crop Switching What-If: current vs proposed crop under climate stress."""
    current_crop: str = Field("Maize", description="Current crop (e.g. Maize, Wheat)")
    proposed_crop: str = Field("None", description="Proposed alternative (e.g. Drought-Resistant Sorghum, Heat-Tolerant Wheat, or None)")
    hectares: float = Field(1000.0, ge=0.0, description="Area in hectares")
    baseline_yield_value: float = Field(500000.0, ge=0.0, description="Baseline revenue/yield value in USD")
    global_warming: float = Field(0.0, ge=-1.0, le=5.0, description="Global warming in °C (e.g. 1.5, 2.0)")
    drought_index: float = Field(0.0, ge=0.0, le=1.0, description="Drought index 0–1; high stress when > 0.6")


class PredictAgriResponse(BaseModel):
    """Response for Crop Switching What-If with stressed yield and transition economics."""
    stressed_yield_value: float
    adjusted_yield_value: float
    transition_capex: float
    avoided_revenue_loss: float
    risk_reduction_pct: float = 0.0


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


class CBARequest(BaseModel):
    """Request for Cost-Benefit Analysis time series of a climate adaptation project."""
    capex: float = Field(500000.0, description="Upfront capital expenditure in USD")
    annual_opex: float = Field(25000.0, description="Annual operating expenditure in USD")
    discount_rate: float = Field(0.08, description="Discount rate as decimal (e.g. 0.08 for 8%)")
    lifespan_years: int = Field(30, ge=1, le=100, description="Project lifespan in years")
    annual_baseline_damage: float = Field(100000.0, description="Annual cost of doing nothing in USD")
    damage_reduction_pct: float = Field(0.80, ge=0.0, le=1.0, description="Fraction of damage the intervention prevents")
    # Parametric Insurance
    base_insurance_premium: float = Field(50000.0, description="Annual insurance premium without intervention in USD")
    insurance_reduction_pct: float = Field(0.25, ge=0.0, le=1.0, description="Premium reduction from intervention (e.g. 0.25 for 25%)")
    # Green Bond financing
    standard_interest_rate: float = Field(0.06, description="Standard bond interest rate as decimal (e.g. 0.06 for 6%)")
    greenium_discount_bps: float = Field(50.0, description="Green bond discount in basis points (e.g. 50 = 0.50%)")
    bond_tenor_years: int = Field(10, ge=1, le=50, description="Bond repayment period in years")
    # Carbon Credit revenue (Layered Value Stacking)
    annual_carbon_credits: float = Field(0.0, description="Tons of CO2 sequestered per year")
    carbon_price_per_ton: float = Field(50.0, description="Price per ton of CO2 in USD")


class CVaRRequest(BaseModel):
    """Request for Climate Value at Risk Monte Carlo simulation."""
    asset_value: float = Field(5_000_000.0, description="Total asset value in USD")
    mean_damage_pct: float = Field(0.02, description="Average annual damage as decimal (e.g. 0.02 for 2%)")
    volatility_pct: float = Field(0.05, description="Damage volatility as decimal (e.g. 0.05 for 5%)")
    num_simulations: int = Field(10_000, ge=100, le=1_000_000, description="Number of Monte Carlo trials")


class FinancingTranches(BaseModel):
    """Financing tranche structure for blended finance."""
    commercial_debt_pct: float = Field(..., ge=0.0, le=1.0, description="Commercial debt percentage (e.g., 0.50 for 50%)")
    concessional_grant_pct: float = Field(..., ge=0.0, le=1.0, description="Concessional grant percentage (e.g., 0.30 for 30%)")
    municipal_equity_pct: float = Field(..., ge=0.0, le=1.0, description="Municipal equity percentage (e.g., 0.20 for 20%)")


class BlendedFinanceRequest(BaseModel):
    """Request for Blended Finance Structuring calculation."""
    total_capex: float = Field(..., gt=0, description="Total capital expenditure in USD")
    resilience_score: int = Field(..., ge=0, le=100, description="Climate resilience score (0-100)")
    tranches: FinancingTranches = Field(..., description="Financing tranche structure")
    rate_shock_bps: Optional[int] = Field(None, description="Optional rate shock in basis points for sensitivity analysis (e.g., 100 for +1%)")
    annual_carbon_revenue: float = Field(0.0, ge=0, description="Annual carbon credit revenue in USD to offset debt service costs")
    base_insurance_premium: float = Field(0.0, ge=0, description="Current annual insurance premium in USD before resilience improvements")
    risk_reduction_pct: float = Field(0.0, ge=0, le=1.0, description="Percentage of physical risk mitigated by resilience investment (0.0 to 1.0)")
    
    @property
    def tranches_sum(self) -> float:
        """Calculate the sum of all tranche percentages."""
        return (
            self.tranches.commercial_debt_pct +
            self.tranches.concessional_grant_pct +
            self.tranches.municipal_equity_pct
        )
    
    def model_post_init(self, __context) -> None:
        """Validate that tranches sum to 1.0 (100%)."""
        tranches_total = self.tranches_sum
        if not (0.99 <= tranches_total <= 1.01):  # Allow 1% tolerance for rounding
            raise ValueError(
                f"Tranches must sum to 1.0 (100%). Current sum: {tranches_total:.4f}"
            )


class BlendedFinanceResponse(BaseModel):
    """Response for Blended Finance Structuring calculation."""
    status: str = "success"
    
    # Input echo
    input_capex: float
    input_resilience_score: int
    
    # Tranche breakdown
    commercial_debt_amount: float
    concessional_grant_amount: float
    municipal_equity_amount: float
    
    # Interest rates
    base_commercial_rate: float
    applied_commercial_rate: float
    concessional_rate: float
    municipal_equity_rate: float
    greenium_discount_bps: float
    
    # Blended metrics
    blended_interest_rate: float
    annual_debt_service: float
    total_greenium_savings: float
    
    # Carbon credit revenue integration
    annual_carbon_revenue: float
    net_annual_debt_service: float
    
    # Insurance premium reduction (Resilience Dividend)
    insurance_savings: float
    adjusted_insurance_premium: float
    
    # Additional context
    loan_term_years: int
    debt_principal: float  # Excludes equity portion
    
    # Sensitivity analysis (optional, only present if rate_shock_bps provided)
    sensitivity_analysis: Optional[Dict[str, Any]] = None

# ---------------------------------------------------------------------------
# Pydantic models for legacy /predict-* routes (ported from Flask)
# ---------------------------------------------------------------------------

PredictCropType = Literal["maize", "cocoa", "coffee"]


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


class PredictCoastalRunupRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    mangrove_width: float = Field(..., description="Mangrove buffer width in meters")
    initial_lifespan_years: int = Field(30, ge=1, le=200, description="Asset initial lifespan for depreciation")
    sea_level_rise: float = Field(0.0, description="Sea level rise in meters")
    intervention: str = Field("", description="e.g. 'Sea Wall', 'Drainage Upgrade', 'Sponge City'")
    base_annual_opex: float = Field(25000.0, description="Base annual OPEX in USD for material degradation")
    daily_revenue: float = Field(0.0, description="Daily revenue (USD) for business interruption")
    expected_downtime_days: int = Field(0, ge=0, description="Expected downtime days")
    # Optional intervention flags (frontend may send these instead of or in addition to intervention string)
    green_roofs: Optional[bool] = Field(None, description="Green roofs intervention enabled")
    drainage_upgrade: Optional[bool] = Field(None, description="Drainage upgrade intervention enabled")


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
    intervention_type: str = Field(..., description="e.g. 'sponge_city', 'Drainage Upgrade', 'Sea Wall'")
    slope_pct: float = Field(2.0, ge=0.1, le=10.0)
    building_value: float = Field(750000.0, description="Building value in USD")
    num_buildings: int = Field(1, ge=1)
    initial_lifespan_years: int = Field(30, ge=1, le=200, description="Asset initial lifespan for depreciation")
    global_warming: float = Field(0.0, description="Global warming in °C for lifespan/OPEX penalty")
    base_annual_opex: float = Field(25000.0, description="Base annual OPEX in USD for material degradation")
    daily_revenue: float = Field(0.0, description="Daily revenue (USD) for business interruption")
    expected_downtime_days: int = Field(0, ge=0, description="Expected downtime days")
    # Optional intervention flags (frontend may send these in addition to intervention_type)
    green_roofs: Optional[bool] = Field(None, description="Green roofs intervention enabled")
    drainage_upgrade: Optional[bool] = Field(None, description="Drainage upgrade intervention enabled")


class StartBatchRequest(BaseModel):
    job_id: str


class CalculateFinancialsRequest(BaseModel):
    cash_flows: List[float] = Field(..., min_length=2)
    discount_rate: float = Field(..., ge=0.0, le=1.0)


class PredictHealthRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    workforce_size: int = Field(..., gt=0)
    daily_wage: float = Field(..., gt=0)
    # Cooling intervention fields
    intervention_type: Optional[str] = Field(
        None, 
        description="Cooling intervention type: 'hvac_retrofit', 'passive_cooling', 'hospital_expansion', 'urban_cooling_center', 'mosquito_eradication', or 'none'"
    )
    intervention_capex: Optional[float] = Field(
        None, 
        ge=0, 
        description="Upfront capital expenditure for cooling intervention in USD"
    )
    intervention_annual_opex: Optional[float] = Field(
        None, 
        ge=0, 
        description="Annual operating expenditure for cooling system in USD"
    )
    # Public health (DALY) fields
    population_size: Optional[int] = Field(
        100000,
        gt=0,
        description="Population size for public health DALY calculations (default: 100,000)"
    )
    gdp_per_capita_usd: Optional[float] = Field(
        8500.0,
        gt=0,
        description="GDP per capita in USD for DALY monetization (default: $8,500)"
    )
    # Healthcare Infrastructure Stress Testing fields
    economy_tier: Optional[str] = Field(
        "middle",
        description="Economic development tier: 'high', 'middle', or 'low' (default: 'middle')"
    )
    user_beds_per_1000: Optional[float] = Field(
        None,
        ge=0,
        description="Override baseline hospital beds per 1,000 population (optional)"
    )
    user_cost_per_bed: Optional[float] = Field(
        None,
        ge=0,
        description="Override cost per hospital bed in USD (optional)"
    )


class PredictPortfolioLocation(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class PredictPortfolioRequest(BaseModel):
    locations: List[PredictPortfolioLocation] = Field(..., min_length=1)
    crop_type: str = "maize"


class PriceShockRequest(BaseModel):
    """Request for commodity price shock calculation from climate-induced yield loss."""
    crop_type: str = Field(..., description="Crop type (e.g., maize, soybeans, wheat, rice, cocoa, coffee)")
    baseline_yield_tons: float = Field(..., gt=0, description="Expected yield under normal conditions (metric tons)")
    stressed_yield_tons: float = Field(..., ge=0, description="Actual/projected yield under climate stress (metric tons)")


class PriceShockResponse(BaseModel):
    """Response for commodity price shock calculation."""
    baseline_price: float = Field(..., description="Original commodity price (USD/ton)")
    shocked_price: float = Field(..., description="New price after supply shock (USD/ton)")
    price_increase_pct: float = Field(..., description="Percentage increase in price")
    price_increase_usd: float = Field(..., description="Absolute increase in price (USD/ton)")
    yield_loss_pct: float = Field(..., description="Percentage drop in yield")
    yield_loss_tons: float = Field(..., description="Absolute drop in yield (tons)")
    elasticity: float = Field(..., description="Supply elasticity coefficient used")
    forward_contract_recommendation: str = Field(..., description="Risk management advice")
    revenue_impact: Dict[str, float] = Field(..., description="Net revenue change analysis")


class ExecutiveSummaryRequest(BaseModel):
    """Request for deterministic NLG executive summary generation."""
    module_name: str = Field(
        ..., 
        description="Module identifier: health_public, health_private, agriculture, coastal, flood, price_shock"
    )
    location_name: str = Field(..., description="Geographic location name for summary context")
    simulation_data: Dict[str, Any] = Field(..., description="Module-specific simulation results dictionary")


class ExecutiveSummaryResponse(BaseModel):
    """Response containing generated executive summary."""
    summary_text: str = Field(..., description="3-sentence executive summary generated from simulation data")


class RouteRiskRequest(BaseModel):
    """Request for Macroeconomic Supply Chain route risk analysis."""
    route_geojson: Dict[str, Any] = Field(..., description="GeoJSON LineString geometry representing the truck route")
    cargo_value: float = Field(100000.0, description="Value of cargo in USD")


class RouteRiskResponse(BaseModel):
    """Response for Macroeconomic Supply Chain route risk analysis."""
    flooded_miles: float = Field(..., description="Total route length intersecting flood zones (miles)")
    detour_delay_hours: float = Field(..., description="Additional delay due to flood detours (hours)")
    freight_delay_cost: float = Field(..., description="Cost of freight delays in USD")
    spoilage_cost: float = Field(..., description="Cost of cargo spoilage due to delays in USD")
    total_value_at_risk: float = Field(..., description="Total economic value at risk in USD")
    intervention_capex: float = Field(..., description="Capital expenditure for flood mitigation in USD")


class GridRiskRequest(BaseModel):
    """Request for Energy & Grid Resilience analysis."""
    facility_sqft: float = Field(50000.0, gt=0, description="Facility size in square feet")
    baseline_temp_c: float = Field(25.0, description="Baseline temperature in Celsius")
    projected_temp_c: float = Field(35.0, description="Projected future temperature in Celsius")


class GridRiskResponse(BaseModel):
    """Response for Energy & Grid Resilience analysis."""
    temp_anomaly: float = Field(..., description="Temperature increase in Celsius")
    hvac_spike_pct: float = Field(..., description="HVAC demand spike as percentage (0-100)")
    downtime_loss: float = Field(..., description="Economic loss from downtime in USD")
    required_solar_kw: float = Field(..., description="Required solar capacity in kW")
    required_bess_kwh: float = Field(..., description="Required battery storage in kWh")
    microgrid_capex: float = Field(..., description="Microgrid capital expenditure in USD")


class PortfolioAsset(BaseModel):
    """Individual asset in a portfolio."""
    id: str = Field(..., description="Unique asset identifier")
    property_name: str = Field(..., description="Property name")
    location: str = Field(..., description="Geographic location")
    asset_value: float = Field(..., gt=0, description="Asset value in USD")
    primary_hazard: Literal["Flood", "Heat", "Coastal", "Supply Chain"] = Field(
        ..., description="Primary climate hazard type"
    )


class PortfolioRequest(BaseModel):
    """Request for Macro-Portfolio Risk analysis."""
    assets: List[PortfolioAsset] = Field(..., min_length=1, description="List of portfolio assets")


class CalculatedAsset(BaseModel):
    """Asset with calculated risk metrics."""
    id: str
    property_name: str
    location: str
    asset_value: float
    primary_hazard: str
    value_at_risk: float
    resilience_score: float
    status: Literal["Critical", "Warning", "Secure"]


class PortfolioSummary(BaseModel):
    """Portfolio-level summary statistics."""
    total_portfolio_value: float = Field(..., description="Total value of all assets in USD")
    total_value_at_risk: float = Field(..., description="Total VaR across all assets in USD")
    average_resilience_score: float = Field(..., description="Average resilience score (0-100)")


class PortfolioVisualizations(BaseModel):
    """Data for portfolio visualizations."""
    var_by_hazard: Dict[str, float] = Field(..., description="VaR grouped by hazard type (for donut chart)")
    top_at_risk_assets: List[CalculatedAsset] = Field(..., description="Top 5 assets by VaR (descending)")


class PortfolioResponse(BaseModel):
    """Response for Macro-Portfolio Risk analysis."""
    summary: PortfolioSummary = Field(..., description="Portfolio-level summary statistics")
    visualizations: PortfolioVisualizations = Field(..., description="Chart data for frontend visualizations")
    ledger: List[CalculatedAsset] = Field(..., description="Full array of calculated assets")


class SovereignRiskCountry(BaseModel):
    """Sovereign climate risk data for a single country."""
    country_code: str = Field(..., min_length=3, max_length=3, description="3-letter ISO country code")
    country_name: str = Field(..., description="Full country name")
    risk_score: int = Field(..., ge=0, le=100, description="Climate risk score (0-100)")
    primary_vulnerability: str = Field(..., description="Primary climate vulnerability")


class SovereignRiskResponse(BaseModel):
    """Response for Sovereign Macro View - global climate risk data."""
    countries: List[SovereignRiskCountry] = Field(..., description="Array of country climate risk data")


class TimelapseResponse(BaseModel):
    """Response for Climate Time-Lapse - global hazard projection tiles."""
    hazard: str = Field(..., description="Hazard type (heat, flood)")
    layers: Dict[str, str] = Field(..., description="Year to XYZ tile URL mapping")


# ==============================================================================
# Sovereign Risk - In-Memory Cache (24-hour expiration)
# ==============================================================================
_SOVEREIGN_RISK_CACHE = {
    "data": None,
    "timestamp": None,
    "ttl_hours": 24
}


def _authenticate_gee_sovereign():
    """Authenticate with Google Earth Engine for sovereign risk calculations."""
    credentials_dict = load_gee_credentials()
    if not credentials_dict:
        raise ValueError("Google Earth Engine credentials not found")
    
    credentials_json = json.dumps(credentials_dict)
    credentials = ee.ServiceAccountCredentials(
        credentials_dict['client_email'],
        key_data=credentials_json
    )
    ee.Initialize(credentials)


def calculate_global_sovereign_risk() -> List[Dict[str, Any]]:
    """
    Calculate climate risk scores for all countries using Google Earth Engine.
    
    This function performs a global spatial reduction to compute flood exposure
    for every country simultaneously. Results are cached for 24 hours to ensure
    fast frontend globe loading.
    
    GEE Processing Steps:
    1. Load global country boundaries (FAO GAUL 2015)
    2. Load JRC Global Surface Water (flood hazard proxy)
    3. Reduce regions to calculate mean water occurrence per country
    4. Normalize to 0-100 risk scores
    5. Format for frontend 3D globe visualization
    
    Returns:
        List of country risk dictionaries with country_code, country_name, 
        risk_score, and primary_vulnerability
    """
    # Check cache first
    if _SOVEREIGN_RISK_CACHE["data"] is not None and _SOVEREIGN_RISK_CACHE["timestamp"] is not None:
        cache_age_hours = (datetime.now() - _SOVEREIGN_RISK_CACHE["timestamp"]).total_seconds() / 3600
        if cache_age_hours < _SOVEREIGN_RISK_CACHE["ttl_hours"]:
            print(f"[Sovereign Risk] Using cached data (age: {cache_age_hours:.1f} hours)")
            return _SOVEREIGN_RISK_CACHE["data"]
    
    print("[Sovereign Risk] Computing fresh global risk scores via GEE...")
    
    try:
        # Authenticate GEE
        _authenticate_gee_sovereign()
        
        # 1. Load global country boundaries (FAO GAUL 2015 - level 0)
        countries = ee.FeatureCollection('FAO/GAUL/2015/level0')
        
        # 2. Load JRC Global Surface Water - flood hazard proxy
        # 'occurrence' band: percentage of time water is present (0-100%)
        flood_hazard = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
        
        # 3. Reduce regions: calculate mean water occurrence for each country
        # CRITICAL: Use scale=50000 (50km) to ensure fast global computation
        country_stats = flood_hazard.reduceRegions(
            collection=countries,
            reducer=ee.Reducer.mean(),
            scale=50000,  # 50km resolution for speed
            crs='EPSG:4326'
        )
        
        # 4. Extract results from GEE
        features = country_stats.getInfo()['features']
        
        # 5. Process and normalize data
        country_risk_data = []
        
        for feature in features:
            props = feature['properties']
            
            # Extract country metadata
            country_name = props.get('ADM0_NAME', 'Unknown')
            country_code = props.get('ADM0_CODE')  # FAO GAUL numeric code
            
            # Skip if no country code
            if not country_code:
                continue
            
            # Extract flood occurrence (mean percentage)
            flood_occurrence = props.get('mean', 0)
            if flood_occurrence is None:
                flood_occurrence = 0
            
            # Normalize to 0-100 risk score
            # Water occurrence of 50%+ = very high risk (score 80-100)
            # Water occurrence of 0% = low risk (score 0-20)
            # Apply exponential scaling to emphasize high-risk countries
            risk_score = min(100, int(flood_occurrence * 1.5 + 20))
            
            # Determine primary vulnerability based on risk score
            if risk_score >= 70:
                primary_vulnerability = "Coastal Flooding"
            elif risk_score >= 50:
                primary_vulnerability = "Riverine Flooding"
            elif risk_score >= 30:
                primary_vulnerability = "Agricultural Yield"
            else:
                primary_vulnerability = "Extreme Heat"
            
            # Convert FAO GAUL code to ISO 3-letter code (simplified mapping)
            # Note: This is a placeholder - production should use proper ISO mapping
            iso_code = _map_fao_to_iso(country_code, country_name)
            
            country_risk_data.append({
                "country_code": iso_code,
                "country_name": country_name,
                "risk_score": risk_score,
                "primary_vulnerability": primary_vulnerability
            })
        
        # Sort by risk score descending
        country_risk_data.sort(key=lambda x: x['risk_score'], reverse=True)
        
        # Update cache
        _SOVEREIGN_RISK_CACHE["data"] = country_risk_data
        _SOVEREIGN_RISK_CACHE["timestamp"] = datetime.now()
        
        print(f"[Sovereign Risk] Computed risk for {len(country_risk_data)} countries")
        
        return country_risk_data
    
    except Exception as e:
        print(f"[Sovereign Risk] GEE computation failed: {e}")
        raise


def _map_fao_to_iso(fao_code: int, country_name: str) -> str:
    """
    Map FAO GAUL country codes to ISO 3-letter codes.
    
    This is a simplified mapping for common countries. Production should use
    a complete ISO 3166-1 alpha-3 lookup table.
    """
    # Common country mappings (FAO code -> ISO 3)
    fao_to_iso = {
        1: "AFG",  # Afghanistan
        2: "ALB",  # Albania
        4: "DZA",  # Algeria
        7: "AGO",  # Angola
        10: "ARG",  # Argentina
        11: "ARM",  # Armenia
        12: "AUS",  # Australia
        14: "AUT",  # Austria
        16: "BGD",  # Bangladesh
        19: "BLR",  # Belarus
        20: "BEL",  # Belgium
        23: "BOL",  # Bolivia
        25: "BRA",  # Brazil
        31: "KHM",  # Cambodia
        32: "CMR",  # Cameroon
        33: "CAN",  # Canada
        39: "TCD",  # Chad
        40: "CHL",  # Chile
        41: "CHN",  # China
        44: "COL",  # Colombia
        49: "COD",  # DR Congo
        53: "CRI",  # Costa Rica
        55: "HRV",  # Croatia
        56: "CUB",  # Cuba
        59: "CZE",  # Czech Republic
        60: "DNK",  # Denmark
        63: "ECU",  # Ecuador
        65: "EGY",  # Egypt
        68: "ETH",  # Ethiopia
        73: "FIN",  # Finland
        75: "FRA",  # France
        79: "DEU",  # Germany
        82: "GHA",  # Ghana
        84: "GRC",  # Greece
        90: "HND",  # Honduras
        91: "HUN",  # Hungary
        93: "IND",  # India
        94: "IDN",  # Indonesia
        95: "IRN",  # Iran
        96: "IRQ",  # Iraq
        97: "IRL",  # Ireland
        98: "ISR",  # Israel
        99: "ITA",  # Italy
        101: "JAM",  # Jamaica
        102: "JPN",  # Japan
        103: "JOR",  # Jordan
        106: "KEN",  # Kenya
        110: "KOR",  # South Korea
        115: "LBN",  # Lebanon
        122: "MYS",  # Malaysia
        133: "MEX",  # Mexico
        143: "MAR",  # Morocco
        144: "MOZ",  # Mozambique
        145: "MMR",  # Myanmar
        147: "NPL",  # Nepal
        149: "NLD",  # Netherlands
        153: "NZL",  # New Zealand
        155: "NGA",  # Nigeria
        162: "NOR",  # Norway
        165: "PAK",  # Pakistan
        170: "PER",  # Peru
        171: "PHL",  # Philippines
        173: "POL",  # Poland
        174: "PRT",  # Portugal
        177: "ROU",  # Romania
        178: "RUS",  # Russia
        183: "SAU",  # Saudi Arabia
        189: "SGP",  # Singapore
        197: "ZAF",  # South Africa
        203: "ESP",  # Spain
        206: "SDN",  # Sudan
        209: "SWE",  # Sweden
        210: "CHE",  # Switzerland
        211: "SYR",  # Syria
        217: "THA",  # Thailand
        222: "TUR",  # Turkey
        226: "UGA",  # Uganda
        230: "UKR",  # Ukraine
        231: "ARE",  # UAE
        232: "GBR",  # United Kingdom
        236: "USA",  # United States
        238: "VEN",  # Venezuela
        240: "VNM",  # Vietnam
        245: "YEM",  # Yemen
        246: "ZMB",  # Zambia
        247: "ZWE",  # Zimbabwe
    }
    
    # Try numeric mapping first
    if fao_code in fao_to_iso:
        return fao_to_iso[fao_code]
    
    # Fallback: Generate 3-letter code from country name
    # Take first 3 letters, uppercase
    return country_name[:3].upper().replace(" ", "")


# ==============================================================================
# Climate Time-Lapse - In-Memory Cache (24-hour expiration)
# NOTE: Cache cleared 2026-03-12 to regenerate masked tiles
# ==============================================================================
_TIMELAPSE_CACHE = {}  # Key: hazard_type, Value: {"data": layers_dict, "timestamp": datetime}


def _authenticate_gee_timelapse():
    """Authenticate with Google Earth Engine for timelapse calculations."""
    credentials_dict = load_gee_credentials()
    if not credentials_dict:
        raise ValueError("Google Earth Engine credentials not found")
    
    credentials_json = json.dumps(credentials_dict)
    credentials = ee.ServiceAccountCredentials(
        credentials_dict['client_email'],
        key_data=credentials_json
    )
    ee.Initialize(credentials)


def calculate_climate_timelapse(hazard_type: str) -> Dict[str, str]:
    """
    Calculate global climate projection tile URLs for time-lapse visualization.
    
    This function generates Mapbox-compatible XYZ tile URLs for future climate
    projections using Google Earth Engine. Results are cached for 24 hours since
    Map IDs are identical for all users (global datasets, no bounding boxes).
    
    GEE Processing Steps:
    1. Load climate projection dataset (NASA NEX-GDDP or JRC for floods)
    2. Loop through target projection years: [2026, 2030, 2040, 2050]
    3. Filter image collection to each year and calculate mean
    4. Apply visualization parameters (color palette, min/max)
    5. Generate Map ID and extract tile URL
    
    Args:
        hazard_type: Climate hazard type ("heat" or "flood")
    
    Returns:
        Dictionary mapping year (str) to XYZ tile URL (str)
        Example: {"2026": "https://earthengine.googleapis.com/.../tiles/{z}/{x}/{y}"}
    """
    # Check cache first
    cache_key = hazard_type
    if cache_key in _TIMELAPSE_CACHE:
        cached = _TIMELAPSE_CACHE[cache_key]
        cache_age_hours = (datetime.now() - cached["timestamp"]).total_seconds() / 3600
        if cache_age_hours < 24:
            print(f"[Timelapse {hazard_type}] Using cached data (age: {cache_age_hours:.1f} hours)")
            return cached["data"]
    
    print(f"[Timelapse {hazard_type}] Computing fresh tile URLs via GEE...")
    
    try:
        # Authenticate GEE
        _authenticate_gee_timelapse()
        
        # Target projection years
        PROJECTION_YEARS = [2026, 2030, 2040, 2050]
        
        # Hazard-specific dataset and visualization parameters
        if hazard_type == "heat":
            # NASA NEX-GDDP: Downscaled climate projections (temperature)
            # Note: Using ERA5 as proxy since NEX-GDDP requires specific access
            # Production should use: ee.ImageCollection('NASA/NEX-GDDP')
            
            # For demo: Use ERA5 Land temperature as baseline
            # and add synthetic warming for future years
            baseline_year = 2020
            
            # Load baseline temperature (mean annual)
            baseline_temp = ee.ImageCollection('ECMWF/ERA5_LAND/MONTHLY') \
                .filterDate(f'{baseline_year}-01-01', f'{baseline_year}-12-31') \
                .select('temperature_2m') \
                .mean() \
                .subtract(273.15)  # Convert Kelvin to Celsius
            
            # Refined visualization parameters with transparent low values
            # Show only areas with significant warming (> 28°C threshold)
            vis_params = {
                'min': 28,    # Mask below 28°C (comfortable baseline)
                'max': 45,    # 45°C extreme heat
                'palette': ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']  # Yellow -> Red
            }
            
            layers = {}
            
            for year in PROJECTION_YEARS:
                # Synthetic warming: +0.2°C per year from baseline
                warming_offset = (year - baseline_year) * 0.2
                
                # Add warming projection
                projected_temp = baseline_temp.add(warming_offset)
                
                # CRITICAL: Apply mask to show only hazardous heat (> 28°C)
                # This makes safe/cool pixels transparent
                masked_temp = projected_temp.updateMask(projected_temp.gte(vis_params['min']))
                
                # Generate Map ID with visualization parameters
                map_id = masked_temp.getMapId(vis_params)
                
                # Extract tile URL
                tile_url = map_id['tile_fetcher'].url_format
                
                layers[str(year)] = tile_url
                print(f"[Timelapse heat] Generated masked tile URL for {year}")
        
        elif hazard_type == "flood":
            # JRC Global Surface Water - historical flood occurrence
            # For future projections, use increasing occurrence % as proxy
            
            # Load JRC base dataset
            base_flood = ee.Image('JRC/GSW1_4/GlobalSurfaceWater').select('occurrence')
            
            # Refined visualization parameters with transparent safe zones
            # Show only areas with significant flood risk (> 10% occurrence)
            vis_params = {
                'min': 10,     # Mask below 10% occurrence (safe zones)
                'max': 100,    # 100% water occurrence (permanent water)
                'palette': ['#c6dbef', '#6baed6', '#2171b5', '#08519c', '#08306b']  # Light Blue -> Dark Blue
            }
            
            layers = {}
            
            for year in PROJECTION_YEARS:
                # Synthetic flood increase: +1% per year from 2020
                flood_increase = (year - 2020) * 1.0
                
                # Project future flood occurrence
                projected_flood = base_flood.add(flood_increase).clamp(0, 100)
                
                # CRITICAL: Apply mask to show only flood-prone areas (> 10% occurrence)
                # This makes safe/dry pixels transparent
                masked_flood = projected_flood.updateMask(projected_flood.gte(vis_params['min']))
                
                # Generate Map ID with visualization parameters
                map_id = masked_flood.getMapId(vis_params)
                
                # Extract tile URL
                tile_url = map_id['tile_fetcher'].url_format
                
                layers[str(year)] = tile_url
                print(f"[Timelapse flood] Generated masked tile URL for {year}")
        
        else:
            raise ValueError(f"Unsupported hazard type: {hazard_type}. Supported: 'heat', 'flood'")
        
        # Update cache
        _TIMELAPSE_CACHE[cache_key] = {
            "data": layers,
            "timestamp": datetime.now()
        }
        
        print(f"[Timelapse {hazard_type}] Generated {len(layers)} tile layers")
        
        return layers
    
    except Exception as e:
        print(f"[Timelapse {hazard_type}] GEE computation failed: {e}")
        raise


app = FastAPI(title="AdaptMetric Simulation API", version="0.1.0")

# CORS configuration - aggressively permissive for development phase
# CRITICAL: This MUST be immediately after FastAPI() and before any routers/routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins temporarily for debugging
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth_router)


@app.on_event("startup")
async def _create_auth_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
def health() -> dict:
    return {
        "status": "awake",
        "environment": "production",
        "timestamp": datetime.now().isoformat()
    }


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


def _climate_stress_applies(global_warming: float, drought_index: float) -> bool:
    """True if global warming > 1.5°C or drought index is high (e.g. > 0.6)."""
    return (
        global_warming > GLOBAL_WARMING_STRESS_THRESHOLD
        or drought_index > DROUGHT_INDEX_HIGH_THRESHOLD
    )


def _current_crop_penalty_fraction(current_crop: str) -> float:
    """Return yield penalty fraction (0–1) for current crop under climate stress."""
    return CLIMATE_PENALTY_BY_CROP.get(current_crop, DEFAULT_CLIMATE_PENALTY)


# Minimum baseline yield value (USD) so dollar outputs are meaningful; use when payload omits or sends tiny value.
AGRI_BASELINE_YIELD_VALUE_FLOOR = 500_000.0


@app.post("/predict-agri", response_model=PredictAgriResponse)
def predict_agri(req: PredictAgriRequest) -> PredictAgriResponse:
    """Crop Switching What-If Engine: compare current crop yield under climate stress
    with a proposed alternative (e.g. Drought-Resistant Sorghum, Heat-Tolerant Wheat).
    Returns stressed yield, adjusted yield after switch, transition CAPEX, avoided revenue loss, and risk reduction %.
    """
    # Ensure baseline is a monetary base (USD): default to 500k if not provided or unreasonably small
    raw_baseline: float = float(req.baseline_yield_value)
    baseline: float = raw_baseline if raw_baseline >= 1000.0 else AGRI_BASELINE_YIELD_VALUE_FLOOR

    hectares: float = float(req.hectares)
    current_crop: str = req.current_crop.strip() or "Maize"
    proposed_crop: str = req.proposed_crop.strip() if req.proposed_crop else "None"
    if proposed_crop.lower() == "none":
        proposed_crop = "None"
    global_warming: float = float(req.global_warming)
    drought_index: float = float(req.drought_index)

    # 1. Baseline penalty (current crop): ALWAYS apply for Maize/Wheat so stressed yield reflects climate risk
    stress: bool = _climate_stress_applies(global_warming, drought_index)
    force_baseline_penalty: bool = current_crop.strip().lower() in ("maize", "wheat")
    apply_baseline_penalty: bool = stress or force_baseline_penalty
    stressed_penalty: float = _current_crop_penalty_fraction(current_crop) if apply_baseline_penalty else 0.0
    penalty_amount: float = baseline * stressed_penalty
    stressed_yield_value: float = baseline - penalty_amount

    # 2. Transition economics (proposed crop): CAPEX and adjusted yield with smaller penalty
    transition_capex: float = 0.0
    adjusted_yield_value: float = stressed_yield_value
    avoided_revenue_loss: float = 0.0
    adjusted_penalty: float = stressed_penalty

    if proposed_crop != "None" and proposed_crop in PROPOSED_CROP_ECONOMICS:
        capex_per_ha, proposed_penalty_fraction = PROPOSED_CROP_ECONOMICS[proposed_crop]
        transition_capex = capex_per_ha * hectares
        adjusted_penalty = proposed_penalty_fraction
        # Adjusted yield = baseline minus small penalty (e.g. 5% for Drought-Resistant Sorghum)
        adjusted_yield_value = baseline * (1.0 - proposed_penalty_fraction)
        avoided_revenue_loss = adjusted_yield_value - stressed_yield_value

    # 3. Risk reduction %: (stressed_penalty - adjusted_penalty) / stressed_penalty * 100, capped at 100%
    if stressed_penalty > 0:
        risk_reduction_pct: float = ((stressed_penalty - adjusted_penalty) / stressed_penalty) * 100.0
        risk_reduction_pct = min(100.0, max(0.0, risk_reduction_pct))
    else:
        risk_reduction_pct = 0.0

    return PredictAgriResponse(
        stressed_yield_value=round(stressed_yield_value, 2),
        adjusted_yield_value=round(adjusted_yield_value, 2),
        transition_capex=round(transition_capex, 2),
        avoided_revenue_loss=round(avoided_revenue_loss, 2),
        risk_reduction_pct=round(risk_reduction_pct, 2),
    )


@app.post("/simulate/coastal")
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
        # Dynamic Asset Depreciation: coastal penalty from sea level rise, rescue from e.g. Sea Wall
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


@app.post("/simulate/flood")
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
        # Dynamic Asset Depreciation: flood/agri penalty from global warming, rescue from e.g. Sponge City
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
        # Force lowercase and remove EVERYTHING except letters, numbers, and underscores
        df.columns = df.columns.astype(str).str.lower().str.replace(r'[^a-z0-9_]', '', regex=True)
        # Map the columns dynamically
        lat_col = next((c for c in df.columns if 'lat' in c), 'lat')
        lon_col = next((c for c in df.columns if 'lon' in c or 'lng' in c), 'lon')
        # Broaden the search for the value column
        val_col = next((c for c in df.columns if any(x in c for x in ['val', 'price', 'amount', 'cost', 'invest', 'usd'])), None)
        if not val_col and len(df.columns) > 2:
            val_col = df.columns[2]  # Fallback to 3rd column
        if not val_col:
            val_col = 'asset_value'  # So required_columns validation reports a known name
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
        for _, row in df.iterrows():
            raw_val = str(row.get(val_col, '0')).lower()
            # Handle text suffixes
            multiplier = 1
            if 'm' in raw_val:
                multiplier = 1000000
            elif 'k' in raw_val:
                multiplier = 1000
            elif 'b' in raw_val:
                multiplier = 1000000000
            # Strip EVERYTHING except numbers and decimals (removes $, commas, spaces)
            clean_val = re.sub(r'[^0-9.]', '', raw_val)
            try:
                val = float(clean_val) * multiplier if clean_val else 0.0
            except ValueError:
                val = 0.0
            lat = float(row.get(lat_col, 0.0))
            lon = float(row.get(lon_col, 0.0))
            crop = str(row.get(crop_col, 'unknown'))
            record = {
                "lat": lat,
                "lon": lon,
                "asset_value": val,
                "crop_type": crop,
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


@app.post("/api/v1/finance/cba-series")
def cba_series(req: CBARequest) -> dict:
    """Calculate a Cost-Benefit Analysis time series for a climate adaptation project.

    Compares a *Baseline* (no-action) scenario against an *Intervention* scenario
    over the project lifespan and returns per-year costs, net benefit, and summary
    metrics (NPV, ROI %, Breakeven Year).  Includes Green Bond financing,
    Parametric Insurance savings, and Carbon Credit revenue (Layered Value Stacking).
    """
    try:
        start_year = datetime.now().year

        # --- Bond financing metrics ---
        standard_rate = req.standard_interest_rate
        green_rate = req.standard_interest_rate - (req.greenium_discount_bps / 10_000)
        n = req.bond_tenor_years
        principal = req.capex

        def _annuity_payment(p: float, r: float, periods: int) -> float:
            """Standard loan amortization: PMT = P * r / (1 - (1+r)^-n)"""
            if r == 0:
                return p / periods
            return p * r / (1.0 - (1.0 + r) ** -periods)

        standard_annual_payment = _annuity_payment(principal, standard_rate, n)
        green_annual_payment = _annuity_payment(principal, green_rate, n)
        total_greenium_savings = (standard_annual_payment - green_annual_payment) * n

        # --- Insurance premiums ---
        baseline_insurance = req.base_insurance_premium
        adjusted_insurance_premium = req.base_insurance_premium * (1.0 - req.insurance_reduction_pct)

        # --- Carbon Credit revenue (Layered Value Stacking) ---
        annual_carbon_revenue = req.annual_carbon_credits * req.carbon_price_per_ton

        # --- Time-series accumulators ---
        baseline_cumulative = 0.0
        intervention_cumulative = req.capex  # Year-0 upfront cost (undiscounted)
        breakeven_year: Optional[int] = None
        time_series: list[dict] = []

        residual_damage = req.annual_baseline_damage * (1.0 - req.damage_reduction_pct)

        for yr in range(1, req.lifespan_years + 1):
            discount_factor = (1.0 + req.discount_rate) ** yr

            # Baseline: discounted (damage + full insurance premium)
            discounted_baseline = (req.annual_baseline_damage + baseline_insurance) / discount_factor
            baseline_cumulative += discounted_baseline

            # Intervention: discounted (opex + residual damage + reduced insurance - carbon revenue)
            intervention_annual_cost = (
                req.annual_opex + residual_damage + adjusted_insurance_premium - annual_carbon_revenue
            )
            discounted_intervention = intervention_annual_cost / discount_factor
            intervention_cumulative += discounted_intervention

            net_benefit = baseline_cumulative - intervention_cumulative

            if breakeven_year is None and net_benefit > 0:
                breakeven_year = yr

            time_series.append({
                "year": start_year + yr,
                "baseline_cost": round(baseline_cumulative, 2),
                "intervention_cost": round(intervention_cumulative, 2),
                "net_benefit": round(net_benefit, 2),
            })

        # --- Summary metrics ---
        final_net_benefit = baseline_cumulative - intervention_cumulative
        total_investment = req.capex + sum(
            (req.annual_opex + residual_damage + adjusted_insurance_premium - annual_carbon_revenue)
            / ((1.0 + req.discount_rate) ** yr)
            for yr in range(1, req.lifespan_years + 1)
        )
        total_roi_pct = (final_net_benefit / total_investment * 100.0) if total_investment > 0 else 0.0

        return {
            "status": "success",
            "summary_metrics": {
                "npv": round(final_net_benefit, 2),
                "total_roi_pct": round(total_roi_pct, 2),
                "breakeven_year": breakeven_year,
                "annual_carbon_revenue": round(annual_carbon_revenue, 2),
            },
            "bond_metrics": {
                "principal": principal,
                "standard_rate": round(standard_rate, 6),
                "green_rate": round(green_rate, 6),
                "standard_annual_payment": round(standard_annual_payment, 2),
                "green_annual_payment": round(green_annual_payment, 2),
                "total_greenium_savings": round(total_greenium_savings, 2),
            },
            "time_series": time_series,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/finance/cvar-simulation")
def cvar_simulation(req: CVaRRequest) -> dict:
    """Run a Monte Carlo simulation to estimate Climate Value at Risk (CVaR).

    Generates *num_simulations* random annual damage percentages from a normal
    distribution, floors them at zero, converts to monetary losses, and returns
    summary risk metrics plus a 40-bin histogram for frontend charting.
    """
    try:
        # Generate random damage percentages (normal distribution, floored at 0)
        damage_pcts = np.random.normal(
            req.mean_damage_pct, req.volatility_pct, req.num_simulations
        )
        damage_pcts = np.maximum(damage_pcts, 0.0)

        # Convert to monetary losses
        losses = damage_pcts * req.asset_value

        # Key risk metrics
        expected_loss = float(np.mean(losses))
        cvar_95 = float(np.percentile(losses, 95))
        cvar_99 = float(np.percentile(losses, 99))

        # 40-bin histogram for frontend charting
        counts, bin_edges = np.histogram(losses, bins=40)
        distribution = [
            {
                "loss_amount": round(float(bin_edges[i]), 2),
                "frequency": int(counts[i]),
            }
            for i in range(len(counts))
        ]

        return {
            "status": "success",
            "metrics": {
                "expected_loss": round(expected_loss, 2),
                "cvar_95": round(cvar_95, 2),
                "cvar_99": round(cvar_99, 2),
            },
            "distribution": distribution,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/finance/blended-structure", response_model=BlendedFinanceResponse)
def blended_finance_structure(req: BlendedFinanceRequest) -> BlendedFinanceResponse:
    """Calculate blended cost of capital with climate resilience-based interest rate discounts.
    
    This endpoint structures blended finance deals by:
    1. Applying "Greenium" discounts based on climate resilience score
    2. Calculating weighted average cost of capital across debt/grant/equity tranches
    3. Computing annual debt service and lifetime savings from green financing
    
    Use case: Determine optimal financing structure for climate adaptation projects
    with mixed public-private funding sources.
    """
    try:
        # --- Define Base Market Rates ---
        BASE_COMMERCIAL_RATE = 0.065  # 6.5%
        CONCESSIONAL_RATE = 0.020     # 2.0%
        MUNICIPAL_EQUITY_RATE = 0.0   # 0.0% (equity has no interest)
        
        LOAN_TERM_YEARS = 20
        
        # --- Apply Greenium Logic based on Resilience Score ---
        greenium_discount_bps = 0.0
        if req.resilience_score >= 80:
            greenium_discount_bps = 50.0  # 50 basis points
        elif req.resilience_score >= 60:
            greenium_discount_bps = 25.0  # 25 basis points
        
        greenium_discount = greenium_discount_bps / 10_000.0  # Convert bps to decimal
        applied_commercial_rate = BASE_COMMERCIAL_RATE - greenium_discount
        
        # --- Calculate Tranche Amounts ---
        commercial_debt_amount = req.total_capex * req.tranches.commercial_debt_pct
        concessional_grant_amount = req.total_capex * req.tranches.concessional_grant_pct
        municipal_equity_amount = req.total_capex * req.tranches.municipal_equity_pct
        
        # --- Calculate Blended Interest Rate (Weighted Average) ---
        # Equity doesn't contribute to interest rate calculation
        blended_interest_rate = (
            (req.tranches.commercial_debt_pct * applied_commercial_rate) +
            (req.tranches.concessional_grant_pct * CONCESSIONAL_RATE) +
            (req.tranches.municipal_equity_pct * MUNICIPAL_EQUITY_RATE)
        )
        
        # --- Calculate Debt Principal (Excludes Equity) ---
        # Equity doesn't need to be repaid, so exclude from loan calculations
        debt_principal = commercial_debt_amount + concessional_grant_amount
        
        # --- Calculate Annual Debt Service (Amortizing Loan) ---
        def calculate_annual_payment(principal: float, rate: float, periods: int) -> float:
            """Calculate annual payment for amortizing loan: PMT = P * r / (1 - (1+r)^-n)"""
            if rate == 0:
                return principal / periods
            return principal * rate / (1.0 - (1.0 + rate) ** -periods)
        
        if debt_principal > 0:
            annual_debt_service = calculate_annual_payment(
                debt_principal, blended_interest_rate, LOAN_TERM_YEARS
            )
        else:
            annual_debt_service = 0.0
        
        # --- Calculate Total Greenium Savings ---
        # Compare actual debt service vs. debt service at base commercial rate
        if commercial_debt_amount > 0:
            # Calculate what commercial debt portion would cost at base rate
            base_commercial_payment = calculate_annual_payment(
                commercial_debt_amount, BASE_COMMERCIAL_RATE, LOAN_TERM_YEARS
            )
            
            # Calculate what commercial debt portion costs at discounted rate
            discounted_commercial_payment = calculate_annual_payment(
                commercial_debt_amount, applied_commercial_rate, LOAN_TERM_YEARS
            )
            
            # Lifetime savings on commercial debt tranche
            annual_savings = base_commercial_payment - discounted_commercial_payment
            total_greenium_savings = annual_savings * LOAN_TERM_YEARS
        else:
            total_greenium_savings = 0.0
        
        # --- Insurance Premium Reduction (Resilience Dividend) ---
        # Insurers pass through 50% of risk reduction as premium savings
        INSURANCE_DISCOUNT_FACTOR = 0.50
        insurance_savings = req.base_insurance_premium * (req.risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR)
        adjusted_insurance_premium = req.base_insurance_premium - insurance_savings
        
        # --- Carbon Credit Revenue Integration ---
        # Calculate net debt service after offsetting with carbon revenue and insurance savings
        net_annual_debt_service = max(0.0, annual_debt_service - req.annual_carbon_revenue - insurance_savings)
        
        # --- Sensitivity Analysis (Rate Shock) ---
        sensitivity_analysis = None
        if req.rate_shock_bps is not None:
            # Apply rate shock to commercial debt portion only
            rate_shock_decimal = req.rate_shock_bps / 10_000.0  # Convert bps to decimal
            stressed_commercial_rate = applied_commercial_rate + rate_shock_decimal
            
            # Calculate stressed blended rate
            stressed_blended_rate = (
                (req.tranches.commercial_debt_pct * stressed_commercial_rate) +
                (req.tranches.concessional_grant_pct * CONCESSIONAL_RATE) +
                (req.tranches.municipal_equity_pct * MUNICIPAL_EQUITY_RATE)
            )
            
            # Calculate stressed annual debt service
            if debt_principal > 0:
                stressed_annual_payment = calculate_annual_payment(
                    debt_principal, stressed_blended_rate, LOAN_TERM_YEARS
                )
            else:
                stressed_annual_payment = 0.0
            
            # Calculate delta metrics
            debt_service_delta = stressed_annual_payment - annual_debt_service
            payment_increase_pct = (debt_service_delta / annual_debt_service * 100) if annual_debt_service > 0 else 0.0
            
            sensitivity_analysis = {
                "rate_shock_bps": req.rate_shock_bps,
                "stressed_commercial_rate": round(stressed_commercial_rate, 6),
                "stressed_blended_rate": round(stressed_blended_rate, 6),
                "base_annual_payment": round(annual_debt_service, 2),
                "stressed_annual_payment": round(stressed_annual_payment, 2),
                "debt_service_delta": round(debt_service_delta, 2),
                "payment_increase_pct": round(payment_increase_pct, 2),
                "lifetime_cost_increase": round(debt_service_delta * LOAN_TERM_YEARS, 2)
            }
        
        # --- Build Response ---
        return BlendedFinanceResponse(
            status="success",
            input_capex=req.total_capex,
            input_resilience_score=req.resilience_score,
            commercial_debt_amount=round(commercial_debt_amount, 2),
            concessional_grant_amount=round(concessional_grant_amount, 2),
            municipal_equity_amount=round(municipal_equity_amount, 2),
            base_commercial_rate=BASE_COMMERCIAL_RATE,
            applied_commercial_rate=round(applied_commercial_rate, 6),
            concessional_rate=CONCESSIONAL_RATE,
            municipal_equity_rate=MUNICIPAL_EQUITY_RATE,
            greenium_discount_bps=greenium_discount_bps,
            blended_interest_rate=round(blended_interest_rate, 6),
            annual_debt_service=round(annual_debt_service, 2),
            total_greenium_savings=round(total_greenium_savings, 2),
            annual_carbon_revenue=round(req.annual_carbon_revenue, 2),
            net_annual_debt_service=round(net_annual_debt_service, 2),
            insurance_savings=round(insurance_savings, 2),
            adjusted_insurance_premium=round(adjusted_insurance_premium, 2),
            loan_term_years=LOAN_TERM_YEARS,
            debt_principal=round(debt_principal, 2),
            sensitivity_analysis=sensitivity_analysis
        )
    
    except ValueError as e:
        # Handle tranche validation errors
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

# ---------------------------------------------------------------------------
# Legacy /predict-* routes (ported from Flask main.py)
# ---------------------------------------------------------------------------


def _legacy_error(status_code: int, message: str, code: str) -> JSONResponse:
    """Return a JSON error response matching the legacy Flask format."""
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message, "code": code},
    )


# Material Degradation Curves: interventions that reduce OPEX climate penalty by 85%
_OPEX_INTERVENTION_NAMES = frozenset(
    s.lower().replace(" ", "_").replace("-", "_")
    for s in ("Sea Wall", "Drainage Upgrade", "Sponge City")
)


def _has_opex_intervention(intervention: str) -> bool:
    """True if intervention protects asset and reduces OPEX climate penalty (85% reduction)."""
    if not intervention or not isinstance(intervention, str):
        return False
    normalized = intervention.strip().lower().replace(" ", "_").replace("-", "_")
    return normalized in _OPEX_INTERVENTION_NAMES or normalized == "sponge_city"


@app.get("/")
def index():
    return {"status": "active"}


@app.post("/get-hazard")
def get_hazard(req: GetHazardRequest):
    """Get climate hazard data for a location using GEE."""
    try:
        lat = req.lat
        lon = req.lon

        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        try:
            weather_data = get_weather_data(
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
            terrain_data = get_terrain_data(lat=lat, lon=lon)
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
        return _legacy_error(400, "Invalid numeric values for lat/lon", "INVALID_NUMERIC_VALUE")


@app.post("/predict")
def predict(req: PredictRequest):
    """Predict crop yield and calculate avoided loss.

    Supports two modes:
    - Mode A (Auto-Lookup): Provide lat/lon to fetch weather data from GEE
    - Mode B (Manual): Provide temp/rain directly
    """
    try:
        crop_type = req.crop_type.lower()

        if crop_type not in ("maize", "cocoa", "coffee"):
            return _legacy_error(
                400,
                f"Unsupported crop_type: {crop_type}. Supported crops: 'maize', 'cocoa', 'coffee'",
                "INVALID_CROP_TYPE",
            )

        if crop_type == "coffee" and coffee_pkl_model is None:
            return _legacy_error(
                500,
                "Coffee model file not found. Ensure coffee_model.pkl exists.",
                "MODEL_NOT_FOUND",
            )

        monthly_data = None
        has_location = False
        location_lat = 0.0
        location_lon = 0.0

        # Mode A: Auto-Lookup using lat/lon
        if req.lat is not None and req.lon is not None:
            lat = float(req.lat)
            lon = float(req.lon)

            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)

                weather_data = get_weather_data(
                    lat=lat, lon=lon,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                )

                base_temp = weather_data["max_temp_celsius"]
                base_rain = weather_data["total_precip_mm"]
                data_source = "gee_auto_lookup"

                try:
                    monthly_data = get_monthly_data(lat, lon)
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

        # Mode B: Manual fallback using temp/rain
        elif req.temp is not None and req.rain is not None:
            base_temp = float(req.temp)
            base_rain = float(req.rain)
            data_source = "manual"

        else:
            return _legacy_error(
                400,
                "Missing required fields: provide either (lat, lon) or (temp, rain)",
                "MISSING_FIELDS",
            )

        temp_increase = float(req.temp_increase)
        rain_change = float(req.rain_change)

        final_simulated_temp = base_temp + temp_increase
        rain_modifier = 1.0 + (rain_change / 100.0)
        final_simulated_rain = max(0.0, base_rain * rain_modifier)

        # === COFFEE MODEL PREDICTION ===
        if crop_type == "coffee":
            elevation = float(
                req.elevation if req.elevation is not None
                else (req.elevation_m if req.elevation_m is not None else 1200.0)
            )
            soil_ph = float(req.soil_ph if req.soil_ph is not None else 6.0)

            if has_location and req.elevation is None and req.elevation_m is None:
                try:
                    terrain_data = get_terrain_data(lat=location_lat, lon=location_lon)
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
                        "baseline_temp_c": round(baseline_temp_c, 2),
                        "temp_anomaly_c": round(temp_anomaly_c, 2),
                        "rainfall_mm": round(rainfall_mm, 2),
                        "rain_anomaly_mm": round(rain_anomaly_mm, 2),
                        "elevation_m": round(elevation, 2),
                        "soil_ph": round(soil_ph, 2),
                        "data_source": data_source,
                        "crop_type": crop_type,
                    },
                    "prediction": {
                        "yield_impact_pct": round(yield_impact, 4),
                        "yield_impact_category": (
                            "optimal" if yield_impact >= 0.8 else
                            "good" if yield_impact >= 0.6 else
                            "moderate" if yield_impact >= 0.4 else
                            "poor" if yield_impact >= 0.2 else
                            "critical"
                        ),
                    },
                    "interpretation": {
                        "description": f"Under current conditions, expected yield is {yield_impact * 100:.1f}% of maximum potential.",
                        "risk_factors": [],
                    },
                },
            }

        # === MAIZE/COCOA PREDICTION ===
        standard_yield = calculate_yield(
            temp=base_temp, rain=base_rain,
            seed_type=SEED_TYPES["standard"],
            crop_type=crop_type,
            temp_delta=temp_increase,
            rain_pct_change=rain_change,
        )

        resilient_yield = calculate_yield(
            temp=base_temp, rain=base_rain,
            seed_type=SEED_TYPES["resilient"],
            crop_type=crop_type,
            temp_delta=temp_increase,
            rain_pct_change=rain_change,
        )

        avoided_loss = resilient_yield - standard_yield
        percentage_improvement = (avoided_loss / standard_yield) * 100 if standard_yield > 0 else 0.0

        # Financial ROI Analysis
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
            "assumptions": {
                "capex": capex,
                "opex": opex,
                "yield_benefit_pct": yield_benefit_pct,
                "price_per_ton": price_per_ton,
                "discount_rate_pct": discount_rate * 100,
                "analysis_years": analysis_years,
            },
        }

        # Spatial analysis (only when location and climate perturbation are present)
        spatial_analysis = None
        if has_location and temp_increase != 0.0:
            try:
                print(f"[SPATIAL] Running spatial analysis for lat={location_lat}, lon={location_lon}, temp_increase={temp_increase}", file=sys.stderr, flush=True)
                spatial_analysis = analyze_spatial_viability(location_lat, location_lon, temp_increase)
                print(f"[SPATIAL] Complete: {spatial_analysis}", file=sys.stderr, flush=True)
            except Exception as spatial_error:
                print(f"Spatial analysis error: {spatial_error}", file=sys.stderr, flush=True)

        # Chart data from monthly GEE observations
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
            "input_conditions": {
                "max_temp_celsius": base_temp,
                "total_rain_mm": base_rain,
                "data_source": data_source,
                "crop_type": crop_type,
            },
            "predictions": {
                "standard_seed": {
                    "type_code": SEED_TYPES["standard"],
                    "predicted_yield": round(standard_yield, 2),
                },
                "resilient_seed": {
                    "type_code": SEED_TYPES["resilient"],
                    "predicted_yield": round(resilient_yield, 2),
                },
            },
            "analysis": {
                "avoided_loss": round(avoided_loss, 2),
                "percentage_improvement": round(percentage_improvement, 2),
                "recommendation": "resilient" if avoided_loss > 0 else "standard",
            },
            "simulation_debug": {
                "raw_temp": round(base_temp, 2),
                "perturbation_added": round(temp_increase, 2),
                "final_simulated_temp": round(final_simulated_temp, 2),
                "raw_rain": round(base_rain, 2),
                "rain_modifier": round(rain_change, 2),
                "final_simulated_rain": round(final_simulated_rain, 2),
            },
        }

        if chart_data is not None:
            response_data["chart_data"] = chart_data
        if spatial_analysis is not None:
            response_data["spatial_analysis"] = spatial_analysis
        if roi_analysis is not None:
            response_data["roi_analysis"] = roi_analysis

        return {"status": "success", "data": response_data}

    except ValueError:
        return _legacy_error(400, "Invalid numeric values for temp/rain", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return _legacy_error(500, f"Prediction failed: {str(e)}", "PREDICTION_ERROR")


@app.post("/predict-coastal")
def predict_coastal(req: PredictCoastalRunupRequest):
    """Predict coastal runup elevation with and without mangrove protection."""
    if coastal_pkl_model is None:
        return _legacy_error(500, "Coastal model file not found. Ensure coastal_surrogate.pkl exists.", "MODEL_NOT_FOUND")

    try:
        print(f"DEBUG PAYLOAD: OPEX={req.base_annual_opex}, Lifespan={req.initial_lifespan_years}, GreenRoofs={req.green_roofs}", flush=True)
        lat = req.lat
        lon = req.lon
        mangrove_width = req.mangrove_width
        initial_lifespan_years = req.initial_lifespan_years
        sea_level_rise = req.sea_level_rise
        intervention = req.intervention.strip()
        daily_revenue = req.daily_revenue
        expected_downtime_days = req.expected_downtime_days

        print(f"[COASTAL REQUEST] lat={lat}, lon={lon}, mangrove_width={mangrove_width}", file=sys.stderr, flush=True)

        # Math uses request variables: initial_lifespan_years, intervention (no hardcoded defaults)
        raw_penalty = coastal_lifespan_penalty(sea_level_rise)
        has_intervention_rescue = coastal_has_intervention_rescue(intervention)
        adjusted_lifespan, lifespan_penalty = apply_lifespan_depreciation(
            initial_lifespan_years, raw_penalty, has_intervention_rescue
        )

        if 0 < mangrove_width < 10:
            print(f"[WARNING] Mangrove width {mangrove_width}m is below minimum effective width. Using 10m minimum.", file=sys.stderr, flush=True)
            mangrove_width = 10

        coastal_data = get_coastal_params(lat, lon)
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
        interruption = calculate_avoided_business_interruption(
            daily_revenue=daily_revenue,
            expected_downtime_days=expected_downtime_days,
            has_intervention=has_intervention,
        )

        # Material Degradation Curves: adjusted_opex uses request base_annual_opex and intervention (no hardcoded defaults)
        base_annual_opex: float = float(req.base_annual_opex)
        if sea_level_rise > 1.0:
            opex_penalty_pct = 0.30
        elif sea_level_rise > 0.5:
            opex_penalty_pct = 0.15
        else:
            opex_penalty_pct = 0.0
        opex_climate_penalty: float = base_annual_opex * opex_penalty_pct
        if _has_opex_intervention(intervention):
            opex_climate_penalty *= 0.15  # 85% reduction
        adjusted_opex: float = base_annual_opex + opex_climate_penalty

        return {
            "status": "success",
            "data": {
                "input_conditions": {
                    "lat": lat,
                    "lon": lon,
                    "mangrove_width_m": mangrove_width,
                    "initial_lifespan_years": initial_lifespan_years,
                    "sea_level_rise_m": sea_level_rise,
                    "intervention": intervention or None,
                    "base_annual_opex": base_annual_opex,
                    "daily_revenue": daily_revenue,
                    "expected_downtime_days": expected_downtime_days,
                },
                "coastal_params": {
                    "detected_slope_pct": round(slope, 2),
                    "storm_wave_height": round(wave_height, 2),
                },
                "predictions": {
                    "baseline_runup": round(runup_a, 4),
                    "protected_runup": round(runup_b, 4),
                },
                "analysis": {
                    "avoided_loss": round(avoided_damage_usd, 2),
                    "avoided_runup_m": round(avoided_runup, 4),
                    "percentage_improvement": round(percentage_improvement, 2),
                    "recommendation": "with_mangroves" if avoided_runup > 0 else "baseline",
                    "avoided_business_interruption": interruption["avoided_business_interruption"],
                },
                "asset_depreciation": {
                    "adjusted_lifespan": adjusted_lifespan,
                    "lifespan_penalty": lifespan_penalty,
                },
                "material_degradation_opex": {
                    "adjusted_opex": round(adjusted_opex, 2),
                    "opex_climate_penalty": round(opex_climate_penalty, 2),
                },
                "economic_assumptions": {
                    "damage_cost_per_meter": DAMAGE_COST_PER_METER,
                    "num_properties": NUM_PROPERTIES,
                    "total_value_basis": "USD per meter of flood reduction \u00d7 properties affected",
                },
                "slope": round(slope / 100, 4),
                "storm_wave": round(wave_height, 2),
                "avoided_loss": round(avoided_damage_usd, 2),
                "avoided_business_interruption": interruption["avoided_business_interruption"],
                "adjusted_opex": round(adjusted_opex, 2),
                "opex_climate_penalty": round(opex_climate_penalty, 2),
            },
        }

    except ValueError:
        return _legacy_error(400, "Invalid numeric values for lat/lon/mangrove_width", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return _legacy_error(500, f"Prediction failed: {str(e)}", "PREDICTION_ERROR")


@app.post("/predict-coastal-flood")
def predict_coastal_flood(req: PredictCoastalFloodRequest):
    """Predict coastal flood risk based on sea level rise and storm surge."""
    try:
        lat = req.lat
        lon = req.lon
        slr_projection = req.slr_projection
        include_surge = req.include_surge
        initial_lifespan_years = req.initial_lifespan_years

        intervention_raw = (
            ((req.intervention_params or {}).get("type"))
            or req.intervention
            or ""
        )
        intervention_str = str(intervention_raw).strip() if intervention_raw else ""

        print(f"[COASTAL FLOOD REQUEST] lat={lat}, lon={lon}, slr_projection={slr_projection}, include_surge={include_surge}", file=sys.stderr, flush=True)

        raw_penalty = coastal_lifespan_penalty(slr_projection)
        has_intervention_rescue = coastal_has_intervention_rescue(intervention_str)
        adjusted_lifespan, lifespan_penalty = apply_lifespan_depreciation(
            initial_lifespan_years, raw_penalty, has_intervention_rescue
        )

        if slr_projection < 0:
            return _legacy_error(400, "Sea level rise projection must be non-negative", "INVALID_SLR_PROJECTION")

        surge_m = 2.5 if include_surge else 0.0
        total_water_level = slr_projection + surge_m

        flood_risk = analyze_flood_risk(lat, lon, slr_projection, surge_m)

        spatial_analysis = None
        try:
            print(f"[SPATIAL] Running urban impact analysis for lat={lat}, lon={lon}, water_level={total_water_level}m", file=sys.stderr, flush=True)
            spatial_analysis = analyze_urban_impact(lat, lon, total_water_level)
            print(f"[SPATIAL] Complete: {spatial_analysis}", file=sys.stderr, flush=True)
        except Exception as spatial_error:
            print(f"Spatial analysis error: {spatial_error}", file=sys.stderr, flush=True)

        response_data: Dict[str, Any] = {
            "input_conditions": {
                "lat": lat,
                "lon": lon,
                "slr_projection_m": slr_projection,
                "include_surge": include_surge,
                "surge_m": surge_m,
                "total_water_level_m": total_water_level,
                "initial_lifespan_years": initial_lifespan_years,
                "intervention": intervention_str or None,
            },
            "flood_risk": flood_risk,
            "asset_depreciation": {
                "adjusted_lifespan": adjusted_lifespan,
                "lifespan_penalty": lifespan_penalty,
            },
        }

        if spatial_analysis is not None:
            response_data["spatial_analysis"] = spatial_analysis

        # Infrastructure ROI Analysis (optional)
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
                    print(f"[INFRASTRUCTURE ROI] Calculating for flood_depth={flood_depth}m, asset_value=${asset_value}, intervention={intervention_type}", file=sys.stderr, flush=True)
                    infrastructure_roi = calculate_infrastructure_roi(
                        flood_depth_m=flood_depth,
                        asset_value=asset_value,
                        daily_revenue=daily_revenue,
                        project_capex=capex,
                        project_opex=opex,
                        intervention_type=intervention_type,
                        analysis_years=20,
                        discount_rate=0.10,
                        wall_height_m=intervention_params.get("wall_height_m", 2.0),
                        drainage_reduction_m=intervention_params.get("drainage_reduction_m", 0.3),
                    )
                    print(f"[INFRASTRUCTURE ROI] Complete: NPV=${infrastructure_roi['financial_analysis']['npv']:,.0f}, BCR={infrastructure_roi['financial_analysis']['bcr']:.2f}", file=sys.stderr, flush=True)
            except Exception as roi_error:
                print(f"Infrastructure ROI error: {roi_error}", file=sys.stderr, flush=True)

        if infrastructure_roi is not None:
            response_data["infrastructure_roi"] = infrastructure_roi

        # Social Impact Analysis (optional)
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
                    social_metrics = calculate_social_metrics(
                        people_at_risk=beneficiaries["people_at_risk"],
                        households_at_risk=beneficiaries["households_at_risk"],
                        intervention_cost=intervention_cost,
                        nature_value=nature_value,
                    )

                impact_metrics: Dict[str, Any] = {"beneficiaries": beneficiaries}
                if nature_value is not None:
                    impact_metrics["nature_value"] = nature_value
                if social_metrics is not None:
                    impact_metrics["social_metrics"] = social_metrics

                print(f"[SOCIAL IMPACT] Beneficiaries: {beneficiaries['people_at_risk']} people, {beneficiaries['households_at_risk']} households", file=sys.stderr, flush=True)
            except Exception as social_error:
                print(f"Social impact analysis error: {social_error}", file=sys.stderr, flush=True)

        if impact_metrics is not None:
            response_data["impact_metrics"] = impact_metrics

        return {"status": "success", "data": response_data}

    except ValueError:
        return _legacy_error(400, "Invalid numeric values for lat/lon/slr_projection", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return _legacy_error(500, f"Flood risk analysis failed: {str(e)}", "FLOOD_RISK_ERROR")


@app.post("/predict-flash-flood")
def predict_flash_flood(req: PredictFlashFloodRequest):
    """Predict flash flood risk using Topographic Wetness Index (TWI) model."""
    try:
        lat = req.lat
        lon = req.lon
        rain_intensity_pct = req.rain_intensity_pct

        print(f"[FLASH FLOOD REQUEST] lat={lat}, lon={lon}, rain_intensity_pct={rain_intensity_pct}", file=sys.stderr, flush=True)

        flash_flood_analysis = analyze_flash_flood(lat, lon, rain_intensity_pct)
        rainfall_frequency = calculate_rainfall_frequency(rain_intensity_pct)

        spatial_analysis = None
        try:
            print(f"[SPATIAL] Running infrastructure risk analysis for lat={lat}, lon={lon}, rain_intensity={rain_intensity_pct}%", file=sys.stderr, flush=True)
            spatial_analysis = analyze_infrastructure_risk(lat, lon, rain_intensity_pct)
            print(f"[SPATIAL] Complete: {spatial_analysis}", file=sys.stderr, flush=True)
        except Exception as spatial_error:
            print(f"Infrastructure risk analysis error: {spatial_error}", file=sys.stderr, flush=True)

        response_data: Dict[str, Any] = {
            "input_conditions": {
                "lat": lat,
                "lon": lon,
                "rain_intensity_increase_pct": rain_intensity_pct,
            },
            "flash_flood_analysis": flash_flood_analysis,
            "analytics": rainfall_frequency,
        }

        if spatial_analysis is not None:
            response_data["spatial_analysis"] = spatial_analysis

        # Infrastructure ROI Analysis (optional)
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
                    print(f"[INFRASTRUCTURE ROI] Calculating for estimated_depth={estimated_flood_depth}m, asset_value=${asset_value}, intervention={intervention_type}", file=sys.stderr, flush=True)
                    infrastructure_roi = calculate_infrastructure_roi(
                        flood_depth_m=estimated_flood_depth,
                        asset_value=asset_value,
                        daily_revenue=daily_revenue,
                        project_capex=capex,
                        project_opex=opex,
                        intervention_type=intervention_type,
                        analysis_years=20,
                        discount_rate=0.10,
                        wall_height_m=intervention_params.get("wall_height_m", 2.0),
                        drainage_reduction_m=intervention_params.get("drainage_reduction_m", 0.3),
                    )
                    print(f"[INFRASTRUCTURE ROI] Complete: NPV=${infrastructure_roi['financial_analysis']['npv']:,.0f}, BCR={infrastructure_roi['financial_analysis']['bcr']:.2f}", file=sys.stderr, flush=True)
            except Exception as roi_error:
                print(f"Infrastructure ROI error: {roi_error}", file=sys.stderr, flush=True)

        if infrastructure_roi is not None:
            response_data["infrastructure_roi"] = infrastructure_roi

        # Social Impact Analysis (optional)
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
                    social_metrics = calculate_social_metrics(
                        people_at_risk=beneficiaries["people_at_risk"],
                        households_at_risk=beneficiaries["households_at_risk"],
                        intervention_cost=intervention_cost,
                        nature_value=nature_value,
                    )

                impact_metrics: Dict[str, Any] = {"beneficiaries": beneficiaries}
                if nature_value is not None:
                    impact_metrics["nature_value"] = nature_value
                if social_metrics is not None:
                    impact_metrics["social_metrics"] = social_metrics

                print(f"[SOCIAL IMPACT] Beneficiaries: {beneficiaries['people_at_risk']} people, {beneficiaries['households_at_risk']} households", file=sys.stderr, flush=True)
            except Exception as social_error:
                print(f"Social impact analysis error: {social_error}", file=sys.stderr, flush=True)

        if impact_metrics is not None:
            response_data["impact_metrics"] = impact_metrics

        return {"status": "success", "data": response_data}

    except ValueError:
        return _legacy_error(400, "Invalid numeric values for lat/lon/rain_intensity_pct", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return _legacy_error(500, f"Flash flood analysis failed: {str(e)}", "FLASH_FLOOD_ERROR")


@app.post("/predict-flood")
def predict_flood(req: PredictUrbanFloodRequest):
    """Predict urban flood depth with and without green infrastructure intervention."""
    if flood_pkl_model is None:
        return _legacy_error(500, "Flood model file not found. Ensure flood_surrogate.pkl exists.", "MODEL_NOT_FOUND")

    try:
        print(f"DEBUG PAYLOAD: OPEX={req.base_annual_opex}, Lifespan={req.initial_lifespan_years}, GreenRoofs={req.green_roofs}", flush=True)
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

        print(f"[FLOOD REQUEST] rain={rain_intensity}, impervious={current_imperviousness}, intervention={intervention_type}, slope={slope_pct}, building_value=${building_value}, num_buildings={num_buildings}", file=sys.stderr, flush=True)

        # Math uses request variables: initial_lifespan_years, intervention_type (no hardcoded defaults)
        raw_penalty = flood_lifespan_penalty(global_warming)
        has_intervention_rescue = flood_has_intervention_rescue(intervention_type)
        adjusted_lifespan, lifespan_penalty = apply_lifespan_depreciation(
            initial_lifespan_years, raw_penalty, has_intervention_rescue
        )

        # Material Degradation Curves: adjusted_opex uses request base_annual_opex and intervention_type (no hardcoded defaults)
        base_annual_opex: float = float(req.base_annual_opex)
        if global_warming > 2.0:
            opex_penalty_pct = 0.25
        elif global_warming > 1.5:
            opex_penalty_pct = 0.12
        else:
            opex_penalty_pct = 0.0
        opex_climate_penalty: float = base_annual_opex * opex_penalty_pct
        if _has_opex_intervention(intervention_type):
            opex_climate_penalty *= 0.15  # 85% reduction
        adjusted_opex: float = base_annual_opex + opex_climate_penalty

        if not (10 <= rain_intensity <= 150):
            return _legacy_error(400, "Rain intensity must be between 10 and 150 mm/hr", "INVALID_RAIN_INTENSITY")
        if not (0.0 <= current_imperviousness <= 1.0):
            return _legacy_error(400, "Current imperviousness must be between 0.0 and 1.0", "INVALID_IMPERVIOUSNESS")
        if not (0.1 <= slope_pct <= 10.0):
            return _legacy_error(400, "Slope must be between 0.1 and 10.0 percent", "INVALID_SLOPE")

        INTERVENTION_FACTORS = {
            "green_roof": 0.30,
            "permeable_pavement": 0.40,
            "bioswales": 0.25,
            "rain_gardens": 0.20,
            "sponge_city": 0.35,
            "sponge city": 0.35,
            "none": 0.0,
        }

        if intervention_type not in INTERVENTION_FACTORS:
            return _legacy_error(
                400,
                f"Invalid intervention type. Must be one of: {', '.join(INTERVENTION_FACTORS.keys())}",
                "INVALID_INTERVENTION_TYPE",
            )

        baseline_df = pd.DataFrame({
            "rain_intensity_mm_hr": [rain_intensity],
            "impervious_pct": [current_imperviousness],
            "slope_pct": [slope_pct],
        })

        reduction_factor = INTERVENTION_FACTORS[intervention_type]
        intervention_imperviousness = max(0.0, current_imperviousness - reduction_factor)

        intervention_df = pd.DataFrame({
            "rain_intensity_mm_hr": [rain_intensity],
            "impervious_pct": [intervention_imperviousness],
            "slope_pct": [slope_pct],
        })

        depth_baseline = float(flood_pkl_model.predict(baseline_df)[0])
        depth_intervention = float(flood_pkl_model.predict(intervention_df)[0])

        avoided_depth_cm = depth_baseline - depth_intervention
        percentage_improvement = (avoided_depth_cm / depth_baseline * 100) if depth_baseline > 0 else 0

        def _flood_damage_pct(depth_cm: float) -> float:
            """Urban flood depth-damage curve (Huizinga et al., 2017)."""
            if depth_cm <= 0:
                return 0.0
            if depth_cm < 5:
                return (depth_cm / 5.0) * 2.0
            if depth_cm < 15:
                return 2.0 + 6.0 * ((depth_cm - 5) / 10.0)
            if depth_cm < 30:
                return 8.0 + 12.0 * ((depth_cm - 15) / 15.0)
            if depth_cm < 60:
                return 20.0 + 20.0 * ((depth_cm - 30) / 30.0)
            return min(40.0 + 30.0 * min((depth_cm - 60) / 60.0, 1.0), 70.0)

        baseline_damage_pct = _flood_damage_pct(depth_baseline)
        intervention_damage_pct = _flood_damage_pct(depth_intervention)
        avoided_damage_pct = baseline_damage_pct - intervention_damage_pct
        avoided_damage_usd = (avoided_damage_pct / 100) * num_buildings * building_value

        from infrastructure_engine import calculate_avoided_business_interruption
        has_intervention = intervention_type != "none"
        interruption = calculate_avoided_business_interruption(
            daily_revenue=daily_revenue,
            expected_downtime_days=expected_downtime_days,
            has_intervention=has_intervention,
        )

        return {
            "status": "success",
            "data": {
                "input_conditions": {
                    "rain_intensity_mm_hr": rain_intensity,
                    "current_imperviousness": current_imperviousness,
                    "intervention_type": intervention_type,
                    "slope_pct": slope_pct,
                    "building_value": building_value,
                    "num_buildings": num_buildings,
                    "initial_lifespan_years": initial_lifespan_years,
                    "global_warming_c": global_warming,
                    "base_annual_opex": base_annual_opex,
                    "daily_revenue": daily_revenue,
                    "expected_downtime_days": expected_downtime_days,
                },
                "asset_depreciation": {
                    "adjusted_lifespan": adjusted_lifespan,
                    "lifespan_penalty": lifespan_penalty,
                },
                "material_degradation_opex": {
                    "adjusted_opex": round(adjusted_opex, 2),
                    "opex_climate_penalty": round(opex_climate_penalty, 2),
                },
                "imperviousness_change": {
                    "baseline": round(current_imperviousness, 3),
                    "intervention": round(intervention_imperviousness, 3),
                    "reduction_factor": reduction_factor,
                    "absolute_reduction": round(current_imperviousness - intervention_imperviousness, 3),
                },
                "predictions": {
                    "baseline_depth_cm": round(depth_baseline, 2),
                    "intervention_depth_cm": round(depth_intervention, 2),
                },
                "analysis": {
                    "avoided_depth_cm": round(avoided_depth_cm, 2),
                    "percentage_improvement": round(percentage_improvement, 2),
                    "baseline_damage_pct": round(baseline_damage_pct, 2),
                    "intervention_damage_pct": round(intervention_damage_pct, 2),
                    "avoided_damage_pct": round(avoided_damage_pct, 2),
                    "avoided_loss": round(avoided_damage_usd, 2),
                    "recommendation": intervention_type if avoided_depth_cm > 0 else "none",
                    "avoided_business_interruption": interruption["avoided_business_interruption"],
                },
                "economic_assumptions": {
                    "num_buildings": num_buildings,
                    "avg_building_value": building_value,
                    "total_value_at_risk": num_buildings * building_value,
                    "damage_function": "Urban Flood Damage (Huizinga et al., 2017)",
                    "total_value_basis": "Avoided structural damage across affected buildings",
                },
                "depth_baseline": round(depth_baseline, 2),
                "depth_intervention": round(depth_intervention, 2),
                "avoided_loss": round(avoided_damage_usd, 2),
                "avoided_business_interruption": interruption["avoided_business_interruption"],
                "adjusted_opex": round(adjusted_opex, 2),
                "opex_climate_penalty": round(opex_climate_penalty, 2),
            },
        }

    except ValueError as ve:
        return _legacy_error(400, f"Invalid numeric values: {str(ve)}", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return _legacy_error(500, f"Prediction failed: {str(e)}", "PREDICTION_ERROR")


@app.post("/start-batch")
def start_batch(req: StartBatchRequest):
    """Start a background batch processing job for portfolio assets."""
    try:
        job_id = req.job_id

        thread = threading.Thread(
            target=run_batch_job,
            args=(job_id,),
            daemon=True,
        )
        thread.start()

        print(f"[API] Started batch job {job_id} in background thread", file=sys.stderr, flush=True)

        return JSONResponse(
            status_code=202,
            content={
                "status": "started",
                "job_id": job_id,
                "message": "Batch processing started in background. Check batch_jobs table for status.",
            },
        )

    except Exception as e:
        return _legacy_error(500, f"Failed to start batch job: {str(e)}", "BATCH_START_ERROR")


@app.post("/calculate-financials")
def calculate_financials(req: CalculateFinancialsRequest):
    """Calculate financial metrics (NPV, BCR, Payback Period) from cash flows."""
    try:
        cash_flows = [float(cf) for cf in req.cash_flows]
        discount_rate = float(req.discount_rate)

        metrics = calculate_roi_metrics(cash_flows, discount_rate)

        return {
            "status": "success",
            "data": {
                "input": {
                    "cash_flows": cash_flows,
                    "discount_rate": discount_rate,
                    "discount_rate_pct": round(discount_rate * 100, 2),
                },
                "metrics": metrics,
                "interpretation": {
                    "npv_positive": metrics["npv"] > 0,
                    "bcr_favorable": metrics["bcr"] > 1.0,
                    "recommendation": "INVEST" if metrics["npv"] > 0 and metrics["bcr"] > 1.0 else "DO NOT INVEST",
                },
            },
        }

    except ValueError as ve:
        return _legacy_error(400, f"Invalid numeric values: {str(ve)}", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return _legacy_error(500, f"Financial calculation failed: {str(e)}", "CALCULATION_ERROR")


@app.post("/predict-health")
def predict_health(req: PredictHealthRequest):
    """Predict climate-related health impacts including heat stress and malaria risk.
    
    Now includes Cooling CAPEX vs. Productivity OPEX Cost-Benefit Analysis.
    
    Cooling interventions reduce WBGT (Wet Bulb Globe Temperature) which improves
    worker productivity. The analysis calculates:
    - Avoided productivity loss from cooling
    - Simple payback period (CAPEX / Net Annual Benefit)
    - 10-year NPV at 10% discount rate
    
    Intervention types:
    - hvac_retrofit: Active cooling system (drops WBGT to safe 22°C)
    - passive_cooling: Passive design improvements (drops WBGT by 3°C)
    - none: No intervention (baseline scenario)
    """
    try:
        from health_engine import calculate_productivity_loss, calculate_malaria_risk, calculate_health_economic_impact, calculate_public_health_impact

        lat = req.lat
        lon = req.lon
        workforce_size = req.workforce_size
        daily_wage = req.daily_wage
        
        # Cooling intervention parameters
        intervention_type = req.intervention_type or "none"
        intervention_capex = req.intervention_capex or 0.0
        intervention_annual_opex = req.intervention_annual_opex or 0.0
        
        # Public health (DALY) parameters
        population_size = req.population_size or 100000
        gdp_per_capita_usd = req.gdp_per_capita_usd or 8500.0
        
        # Healthcare Infrastructure Stress Testing parameters
        economy_tier = (req.economy_tier or "middle").lower()
        user_beds_per_1000 = req.user_beds_per_1000
        user_cost_per_bed = req.user_cost_per_bed

        print(f"[HEALTH REQUEST] lat={lat}, lon={lon}, workforce={workforce_size}, wage=${daily_wage}, intervention={intervention_type}, population={population_size}, gdp_per_capita=${gdp_per_capita_usd}, economy_tier={economy_tier}", file=sys.stderr, flush=True)

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            weather_data = get_weather_data(
                lat=lat, lon=lon,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
            )

            temp_c = weather_data["max_temp_celsius"]
            precip_mm = weather_data["total_precip_mm"]

            if precip_mm < 500:
                humidity_pct = 50.0
            elif precip_mm < 1000:
                humidity_pct = 65.0
            else:
                humidity_pct = 80.0

            print(f"[HEALTH] Climate data: temp={temp_c}°C, precip={precip_mm}mm, humidity_est={humidity_pct}%", file=sys.stderr, flush=True)

        except Exception as weather_error:
            print(f"Weather data error: {weather_error}", file=sys.stderr, flush=True)
            return _legacy_error(500, f"Failed to fetch climate data: {str(weather_error)}", "WEATHER_DATA_ERROR")

        # ====================================================================
        # BASELINE ANALYSIS (No Intervention)
        # ====================================================================
        productivity_analysis_baseline = calculate_productivity_loss(temp_c, humidity_pct)
        baseline_wbgt = productivity_analysis_baseline["wbgt_estimate"]
        baseline_productivity_loss_pct = productivity_analysis_baseline["productivity_loss_pct"]
        
        malaria_analysis = calculate_malaria_risk(temp_c, precip_mm)
        economic_impact_baseline = calculate_health_economic_impact(
            workforce_size=workforce_size,
            daily_wage=daily_wage,
            productivity_loss_pct=baseline_productivity_loss_pct,
            malaria_risk_score=malaria_analysis["risk_score"],
        )

        print(f"[HEALTH] BASELINE: WBGT={baseline_wbgt}°C, loss={baseline_productivity_loss_pct}%, annual_loss=${economic_impact_baseline['heat_stress_impact']['annual_productivity_loss']:,.2f}", file=sys.stderr, flush=True)

        # ====================================================================
        # INTERVENTION ANALYSIS (Cooling CAPEX vs. Productivity OPEX)
        # ====================================================================
        intervention_analysis = None
        
        # Check if this is a private-sector workplace intervention (not public health)
        private_sector_interventions = ["hvac_retrofit", "passive_cooling"]
        public_sector_interventions = ["urban_cooling_center", "mosquito_eradication"]
        
        is_private_sector_intervention = (
            intervention_type and 
            intervention_type.lower() not in ["none", ""] and
            intervention_type.lower() in private_sector_interventions
        )
        
        if is_private_sector_intervention:
            # Calculate adjusted WBGT based on intervention type
            adjusted_wbgt = baseline_wbgt
            wbgt_reduction = 0.0
            
            if intervention_type.lower() == "hvac_retrofit":
                # HVAC retrofit: Active cooling drops WBGT to safe baseline (22°C)
                # Assumption: Industrial HVAC can maintain 22°C WBGT regardless of external conditions
                adjusted_wbgt = 22.0
                wbgt_reduction = baseline_wbgt - adjusted_wbgt
                intervention_description = "Active HVAC cooling system maintains safe 22°C WBGT"
                
            elif intervention_type.lower() == "passive_cooling":
                # Passive cooling: Natural ventilation, shading, green roofs, etc.
                # Assumption: Can reduce WBGT by 3°C
                wbgt_reduction = 3.0
                adjusted_wbgt = max(baseline_wbgt - wbgt_reduction, 20.0)  # Floor at 20°C
                intervention_description = "Passive cooling (ventilation, shading, green roofs) reduces WBGT by 3°C"
            
            # Recalculate productivity loss with adjusted WBGT
            # We need to reverse-engineer temp/humidity from WBGT for the calculation
            # Since WBGT ≈ 0.7*Temp + 0.1*Humidity, we'll adjust temperature proportionally
            if wbgt_reduction > 0:
                # Adjust temperature to achieve desired WBGT
                # Keep humidity constant, adjust temp
                adjusted_temp = temp_c - (wbgt_reduction / 0.7)
                productivity_analysis_adjusted = calculate_productivity_loss(adjusted_temp, humidity_pct)
            else:
                productivity_analysis_adjusted = productivity_analysis_baseline
            
            adjusted_productivity_loss_pct = productivity_analysis_adjusted["productivity_loss_pct"]
            
            # Calculate avoided productivity loss
            avoided_productivity_loss_pct = baseline_productivity_loss_pct - adjusted_productivity_loss_pct
            
            # Economic impact with intervention
            economic_impact_adjusted = calculate_health_economic_impact(
                workforce_size=workforce_size,
                daily_wage=daily_wage,
                productivity_loss_pct=adjusted_productivity_loss_pct,
                malaria_risk_score=malaria_analysis["risk_score"],
            )
            
            # Calculate avoided annual economic loss (260 working days/year)
            # Note: Using 260 instead of 250 as requested
            working_days_per_year = 260
            baseline_annual_heat_loss = economic_impact_baseline['heat_stress_impact']['annual_productivity_loss']
            adjusted_annual_heat_loss = economic_impact_adjusted['heat_stress_impact']['annual_productivity_loss']
            avoided_annual_economic_loss_usd = baseline_annual_heat_loss - adjusted_annual_heat_loss
            
            print(f"[HEALTH] INTERVENTION: WBGT={adjusted_wbgt}°C, loss={adjusted_productivity_loss_pct}%, avoided_loss=${avoided_annual_economic_loss_usd:,.2f}/year", file=sys.stderr, flush=True)
            
            # ================================================================
            # FINANCIAL ROI ANALYSIS
            # ================================================================
            payback_period_years = None
            npv_10yr = None
            bcr = None
            roi_recommendation = "No financial analysis (zero CAPEX)"
            
            if intervention_capex > 0:
                # Net annual benefit = Avoided loss - Annual OPEX
                net_annual_benefit = avoided_annual_economic_loss_usd - intervention_annual_opex
                
                # Simple Payback Period: CAPEX / Net Annual Benefit
                if net_annual_benefit > 0:
                    payback_period_years = intervention_capex / net_annual_benefit
                else:
                    payback_period_years = None  # Never pays back (OPEX exceeds benefit)
                
                # 10-year NPV at 10% discount rate
                discount_rate = 0.10
                analysis_period = 10
                
                # Cash flow structure:
                # Year 0: -CAPEX
                # Years 1-10: Net Annual Benefit
                cash_flows = [-intervention_capex] + [net_annual_benefit] * analysis_period
                
                # Calculate NPV using financial_engine
                npv_result = calculate_npv(cash_flows, discount_rate)
                npv_10yr = npv_result
                
                # Calculate BCR (Benefit-Cost Ratio)
                # BCR = PV(Benefits) / PV(Costs)
                pv_benefits = sum([
                    avoided_annual_economic_loss_usd / ((1 + discount_rate) ** year)
                    for year in range(1, analysis_period + 1)
                ])
                pv_costs = intervention_capex + sum([
                    intervention_annual_opex / ((1 + discount_rate) ** year)
                    for year in range(1, analysis_period + 1)
                ])
                bcr = pv_benefits / pv_costs if pv_costs > 0 else 0.0
                
                # ROI Recommendation
                if npv_10yr > 0 and bcr > 1.0:
                    roi_recommendation = "✅ INVEST: Positive NPV and BCR > 1.0 - financially attractive"
                elif npv_10yr > 0:
                    roi_recommendation = "⚠️ MARGINAL: Positive NPV but low BCR - consider alternative interventions"
                else:
                    roi_recommendation = "❌ DO NOT INVEST: Negative NPV - OPEX and CAPEX exceed productivity gains"
                
                # Safe formatting for print statement (handle None values)
                safe_npv = npv_10yr if npv_10yr is not None else 0.0
                safe_payback = payback_period_years if payback_period_years is not None else 0.0
                safe_bcr = bcr if bcr is not None else 0.0
                print(f"[HEALTH] ROI: NPV=${safe_npv:,.2f}, Payback={safe_payback:.1f}yr, BCR={safe_bcr:.2f}", file=sys.stderr, flush=True)
            
            # Build intervention analysis response
            intervention_analysis = {
                "intervention_type": intervention_type,
                "intervention_description": intervention_description,
                "wbgt_adjustment": {
                    "baseline_wbgt": round(baseline_wbgt, 1),
                    "adjusted_wbgt": round(adjusted_wbgt, 1),
                    "wbgt_reduction": round(wbgt_reduction, 1),
                },
                "productivity_impact": {
                    "baseline_productivity_loss_pct": round(baseline_productivity_loss_pct, 1),
                    "adjusted_productivity_loss_pct": round(adjusted_productivity_loss_pct, 1),
                    "avoided_productivity_loss_pct": round(avoided_productivity_loss_pct, 1),
                },
                "economic_impact": {
                    "baseline_annual_loss_usd": round(baseline_annual_heat_loss, 2),
                    "adjusted_annual_loss_usd": round(adjusted_annual_heat_loss, 2),
                    "avoided_annual_economic_loss_usd": round(avoided_annual_economic_loss_usd, 2),
                    "working_days_per_year": working_days_per_year,
                },
                "financial_analysis": {
                    "intervention_capex": round(intervention_capex, 2),
                    "intervention_annual_opex": round(intervention_annual_opex, 2),
                    "net_annual_benefit": round(net_annual_benefit, 2) if intervention_capex > 0 else None,
                    "payback_period_years": round(payback_period_years, 2) if payback_period_years else None,
                    "npv_10yr_at_10pct_discount": round(npv_10yr, 2) if npv_10yr else None,
                    "bcr": round(bcr, 2) if bcr else None,
                    "roi_recommendation": roi_recommendation,
                },
                "heat_stress_category_after_intervention": productivity_analysis_adjusted["heat_stress_category"],
                "recommendation_after_intervention": productivity_analysis_adjusted["recommendation"],
            }

        # ====================================================================
        # PUBLIC HEALTH DALY ANALYSIS
        # ====================================================================
        # Calculate public health impact using DALYs for population-level analysis
        # This serves public sector users (governments, WHO, NGOs) who need to
        # understand population health burden and cost-effectiveness of interventions
        public_health_analysis = calculate_public_health_impact(
            population=population_size,
            gdp_per_capita=gdp_per_capita_usd,
            wbgt=baseline_wbgt,
            malaria_risk_score=malaria_analysis["risk_score"],
            intervention_type=intervention_type  # Use same intervention type as cooling analysis
        )
        
        print(f"[HEALTH] PUBLIC HEALTH: baseline_dalys={public_health_analysis['baseline_dalys_lost']}, averted={public_health_analysis['dalys_averted']}, value=${public_health_analysis['economic_value_preserved_usd']:,.2f}", file=sys.stderr, flush=True)

        # ====================================================================
        # HEALTHCARE INFRASTRUCTURE STRESS TESTING
        # ====================================================================
        # Research-backed data for hospital capacity stress testing
        research_data = {
            "high": {
                "beds_per_1000": 3.8,
                "capex": 1000000,
                "occupancy": 0.72,
                "surge_pct": 0.035,
                "dalys_per_deficit": 2.5
            },
            "middle": {
                "beds_per_1000": 2.8,
                "capex": 250000,
                "occupancy": 0.75,
                "surge_pct": 0.075,
                "dalys_per_deficit": 4.8
            },
            "low": {
                "beds_per_1000": 1.2,
                "capex": 60000,
                "occupancy": 0.80,
                "surge_pct": 0.135,
                "dalys_per_deficit": 8.2
            }
        }
        
        # Set active tier with fallback to middle
        active_tier = research_data.get(economy_tier, research_data["middle"])
        
        # Allow user overrides for baseline beds and cost
        baseline_beds_per_1000 = user_beds_per_1000 if user_beds_per_1000 is not None else active_tier["beds_per_1000"]
        cost_per_bed = user_cost_per_bed if user_cost_per_bed is not None else active_tier["capex"]
        
        # Calculate infrastructure stress metrics
        # Temperature increase from baseline (using actual temp_c vs. assumed baseline of 25°C)
        baseline_temp = 25.0
        projected_temp_increase = max(0, temp_c - baseline_temp)
        
        # Baseline capacity calculation
        baseline_capacity = (population_size / 1000) * baseline_beds_per_1000
        
        # Available beds after baseline occupancy
        available_beds = baseline_capacity * (1.0 - active_tier["occupancy"])
        
        # Climate-induced surge admissions (increases with temperature)
        surge_admissions = baseline_capacity * (active_tier["surge_pct"] * projected_temp_increase)
        
        # Bed deficit if surge exceeds available capacity
        bed_deficit = max(0, surge_admissions - available_beds)
        
        # Infrastructure bond CAPEX to address deficit
        infrastructure_bond_capex = bed_deficit * cost_per_bed
        
        # Build infrastructure stress test response
        infrastructure_stress_test = {
            "baseline_capacity": round(baseline_capacity, 2),
            "available_beds": round(available_beds, 2),
            "surge_admissions": round(surge_admissions, 2),
            "bed_deficit": round(bed_deficit, 2),
            "infrastructure_bond_capex": round(infrastructure_bond_capex, 2),
            "capacity_breach": bool(bed_deficit > 0),
            "applied_tier": economy_tier,
            "baseline_beds_per_1000": round(baseline_beds_per_1000, 2),
            "cost_per_bed": round(cost_per_bed, 2),
            "projected_temp_increase": round(projected_temp_increase, 1)
        }
        
        # If intervention is hospital_expansion, update public health analysis with infrastructure ROI
        if intervention_type and intervention_type.lower() == "hospital_expansion":
            # Calculate DALYs averted by addressing bed deficit
            dalys_averted_infrastructure = bed_deficit * active_tier["dalys_per_deficit"]
            
            # Use same value_per_daly as public health analysis (2x GDP per capita)
            value_per_daly = 2.0 * gdp_per_capita_usd
            economic_value_preserved_infrastructure = dalys_averted_infrastructure * value_per_daly
            
            # Update public health analysis with infrastructure intervention
            public_health_analysis["intervention_type"] = "hospital_expansion"
            public_health_analysis["dalys_averted"] = round(dalys_averted_infrastructure, 1)
            public_health_analysis["economic_value_preserved_usd"] = round(economic_value_preserved_infrastructure, 2)
            public_health_analysis["intervention_description"] = f"Hospital expansion adds {bed_deficit:.0f} beds to address climate-induced surge capacity"
            
            # Update intervention CAPEX to infrastructure bond amount
            intervention_capex = infrastructure_bond_capex
            
            print(f"[HEALTH] HOSPITAL EXPANSION: bed_deficit={bed_deficit:.0f}, capex=${infrastructure_bond_capex:,.2f}, dalys_averted={dalys_averted_infrastructure:.1f}, value=${economic_value_preserved_infrastructure:,.2f}", file=sys.stderr, flush=True)
        
        print(f"[HEALTH] INFRASTRUCTURE STRESS: capacity={baseline_capacity:.0f}, surge={surge_admissions:.0f}, deficit={bed_deficit:.0f}, capex=${infrastructure_bond_capex:,.2f}", file=sys.stderr, flush=True)

        # ====================================================================
        # RESPONSE CONSTRUCTION
        # ====================================================================
        response_data = {
            "location": {"lat": lat, "lon": lon},
            "climate_conditions": {
                "temperature_c": round(temp_c, 1),
                "precipitation_mm": round(precip_mm, 1),
                "humidity_pct_estimated": humidity_pct,
            },
            "heat_stress_analysis": productivity_analysis_baseline,
            "malaria_risk_analysis": malaria_analysis,
            "economic_impact": economic_impact_baseline,
            "workforce_parameters": {
                "workforce_size": workforce_size,
                "daily_wage": daily_wage,
                "currency": "USD",
            },
            "public_health_analysis": public_health_analysis,
            "infrastructure_stress_test": infrastructure_stress_test,
        }
        
        # Add intervention analysis if cooling intervention was requested
        if intervention_analysis:
            response_data["intervention_analysis"] = intervention_analysis

        return {"status": "success", "data": response_data}

    except ValueError as ve:
        return _legacy_error(400, f"Invalid numeric values: {str(ve)}", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        print(f"Health prediction error: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        return _legacy_error(500, f"Health analysis failed: {str(e)}", "HEALTH_ERROR")



@app.post("/predict-portfolio")
def predict_portfolio(req: PredictPortfolioRequest):
    """Analyze portfolio diversification across multiple locations.

    Simulates 10 years of climate variation for each location and
    calculates aggregate tonnage and portfolio volatility.
    """
    try:
        from physics_engine import calculate_volatility

        locations = req.locations
        crop_type = req.crop_type.lower()

        if crop_type not in ("maize", "cocoa"):
            return _legacy_error(
                400,
                f"Unsupported crop_type: {crop_type}. Supported crops: 'maize', 'cocoa'",
                "INVALID_CROP_TYPE",
            )

        print(f"[PORTFOLIO] Processing {len(locations)} locations for crop_type={crop_type}", file=sys.stderr, flush=True)

        all_location_cvs: list[float] = []
        total_tonnage = 0.0
        location_results: list[dict] = []

        for idx, loc in enumerate(locations):
            lat = loc.lat
            lon = loc.lon

            print(f"[PORTFOLIO] Location {idx + 1}/{len(locations)}: lat={lat}, lon={lon}", file=sys.stderr, flush=True)

            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)

                weather_data = get_weather_data(
                    lat=lat, lon=lon,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d"),
                )

                base_temp = weather_data["max_temp_celsius"]
                base_rain = weather_data["total_precip_mm"]

            except Exception as weather_error:
                print(f"Weather data error for location {idx}: {weather_error}", file=sys.stderr, flush=True)
                return _legacy_error(
                    500,
                    f"Failed to fetch weather data for location {idx}: {str(weather_error)}",
                    "WEATHER_DATA_ERROR",
                )

            years = 10
            annual_yields: list[float] = []

            for _ in range(years):
                temp_variation = random.uniform(-2.0, 2.0)
                rain_variation = random.uniform(-15.0, 15.0)

                year_yield = calculate_yield(
                    temp=base_temp, rain=base_rain,
                    seed_type=SEED_TYPES["resilient"],
                    crop_type=crop_type,
                    temp_delta=temp_variation,
                    rain_pct_change=rain_variation,
                )
                annual_yields.append(year_yield)

            mean_yield = statistics.mean(annual_yields)
            location_cv = calculate_volatility(annual_yields)

            max_potential_tons = 10.0
            location_tonnage = (mean_yield / 100.0) * max_potential_tons

            total_tonnage += location_tonnage
            all_location_cvs.append(location_cv)

            location_results.append({
                "location_index": idx,
                "lat": lat,
                "lon": lon,
                "mean_yield_pct": round(mean_yield, 2),
                "volatility_cv_pct": location_cv,
                "tonnage": round(location_tonnage, 2),
            })

            print(f"[PORTFOLIO] Location {idx + 1} complete: mean_yield={mean_yield:.2f}%, CV={location_cv:.2f}%, tonnage={location_tonnage:.2f}t", file=sys.stderr, flush=True)

        portfolio_volatility = statistics.mean(all_location_cvs) if all_location_cvs else 0.0

        if portfolio_volatility < 10.0:
            risk_rating = "Low"
        elif portfolio_volatility < 20.0:
            risk_rating = "Medium"
        elif portfolio_volatility < 30.0:
            risk_rating = "High"
        else:
            risk_rating = "Very High"

        print(f"[PORTFOLIO] Complete: total_tonnage={total_tonnage:.2f}t, portfolio_volatility={portfolio_volatility:.2f}%, risk={risk_rating}", file=sys.stderr, flush=True)

        return {
            "status": "success",
            "data": {
                "portfolio_summary": {
                    "total_tonnage": round(total_tonnage, 2),
                    "portfolio_volatility_pct": round(portfolio_volatility, 2),
                    "risk_rating": risk_rating,
                    "num_locations": len(locations),
                    "crop_type": crop_type,
                },
                "locations": location_results,
                "risk_interpretation": {
                    "low": "0-10% CV: Very stable production",
                    "medium": "10-20% CV: Moderate variation",
                    "high": "20-30% CV: Significant variation",
                    "very_high": "30%+ CV: Highly volatile",
                },
            },
        }

    except ValueError as ve:
        return _legacy_error(400, f"Invalid numeric values: {str(ve)}", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        print(f"Portfolio error: {e}", file=sys.stderr, flush=True)
        return _legacy_error(500, f"Portfolio analysis failed: {str(e)}", "PORTFOLIO_ERROR")


# ---------------------------------------------------------------------------
# Earth Observation — NDVI time-series
# ---------------------------------------------------------------------------

def _ndvi_mock_series() -> list[dict]:
    """Generate a deterministic 12-month mock NDVI series as a safe fallback."""
    base = [0.32, 0.35, 0.42, 0.55, 0.68, 0.74,
            0.76, 0.72, 0.63, 0.50, 0.38, 0.33]
    now = datetime.now()
    return [
        {
            "month": f"{(now - timedelta(days=30 * (12 - i))).strftime('%Y-%m')}",
            "value": round(v + random.uniform(-0.02, 0.02), 4),
        }
        for i, v in enumerate(base)
    ]


@app.get("/api/v1/eo/ndvi")
def eo_ndvi(lat: float, lon: float):
    """Return a 12-month NDVI time-series from MODIS via Google Earth Engine."""
    try:
        series = get_ndvi_timeseries(lat, lon)
        return {"status": "success", "source": "gee", "data": series}
    except Exception as exc:
        print(
            f"[EO/NDVI] GEE request failed for lat={lat}, lon={lon}: {exc}",
            file=sys.stderr,
            flush=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "fallback",
                "message": "GEE unavailable – returning mock NDVI data",
                "source": "mock",
                "data": _ndvi_mock_series(),
            },
        )


@app.post("/api/v1/finance/price-shock", response_model=PriceShockResponse)
def price_shock(req: PriceShockRequest) -> dict:
    """Calculate commodity price shock from climate-induced yield loss.

    When climate stress reduces local crop yields, this endpoint calculates the
    resulting spike in local commodity prices based on price elasticity of supply.

    Theory:
    - Price Elasticity of Supply: ε = (% change in quantity) / (% change in price)
    - When supply drops, prices rise according to: % price change = (% supply change) / ε
    - For agricultural commodities, supply is typically inelastic in the short term,
      so price shocks can be severe (e.g., 10% yield loss → 40% price increase for maize).

    Example Use Cases:
    - Assess financial impact of drought on farmers' revenue
    - Determine optimal hedging strategy via forward contracts
    - Calculate price risk for food importers/processors
    - Evaluate crop insurance payout thresholds

    Supported Crops:
    - Grains: maize, wheat, rice, barley, sorghum, millet
    - Oilseeds: soybeans, canola, sunflower
    - Cash crops: cocoa, coffee, cotton, sugar
    - Pulses: chickpeas, lentils, beans
    - Other: cassava, potato, tomato

    Returns:
    - Baseline and shocked prices
    - Revenue impact (yield loss partially offset by higher prices)
    - Forward contract recommendation based on risk severity
    """
    try:
        result = calculate_price_shock(
            crop_type=req.crop_type,
            baseline_yield_tons=req.baseline_yield_tons,
            stressed_yield_tons=req.stressed_yield_tons
        )
        return result

    except ValueError as e:
        # User input validation errors (invalid crop type, negative yields, etc.)
        raise HTTPException(status_code=400, detail=str(e)) from e
    
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=500, detail=str(e)) from e


def calculate_flooded_miles(geojson: Dict[str, Any]) -> float:
    """Mock/placeholder function for GEE flood hazard analysis.
    
    Returns a mock value until real Earth Engine raster integration is implemented.
    
    Args:
        geojson: GeoJSON LineString geometry
    
    Returns:
        float: Flooded miles (mock value: 2.5)
    """
    # TODO: Wire real Earth Engine raster integration
    # For now, return mock value for testing and frontend development
    return 2.5


@app.post("/api/v1/network/route-risk", response_model=RouteRiskResponse)
def calculate_route_risk(req: RouteRiskRequest) -> dict:
    """Calculate economic risk for truck routes intersecting flood zones.
    
    This endpoint analyzes supply chain disruption risk using ATRI benchmarks:
    1. Mock flooded miles calculation (placeholder for GEE integration)
    2. Calculate detour delays and economic costs
    3. Estimate intervention capital expenditure for flood mitigation
    
    Economic Formulas (ATRI & Industry Benchmarks):
    - flooded_miles = 2.5 (mock/placeholder)
    - detour_delay_hours = flooded_miles × 0.5 (30 min delay per flooded mile)
    - freight_delay_cost = detour_delay_hours × $91.27 (ATRI Value of Time)
    - spoilage_cost = cargo_value × 0.20 × (detour_delay_hours / 24) (20% spoilage rate per day)
    - total_value_at_risk = freight_delay_cost + spoilage_cost
    - intervention_capex = flooded_miles × $5,000,000 ($5M per mile highway elevation)
    
    Use Cases:
    - Trucking companies assessing climate risk on critical routes
    - Insurance companies pricing supply chain disruption policies
    - Infrastructure planners prioritizing road elevation projects
    
    Example Request:
    {
        "route_geojson": {
            "type": "LineString",
            "coordinates": [[-74.006, 40.7128], [-73.935, 40.7306]]
        },
        "cargo_value": 100000.0
    }
    
    Returns:
    - flooded_miles: Length of route intersecting flood zones (mock: 2.5)
    - detour_delay_hours: Additional delay from detours
    - freight_delay_cost: ATRI-based freight cost increase
    - spoilage_cost: Cargo spoilage from delays
    - total_value_at_risk: Combined economic impact
    - intervention_capex: Highway elevation cost ($5M/mile)
    """
    try:
        # Validate GeoJSON structure
        if req.route_geojson.get('type') != 'LineString':
            raise HTTPException(
                status_code=400,
                detail="Invalid GeoJSON: Expected LineString geometry"
            )
        
        coordinates = req.route_geojson.get('coordinates')
        if not coordinates or len(coordinates) < 2:
            raise HTTPException(
                status_code=400,
                detail="Invalid LineString: Must have at least 2 coordinate pairs"
            )
        
        # Mock/placeholder for GEE integration
        flooded_miles = calculate_flooded_miles(req.route_geojson)
        
        # Economic calculations (ATRI & Industry Benchmarks)
        # 1. Detour delay: 30 minutes (0.5 hours) per flooded mile
        detour_delay_hours = flooded_miles * 0.5
        
        # 2. Freight delay cost: ATRI Value of Time ($91.27/hour)
        freight_delay_cost = detour_delay_hours * 91.27
        
        # 3. Spoilage cost: 20% spoilage rate per day
        spoilage_cost = req.cargo_value * 0.20 * (detour_delay_hours / 24.0)
        
        # 4. Total value at risk
        total_value_at_risk = freight_delay_cost + spoilage_cost
        
        # 5. Intervention CAPEX: $5 million per mile highway elevation
        intervention_capex = flooded_miles * 5_000_000.0
        
        return {
            "flooded_miles": round(flooded_miles, 2),
            "detour_delay_hours": round(detour_delay_hours, 2),
            "freight_delay_cost": round(freight_delay_cost, 2),
            "spoilage_cost": round(spoilage_cost, 2),
            "total_value_at_risk": round(total_value_at_risk, 2),
            "intervention_capex": round(intervention_capex, 2)
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    
    except Exception as e:
        # Catch any calculation errors
        raise HTTPException(
            status_code=500,
            detail=f"Route risk analysis failed: {str(e)}"
        ) from e


@app.post("/api/v1/network/grid-resilience", response_model=GridRiskResponse)
def calculate_grid_resilience(req: GridRiskRequest) -> dict:
    """Calculate energy grid brownout risk and microgrid sizing for heatwaves.
    
    This endpoint analyzes grid failure risk from HVAC demand spikes during heat waves
    using ASHRAE & NREL ATB 2024 benchmarks, and calculates microgrid requirements
    (solar + battery storage) to maintain operations.
    
    Economic Formulas (ASHRAE & NREL ATB 2024):
    - temp_anomaly = projected_temp_c - baseline_temp_c
    - hvac_spike_pct = temp_anomaly × 3.0 (3% spike per degree C)
    - grid_failure_probability = min((hvac_spike_pct / 100) × 1.5, 1.0)
    - expected_downtime_hours = grid_failure_probability × 12.0
    - downtime_loss = expected_downtime_hours × $25,000 (Fuji/Siemens $25k/hr benchmark)
    
    Microgrid Sizing (NREL ATB 2024):
    - required_solar_kw = facility_sqft × 0.01
    - required_bess_kwh = required_solar_kw × 4.0
    - microgrid_capex = (required_solar_kw × $1,780) + (required_bess_kwh × $400)
    
    Use Cases:
    - Data centers ensuring uptime during heat-induced grid failures
    - Manufacturing facilities calculating business continuity costs
    - Commercial real estate evaluating microgrid ROI
    - Utilities planning grid hardening investments
    
    Example Request:
    {
        "facility_sqft": 50000.0,
        "baseline_temp_c": 25.0,
        "projected_temp_c": 35.0
    }
    
    Returns:
    - temp_anomaly: Temperature increase in °C
    - hvac_spike_pct: HVAC demand spike percentage
    - downtime_loss: Economic loss from downtime (Fuji/Siemens benchmark)
    - required_solar_kw: Solar capacity needed
    - required_bess_kwh: Battery storage capacity needed
    - microgrid_capex: Total microgrid investment cost (NREL ATB 2024)
    """
    try:
        # 1. Temperature anomaly calculation
        temp_anomaly = req.projected_temp_c - req.baseline_temp_c
        
        # 2. HVAC spike percentage (3% per degree Celsius - ASHRAE)
        hvac_spike_pct = temp_anomaly * 3.0
        
        # 3. Grid failure probability (capped at 100%)
        grid_failure_probability = min((hvac_spike_pct / 100.0) * 1.5, 1.0)
        
        # 4. Expected downtime hours (maximum 12-hour outage assumption)
        expected_downtime_hours = grid_failure_probability * 12.0
        
        # 5. Downtime economic loss (Fuji/Siemens $25k/hr benchmark)
        downtime_loss = expected_downtime_hours * 25000.0
        
        # 6. Microgrid sizing - Solar capacity (1% of facility size rule)
        required_solar_kw = req.facility_sqft * 0.01
        
        # 7. Battery storage sizing (4 hours of backup)
        required_bess_kwh = required_solar_kw * 4.0
        
        # 8. Microgrid capital expenditure (NREL ATB 2024)
        # Solar: $1,780/kW, Battery: $400/kWh
        solar_cost = required_solar_kw * 1780.0
        bess_cost = required_bess_kwh * 400.0
        microgrid_capex = solar_cost + bess_cost
        
        return {
            "temp_anomaly": round(temp_anomaly, 2),
            "hvac_spike_pct": round(hvac_spike_pct, 2),
            "downtime_loss": round(downtime_loss, 2),
            "required_solar_kw": round(required_solar_kw, 2),
            "required_bess_kwh": round(required_bess_kwh, 2),
            "microgrid_capex": round(microgrid_capex, 2)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Grid resilience analysis failed: {str(e)}"
        ) from e


@app.post("/api/v1/portfolio/analyze", response_model=PortfolioResponse)
def analyze_portfolio(req: PortfolioRequest) -> dict:
    """Analyze macro-portfolio risk across multiple assets with different climate hazards.
    
    This endpoint processes a portfolio of assets, calculates Value at Risk (VaR) based on
    primary climate hazards, assigns resilience scores, and provides aggregated analytics
    for executive dashboards and risk visualization.
    
    Risk Metrics by Hazard Type:
    - Flood: 15% VaR (riverine/pluvial flooding damage)
    - Heat: 5% VaR (HVAC failure, productivity loss)
    - Coastal: 20% VaR (storm surge, sea level rise)
    - Supply Chain: 10% VaR (logistics disruption, spoilage)
    
    Resilience Scoring:
    - Score = 100 - (VaR percentage × 5)
    - Critical: < 40 (high risk, immediate action needed)
    - Warning: 40-70 (moderate risk, monitoring required)
    - Secure: > 70 (low risk, minimal intervention)
    
    Use Cases:
    - Portfolio managers assessing climate risk across real estate holdings
    - Insurers pricing climate risk premiums by asset class
    - CFOs prioritizing adaptation investments by ROI
    - Board-level climate risk reporting (TCFD compliance)
    
    Example Request:
    {
        "assets": [
            {
                "id": "PROP-001",
                "property_name": "Manhattan Data Center",
                "location": "New York, NY",
                "asset_value": 50000000.0,
                "primary_hazard": "Flood"
            },
            {
                "id": "PROP-002",
                "property_name": "Phoenix Warehouse",
                "location": "Phoenix, AZ",
                "asset_value": 10000000.0,
                "primary_hazard": "Heat"
            }
        ]
    }
    
    Returns:
    - summary: Portfolio totals (value, VaR, avg resilience)
    - visualizations: Donut chart (VaR by hazard), Top 5 at-risk assets
    - ledger: Full asset list with calculated metrics
    """
    try:
        # Hazard-based VaR percentages (industry benchmarks)
        HAZARD_VAR = {
            "Flood": 0.15,      # 15% (riverine/pluvial flooding)
            "Heat": 0.05,       # 5% (HVAC failure, heat stress)
            "Coastal": 0.20,    # 20% (storm surge, SLR)
            "Supply Chain": 0.10  # 10% (logistics disruption)
        }
        
        calculated_assets = []
        
        # Process each asset
        for asset in req.assets:
            # Calculate Value at Risk
            var_percentage = HAZARD_VAR[asset.primary_hazard]
            value_at_risk = asset.asset_value * var_percentage
            
            # Calculate resilience score (0-100, inversely proportional to VaR)
            # Formula: 100 - (VaR% × 5)
            # Example: 15% VaR → 100 - 75 = 25 (Critical)
            # Example: 5% VaR → 100 - 25 = 75 (Secure)
            resilience_score = 100.0 - (var_percentage * 100.0 * 5.0)
            
            # Assign status based on resilience score
            if resilience_score < 40:
                status = "Critical"
            elif resilience_score <= 70:
                status = "Warning"
            else:
                status = "Secure"
            
            calculated_assets.append({
                "id": asset.id,
                "property_name": asset.property_name,
                "location": asset.location,
                "asset_value": asset.asset_value,
                "primary_hazard": asset.primary_hazard,
                "value_at_risk": round(value_at_risk, 2),
                "resilience_score": round(resilience_score, 2),
                "status": status
            })
        
        # Aggregation Logic
        # 1. Calculate totals
        total_portfolio_value = sum(a.asset_value for a in req.assets)
        total_value_at_risk = sum(a["value_at_risk"] for a in calculated_assets)
        average_resilience_score = sum(a["resilience_score"] for a in calculated_assets) / len(calculated_assets)
        
        # 2. Group VaR by hazard type (for donut chart)
        var_by_hazard = {}
        for asset in calculated_assets:
            hazard = asset["primary_hazard"]
            var_by_hazard[hazard] = var_by_hazard.get(hazard, 0.0) + asset["value_at_risk"]
        
        # 3. Top 5 at-risk assets (sorted by VaR descending)
        sorted_assets = sorted(calculated_assets, key=lambda x: x["value_at_risk"], reverse=True)
        top_at_risk_assets = sorted_assets[:5]
        
        # Build response
        return {
            "summary": {
                "total_portfolio_value": round(total_portfolio_value, 2),
                "total_value_at_risk": round(total_value_at_risk, 2),
                "average_resilience_score": round(average_resilience_score, 2)
            },
            "visualizations": {
                "var_by_hazard": {k: round(v, 2) for k, v in var_by_hazard.items()},
                "top_at_risk_assets": top_at_risk_assets
            },
            "ledger": calculated_assets
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Portfolio analysis failed: {str(e)}"
        ) from e


@app.get("/api/v1/macro/sovereign-risk", response_model=SovereignRiskResponse)
def get_sovereign_risk() -> dict:
    """Get global sovereign climate risk scores for 3D globe visualization.
    
    This endpoint computes country-level climate risk using Google Earth Engine
    to analyze flood exposure across all nations simultaneously. Results are cached
    for 24 hours to ensure instant frontend globe loading.
    
    GEE Data Sources:
    - Country Boundaries: FAO GAUL 2015 (level 0, ~250 countries)
    - Hazard Dataset: JRC Global Surface Water (flood occurrence 1984-2021)
    
    Spatial Processing:
    - Global reduceRegions at 50km resolution for fast computation
    - Mean water occurrence calculated per country
    - Normalized to 0-100 risk scores with exponential scaling
    
    Risk Score Interpretation:
    - 80-100: Critical (high coastal/riverine flooding)
    - 60-79: High (significant flood exposure)
    - 40-59: Moderate (some flood risk)
    - 20-39: Low (minimal flooding, other hazards)
    - 0-19: Very Low (limited climate exposure)
    
    Primary Vulnerabilities:
    - Coastal Flooding: Risk score >= 70
    - Riverine Flooding: Risk score 50-69
    - Agricultural Yield: Risk score 30-49
    - Extreme Heat: Risk score < 30
    
    Performance:
    - First call: 15-30 seconds (GEE global computation)
    - Subsequent calls: <50ms (in-memory cache, 24-hour TTL)
    - Cache invalidates daily to reflect updated GEE datasets
    
    Use Cases:
    - Interactive 3D globe visualization (frontend Three.js/D3.js)
    - Board-level sovereign risk reporting
    - Climate finance risk assessment by country
    - Portfolio geographic diversification analysis
    
    Example Response:
    {
        "countries": [
            {
                "country_code": "BGD",
                "country_name": "Bangladesh",
                "risk_score": 88,
                "primary_vulnerability": "Coastal Flooding"
            },
            {
                "country_code": "USA",
                "country_name": "United States",
                "risk_score": 55,
                "primary_vulnerability": "Riverine Flooding"
            }
        ]
    }
    
    Returns:
        Array of country risk data with ISO codes, names, scores, and vulnerabilities
    """
    try:
        # Calculate or retrieve from cache
        country_data = calculate_global_sovereign_risk()
        
        return {
            "countries": country_data
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sovereign risk calculation failed: {str(e)}"
        ) from e


@app.get("/api/v1/spatial/timelapse/{hazard_type}", response_model=TimelapseResponse)
def get_climate_timelapse(hazard_type: str) -> dict:
    """Get global climate projection tile URLs for time-lapse visualization.
    
    This endpoint generates Mapbox-compatible XYZ tile URLs for future climate
    projections using Google Earth Engine. Results are aggressively cached for
    24 hours since Map IDs are identical for all users (global datasets, no bbox).
    
    Path Parameters:
    - hazard_type: Climate hazard type ("heat" or "flood")
    
    Supported Hazards:
    - "heat": Temperature projections (NASA NEX-GDDP / ERA5 + synthetic warming)
    - "flood": Flood occurrence projections (JRC Global Surface Water + increase)
    
    Projection Years:
    - 2026: Near-term (current trends)
    - 2030: Paris Agreement checkpoint
    - 2040: Mid-century approaching
    - 2050: Standard climate target year
    
    Visualization Parameters:
    
    Heat (Temperature):
    - Min: 20°C, Max: 45°C
    - Palette: Yellow → Orange → Red → Dark Red
    - Dataset: ERA5 Land + 0.2°C/year warming
    
    Flood (Water Occurrence):
    - Min: 0%, Max: 100%
    - Palette: White → Light Blue → Blue → Dark Blue
    - Dataset: JRC Global Surface Water + 1%/year increase
    
    Performance:
    - First call: 20-40 seconds (4 GEE Map IDs generated)
    - Subsequent calls: <50ms (in-memory cache, 24-hour TTL)
    - Cache shared across all users (global tiles)
    
    Use Cases:
    - Frontend time-lapse globe animation (slide through years)
    - Climate scenario visualization (compare 2026 vs 2050)
    - Executive presentations (visual climate storytelling)
    - TCFD reporting (forward-looking risk disclosure)
    
    Example Response:
    {
        "hazard": "heat",
        "layers": {
            "2026": "https://earthengine.googleapis.com/.../tiles/{z}/{x}/{y}",
            "2030": "https://earthengine.googleapis.com/.../tiles/{z}/{x}/{y}",
            "2040": "https://earthengine.googleapis.com/.../tiles/{z}/{x}/{y}",
            "2050": "https://earthengine.googleapis.com/.../tiles/{z}/{x}/{y}"
        }
    }
    
    Frontend Integration (Mapbox GL JS):
    ```javascript
    const response = await fetch('/api/v1/spatial/timelapse/heat');
    const { hazard, layers } = await response.json();
    
    // Add each year as a separate raster layer
    Object.entries(layers).forEach(([year, tileUrl]) => {
      map.addLayer({
        id: `heat-${year}`,
        type: 'raster',
        source: {
          type: 'raster',
          tiles: [tileUrl],
          tileSize: 256
        },
        layout: { visibility: year === '2026' ? 'visible' : 'none' }
      });
    });
    
    // Animate through years
    function animateTimelapse() {
      const years = ['2026', '2030', '2040', '2050'];
      let currentIndex = 0;
      
      setInterval(() => {
        years.forEach(year => {
          map.setLayoutProperty(`heat-${year}`, 'visibility', 'none');
        });
        map.setLayoutProperty(`heat-${years[currentIndex]}`, 'visibility', 'visible');
        currentIndex = (currentIndex + 1) % years.length;
      }, 2000); // 2-second intervals
    }
    ```
    
    Returns:
        Dictionary with hazard type and year-to-tile-URL mapping
    """
    try:
        # Validate hazard type
        valid_hazards = ["heat", "flood"]
        if hazard_type not in valid_hazards:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid hazard type: {hazard_type}. Supported: {', '.join(valid_hazards)}"
            )
        
        # Calculate or retrieve from cache
        tile_layers = calculate_climate_timelapse(hazard_type)
        
        return {
            "hazard": hazard_type,
            "layers": tile_layers
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Climate timelapse calculation failed: {str(e)}"
        ) from e


@app.post("/api/v1/ai/executive-summary", response_model=ExecutiveSummaryResponse)
def executive_summary(req: ExecutiveSummaryRequest) -> dict:
    """Generate deterministic executive summary using NLG templates.
    
    This endpoint generates executive summaries using deterministic Python f-strings
    to avoid LLM token costs and hallucination risks. All text is template-based
    with dynamic value insertion.
    
    Zero LLM Calls:
    - No ChatGPT, Claude, or other LLM APIs
    - No hallucination risk
    - Instant response (no API latency)
    - Zero per-request costs
    
    Supported Modules:
    - health_public: Public health DALY analysis (population-level)
    - health_private: Private sector workplace cooling CBA
    - agriculture: Crop yield and revenue analysis
    - coastal: Coastal flood risk and infrastructure
    - flood: Urban/flash flood risk
    - price_shock: Commodity price shock from climate stress
    
    Response Format:
    - Exactly 3 sentences
    - Sentence 1: Context and hazard description
    - Sentence 2: Intervention/impact quantification
    - Sentence 3: Economic value and recommendation
    
    Example Request:
    {
        "module_name": "health_public",
        "location_name": "Bangkok",
        "simulation_data": {
            "dalys_averted": 4107.0,
            "economic_value_preserved_usd": 98568000.0,
            "intervention_type": "urban_cooling_center",
            "wbgt_estimate": 30.8,
            "malaria_risk_score": 100
        }
    }
    
    Example Response:
    {
        "summary_text": "Bangkok faces severe economic disruption from projected 
        climate hazards including extreme heat stress and high malaria transmission 
        risk. Implementing urban cooling centers will avert 4,107 Disability-Adjusted 
        Life Years (DALYs). This preserves $98.6 million in macroeconomic value, 
        making it a highly favorable public sector investment."
    }
    
    Fallback Behavior:
    - If module is unknown or data parsing fails, returns generic fallback message
    - No errors thrown - always returns valid summary text
    - Graceful degradation ensures robustness
    """
    try:
        # Generate summary using deterministic NLG
        summary_text = generate_deterministic_summary(
            module_name=req.module_name,
            location_name=req.location_name,
            data=req.simulation_data
        )
        
        return {
            "summary_text": summary_text
        }
    
    except Exception as e:
        # Fallback to generic message if NLG fails
        fallback = f"Data successfully processed for {req.location_name}. Please refer to the quantitative metrics provided in the dashboard for detailed ROI analysis."
        return {
            "summary_text": fallback
        }


def main() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
