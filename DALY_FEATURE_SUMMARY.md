# Public Health DALY Feature - Summary for Frontend Team

## What Changed

The `/predict-health` endpoint now calculates **DALYs (Disability-Adjusted Life Years)** for public sector users (governments, WHO, NGOs) who need population-level health burden analysis.

---

## 1. Updated Request Model

### New Optional Fields Added

```python
class PredictHealthRequest(BaseModel):
    # ... existing fields ...
    lat: float
    lon: float
    workforce_size: int
    daily_wage: float
    intervention_type: Optional[str] = None
    intervention_capex: Optional[float] = None
    intervention_annual_opex: Optional[float] = None
    
    # NEW FIELDS FOR PUBLIC HEALTH
    population_size: Optional[int] = 100000      # Default: 100,000
    gdp_per_capita_usd: Optional[float] = 8500.0  # Default: $8,500
```

### Example Request with DALY Fields

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

---

## 2. New DALY Function in `health_engine.py`

```python
def calculate_public_health_impact(
    population: int,
    gdp_per_capita: float,
    wbgt: float,
    malaria_risk_score: int,
    intervention_type: str = "none"
) -> Dict
```

### Scientific Baselines

- **Heat DALYs:** 1.82 per 1,000 people (WHO GHE 2019)
- **Malaria DALYs:** 105 per 1,000 people (GBD 2019)

### Intervention Efficacy

| Intervention Type | Heat Reduction | Malaria Reduction |
|-------------------|----------------|-------------------|
| `"urban_cooling_center"` | 40% | 0% |
| `"mosquito_eradication"` | 0% | 70% |
| `"none"` | 0% | 0% |

### DALY Calculation

1. **Baseline DALYs:**
   - Heat: Scales with WBGT severity (26-32°C range)
   - Malaria: Scales with risk score (0-100)
   
2. **Apply Intervention:**
   - Reduce DALYs by intervention efficacy
   
3. **Calculate Averted DALYs:**
   - `dalys_averted = baseline - post_intervention`
   
4. **Monetize (WHO Standard):**
   - `economic_value = dalys_averted × (gdp_per_capita × 2)`

---

## 3. Updated Response Structure

### New Response Block: `public_health_analysis`

The response now includes a **new sibling block** to `economic_impact`:

```json
{
  "status": "success",
  "data": {
    "location": { /* ... */ },
    "climate_conditions": { /* ... */ },
    "heat_stress_analysis": { /* ... */ },
    "malaria_risk_analysis": { /* ... */ },
    "economic_impact": { /* ... */ },
    "workforce_parameters": { /* ... */ },
    
    "public_health_analysis": {
      "baseline_dalys_lost": 26705.0,
      "post_intervention_dalys_lost": 22598.0,
      "dalys_averted": 4107.0,
      "economic_value_preserved_usd": 98568000.0,
      "intervention_type": "urban_cooling_center",
      "intervention_description": "Urban cooling centers reduce heat-related DALYs by 40%",
      "breakdown": {
        "heat_dalys_per_1000_baseline": 1.46,
        "malaria_dalys_per_1000_baseline": 105.0,
        "total_dalys_per_1000_baseline": 106.46,
        "heat_reduction_pct": 40.0,
        "malaria_reduction_pct": 0.0
      },
      "monetization": {
        "gdp_per_capita_usd": 12000.0,
        "value_per_daly_usd": 24000.0,
        "methodology": "WHO-CHOICE standard: 2× GDP per capita per DALY"
      },
      "population_parameters": {
        "population_size": 250000,
        "baseline_dalys_per_1000": 106.46,
        "post_intervention_dalys_per_1000": 90.39
      }
    },
    
    "intervention_analysis": { /* Optional - for workplace cooling CBA */ }
  }
}
```

---

## 4. Complete Dummy JSON Response

### Scenario: Bangkok with Urban Cooling Centers

```json
{
  "status": "success",
  "data": {
    "location": {
      "lat": 13.7563,
      "lon": 100.5018
    },
    "climate_conditions": {
      "temperature_c": 32.5,
      "precipitation_mm": 1450.0,
      "humidity_pct_estimated": 80.0
    },
    "heat_stress_analysis": {
      "wbgt_estimate": 30.8,
      "productivity_loss_pct": 40.0,
      "heat_stress_category": "Very High",
      "recommendation": "All work affected, frequent breaks required",
      "inputs": {
        "temperature_c": 32.5,
        "humidity_pct": 80.0
      }
    },
    "malaria_risk_analysis": {
      "risk_score": 100,
      "risk_category": "High",
      "description": "Climate conditions highly suitable for malaria transmission",
      "climate_suitability": {
        "temperature_suitable": true,
        "precipitation_suitable": true,
        "temperature_c": 32.5,
        "precipitation_mm": 1450.0
      },
      "risk_factors": [
        "Temperature in optimal range (16-34°C)",
        "Precipitation sufficient (1450mm > 80mm threshold)"
      ],
      "mitigation_measures": [
        "Use insecticide-treated bed nets",
        "Indoor residual spraying",
        "Eliminate standing water",
        "Prophylactic medication for high-risk areas",
        "Early diagnosis and treatment"
      ]
    },
    "economic_impact": {
      "heat_stress_impact": {
        "daily_productivity_loss": 5000.0,
        "annual_productivity_loss": 1250000.0,
        "affected_workers": 500,
        "loss_per_worker_daily": 10.0
      },
      "malaria_impact": {
        "estimated_days_lost_per_worker": 10,
        "annual_absenteeism_cost": 125000.0,
        "annual_healthcare_costs": 5000.0
      },
      "total_economic_impact": {
        "annual_loss": 1380000.0,
        "daily_loss_average": 5520.0,
        "per_worker_annual_loss": 2760.0
      }
    },
    "workforce_parameters": {
      "workforce_size": 500,
      "daily_wage": 25.0,
      "currency": "USD"
    },
    "public_health_analysis": {
      "baseline_dalys_lost": 26705.0,
      "post_intervention_dalys_lost": 22598.0,
      "dalys_averted": 4107.0,
      "economic_value_preserved_usd": 98568000.0,
      "intervention_type": "urban_cooling_center",
      "intervention_description": "Urban cooling centers reduce heat-related DALYs by 40%",
      "breakdown": {
        "heat_dalys_per_1000_baseline": 1.46,
        "malaria_dalys_per_1000_baseline": 105.0,
        "total_dalys_per_1000_baseline": 106.46,
        "heat_reduction_pct": 40.0,
        "malaria_reduction_pct": 0.0
      },
      "monetization": {
        "gdp_per_capita_usd": 12000.0,
        "value_per_daly_usd": 24000.0,
        "methodology": "WHO-CHOICE standard: 2× GDP per capita per DALY"
      },
      "population_parameters": {
        "population_size": 250000,
        "baseline_dalys_per_1000": 106.46,
        "post_intervention_dalys_per_1000": 90.39
      }
    }
  }
}
```

---

## 5. Frontend Mapping - Key Paths

| UI Field | JSON Path | Type | Units |
|----------|-----------|------|-------|
| **Baseline DALYs Lost** | `data.public_health_analysis.baseline_dalys_lost` | number | DALYs |
| **DALYs Averted** | `data.public_health_analysis.dalys_averted` | number | DALYs |
| **Economic Value Preserved** | `data.public_health_analysis.economic_value_preserved_usd` | number | USD |
| **Intervention Type** | `data.public_health_analysis.intervention_type` | string | - |
| **Intervention Description** | `data.public_health_analysis.intervention_description` | string | - |
| **Heat Reduction %** | `data.public_health_analysis.breakdown.heat_reduction_pct` | number | % |
| **Malaria Reduction %** | `data.public_health_analysis.breakdown.malaria_reduction_pct` | number | % |
| **Population Size** | `data.public_health_analysis.population_parameters.population_size` | number | people |
| **Value per DALY** | `data.public_health_analysis.monetization.value_per_daly_usd` | number | USD |

---

## 6. TypeScript Interface

```typescript
interface PublicHealthAnalysis {
  baseline_dalys_lost: number;
  post_intervention_dalys_lost: number;
  dalys_averted: number;
  economic_value_preserved_usd: number;
  intervention_type: string;
  intervention_description: string;
  breakdown: {
    heat_dalys_per_1000_baseline: number;
    malaria_dalys_per_1000_baseline: number;
    total_dalys_per_1000_baseline: number;
    heat_reduction_pct: number;
    malaria_reduction_pct: number;
  };
  monetization: {
    gdp_per_capita_usd: number;
    value_per_daly_usd: number;
    methodology: string;
  };
  population_parameters: {
    population_size: number;
    baseline_dalys_per_1000: number;
    post_intervention_dalys_per_1000: number;
  };
}
```

---

## 7. Example Usage

### Request: Baseline Assessment (No Intervention)

```bash
curl -X POST http://localhost:8000/predict-health \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 13.7563,
    "lon": 100.5018,
    "workforce_size": 500,
    "daily_wage": 25.0,
    "population_size": 100000,
    "gdp_per_capita_usd": 10000.0,
    "intervention_type": "none"
  }'
```

### Request: Urban Cooling Centers

```bash
curl -X POST http://localhost:8000/predict-health \
  -H "Content-Type: application/json" \
  -d '{
    "lat": 13.7563,
    "lon": 100.5018,
    "workforce_size": 500,
    "daily_wage": 25.0,
    "population_size": 250000,
    "gdp_per_capita_usd": 12000.0,
    "intervention_type": "urban_cooling_center"
  }'
```

### Request: Mosquito Eradication

```bash
curl -X POST http://localhost:8000/predict-health \
  -H "Content-Type: application/json" \
  -d '{
    "lat": -1.2864,
    "lon": 36.8172,
    "workforce_size": 1000,
    "daily_wage": 10.0,
    "population_size": 500000,
    "gdp_per_capita_usd": 2000.0,
    "intervention_type": "mosquito_eradication"
  }'
```

---

## 8. Interpretation Guide

### Understanding the Numbers

**Baseline DALYs Lost:** Total health burden from climate-induced heat stress and malaria
- Low burden: < 100 DALYs per 100,000 people
- Moderate: 100-1,000 DALYs
- High: > 1,000 DALYs

**DALYs Averted:** Health benefit from intervention
- Each DALY averted = 1 full healthy life year preserved

**Economic Value Preserved:** Monetary value using WHO standard
- Formula: DALYs averted × (2 × GDP per capita)
- Used for cost-effectiveness analysis

### Cost-Effectiveness Thresholds (WHO-CHOICE)

- **Very cost-effective:** Intervention cost < 1× GDP per capita per DALY
- **Cost-effective:** Intervention cost < 2× GDP per capita per DALY
- **Not cost-effective:** Intervention cost > 2× GDP per capita per DALY

**Example:**
- GDP per capita: $10,000
- DALYs averted: 1,000
- Economic value: $20 million
- If intervention costs $15M → BCR = 1.33 → ✅ Cost-effective
- If intervention costs $25M → BCR = 0.80 → ❌ Not cost-effective

---

## 9. Use Cases

### Public Sector User: Ministry of Health
- **Goal:** Assess national climate health burden
- **Use:** Set `population_size` to national population, use `intervention_type: "none"` for baseline

### Public Sector User: City Government
- **Goal:** Justify cooling center budget
- **Use:** Set `intervention_type: "urban_cooling_center"`, compare economic value vs. budget

### NGO/WHO: Malaria Program
- **Goal:** Evaluate eradication program ROI
- **Use:** Set `intervention_type: "mosquito_eradication"`, calculate BCR

### Climate Fund Proposal
- **Goal:** Request funding for adaptation project
- **Use:** Show `economic_value_preserved_usd` as benefit in funding proposal

---

## 10. Key Differences from Cooling CBA

| Feature | Cooling CBA (`intervention_analysis`) | Public Health DALY |
|---------|--------------------------------------|-------------------|
| **Target User** | Private sector (businesses, factories) | Public sector (governments, WHO, NGOs) |
| **Metric** | Worker productivity loss (%) | DALYs (population health burden) |
| **Scale** | Workforce (hundreds to thousands) | Population (thousands to millions) |
| **Intervention** | HVAC retrofit, passive cooling | Urban cooling centers, mosquito eradication |
| **Valuation** | Avoided wage loss (direct economic) | WHO standard (2× GDP per capita) |
| **Use Case** | Workplace investment decisions | Public health policy, climate adaptation |

**Both features can coexist in the same response!**

---

**For complete technical documentation, see:** `docs/HEALTH_DALY_PUBLIC_SECTOR.md`

**Frontend Integration Checklist:**
- [ ] Add `population_size` and `gdp_per_capita_usd` to request form
- [ ] Display `public_health_analysis` metrics in dedicated card/section
- [ ] Show DALYs averted as primary KPI
- [ ] Show economic value as secondary KPI
- [ ] Include intervention description for context
- [ ] Add tooltips explaining DALY concept
- [ ] Use WHO cost-effectiveness thresholds for recommendations

---

**Status:** ✅ Production Ready  
**Last Updated:** 2026-03-01  
**API Version:** v1.0.0
