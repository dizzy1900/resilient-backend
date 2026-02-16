# Flood Twin Implementation Summary

## Overview
Successfully implemented a complete Flood Twin Digital Twin system that predicts urban flood depths and evaluates green infrastructure interventions.

## Components Created

### 1. Training Script: `train_flood_surrogate.py`
- Generates 20,000 synthetic catchment scenarios
- **Input Features:**
  - `rain_intensity_mm_hr`: 10-150 mm/hr
  - `impervious_pct`: 0.0-1.0 (fraction)
  - `slope_pct`: 0.1-10.0%

- **Physics-Based Target:**
  - Uses Rational Method: Q = C × I × A
  - Dynamic composite C-value: C = (0.95 × impervious) + (0.10 × pervious)
  - Manning's equation for depth calculation

- **Model Performance:**
  - R² Score: 0.997 (excellent fit)
  - MAE: 0.022 cm
  - RMSE: 0.049 cm
  - Balanced feature importance (~34% each)

### 2. Trained Model: `flood_surrogate.pkl`
- RandomForestRegressor (100 estimators)
- Model size: 49MB
- Predicts flood depth in centimeters

### 3. API Endpoint: `/predict-flood`

#### Request Format
```json
{
  "rain_intensity": 100.0,           // mm/hr (10-150)
  "current_imperviousness": 0.7,     // fraction (0.0-1.0)
  "intervention_type": "green_roof", // see options below
  "slope_pct": 2.0                   // optional, default 2.0%
}
```

#### Intervention Types
Based on EPA and ASCE research:
- **`green_roof`**: 30% imperviousness reduction
- **`permeable_pavement`**: 40% imperviousness reduction
- **`bioswales`**: 25% imperviousness reduction
- **`rain_gardens`**: 20% imperviousness reduction
- **`none`**: 0% reduction (baseline)

#### Response Format
```json
{
  "status": "success",
  "data": {
    "input_conditions": {
      "rain_intensity_mm_hr": 100.0,
      "current_imperviousness": 0.7,
      "intervention_type": "green_roof",
      "slope_pct": 2.0
    },
    "imperviousness_change": {
      "baseline": 0.700,
      "intervention": 0.400,
      "reduction_factor": 0.3,
      "absolute_reduction": 0.300
    },
    "predictions": {
      "baseline_depth_cm": 2.52,
      "intervention_depth_cm": 1.92
    },
    "analysis": {
      "avoided_depth_cm": 0.60,
      "percentage_improvement": 24.0,
      "baseline_damage_pct": 0.79,
      "intervention_damage_pct": 0.60,
      "avoided_damage_pct": 0.19,
      "avoided_loss": 47078.94,
      "recommendation": "green_roof"
    },
    "economic_assumptions": {
      "num_buildings": 50,
      "avg_building_value": 500000,
      "damage_function": "FEMA HAZUS 1-story commercial",
      "total_value_basis": "Avoided structural damage across affected buildings"
    }
  }
}
```

## Economic Valuation

### FEMA HAZUS Depth-Damage Function
- Based on 1-story commercial buildings
- Formula: Damage% = 72% × (1 - e^(-0.1332 × depth_ft))
- Accounts for:
  - Structural damage
  - Contents damage
  - Cleanup costs
  - Business interruption

### Scale Assumptions
- **50 buildings** (typical urban block)
- **$500,000** average building value
- **Conservative estimates** for real-world applicability

## Test Results

### Test Case 1: Green Roof (30% reduction)
- **Input:** 100 mm/hr rain, 70% impervious, 2% slope
- **Baseline depth:** 2.52 cm
- **Intervention depth:** 1.92 cm
- **Avoided depth:** 0.60 cm (24% improvement)
- **Economic value:** $47,078 avoided damage

### Test Case 2: Permeable Pavement (40% reduction)
- **Input:** 80 mm/hr rain, 80% impervious, 3% slope
- **Baseline depth:** 2.07 cm
- **Intervention depth:** 1.47 cm
- **Avoided depth:** 0.60 cm (29% improvement)
- **Economic value:** $46,877 avoided damage

### Test Case 3: Rain Gardens (20% reduction)
- **Input:** 120 mm/hr rain, 60% impervious, 1.5% slope
- **Baseline depth:** 2.86 cm
- **Intervention depth:** 2.30 cm
- **Avoided depth:** 0.57 cm (19.8% improvement)
- **Economic value:** $44,127 avoided damage

### Test Case 4: No Intervention (0% reduction)
- **Input:** 50 mm/hr rain, 50% impervious, 2% slope
- **Baseline depth:** 1.42 cm
- **Intervention depth:** 1.42 cm
- **Avoided depth:** 0.00 cm (0% improvement)
- **Economic value:** $0 avoided damage

## Integration with Existing System

The `/predict-flood` endpoint follows the same patterns as existing endpoints:
- Uses `@validate_json` decorator for input validation
- Implements comprehensive error handling
- Returns structured JSON with nested and flat fields
- Includes economic assumptions for transparency
- Logs requests for debugging

## Scientific References

### Runoff Coefficients
- EPA SWMM 5.1 User's Manual (2015)
- Concrete/Asphalt: C = 0.95
- Grass/Pervious: C = 0.10

### Manning's Roughness
- Standard asphalt: n = 0.016

### Depth-Damage Functions
- USACE IWR Report 96-R-12 (1996)
- FEMA HAZUS Flood Model Technical Manual (2022)

### Green Infrastructure Effectiveness
- EPA Green Infrastructure Case Studies (2010)
- ASCE Low Impact Development Manual (2015)

## Usage Example

### Start the API
```bash
python3 main.py
```

### Test the Endpoint
```bash
curl -X POST http://localhost:5001/predict-flood \
  -H "Content-Type: application/json" \
  -d '{
    "rain_intensity": 100.0,
    "current_imperviousness": 0.7,
    "intervention_type": "green_roof",
    "slope_pct": 2.0
  }'
```

## Files Modified/Created
1. ✅ `train_flood_surrogate.py` - Training script
2. ✅ `flood_surrogate.pkl` - Trained model (49MB)
3. ✅ `main.py` - Updated with `/predict-flood` endpoint
4. ✅ `test_flood_logic.py` - Logic validation tests
5. ✅ `test_flood_endpoint.py` - API endpoint tests

## Next Steps (Optional)
1. Update `start.sh` to include flood model download/training
2. Add frontend integration for flood predictions
3. Implement additional intervention types (e.g., detention ponds, infiltration trenches)
4. Add location-based imperviousness detection using GEE
5. Expand to multiple building types (residential, industrial)

---

**Status:** ✅ Complete and tested
**Date:** 2026-01-29
