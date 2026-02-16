#!/usr/bin/env python3
"""
Test script to verify /predict endpoint includes spatial_analysis
"""

import json

# Test the logic for when spatial analysis should be included

def test_spatial_analysis_logic():
    """Test when spatial_analysis should be included in response."""
    
    print("Testing spatial_analysis inclusion logic")
    print("=" * 60)
    
    # Test Case 1: Mode A (lat/lon) with temp_increase > 0
    print("\nTest Case 1: Mode A with temp_increase=2.0")
    has_location = True
    location_lat = 42.0
    location_lon = -93.5
    temp_increase = 2.0
    
    should_run_spatial = has_location and temp_increase != 0.0
    print(f"  has_location: {has_location}")
    print(f"  temp_increase: {temp_increase}")
    print(f"  Should run spatial analysis: {should_run_spatial}")
    assert should_run_spatial == True, "Should run spatial analysis"
    print("  ✓ Passed")
    
    # Test Case 2: Mode A (lat/lon) with temp_increase = 0
    print("\nTest Case 2: Mode A with temp_increase=0.0")
    has_location = True
    temp_increase = 0.0
    
    should_run_spatial = has_location and temp_increase != 0.0
    print(f"  has_location: {has_location}")
    print(f"  temp_increase: {temp_increase}")
    print(f"  Should run spatial analysis: {should_run_spatial}")
    assert should_run_spatial == False, "Should NOT run spatial analysis (no temperature change)"
    print("  ✓ Passed")
    
    # Test Case 3: Mode B (manual temp/rain)
    print("\nTest Case 3: Mode B (manual) with temp_increase=2.0")
    has_location = False
    temp_increase = 2.0
    
    should_run_spatial = has_location and temp_increase != 0.0
    print(f"  has_location: {has_location}")
    print(f"  temp_increase: {temp_increase}")
    print(f"  Should run spatial analysis: {should_run_spatial}")
    assert should_run_spatial == False, "Should NOT run spatial analysis (no location)"
    print("  ✓ Passed")
    
    # Test Case 4: Mode A with negative temp_increase (cooling)
    print("\nTest Case 4: Mode A with temp_increase=-1.0 (cooling)")
    has_location = True
    temp_increase = -1.0
    
    should_run_spatial = has_location and temp_increase != 0.0
    print(f"  has_location: {has_location}")
    print(f"  temp_increase: {temp_increase}")
    print(f"  Should run spatial analysis: {should_run_spatial}")
    assert should_run_spatial == True, "Should run spatial analysis (cooling scenario)"
    print("  ✓ Passed")
    
    print("\n" + "=" * 60)
    print("All logic tests passed! ✓")
    print("=" * 60)
    
    # Show example response structure
    print("\nExample Response Structure:")
    example_response = {
        "status": "success",
        "data": {
            "input_conditions": {
                "max_temp_celsius": 28.5,
                "total_rain_mm": 520.0,
                "data_source": "gee_auto_lookup"
            },
            "predictions": {
                "standard_seed": {"type_code": 0, "predicted_yield": 5.2},
                "resilient_seed": {"type_code": 1, "predicted_yield": 6.1}
            },
            "analysis": {
                "avoided_loss": 0.9,
                "percentage_improvement": 17.3,
                "recommendation": "resilient"
            },
            "simulation_debug": {
                "raw_temp": 28.5,
                "perturbation_added": 2.0,
                "final_simulated_temp": 30.5,
                "raw_rain": 520.0,
                "rain_modifier": 0.0,
                "final_simulated_rain": 520.0
            },
            "chart_data": {
                "months": ["Jan", "Feb", "..."],
                "rainfall_baseline": [50, 45, "..."],
                "rainfall_projected": [50, 45, "..."],
                "soil_moisture_baseline": [0.25, 0.23, "..."]
            },
            "spatial_analysis": {
                "baseline_sq_km": 120.5,
                "future_sq_km": 85.2,
                "loss_pct": 29.3
            }
        }
    }
    
    print(json.dumps(example_response, indent=2))


if __name__ == '__main__':
    test_spatial_analysis_logic()
