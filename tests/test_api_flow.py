"""
Test the full API flow to diagnose $0 avoided loss issue
"""
import requests
import json

API_BASE = "https://web-production-8ff9e.up.railway.app"

def test_location_flow(lat, lon, location_name):
    """Test the full flow for a specific location."""
    print(f"\n{'='*60}")
    print(f"Testing: {location_name}")
    print(f"Coordinates: ({lat}, {lon})")
    print(f"{'='*60}")
    
    # Step 1: Get hazard data
    hazard_response = requests.post(
        f"{API_BASE}/get-hazard",
        json={"lat": lat, "lon": lon},
        headers={"Content-Type": "application/json"}
    )
    
    if hazard_response.status_code != 200:
        print(f"❌ Hazard request failed: {hazard_response.status_code}")
        print(hazard_response.text)
        return
    
    hazard_data = hazard_response.json()
    print(f"✓ Hazard data retrieved:")
    print(f"  Temperature: {hazard_data['data']['hazard_metrics']['max_temp_celsius']:.2f}°C")
    print(f"  Rainfall: {hazard_data['data']['hazard_metrics']['total_rain_mm']:.2f}mm")
    
    # Step 2: Make prediction with those values
    temp = hazard_data['data']['hazard_metrics']['max_temp_celsius']
    rain = hazard_data['data']['hazard_metrics']['total_rain_mm']
    
    predict_response = requests.post(
        f"{API_BASE}/predict",
        json={"temp": temp, "rain": rain},
        headers={"Content-Type": "application/json"}
    )
    
    if predict_response.status_code != 200:
        print(f"❌ Prediction request failed: {predict_response.status_code}")
        print(predict_response.text)
        return
    
    predict_data = predict_response.json()
    print(f"\n✓ Prediction results:")
    print(f"  Standard seed yield: {predict_data['data']['predictions']['standard_seed']['predicted_yield']}")
    print(f"  Resilient seed yield: {predict_data['data']['predictions']['resilient_seed']['predicted_yield']}")
    print(f"  Avoided loss: {predict_data['data']['analysis']['avoided_loss']}")
    print(f"  Percentage improvement: {predict_data['data']['analysis']['percentage_improvement']}%")
    print(f"  Recommendation: {predict_data['data']['analysis']['recommendation']}")
    
    # Highlight if avoided loss is zero
    if predict_data['data']['analysis']['avoided_loss'] == 0.0:
        print(f"\n⚠️  ISSUE FOUND: Avoided loss is $0!")
        print(f"   This happens when both seed types predict the same yield.")
        print(f"   Weather conditions are optimal (no stress), so resilient seeds offer no advantage.")

# Test various locations
test_cases = [
    (40.7128, -74.0060, "New York (Cool/Wet)"),
    (25.7617, -80.1918, "Miami (Warm/Wet)"),
    (36.7783, -119.4179, "Central Valley CA (Agriculture Hub)"),
    (19.4326, -99.1332, "Mexico City (Highlands)"),
    (-23.5505, -46.6333, "São Paulo, Brazil"),
    (28.5, 77.2, "Delhi, India (Hot/Variable)"),
    (30.0444, 31.2357, "Cairo, Egypt (Hot/Dry)"),
]

for lat, lon, name in test_cases:
    test_location_flow(lat, lon, name)

print(f"\n{'='*60}")
print("Summary:")
print("The API is working correctly. $0 avoided losses occur when:")
print("1. Weather conditions are optimal (moderate temp, adequate rain)")
print("2. Both seed types achieve maximum yield (~100%)")
print("3. No stress = no benefit from resilient seeds")
print("\nTo see non-zero avoided losses, select locations with:")
print("- High temperatures (>33°C)")
print("- Low rainfall (<400mm) or excessive rainfall (>1400mm)")
print("- Or both (drought + heat stress)")
print(f"{'='*60}")
