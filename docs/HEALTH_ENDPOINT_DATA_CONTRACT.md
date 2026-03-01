# /predict-health Endpoint - Complete Data Contract

## Endpoint

**`POST /predict-health`**

---

## 1. REQUEST PAYLOAD

### Required Fields

```json
{
  "lat": 13.7563,           // float, -90 to 90
  "lon": 100.5018,          // float, -180 to 180
  "workforce_size": 500,    // int, > 0
  "daily_wage": 25.0        // float, > 0 (USD)
}
```

### Optional Cooling Intervention Fields

```json
{
  "intervention_type": "hvac_retrofit",     // string, optional
  "intervention_capex": 250000.0,           // float, optional, >= 0 (USD)
  "intervention_annual_opex": 30000.0       // float, optional, >= 0 (USD)
}
```

### Field Specifications

#### `intervention_type` (Optional[str])

**EXACT ACCEPTED VALUES (case-insensitive):**
- `"hvac_retrofit"` - Active HVAC cooling (drops WBGT to 22°C)
- `"passive_cooling"` - Passive design improvements (reduces WBGT by 3°C)
- `"none"` - No intervention (baseline only)
- `null` or omitted - Same as "none"
- `""` (empty string) - Treated as "none"

**⚠️ IMPORTANT:** The endpoint uses `.lower()` for comparison, so:
- ✅ `"hvac_retrofit"` → Works
- ✅ `"HVAC_RETROFIT"` → Works
- ✅ `"Hvac_Retrofit"` → Works
- ❌ `"HVAC Retrofit"` → **DOES NOT WORK** (treated as unknown, no intervention applied)
- ❌ `"hvac retrofit"` → **DOES NOT WORK** (space instead of underscore)

**Correct snake_case format with underscore is REQUIRED.**

#### `intervention_capex` (Optional[float])

- **Default:** `0.0` if not provided
- **Validation:** `>= 0`
- **Units:** USD
- **Effect:** If `0.0`, financial analysis (NPV, payback, BCR) is skipped

#### `intervention_annual_opex` (Optional[float])

- **Default:** `0.0` if not provided
- **Validation:** `>= 0`
- **Units:** USD per year
- **Effect:** Subtracted from avoided loss to calculate net annual benefit

---

## 2. RESPONSE STRUCTURE

### Baseline Response (No Intervention)

When `intervention_type` is not provided or is `"none"`:

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
    }
  }
}
```

### Full Response (With Cooling Intervention)

When `intervention_type` is provided (e.g., `"hvac_retrofit"`):

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
        "payback_period_years": 0.2,
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

## 3. KEY FRONTEND MAPPING

### Critical Path: Accessing Intervention Metrics

**✅ Intervention analysis is located at:**
```javascript
response.data.intervention_analysis
```

**⚠️ This key only exists if:**
1. `intervention_type` was provided in the request
2. `intervention_type` is not `"none"` or `""`

**Check for presence:**
```javascript
if (response.data.intervention_analysis) {
  // Intervention was applied
} else {
  // Baseline only
}
```

### Exact Key Paths for UI Fields

| UI Field | JSON Path | Type | Units |
|----------|-----------|------|-------|
| **Baseline WBGT** | `data.intervention_analysis.wbgt_adjustment.baseline_wbgt` | float | °C |
| **Adjusted WBGT** | `data.intervention_analysis.wbgt_adjustment.adjusted_wbgt` | float | °C |
| **WBGT Reduction** | `data.intervention_analysis.wbgt_adjustment.wbgt_reduction` | float | °C |
| **Baseline Productivity Loss** | `data.intervention_analysis.productivity_impact.baseline_productivity_loss_pct` | float | % |
| **Adjusted Productivity Loss** | `data.intervention_analysis.productivity_impact.adjusted_productivity_loss_pct` | float | % |
| **Avoided Productivity Loss** | `data.intervention_analysis.productivity_impact.avoided_productivity_loss_pct` | float | % |
| **Baseline Annual Loss** | `data.intervention_analysis.economic_impact.baseline_annual_loss_usd` | float | USD |
| **Adjusted Annual Loss** | `data.intervention_analysis.economic_impact.adjusted_annual_loss_usd` | float | USD |
| **Avoided Annual Loss** | `data.intervention_analysis.economic_impact.avoided_annual_economic_loss_usd` | float | USD |
| **Working Days/Year** | `data.intervention_analysis.economic_impact.working_days_per_year` | int | days |
| **CAPEX** | `data.intervention_analysis.financial_analysis.intervention_capex` | float | USD |
| **Annual OPEX** | `data.intervention_analysis.financial_analysis.intervention_annual_opex` | float | USD |
| **Net Annual Benefit** | `data.intervention_analysis.financial_analysis.net_annual_benefit` | float or null | USD |
| **Payback Period** | `data.intervention_analysis.financial_analysis.payback_period_years` | float or null | years |
| **NPV (10-year)** | `data.intervention_analysis.financial_analysis.npv_10yr_at_10pct_discount` | float or null | USD |
| **BCR** | `data.intervention_analysis.financial_analysis.bcr` | float or null | ratio |
| **ROI Recommendation** | `data.intervention_analysis.financial_analysis.roi_recommendation` | string | text |
| **Heat Stress Category (After)** | `data.intervention_analysis.heat_stress_category_after_intervention` | string | category |
| **Recommendation (After)** | `data.intervention_analysis.recommendation_after_intervention` | string | text |

### Financial Analysis Nullability

**⚠️ IMPORTANT:** If `intervention_capex == 0.0`, the following fields will be `null`:
- `net_annual_benefit`
- `payback_period_years`
- `npv_10yr_at_10pct_discount`
- `bcr`

**Example (Zero CAPEX):**
```json
{
  "financial_analysis": {
    "intervention_capex": 0.0,
    "intervention_annual_opex": 0.0,
    "net_annual_benefit": null,
    "payback_period_years": null,
    "npv_10yr_at_10pct_discount": null,
    "bcr": null,
    "roi_recommendation": "No financial analysis (zero CAPEX)"
  }
}
```

### Payback Period Edge Case

If `net_annual_benefit <= 0` (OPEX exceeds avoided loss):
```json
{
  "payback_period_years": null,
  "roi_recommendation": "❌ DO NOT INVEST: Negative NPV - OPEX and CAPEX exceed productivity gains"
}
```

---

## 4. FRONTEND INTEGRATION EXAMPLES

### TypeScript Interface

```typescript
interface PredictHealthRequest {
  lat: number;                        // -90 to 90
  lon: number;                        // -180 to 180
  workforce_size: number;             // > 0
  daily_wage: number;                 // > 0
  intervention_type?: string;         // "hvac_retrofit" | "passive_cooling" | "none"
  intervention_capex?: number;        // >= 0
  intervention_annual_opex?: number;  // >= 0
}

interface WBGTAdjustment {
  baseline_wbgt: number;
  adjusted_wbgt: number;
  wbgt_reduction: number;
}

interface ProductivityImpact {
  baseline_productivity_loss_pct: number;
  adjusted_productivity_loss_pct: number;
  avoided_productivity_loss_pct: number;
}

interface EconomicImpact {
  baseline_annual_loss_usd: number;
  adjusted_annual_loss_usd: number;
  avoided_annual_economic_loss_usd: number;
  working_days_per_year: number;
}

interface FinancialAnalysis {
  intervention_capex: number;
  intervention_annual_opex: number;
  net_annual_benefit: number | null;
  payback_period_years: number | null;
  npv_10yr_at_10pct_discount: number | null;
  bcr: number | null;
  roi_recommendation: string;
}

interface InterventionAnalysis {
  intervention_type: string;
  intervention_description: string;
  wbgt_adjustment: WBGTAdjustment;
  productivity_impact: ProductivityImpact;
  economic_impact: EconomicImpact;
  financial_analysis: FinancialAnalysis;
  heat_stress_category_after_intervention: string;
  recommendation_after_intervention: string;
}

interface PredictHealthResponse {
  status: "success" | "error";
  data?: {
    location: { lat: number; lon: number };
    climate_conditions: {
      temperature_c: number;
      precipitation_mm: number;
      humidity_pct_estimated: number;
    };
    heat_stress_analysis: {
      wbgt_estimate: number;
      productivity_loss_pct: number;
      heat_stress_category: string;
      recommendation: string;
      inputs: {
        temperature_c: number;
        humidity_pct: number;
      };
    };
    malaria_risk_analysis: object;
    economic_impact: object;
    workforce_parameters: object;
    intervention_analysis?: InterventionAnalysis;  // Optional
  };
  message?: string;
  code?: string;
}
```

### React Example

```tsx
const response = await fetch('/predict-health', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lat: 13.7563,
    lon: 100.5018,
    workforce_size: 500,
    daily_wage: 25.0,
    intervention_type: 'hvac_retrofit',
    intervention_capex: 250000.0,
    intervention_annual_opex: 30000.0,
  }),
});

const data = await response.json();

// Check if intervention was applied
if (data.data.intervention_analysis) {
  const intervention = data.data.intervention_analysis;
  
  // Display WBGT reduction
  console.log(`WBGT: ${intervention.wbgt_adjustment.baseline_wbgt}°C → ${intervention.wbgt_adjustment.adjusted_wbgt}°C`);
  console.log(`Reduction: ${intervention.wbgt_adjustment.wbgt_reduction}°C`);
  
  // Display financial metrics
  const financial = intervention.financial_analysis;
  console.log(`Avoided Loss: $${intervention.economic_impact.avoided_annual_economic_loss_usd.toLocaleString()}/year`);
  
  if (financial.payback_period_years !== null) {
    console.log(`Payback: ${financial.payback_period_years.toFixed(1)} years`);
    console.log(`NPV: $${financial.npv_10yr_at_10pct_discount.toLocaleString()}`);
    console.log(`BCR: ${financial.bcr.toFixed(1)}`);
  }
  
  console.log(`Recommendation: ${financial.roi_recommendation}`);
} else {
  console.log('Baseline analysis only (no intervention)');
}
```

---

## 5. VALIDATION RULES

### Request Validation

**FastAPI/Pydantic enforces:**
- `lat`: Must be between -90 and 90
- `lon`: Must be between -180 and 180
- `workforce_size`: Must be > 0 (positive integer)
- `daily_wage`: Must be > 0 (positive float)
- `intervention_capex`: Must be >= 0 if provided
- `intervention_annual_opex`: Must be >= 0 if provided

**Backend logic:**
- `intervention_type` is converted to lowercase for comparison
- If `intervention_type` not in `["hvac_retrofit", "passive_cooling"]`, treated as "none"
- Empty string `""` or `null` treated as "none"

### Response Guarantees

**Always present:**
- `status`: "success" or "error"
- `data.location`
- `data.climate_conditions`
- `data.heat_stress_analysis`
- `data.malaria_risk_analysis`
- `data.economic_impact`
- `data.workforce_parameters`

**Conditionally present:**
- `data.intervention_analysis`: Only if intervention was applied and is not "none"

**Within `intervention_analysis.financial_analysis`:**
- `net_annual_benefit`: `null` if `intervention_capex == 0`
- `payback_period_years`: `null` if `intervention_capex == 0` or `net_annual_benefit <= 0`
- `npv_10yr_at_10pct_discount`: `null` if `intervention_capex == 0`
- `bcr`: `null` if `intervention_capex == 0`

---

## 6. ERROR RESPONSES

### Invalid Inputs (400)

```json
{
  "status": "error",
  "message": "Invalid numeric values: ...",
  "code": "INVALID_NUMERIC_VALUE"
}
```

### Weather Data Failure (500)

```json
{
  "status": "error",
  "message": "Failed to fetch climate data: ...",
  "code": "WEATHER_DATA_ERROR"
}
```

### General Failure (500)

```json
{
  "status": "error",
  "message": "Health analysis failed: ...",
  "code": "HEALTH_ERROR"
}
```

---

## 7. WORKING DAYS CONSTANT

**⚠️ HARDCODED VALUE:** The endpoint uses **260 working days per year** for all calculations.

This is visible in:
```json
{
  "economic_impact": {
    "working_days_per_year": 260
  }
}
```

**Note:** This differs from the `health_engine.py` default of 250 days. The endpoint override takes precedence.

---

## 8. TESTING PAYLOADS

### Test 1: Baseline Only
```json
{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0
}
```

### Test 2: HVAC Retrofit
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

### Test 3: Passive Cooling
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

### Test 4: Zero CAPEX (Policy-based)
```json
{
  "lat": 1.3521,
  "lon": 103.8198,
  "workforce_size": 100,
  "daily_wage": 40.0,
  "intervention_type": "passive_cooling",
  "intervention_capex": 0.0,
  "intervention_annual_opex": 0.0
}
```

---

## Summary Checklist for Frontend

✅ **Request Fields:**
- [ ] `intervention_type` must use snake_case: `"hvac_retrofit"` or `"passive_cooling"`
- [ ] Case-insensitive but must use underscore, not space
- [ ] All three fields are optional

✅ **Response Structure:**
- [ ] Check for `data.intervention_analysis` existence before accessing
- [ ] Handle `null` values in `financial_analysis` when CAPEX is 0
- [ ] Handle `null` payback when OPEX exceeds benefit

✅ **Key Paths:**
- [ ] Adjusted WBGT: `data.intervention_analysis.wbgt_adjustment.adjusted_wbgt`
- [ ] Avoided Loss: `data.intervention_analysis.economic_impact.avoided_annual_economic_loss_usd`
- [ ] Payback: `data.intervention_analysis.financial_analysis.payback_period_years`
- [ ] NPV: `data.intervention_analysis.financial_analysis.npv_10yr_at_10pct_discount`
- [ ] BCR: `data.intervention_analysis.financial_analysis.bcr`
- [ ] Recommendation: `data.intervention_analysis.financial_analysis.roi_recommendation`

---

**Last Updated:** 2026-02-26  
**API Version:** 1.0.0  
**Status:** ✅ Production
