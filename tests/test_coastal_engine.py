#!/usr/bin/env python3
"""
Test script for coastal_engine.py analyze_flood_risk function
"""

from coastal_engine import analyze_flood_risk

print("Testing analyze_flood_risk function")
print("=" * 60)

# Test Case 1: Miami, FL - Low elevation coastal area
print("\nTest Case 1: Miami, FL (low coastal elevation)")
print("-" * 60)
lat = 25.7617
lon = -80.1918
slr_meters = 0.3  # 30cm sea level rise
surge_meters = 1.5  # 1.5m storm surge

print(f"Location: lat={lat}, lon={lon}")
print(f"Sea Level Rise: {slr_meters}m")
print(f"Storm Surge: {surge_meters}m")
print(f"Total Water Level: {slr_meters + surge_meters}m")

try:
    result = analyze_flood_risk(lat, lon, slr_meters, surge_meters)
    print(f"\nResults:")
    print(f"  Elevation: {result['elevation_m']}m")
    print(f"  Is Underwater: {result['is_underwater']}")
    print(f"  Flood Depth: {result['flood_depth_m']}m")
    print(f"  Risk Category: {result['risk_category']}")
    
    # Validate structure
    assert 'elevation_m' in result, "Missing elevation_m"
    assert 'is_underwater' in result, "Missing is_underwater"
    assert 'flood_depth_m' in result, "Missing flood_depth_m"
    assert 'risk_category' in result, "Missing risk_category"
    assert result['risk_category'] in ['Low', 'Moderate', 'High', 'Extreme'], "Invalid risk category"
    
    print("  ✓ Test passed")
except Exception as e:
    print(f"  ✗ Test failed: {e}")

# Test Case 2: High elevation area (should be safe)
print("\nTest Case 2: Denver, CO (high elevation - not coastal)")
print("-" * 60)
lat = 39.7392
lon = -104.9903
slr_meters = 1.0
surge_meters = 3.0

print(f"Location: lat={lat}, lon={lon}")
print(f"Sea Level Rise: {slr_meters}m")
print(f"Storm Surge: {surge_meters}m")
print(f"Total Water Level: {slr_meters + surge_meters}m")

try:
    result = analyze_flood_risk(lat, lon, slr_meters, surge_meters)
    print(f"\nResults:")
    print(f"  Elevation: {result['elevation_m']}m")
    print(f"  Is Underwater: {result['is_underwater']}")
    print(f"  Flood Depth: {result['flood_depth_m']}m")
    print(f"  Risk Category: {result['risk_category']}")
    
    assert result['is_underwater'] == False, "Denver should not be underwater"
    assert result['flood_depth_m'] == 0.0, "Flood depth should be 0"
    assert result['risk_category'] == 'Low', "Risk should be Low"
    
    print("  ✓ Test passed")
except Exception as e:
    print(f"  ✗ Test failed: {e}")

# Test Case 3: No flooding scenario
print("\nTest Case 3: No flooding (minimal SLR and surge)")
print("-" * 60)
lat = 25.7617
lon = -80.1918
slr_meters = 0.1
surge_meters = 0.2

print(f"Location: lat={lat}, lon={lon}")
print(f"Sea Level Rise: {slr_meters}m")
print(f"Storm Surge: {surge_meters}m")
print(f"Total Water Level: {slr_meters + surge_meters}m")

try:
    result = analyze_flood_risk(lat, lon, slr_meters, surge_meters)
    print(f"\nResults:")
    print(f"  Elevation: {result['elevation_m']}m")
    print(f"  Is Underwater: {result['is_underwater']}")
    print(f"  Flood Depth: {result['flood_depth_m']}m")
    print(f"  Risk Category: {result['risk_category']}")
    print("  ✓ Test passed")
except Exception as e:
    print(f"  ✗ Test failed: {e}")

# Test Case 4: Extreme flooding scenario
print("\nTest Case 4: Extreme flooding (high SLR + surge)")
print("-" * 60)
lat = 25.7617
lon = -80.1918
slr_meters = 1.0
surge_meters = 3.0

print(f"Location: lat={lat}, lon={lon}")
print(f"Sea Level Rise: {slr_meters}m")
print(f"Storm Surge: {surge_meters}m")
print(f"Total Water Level: {slr_meters + surge_meters}m")

try:
    result = analyze_flood_risk(lat, lon, slr_meters, surge_meters)
    print(f"\nResults:")
    print(f"  Elevation: {result['elevation_m']}m")
    print(f"  Is Underwater: {result['is_underwater']}")
    print(f"  Flood Depth: {result['flood_depth_m']}m")
    print(f"  Risk Category: {result['risk_category']}")
    print("  ✓ Test passed")
except Exception as e:
    print(f"  ✗ Test failed: {e}")

print("\n" + "=" * 60)
print("Testing complete!")
print("=" * 60)
