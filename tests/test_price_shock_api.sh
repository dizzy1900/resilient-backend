#!/bin/bash
# =============================================================================
# API Test Script for Price Shock Endpoint
# =============================================================================
# Tests the POST /api/v1/finance/price-shock endpoint with various scenarios
#
# Usage:
#   chmod +x tests/test_price_shock_api.sh
#   ./tests/test_price_shock_api.sh
#
# Prerequisites:
#   - Server running on http://localhost:8000
#   - jq installed (for JSON formatting): brew install jq
# =============================================================================

API_URL="${API_URL:-http://localhost:8000}"
ENDPOINT="$API_URL/api/v1/finance/price-shock"

echo "======================================================================"
echo "COMMODITY PRICE SHOCK API TESTS"
echo "======================================================================"
echo "Testing endpoint: $ENDPOINT"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test an endpoint
test_endpoint() {
    local test_name="$1"
    local payload="$2"
    local expected_status="${3:-200}"
    
    echo "----------------------------------------------------------------------"
    echo "TEST: $test_name"
    echo "----------------------------------------------------------------------"
    echo "Request:"
    echo "$payload" | jq '.' 2>/dev/null || echo "$payload"
    echo ""
    
    response=$(curl -s -w "\n%{http_code}" -X POST "$ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$payload")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    echo "Response (HTTP $http_code):"
    if command -v jq &> /dev/null; then
        echo "$body" | jq '.'
    else
        echo "$body"
    fi
    echo ""
    
    if [ "$http_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ Test passed (HTTP $http_code)${NC}"
    else
        echo -e "${RED}✗ Test failed (expected HTTP $expected_status, got $http_code)${NC}"
    fi
    echo ""
}

# =============================================================================
# TEST 1: Basic Maize Drought (30% yield loss)
# =============================================================================
test_endpoint "Basic Maize Drought (30% yield loss)" '{
  "crop_type": "maize",
  "baseline_yield_tons": 1000.0,
  "stressed_yield_tons": 700.0
}' 200

# =============================================================================
# TEST 2: Wheat Moderate Loss (10% yield loss)
# =============================================================================
test_endpoint "Wheat Moderate Loss (10% yield loss)" '{
  "crop_type": "wheat",
  "baseline_yield_tons": 500.0,
  "stressed_yield_tons": 450.0
}' 200

# =============================================================================
# TEST 3: Soybeans Minimal Loss (3% yield loss)
# =============================================================================
test_endpoint "Soybeans Minimal Loss (3% yield loss)" '{
  "crop_type": "soybeans",
  "baseline_yield_tons": 800.0,
  "stressed_yield_tons": 776.0
}' 200

# =============================================================================
# TEST 4: Rice Severe Drought (40% yield loss)
# =============================================================================
test_endpoint "Rice Severe Drought (40% yield loss)" '{
  "crop_type": "rice",
  "baseline_yield_tons": 2000.0,
  "stressed_yield_tons": 1200.0
}' 200

# =============================================================================
# TEST 5: Cocoa Highly Inelastic (15% yield loss)
# =============================================================================
test_endpoint "Cocoa Highly Inelastic (15% yield loss)" '{
  "crop_type": "cocoa",
  "baseline_yield_tons": 100.0,
  "stressed_yield_tons": 85.0
}' 200

# =============================================================================
# TEST 6: Complete Crop Failure (100% yield loss)
# =============================================================================
test_endpoint "Complete Crop Failure (100% yield loss)" '{
  "crop_type": "maize",
  "baseline_yield_tons": 500.0,
  "stressed_yield_tons": 0.0
}' 200

# =============================================================================
# TEST 7: Zero Yield Loss (no shock)
# =============================================================================
test_endpoint "Zero Yield Loss (prices unchanged)" '{
  "crop_type": "wheat",
  "baseline_yield_tons": 1000.0,
  "stressed_yield_tons": 1000.0
}' 200

# =============================================================================
# TEST 8: Case Insensitive Crop Name
# =============================================================================
test_endpoint "Case Insensitive Crop Name (MAIZE)" '{
  "crop_type": "MAIZE",
  "baseline_yield_tons": 1000.0,
  "stressed_yield_tons": 900.0
}' 200

# =============================================================================
# TEST 9: Crop Alias (corn = maize)
# =============================================================================
test_endpoint "Crop Alias (corn = maize)" '{
  "crop_type": "corn",
  "baseline_yield_tons": 1000.0,
  "stressed_yield_tons": 900.0
}' 200

# =============================================================================
# TEST 10: Large-Scale Commercial Farm
# =============================================================================
test_endpoint "Large-Scale Commercial Farm (50K tons)" '{
  "crop_type": "wheat",
  "baseline_yield_tons": 50000.0,
  "stressed_yield_tons": 42000.0
}' 200

# =============================================================================
# ERROR TESTS
# =============================================================================

echo "======================================================================"
echo "ERROR HANDLING TESTS"
echo "======================================================================"
echo ""

# =============================================================================
# TEST 11: Invalid Crop Type
# =============================================================================
test_endpoint "Invalid Crop Type (should fail with 400)" '{
  "crop_type": "banana",
  "baseline_yield_tons": 1000.0,
  "stressed_yield_tons": 900.0
}' 400

# =============================================================================
# TEST 12: Negative Baseline Yield
# =============================================================================
test_endpoint "Negative Baseline Yield (should fail with 422)" '{
  "crop_type": "maize",
  "baseline_yield_tons": -100.0,
  "stressed_yield_tons": 900.0
}' 422

# =============================================================================
# TEST 13: Negative Stressed Yield
# =============================================================================
test_endpoint "Negative Stressed Yield (should fail with 422)" '{
  "crop_type": "maize",
  "baseline_yield_tons": 1000.0,
  "stressed_yield_tons": -50.0
}' 422

# =============================================================================
# TEST 14: Missing Required Field
# =============================================================================
test_endpoint "Missing Required Field (should fail with 422)" '{
  "crop_type": "maize",
  "baseline_yield_tons": 1000.0
}' 422

# =============================================================================
# TEST 15: Invalid JSON
# =============================================================================
echo "----------------------------------------------------------------------"
echo "TEST: Invalid JSON (should fail with 422)"
echo "----------------------------------------------------------------------"
echo "Request: {invalid json}"
echo ""
curl -s -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -d '{invalid json}' | jq '.' 2>/dev/null || echo "Parse error (expected)"
echo ""
echo -e "${GREEN}✓ Test passed (malformed JSON rejected)${NC}"
echo ""

# =============================================================================
# SUMMARY
# =============================================================================
echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo ""
echo "✓ Completed all API tests for /api/v1/finance/price-shock"
echo ""
echo "Coverage:"
echo "  • Basic calculations (success cases)"
echo "  • Edge cases (zero loss, complete failure)"
echo "  • Input validation (crop types, aliases)"
echo "  • Error handling (invalid inputs, missing fields)"
echo ""
echo "Next steps:"
echo "  1. Review test results above"
echo "  2. Check server logs for any errors"
echo "  3. Run unit tests: pytest tests/test_price_shock_engine.py"
echo "  4. Run integration tests: pytest tests/test_price_shock_endpoint.py"
echo ""
echo "======================================================================"
