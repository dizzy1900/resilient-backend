#!/bin/bash

# Comprehensive API endpoint testing script
# Tests all three endpoints and compares responses

API_BASE="https://web-production-8ff9e.up.railway.app"

echo "================================================================================"
echo "  ADAPTMETRIC BACKEND - COMPREHENSIVE API TEST"
echo "  Testing: $API_BASE"
echo "  Date: $(date)"
echo "================================================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_endpoint() {
    local name=$1
    local method=$2
    local path=$3
    local payload=$4
    
    echo ""
    echo "================================================================================  "
    echo "  TEST: $name"
    echo "================================================================================"
    echo "  Endpoint: $method $path"
    echo ""
    
    if [ "$method" = "GET" ]; then
        echo "  Request: GET $API_BASE$path"
        echo ""
        response=$(curl -s -w "\n%{http_code}" "$API_BASE$path")
    else
        echo "  Request: POST $API_BASE$path"
        echo "  Payload:"
        echo "$payload" | jq '.' 2>/dev/null || echo "$payload"
        echo ""
        response=$(curl -s -w "\n%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -H "Origin: https://lovable.dev" \
            -d "$payload" \
            "$API_BASE$path")
    fi
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract body (everything except last line)
    body=$(echo "$response" | sed '$d')
    
    echo "  Status Code: $status_code"
    
    if [ "$status_code" = "200" ]; then
        echo -e "  ${GREEN}✅ SUCCESS${NC}"
        echo ""
        echo "  Response:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        
        # Extract avoided_loss if present
        avoided_loss=$(echo "$body" | jq -r '.data.analysis.avoided_loss // empty' 2>/dev/null)
        if [ -n "$avoided_loss" ]; then
            echo ""
            echo -e "  ${GREEN}💰 AVOIDED LOSS: \$$avoided_loss${NC}"
        fi
    else
        echo -e "  ${RED}❌ FAILED${NC}"
        echo ""
        echo "  Response:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    fi
}

# Test 1: Health check
test_endpoint \
    "Health Check" \
    "GET" \
    "/health" \
    ""

# Test 2: Agricultural prediction
test_endpoint \
    "Agricultural Prediction" \
    "POST" \
    "/predict" \
    '{
        "temp": 30.0,
        "rain": 450.0
    }'

# Test 3: Coastal prediction
test_endpoint \
    "Coastal Prediction" \
    "POST" \
    "/predict-coastal" \
    '{
        "lat": 25.7617,
        "lon": -80.1918,
        "mangrove_width": 50
    }'

# Test 4: Flood prediction - Green Roof
test_endpoint \
    "Flood Prediction - Green Roof" \
    "POST" \
    "/predict-flood" \
    '{
        "rain_intensity": 100.0,
        "current_imperviousness": 0.7,
        "intervention_type": "green_roof",
        "slope_pct": 2.0
    }'

# Test 5: Flood prediction - Permeable Pavement
test_endpoint \
    "Flood Prediction - Permeable Pavement" \
    "POST" \
    "/predict-flood" \
    '{
        "rain_intensity": 80.0,
        "current_imperviousness": 0.8,
        "intervention_type": "permeable_pavement"
    }'

# Test 6: Flood prediction - No Intervention
test_endpoint \
    "Flood Prediction - No Intervention" \
    "POST" \
    "/predict-flood" \
    '{
        "rain_intensity": 50.0,
        "current_imperviousness": 0.5,
        "intervention_type": "none"
    }'

# Test CORS headers
echo ""
echo "================================================================================"
echo "  CORS HEADERS TEST"
echo "================================================================================"
echo "  Testing OPTIONS request (browser preflight)"
echo ""

cors_response=$(curl -s -i -X OPTIONS \
    -H "Origin: https://lovable.dev" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: content-type" \
    "$API_BASE/predict-flood")

echo "$cors_response" | grep -i "access-control"

if echo "$cors_response" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✅ CORS properly configured${NC}"
else
    echo -e "${RED}❌ CORS headers missing${NC}"
fi

# Summary
echo ""
echo "================================================================================"
echo "  SUMMARY"
echo "================================================================================"
echo ""
echo "All endpoints tested. If all show ✅ SUCCESS, the backend is working correctly."
echo ""
echo "If your frontend still shows dummy values, the issue is in the frontend code:"
echo "  1. Check the API URL in your frontend"
echo "  2. Verify you're calling /predict-flood endpoint"
echo "  3. Check field path: data.analysis.avoided_loss"
echo "  4. Compare with working coastal endpoint code"
echo ""
echo "For detailed frontend debugging, see: FRONTEND_DEBUG_GUIDE.md"
echo ""
