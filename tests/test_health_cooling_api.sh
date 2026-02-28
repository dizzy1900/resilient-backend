#!/bin/bash
# =============================================================================
# API Test Script for Enhanced /predict-health Endpoint
# Cooling CAPEX vs. Productivity OPEX Cost-Benefit Analysis
# =============================================================================

API_URL="${API_URL:-http://localhost:8000}"
ENDPOINT="$API_URL/predict-health"

echo "======================================================================"
echo "COOLING INTERVENTION API TESTS"
echo "======================================================================"
echo "Testing endpoint: $ENDPOINT"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to test an endpoint
test_endpoint() {
    local test_name="$1"
    local payload="$2"
    
    echo "----------------------------------------------------------------------"
    echo "TEST: $test_name"
    echo "----------------------------------------------------------------------"
    echo "Request:"
    echo "$payload" | python3 -m json.tool 2>/dev/null || echo "$payload"
    echo ""
    
    response=$(curl -s -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    echo "Response:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    echo ""
    
    # Check for intervention_analysis in response
    if echo "$response" | grep -q "intervention_analysis"; then
        echo -e "${GREEN}✓ Intervention analysis present${NC}"
    else
        echo -e "${YELLOW}⚠ No intervention analysis (baseline only)${NC}"
    fi
    echo ""
}

# =============================================================================
# TEST 1: Baseline (No Intervention)
# =============================================================================
test_endpoint "Baseline Health Analysis (No Intervention)" '{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0
}'

# =============================================================================
# TEST 2: HVAC Retrofit
# =============================================================================
test_endpoint "HVAC Retrofit ($250K CAPEX, $30K OPEX)" '{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 500,
  "daily_wage": 25.0,
  "intervention_type": "hvac_retrofit",
  "intervention_capex": 250000.0,
  "intervention_annual_opex": 30000.0
}'

# =============================================================================
# TEST 3: Passive Cooling
# =============================================================================
test_endpoint "Passive Cooling ($50K CAPEX, $5K OPEX)" '{
  "lat": 28.6139,
  "lon": 77.2090,
  "workforce_size": 200,
  "daily_wage": 15.0,
  "intervention_type": "passive_cooling",
  "intervention_capex": 50000.0,
  "intervention_annual_opex": 5000.0
}'

# =============================================================================
# TEST 4: Zero CAPEX (Policy-based intervention)
# =============================================================================
test_endpoint "Zero CAPEX Intervention (Policy Change)" '{
  "lat": 1.3521,
  "lon": 103.8198,
  "workforce_size": 100,
  "daily_wage": 40.0,
  "intervention_type": "passive_cooling",
  "intervention_capex": 0.0,
  "intervention_annual_opex": 0.0
}'

# =============================================================================
# TEST 5: Unprofitable Intervention (High OPEX)
# =============================================================================
test_endpoint "Unprofitable Intervention (OPEX > Benefit)" '{
  "lat": 13.7563,
  "lon": 100.5018,
  "workforce_size": 100,
  "daily_wage": 15.0,
  "intervention_type": "hvac_retrofit",
  "intervention_capex": 200000.0,
  "intervention_annual_opex": 100000.0
}'

# =============================================================================
# TEST 6: Cool Climate (Minimal Benefit)
# =============================================================================
test_endpoint "Cool Climate - Minimal Intervention Benefit" '{
  "lat": 51.5074,
  "lon": -0.1278,
  "workforce_size": 200,
  "daily_wage": 50.0,
  "intervention_type": "hvac_retrofit",
  "intervention_capex": 100000.0,
  "intervention_annual_opex": 15000.0
}'

# =============================================================================
# SUMMARY
# =============================================================================
echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo ""
echo "✓ Completed all API tests for enhanced /predict-health endpoint"
echo ""
echo "Coverage:"
echo "  • Baseline analysis (no intervention)"
echo "  • HVAC retrofit (active cooling to 22°C)"
echo "  • Passive cooling (3°C WBGT reduction)"
echo "  • Zero CAPEX scenarios"
echo "  • Unprofitable interventions"
echo "  • Cool climate edge cases"
echo ""
echo "Response Structure:"
echo "  • heat_stress_analysis: Baseline WBGT and productivity loss"
echo "  • intervention_analysis: (if intervention requested)"
echo "    - wbgt_adjustment: Baseline vs. adjusted WBGT"
echo "    - productivity_impact: Baseline vs. adjusted loss %"
echo "    - economic_impact: Avoided annual loss ($)"
echo "    - financial_analysis: NPV, payback period, BCR, recommendation"
echo ""
echo "======================================================================"
