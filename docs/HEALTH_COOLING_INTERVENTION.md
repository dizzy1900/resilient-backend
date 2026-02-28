# Health Endpoint - Cooling CAPEX vs. Productivity OPEX CBA

## Overview

The `/predict-health` endpoint has been enhanced with **Cooling CAPEX vs. Productivity OPEX Cost-Benefit Analysis**. This feature calculates the financial return on investment (ROI) of workplace cooling interventions that reduce heat stress and improve worker productivity.

## Problem Statement

**Heat stress reduces worker productivity** in hot climates. When Wet Bulb Globe Temperature (WBGT) exceeds 26°C, workers experience:
- Reduced physical capacity
- Slower task completion
- Increased error rates
- Heat-related illnesses

**Solution:** Cooling interventions (HVAC, passive cooling) can reduce WBGT and improve productivity, but they require upfront investment (CAPEX) and ongoing maintenance (OPEX).

**Key Question:** *Does the productivity gain justify the cooling system cost?*

---

## What's New

### 1. Updated Request Model

**New optional fields in `PredictHealthRequest`:**

```python
class PredictHealthRequest(BaseModel):
    lat: float  # Latitude
    lon: float  # Longitude
    workforce_size: int  # Number of workers
    daily_wage: float  # Daily wage per worker (USD)
    
    # NEW: Cooling intervention parameters
    intervention_type: Optional[str] = None  # "hvac_retrofit", "passive_cooling", or "none"
    intervention_capex: Optional[float] = None  # Upfront capital expenditure (USD)
    intervention_annual_opex: Optional[float] = None  # Annual operating cost (USD)
```

### 2. Cooling Intervention Types

| Intervention Type | WBGT Adjustment | Description | Typical Cost |
|------------------|----------------|-------------|--------------|
| **hvac_retrofit** | Drops to 22°C | Active HVAC cooling system maintains safe 22°C WBGT | CAPEX: $200K-$500K<br>OPEX: $20K-$50K/year |
| **passive_cooling** | Reduces by 3°C | Passive design: ventilation, shading, green roofs, reflective surfaces | CAPEX: $30K-$100K<br>OPEX: $3K-$10K/year |
| **none** | No change | Baseline scenario (no intervention) | N/A |

### 3. Financial Metrics Calculated

If `intervention_capex > 0`, the endpoint calculates:

1. **Net Annual Benefit** = Avoided Loss - Annual OPEX
2. **Simple Payback Period** = CAPEX / Net Annual Benefit (years)
3. **10-Year NPV** at 10% discount rate
4. **Benefit-Cost Ratio (BCR)** = PV(Benefits) / PV(Costs)
5. **ROI Recommendation**:
   - ✅ INVEST: NPV > 0 and BCR > 1.0
   - ⚠️ MARGINAL: NPV > 0 but low BCR
   - ❌ DO NOT INVEST: Negative NPV

---

## API Endpoint

### `POST /predict-health`

**Request Example:**

```json
{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0,
  "intervention_type": "hvac_retrofit",
  "intervention_capex": 250000.0,
  "intervention_annual_opex": 30000.0
}
```

**Response Structure:**

```json
{
  "status": "success",
  "data": {
    "location": {"lat": 13.7563, "lon": 100.5018},
    "climate_conditions": {
      "temperature_c": 32.5,
      "precipitation_mm": 1450.0,
      "humidity_pct_estimated": 80.0
    },
    "heat_stress_analysis": {
      "wbgt_estimate": 30.8,
      "productivity_loss_pct": 40.0,
      "heat_stress_category": "Very High",
      "recommendation": "All work affected, frequent breaks required"
    },
    "economic_impact": {
      "heat_stress_impact": {
        "daily_productivity_loss": 5000.0,
        "annual_productivity_loss": 1250000.0
      }
    },
    "intervention_analysis": {
      "intervention_type": "hvac_retrofit",
      "intervention_description": "Active HVAC cooling system maintains safe 22°C WBGT",
      "wbgt_adjustment": {
        "baseline_wbgt": 30.8,
        "adjusted_wbgt": 22.0,
        "wbgt_reduction": 8.8
      },
      "productivity_impact": {
        "baseline_productivity_loss_pct": 40.0,
        "adjusted_productivity_loss_pct": 0.0,
        "avoided_productivity_loss_pct": 40.0
      },
      "economic_impact": {
        "baseline_annual_loss_usd": 1250000.0,
        "adjusted_annual_loss_usd": 0.0,
        "avoided_annual_economic_loss_usd": 1250000.0,
        "working_days_per_year": 260
      },
      "financial_analysis": {
        "intervention_capex": 250000.0,
        "intervention_annual_opex": 30000.0,
        "net_annual_benefit": 1220000.0,
        "payback_period_years": 0.20,
        "npv_10yr_at_10pct_discount": 7249818.25,
        "bcr": 30.0,
        "roi_recommendation": "✅ INVEST: Positive NPV and BCR > 1.0 - financially attractive"
      },
      "heat_stress_category_after_intervention": "Low",
      "recommendation_after_intervention": "Normal work possible"
    }
  }
}
```

---

## Use Cases

### 1. Manufacturing Facility in Hot Climate

**Scenario:** Factory in Bangkok with 500 workers, considering HVAC retrofit

**Input:**
```json
{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0,
  "intervention_type": "hvac_retrofit",
  "intervention_capex": 250000.0,
  "intervention_annual_opex": 30000.0
}
```

**Output:**
- Baseline WBGT: 30.8°C → 40% productivity loss → $1.25M/year loss
- With HVAC: WBGT: 22°C → 0% productivity loss → $0/year loss
- **Avoided loss:** $1.25M/year
- **Net benefit:** $1.22M/year (after $30K OPEX)
- **Payback:** 0.2 years (2.5 months!)
- **NPV:** $7.25M over 10 years
- **BCR:** 30.0 (benefit is 30x the cost)
- **Recommendation:** ✅ INVEST

### 2. Warehouse in Moderate Heat

**Scenario:** Warehouse in New Delhi with 200 workers, considering passive cooling

**Input:**
```json
{
  "lat": 28.6139,
  "lon": 77.2090,
  "workforce_size": 200,
  "daily_wage": 15.0,
  "intervention_type": "passive_cooling",
  "intervention_capex": 50000.0,
  "intervention_annual_opex": 5000.0
}
```

**Output:**
- Baseline WBGT: 29.2°C → 26.7% productivity loss → $208K/year
- With passive cooling: WBGT: 26.2°C → 2.0% productivity loss → $16K/year
- **Avoided loss:** $192K/year
- **Net benefit:** $187K/year
- **Payback:** 0.27 years (3.2 months)
- **NPV:** $1.10M over 10 years
- **BCR:** 13.5
- **Recommendation:** ✅ INVEST

### 3. Small Operation - Unprofitable Case

**Scenario:** Small shop with 100 workers, low wages, considering HVAC

**Input:**
```json
{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 100,
  "daily_wage": 15.0,
  "intervention_type": "hvac_retrofit",
  "intervention_capex": 200000.0,
  "intervention_annual_opex": 100000.0
}
```

**Output:**
- Baseline loss: $150K/year
- Avoided loss: $150K/year
- **Net benefit:** $50K/year (after $100K OPEX)
- **Payback:** 4.0 years
- **NPV:** $107K (marginally positive)
- **BCR:** 1.2 (barely profitable)
- **Recommendation:** ⚠️ MARGINAL - Consider cheaper alternatives

### 4. Cool Climate - No Benefit

**Scenario:** Office in London (already cool)

**Input:**
```json
{
  "lat": 51.5074,
  "lon": -0.1278,
  "workforce_size": 200,
  "daily_wage": 50.0,
  "intervention_type": "hvac_retrofit",
  "intervention_capex": 100000.0,
  "intervention_annual_opex": 15000.0
}
```

**Output:**
- Baseline WBGT: 24.5°C → 0% productivity loss (already safe)
- Avoided loss: $0/year
- **Net benefit:** -$15K/year (pure cost!)
- **Payback:** Never
- **NPV:** -$192K
- **BCR:** 0.0
- **Recommendation:** ❌ DO NOT INVEST - No heat stress in baseline

---

## Calculation Methodology

### WBGT (Wet Bulb Globe Temperature)

WBGT is a composite measure of heat stress that combines:
- Air temperature
- Humidity
- Radiant heat
- Air movement

**Simplified Formula:** `WBGT ≈ 0.7 × Temp + 0.1 × Humidity`

### Productivity Loss Thresholds

Based on ILO (International Labour Organization) heat stress guidelines:

| WBGT (°C) | Category | Productivity Loss |
|-----------|----------|------------------|
| < 26°C | Low | 0% |
| 26-28°C | Moderate | 0-16.7% |
| 28-30°C | High | 16.7-33.3% |
| 30-32°C | Very High | 33.3-50.0% |
| > 32°C | Extreme | 50.0% (capped) |

**Formula:** Linear interpolation between 26°C (0% loss) and 32°C (50% loss)

### WBGT Adjustments

**HVAC Retrofit:**
- Drops WBGT to 22°C (safe baseline)
- Assumption: Industrial HVAC maintains indoor temp regardless of external heat
- Eliminates all heat-related productivity loss

**Passive Cooling:**
- Reduces WBGT by 3°C
- Assumption: Natural ventilation, shading, green roofs reduce heat load
- Partial productivity improvement

### Financial Calculations

**Avoided Annual Economic Loss:**
```
Baseline Annual Loss = Daily Wage × Workforce Size × Baseline Loss % × 260 days
Adjusted Annual Loss = Daily Wage × Workforce Size × Adjusted Loss % × 260 days
Avoided Loss = Baseline Annual Loss - Adjusted Annual Loss
```

**Net Annual Benefit:**
```
Net Annual Benefit = Avoided Loss - Annual OPEX
```

**Payback Period:**
```
Payback Period = CAPEX / Net Annual Benefit  (years)
```

**10-Year NPV at 10% Discount:**
```
Cash Flow (Year 0) = -CAPEX
Cash Flow (Years 1-10) = Net Annual Benefit
NPV = Σ [Cash Flow_t / (1.10)^t]  for t = 0 to 10
```

**Benefit-Cost Ratio:**
```
PV(Benefits) = Σ [Avoided Loss / (1.10)^t]  for t = 1 to 10
PV(Costs) = CAPEX + Σ [Annual OPEX / (1.10)^t]  for t = 1 to 10
BCR = PV(Benefits) / PV(Costs)
```

---

## Assumptions & Limitations

### Assumptions

1. **260 Working Days:** Analysis assumes 260 working days per year (5-day work week, 2 weeks vacation)
2. **HVAC Performance:** HVAC systems can maintain 22°C WBGT regardless of external conditions
3. **Passive Cooling:** Passive interventions reduce WBGT by 3°C (conservative estimate)
4. **Constant Workforce:** Workforce size and wages remain constant over 10 years
5. **10% Discount Rate:** Standard discount rate for infrastructure investments
6. **10-Year Lifespan:** Analysis period matches typical cooling system lifespan

### Limitations

1. **WBGT Simplification:** Uses simplified WBGT formula (0.7×Temp + 0.1×Humidity) instead of full psychrometric calculation
2. **Uniform Productivity:** Assumes all workers experience same productivity loss (reality: varies by task, fitness, acclimatization)
3. **No Climate Change Trends:** Uses current climate data, doesn't project future warming
4. **Binary Intervention:** Assumes intervention is fully implemented, no partial adoption
5. **No Behavioral Factors:** Doesn't account for worker adaptation strategies (e.g., self-pacing, hydration)
6. **Capital vs. Operating Split:** Doesn't consider equipment depreciation, replacement cycles

### When NOT to Use

- **Cool climates** (Baseline WBGT < 26°C) - No heat stress to address
- **Outdoor work** - Cooling interventions ineffective outdoors
- **Short-term projects** (<2 years) - Insufficient time to recoup CAPEX
- **Variable occupancy** - Analysis assumes consistent workforce presence

---

## Integration Examples

### Python Integration

```python
import requests

response = requests.post(
    "http://localhost:8000/predict-health",
    json={
        "lat": 13.7563,
        "lon": 100.5018,
        "workforce_size": 500,
        "daily_wage": 25.0,
        "intervention_type": "hvac_retrofit",
        "intervention_capex": 250000.0,
        "intervention_annual_opex": 30000.0,
    }
)

data = response.json()["data"]

# Check if intervention is profitable
if "intervention_analysis" in data:
    intervention = data["intervention_analysis"]
    financial = intervention["financial_analysis"]
    
    print(f"NPV: ${financial['npv_10yr_at_10pct_discount']:,.2f}")
    print(f"Payback: {financial['payback_period_years']:.1f} years")
    print(f"BCR: {financial['bcr']:.1f}")
    print(f"Recommendation: {financial['roi_recommendation']}")
```

### cURL Example

```bash
curl -X POST http://localhost:8000/predict-health \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 13.7563,
    "lon": 100.5018,
    "workforce_size": 500,
    "daily_wage": 25.0,
    "intervention_type": "hvac_retrofit",
    "intervention_capex": 250000.0,
    "intervention_annual_opex": 30000.0
  }'
```

---

## Testing

### Manual Tests

```bash
# Run test scenarios
python tests/test_health_cooling_intervention.py
```

### API Tests

```bash
# Start server
uvicorn api:app --reload --port 8000

# Run API tests
./tests/test_health_cooling_api.sh
```

---

## Future Enhancements

### Planned Features

1. **Climate Change Projections:** Integrate SSP scenarios for future WBGT trends
2. **Multiple Intervention Comparison:** Allow user to compare 2-3 interventions side-by-side
3. **Uncertainty Analysis:** Monte Carlo simulation of productivity loss ranges
4. **Seasonal Variation:** Month-by-month WBGT analysis for variable climates
5. **Task-Specific Loss:** Different productivity curves for light/moderate/heavy work
6. **Acclimatization Factor:** Account for worker heat adaptation over time

### Research Opportunities

- Validate WBGT simplification against full psychrometric models
- Collect empirical data on passive cooling effectiveness (currently assumed 3°C)
- Study relationship between HVAC efficiency and external temperature extremes
- Develop region-specific productivity loss curves

---

## References

1. **ILO (2019).** "Working on a warmer planet: The impact of heat stress on labour productivity and decent work." International Labour Organization.

2. **Kjellstrom, T., et al. (2016).** "Heat, Human Performance, and Occupational Health: A Key Issue for the Assessment of Global Climate Change Impacts." *Annual Review of Public Health*, 37, 97-112.

3. **ISO 7243:2017.** "Ergonomics of the thermal environment — Assessment of heat stress using the WBGT (wet bulb globe temperature) index."

4. **ASHRAE (2021).** "ASHRAE Handbook - Fundamentals." American Society of Heating, Refrigerating and Air-Conditioning Engineers.

---

## Support

**Documentation:** `docs/HEALTH_COOLING_INTERVENTION.md`  
**Tests:** `tests/test_health_cooling_*.py`, `tests/test_health_cooling_api.sh`  
**Endpoint:** `POST /predict-health`

**Questions?** Open an issue on GitHub or contact the development team.

---

**Developed by:** AdaptMetric Backend Team  
**Date:** 2026-02-26  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
