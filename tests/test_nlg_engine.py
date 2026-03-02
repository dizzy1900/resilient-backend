#!/usr/bin/env python3
"""
Test suite for Deterministic NLG Executive Summary Generator
============================================================

Tests all module-specific summary generators to ensure correct
string generation from simulation data.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlg_engine import generate_deterministic_summary, format_currency, format_percentage


def test_health_public_summary():
    """Test public health DALY summary generation."""
    print("\n" + "="*80)
    print("TEST 1: Public Health DALY Summary")
    print("="*80)
    
    data = {
        'dalys_averted': 4107.0,
        'economic_value_preserved_usd': 98568000.0,
        'intervention_type': 'urban_cooling_center',
        'baseline_dalys_lost': 26614.0,
        'wbgt_estimate': 30.8,
        'malaria_risk_score': 100
    }
    
    summary = generate_deterministic_summary('health_public', 'Bangkok', data)
    
    print(f"Location: Bangkok")
    print(f"Module: health_public")
    print(f"\nInput Data:")
    print(f"  - DALYs averted: {data['dalys_averted']:,.0f}")
    print(f"  - Economic value: ${data['economic_value_preserved_usd']:,.0f}")
    print(f"  - Intervention: {data['intervention_type']}")
    print(f"  - WBGT: {data['wbgt_estimate']}°C")
    print(f"  - Malaria risk: {data['malaria_risk_score']}")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    # Assertions
    assert "Bangkok" in summary, "Should mention location"
    assert "4,107" in summary or "4107" in summary, "Should mention DALYs averted"
    assert "urban cooling centers" in summary.lower(), "Should mention intervention"
    assert len(summary.split('. ')) >= 3, "Should have at least 3 sentences"
    print("✅ PASSED")


def test_health_private_summary_positive_npv():
    """Test private sector workplace cooling with positive NPV."""
    print("\n" + "="*80)
    print("TEST 2: Private Sector Workplace Cooling (Positive NPV)")
    print("="*80)
    
    data = {
        'npv_10yr_at_10pct_discount': 7249818.25,
        'payback_period_years': 0.2,
        'intervention_capex': 250000.0,
        'intervention_annual_opex': 30000.0,
        'intervention_type': 'hvac_retrofit',
        'avoided_annual_economic_loss_usd': 1250000.0
    }
    
    summary = generate_deterministic_summary('health_private', 'Factory Complex, Chennai', data)
    
    print(f"Location: Factory Complex, Chennai")
    print(f"Module: health_private")
    print(f"\nInput Data:")
    print(f"  - NPV (10-year): ${data['npv_10yr_at_10pct_discount']:,.0f}")
    print(f"  - Payback: {data['payback_period_years']:.1f} years")
    print(f"  - CAPEX: ${data['intervention_capex']:,.0f}")
    print(f"  - Intervention: {data['intervention_type']}")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "Chennai" in summary, "Should mention location"
    assert "NPV" in summary or "7.2" in summary, "Should mention NPV"
    assert "excellent investment" in summary.lower() or "attractive" in summary.lower(), "Should recommend investment"
    print("✅ PASSED")


def test_health_private_summary_negative_npv():
    """Test private sector workplace cooling with negative NPV."""
    print("\n" + "="*80)
    print("TEST 3: Private Sector Workplace Cooling (Negative NPV)")
    print("="*80)
    
    data = {
        'npv_10yr_at_10pct_discount': -150000.0,
        'payback_period_years': None,
        'intervention_capex': 500000.0,
        'intervention_annual_opex': 100000.0,
        'intervention_type': 'hvac_retrofit',
        'avoided_annual_economic_loss_usd': 80000.0
    }
    
    summary = generate_deterministic_summary('health_private', 'Small Office, Mumbai', data)
    
    print(f"Location: Small Office, Mumbai")
    print(f"Module: health_private")
    print(f"\nInput Data:")
    print(f"  - NPV (10-year): ${data['npv_10yr_at_10pct_discount']:,.0f}")
    print(f"  - CAPEX: ${data['intervention_capex']:,.0f}")
    print(f"  - Annual OPEX: ${data['intervention_annual_opex']:,.0f}")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "Mumbai" in summary, "Should mention location"
    assert "not recommended" in summary.lower() or "negative" in summary.lower(), "Should recommend against investment"
    print("✅ PASSED")


def test_agriculture_summary():
    """Test agriculture crop switching summary."""
    print("\n" + "="*80)
    print("TEST 4: Agriculture Crop Switching")
    print("="*80)
    
    data = {
        'current_yield_tons': 3.2,
        'proposed_yield_tons': 4.5,
        'current_revenue': 640000.0,
        'proposed_revenue': 900000.0,
        'crop_type': 'maize'
    }
    
    summary = generate_deterministic_summary('agriculture', 'Midwest Farm Belt', data)
    
    print(f"Location: Midwest Farm Belt")
    print(f"Module: agriculture")
    print(f"\nInput Data:")
    print(f"  - Current yield: {data['current_yield_tons']} tons/ha")
    print(f"  - Proposed yield: {data['proposed_yield_tons']} tons/ha")
    print(f"  - Current revenue: ${data['current_revenue']:,.0f}")
    print(f"  - Proposed revenue: ${data['proposed_revenue']:,.0f}")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "Midwest" in summary, "Should mention location"
    assert "maize" in summary.lower(), "Should mention crop"
    assert "40" in summary or "41" in summary, "Should mention ~40% yield increase"
    print("✅ PASSED")


def test_coastal_summary():
    """Test coastal flood risk summary."""
    print("\n" + "="*80)
    print("TEST 5: Coastal Flood Risk")
    print("="*80)
    
    data = {
        'slr_projection': 0.5,  # 50cm
        'annual_damage_usd': 2500000.0,
        'intervention_type': 'sea_wall',
        'damage_reduction_pct': 70.0
    }
    
    summary = generate_deterministic_summary('coastal', 'Miami Beach Condominiums', data)
    
    print(f"Location: Miami Beach Condominiums")
    print(f"Module: coastal")
    print(f"\nInput Data:")
    print(f"  - Sea level rise: {data['slr_projection']}m")
    print(f"  - Annual damage: ${data['annual_damage_usd']:,.0f}")
    print(f"  - Intervention: {data['intervention_type']}")
    print(f"  - Damage reduction: {data['damage_reduction_pct']}%")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "Miami" in summary, "Should mention location"
    assert "50cm" in summary or "50 cm" in summary, "Should mention sea level rise"
    assert "70" in summary, "Should mention damage reduction percentage"
    print("✅ PASSED")


def test_flood_summary():
    """Test urban flood risk summary."""
    print("\n" + "="*80)
    print("TEST 6: Urban Flood Risk")
    print("="*80)
    
    data = {
        'flood_depth_meters': 0.8,
        'annual_damage_usd': 1200000.0,
        'intervention_type': 'sponge_city',
        'damage_reduction_pct': 55.0
    }
    
    summary = generate_deterministic_summary('flood', 'Downtown Business District', data)
    
    print(f"Location: Downtown Business District")
    print(f"Module: flood")
    print(f"\nInput Data:")
    print(f"  - Flood depth: {data['flood_depth_meters']}m")
    print(f"  - Annual damage: ${data['annual_damage_usd']:,.0f}")
    print(f"  - Intervention: {data['intervention_type']}")
    print(f"  - Damage reduction: {data['damage_reduction_pct']}%")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "Downtown" in summary, "Should mention location"
    assert "80cm" in summary or "80 cm" in summary, "Should mention flood depth"
    assert "sponge city" in summary.lower(), "Should mention intervention"
    print("✅ PASSED")


def test_price_shock_summary():
    """Test commodity price shock summary."""
    print("\n" + "="*80)
    print("TEST 7: Commodity Price Shock")
    print("="*80)
    
    data = {
        'crop_type': 'wheat',
        'yield_loss_pct': 15.0,
        'price_increase_pct': 37.5,
        'revenue_impact_usd': 50000.0
    }
    
    summary = generate_deterministic_summary('price_shock', 'Kansas Wheat Belt', data)
    
    print(f"Location: Kansas Wheat Belt")
    print(f"Module: price_shock")
    print(f"\nInput Data:")
    print(f"  - Crop: {data['crop_type']}")
    print(f"  - Yield loss: {data['yield_loss_pct']}%")
    print(f"  - Price increase: {data['price_increase_pct']}%")
    print(f"  - Revenue impact: ${data['revenue_impact_usd']:,.0f}")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "Kansas" in summary, "Should mention location"
    assert "wheat" in summary.lower(), "Should mention crop"
    assert "15" in summary, "Should mention yield loss"
    print("✅ PASSED")


def test_fallback_summary():
    """Test fallback for unknown module."""
    print("\n" + "="*80)
    print("TEST 8: Fallback for Unknown Module")
    print("="*80)
    
    data = {'random_key': 'random_value'}
    
    summary = generate_deterministic_summary('unknown_module', 'Test Location', data)
    
    print(f"Location: Test Location")
    print(f"Module: unknown_module")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "Test Location" in summary, "Should mention location"
    assert "successfully processed" in summary.lower(), "Should use fallback message"
    print("✅ PASSED")


def test_utility_functions():
    """Test utility functions for value formatting."""
    print("\n" + "="*80)
    print("TEST 9: Utility Functions")
    print("="*80)
    
    # Test currency formatting
    assert format_currency(1500000) == "$1.5M", "Should format millions"
    assert format_currency(2500000000) == "$2.5B", "Should format billions"
    assert format_currency(50000) == "$50,000", "Should format thousands"
    print("✅ Currency formatting works")
    
    # Test percentage formatting
    assert format_percentage(25.5) == "26%", "Should format percentages (0-100 scale)"
    assert format_percentage(0.255, decimals=1) == "25.5%", "Should format percentages (0-1 scale)"
    print("✅ Percentage formatting works")
    
    print("✅ PASSED")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("DETERMINISTIC NLG EXECUTIVE SUMMARY - TEST SUITE")
    print("="*80)
    
    tests = [
        test_health_public_summary,
        test_health_private_summary_positive_npv,
        test_health_private_summary_negative_npv,
        test_agriculture_summary,
        test_coastal_summary,
        test_flood_summary,
        test_price_shock_summary,
        test_fallback_summary,
        test_utility_functions,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n❌ {failed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
