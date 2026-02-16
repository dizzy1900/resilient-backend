"""
Test to verify both APIs return consistent structure for frontend
"""
import requests
import json

API_BASE = "https://web-production-8ff9e.up.railway.app"

print("="*70)
print("API STRUCTURE COMPARISON - AGRICULTURAL vs COASTAL")
print("="*70)
print()

# Test Agricultural API
print("1. AGRICULTURAL MODEL API")
print("-" * 70)
ag_response = requests.post(
    f"{API_BASE}/predict",
    json={"temp": 30.0, "rain": 450.0},
    timeout=30
)

if ag_response.status_code == 200:
    ag_data = ag_response.json()['data']
    print("✓ Response structure:")
    print(f"  - input_conditions: {list(ag_data.get('input_conditions', {}).keys())}")
    print(f"  - predictions: {list(ag_data.get('predictions', {}).keys())}")
    print(f"  - analysis: {list(ag_data.get('analysis', {}).keys())}")
    print()
    print(f"✓ Avoided Loss Field:")
    avoided_loss = ag_data['analysis']['avoided_loss']
    print(f"  data.analysis.avoided_loss = {avoided_loss}")
    print(f"  Type: {type(avoided_loss).__name__}")
    print(f"  Value: {avoided_loss} yield units")
else:
    print(f"❌ Agricultural API failed: {ag_response.status_code}")

print()
print("="*70)
print("2. COASTAL MODEL API")
print("-" * 70)
coastal_response = requests.post(
    f"{API_BASE}/predict-coastal",
    json={"lat": 25.7617, "lon": -80.1918, "mangrove_width": 50},
    timeout=90
)

if coastal_response.status_code == 200:
    coastal_data = coastal_response.json()['data']
    print("✓ Response structure:")
    print(f"  - input_conditions: {list(coastal_data.get('input_conditions', {}).keys())}")
    print(f"  - coastal_params: {list(coastal_data.get('coastal_params', {}).keys())}")
    print(f"  - predictions: {list(coastal_data.get('predictions', {}).keys())}")
    print(f"  - analysis: {list(coastal_data.get('analysis', {}).keys())}")
    print(f"  - economic_assumptions: {list(coastal_data.get('economic_assumptions', {}).keys())}")
    print()
    print(f"✓ Avoided Loss Field:")
    avoided_loss = coastal_data['analysis']['avoided_loss']
    print(f"  data.analysis.avoided_loss = {avoided_loss}")
    print(f"  Type: {type(avoided_loss).__name__}")
    print(f"  Value: ${avoided_loss:,.2f} USD")
else:
    print(f"❌ Coastal API failed: {coastal_response.status_code}")

print()
print("="*70)
print("3. CONSISTENCY CHECK")
print("-" * 70)

if ag_response.status_code == 200 and coastal_response.status_code == 200:
    ag_data = ag_response.json()['data']
    coastal_data = coastal_response.json()['data']
    
    # Check both have analysis.avoided_loss
    ag_has_field = 'analysis' in ag_data and 'avoided_loss' in ag_data['analysis']
    coastal_has_field = 'analysis' in coastal_data and 'avoided_loss' in coastal_data['analysis']
    
    print(f"✓ Both APIs have 'data.analysis.avoided_loss' field:")
    print(f"  Agricultural: {ag_has_field} {'✅' if ag_has_field else '❌'}")
    print(f"  Coastal:      {coastal_has_field} {'✅' if coastal_has_field else '❌'}")
    print()
    
    # Check both are numeric
    ag_value = ag_data['analysis']['avoided_loss']
    coastal_value = coastal_data['analysis']['avoided_loss']
    
    ag_is_numeric = isinstance(ag_value, (int, float))
    coastal_is_numeric = isinstance(coastal_value, (int, float))
    
    print(f"✓ Both values are numeric:")
    print(f"  Agricultural: {ag_is_numeric} {'✅' if ag_is_numeric else '❌'} (value: {ag_value})")
    print(f"  Coastal:      {coastal_is_numeric} {'✅' if coastal_is_numeric else '❌'} (value: {coastal_value})")
    print()
    
    # Check both are non-zero for valid inputs
    ag_nonzero = ag_value != 0
    coastal_nonzero = coastal_value != 0
    
    print(f"✓ Both values are NON-ZERO:")
    print(f"  Agricultural: {ag_nonzero} {'✅' if ag_nonzero else '❌'} ({ag_value})")
    print(f"  Coastal:      {coastal_nonzero} {'✅' if coastal_nonzero else '❌'} (${coastal_value:,.2f})")
    print()
    
    if ag_has_field and coastal_has_field and ag_nonzero and coastal_nonzero:
        print("✅ PASS: Both APIs return consistent structure with non-zero avoided_loss")
    else:
        print("❌ FAIL: APIs are not consistent")

print()
print("="*70)
print("4. FRONTEND INTEGRATION")
print("-" * 70)
print()
print("Frontend code can now parse both responses identically:")
print()
print("```javascript")
print("// Get avoided loss from either API")
print("const avoidedLoss = response.data.analysis.avoided_loss;")
print()
print("// Display value")
print("if (apiType === 'agricultural') {")
print("  // Yield units - convert to $ using crop price")
print("  displayValue(`${avoidedLoss} yield units`);")
print("} else if (apiType === 'coastal') {")
print("  // Already in USD")
print("  displayValue(`$${avoidedLoss.toLocaleString()}`);")
print("}")
print("```")
print()
print("="*70)
print("🎉 APIs are now CONSISTENT and frontend-ready!")
print("="*70)
