# Commodity Price Shock Engine

## Overview

The Commodity Price Shock Engine calculates how climate-induced crop yield losses affect local commodity prices through supply elasticity dynamics. When climate stress (drought, floods, heat waves) reduces agricultural yields, commodity prices spike due to supply shortages—this engine quantifies that price response and provides hedging recommendations.

## Theory

### Price Elasticity of Supply

**Definition:** Price Elasticity of Supply (ε) measures how responsive supply is to price changes:

```
ε = (% change in quantity supplied) / (% change in price)
```

**Inverse Relationship:** When supply drops, prices rise according to:

```
% price change = (% supply change) / ε
```

### Agricultural Commodities are Inelastic

For agricultural commodities, short-run supply elasticity is typically **0.1 - 0.5** (highly inelastic) because:

1. **Biological constraints:** Crops take months to grow
2. **Fixed land:** Farmers can't quickly expand acreage
3. **Capital intensity:** Equipment, irrigation, inputs are fixed
4. **Seasonal production:** Can't respond mid-season

**Result:** Small yield losses cause large price spikes.

### Example: Maize

- **Elasticity:** 0.25
- **Yield loss:** 10%
- **Price increase:** 10% / 0.25 = **40%**

A 10% drought-induced yield loss causes a 40% price spike!

## Supported Crops

### Grains (Highly Inelastic)
| Crop | Baseline Price ($/ton) | Elasticity | Price Impact* |
|------|----------------------:|------------|--------------|
| Maize/Corn | $180 | 0.25 | 1% loss → 4.0% price ↑ |
| Wheat | $220 | 0.30 | 1% loss → 3.3% price ↑ |
| Rice | $450 | 0.20 | 1% loss → 5.0% price ↑ |
| Barley | $200 | 0.28 | 1% loss → 3.6% price ↑ |
| Sorghum | $170 | 0.30 | 1% loss → 3.3% price ↑ |
| Millet | $300 | 0.35 | 1% loss → 2.9% price ↑ |

### Oilseeds (Moderately Inelastic)
| Crop | Baseline Price ($/ton) | Elasticity | Price Impact* |
|------|----------------------:|------------|--------------|
| Soybeans/Soy | $450 | 0.35 | 1% loss → 2.9% price ↑ |
| Canola/Rapeseed | $500 | 0.40 | 1% loss → 2.5% price ↑ |
| Sunflower | $420 | 0.38 | 1% loss → 2.6% price ↑ |

### Cash Crops (Highly Inelastic)
| Crop | Baseline Price ($/ton) | Elasticity | Price Impact* |
|------|----------------------:|------------|--------------|
| Cocoa | $2,500 | 0.15 | 1% loss → 6.7% price ↑ |
| Coffee | $3,500 | 0.18 | 1% loss → 5.6% price ↑ |
| Cotton | $1,800 | 0.45 | 1% loss → 2.2% price ↑ |
| Sugar | $400 | 0.35 | 1% loss → 2.9% price ↑ |

### Pulses (Moderately Elastic)
| Crop | Baseline Price ($/ton) | Elasticity | Price Impact* |
|------|----------------------:|------------|--------------|
| Chickpeas | $800 | 0.50 | 1% loss → 2.0% price ↑ |
| Lentils | $600 | 0.55 | 1% loss → 1.8% price ↑ |
| Beans | $700 | 0.48 | 1% loss → 2.1% price ↑ |

### Other Crops
| Crop | Baseline Price ($/ton) | Elasticity | Price Impact* |
|------|----------------------:|------------|--------------|
| Cassava | $250 | 0.40 | 1% loss → 2.5% price ↑ |
| Potato | $350 | 0.60 | 1% loss → 1.7% price ↑ |
| Tomato | $600 | 0.65 | 1% loss → 1.5% price ↑ |

*Price impact shows how much prices rise for every 1% yield loss.

## API Endpoint

### `POST /api/v1/finance/price-shock`

Calculate commodity price shock from climate-induced yield loss.

**Request Body:**
```json
{
  "crop_type": "maize",
  "baseline_yield_tons": 1000.0,
  "stressed_yield_tons": 700.0
}
```

**Response:**
```json
{
  "baseline_price": 180.0,
  "shocked_price": 396.0,
  "price_increase_pct": 120.0,
  "price_increase_usd": 216.0,
  "yield_loss_pct": 30.0,
  "yield_loss_tons": 300.0,
  "elasticity": 0.25,
  "forward_contract_recommendation": "🚨 URGENT: Lock in forward contracts immediately. Projected 30.0% yield loss will cause severe price volatility. Consider hedging 70-80% of expected production at current prices.",
  "revenue_impact": {
    "baseline_revenue_usd": 180000.0,
    "stressed_revenue_usd": 277200.0,
    "net_revenue_change_usd": 97200.0,
    "net_revenue_change_pct": 54.0
  }
}
```

## Use Cases

### 1. Farmer Revenue Protection
**Scenario:** A maize farmer expects drought to reduce yield by 25%.

**Input:**
```json
{
  "crop_type": "maize",
  "baseline_yield_tons": 500.0,
  "stressed_yield_tons": 375.0
}
```

**Output:**
- Price will spike 100% (from $180 to $360/ton)
- Revenue increases despite yield loss: $135,000 (stressed) vs $90,000 (baseline)
- **Recommendation:** Lock in forward contracts to capture high prices

### 2. Food Processor Price Risk
**Scenario:** A wheat mill needs 10,000 tons annually. Climate forecasts predict 15% regional yield loss.

**Input:**
```json
{
  "crop_type": "wheat",
  "baseline_yield_tons": 100000.0,
  "stressed_yield_tons": 85000.0
}
```

**Output:**
- Wheat prices will rise 50% (from $220 to $330/ton)
- Additional procurement cost: $1.1M
- **Recommendation:** Hedge 50-60% of annual needs via forward contracts

### 3. Crop Insurance Trigger Design
**Scenario:** Design parametric insurance that pays when prices exceed thresholds.

**Analysis:**
- 10% yield loss → 40% price increase (maize)
- 20% yield loss → 80% price increase
- 30% yield loss → 120% price increase

**Insurance Design:**
- Trigger: Prices exceed baseline by 60%
- Payout: Corresponds to ~15% regional yield loss
- Basis risk: Minimized by using supply elasticity model

### 4. National Food Security Planning
**Scenario:** Government needs to assess price impact of 20% drought-induced rice yield loss.

**Input:**
```json
{
  "crop_type": "rice",
  "baseline_yield_tons": 5000000.0,
  "stressed_yield_tons": 4000000.0
}
```

**Output:**
- Rice prices will spike 100% (from $450 to $900/ton)
- Import needs: 1M tons at elevated prices
- Budget impact: $900M (vs $450M at baseline)
- **Recommendation:** Build strategic reserves, diversify suppliers

## Revenue Impact: The Farmer's Dilemma

### When Price Shocks Compensate for Yield Loss

For **inelastic crops** (maize, rice, wheat), price spikes can **increase farmer revenue** despite lower yields:

**Example: Maize Farmer**
- Baseline: 1,000 tons × $180 = $180,000
- Drought scenario (20% loss): 800 tons × $324 = $259,200
- **Net gain: $79,200 (+44%)**

**Why?** The 80% price increase (from inelasticity) more than compensates for the 20% yield loss.

### When Yield Loss Causes Revenue Decline

For **elastic crops** (potato, tomato) or **severe losses** (>60%), revenue falls:

**Example: Potato Farmer**
- Baseline: 1,000 tons × $350 = $350,000
- Severe drought (60% loss): 400 tons × $700 = $280,000
- **Net loss: -$70,000 (-20%)**

**Why?** Even a 100% price increase can't compensate for losing 60% of production.

## Forward Contract Recommendations

The engine provides risk-tiered hedging advice:

### 🚨 URGENT (Yield Loss >30%)
```
"Lock in forward contracts immediately. 
Projected X% yield loss will cause severe price volatility. 
Consider hedging 70-80% of expected production at current prices."
```

**Action:** Hedge aggressively now before prices spike further.

### ⚠️ HIGH RISK (Yield Loss 15-30%)
```
"Consider forward contracts now. 
Projected X% yield loss will drive prices Y% higher. 
Hedge 50-60% of expected production to protect against further volatility."
```

**Action:** Start hedging positions, monitor closely.

### ⚡ MODERATE RISK (Yield Loss 5-15%)
```
"Monitor markets closely. 
Projected X% yield loss may push prices Y% higher. 
Consider hedging 30-40% of production if prices continue rising."
```

**Action:** Prepare hedging strategy, wait for opportune moment.

### ✅ LOW RISK (Yield Loss <5%)
```
"No immediate hedging needed. 
Projected X% yield loss will have minimal price impact. 
Continue monitoring weather forecasts and market conditions."
```

**Action:** Business as usual, stay vigilant.

## Integration with Climate Risk Models

### Workflow: Drought → Yield Loss → Price Shock

```
1. Climate Model (GEE)
   ↓ (rainfall deficit, heat stress)
   
2. Crop Yield Model (physics_engine.py)
   ↓ (baseline vs stressed yield)
   
3. Price Shock Engine (price_shock_engine.py)
   ↓ (elasticity-driven price response)
   
4. Financial Impact (financial_engine.py)
   ↓ (NPV, ROI, payback period)
   
5. Risk Management (recommendations)
```

### Example Integration

```python
from physics_engine import calculate_yield
from price_shock_engine import calculate_price_shock
from financial_engine import calculate_roi_metrics

# Step 1: Calculate climate-stressed yield
baseline_yield = calculate_yield(temp=28, rain=600, seed_type=0, crop_type="maize")
stressed_yield = calculate_yield(temp=35, rain=400, seed_type=0, crop_type="maize")

# Step 2: Calculate price shock
price_result = calculate_price_shock(
    crop_type="maize",
    baseline_yield_tons=baseline_yield,
    stressed_yield_tons=stressed_yield
)

# Step 3: Calculate ROI of resilient seeds
resilient_yield = calculate_yield(temp=35, rain=400, seed_type=1, crop_type="maize")
avoided_loss = resilient_yield - stressed_yield
benefit = avoided_loss * price_result['shocked_price']

cash_flows = [-2000] + [benefit - 425] * 10  # CAPEX, then annual net benefit
roi_metrics = calculate_roi_metrics(cash_flows, discount_rate=0.10)

print(f"NPV of resilient seeds: ${roi_metrics['npv']:,.2f}")
print(f"Payback period: {roi_metrics['payback_period_years']:.1f} years")
```

## Data Sources & References

### Elasticity Estimates
1. **Roberts, M. J., & Schlenker, W. (2013).** "Identifying Supply and Demand Elasticities of Agricultural Commodities." *American Economic Review*, 103(6), 2265-2295.
2. **USDA Economic Research Service.** Agricultural Supply Response database.
3. **FAO (2023).** "Price Volatility in Food and Agricultural Markets: Policy Responses."

### Baseline Prices
- **World Bank Commodity Price Data** (Pink Sheet, monthly updates)
- **USDA Agricultural Projections** 2024-2033
- **ICE Futures, CME Group** (commodity exchanges)

### Price Updating
Baseline prices should be updated quarterly using:
```python
BASELINE_PRICES["maize"] = get_latest_price_from_world_bank("maize")
```

## Limitations & Caveats

### 1. **Local vs Global Markets**
- Elasticities reflect **regional supply responses**
- Local prices may vary ±20-30% from global benchmarks
- Transportation costs, trade barriers, and local policies matter

### 2. **Short-Run vs Long-Run**
- These elasticities are **short-run** (current season)
- Long-run elasticity (1-3 years) is higher as farmers adjust
- Over time, high prices incentivize increased planting

### 3. **Substitution Effects**
- Model assumes **no crop substitution**
- In reality, consumers may switch (e.g., rice → wheat)
- This dampens price spikes for crops with close substitutes

### 4. **Market Structure**
- Assumes **competitive markets**
- Oligopolistic markets (few traders) may have different dynamics
- Government price controls can suppress market-driven shocks

### 5. **Demand Side**
- Model focuses on **supply-side shocks**
- Doesn't account for demand changes (income, preferences)
- Income effects during economic crises are not modeled

### 6. **Strategic Reserves**
- National grain reserves can buffer price shocks
- Model doesn't account for government interventions
- Buffer stocks reduce volatility in practice

## Advanced Features

### 1. **Multi-Crop Portfolio Analysis**
Aggregate price risk across multiple crops:

```python
portfolio = [
    {"crop": "maize", "baseline": 1000, "stressed": 800},
    {"crop": "wheat", "baseline": 500, "stressed": 450},
    {"crop": "soybeans", "baseline": 300, "stressed": 270}
]

total_baseline_revenue = 0
total_stressed_revenue = 0

for asset in portfolio:
    result = calculate_price_shock(
        crop_type=asset["crop"],
        baseline_yield_tons=asset["baseline"],
        stressed_yield_tons=asset["stressed"]
    )
    total_baseline_revenue += result["revenue_impact"]["baseline_revenue_usd"]
    total_stressed_revenue += result["revenue_impact"]["stressed_revenue_usd"]

portfolio_impact_pct = (
    (total_stressed_revenue - total_baseline_revenue) / total_baseline_revenue * 100
)
```

### 2. **Scenario Analysis**
Test multiple drought severity scenarios:

```python
drought_scenarios = [5, 10, 15, 20, 30, 40]  # % yield loss

for loss_pct in drought_scenarios:
    stressed = baseline * (1 - loss_pct / 100)
    result = calculate_price_shock("maize", baseline, stressed)
    print(f"{loss_pct}% loss → {result['price_increase_pct']:.1f}% price increase")
```

Output:
```
5% loss → 20.0% price increase
10% loss → 40.0% price increase
15% loss → 60.0% price increase
20% loss → 80.0% price increase
30% loss → 120.0% price increase
40% loss → 160.0% price increase
```

### 3. **Hedging Strategy Optimization**
Calculate optimal hedge ratio:

```python
from scipy.optimize import minimize

def hedging_cost(hedge_ratio, baseline, stressed, price_shock):
    """Minimize variance of hedged revenue."""
    hedged_qty = baseline * hedge_ratio
    spot_qty = stressed - hedged_qty
    
    # Revenue: hedged at baseline price + spot at shocked price
    revenue = (hedged_qty * price_shock["baseline_price"] + 
               spot_qty * price_shock["shocked_price"])
    
    # Variance proxy: squared deviation from baseline revenue
    baseline_revenue = baseline * price_shock["baseline_price"]
    variance = (revenue - baseline_revenue) ** 2
    
    return variance

# Optimize hedge ratio (0 to 1)
result = minimize(hedging_cost, x0=0.5, bounds=[(0, 1)], 
                  args=(baseline, stressed, price_shock))
optimal_hedge = result.x[0]
```

## Future Enhancements

### Planned Features
1. **Time-varying elasticity:** Seasonal and long-run adjustments
2. **Spatial correlation:** Regional yield correlation matrices
3. **Demand-side shocks:** Income effects, consumer preferences
4. **Government policy:** Price controls, subsidies, trade barriers
5. **Climate scenario integration:** SSP scenarios (SSP2-4.5, SSP5-8.5)
6. **Machine learning:** Train elasticity models on historical data

### Data Needs
- Historical price/yield panel data (20+ years)
- Regional supply/demand balances
- Trade flow data (imports/exports)
- Weather station data (NOAA, WMO)
- Crop calendar information (FAO)

## Support & Citation

**Developed by:** AdaptMetric Climate Resilience Engine  
**Version:** 1.0.0  
**Last Updated:** 2026-02-26

**Citation:**
```
AdaptMetric (2026). Commodity Price Shock Engine: Climate-Induced Supply 
Disruption Modeling. Retrieved from https://github.com/dizzy1900/resilient-backend
```

**Contact:** For questions, bug reports, or collaboration inquiries, open an issue on GitHub.

---

**License:** MIT License - See LICENSE file for details.
