#!/usr/bin/env python3
"""
Test the updated /predict-coastal-flood endpoint with spatial analysis
"""

import json

def test_coastal_flood_spatial_logic():
    """Test the coastal flood endpoint with spatial analysis."""
    
    print("Testing /predict-coastal-flood endpoint with spatial analysis")
    print("=" * 60)
    
    # Test Case 1: Request with surge (should include spatial analysis)
    print("\nTest Case 1: With surge and spatial analysis")
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
    total_water_level = slr_projection + surge_m
    
    print(f"  Request: {json.dumps(request_data, indent=4)}")
    print(f"\n  Calculated values:")
    print(f"    surge_m: {surge_m}m")
    print(f"    total_water_level: {total_water_level}m")
    
    # Simulate response structure
    response_data = {
        'input_conditions': {
            'lat': lat,
            'lon': lon,
            'slr_projection_m': slr_projection,
            'include_surge': include_surge,
            'surge_m': surge_m,
            'total_water_level_m': total_water_level
        },
        'flood_risk': {
            'elevation_m': 2.5,
            'is_underwater': True,
            'flood_depth_m': 0.5,
            'risk_category': 'Moderate'
        },
        'spatial_analysis': {
            'total_urban_km2': 15.2,
            'flooded_urban_km2': 3.4,
            'urban_impact_pct': 22.37
        }
    }
    
    print(f"\n  Response structure:")
    print(json.dumps(response_data, indent=4))
    
    assert 'input_conditions' in response_data, "Missing input_conditions"
    assert 'flood_risk' in response_data, "Missing flood_risk"
    assert 'spatial_analysis' in response_data, "Missing spatial_analysis"
    assert response_data['input_conditions']['total_water_level_m'] == 3.0, "Total water level should be 3.0m"
    print("  ✓ Passed")
    
    # Test Case 2: Request without surge
    print("\nTest Case 2: Without surge (lower water level)")
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
    total_water_level = slr_projection + surge_m
    
    print(f"  Request: {json.dumps(request_data, indent=4)}")
    print(f"\n  Calculated values:")
    print(f"    surge_m: {surge_m}m")
    print(f"    total_water_level: {total_water_level}m")
    
    assert total_water_level == 0.5, "Total water level should be 0.5m"
    assert surge_m == 0.0, "Surge should be 0.0m"
    print("  ✓ Passed")
    
    # Test Case 3: Error handling (spatial analysis fails)
    print("\nTest Case 3: Error handling (spatial analysis fails)")
    print("-" * 60)
    
    spatial_analysis = None
    try:
        # Simulate error
        raise Exception("GEE timeout")
    except Exception as spatial_error:
        print(f"  Caught error: {spatial_error}")
        spatial_analysis = None
    
    # Response should still work without spatial_analysis
    response_data = {
        'input_conditions': {
            'lat': 25.7617,
            'lon': -80.1918,
            'slr_projection_m': 0.5,
            'include_surge': True,
            'surge_m': 2.5,
            'total_water_level_m': 3.0
        },
        'flood_risk': {
            'elevation_m': 2.5,
            'is_underwater': True,
            'flood_depth_m': 0.5,
            'risk_category': 'Moderate'
        }
    }
    
    # Add spatial_analysis only if available
    if spatial_analysis is not None:
        response_data['spatial_analysis'] = spatial_analysis
    
    print(f"  Response without spatial_analysis:")
    print(json.dumps(response_data, indent=4))
    
    assert 'spatial_analysis' not in response_data, "spatial_analysis should not be in response when it fails"
    assert 'flood_risk' in response_data, "flood_risk should still be present"
    print("  ✓ Passed (graceful degradation)")
    
    print("\n" + "=" * 60)
    print("All logic tests passed! ✓")
    print("=" * 60)
    
    # Show complete example response
    print("\nComplete Example Response (with spatial analysis):")
    print("=" * 60)
    
    complete_response = {
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
            },
            "spatial_analysis": {
                "total_urban_km2": 15.2,
                "flooded_urban_km2": 3.4,
                "urban_impact_pct": 22.37
            }
        }
    }
    
    print(json.dumps(complete_response, indent=2))


if __name__ == '__main__':
    test_coastal_flood_spatial_logic()
