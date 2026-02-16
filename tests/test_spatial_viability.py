#!/usr/bin/env python3
"""
Test script for analyze_spatial_viability function
"""

from gee_connector import analyze_spatial_viability

# Test with a major agricultural region (Iowa, USA)
lat = 42.0
lon = -93.5

print("Testing analyze_spatial_viability")
print("=" * 60)
print(f"Location: lat={lat}, lon={lon} (Iowa, USA - major corn belt)")
print(f"Buffer: 50km radius")
print(f"Threshold: 35°C (maize heat stress limit)")
print("=" * 60)

# Test Case 1: No temperature increase
print("\nTest Case 1: Baseline (0°C increase)")
print("-" * 60)
try:
    result = analyze_spatial_viability(lat, lon, 0.0)
    print(f"  Baseline viable area: {result['baseline_sq_km']} sq km")
    print(f"  Future viable area: {result['future_sq_km']} sq km")
    print(f"  Loss percentage: {result['loss_pct']}%")
    print("  ✓ Test passed")
except Exception as e:
    print(f"  ✗ Test failed: {e}")

# Test Case 2: +2°C increase (moderate warming)
print("\nTest Case 2: +2°C increase (moderate warming)")
print("-" * 60)
try:
    result = analyze_spatial_viability(lat, lon, 2.0)
    print(f"  Baseline viable area: {result['baseline_sq_km']} sq km")
    print(f"  Future viable area: {result['future_sq_km']} sq km")
    print(f"  Loss percentage: {result['loss_pct']}%")
    
    # Validate structure
    assert 'baseline_sq_km' in result, "Missing baseline_sq_km"
    assert 'future_sq_km' in result, "Missing future_sq_km"
    assert 'loss_pct' in result, "Missing loss_pct"
    assert result['future_sq_km'] <= result['baseline_sq_km'], "Future should be <= Baseline"
    
    print("  ✓ Test passed")
except Exception as e:
    print(f"  ✗ Test failed: {e}")
    import traceback
    traceback.print_exc()

# Test Case 3: +4°C increase (severe warming)
print("\nTest Case 3: +4°C increase (severe warming)")
print("-" * 60)
try:
    result = analyze_spatial_viability(lat, lon, 4.0)
    print(f"  Baseline viable area: {result['baseline_sq_km']} sq km")
    print(f"  Future viable area: {result['future_sq_km']} sq km")
    print(f"  Loss percentage: {result['loss_pct']}%")
    print("  ✓ Test passed")
except Exception as e:
    print(f"  ✗ Test failed: {e}")

print("\n" + "=" * 60)
print("Testing complete!")
print("=" * 60)
