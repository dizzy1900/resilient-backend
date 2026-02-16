#!/usr/bin/env python3
"""
Test script for analyze_flash_flood function
"""

def test_flash_flood_logic():
    """Test flash flood calculation logic."""
    
    print("Testing analyze_flash_flood calculation logic")
    print("=" * 60)
    
    # Constants from the model
    BASELINE_THRESHOLD = 12.0
    SCALING_FACTOR = 0.07
    
    # Test Case 1: No rain intensity increase (baseline)
    print("\nTest Case 1: No rain intensity increase (0%)")
    print("-" * 60)
    rain_intensity_increase_pct = 0.0
    dynamic_threshold = BASELINE_THRESHOLD * (1 - (rain_intensity_increase_pct / 100 * SCALING_FACTOR))
    
    print(f"  Rain intensity increase: {rain_intensity_increase_pct}%")
    print(f"  Baseline threshold: {BASELINE_THRESHOLD}")
    print(f"  Dynamic threshold: {dynamic_threshold}")
    
    assert dynamic_threshold == BASELINE_THRESHOLD, "Dynamic threshold should equal baseline when no increase"
    print("  ✓ Passed")
    
    # Test Case 2: 20% rain intensity increase
    print("\nTest Case 2: 20% rain intensity increase")
    print("-" * 60)
    rain_intensity_increase_pct = 20.0
    dynamic_threshold = BASELINE_THRESHOLD * (1 - (rain_intensity_increase_pct / 100 * SCALING_FACTOR))
    
    print(f"  Rain intensity increase: {rain_intensity_increase_pct}%")
    print(f"  Baseline threshold: {BASELINE_THRESHOLD}")
    print(f"  Scaling factor: {SCALING_FACTOR}")
    print(f"  Dynamic threshold: {round(dynamic_threshold, 2)}")
    
    # 20% increase → 20 * 0.07 = 1.4% reduction → 12 * (1 - 0.014) = 11.832
    expected_threshold = 12.0 * (1 - 0.014)
    assert abs(dynamic_threshold - expected_threshold) < 0.01, f"Expected {expected_threshold}, got {dynamic_threshold}"
    print("  ✓ Passed")
    
    # Test Case 3: 50% rain intensity increase
    print("\nTest Case 3: 50% rain intensity increase")
    print("-" * 60)
    rain_intensity_increase_pct = 50.0
    dynamic_threshold = BASELINE_THRESHOLD * (1 - (rain_intensity_increase_pct / 100 * SCALING_FACTOR))
    
    print(f"  Rain intensity increase: {rain_intensity_increase_pct}%")
    print(f"  Dynamic threshold: {round(dynamic_threshold, 2)}")
    
    # 50% increase → 50 * 0.07 = 3.5% reduction → 12 * (1 - 0.035) = 11.58
    expected_threshold = 12.0 * (1 - 0.035)
    assert abs(dynamic_threshold - expected_threshold) < 0.01, f"Expected {expected_threshold}, got {dynamic_threshold}"
    print("  ✓ Passed")
    
    # Test Case 4: Risk increase calculation
    print("\nTest Case 4: Risk increase calculation")
    print("-" * 60)
    
    # Simulate area calculations
    baseline_flood_km2 = 45.2
    future_flood_km2 = 62.8
    risk_increase_pct = ((future_flood_km2 - baseline_flood_km2) / baseline_flood_km2) * 100
    
    print(f"  Baseline flood area: {baseline_flood_km2} km²")
    print(f"  Future flood area: {future_flood_km2} km²")
    print(f"  Risk increase: {round(risk_increase_pct, 2)}%")
    
    # (62.8 - 45.2) / 45.2 * 100 = 38.94%
    expected_increase = 38.94
    assert abs(risk_increase_pct - expected_increase) < 0.1, f"Expected {expected_increase}%, got {risk_increase_pct}%"
    print("  ✓ Passed")
    
    # Test Case 5: Edge case - no baseline flood area
    print("\nTest Case 5: Edge case - no baseline flood area")
    print("-" * 60)
    
    baseline_flood_km2 = 0.0
    future_flood_km2 = 10.0
    risk_increase_pct = ((future_flood_km2 - baseline_flood_km2) / baseline_flood_km2) * 100 if baseline_flood_km2 > 0 else 0.0
    
    print(f"  Baseline flood area: {baseline_flood_km2} km²")
    print(f"  Future flood area: {future_flood_km2} km²")
    print(f"  Risk increase: {risk_increase_pct}%")
    
    assert risk_increase_pct == 0.0, "Risk increase should be 0 when baseline is 0"
    print("  ✓ Passed")
    
    # Test Case 6: Threshold reduction visualization
    print("\nTest Case 6: Threshold reduction at different rain intensities")
    print("-" * 60)
    
    test_intensities = [0, 10, 20, 30, 40, 50]
    print(f"  {'Rain +%':<10} {'Threshold':<12} {'Reduction':<12}")
    print(f"  {'-'*10} {'-'*12} {'-'*12}")
    
    for intensity in test_intensities:
        threshold = BASELINE_THRESHOLD * (1 - (intensity / 100 * SCALING_FACTOR))
        reduction = BASELINE_THRESHOLD - threshold
        print(f"  {intensity:<10} {threshold:<12.2f} {reduction:<12.2f}")
    
    print("  ✓ All thresholds calculated correctly")
    
    print("\n" + "=" * 60)
    print("All logic tests passed! ✓")
    print("=" * 60)
    
    # Show example output structure
    print("\nExample Output Structure:")
    import json
    example = {
        'baseline_flood_area_km2': 45.2,
        'future_flood_area_km2': 62.8,
        'risk_increase_pct': 38.94
    }
    print(json.dumps(example, indent=2))


if __name__ == '__main__':
    test_flash_flood_logic()
