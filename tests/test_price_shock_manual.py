#!/usr/bin/env python3
"""
Manual test script for the Price Shock Engine.

Run this directly without pytest:
    python tests/test_price_shock_manual.py
"""

from price_shock_engine import calculate_price_shock, get_crop_info, get_all_crops


def test_basic_calculation():
    """Test basic price shock calculation."""
    print("\n=== Test 1: Basic Maize Calculation (30% yield loss) ===")
    
    result = calculate_price_shock(
        crop_type="maize",
        baseline_yield_tons=1000.0,
        stressed_yield_tons=700.0
    )
    
    print(f"Baseline Price: ${result['baseline_price']}/ton")
    print(f"Shocked Price: ${result['shocked_price']}/ton")
    print(f"Price Increase: {result['price_increase_pct']}%")
    print(f"Yield Loss: {result['yield_loss_pct']}%")
    print(f"Elasticity: {result['elasticity']}")
    print(f"\nRevenue Impact:")
    print(f"  Baseline Revenue: ${result['revenue_impact']['baseline_revenue_usd']:,.2f}")
    print(f"  Stressed Revenue: ${result['revenue_impact']['stressed_revenue_usd']:,.2f}")
    print(f"  Net Change: ${result['revenue_impact']['net_revenue_change_usd']:,.2f} ({result['revenue_impact']['net_revenue_change_pct']:.2f}%)")
    print(f"\nRecommendation: {result['forward_contract_recommendation']}")
    
    assert result['yield_loss_pct'] == 30.0
    assert result['baseline_price'] == 180.0
    assert abs(result['price_increase_pct'] - 120.0) < 0.1
    print("✓ Test passed!")


def test_multiple_crops():
    """Test different crop types."""
    print("\n=== Test 2: Multiple Crop Types (10% yield loss each) ===")
    
    crops = ["maize", "wheat", "soybeans", "rice", "cocoa"]
    
    for crop in crops:
        result = calculate_price_shock(
            crop_type=crop,
            baseline_yield_tons=1000.0,
            stressed_yield_tons=900.0
        )
        print(f"\n{crop.upper()}:")
        print(f"  Baseline: ${result['baseline_price']}/ton")
        print(f"  Shocked: ${result['shocked_price']}/ton")
        print(f"  Price Increase: {result['price_increase_pct']:.2f}%")
        print(f"  Elasticity: {result['elasticity']}")
    
    print("\n✓ Test passed!")


def test_severe_loss():
    """Test severe yield loss scenario."""
    print("\n=== Test 3: Severe Yield Loss (40% loss) ===")
    
    result = calculate_price_shock(
        crop_type="rice",
        baseline_yield_tons=2000.0,
        stressed_yield_tons=1200.0
    )
    
    print(f"Yield Loss: {result['yield_loss_pct']}%")
    print(f"Price Increase: {result['price_increase_pct']:.2f}%")
    print(f"Shocked Price: ${result['shocked_price']:.2f}/ton")
    print(f"\nRecommendation: {result['forward_contract_recommendation']}")
    
    assert "URGENT" in result['forward_contract_recommendation']
    print("✓ Test passed!")


def test_zero_loss():
    """Test zero yield loss."""
    print("\n=== Test 4: Zero Yield Loss ===")
    
    result = calculate_price_shock(
        crop_type="soybeans",
        baseline_yield_tons=800.0,
        stressed_yield_tons=800.0
    )
    
    print(f"Yield Loss: {result['yield_loss_pct']}%")
    print(f"Price Increase: {result['price_increase_pct']}%")
    print(f"Baseline Price: ${result['baseline_price']}")
    print(f"Shocked Price: ${result['shocked_price']}")
    
    assert result['yield_loss_pct'] == 0.0
    assert result['price_increase_pct'] == 0.0
    assert result['shocked_price'] == result['baseline_price']
    print("✓ Test passed!")


def test_complete_failure():
    """Test complete crop failure."""
    print("\n=== Test 5: Complete Crop Failure (100% loss) ===")
    
    result = calculate_price_shock(
        crop_type="wheat",
        baseline_yield_tons=500.0,
        stressed_yield_tons=0.0
    )
    
    print(f"Yield Loss: {result['yield_loss_pct']}%")
    print(f"Price Increase: {result['price_increase_pct']:.2f}%")
    print(f"Shocked Price: ${result['shocked_price']:.2f}/ton")
    print(f"Revenue Change: ${result['revenue_impact']['net_revenue_change_usd']:,.2f}")
    
    assert result['yield_loss_pct'] == 100.0
    assert result['revenue_impact']['stressed_revenue_usd'] == 0.0
    print("✓ Test passed!")


def test_crop_info():
    """Test crop info retrieval."""
    print("\n=== Test 6: Crop Information Retrieval ===")
    
    info = get_crop_info("maize")
    print(f"\nMaize Info:")
    print(f"  Baseline Price: ${info['baseline_price_usd_per_ton']}/ton")
    print(f"  Elasticity: {info['supply_elasticity']}")
    print(f"  Interpretation: {info['elasticity_interpretation']}")
    
    assert info['baseline_price_usd_per_ton'] == 180.0
    assert info['supply_elasticity'] == 0.25
    print("✓ Test passed!")


def test_error_handling():
    """Test error handling."""
    print("\n=== Test 7: Error Handling ===")
    
    # Test invalid crop
    try:
        calculate_price_shock("banana", 1000.0, 900.0)
        print("✗ Should have raised ValueError for invalid crop")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    # Test negative baseline
    try:
        calculate_price_shock("maize", -100.0, 900.0)
        print("✗ Should have raised ValueError for negative baseline")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    # Test negative stressed yield
    try:
        calculate_price_shock("maize", 1000.0, -50.0)
        print("✗ Should have raised ValueError for negative stressed yield")
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    print("✓ All error tests passed!")


def test_highly_inelastic():
    """Test highly inelastic crop (cocoa)."""
    print("\n=== Test 8: Highly Inelastic Crop (Cocoa) ===")
    
    result = calculate_price_shock(
        crop_type="cocoa",
        baseline_yield_tons=100.0,
        stressed_yield_tons=85.0
    )
    
    print(f"Yield Loss: {result['yield_loss_pct']}%")
    print(f"Elasticity: {result['elasticity']} (highly inelastic)")
    print(f"Price Increase: {result['price_increase_pct']:.2f}%")
    print(f"Baseline: ${result['baseline_price']}/ton")
    print(f"Shocked: ${result['shocked_price']:.2f}/ton")
    
    # 15% loss / 0.15 elasticity = 100% price increase
    assert abs(result['price_increase_pct'] - 100.0) < 0.1
    print("✓ Test passed!")


def main():
    """Run all tests."""
    print("=" * 70)
    print("COMMODITY PRICE SHOCK ENGINE - MANUAL TEST SUITE")
    print("=" * 70)
    
    try:
        test_basic_calculation()
        test_multiple_crops()
        test_severe_loss()
        test_zero_loss()
        test_complete_failure()
        test_crop_info()
        test_error_handling()
        test_highly_inelastic()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        return 0
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
