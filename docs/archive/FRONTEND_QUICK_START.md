# Frontend Quick Start - Flood Predictions

## TL;DR

**Endpoint:** `POST https://web-production-8ff9e.up.railway.app/predict-flood`  
**Status:** ✅ LIVE and working  
**Response Time:** ~180ms

---

## Minimal Example

```javascript
const response = await fetch(
  'https://web-production-8ff9e.up.railway.app/predict-flood',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      rain_intensity: 100,
      current_imperviousness: 0.7,
      intervention_type: 'green_roof'
    })
  }
);

const data = await response.json();
const avoidedLoss = data.data.analysis.avoided_loss;

console.log(`You'll avoid $${avoidedLoss.toLocaleString()} in flood damage!`);
// Output: "You'll avoid $47,079 in flood damage!"
```

---

## Request Format

```json
{
  "rain_intensity": 100.0,           // Required: 10-150 mm/hr
  "current_imperviousness": 0.7,     // Required: 0.0-1.0 (0.7 = 70%)
  "intervention_type": "green_roof", // Required: see options below
  "slope_pct": 2.0                   // Optional: default 2.0%
}
```

### Intervention Options

| Value | Description | Imperviousness Reduction |
|-------|-------------|--------------------------|
| `"green_roof"` | Green roofs on buildings | -30% |
| `"permeable_pavement"` | Permeable paving | -40% |
| `"bioswales"` | Bioswale drainage | -25% |
| `"rain_gardens"` | Rain gardens | -20% |
| `"none"` | No intervention | 0% |

---

## Response Format

```json
{
  "status": "success",
  "data": {
    "analysis": {
      "avoided_loss": 47078.94,           // ← Display this ($)
      "avoided_depth_cm": 0.6,            // ← Depth reduction (cm)
      "percentage_improvement": 24.0,      // ← Improvement (%)
      "recommendation": "green_roof"       // ← Best choice
    }
  }
}
```

**Key Fields:**
- `data.analysis.avoided_loss` → Dollar value to display
- `data.analysis.percentage_improvement` → % improvement
- `data.analysis.recommendation` → Suggested intervention

---

## Expected Values

### By Intervention Type

| Intervention | Typical Avoided Loss |
|--------------|---------------------|
| Green Roof | $35K - $50K |
| Permeable Pavement | $40K - $60K |
| Bioswales | $30K - $45K |
| Rain Gardens | $25K - $40K |
| None | $0 |

### By Rain Intensity

| Rain Level | Range | Typical Avoided Loss |
|------------|-------|---------------------|
| Light | 10-50 mm/hr | $15K - $30K |
| Moderate | 50-100 mm/hr | $30K - $60K |
| Heavy | 100-150 mm/hr | $50K - $90K |

---

## Error Handling

```javascript
try {
  const response = await fetch(API_URL + '/predict-flood', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const data = await response.json();
  
  if (data.status !== 'success') {
    throw new Error(data.message || 'Prediction failed');
  }

  return data.data.analysis.avoided_loss;

} catch (error) {
  console.error('Flood prediction error:', error);
  return null; // Or show error message to user
}
```

---

## Common Mistakes

### ❌ Wrong: Imperviousness as percentage
```javascript
{
  "current_imperviousness": 70  // WRONG!
}
```

### ✅ Correct: Imperviousness as decimal
```javascript
{
  "current_imperviousness": 0.7  // Correct (70%)
}
```

### ❌ Wrong: Invalid intervention
```javascript
{
  "intervention_type": "green-roof"  // WRONG! (hyphen)
}
```

### ✅ Correct: Valid intervention
```javascript
{
  "intervention_type": "green_roof"  // Correct (underscore)
}
```

---

## Same Code for All Three APIs

```javascript
const API_ENDPOINTS = {
  agricultural: '/predict',
  coastal: '/predict-coastal',
  flood: '/predict-flood'
};

async function getAvoidedLoss(type, params) {
  const response = await fetch(API_URL + API_ENDPOINTS[type], {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });

  const data = await response.json();
  
  // Same field path for ALL APIs!
  return data.data.analysis.avoided_loss;
}

// Use with any API
const floodLoss = await getAvoidedLoss('flood', {
  rain_intensity: 100,
  current_imperviousness: 0.7,
  intervention_type: 'green_roof'
});

const coastalLoss = await getAvoidedLoss('coastal', {
  lat: 25.76,
  lon: -80.19,
  mangrove_width: 50
});

const agLoss = await getAvoidedLoss('agricultural', {
  temp: 30,
  rain: 450
});
```

---

## Test It Right Now

```bash
curl -X POST https://web-production-8ff9e.up.railway.app/predict-flood \
  -H "Content-Type: application/json" \
  -d '{
    "rain_intensity": 100,
    "current_imperviousness": 0.7,
    "intervention_type": "green_roof"
  }'
```

**Expected Response:**
```json
{
  "status": "success",
  "data": {
    "analysis": {
      "avoided_loss": 47078.94,
      "percentage_improvement": 24.0,
      "recommendation": "green_roof"
    }
  }
}
```

---

## UI Display Examples

### Simple Display
```
✅ Avoided Loss: $47,079
📊 Improvement: 24%
💡 Recommendation: Green Roof
```

### Detailed Display
```
🌊 Urban Flood Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scenario:
• Rain Intensity: 100 mm/hr (Heavy)
• Current Imperviousness: 70%

Baseline (No Intervention):
• Flood Depth: 2.52 cm
• Estimated Damage: $98,500

With Green Roof:
• Flood Depth: 1.92 cm (↓ 24%)
• Estimated Damage: $51,421

✅ Avoided Loss: $47,079
💰 ROI: High
⏱️ Payback: 3-5 years
```

---

## Need Help?

- **Endpoint not working?** → Check `https://web-production-8ff9e.up.railway.app/health`
- **Getting $0 values?** → Check imperviousness is decimal (0.7 not 70)
- **Getting errors?** → Check intervention_type spelling (underscore not hyphen)
- **Still stuck?** → Check `/Users/david/adaptmetric-backend/FLOOD_FIX_VERIFICATION.md`

---

**Status:** ✅ Ready to integrate  
**Last Updated:** 2026-01-29  
**Production URL:** https://web-production-8ff9e.up.railway.app
