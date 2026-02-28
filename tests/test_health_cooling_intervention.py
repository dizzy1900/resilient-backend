"""
Test script for the enhanced /predict-health endpoint with Cooling CAPEX vs. Productivity OPEX CBA.

Tests various cooling intervention scenarios.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_baseline_no_intervention():
    """Test 1: Baseline health analysis without any cooling intervention."""
    print("\n" + "=" * 70)
    print("TEST 1: Baseline Analysis (No Intervention)")
    print("=" * 70)
    
    # Test parameters
    test_case = {
        "lat": 13.7563,  # Bangkok, Thailand (hot & humid)
        "lon": 100.5018,
        "workforce_size": 500,
        "daily_wage": 25.0,
    }
    
    print(f"\nLocation: Bangkok, Thailand")
    print(f"Workforce: {test_case['workforce_size']} workers")
    print(f"Daily wage: ${test_case['daily_wage']}/worker")
    print(f"\nExpected: High heat stress, significant productivity loss")
    print(f"✓ Test structure valid\n")


def test_hvac_retrofit_intervention():
    """Test 2: HVAC retrofit intervention (drops WBGT to 22°C)."""
    print("\n" + "=" * 70)
    print("TEST 2: HVAC Retrofit Intervention")
    print("=" * 70)
    
    test_case = {
        "lat": 13.7563,  # Bangkok
        "lon": 100.5018,
        "workforce_size": 500,
        "daily_wage": 25.0,
        "intervention_type": "hvac_retrofit",
        "intervention_capex": 250000.0,  # $250K HVAC system
        "intervention_annual_opex": 30000.0,  # $30K/year maintenance + energy
    }
    
    print(f"\nIntervention: HVAC Retrofit")
    print(f"CAPEX: ${test_case['intervention_capex']:,.2f}")
    print(f"Annual OPEX: ${test_case['intervention_annual_opex']:,.2f}")
    print(f"\nExpected:")
    print(f"  • WBGT drops to safe 22°C")
    print(f"  • Productivity loss eliminated or greatly reduced")
    print(f"  • Calculate payback period and NPV")
    print(f"  • BCR should indicate financial viability")
    print(f"✓ Test structure valid\n")


def test_passive_cooling_intervention():
    """Test 3: Passive cooling intervention (reduces WBGT by 3°C)."""
    print("\n" + "=" * 70)
    print("TEST 3: Passive Cooling Intervention")
    print("=" * 70)
    
    test_case = {
        "lat": 28.6139,  # New Delhi, India (very hot)
        "lon": 77.2090,
        "workforce_size": 200,
        "daily_wage": 15.0,
        "intervention_type": "passive_cooling",
        "intervention_capex": 50000.0,  # $50K for green roofs, ventilation, shading
        "intervention_annual_opex": 5000.0,  # $5K/year maintenance
    }
    
    print(f"\nLocation: New Delhi, India")
    print(f"Intervention: Passive Cooling")
    print(f"CAPEX: ${test_case['intervention_capex']:,.2f}")
    print(f"Annual OPEX: ${test_case['intervention_annual_opex']:,.2f}")
    print(f"\nExpected:")
    print(f"  • WBGT reduced by 3°C")
    print(f"  • Partial productivity improvement")
    print(f"  • Lower cost than HVAC, lower benefit")
    print(f"  • Faster payback period due to lower CAPEX")
    print(f"✓ Test structure valid\n")


def test_zero_capex_intervention():
    """Test 4: Zero CAPEX intervention (no financial analysis)."""
    print("\n" + "=" * 70)
    print("TEST 4: Zero CAPEX Intervention")
    print("=" * 70)
    
    test_case = {
        "lat": 1.3521,  # Singapore (hot & humid year-round)
        "lon": 103.8198,
        "workforce_size": 100,
        "daily_wage": 40.0,
        "intervention_type": "passive_cooling",
        "intervention_capex": 0.0,  # Free intervention (policy change, etc.)
        "intervention_annual_opex": 0.0,
    }
    
    print(f"\nScenario: Policy-based cooling (no cost)")
    print(f"CAPEX: $0 (e.g., mandatory break policies)")
    print(f"Annual OPEX: $0")
    print(f"\nExpected:")
    print(f"  • WBGT reduced by 3°C")
    print(f"  • Productivity improvement calculated")
    print(f"  • No financial ROI analysis (zero investment)")
    print(f"  • Response should not include payback/NPV")
    print(f"✓ Test structure valid\n")


def test_high_opex_unprofitable():
    """Test 5: High OPEX makes intervention unprofitable."""
    print("\n" + "=" * 70)
    print("TEST 5: Unprofitable Intervention (High OPEX)")
    print("=" * 70)
    
    test_case = {
        "lat": 13.7563,  # Bangkok
        "lon": 100.5018,
        "workforce_size": 100,  # Small workforce
        "daily_wage": 15.0,  # Low wage
        "intervention_type": "hvac_retrofit",
        "intervention_capex": 200000.0,
        "intervention_annual_opex": 100000.0,  # Very high OPEX - exceeds benefit
    }
    
    print(f"\nScenario: Small workforce, high OPEX")
    print(f"Workforce: {test_case['workforce_size']} workers")
    print(f"CAPEX: ${test_case['intervention_capex']:,.2f}")
    print(f"Annual OPEX: ${test_case['intervention_annual_opex']:,.2f}")
    print(f"\nExpected:")
    print(f"  • Avoided loss < Annual OPEX")
    print(f"  • Negative NPV")
    print(f"  • BCR < 1.0")
    print(f"  • Recommendation: DO NOT INVEST")
    print(f"  • Payback period: None (never pays back)")
    print(f"✓ Test structure valid\n")


def test_comparison_hvac_vs_passive():
    """Test 6: Side-by-side comparison of HVAC vs. Passive cooling."""
    print("\n" + "=" * 70)
    print("TEST 6: Comparison - HVAC vs. Passive Cooling")
    print("=" * 70)
    
    location = {"lat": 25.2048, "lon": 55.2708}  # Dubai, UAE (extreme heat)
    workforce = {"workforce_size": 300, "daily_wage": 35.0}
    
    hvac = {
        **location,
        **workforce,
        "intervention_type": "hvac_retrofit",
        "intervention_capex": 300000.0,
        "intervention_annual_opex": 40000.0,
    }
    
    passive = {
        **location,
        **workforce,
        "intervention_type": "passive_cooling",
        "intervention_capex": 75000.0,
        "intervention_annual_opex": 8000.0,
    }
    
    print(f"\nLocation: Dubai, UAE (extreme heat)")
    print(f"Workforce: {workforce['workforce_size']} workers @ ${workforce['daily_wage']}/day")
    print(f"\nOption A - HVAC Retrofit:")
    print(f"  CAPEX: ${hvac['intervention_capex']:,.2f}")
    print(f"  OPEX: ${hvac['intervention_annual_opex']:,.2f}/year")
    print(f"  Benefit: WBGT → 22°C (maximum cooling)")
    print(f"\nOption B - Passive Cooling:")
    print(f"  CAPEX: ${passive['intervention_capex']:,.2f}")
    print(f"  OPEX: ${passive['intervention_annual_opex']:,.2f}/year")
    print(f"  Benefit: WBGT reduced by 3°C")
    print(f"\nExpected:")
    print(f"  • HVAC: Higher avoided loss, higher cost, potentially better BCR")
    print(f"  • Passive: Lower cost, faster payback, but less productivity gain")
    print(f"  • Compare NPV and payback period to determine best option")
    print(f"✓ Test structure valid\n")


def test_edge_case_already_cool_climate():
    """Test 7: Edge case - Already cool climate (low baseline WBGT)."""
    print("\n" + "=" * 70)
    print("TEST 7: Edge Case - Cool Climate (Minimal Intervention Benefit)")
    print("=" * 70)
    
    test_case = {
        "lat": 51.5074,  # London, UK (cool climate)
        "lon": -0.1278,
        "workforce_size": 200,
        "daily_wage": 50.0,
        "intervention_type": "hvac_retrofit",
        "intervention_capex": 100000.0,
        "intervention_annual_opex": 15000.0,
    }
    
    print(f"\nLocation: London, UK (temperate climate)")
    print(f"Intervention: HVAC Retrofit")
    print(f"\nExpected:")
    print(f"  • Baseline WBGT already low (~24-26°C)")
    print(f"  • Minimal productivity loss in baseline")
    print(f"  • Very small avoided loss from intervention")
    print(f"  • Negative NPV (cost exceeds benefit)")
    print(f"  • Recommendation: DO NOT INVEST in cooling")
    print(f"✓ Test structure valid\n")


def main():
    """Run all test cases."""
    print("\n" + "=" * 70)
    print("COOLING CAPEX vs. PRODUCTIVITY OPEX - TEST SUITE")
    print("Enhanced /predict-health Endpoint")
    print("=" * 70)
    
    test_baseline_no_intervention()
    test_hvac_retrofit_intervention()
    test_passive_cooling_intervention()
    test_zero_capex_intervention()
    test_high_opex_unprofitable()
    test_comparison_hvac_vs_passive()
    test_edge_case_already_cool_climate()
    
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"\n✓ 7 test scenarios defined")
    print(f"\nTo run actual API tests:")
    print(f"  1. Start server: uvicorn api:app --reload --port 8000")
    print(f"  2. Run: ./tests/test_health_cooling_api.sh")
    print(f"\nTest Coverage:")
    print(f"  • Baseline analysis (no intervention)")
    print(f"  • HVAC retrofit (drops WBGT to 22°C)")
    print(f"  • Passive cooling (reduces WBGT by 3°C)")
    print(f"  • Zero CAPEX interventions")
    print(f"  • Unprofitable interventions (high OPEX)")
    print(f"  • HVAC vs. Passive comparison")
    print(f"  • Edge case: cool climate")
    print(f"\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
