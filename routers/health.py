"""Health prediction endpoints — heat stress, malaria, DALY analysis."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from auth import get_current_user
from models import User
from gee_connector import get_weather_data
from financial_engine import calculate_npv
from routers._shared import legacy_error

router = APIRouter(prefix="/api/v1/health", tags=["Health"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class PredictHealthRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    workforce_size: int = Field(..., gt=0)
    daily_wage: float = Field(..., gt=0)
    intervention_type: Optional[str] = Field(
        None,
        description="Cooling intervention type: 'hvac_retrofit', 'passive_cooling', 'hospital_expansion', 'urban_cooling_center', 'mosquito_eradication', or 'none'",
    )
    intervention_capex: Optional[float] = Field(None, ge=0)
    intervention_annual_opex: Optional[float] = Field(None, ge=0)
    population_size: Optional[int] = Field(100000, gt=0)
    gdp_per_capita_usd: Optional[float] = Field(8500.0, gt=0)
    economy_tier: Optional[str] = Field("middle")
    user_beds_per_1000: Optional[float] = Field(None, ge=0)
    user_cost_per_bed: Optional[float] = Field(None, ge=0)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/predict")
async def predict_health(req: PredictHealthRequest, user: User = Depends(get_current_user)):
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
        from health_engine import (
            calculate_productivity_loss,
            calculate_malaria_risk,
            calculate_health_economic_impact,
            calculate_public_health_impact,
        )

        lat = req.lat
        lon = req.lon
        workforce_size = req.workforce_size
        daily_wage = req.daily_wage

        intervention_type = req.intervention_type or "none"
        intervention_capex = req.intervention_capex or 0.0
        intervention_annual_opex = req.intervention_annual_opex or 0.0

        population_size = req.population_size or 100000
        gdp_per_capita_usd = req.gdp_per_capita_usd or 8500.0

        economy_tier = (req.economy_tier or "middle").lower()
        user_beds_per_1000 = req.user_beds_per_1000
        user_cost_per_bed = req.user_cost_per_bed

        print(
            f"[HEALTH REQUEST] lat={lat}, lon={lon}, workforce={workforce_size}, wage=${daily_wage}, "
            f"intervention={intervention_type}, population={population_size}, gdp_per_capita=${gdp_per_capita_usd}, "
            f"economy_tier={economy_tier}",
            file=sys.stderr,
            flush=True,
        )

        # ── Fetch climate data ──────────────────────────────────────────
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            weather_data = await run_in_threadpool(
                get_weather_data,
                lat=lat,
                lon=lon,
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

            print(
                f"[HEALTH] Climate data: temp={temp_c}°C, precip={precip_mm}mm, humidity_est={humidity_pct}%",
                file=sys.stderr,
                flush=True,
            )

        except Exception as weather_error:
            print(f"Weather data error: {weather_error}", file=sys.stderr, flush=True)
            return legacy_error(500, f"Failed to fetch climate data: {str(weather_error)}", "WEATHER_DATA_ERROR")

        # ── BASELINE ANALYSIS ───────────────────────────────────────────
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

        print(
            f"[HEALTH] BASELINE: WBGT={baseline_wbgt}°C, loss={baseline_productivity_loss_pct}%, "
            f"annual_loss=${economic_impact_baseline['heat_stress_impact']['annual_productivity_loss']:,.2f}",
            file=sys.stderr,
            flush=True,
        )

        # ── INTERVENTION ANALYSIS ───────────────────────────────────────
        intervention_analysis = None

        private_sector_interventions = ["hvac_retrofit", "passive_cooling"]

        is_private_sector_intervention = (
            intervention_type
            and intervention_type.lower() not in ["none", ""]
            and intervention_type.lower() in private_sector_interventions
        )

        if is_private_sector_intervention:
            adjusted_wbgt = baseline_wbgt
            wbgt_reduction = 0.0

            if intervention_type.lower() == "hvac_retrofit":
                adjusted_wbgt = 22.0
                wbgt_reduction = baseline_wbgt - adjusted_wbgt
                intervention_description = "Active HVAC cooling system maintains safe 22°C WBGT"
            elif intervention_type.lower() == "passive_cooling":
                wbgt_reduction = 3.0
                adjusted_wbgt = max(baseline_wbgt - wbgt_reduction, 20.0)
                intervention_description = "Passive cooling (ventilation, shading, green roofs) reduces WBGT by 3°C"

            if wbgt_reduction > 0:
                adjusted_temp = temp_c - (wbgt_reduction / 0.7)
                productivity_analysis_adjusted = calculate_productivity_loss(adjusted_temp, humidity_pct)
            else:
                productivity_analysis_adjusted = productivity_analysis_baseline

            adjusted_productivity_loss_pct = productivity_analysis_adjusted["productivity_loss_pct"]
            avoided_productivity_loss_pct = baseline_productivity_loss_pct - adjusted_productivity_loss_pct

            economic_impact_adjusted = calculate_health_economic_impact(
                workforce_size=workforce_size,
                daily_wage=daily_wage,
                productivity_loss_pct=adjusted_productivity_loss_pct,
                malaria_risk_score=malaria_analysis["risk_score"],
            )

            working_days_per_year = 260
            baseline_annual_heat_loss = economic_impact_baseline["heat_stress_impact"]["annual_productivity_loss"]
            adjusted_annual_heat_loss = economic_impact_adjusted["heat_stress_impact"]["annual_productivity_loss"]
            avoided_annual_economic_loss_usd = baseline_annual_heat_loss - adjusted_annual_heat_loss

            print(
                f"[HEALTH] INTERVENTION: WBGT={adjusted_wbgt}°C, loss={adjusted_productivity_loss_pct}%, "
                f"avoided_loss=${avoided_annual_economic_loss_usd:,.2f}/year",
                file=sys.stderr,
                flush=True,
            )

            # ── FINANCIAL ROI ANALYSIS ──────────────────────────────────
            payback_period_years = None
            npv_10yr = None
            bcr = None
            roi_recommendation = "No financial analysis (zero CAPEX)"

            if intervention_capex > 0:
                net_annual_benefit = avoided_annual_economic_loss_usd - intervention_annual_opex

                if net_annual_benefit > 0:
                    payback_period_years = intervention_capex / net_annual_benefit
                else:
                    payback_period_years = None

                discount_rate = 0.10
                analysis_period = 10

                cash_flows = [-intervention_capex] + [net_annual_benefit] * analysis_period
                npv_result = calculate_npv(cash_flows, discount_rate)
                npv_10yr = npv_result

                pv_benefits = sum(
                    avoided_annual_economic_loss_usd / ((1 + discount_rate) ** year)
                    for year in range(1, analysis_period + 1)
                )
                pv_costs = intervention_capex + sum(
                    intervention_annual_opex / ((1 + discount_rate) ** year)
                    for year in range(1, analysis_period + 1)
                )
                bcr = pv_benefits / pv_costs if pv_costs > 0 else 0.0

                if npv_10yr > 0 and bcr > 1.0:
                    roi_recommendation = "✅ INVEST: Positive NPV and BCR > 1.0 - financially attractive"
                elif npv_10yr > 0:
                    roi_recommendation = "⚠️ MARGINAL: Positive NPV but low BCR - consider alternative interventions"
                else:
                    roi_recommendation = "❌ DO NOT INVEST: Negative NPV - OPEX and CAPEX exceed productivity gains"

                safe_npv = npv_10yr if npv_10yr is not None else 0.0
                safe_payback = payback_period_years if payback_period_years is not None else 0.0
                safe_bcr = bcr if bcr is not None else 0.0
                print(
                    f"[HEALTH] ROI: NPV=${safe_npv:,.2f}, Payback={safe_payback:.1f}yr, BCR={safe_bcr:.2f}",
                    file=sys.stderr,
                    flush=True,
                )

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

        # ── PUBLIC HEALTH DALY ANALYSIS ─────────────────────────────────
        public_health_analysis = calculate_public_health_impact(
            population=population_size,
            gdp_per_capita=gdp_per_capita_usd,
            wbgt=baseline_wbgt,
            malaria_risk_score=malaria_analysis["risk_score"],
            intervention_type=intervention_type,
        )

        print(
            f"[HEALTH] PUBLIC HEALTH: baseline_dalys={public_health_analysis['baseline_dalys_lost']}, "
            f"averted={public_health_analysis['dalys_averted']}, "
            f"value=${public_health_analysis['economic_value_preserved_usd']:,.2f}",
            file=sys.stderr,
            flush=True,
        )

        # ── HEALTHCARE INFRASTRUCTURE STRESS TESTING ────────────────────
        research_data = {
            "high": {"beds_per_1000": 3.8, "capex": 1000000, "occupancy": 0.72, "surge_pct": 0.035, "dalys_per_deficit": 2.5},
            "middle": {"beds_per_1000": 2.8, "capex": 250000, "occupancy": 0.75, "surge_pct": 0.075, "dalys_per_deficit": 4.8},
            "low": {"beds_per_1000": 1.2, "capex": 60000, "occupancy": 0.80, "surge_pct": 0.135, "dalys_per_deficit": 8.2},
        }

        active_tier = research_data.get(economy_tier, research_data["middle"])

        baseline_beds_per_1000 = user_beds_per_1000 if user_beds_per_1000 is not None else active_tier["beds_per_1000"]
        cost_per_bed = user_cost_per_bed if user_cost_per_bed is not None else active_tier["capex"]

        baseline_temp = 25.0
        projected_temp_increase = max(0, temp_c - baseline_temp)

        baseline_capacity = (population_size / 1000) * baseline_beds_per_1000
        available_beds = baseline_capacity * (1.0 - active_tier["occupancy"])
        surge_admissions = baseline_capacity * (active_tier["surge_pct"] * projected_temp_increase)
        bed_deficit = max(0, surge_admissions - available_beds)
        infrastructure_bond_capex = bed_deficit * cost_per_bed

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
            "projected_temp_increase": round(projected_temp_increase, 1),
        }

        if intervention_type and intervention_type.lower() == "hospital_expansion":
            dalys_averted_infrastructure = bed_deficit * active_tier["dalys_per_deficit"]
            value_per_daly = 2.0 * gdp_per_capita_usd
            economic_value_preserved_infrastructure = dalys_averted_infrastructure * value_per_daly

            public_health_analysis["intervention_type"] = "hospital_expansion"
            public_health_analysis["dalys_averted"] = round(dalys_averted_infrastructure, 1)
            public_health_analysis["economic_value_preserved_usd"] = round(economic_value_preserved_infrastructure, 2)
            public_health_analysis["intervention_description"] = (
                f"Hospital expansion adds {bed_deficit:.0f} beds to address climate-induced surge capacity"
            )

            intervention_capex = infrastructure_bond_capex

            print(
                f"[HEALTH] HOSPITAL EXPANSION: bed_deficit={bed_deficit:.0f}, capex=${infrastructure_bond_capex:,.2f}, "
                f"dalys_averted={dalys_averted_infrastructure:.1f}, value=${economic_value_preserved_infrastructure:,.2f}",
                file=sys.stderr,
                flush=True,
            )

        print(
            f"[HEALTH] INFRASTRUCTURE STRESS: capacity={baseline_capacity:.0f}, surge={surge_admissions:.0f}, "
            f"deficit={bed_deficit:.0f}, capex=${infrastructure_bond_capex:,.2f}",
            file=sys.stderr,
            flush=True,
        )

        # ── RESPONSE ────────────────────────────────────────────────────
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

        if intervention_analysis:
            response_data["intervention_analysis"] = intervention_analysis

        return {"status": "success", "data": response_data}

    except ValueError as ve:
        return legacy_error(400, f"Invalid numeric values: {str(ve)}", "INVALID_NUMERIC_VALUE")
    except Exception as e:
        print(f"Health prediction error: {e}", file=sys.stderr, flush=True)
        import traceback

        traceback.print_exc()
        return legacy_error(500, f"Health analysis failed: {str(e)}", "HEALTH_ERROR")
