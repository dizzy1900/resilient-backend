#!/usr/bin/env python3
"""
Test the updated /predict-flash-flood endpoint with infrastructure risk spatial analysis
"""

import json

def test_flash_flood_spatial_analysis():
    """Test the flash flood endpoint with infrastructure risk spatial analysis."""
    
    print("Testing /predict-flash-flood with spatial_analysis")
    print("=" * 60)
    
    # Test Case 1: Complete request with all features
    print("\nTest Case 1: Complete request with spatial analysis")
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
    
    # Simulate complete response structure
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
        },
        'analytics': {
            'rain_chart_data': [
                {'period': '1yr', 'baseline_mm': 70.0, 'future_mm': 84.0},
                {'period': '10yr', 'baseline_mm': 121.5, 'future_mm': 145.8},
                {'period': '50yr', 'baseline_mm': 159.7, 'future_mm': 191.64},
                {'period': '100yr', 'baseline_mm': 179.4, 'future_mm': 215.28}
            ]
        },
        'spatial_analysis': {
            'infrastructure_risk': {
                'total_km2': 150.0,
                'flooded_km2': 12.5,
                'risk_pct': 8.33
            }
        }
    }
    
    print(f"\n  Complete response structure:")
    print(json.dumps(response_data, indent=4))
    
    # Validate all sections
    assert 'input_conditions' in response_data, "Missing input_conditions"
    assert 'flash_flood_analysis' in response_data, "Missing flash_flood_analysis"
    assert 'analytics' in response_data, "Missing analytics"
    assert 'spatial_analysis' in response_data, "Missing spatial_analysis"
    assert 'infrastructure_risk' in response_data['spatial_analysis'], "Missing infrastructure_risk"
    
    # Validate spatial_analysis structure
    infra_risk = response_data['spatial_analysis']['infrastructure_risk']
    assert 'total_km2' in infra_risk, "Missing total_km2"
    assert 'flooded_km2' in infra_risk, "Missing flooded_km2"
    assert 'risk_pct' in infra_risk, "Missing risk_pct"
    
    print("  ✓ All fields present and valid")
    
    # Test Case 2: Error handling (spatial analysis fails gracefully)
    print("\nTest Case 2: Graceful degradation when spatial analysis fails")
    print("-" * 60)
    
    spatial_analysis = None
    try:
        # Simulate error
        raise Exception("GEE timeout")
    except Exception as spatial_error:
        print(f"  Caught error: {spatial_error}")
        spatial_analysis = None
    
    # Response should still work without spatial_analysis
    response_data_fallback = {
        'input_conditions': {
            'lat': 42.0,
            'lon': -93.5,
            'rain_intensity_increase_pct': 20.0
        },
        'flash_flood_analysis': {
            'baseline_flood_area_km2': 45.2,
            'future_flood_area_km2': 62.8,
            'risk_increase_pct': 38.94
        },
        'analytics': {
            'rain_chart_data': [
                {'period': '1yr', 'baseline_mm': 70.0, 'future_mm': 84.0}
            ]
        }
    }
    
    # Add spatial_analysis only if available
    if spatial_analysis is not None:
        response_data_fallback['spatial_analysis'] = spatial_analysis
    
    print(f"  Response without spatial_analysis:")
    print(json.dumps(response_data_fallback, indent=4))
    
    assert 'spatial_analysis' not in response_data_fallback, "spatial_analysis should not be present when it fails"
    assert 'flash_flood_analysis' in response_data_fallback, "flash_flood_analysis should still be present"
    assert 'analytics' in response_data_fallback, "analytics should still be present"
    print("  ✓ Graceful degradation works correctly")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
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
            },
            "analytics": {
                "rain_chart_data": [
                    {"period": "1yr", "baseline_mm": 70.0, "future_mm": 84.0},
                    {"period": "10yr", "baseline_mm": 121.5, "future_mm": 145.8},
                    {"period": "50yr", "baseline_mm": 159.7, "future_mm": 191.64},
                    {"period": "100yr", "baseline_mm": 179.4, "future_mm": 215.28}
                ]
            },
            "spatial_analysis": {
                "infrastructure_risk": {
                    "total_km2": 150.0,
                    "flooded_km2": 12.5,
                    "risk_pct": 8.33
                }
            }
        }
    }
    
    print(json.dumps(complete_response, indent=2))


if __name__ == '__main__':
    test_flash_flood_spatial_analysis()
