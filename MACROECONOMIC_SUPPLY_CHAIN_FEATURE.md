# Macroeconomic Supply Chain Module - Route Risk Analysis

## Overview

The Macroeconomic Supply Chain module analyzes climate-related disruption risks for truck routes, focusing on flood hazards that cause detours, delays, and cargo spoilage. This feature enables logistics companies, insurers, and infrastructure planners to quantify economic losses and prioritize flood mitigation investments.

## API Endpoint

**POST** `/api/v1/network/route-risk`

### Request Schema

```json
{
  "route_linestring": {
    "type": "LineString",
    "coordinates": [
      [-74.0060, 40.7128],
      [-74.0377, 40.7178],
      [-74.0721, 40.7282],
      [-74.1724, 40.7357]
    ]
  },
  "cargo_value": 100000.0,
  "baseline_travel_hours": 1.5
}
```

**Parameters:**
- `route_linestring` (required): GeoJSON LineString geometry representing the truck route
  - Must be valid GeoJSON with `type: "LineString"`
  - Coordinates array must contain at least 2 coordinate pairs `[lon, lat]`
- `cargo_value` (float, default: $100,000): Value of cargo in USD
- `baseline_travel_hours` (float, required): Expected travel time under normal conditions (hours)

### Response Schema

```json
{
  "flooded_miles": 2.34,
  "detour_delay_hours": 1.17,
  "freight_delay_cost": 106.79,
  "spoilage_cost": 975.00,
  "total_value_at_risk": 1081.79,
  "intervention_capex": 15210000.00
}
```

**Fields:**
- `flooded_miles`: Total length of route intersecting flood zones (miles)
- `detour_delay_hours`: Additional delay from detours (hours)
- `freight_delay_cost`: Direct freight cost increase (USD)
- `spoilage_cost`: Cargo spoilage from delays (USD)
- `total_value_at_risk`: Combined economic impact (USD)
- `intervention_capex`: Capital expenditure for flood mitigation (USD)

## Economic Formulas

### 1. Detour Delay Calculation
```
detour_delay_hours = flooded_miles × 0.5
```
**Rationale:** Assumes 30 minutes (0.5 hours) delay per flooded mile due to:
- Road damage requiring slower speeds
- Detour routing around flooded sections
- Traffic congestion at detour points

### 2. Freight Delay Cost
```
freight_delay_cost = detour_delay_hours × $91.27/hour
```
**Rationale:** Based on US trucking industry standard operating costs:
- Fuel consumption during delays
- Driver wages and overtime
- Equipment depreciation
- Industry benchmark: $91.27/hour average delay cost

### 3. Spoilage Cost
```
spoilage_cost = cargo_value × 0.2 × (detour_delay_hours / 24)
```
**Rationale:** Models perishable goods spoilage:
- 20% of cargo value is perishable goods (food, pharmaceuticals, etc.)
- Spoilage rate is proportional to delay duration
- Normalized by 24 hours (1 day delay = full spoilage of perishable portion)

### 4. Total Value at Risk
```
total_value_at_risk = freight_delay_cost + spoilage_cost
```
**Rationale:** Aggregates direct operational costs and cargo value losses

### 5. Intervention Capital Expenditure
```
intervention_capex = flooded_miles × $6,500,000/mile
```
**Rationale:** Infrastructure investment to mitigate flood risk:
- Road elevation (raising grade above flood level)
- Improved drainage systems
- Culvert upgrades
- Industry benchmark: $6.5 million per mile for comprehensive flood-proofing

## Geospatial Integration (Google Earth Engine)

### Data Source
**JRC Global Surface Water v1.4** (European Commission Joint Research Centre)
- Dataset: `JRC/GSW1_4/GlobalSurfaceWater`
- Band: `occurrence` (percentage of time water is present)
- Resolution: 30m (Landsat-scale)
- Temporal Coverage: 1984-2021

### Flood Hazard Detection Logic

```python
def analyze_route_flood_risk(linestring_coords: List[List[float]]) -> float:
    """
    1. Create LineString geometry from coordinates
    2. Buffer route by 100m to capture flood zones along road
    3. Select flood occurrence band from JRC dataset
    4. Create flood mask: occurrence > 20% (floods >20% of time)
    5. Calculate intersection area between route buffer and flood mask
    6. Convert area to route length (area / buffer_width)
    7. Convert meters to miles
    """
```

**Flood Threshold:** Areas with >20% water occurrence are considered flood-prone
- Represents locations that flood >73 days/year on average
- Proxy for flood depth >0.5m (assumption: persistent flooding indicates significant depth)

**Route Buffer:** 100m on each side (200m total width)
- Captures flood zones that impact the road corridor
- Accounts for road width + immediate drainage infrastructure

## Use Cases

### 1. Logistics Risk Management
**Scenario:** Trucking company evaluates climate risk on critical supply routes

**Workflow:**
1. Frontend: User draws route on Mapbox map
2. Frontend: Mapbox Directions API generates LineString
3. Backend: Calculate flood risk and economic impact
4. Frontend: Display risk heatmap and intervention ROI

**Business Value:**
- Identify high-risk routes for rerouting or hardening
- Quantify insurance needs for supply chain disruption
- Prioritize infrastructure upgrades

### 2. Infrastructure Investment Prioritization
**Scenario:** State DOT evaluates flood mitigation projects

**Workflow:**
1. Analyze multiple road segments in flood-prone regions
2. Compare `intervention_capex` vs. annual `total_value_at_risk`
3. Rank projects by benefit-cost ratio
4. Allocate FEMA BRIC grants to highest-ROI projects

**Business Value:**
- Data-driven capital allocation
- Maximize resilience per dollar spent
- Justify grant applications with quantitative risk analysis

### 3. Parametric Insurance Pricing
**Scenario:** Insurer prices supply chain disruption policies

**Workflow:**
1. Policyholder submits typical routes
2. Calculate expected annual losses from flood delays
3. Price premium based on `total_value_at_risk` × probability
4. Offer premium discounts for routes with lower `flooded_miles`

**Business Value:**
- Actuarially sound pricing based on geospatial risk
- Incentivize policyholders to use climate-resilient routes
- Reduce claims frequency and severity

## Integration with Frontend

### Expected Frontend Workflow

1. **Route Drawing:**
   - User draws route on Mapbox map
   - Mapbox GL JS captures user clicks as coordinate pairs
   - Or: Use Mapbox Directions API to generate optimal route

2. **API Call:**
   ```javascript
   const response = await fetch('/api/v1/network/route-risk', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       route_linestring: {
         type: 'LineString',
         coordinates: mapboxRoute.geometry.coordinates
       },
       cargo_value: 250000,
       baseline_travel_hours: routeDuration / 3600  // Convert seconds to hours
     })
   });
   
   const risk = await response.json();
   ```

3. **Visualization:**
   - Display `flooded_miles` as red overlay on map
   - Show `total_value_at_risk` in dashboard card
   - Render intervention CBA: `intervention_capex` vs. annual avoided losses

### Example Mapbox Integration

```javascript
// Assume user has drawn a route using Mapbox Directions API
const routeGeometry = directionsResponse.routes[0].geometry;  // GeoJSON LineString
const routeDuration = directionsResponse.routes[0].duration;  // seconds

// Call route-risk endpoint
const riskResponse = await fetch('/api/v1/network/route-risk', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    route_linestring: routeGeometry,
    cargo_value: cargoValue,
    baseline_travel_hours: routeDuration / 3600
  })
});

const riskData = await riskResponse.json();

// Display flooded segments on map
map.addLayer({
  id: 'flooded-route',
  type: 'line',
  source: { type: 'geojson', data: routeGeometry },
  paint: {
    'line-color': '#FF0000',
    'line-width': 4,
    'line-opacity': riskData.flooded_miles > 0 ? 0.8 : 0
  }
});
```

## Testing

### Test Script Location
`/Users/david/resilient-backend/test_route_risk.py`

### Running Tests
```bash
# Start API server
python api.py

# In another terminal, run tests
python test_route_risk.py
```

### Test Cases

1. **NYC to Newark (Hudson River crossing)**
   - Tests flood-prone coastal route
   - Validates calculation logic

2. **High-Value Cargo (Miami to Fort Lauderdale)**
   - Tests spoilage cost calculation
   - Coastal route with storm surge risk

3. **Long-Distance Route (Houston to Dallas)**
   - Tests route through flood-prone East Texas
   - Validates intervention CAPEX scaling

4. **Invalid Geometry (Polygon instead of LineString)**
   - Tests error handling
   - Should return 400 error

## Technical Implementation

### File Modifications

1. **gee_connector.py**
   - Added `analyze_route_flood_risk()` function
   - Implements GEE flood hazard intersection logic
   - Uses JRC Global Surface Water dataset

2. **api.py**
   - Added `RouteRiskRequest` and `RouteRiskResponse` schemas
   - Added `/api/v1/network/route-risk` endpoint
   - Implements economic calculation logic
   - Error handling for invalid GeoJSON

### Dependencies
All required packages already in `requirements.txt`:
- `earthengine-api==1.7.10` (Google Earth Engine)
- `fastapi==0.109.0` (Web framework)
- `pydantic>=2.11.7` (Data validation)

### Authentication
Requires Google Earth Engine credentials (same as existing GEE endpoints):
- `WARP_GEE_CREDENTIALS` environment variable (preferred)
- Or `credentials.json` in project root

## Limitations and Future Enhancements

### Current Limitations

1. **Flood Depth Proxy:** Uses water occurrence (>20%) as proxy for flood depth >0.5m
   - More direct flood depth data would improve accuracy
   - Could integrate FEMA flood maps or MERIT-Hydro flood depth layers

2. **Static Buffer Width:** 100m buffer may not capture all flood impacts
   - Future: Dynamic buffer based on road type (highway vs. local road)

3. **Single Hazard:** Only considers flood risk
   - Future: Add landslides, wildfires, extreme heat (pavement damage)

4. **Linear Delay Model:** Assumes 0.5 hours/mile delay is constant
   - Future: Dynamic delay based on flood severity, traffic models

### Potential Enhancements

1. **Multi-Hazard Analysis**
   - Add wildfire risk along routes (smoke, road closures)
   - Include extreme heat (pavement buckling, tire failure risk)
   - Landslide risk for mountain routes

2. **Seasonal Variability**
   - Calculate risk by season (monsoon vs. dry season)
   - Enable "worst-case scenario" vs. "average risk" modes

3. **Alternative Route Optimization**
   - Generate alternative routes with lower flood risk
   - Calculate trade-off: longer distance vs. lower flood exposure

4. **Historical Validation**
   - Compare predicted flooded miles to actual road closure data
   - Calibrate delay coefficients from historical logistics data

5. **Real-Time Integration**
   - Integrate with weather forecasts (7-day flood predictions)
   - Dynamic rerouting based on current flood conditions

## API Contract Stability

**Status:** Production-ready

**Breaking Changes:** None expected

**Versioning:** Part of `/api/v1/network/*` namespace
- Future versions will maintain backward compatibility
- New fields will be added as optional (default values)

## Support and Contact

**Developer:** AdaptMetric Backend Team  
**Documentation:** This file + inline code comments  
**Issues:** Report via GitHub or internal ticketing system
