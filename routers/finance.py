"""Finance endpoints — CBA, CVaR, blended finance, price shock, financials."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional

import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from financial_engine import calculate_roi_metrics
from price_shock_engine import calculate_price_shock
from routers._shared import legacy_error

router = APIRouter(prefix="/api/v1/finance", tags=["Finance"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CBARequest(BaseModel):
    """Request for Cost-Benefit Analysis time series of a climate adaptation project."""
    capex: float = Field(500000.0, description="Upfront capital expenditure in USD")
    annual_opex: float = Field(25000.0, description="Annual operating expenditure in USD")
    discount_rate: float = Field(0.08, description="Discount rate as decimal (e.g. 0.08 for 8%)")
    lifespan_years: int = Field(30, ge=1, le=100, description="Project lifespan in years")
    annual_baseline_damage: float = Field(100000.0, description="Annual cost of doing nothing in USD")
    damage_reduction_pct: float = Field(0.80, ge=0.0, le=1.0, description="Fraction of damage the intervention prevents")
    base_insurance_premium: float = Field(50000.0, description="Annual insurance premium without intervention in USD")
    insurance_reduction_pct: float = Field(0.25, ge=0.0, le=1.0, description="Premium reduction from intervention")
    standard_interest_rate: float = Field(0.06, description="Standard bond interest rate as decimal")
    greenium_discount_bps: float = Field(50.0, description="Green bond discount in basis points")
    bond_tenor_years: int = Field(10, ge=1, le=50, description="Bond repayment period in years")
    annual_carbon_credits: float = Field(0.0, description="Tons of CO2 sequestered per year")
    carbon_price_per_ton: float = Field(50.0, description="Price per ton of CO2 in USD")


class CVaRRequest(BaseModel):
    """Request for Climate Value at Risk Monte Carlo simulation."""
    asset_value: float = Field(5_000_000.0, description="Total asset value in USD")
    mean_damage_pct: float = Field(0.02, description="Average annual damage as decimal")
    volatility_pct: float = Field(0.05, description="Damage volatility as decimal")
    num_simulations: int = Field(10_000, ge=100, le=1_000_000, description="Number of Monte Carlo trials")


class FinancingTranches(BaseModel):
    """Financing tranche structure for blended finance."""
    commercial_debt_pct: float = Field(..., ge=0.0, le=1.0)
    concessional_grant_pct: float = Field(..., ge=0.0, le=1.0)
    municipal_equity_pct: float = Field(..., ge=0.0, le=1.0)


class BlendedFinanceRequest(BaseModel):
    """Request for Blended Finance Structuring calculation."""
    total_capex: float = Field(..., gt=0, description="Total capital expenditure in USD")
    resilience_score: int = Field(..., ge=0, le=100, description="Climate resilience score (0-100)")
    tranches: FinancingTranches = Field(..., description="Financing tranche structure")
    rate_shock_bps: Optional[int] = Field(None, description="Optional rate shock in basis points for sensitivity analysis")
    annual_carbon_revenue: float = Field(0.0, ge=0, description="Annual carbon credit revenue in USD")
    base_insurance_premium: float = Field(0.0, ge=0, description="Current annual insurance premium in USD")
    risk_reduction_pct: float = Field(0.0, ge=0, le=1.0, description="Percentage of physical risk mitigated")

    @property
    def tranches_sum(self) -> float:
        return (
            self.tranches.commercial_debt_pct +
            self.tranches.concessional_grant_pct +
            self.tranches.municipal_equity_pct
        )

    def model_post_init(self, __context) -> None:
        tranches_total = self.tranches_sum
        if not (0.99 <= tranches_total <= 1.01):
            raise ValueError(
                f"Tranches must sum to 1.0 (100%). Current sum: {tranches_total:.4f}"
            )


class BlendedFinanceResponse(BaseModel):
    """Response for Blended Finance Structuring calculation."""
    status: str = "success"
    input_capex: float
    input_resilience_score: int
    commercial_debt_amount: float
    concessional_grant_amount: float
    municipal_equity_amount: float
    base_commercial_rate: float
    applied_commercial_rate: float
    concessional_rate: float
    municipal_equity_rate: float
    greenium_discount_bps: float
    blended_interest_rate: float
    annual_debt_service: float
    total_greenium_savings: float
    annual_carbon_revenue: float
    net_annual_debt_service: float
    insurance_savings: float
    adjusted_insurance_premium: float
    loan_term_years: int
    debt_principal: float
    sensitivity_analysis: Optional[Dict[str, Any]] = None


class PriceShockRequest(BaseModel):
    """Request for commodity price shock calculation."""
    crop_type: str = Field(..., description="Crop type")
    baseline_yield_tons: float = Field(..., gt=0, description="Expected yield under normal conditions")
    stressed_yield_tons: float = Field(..., ge=0, description="Actual/projected yield under climate stress")


class PriceShockResponse(BaseModel):
    """Response for commodity price shock calculation."""
    baseline_price: float
    shocked_price: float
    price_increase_pct: float
    price_increase_usd: float
    yield_loss_pct: float
    yield_loss_tons: float
    elasticity: float
    forward_contract_recommendation: str
    revenue_impact: Dict[str, float]


class CalculateFinancialsRequest(BaseModel):
    cash_flows: List[float] = Field(..., min_length=2)
    discount_rate: float = Field(..., ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/cba-series")
def cba_series(req: CBARequest) -> dict:
    """Calculate a Cost-Benefit Analysis time series for a climate adaptation project."""
    try:
        start_year = datetime.now().year

        standard_rate = req.standard_interest_rate
        green_rate = req.standard_interest_rate - (req.greenium_discount_bps / 10_000)
        n = req.bond_tenor_years
        principal = req.capex

        def _annuity_payment(p: float, r: float, periods: int) -> float:
            if r == 0:
                return p / periods
            return p * r / (1.0 - (1.0 + r) ** -periods)

        standard_annual_payment = _annuity_payment(principal, standard_rate, n)
        green_annual_payment = _annuity_payment(principal, green_rate, n)
        total_greenium_savings = (standard_annual_payment - green_annual_payment) * n

        baseline_insurance = req.base_insurance_premium
        adjusted_insurance_premium = req.base_insurance_premium * (1.0 - req.insurance_reduction_pct)
        annual_carbon_revenue = req.annual_carbon_credits * req.carbon_price_per_ton

        baseline_cumulative = 0.0
        intervention_cumulative = req.capex
        breakeven_year: Optional[int] = None
        time_series: list[dict] = []
        residual_damage = req.annual_baseline_damage * (1.0 - req.damage_reduction_pct)

        for yr in range(1, req.lifespan_years + 1):
            discount_factor = (1.0 + req.discount_rate) ** yr
            discounted_baseline = (req.annual_baseline_damage + baseline_insurance) / discount_factor
            baseline_cumulative += discounted_baseline

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


@router.post("/cvar-simulation")
def cvar_simulation(req: CVaRRequest) -> dict:
    """Run a Monte Carlo simulation to estimate Climate Value at Risk (CVaR)."""
    try:
        damage_pcts = np.random.normal(req.mean_damage_pct, req.volatility_pct, req.num_simulations)
        damage_pcts = np.maximum(damage_pcts, 0.0)
        losses = damage_pcts * req.asset_value

        expected_loss = float(np.mean(losses))
        cvar_95 = float(np.percentile(losses, 95))
        cvar_99 = float(np.percentile(losses, 99))

        counts, bin_edges = np.histogram(losses, bins=40)
        distribution = [
            {"loss_amount": round(float(bin_edges[i]), 2), "frequency": int(counts[i])}
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


@router.post("/blended-structure", response_model=BlendedFinanceResponse)
def blended_finance_structure(req: BlendedFinanceRequest) -> BlendedFinanceResponse:
    """Calculate blended cost of capital with climate resilience-based interest rate discounts."""
    try:
        BASE_COMMERCIAL_RATE = 0.065
        CONCESSIONAL_RATE = 0.020
        MUNICIPAL_EQUITY_RATE = 0.0
        LOAN_TERM_YEARS = 20

        greenium_discount_bps = 0.0
        if req.resilience_score >= 80:
            greenium_discount_bps = 50.0
        elif req.resilience_score >= 60:
            greenium_discount_bps = 25.0

        greenium_discount = greenium_discount_bps / 10_000.0
        applied_commercial_rate = BASE_COMMERCIAL_RATE - greenium_discount

        commercial_debt_amount = req.total_capex * req.tranches.commercial_debt_pct
        concessional_grant_amount = req.total_capex * req.tranches.concessional_grant_pct
        municipal_equity_amount = req.total_capex * req.tranches.municipal_equity_pct

        blended_interest_rate = (
            (req.tranches.commercial_debt_pct * applied_commercial_rate) +
            (req.tranches.concessional_grant_pct * CONCESSIONAL_RATE) +
            (req.tranches.municipal_equity_pct * MUNICIPAL_EQUITY_RATE)
        )

        debt_principal = commercial_debt_amount + concessional_grant_amount

        def calculate_annual_payment(principal: float, rate: float, periods: int) -> float:
            if rate == 0:
                return principal / periods
            return principal * rate / (1.0 - (1.0 + rate) ** -periods)

        annual_debt_service = calculate_annual_payment(debt_principal, blended_interest_rate, LOAN_TERM_YEARS) if debt_principal > 0 else 0.0

        if commercial_debt_amount > 0:
            base_commercial_payment = calculate_annual_payment(commercial_debt_amount, BASE_COMMERCIAL_RATE, LOAN_TERM_YEARS)
            discounted_commercial_payment = calculate_annual_payment(commercial_debt_amount, applied_commercial_rate, LOAN_TERM_YEARS)
            annual_savings = base_commercial_payment - discounted_commercial_payment
            total_greenium_savings = annual_savings * LOAN_TERM_YEARS
        else:
            total_greenium_savings = 0.0

        INSURANCE_DISCOUNT_FACTOR = 0.50
        insurance_savings = req.base_insurance_premium * (req.risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR)
        adjusted_insurance_premium = req.base_insurance_premium - insurance_savings

        net_annual_debt_service = max(0.0, annual_debt_service - req.annual_carbon_revenue - insurance_savings)

        sensitivity_analysis = None
        if req.rate_shock_bps is not None:
            rate_shock_decimal = req.rate_shock_bps / 10_000.0
            stressed_commercial_rate = applied_commercial_rate + rate_shock_decimal
            stressed_blended_rate = (
                (req.tranches.commercial_debt_pct * stressed_commercial_rate) +
                (req.tranches.concessional_grant_pct * CONCESSIONAL_RATE) +
                (req.tranches.municipal_equity_pct * MUNICIPAL_EQUITY_RATE)
            )
            stressed_annual_payment = calculate_annual_payment(debt_principal, stressed_blended_rate, LOAN_TERM_YEARS) if debt_principal > 0 else 0.0
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
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/price-shock", response_model=PriceShockResponse)
def price_shock(req: PriceShockRequest) -> dict:
    """Calculate commodity price shock from climate-induced yield loss."""
    try:
        return calculate_price_shock(
            crop_type=req.crop_type,
            baseline_yield_tons=req.baseline_yield_tons,
            stressed_yield_tons=req.stressed_yield_tons
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/calculate")
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
        return legacy_error(400, f"Invalid numeric values: {str(ve)}", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        return legacy_error(500, f"Financial calculation failed: {str(e)}", "CALCULATION_ERROR")
