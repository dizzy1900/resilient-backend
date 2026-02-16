#!/usr/bin/env python3
"""
Test script for analyze_urban_impact function
"""

# Test the calculation logic without GEE

def test_urban_impact_logic():
    """Test urban impact calculation logic."""
    
    print("Testing analyze_urban_impact calculation logic")
    print("=" * 60)
    
    # Test Case 1: No flooding (water level below all urban areas)
    print("\nTest Case 1: No flooding")
    print("-" * 60)
    total_urban_m2 = 15_200_000  # 15.2 km²
    flooded_urban_m2 = 0
    
    total_urban_km2 = total_urban_m2 / 1_000_000
    flooded_urban_km2 = flooded_urban_m2 / 1_000_000
    urban_impact_pct = (flooded_urban_km2 / total_urban_km2) * 100 if total_urban_km2 > 0 else 0.0
    
    print(f"  Total Urban: {total_urban_km2} km²")
    print(f"  Flooded Urban: {flooded_urban_km2} km²")
    print(f"  Impact: {urban_impact_pct}%")
    
    assert total_urban_km2 == 15.2, "Total should be 15.2 km²"
    assert flooded_urban_km2 == 0.0, "Flooded should be 0"
    assert urban_impact_pct == 0.0, "Impact should be 0%"
    print("  ✓ Passed")
    
    # Test Case 2: Partial flooding (22.3% impact)
    print("\nTest Case 2: Partial flooding (22.3% impact)")
    print("-" * 60)
    total_urban_m2 = 15_200_000  # 15.2 km²
    flooded_urban_m2 = 3_400_000  # 3.4 km²
    
    total_urban_km2 = total_urban_m2 / 1_000_000
    flooded_urban_km2 = flooded_urban_m2 / 1_000_000
    urban_impact_pct = (flooded_urban_km2 / total_urban_km2) * 100 if total_urban_km2 > 0 else 0.0
    
    print(f"  Total Urban: {round(total_urban_km2, 2)} km²")
    print(f"  Flooded Urban: {round(flooded_urban_km2, 2)} km²")
    print(f"  Impact: {round(urban_impact_pct, 2)}%")
    
    assert round(total_urban_km2, 2) == 15.2, "Total should be 15.2 km²"
    assert round(flooded_urban_km2, 2) == 3.4, "Flooded should be 3.4 km²"
    assert round(urban_impact_pct, 2) == 22.37, "Impact should be 22.37%"
    print("  ✓ Passed")
    
    # Test Case 3: Complete flooding (100% impact)
    print("\nTest Case 3: Complete flooding (100% impact)")
    print("-" * 60)
    total_urban_m2 = 15_200_000  # 15.2 km²
    flooded_urban_m2 = 15_200_000  # 15.2 km²
    
    total_urban_km2 = total_urban_m2 / 1_000_000
    flooded_urban_km2 = flooded_urban_m2 / 1_000_000
    urban_impact_pct = (flooded_urban_km2 / total_urban_km2) * 100 if total_urban_km2 > 0 else 0.0
    
    print(f"  Total Urban: {round(total_urban_km2, 2)} km²")
    print(f"  Flooded Urban: {round(flooded_urban_km2, 2)} km²")
    print(f"  Impact: {round(urban_impact_pct, 2)}%")
    
    assert round(total_urban_km2, 2) == 15.2, "Total should be 15.2 km²"
    assert round(flooded_urban_km2, 2) == 15.2, "Flooded should be 15.2 km²"
    assert round(urban_impact_pct, 2) == 100.0, "Impact should be 100%"
    print("  ✓ Passed")
    
    # Test Case 4: No urban area (edge case)
    print("\nTest Case 4: No urban area found")
    print("-" * 60)
    total_urban_m2 = 0
    flooded_urban_m2 = 0
    
    total_urban_km2 = total_urban_m2 / 1_000_000
    flooded_urban_km2 = flooded_urban_m2 / 1_000_000
    urban_impact_pct = (flooded_urban_km2 / total_urban_km2) * 100 if total_urban_km2 > 0 else 0.0
    
    print(f"  Total Urban: {round(total_urban_km2, 2)} km²")
    print(f"  Flooded Urban: {round(flooded_urban_km2, 2)} km²")
    print(f"  Impact: {round(urban_impact_pct, 2)}%")
    
    assert total_urban_km2 == 0.0, "Total should be 0"
    assert flooded_urban_km2 == 0.0, "Flooded should be 0"
    assert urban_impact_pct == 0.0, "Impact should be 0%"
    print("  ✓ Passed")
    
    # Test Case 5: Small urban area
    print("\nTest Case 5: Small urban area (1.5 km²)")
    print("-" * 60)
    total_urban_m2 = 1_500_000  # 1.5 km²
    flooded_urban_m2 = 450_000   # 0.45 km²
    
    total_urban_km2 = total_urban_m2 / 1_000_000
    flooded_urban_km2 = flooded_urban_m2 / 1_000_000
    urban_impact_pct = (flooded_urban_km2 / total_urban_km2) * 100 if total_urban_km2 > 0 else 0.0
    
    print(f"  Total Urban: {round(total_urban_km2, 2)} km²")
    print(f"  Flooded Urban: {round(flooded_urban_km2, 2)} km²")
    print(f"  Impact: {round(urban_impact_pct, 2)}%")
    
    assert round(total_urban_km2, 2) == 1.5, "Total should be 1.5 km²"
    assert round(flooded_urban_km2, 2) == 0.45, "Flooded should be 0.45 km²"
    assert round(urban_impact_pct, 2) == 30.0, "Impact should be 30%"
    print("  ✓ Passed")
    
    print("\n" + "=" * 60)
    print("All logic tests passed! ✓")
    print("=" * 60)
    
    # Show example output structure
    print("\nExample Output Structure:")
    import json
    example = {
        'total_urban_km2': 15.2,
        'flooded_urban_km2': 3.4,
        'urban_impact_pct': 22.37
    }
    print(json.dumps(example, indent=2))


if __name__ == '__main__':
    test_urban_impact_logic()
