# NLG Nested Data Extraction Fix - health_public Module

## Issue Summary

The frontend was successfully calling `/api/v1/ai/executive-summary` with the `health_public` module, but the NLG engine was generating summaries with "0 DALYs" instead of the actual values.

**Root Cause:** The NLG engine was trying to extract data from the root level of `simulation_data`, but the actual metrics were nested inside `public_health_analysis`.

---

## The Problem

### Original Parsing Logic (BROKEN)

```python
def _generate_health_public_summary(location_name: str, data: Dict[str, Any]) -> str:
    try:
        # ❌ WRONG: Looking at root level
        dalys_averted = data.get('dalys_averted', 0.0)
        economic_value = data.get('economic_value_preserved_usd', 0.0)
        intervention_type = data.get('intervention_type', 'none')
        baseline_dalys = data.get('baseline_dalys_lost', 0.0)
        wbgt = data.get('wbgt_estimate', None)
        malaria_risk = data.get('malaria_risk_score', 0)
```

**Problem:** The `/predict-health` endpoint returns a nested structure where DALY metrics are inside `public_health_analysis`, not at the root level.

---

## The Solution

### Updated Parsing Logic (FIXED)

```python
def _generate_health_public_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for public health DALY analysis.
    
    Expected data structure (from /predict-health response):
    {
        "public_health_analysis": {
            "dalys_averted": float,
            "economic_value_preserved_usd": float,
            "intervention_type": str,
            "intervention_description": str,
            "baseline_dalys_lost": float
        },
        "heat_stress_analysis": {
            "wbgt_estimate": float
        },
        "malaria_risk_analysis": {
            "risk_score": int
        }
    }
    """
    try:
        # ✅ CORRECT: Extract from nested public_health_analysis
        public_health = data.get('public_health_analysis', {})
        dalys_averted = public_health.get('dalys_averted', 0.0)
        economic_value = public_health.get('economic_value_preserved_usd', 0.0)
        intervention_type = public_health.get('intervention_type', 'none')
        baseline_dalys = public_health.get('baseline_dalys_lost', 0.0)
        
        # ✅ CORRECT: Extract climate data from other top-level keys
        heat_stress = data.get('heat_stress_analysis', {})
        wbgt = heat_stress.get('wbgt_estimate', None)
        
        malaria_risk_data = data.get('malaria_risk_analysis', {})
        malaria_risk = malaria_risk_data.get('risk_score', 0)
```

---

## Data Structure Mapping

### Frontend Payload (from /predict-health)

```json
{
  "location": { "lat": 13.7563, "lon": 100.5018 },
  "climate_conditions": { "temperature_c": 32.5, ... },
  
  "heat_stress_analysis": {
    "wbgt_estimate": 30.8,              // ← Extract WBGT here
    "productivity_loss_pct": 40.0,
    "heat_stress_category": "Very High"
  },
  
  "malaria_risk_analysis": {
    "risk_score": 100,                  // ← Extract malaria risk here
    "risk_category": "High"
  },
  
  "public_health_analysis": {           // ← Main DALY data nested here
    "baseline_dalys_lost": 26614.0,
    "dalys_averted": 145.6,             // ✅ Extract this
    "economic_value_preserved_usd": 3494400.0,  // ✅ Extract this
    "intervention_type": "urban_cooling_center", // ✅ Extract this
    "intervention_description": "Urban cooling centers reduce heat-related DALYs by 40%"
  }
}
```

---

## Extraction Logic Breakdown

### Step 1: Extract Public Health Metrics
```python
public_health = data.get('public_health_analysis', {})
dalys_averted = public_health.get('dalys_averted', 0.0)           # 145.6
economic_value = public_health.get('economic_value_preserved_usd', 0.0)  # 3494400.0
intervention_type = public_health.get('intervention_type', 'none')      # "urban_cooling_center"
baseline_dalys = public_health.get('baseline_dalys_lost', 0.0)          # 26614.0
```

### Step 2: Extract Climate Context
```python
heat_stress = data.get('heat_stress_analysis', {})
wbgt = heat_stress.get('wbgt_estimate', None)  # 30.8

malaria_risk_data = data.get('malaria_risk_analysis', {})
malaria_risk = malaria_risk_data.get('risk_score', 0)  # 100
```

### Step 3: Build Summary
- **Sentence 1:** Uses `wbgt` and `malaria_risk` for hazard context
- **Sentence 2:** Uses `dalys_averted` and `intervention_type`
- **Sentence 3:** Uses `economic_value` for ROI recommendation

---

## Before vs. After

### Before Fix

**Request:**
```json
{
  "module_name": "health_public",
  "location_name": "Bangkok",
  "simulation_data": {
    "public_health_analysis": {
      "dalys_averted": 145.6,
      "economic_value_preserved_usd": 3494400.0
    }
  }
}
```

**Response (BROKEN):**
```json
{
  "summary_text": "Bangkok faces economic disruption from projected climate hazards. The baseline health burden is 0 DALYs lost annually without intervention. Please refer to the quantitative metrics provided in the dashboard for detailed cost-benefit analysis."
}
```

❌ **Problem:** Shows "0 DALYs" because it couldn't find data at root level

---

### After Fix

**Request:**
```json
{
  "module_name": "health_public",
  "location_name": "Bangkok",
  "simulation_data": {
    "heat_stress_analysis": {
      "wbgt_estimate": 30.8
    },
    "malaria_risk_analysis": {
      "risk_score": 100
    },
    "public_health_analysis": {
      "dalys_averted": 145.6,
      "economic_value_preserved_usd": 3494400.0,
      "intervention_type": "urban_cooling_center"
    }
  }
}
```

**Response (FIXED):**
```json
{
  "summary_text": "Bangkok faces severe economic disruption from projected climate hazards including extreme heat stress and high malaria transmission risk. Implementing urban cooling centers will avert 146 Disability-Adjusted Life Years (DALYs). This preserves $3.5 million in macroeconomic value, making it a highly favorable public sector investment."
}
```

✅ **Fixed:** Correctly extracts 145.6 DALYs and $3.5M economic value

---

## Intervention Type Formatting

### Additional Enhancement

The fix also improves intervention type handling when not in the predefined mapping:

```python
# Format intervention type: if not in mapping, convert underscores to spaces and title case
intervention_display = intervention_names.get(intervention_type.lower(), None)
if intervention_display is None:
    # Format raw intervention_type by replacing underscores and title casing
    intervention_display = intervention_type.replace('_', ' ').title().lower()
    if intervention_display == 'none':
        intervention_display = 'no intervention'
```

**Example:**
- Input: `"urban_cooling_center"`
- Mapped: `"urban cooling centers"` (from predefined mapping)

- Input: `"new_intervention_type"`
- Fallback: `"new intervention type"` (auto-formatted)

---

## Testing

### Test Suite: `tests/test_nlg_nested_extraction.py`

**4 comprehensive tests:**
1. ✅ Nested data extraction from actual /predict-health structure
2. ✅ High DALY scenario (large population)
3. ✅ Mosquito eradication intervention
4. ✅ Baseline (no intervention, 0 DALYs)

**Run Tests:**
```bash
cd /Users/david/resilient-backend
python3 tests/test_nlg_nested_extraction.py
```

**Result:** ✅ All 4 tests passed

---

## Example Test Output

```
TEST: Health Public Nested Data Extraction
==========================================
Location: Bangkok
Module: health_public

Extracted Data:
  - DALYs averted: 145.6
  - Economic value: $3,494,400
  - Intervention: urban_cooling_center
  - WBGT: 30.8°C
  - Malaria risk: 100

Generated Summary:
Bangkok faces severe economic disruption from projected climate hazards 
including extreme heat stress and high malaria transmission risk. 
Implementing urban cooling centers will avert 146 Disability-Adjusted 
Life Years (DALYs). This preserves $3.5 million in macroeconomic value, 
making it a highly favorable public sector investment.

✅ PASSED - Correctly extracted nested data
```

---

## Files Changed

| File | Change |
|------|--------|
| `nlg_engine.py` | Fixed nested data extraction in `_generate_health_public_summary()` |
| `tests/test_nlg_nested_extraction.py` | New test suite for nested extraction validation |
| `NLG_NESTED_EXTRACTION_FIX.md` | This documentation |

---

## Summary of Changes

### 1. Nested Data Extraction
- ✅ Extract from `public_health_analysis` instead of root
- ✅ Extract from `heat_stress_analysis` for WBGT
- ✅ Extract from `malaria_risk_analysis` for risk score

### 2. Improved Error Handling
- ✅ Use `.get()` with defaults to prevent KeyErrors
- ✅ Graceful fallback if nested keys missing

### 3. Better Intervention Formatting
- ✅ Auto-format unknown intervention types
- ✅ Convert underscores to spaces

---

## Frontend Integration

The frontend should pass the **entire `/predict-health` response** as `simulation_data`:

```typescript
// Correct frontend usage
const healthResponse = await fetch('/predict-health', {
  method: 'POST',
  body: JSON.stringify({
    lat: 13.7563,
    lon: 100.5018,
    workforce_size: 500,
    daily_wage: 25.0,
    population_size: 250000,
    gdp_per_capita_usd: 12000.0,
    intervention_type: 'urban_cooling_center'
  })
});

const healthData = await healthResponse.json();

// Generate executive summary with full response
const summaryResponse = await fetch('/api/v1/ai/executive-summary', {
  method: 'POST',
  body: JSON.stringify({
    module_name: 'health_public',
    location_name: 'Bangkok',
    simulation_data: healthData.data  // ← Pass entire data object
  })
});

const summary = await summaryResponse.json();
console.log(summary.summary_text);
// "Bangkok faces severe economic disruption from projected climate hazards..."
```

---

## Key Takeaways

1. **Always pass the full `/predict-health` response** to the NLG endpoint
2. **Don't cherry-pick fields** - let the NLG engine extract what it needs
3. **The fix handles nested structures correctly** - no more "0 DALYs"
4. **Tests validate real-world scenarios** - based on actual API responses

---

**Status:** ✅ Fixed and tested  
**Tests:** ✅ All passing  
**Ready for:** Production deployment
