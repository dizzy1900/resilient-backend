# /predict-health Quick Reference Card

## Request Format

```json
{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0,
  "intervention_type": "hvac_retrofit",        // OPTIONAL
  "intervention_capex": 250000.0,              // OPTIONAL
  "intervention_annual_opex": 30000.0          // OPTIONAL
}
```

## Intervention Types (Exact Strings)

✅ **CORRECT:**
- `"hvac_retrofit"` - Drops WBGT to 22°C
- `"passive_cooling"` - Reduces WBGT by 3°C
- `"none"` - Baseline only

❌ **INCORRECT (will not work):**
- `"HVAC Retrofit"` - Has space, not underscore
- `"hvac retrofit"` - Has space, not underscore
- `"HvacRetrofit"` - Needs underscore

**Note:** Case-insensitive (`"HVAC_RETROFIT"` works), but **underscore is required**.

---

## Response Path Quick Lookup

### Check If Intervention Was Applied

```javascript
if (response.data.intervention_analysis) {
  // Intervention applied
} else {
  // Baseline only
}
```

### Access Intervention Metrics

| Metric | JSON Path | Type |
|--------|-----------|------|
| **Baseline WBGT** | `data.intervention_analysis.wbgt_adjustment.baseline_wbgt` | number |
| **Adjusted WBGT** | `data.intervention_analysis.wbgt_adjustment.adjusted_wbgt` | number |
| **WBGT Reduction** | `data.intervention_analysis.wbgt_adjustment.wbgt_reduction` | number |
| **Avoided Annual Loss** | `data.intervention_analysis.economic_impact.avoided_annual_economic_loss_usd` | number |
| **Payback Period** | `data.intervention_analysis.financial_analysis.payback_period_years` | number\|null |
| **NPV (10-year)** | `data.intervention_analysis.financial_analysis.npv_10yr_at_10pct_discount` | number\|null |
| **BCR** | `data.intervention_analysis.financial_analysis.bcr` | number\|null |
| **Recommendation** | `data.intervention_analysis.financial_analysis.roi_recommendation` | string |

---

## Complete Response Example

```json
{
  "status": "success",
  "data": {
    "intervention_analysis": {
      "intervention_type": "hvac_retrofit",
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
      }
    }
  }
}
```

---

## Null Value Handling

**⚠️ If `intervention_capex == 0`, these fields are `null`:**
- `net_annual_benefit`
- `payback_period_years`
- `npv_10yr_at_10pct_discount`
- `bcr`

**Frontend should check:**
```javascript
if (financial.payback_period_years !== null) {
  // Display payback
} else {
  // Display "N/A" or "No financial analysis"
}
```

---

## TypeScript Type

```typescript
interface InterventionAnalysis {
  intervention_type: string;
  intervention_description: string;
  wbgt_adjustment: {
    baseline_wbgt: number;
    adjusted_wbgt: number;
    wbgt_reduction: number;
  };
  productivity_impact: {
    baseline_productivity_loss_pct: number;
    adjusted_productivity_loss_pct: number;
    avoided_productivity_loss_pct: number;
  };
  economic_impact: {
    baseline_annual_loss_usd: number;
    adjusted_annual_loss_usd: number;
    avoided_annual_economic_loss_usd: number;
    working_days_per_year: number;
  };
  financial_analysis: {
    intervention_capex: number;
    intervention_annual_opex: number;
    net_annual_benefit: number | null;
    payback_period_years: number | null;
    npv_10yr_at_10pct_discount: number | null;
    bcr: number | null;
    roi_recommendation: string;
  };
  heat_stress_category_after_intervention: string;
  recommendation_after_intervention: string;
}
```

---

## Common Frontend Patterns

### Display Intervention Summary

```javascript
const intervention = response.data.intervention_analysis;

if (intervention) {
  return (
    <div>
      <h3>{intervention.intervention_type}</h3>
      <p>{intervention.intervention_description}</p>
      
      <div>
        <span>WBGT: {intervention.wbgt_adjustment.baseline_wbgt}°C → {intervention.wbgt_adjustment.adjusted_wbgt}°C</span>
        <span>Reduction: {intervention.wbgt_adjustment.wbgt_reduction}°C</span>
      </div>
      
      <div>
        <span>Avoided Loss: ${intervention.economic_impact.avoided_annual_economic_loss_usd.toLocaleString()}/year</span>
      </div>
      
      {intervention.financial_analysis.payback_period_years !== null && (
        <div>
          <span>Payback: {intervention.financial_analysis.payback_period_years.toFixed(1)} years</span>
          <span>NPV: ${intervention.financial_analysis.npv_10yr_at_10pct_discount.toLocaleString()}</span>
          <span>BCR: {intervention.financial_analysis.bcr.toFixed(1)}</span>
        </div>
      )}
      
      <p>{intervention.financial_analysis.roi_recommendation}</p>
    </div>
  );
}
```

### ROI Badge Color

```javascript
const getRecommendationColor = (recommendation) => {
  if (recommendation.includes('INVEST:')) return 'green';
  if (recommendation.includes('MARGINAL:')) return 'yellow';
  if (recommendation.includes('DO NOT INVEST:')) return 'red';
  return 'gray';
};
```

---

## Testing

### cURL Test

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

**For complete documentation, see:** `HEALTH_ENDPOINT_DATA_CONTRACT.md`
