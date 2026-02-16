#!/usr/bin/env python3
"""
Test the flood risk calculation logic without GEE
"""

def test_flood_risk_logic():
    """Test flood risk calculations with different elevation scenarios."""
    
    print("Testing flood risk calculation logic")
    print("=" * 60)
    
    # Test Case 1: Location above water level (no flooding)
    print("\nTest Case 1: Elevation above water level")
    elevation_m = 5.0
    slr_meters = 0.5
    surge_meters = 1.5
    total_water_level = slr_meters + surge_meters
    is_underwater = elevation_m < total_water_level
    flood_depth_m = max(0.0, total_water_level - elevation_m)
    
    print(f"  Elevation: {elevation_m}m")
    print(f"  Total Water Level: {total_water_level}m")
    print(f"  Is Underwater: {is_underwater}")
    print(f"  Flood Depth: {flood_depth_m}m")
    
    assert is_underwater == False, "Should not be underwater"
    assert flood_depth_m == 0.0, "Flood depth should be 0"
    print("  ✓ Passed")
    
    # Test Case 2: Location below water level (flooded)
    print("\nTest Case 2: Elevation below water level")
    elevation_m = 1.0
    slr_meters = 0.5
    surge_meters = 1.5
    total_water_level = slr_meters + surge_meters
    is_underwater = elevation_m < total_water_level
    flood_depth_m = max(0.0, total_water_level - elevation_m)
    
    print(f"  Elevation: {elevation_m}m")
    print(f"  Total Water Level: {total_water_level}m")
    print(f"  Is Underwater: {is_underwater}")
    print(f"  Flood Depth: {flood_depth_m}m")
    
    assert is_underwater == True, "Should be underwater"
    assert flood_depth_m == 1.0, "Flood depth should be 1.0m"
    print("  ✓ Passed")
    
    # Test Case 3: Risk categories
    print("\nTest Case 3: Risk category assignment")
    test_cases = [
        (0.0, "Low"),
        (0.3, "Moderate"),
        (0.8, "High"),
        (2.0, "Extreme")
    ]
    
    for flood_depth, expected_category in test_cases:
        if flood_depth == 0:
            risk_category = "Low"
        elif flood_depth < 0.5:
            risk_category = "Moderate"
        elif flood_depth < 1.5:
            risk_category = "High"
        else:
            risk_category = "Extreme"
        
        print(f"  Flood depth {flood_depth}m → {risk_category} (expected: {expected_category})")
        assert risk_category == expected_category, f"Risk category mismatch for {flood_depth}m"
    
    print("  ✓ All risk categories correct")
    
    # Test Case 4: Edge case - exactly at water level
    print("\nTest Case 4: Elevation exactly at water level")
    elevation_m = 2.0
    slr_meters = 0.5
    surge_meters = 1.5
    total_water_level = slr_meters + surge_meters
    is_underwater = elevation_m < total_water_level
    flood_depth_m = max(0.0, total_water_level - elevation_m)
    
    print(f"  Elevation: {elevation_m}m")
    print(f"  Total Water Level: {total_water_level}m")
    print(f"  Is Underwater: {is_underwater}")
    print(f"  Flood Depth: {flood_depth_m}m")
    
    assert is_underwater == False, "Should not be underwater (at exact level)"
    assert flood_depth_m == 0.0, "Flood depth should be 0"
    print("  ✓ Passed")
    
    # Test Case 5: Negative elevation (below sea level)
    print("\nTest Case 5: Negative elevation (below sea level)")
    elevation_m = -1.0
    slr_meters = 0.5
    surge_meters = 1.5
    total_water_level = slr_meters + surge_meters
    is_underwater = elevation_m < total_water_level
    flood_depth_m = max(0.0, total_water_level - elevation_m)
    
    print(f"  Elevation: {elevation_m}m")
    print(f"  Total Water Level: {total_water_level}m")
    print(f"  Is Underwater: {is_underwater}")
    print(f"  Flood Depth: {flood_depth_m}m")
    
    assert is_underwater == True, "Should be underwater"
    assert flood_depth_m == 3.0, "Flood depth should be 3.0m"
    print("  ✓ Passed")
    
    print("\n" + "=" * 60)
    print("All logic tests passed! ✓")
    print("=" * 60)


if __name__ == '__main__':
    test_flood_risk_logic()
