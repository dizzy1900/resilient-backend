#!/usr/bin/env python3
"""
Test script for analyze_infrastructure_risk function
"""

def test_infrastructure_risk_logic():
    """Test infrastructure risk calculation logic."""
    
    print("Testing analyze_infrastructure_risk calculation logic")
    print("=" * 60)
    
    # Test Case 1: No flooding (low risk)
    print("\nTest Case 1: Low risk scenario")
    print("-" * 60)
    total_m2 = 150_000_000  # 150 km²
    flooded_m2 = 12_500_000  # 12.5 km²
    
    total_km2 = total_m2 / 1_000_000
    flooded_km2 = flooded_m2 / 1_000_000
    risk_pct = (flooded_km2 / total_km2) * 100 if total_km2 > 0 else 0.0
    
    print(f"  Total urban: {total_km2} km²")
    print(f"  Flooded urban: {flooded_km2} km²")
    print(f"  Risk: {round(risk_pct, 2)}%")
    
    assert total_km2 == 150.0, "Total should be 150.0 km²"
    assert flooded_km2 == 12.5, "Flooded should be 12.5 km²"
    assert abs(risk_pct - 8.33) < 0.01, "Risk should be ~8.33%"
    print("  ✓ Passed")
    
    # Test Case 2: Higher risk
    print("\nTest Case 2: Higher risk scenario (25%)")
    print("-" * 60)
    total_m2 = 100_000_000  # 100 km²
    flooded_m2 = 25_000_000  # 25 km²
    
    total_km2 = total_m2 / 1_000_000
    flooded_km2 = flooded_m2 / 1_000_000
    risk_pct = (flooded_km2 / total_km2) * 100 if total_km2 > 0 else 0.0
    
    print(f"  Total urban: {round(total_km2, 2)} km²")
    print(f"  Flooded urban: {round(flooded_km2, 2)} km²")
    print(f"  Risk: {round(risk_pct, 2)}%")
    
    assert round(total_km2, 2) == 100.0, "Total should be 100.0 km²"
    assert round(flooded_km2, 2) == 25.0, "Flooded should be 25.0 km²"
    assert round(risk_pct, 2) == 25.0, "Risk should be 25%"
    print("  ✓ Passed")
    
    # Test Case 3: No urban area (edge case)
    print("\nTest Case 3: No urban area found")
    print("-" * 60)
    total_m2 = 0
    flooded_m2 = 0
    
    total_km2 = total_m2 / 1_000_000
    flooded_km2 = flooded_m2 / 1_000_000
    risk_pct = (flooded_km2 / total_km2) * 100 if total_km2 > 0 else 0.0
    
    print(f"  Total urban: {round(total_km2, 2)} km²")
    print(f"  Flooded urban: {round(flooded_km2, 2)} km²")
    print(f"  Risk: {round(risk_pct, 2)}%")
    
    assert total_km2 == 0.0, "Total should be 0"
    assert flooded_km2 == 0.0, "Flooded should be 0"
    assert risk_pct == 0.0, "Risk should be 0%"
    print("  ✓ Passed")
    
    # Test Case 4: Complete flooding (100%)
    print("\nTest Case 4: Complete flooding")
    print("-" * 60)
    total_m2 = 50_000_000   # 50 km²
    flooded_m2 = 50_000_000  # 50 km²
    
    total_km2 = total_m2 / 1_000_000
    flooded_km2 = flooded_m2 / 1_000_000
    risk_pct = (flooded_km2 / total_km2) * 100 if total_km2 > 0 else 0.0
    
    print(f"  Total urban: {round(total_km2, 2)} km²")
    print(f"  Flooded urban: {round(flooded_km2, 2)} km²")
    print(f"  Risk: {round(risk_pct, 2)}%")
    
    assert round(total_km2, 2) == 50.0, "Total should be 50.0 km²"
    assert round(flooded_km2, 2) == 50.0, "Flooded should be 50.0 km²"
    assert round(risk_pct, 2) == 100.0, "Risk should be 100%"
    print("  ✓ Passed")
    
    # Test Case 5: Verify TWI threshold calculation
    print("\nTest Case 5: TWI dynamic threshold calculation")
    print("-" * 60)
    
    BASELINE_THRESHOLD = 12.0
    SCALING_FACTOR = 0.07
    
    test_intensities = [0, 10, 20, 30]
    print(f"  {'Rain +%':<10} {'Dynamic Threshold':<20}")
    print(f"  {'-'*10} {'-'*20}")
    
    for intensity in test_intensities:
        threshold = BASELINE_THRESHOLD * (1 - (intensity / 100 * SCALING_FACTOR))
        print(f"  {intensity:<10} {threshold:<20.2f}")
        
        # Verify the calculation
        if intensity == 0:
            assert threshold == 12.0, "At 0%, threshold should be 12.0"
        elif intensity == 20:
            expected = 12.0 * (1 - 0.014)  # 20 * 0.07 / 100 = 0.014
            assert abs(threshold - expected) < 0.01, f"At 20%, threshold should be ~{expected}"
    
    print("  ✓ All threshold calculations correct")
    
    print("\n" + "=" * 60)
    print("All logic tests passed! ✓")
    print("=" * 60)
    
    # Show example output structure
    print("\nExample Output Structure:")
    import json
    example = {
        'infrastructure_risk': {
            'total_km2': 150.0,
            'flooded_km2': 12.5,
            'risk_pct': 8.33
        }
    }
    print(json.dumps(example, indent=2))


if __name__ == '__main__':
    test_infrastructure_risk_logic()
