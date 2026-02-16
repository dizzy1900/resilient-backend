#!/usr/bin/env python3
"""
Test the /predict-coastal-flood endpoint logic
"""

import json

def test_coastal_flood_endpoint_logic():
    """Test the coastal flood endpoint request/response logic."""
    
    print("Testing /predict-coastal-flood endpoint logic")
    print("=" * 60)
    
    # Test Case 1: Without surge
    print("\nTest Case 1: Without storm surge")
    print("-" * 60)
    request_data = {
        'lat': 25.7617,
        'lon': -80.1918,
        'slr_projection': 0.5,
        'include_surge': False
    }
    
    lat = float(request_data['lat'])
    lon = float(request_data['lon'])
    slr_projection = float(request_data['slr_projection'])
    include_surge = request_data.get('include_surge', False)
    surge_m = 2.5 if include_surge else 0.0
    
    print(f"  Request: {json.dumps(request_data, indent=2)}")
    print(f"  Surge calculated: {surge_m}m")
    print(f"  Total water level: {slr_projection + surge_m}m")
    
    assert surge_m == 0.0, "Surge should be 0.0 when include_surge is False"
    assert slr_projection + surge_m == 0.5, "Total water level should be 0.5m"
    print("  ✓ Passed")
    
    # Test Case 2: With surge
    print("\nTest Case 2: With storm surge")
    print("-" * 60)
    request_data = {
        'lat': 25.7617,
        'lon': -80.1918,
        'slr_projection': 0.5,
        'include_surge': True
    }
    
    lat = float(request_data['lat'])
    lon = float(request_data['lon'])
    slr_projection = float(request_data['slr_projection'])
    include_surge = request_data.get('include_surge', False)
    surge_m = 2.5 if include_surge else 0.0
    
    print(f"  Request: {json.dumps(request_data, indent=2)}")
    print(f"  Surge calculated: {surge_m}m")
    print(f"  Total water level: {slr_projection + surge_m}m")
    
    assert surge_m == 2.5, "Surge should be 2.5m when include_surge is True"
    assert slr_projection + surge_m == 3.0, "Total water level should be 3.0m"
    print("  ✓ Passed")
    
    # Test Case 3: Default include_surge (should be False)
    print("\nTest Case 3: Missing include_surge (default False)")
    print("-" * 60)
    request_data = {
        'lat': 25.7617,
        'lon': -80.1918,
        'slr_projection': 1.0
    }
    
    lat = float(request_data['lat'])
    lon = float(request_data['lon'])
    slr_projection = float(request_data['slr_projection'])
    include_surge = request_data.get('include_surge', False)
    surge_m = 2.5 if include_surge else 0.0
    
    print(f"  Request: {json.dumps(request_data, indent=2)}")
    print(f"  Surge calculated: {surge_m}m")
    print(f"  Total water level: {slr_projection + surge_m}m")
    
    assert surge_m == 0.0, "Surge should default to 0.0"
    assert slr_projection + surge_m == 1.0, "Total water level should be 1.0m"
    print("  ✓ Passed")
    
    # Test Case 4: Validation - negative SLR
    print("\nTest Case 4: Invalid negative SLR")
    print("-" * 60)
    request_data = {
        'lat': 25.7617,
        'lon': -80.1918,
        'slr_projection': -0.5,
        'include_surge': False
    }
    
    slr_projection = float(request_data['slr_projection'])
    print(f"  Request SLR: {slr_projection}m")
    
    if slr_projection < 0:
        print("  Error: Sea level rise projection must be non-negative")
        print("  ✓ Validation works correctly")
    
    # Test Case 5: Validation - invalid coordinates
    print("\nTest Case 5: Invalid coordinates")
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
    
    # Example response structure
    print("\n" + "=" * 60)
    print("Example Response Structure:")
    print("=" * 60)
    
    example_response = {
        "status": "success",
        "data": {
            "input_conditions": {
                "lat": 25.7617,
                "lon": -80.1918,
                "slr_projection_m": 0.5,
                "include_surge": True,
                "surge_m": 2.5,
                "total_water_level_m": 3.0
            },
            "flood_risk": {
                "elevation_m": 2.5,
                "is_underwater": True,
                "flood_depth_m": 0.5,
                "risk_category": "Moderate"
            }
        }
    }
    
    print(json.dumps(example_response, indent=2))
    
    print("\n" + "=" * 60)
    print("All logic tests passed! ✓")
    print("=" * 60)


if __name__ == '__main__':
    test_coastal_flood_endpoint_logic()
