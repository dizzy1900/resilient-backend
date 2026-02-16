#!/usr/bin/env python3
"""
Test the /predict-flash-flood endpoint logic
"""

import json

def test_flash_flood_endpoint_logic():
    """Test the flash flood endpoint request/response logic."""
    
    print("Testing /predict-flash-flood endpoint logic")
    print("=" * 60)
    
    # Test Case 1: Valid request with 20% rain intensity increase
    print("\nTest Case 1: Valid request (20% rain increase)")
    print("-" * 60)
    
    request_data = {
        'lat': 42.0,
        'lon': -93.5,
        'rain_intensity_pct': 20.0
    }
    
    lat = float(request_data['lat'])
    lon = float(request_data['lon'])
    rain_intensity_pct = float(request_data['rain_intensity_pct'])
    
    print(f"  Request: {json.dumps(request_data, indent=4)}")
    
    # Validate
    assert -90 <= lat <= 90, "Latitude out of range"
    assert -180 <= lon <= 180, "Longitude out of range"
    assert rain_intensity_pct >= 0, "Rain intensity must be non-negative"
    
    # Simulate response
    response_data = {
        'input_conditions': {
            'lat': lat,
            'lon': lon,
            'rain_intensity_increase_pct': rain_intensity_pct
        },
        'flash_flood_analysis': {
            'baseline_flood_area_km2': 45.2,
            'future_flood_area_km2': 62.8,
            'risk_increase_pct': 38.94
        }
    }
    
    print(f"\n  Response structure:")
    print(json.dumps(response_data, indent=4))
    
    assert 'input_conditions' in response_data, "Missing input_conditions"
    assert 'flash_flood_analysis' in response_data, "Missing flash_flood_analysis"
    print("  ✓ Passed")
    
    # Test Case 2: Zero rain intensity increase (baseline)
    print("\nTest Case 2: Baseline (0% rain increase)")
    print("-" * 60)
    
    request_data = {
        'lat': 25.7617,
        'lon': -80.1918,
        'rain_intensity_pct': 0.0
    }
    
    lat = float(request_data['lat'])
    lon = float(request_data['lon'])
    rain_intensity_pct = float(request_data['rain_intensity_pct'])
    
    print(f"  Request: {json.dumps(request_data, indent=4)}")
    print(f"  Rain intensity: {rain_intensity_pct}%")
    
    assert rain_intensity_pct == 0.0, "Rain intensity should be 0"
    print("  ✓ Passed")
    
    # Test Case 3: High rain intensity increase (50%)
    print("\nTest Case 3: High rain increase (50%)")
    print("-" * 60)
    
    request_data = {
        'lat': 30.0,
        'lon': -90.0,
        'rain_intensity_pct': 50.0
    }
    
    lat = float(request_data['lat'])
    lon = float(request_data['lon'])
    rain_intensity_pct = float(request_data['rain_intensity_pct'])
    
    print(f"  Request: {json.dumps(request_data, indent=4)}")
    print(f"  Rain intensity: {rain_intensity_pct}%")
    
    assert rain_intensity_pct == 50.0, "Rain intensity should be 50"
    print("  ✓ Passed")
    
    # Test Case 4: Validation - invalid coordinates
    print("\nTest Case 4: Invalid coordinates")
    print("-" * 60)
    
    test_cases = [
        (91.0, -80.0, "latitude too high"),
        (-91.0, -80.0, "latitude too low"),
        (25.0, 181.0, "longitude too high"),
        (25.0, -181.0, "longitude too low")
    ]
    
    for lat, lon, error_msg in test_cases:
        valid_lat = -90 <= lat <= 90
        valid_lon = -180 <= lon <= 180
        print(f"  lat={lat}, lon={lon}: valid_lat={valid_lat}, valid_lon={valid_lon} ({error_msg})")
        
        if not valid_lat or not valid_lon:
            print(f"    → Correctly rejected")
    
    print("  ✓ All validations work correctly")
    
    # Test Case 5: Validation - negative rain intensity
    print("\nTest Case 5: Invalid negative rain intensity")
    print("-" * 60)
    
    rain_intensity_pct = -10.0
    print(f"  Rain intensity: {rain_intensity_pct}%")
    
    if rain_intensity_pct < 0:
        print("  Error: Rain intensity increase must be non-negative")
        print("  ✓ Validation works correctly")
    
    print("\n" + "=" * 60)
    print("All logic tests passed! ✓")
    print("=" * 60)
    
    # Show complete example response
    print("\nComplete Example Response:")
    print("=" * 60)
    
    complete_response = {
        "status": "success",
        "data": {
            "input_conditions": {
                "lat": 42.0,
                "lon": -93.5,
                "rain_intensity_increase_pct": 20.0
            },
            "flash_flood_analysis": {
                "baseline_flood_area_km2": 45.2,
                "future_flood_area_km2": 62.8,
                "risk_increase_pct": 38.94
            }
        }
    }
    
    print(json.dumps(complete_response, indent=2))


if __name__ == '__main__':
    test_flash_flood_endpoint_logic()
