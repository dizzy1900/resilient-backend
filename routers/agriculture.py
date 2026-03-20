"""Agriculture endpoints — extracted from api.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Dict, Optional, Tuple
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import get_current_user
from models import User

router = APIRouter(prefix="/api/v1/agriculture", tags=["Agriculture"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class FinancialOverrides(BaseModel):
    """Optional financial parameters for ROI calculations."""
    capex_budget: float = Field(2000.0, description="Initial capital expenditure in USD")
    opex_annual: float = Field(425.0, description="Annual operating expenses in USD")
    discount_rate_pct: float = Field(10.0, description="Discount rate as percentage")
    asset_lifespan_years: int = Field(10, ge=1, le=50, description="Asset lifespan in years")


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


def _resolve_headless_runner_path() -> Path:
    """
    Resolve `headless_runner.py` without relying on the current working directory.

    This fixes container/deployment issues where subprocess CWD changes after refactors.
    """
    this_dir = Path(__file__).resolve().parent
    for candidate_dir in (this_dir, *this_dir.parents):
        candidate = candidate_dir / "headless_runner.py"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Unable to locate 'headless_runner.py'. "
        "Expected it somewhere above 'routers/agriculture.py' in the repo."
    )

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


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


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

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/simulate")
def run_agriculture_simulation(req: AgricultureRequest) -> dict:
    """Run agriculture simulation with optional financial overrides.
    
    This endpoint calls the headless_runner with custom financial parameters
    and returns the complete analysis including NPV and ROI calculations.
    """
    try:
        runner_path = _resolve_headless_runner_path()

        # Build command for headless_runner
        cmd = [
            sys.executable,
            str(runner_path),
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
            cwd=str(runner_path.parent),
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
        
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict", response_model=PredictAgriResponse)
def predict_agri(req: PredictAgriRequest, user: User = Depends(get_current_user)) -> PredictAgriResponse:
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
