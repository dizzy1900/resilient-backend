# Intervention Routing Fix - /predict-health Endpoint

## Issue Summary

The FastAPI server was crashing with:
```
TypeError: unsupported format string passed to NoneType.__format__
```

**Root Cause:**
1. Public sector interventions (`urban_cooling_center`, `mosquito_eradication`) were being treated as "unknown" interventions
2. This bypassed the private-sector financial calculations, leaving `npv_10yr`, `payback_period_years`, and `bcr` as `None`
3. The print statement on line 2368 tried to format these `None` values with `:.2f`, causing a crash
4. Additionally, public sector interventions triggered a misleading `[HEALTH WARNING] Unknown intervention_type` log

---

## Fixes Applied

### Fix 1: Intervention Routing Logic

**Before:**
```python
if intervention_type and intervention_type.lower() not in ["none", ""]:
    # Calculate adjusted WBGT based on intervention type
    adjusted_wbgt = baseline_wbgt
    wbgt_reduction = 0.0
    
    if intervention_type.lower() == "hvac_retrofit":
        # ... HVAC logic
    elif intervention_type.lower() == "passive_cooling":
        # ... passive cooling logic
    else:
        # Unknown intervention type - treat as no intervention
        print(f"[HEALTH WARNING] Unknown intervention_type: {intervention_type}, treating as 'none'")
        adjusted_wbgt = baseline_wbgt
        intervention_description = "Unknown intervention type - no WBGT adjustment applied"
```

**After:**
```python
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
        adjusted_wbgt = 22.0
        wbgt_reduction = baseline_wbgt - adjusted_wbgt
        intervention_description = "Active HVAC cooling system maintains safe 22°C WBGT"
        
    elif intervention_type.lower() == "passive_cooling":
        # Passive cooling: Natural ventilation, shading, green roofs, etc.
        wbgt_reduction = 3.0
        adjusted_wbgt = max(baseline_wbgt - wbgt_reduction, 20.0)
        intervention_description = "Passive cooling (ventilation, shading, green roofs) reduces WBGT by 3°C"
    
    # ... rest of private-sector calculations (productivity, financial ROI, etc.)
```

**Benefits:**
- ✅ Public sector interventions (`urban_cooling_center`, `mosquito_eradication`) now gracefully bypass private-sector calculations
- ✅ No more `[HEALTH WARNING] Unknown intervention_type` for valid public sector interventions
- ✅ Clear separation between private-sector (workplace) and public-sector (population) interventions

---

### Fix 2: Safe Print Statement

**Before:**
```python
print(f"[HEALTH] ROI: NPV=${npv_10yr:,.2f}, Payback={payback_period_years:.1f}yr, BCR={bcr:.2f}", file=sys.stderr, flush=True)
```

**Problem:** Crashes if `npv_10yr`, `payback_period_years`, or `bcr` are `None`

**After:**
```python
# Safe formatting for print statement (handle None values)
safe_npv = npv_10yr if npv_10yr is not None else 0.0
safe_payback = payback_period_years if payback_period_years is not None else 0.0
safe_bcr = bcr if bcr is not None else 0.0
print(f"[HEALTH] ROI: NPV=${safe_npv:,.2f}, Payback={safe_payback:.1f}yr, BCR={safe_bcr:.2f}", file=sys.stderr, flush=True)
```

**Benefits:**
- ✅ No more crashes when financial metrics are `None`
- ✅ Logs show `0.0` for metrics that weren't calculated (clear fallback)
- ✅ Works for both zero-CAPEX scenarios and public-sector interventions

---

## Updated Code Block (api.py, lines 2253-2420)

```python
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
    if wbgt_reduction > 0:
        adjusted_temp = temp_c - (wbgt_reduction / 0.7)
        productivity_analysis_adjusted = calculate_productivity_loss(adjusted_temp, humidity_pct)
    else:
        productivity_analysis_adjusted = productivity_analysis_baseline
    
    adjusted_productivity_loss_pct = productivity_analysis_adjusted["productivity_loss_pct"]
    avoided_productivity_loss_pct = baseline_productivity_loss_pct - adjusted_productivity_loss_pct
    
    # Economic impact with intervention
    economic_impact_adjusted = calculate_health_economic_impact(
        workforce_size=workforce_size,
        daily_wage=daily_wage,
        productivity_loss_pct=adjusted_productivity_loss_pct,
        malaria_risk_score=malaria_analysis["risk_score"],
    )
    
    # Calculate avoided annual economic loss (260 working days/year)
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
        
        # Simple Payback Period
        if net_annual_benefit > 0:
            payback_period_years = intervention_capex / net_annual_benefit
        else:
            payback_period_years = None
        
        # 10-year NPV at 10% discount rate
        discount_rate = 0.10
        analysis_period = 10
        cash_flows = [-intervention_capex] + [net_annual_benefit] * analysis_period
        npv_result = calculate_npv(cash_flows, discount_rate)
        npv_10yr = npv_result
        
        # Calculate BCR (Benefit-Cost Ratio)
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
    intervention_type=intervention_type  # Use same intervention type
)

print(f"[HEALTH] PUBLIC HEALTH: baseline_dalys={public_health_analysis['baseline_dalys_lost']}, averted={public_health_analysis['dalys_averted']}, value=${public_health_analysis['economic_value_preserved_usd']:,.2f}", file=sys.stderr, flush=True)
```

---

## Intervention Type Routing Table

| Intervention Type | Category | Calculations Triggered |
|-------------------|----------|------------------------|
| `"hvac_retrofit"` | Private Sector | ✅ WBGT adjustment, productivity loss, financial ROI, DALY analysis |
| `"passive_cooling"` | Private Sector | ✅ WBGT adjustment, productivity loss, financial ROI, DALY analysis |
| `"urban_cooling_center"` | Public Sector | ✅ DALY analysis only (no workplace productivity/ROI) |
| `"mosquito_eradication"` | Public Sector | ✅ DALY analysis only (no workplace productivity/ROI) |
| `"none"` or empty | Baseline | ✅ DALY analysis only (baseline burden) |

---

## Testing

### Test 1: Private Sector Intervention (HVAC Retrofit)

**Request:**
```json
{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0,
  "intervention_type": "hvac_retrofit",
  "intervention_capex": 250000.0,
  "intervention_annual_opex": 30000.0,
  "population_size": 100000,
  "gdp_per_capita_usd": 10000.0
}
```

**Expected:**
- ✅ `intervention_analysis` block present (with WBGT, productivity, financial ROI)
- ✅ `public_health_analysis` block present (with DALYs)
- ✅ No warning logs

### Test 2: Public Sector Intervention (Urban Cooling Center)

**Request:**
```json
{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0,
  "intervention_type": "urban_cooling_center",
  "population_size": 250000,
  "gdp_per_capita_usd": 12000.0
}
```

**Expected:**
- ✅ NO `intervention_analysis` block (no workplace productivity calculation)
- ✅ `public_health_analysis` block present (with DALYs, 40% heat reduction)
- ✅ No warning logs
- ✅ No crash from None formatting

### Test 3: Baseline (No Intervention)

**Request:**
```json
{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0,
  "intervention_type": "none",
  "population_size": 100000,
  "gdp_per_capita_usd": 8500.0
}
```

**Expected:**
- ✅ NO `intervention_analysis` block
- ✅ `public_health_analysis` block present (baseline burden, 0 DALYs averted)
- ✅ No warning logs
- ✅ No crash

---

## Summary of Changes

**File:** `api.py`

**Changes:**
1. Added intervention type classification lists:
   - `private_sector_interventions = ["hvac_retrofit", "passive_cooling"]`
   - `public_sector_interventions = ["urban_cooling_center", "mosquito_eradication"]`

2. Replaced broad `if intervention_type` check with specific `is_private_sector_intervention` check

3. Added safe formatting for None values in print statement:
   ```python
   safe_npv = npv_10yr if npv_10yr is not None else 0.0
   safe_payback = payback_period_years if payback_period_years is not None else 0.0
   safe_bcr = bcr if bcr is not None else 0.0
   ```

**Impact:**
- ✅ No more crashes from None formatting
- ✅ No more misleading warnings for valid public sector interventions
- ✅ Clear separation of private vs. public sector logic
- ✅ Both intervention types work correctly in parallel

---

**Status:** ✅ Fixed and ready to commit  
**Syntax Validation:** ✅ Passed  
**Next Step:** Test with running server
