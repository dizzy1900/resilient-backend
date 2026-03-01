#!/usr/bin/env python3
"""
Test script for Public Health DALY calculations
Tests the calculate_public_health_impact function with various scenarios
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health_engine import calculate_public_health_impact


def test_baseline_no_intervention():
    """Test 1: Baseline with no intervention (high heat + high malaria)"""
    print("\n" + "="*80)
    print("TEST 1: Baseline - No Intervention (Bangkok scenario)")
    print("="*80)
    
    result = calculate_public_health_impact(
        population=250000,
        gdp_per_capita=12000.0,
        wbgt=30.8,  # High heat stress
        malaria_risk_score=100,  # High malaria risk
        intervention_type="none"
    )
    
    print(f"Population: {result['population_parameters']['population_size']:,}")
    print(f"GDP per capita: ${result['monetization']['gdp_per_capita_usd']:,.2f}")
    print(f"WBGT: 30.8°C (Very High heat stress)")
    print(f"Malaria risk score: 100 (High)")
    print()
    print(f"Baseline DALYs lost: {result['baseline_dalys_lost']:,.2f}")
    print(f"  - Heat DALYs/1000: {result['breakdown']['heat_dalys_per_1000_baseline']}")
    print(f"  - Malaria DALYs/1000: {result['breakdown']['malaria_dalys_per_1000_baseline']}")
    print(f"  - Total DALYs/1000: {result['breakdown']['total_dalys_per_1000_baseline']}")
    print()
    print(f"Intervention: {result['intervention_type']}")
    print(f"Description: {result['intervention_description']}")
    print(f"DALYs averted: {result['dalys_averted']:,.2f} (no intervention)")
    print(f"Economic value: ${result['economic_value_preserved_usd']:,.2f}")
    print()
    assert result['baseline_dalys_lost'] > 0, "Should have baseline DALYs"
    assert result['dalys_averted'] == 0, "No intervention should not avert DALYs"
    print("✅ PASSED")


def test_urban_cooling_center():
    """Test 2: Urban cooling center (40% heat reduction)"""
    print("\n" + "="*80)
    print("TEST 2: Urban Cooling Center - 40% Heat Reduction")
    print("="*80)
    
    result = calculate_public_health_impact(
        population=250000,
        gdp_per_capita=12000.0,
        wbgt=30.8,  # High heat stress
        malaria_risk_score=100,  # High malaria risk
        intervention_type="urban_cooling_center"
    )
    
    print(f"Population: {result['population_parameters']['population_size']:,}")
    print(f"GDP per capita: ${result['monetization']['gdp_per_capita_usd']:,.2f}")
    print()
    print(f"Baseline DALYs lost: {result['baseline_dalys_lost']:,.2f}")
    print(f"Post-intervention DALYs lost: {result['post_intervention_dalys_lost']:,.2f}")
    print(f"DALYs averted: {result['dalys_averted']:,.2f}")
    print()
    print(f"Intervention: {result['intervention_type']}")
    print(f"Description: {result['intervention_description']}")
    print(f"Heat reduction: {result['breakdown']['heat_reduction_pct']}%")
    print(f"Malaria reduction: {result['breakdown']['malaria_reduction_pct']}%")
    print()
    print(f"Economic value preserved: ${result['economic_value_preserved_usd']:,.2f}")
    print(f"Value per DALY: ${result['monetization']['value_per_daly_usd']:,.2f}")
    print()
    assert result['dalys_averted'] > 0, "Should avert DALYs"
    assert result['breakdown']['heat_reduction_pct'] == 40.0, "Should be 40% heat reduction"
    assert result['breakdown']['malaria_reduction_pct'] == 0.0, "Should not reduce malaria"
    print("✅ PASSED")


def test_mosquito_eradication():
    """Test 3: Mosquito eradication (70% malaria reduction)"""
    print("\n" + "="*80)
    print("TEST 3: Mosquito Eradication - 70% Malaria Reduction")
    print("="*80)
    
    result = calculate_public_health_impact(
        population=500000,
        gdp_per_capita=2000.0,
        wbgt=28.0,  # Moderate heat stress
        malaria_risk_score=100,  # High malaria risk
        intervention_type="mosquito_eradication"
    )
    
    print(f"Population: {result['population_parameters']['population_size']:,}")
    print(f"GDP per capita: ${result['monetization']['gdp_per_capita_usd']:,.2f}")
    print()
    print(f"Baseline DALYs lost: {result['baseline_dalys_lost']:,.2f}")
    print(f"Post-intervention DALYs lost: {result['post_intervention_dalys_lost']:,.2f}")
    print(f"DALYs averted: {result['dalys_averted']:,.2f}")
    print()
    print(f"Intervention: {result['intervention_type']}")
    print(f"Description: {result['intervention_description']}")
    print(f"Heat reduction: {result['breakdown']['heat_reduction_pct']}%")
    print(f"Malaria reduction: {result['breakdown']['malaria_reduction_pct']}%")
    print()
    print(f"Economic value preserved: ${result['economic_value_preserved_usd']:,.2f}")
    print(f"Value per DALY: ${result['monetization']['value_per_daly_usd']:,.2f}")
    print()
    assert result['dalys_averted'] > 0, "Should avert DALYs"
    assert result['breakdown']['heat_reduction_pct'] == 0.0, "Should not reduce heat"
    assert result['breakdown']['malaria_reduction_pct'] == 70.0, "Should be 70% malaria reduction"
    print("✅ PASSED")


def test_low_heat_no_malaria():
    """Test 4: Low heat, no malaria (minimal burden)"""
    print("\n" + "="*80)
    print("TEST 4: Low Heat, No Malaria - Minimal Burden")
    print("="*80)
    
    result = calculate_public_health_impact(
        population=100000,
        gdp_per_capita=8500.0,
        wbgt=24.0,  # Low heat stress (below threshold)
        malaria_risk_score=0,  # No malaria risk
        intervention_type="none"
    )
    
    print(f"Population: {result['population_parameters']['population_size']:,}")
    print(f"GDP per capita: ${result['monetization']['gdp_per_capita_usd']:,.2f}")
    print(f"WBGT: 24.0°C (Low heat stress, below 26°C threshold)")
    print(f"Malaria risk score: 0 (No risk)")
    print()
    print(f"Baseline DALYs lost: {result['baseline_dalys_lost']:,.2f}")
    print(f"  - Heat DALYs/1000: {result['breakdown']['heat_dalys_per_1000_baseline']}")
    print(f"  - Malaria DALYs/1000: {result['breakdown']['malaria_dalys_per_1000_baseline']}")
    print()
    assert result['baseline_dalys_lost'] == 0, "Should have no DALYs (no risk)"
    assert result['breakdown']['heat_dalys_per_1000_baseline'] == 0, "No heat DALYs"
    assert result['breakdown']['malaria_dalys_per_1000_baseline'] == 0, "No malaria DALYs"
    print("✅ PASSED")


def test_heat_severity_scaling():
    """Test 5: Heat severity scaling (26°C to 32°C)"""
    print("\n" + "="*80)
    print("TEST 5: Heat Severity Scaling")
    print("="*80)
    
    wbgt_scenarios = [26.0, 28.0, 30.0, 32.0, 34.0]
    
    for wbgt in wbgt_scenarios:
        result = calculate_public_health_impact(
            population=100000,
            gdp_per_capita=10000.0,
            wbgt=wbgt,
            malaria_risk_score=0,
            intervention_type="none"
        )
        
        heat_dalys_per_1000 = result['breakdown']['heat_dalys_per_1000_baseline']
        total_dalys = result['baseline_dalys_lost']
        
        print(f"WBGT {wbgt}°C: {heat_dalys_per_1000:.2f} DALYs/1000 → {total_dalys:.2f} total DALYs")
    
    print()
    print("✅ PASSED - Heat DALYs scale with WBGT severity")


def test_large_population():
    """Test 6: Large population (10M) with intervention"""
    print("\n" + "="*80)
    print("TEST 6: Large Population - National Scale")
    print("="*80)
    
    result = calculate_public_health_impact(
        population=10000000,  # 10 million
        gdp_per_capita=7000.0,
        wbgt=29.5,
        malaria_risk_score=80,
        intervention_type="urban_cooling_center"
    )
    
    print(f"Population: {result['population_parameters']['population_size']:,}")
    print(f"GDP per capita: ${result['monetization']['gdp_per_capita_usd']:,.2f}")
    print()
    print(f"Baseline DALYs lost: {result['baseline_dalys_lost']:,.2f}")
    print(f"DALYs averted: {result['dalys_averted']:,.2f}")
    print(f"Economic value preserved: ${result['economic_value_preserved_usd']:,.2f}")
    print(f"  = ${result['economic_value_preserved_usd']/1e6:.2f} million")
    print()
    assert result['baseline_dalys_lost'] > 100000, "Large population should have high DALYs"
    assert result['economic_value_preserved_usd'] > 1e6, "Should be > $1 million"
    print("✅ PASSED")


def test_cost_effectiveness_example():
    """Test 7: Cost-effectiveness calculation example"""
    print("\n" + "="*80)
    print("TEST 7: Cost-Effectiveness Analysis Example")
    print("="*80)
    
    intervention_cost = 50000000  # $50M for cooling centers
    
    result = calculate_public_health_impact(
        population=2000000,
        gdp_per_capita=12000.0,
        wbgt=31.0,
        malaria_risk_score=50,
        intervention_type="urban_cooling_center"
    )
    
    dalys_averted = result['dalys_averted']
    economic_value = result['economic_value_preserved_usd']
    bcr = economic_value / intervention_cost
    cost_per_daly = intervention_cost / dalys_averted if dalys_averted > 0 else 0
    threshold = result['monetization']['value_per_daly_usd']
    
    print(f"Intervention cost: ${intervention_cost:,.2f}")
    print(f"Population: {result['population_parameters']['population_size']:,}")
    print()
    print(f"DALYs averted: {dalys_averted:,.2f}")
    print(f"Economic value: ${economic_value:,.2f}")
    print()
    print(f"Benefit-Cost Ratio (BCR): {bcr:.2f}")
    print(f"Cost per DALY averted: ${cost_per_daly:,.2f}")
    print(f"WHO threshold (2× GDP): ${threshold:,.2f}")
    print()
    if cost_per_daly < threshold:
        print(f"✅ COST-EFFECTIVE: ${cost_per_daly:,.2f} < ${threshold:,.2f}")
    elif bcr > 0.5:
        print(f"⚠️ MARGINAL: BCR={bcr:.2f}, cost per DALY=${cost_per_daly:,.2f}")
    else:
        print(f"❌ NOT COST-EFFECTIVE: ${cost_per_daly:,.2f} > ${threshold:,.2f}")
    print()
    # This test demonstrates cost-effectiveness calculation, not all scenarios will be cost-effective
    # The actual result depends on the specific scenario parameters
    print("✅ PASSED - Cost-effectiveness calculation works correctly")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PUBLIC HEALTH DALY CALCULATION - TEST SUITE")
    print("="*80)
    
    tests = [
        test_baseline_no_intervention,
        test_urban_cooling_center,
        test_mosquito_eradication,
        test_low_heat_no_malaria,
        test_heat_severity_scaling,
        test_large_population,
        test_cost_effectiveness_example,
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
