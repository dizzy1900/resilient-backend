# Healthcare Infrastructure Stress Testing

## Overview
Dynamic healthcare capacity stress testing that adapts based on the region's economic development tier. This feature models climate-induced hospital bed deficits and calculates infrastructure bond requirements.

## Updated Request Model

### New Fields in `PredictHealthRequest`

```python
class PredictHealthRequest(BaseModel):
    # ... existing fields ...
    
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
```

**New intervention type:** `"hospital_expansion"` - Triggers infrastructure stress testing ROI

## Research Data Dictionary

```python
research_data = {
    "high": {
        "beds_per_1000": 3.8,        # High-income baseline capacity
        "capex": 1000000,            # $1M per bed (advanced facilities)
        "occupancy": 0.72,           # 72% baseline occupancy
        "surge_pct": 0.035,          # 3.5% surge per °C temp increase
        "dalys_per_deficit": 2.5     # Lower DALYs (better outcomes)
    },
    "middle": {
        "beds_per_1000": 2.8,        # Middle-income capacity
        "capex": 250000,             # $250K per bed
        "occupancy": 0.75,           # 75% baseline occupancy
        "surge_pct": 0.075,          # 7.5% surge per °C
        "dalys_per_deficit": 4.8     # Moderate health burden
    },
    "low": {
        "beds_per_1000": 1.2,        # Low-income capacity
        "capex": 60000,              # $60K per bed (basic facilities)
        "occupancy": 0.80,           # 80% baseline occupancy (overstretched)
        "surge_pct": 0.135,          # 13.5% surge per °C (vulnerable)
        "dalys_per_deficit": 8.2     # Higher DALYs (worse outcomes)
    }
}
```

## Math Implementation

### Step 1: Set Active Variables

```python
# Get tier-specific parameters
active_tier = research_data.get(economy_tier, research_data["middle"])

# Allow user overrides
baseline_beds_per_1000 = user_beds_per_1000 or active_tier["beds_per_1000"]
cost_per_bed = user_cost_per_bed or active_tier["capex"]
```

### Step 2: Calculate Infrastructure Stress

```python
# Temperature increase from baseline
baseline_temp = 25.0  # °C
projected_temp_increase = max(0, temp_c - baseline_temp)

# Baseline hospital capacity
baseline_capacity = (population_size / 1000) * baseline_beds_per_1000

# Available beds after baseline occupancy
available_beds = baseline_capacity * (1.0 - active_tier["occupancy"])

# Climate-induced surge admissions (scales with temperature)
surge_admissions = baseline_capacity * (active_tier["surge_pct"] * projected_temp_increase)

# Bed deficit (if surge exceeds available capacity)
bed_deficit = max(0, surge_admissions - available_beds)

# Infrastructure bond CAPEX to address deficit
infrastructure_bond_capex = bed_deficit * cost_per_bed
```

### Step 3: Calculate Intervention ROI (if `intervention_type == "hospital_expansion"`)

```python
# DALYs averted by addressing bed deficit
dalys_averted = bed_deficit * active_tier["dalys_per_deficit"]

# WHO-CHOICE monetization (2x GDP per capita)
value_per_daly = 2.0 * gdp_per_capita_usd
economic_value_preserved = dalys_averted * value_per_daly

# Update public health analysis
public_health_analysis["intervention_type"] = "hospital_expansion"
public_health_analysis["dalys_averted"] = dalys_averted
public_health_analysis["economic_value_preserved_usd"] = economic_value_preserved
public_health_analysis["intervention_description"] = f"Hospital expansion adds {bed_deficit:.0f} beds to address climate-induced surge capacity"
```

## Response Structure

### New Response Block: `infrastructure_stress_test`

```json
{
  "infrastructure_stress_test": {
    "baseline_capacity": 1400.0,
    "available_beds": 350.0,
    "surge_admissions": 1050.0,
    "bed_deficit": 700.0,
    "infrastructure_bond_capex": 175000000.0,
    "capacity_breach": true,
    "applied_tier": "middle",
    "baseline_beds_per_1000": 2.8,
    "cost_per_bed": 250000.0,
    "projected_temp_increase": 10.0
  }
}
```

## Example Scenarios

### Example 1: Middle-Income Country, Extreme Heat

**Input:**
- Population: 500,000
- Temperature: 35°C (10°C above baseline)
- Economy tier: "middle"

**Calculation:**
- Baseline capacity: 500 × 2.8 = **1,400 beds**
- Available beds: 1,400 × (1 - 0.75) = **350 beds**
- Surge admissions: 1,400 × (0.075 × 10) = **1,050 beds**
- Bed deficit: 1,050 - 350 = **700 beds**
- Infrastructure CAPEX: 700 × $250,000 = **$175,000,000**
- DALYs averted: 700 × 4.8 = **3,360 DALYs**
- Economic value: 3,360 × (2 × $8,500) = **$57,120,000**

### Example 2: High-Income Country, Moderate Heat

**Input:**
- Population: 100,000
- Temperature: 30°C (5°C above baseline)
- Economy tier: "high"

**Calculation:**
- Baseline capacity: 100 × 3.8 = **380 beds**
- Available beds: 380 × (1 - 0.72) = **106 beds**
- Surge admissions: 380 × (0.035 × 5) = **67 beds**
- Bed deficit: max(0, 67 - 106) = **0 beds** (no breach!)
- Infrastructure CAPEX: **$0**
- Capacity breach: **false**

### Example 3: Low-Income Country, Moderate Heat

**Input:**
- Population: 100,000
- Temperature: 30°C (5°C above baseline)
- Economy tier: "low"

**Calculation:**
- Baseline capacity: 100 × 1.2 = **120 beds**
- Available beds: 120 × (1 - 0.80) = **24 beds**
- Surge admissions: 120 × (0.135 × 5) = **81 beds**
- Bed deficit: 81 - 24 = **57 beds**
- Infrastructure CAPEX: 57 × $60,000 = **$3,420,000**
- DALYs averted: 57 × 8.2 = **467 DALYs**
- Economic value: 467 × (2 × $3,000) = **$2,804,400**

## Tier Comparison

| Metric | High Income | Middle Income | Low Income |
|--------|-------------|---------------|------------|
| **Beds per 1,000** | 3.8 | 2.8 | 1.2 |
| **Cost per bed** | $1,000,000 | $250,000 | $60,000 |
| **Baseline occupancy** | 72% | 75% | 80% |
| **Surge per °C** | 3.5% | 7.5% | 13.5% |
| **DALYs per deficit** | 2.5 | 4.8 | 8.2 |
| **Resilience** | High | Medium | Low |

## Key Insights

1. **High-income countries** have more baseline capacity and lower surge rates → Less likely to breach
2. **Low-income countries** have less capacity, higher occupancy, and higher surge rates → More vulnerable
3. **Temperature sensitivity:** Each °C above baseline increases surge admissions
4. **Cost tradeoffs:** Low-income beds are cheaper but health outcomes worse (higher DALYs per deficit)

## User Override Example

### Scenario: Custom Hospital Configuration

```json
{
  "economy_tier": "middle",
  "user_beds_per_1000": 3.5,
  "user_cost_per_bed": 500000,
  "population_size": 200000,
  "intervention_type": "hospital_expansion"
}
```

**Effect:**
- Uses middle-income surge/occupancy parameters
- BUT uses custom capacity (3.5 beds/1000 instead of 2.8)
- AND uses custom cost ($500K instead of $250K)
- Allows modeling of hybrid scenarios (e.g., middle-income country with high-end hospital investment)

## Integration with Public Health DALY Analysis

When `intervention_type == "hospital_expansion"`:

1. Infrastructure stress test calculates bed deficit
2. Bed deficit → DALYs averted (using tier-specific multiplier)
3. DALYs averted → Economic value (using 2× GDP per capita)
4. `public_health_analysis` block updated with infrastructure intervention results
5. Frontend can display both infrastructure CAPEX and public health ROI

## API Usage

### Basic Request (Auto-detect tier)

```bash
POST /api/v1/health/predict-health
{
  "lat": 13.75,
  "lon": 100.52,
  "workforce_size": 1000,
  "daily_wage": 50,
  "population_size": 500000,
  "economy_tier": "middle"
}
```

### Hospital Expansion Intervention

```bash
POST /api/v1/health/predict-health
{
  "lat": 13.75,
  "lon": 100.52,
  "workforce_size": 1000,
  "daily_wage": 50,
  "population_size": 500000,
  "gdp_per_capita_usd": 8500,
  "economy_tier": "middle",
  "intervention_type": "hospital_expansion"
}
```

### With User Overrides

```bash
POST /api/v1/health/predict-health
{
  "lat": 13.75,
  "lon": 100.52,
  "workforce_size": 1000,
  "daily_wage": 50,
  "population_size": 500000,
  "economy_tier": "low",
  "user_beds_per_1000": 2.0,
  "user_cost_per_bed": 100000,
  "intervention_type": "hospital_expansion"
}
```

## Testing

Run infrastructure stress tests:
```bash
python3 tests/test_infrastructure_stress.py
```

All 3 tests passing:
- ✅ Math calculation accuracy
- ✅ Tier comparison (high/middle/low)
- ✅ User override functionality

## References

- WHO GHE 2019: Global Health Estimates
- World Bank: Hospital bed density by income group
- Climate health literature: Temperature-admission relationships
- WHO-CHOICE: Cost-effectiveness thresholds
