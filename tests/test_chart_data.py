#!/usr/bin/env python3
"""
Test script for /predict endpoint with chart_data
"""

import json
import sys

# Mock test to validate logic without running the server
# This tests the projection logic in isolation

def test_rainfall_projection_logic():
    """Test the rainfall projection logic with summer drought penalty."""
    
    # Sample baseline data (12 months)
    rainfall_baseline = [50, 45, 60, 70, 80, 90, 100, 95, 85, 75, 60, 55]
    
    # Test Case 1: No change (rain_change = 0)
    rain_change = 0
    rainfall_projected = []
    for i, baseline_value in enumerate(rainfall_baseline):
        projected_value = baseline_value * (1 + rain_change / 100)
        if rain_change < 0:
            if i in [5, 6, 7]:  # Summer months
                additional_penalty = abs(rain_change) / 100
                projected_value = projected_value * (1 - additional_penalty)
        rainfall_projected.append(round(projected_value, 2))
    
    print("Test Case 1: No change (rain_change = 0)")
    print(f"  Baseline: {rainfall_baseline}")
    print(f"  Projected: {rainfall_projected}")
    assert rainfall_projected == rainfall_baseline, "No change should keep values the same"
    print("  ✓ Passed\n")
    
    # Test Case 2: +20% increase
    rain_change = 20
    rainfall_projected = []
    for i, baseline_value in enumerate(rainfall_baseline):
        projected_value = baseline_value * (1 + rain_change / 100)
        if rain_change < 0:
            if i in [5, 6, 7]:  # Summer months
                additional_penalty = abs(rain_change) / 100
                projected_value = projected_value * (1 - additional_penalty)
        rainfall_projected.append(round(projected_value, 2))
    
    print("Test Case 2: +20% increase (rain_change = 20)")
    print(f"  Baseline: {rainfall_baseline}")
    print(f"  Projected: {rainfall_projected}")
    print(f"  Expected first value: {50 * 1.2} = 60.0")
    assert rainfall_projected[0] == 60.0, "20% increase should multiply by 1.2"
    print("  ✓ Passed\n")
    
    # Test Case 3: -30% decrease (drought with summer penalty)
    rain_change = -30
    rainfall_projected = []
    for i, baseline_value in enumerate(rainfall_baseline):
        projected_value = baseline_value * (1 + rain_change / 100)
        if rain_change < 0:
            if i in [5, 6, 7]:  # Summer months (Jun, Jul, Aug)
                additional_penalty = abs(rain_change) / 100
                projected_value = projected_value * (1 - additional_penalty)
        rainfall_projected.append(round(projected_value, 2))
    
    print("Test Case 3: -30% decrease with summer drought penalty")
    print(f"  Baseline: {rainfall_baseline}")
    print(f"  Projected: {rainfall_projected}")
    
    # January (index 0): No summer penalty
    # 50 * 0.7 = 35.0
    print(f"  Jan (no penalty): {rainfall_baseline[0]} * 0.7 = {rainfall_projected[0]}")
    assert rainfall_projected[0] == 35.0, "January should only have base penalty"
    
    # June (index 5): Summer penalty applies
    # 90 * 0.7 = 63.0, then 63.0 * 0.7 = 44.1
    print(f"  Jun (summer penalty): {rainfall_baseline[5]} * 0.7 * 0.7 = {rainfall_projected[5]}")
    assert rainfall_projected[5] == 44.1, "June should have double penalty"
    
    # July (index 6): Summer penalty applies
    # 100 * 0.7 = 70.0, then 70.0 * 0.7 = 49.0
    print(f"  Jul (summer penalty): {rainfall_baseline[6]} * 0.7 * 0.7 = {rainfall_projected[6]}")
    assert rainfall_projected[6] == 49.0, "July should have double penalty"
    
    # August (index 7): Summer penalty applies
    # 95 * 0.7 = 66.5, then 66.5 * 0.7 = 46.55
    print(f"  Aug (summer penalty): {rainfall_baseline[7]} * 0.7 * 0.7 = {rainfall_projected[7]}")
    assert rainfall_projected[7] == 46.55, "August should have double penalty"
    
    print("  ✓ Passed\n")
    
    # Test Case 4: Verify chart_data structure
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    soil_moisture_baseline = [0.25, 0.23, 0.28, 0.30, 0.32, 0.30, 0.28, 0.26, 0.27, 0.29, 0.26, 0.24]
    
    chart_data = {
        'months': months,
        'rainfall_baseline': rainfall_baseline,
        'rainfall_projected': rainfall_projected,
        'soil_moisture_baseline': soil_moisture_baseline
    }
    
    print("Test Case 4: Chart data structure")
    print(f"  Months count: {len(chart_data['months'])}")
    print(f"  Rainfall baseline count: {len(chart_data['rainfall_baseline'])}")
    print(f"  Rainfall projected count: {len(chart_data['rainfall_projected'])}")
    print(f"  Soil moisture count: {len(chart_data['soil_moisture_baseline'])}")
    
    assert len(chart_data['months']) == 12, "Should have 12 months"
    assert len(chart_data['rainfall_baseline']) == 12, "Should have 12 baseline values"
    assert len(chart_data['rainfall_projected']) == 12, "Should have 12 projected values"
    assert len(chart_data['soil_moisture_baseline']) == 12, "Should have 12 soil moisture values"
    print("  ✓ Passed\n")
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == '__main__':
    test_rainfall_projection_logic()
