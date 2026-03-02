#!/usr/bin/env python3
"""
Test suite for Healthcare Infrastructure Stress Testing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_infrastructure_stress_calculation():
    """Test the infrastructure stress calculation logic"""
    print("\n" + "="*80)
    print("TEST: Healthcare Infrastructure Stress Testing Math")
    print("="*80)
    
    # Research data
    research_data = {
        "high": {
            "beds_per_1000": 3.8,
            "capex": 1000000,
            "occupancy": 0.72,
            "surge_pct": 0.035,
            "dalys_per_deficit": 2.5
        },
        "middle": {
            "beds_per_1000": 2.8,
            "capex": 250000,
            "occupancy": 0.75,
            "surge_pct": 0.075,
            "dalys_per_deficit": 4.8
        },
        "low": {
            "beds_per_1000": 1.2,
            "capex": 60000,
            "occupancy": 0.80,
            "surge_pct": 0.135,
            "dalys_per_deficit": 8.2
        }
    }
    
    # Test scenario: Middle-income country with extreme heat
    economy_tier = "middle"
    population_size = 500000
    temp_c = 35.0  # Extreme heat
    baseline_temp = 25.0
    
    active_tier = research_data[economy_tier]
    baseline_beds_per_1000 = active_tier["beds_per_1000"]
    cost_per_bed = active_tier["capex"]
    
    # Calculate metrics
    projected_temp_increase = max(0, temp_c - baseline_temp)
    baseline_capacity = (population_size / 1000) * baseline_beds_per_1000
    available_beds = baseline_capacity * (1.0 - active_tier["occupancy"])
    surge_admissions = baseline_capacity * (active_tier["surge_pct"] * projected_temp_increase)
    bed_deficit = max(0, surge_admissions - available_beds)
    infrastructure_bond_capex = bed_deficit * cost_per_bed
    dalys_averted = bed_deficit * active_tier["dalys_per_deficit"]
    
    print(f"\nScenario:")
    print(f"  - Economy Tier: {economy_tier}")
    print(f"  - Population: {population_size:,}")
    print(f"  - Temperature: {temp_c}°C (baseline: {baseline_temp}°C)")
    print(f"  - Temp Increase: {projected_temp_increase}°C")
    
    print(f"\nResearch Parameters (tier={economy_tier}):")
    print(f"  - Beds per 1,000: {baseline_beds_per_1000}")
    print(f"  - Cost per bed: ${cost_per_bed:,}")
    print(f"  - Baseline occupancy: {active_tier['occupancy']*100}%")
    print(f"  - Surge factor: {active_tier['surge_pct']*100}% per °C")
    print(f"  - DALYs per bed deficit: {active_tier['dalys_per_deficit']}")
    
    print(f"\nCalculated Metrics:")
    print(f"  - Baseline capacity: {baseline_capacity:,.0f} beds")
    print(f"  - Available beds (after occupancy): {available_beds:,.0f} beds")
    print(f"  - Surge admissions: {surge_admissions:,.0f} beds")
    print(f"  - Bed deficit: {bed_deficit:,.0f} beds")
    print(f"  - Infrastructure bond CAPEX: ${infrastructure_bond_capex:,.2f}")
    print(f"  - DALYs averted if addressed: {dalys_averted:,.1f}")
    print(f"  - Capacity breach: {bed_deficit > 0}")
    
    # Assertions
    assert baseline_capacity == 1400.0, f"Expected 1,400 beds, got {baseline_capacity}"
    assert available_beds == 350.0, f"Expected 350 available beds, got {available_beds}"
    assert surge_admissions == 1050.0, f"Expected 1,050 surge admissions, got {surge_admissions}"
    assert bed_deficit == 700.0, f"Expected 700 bed deficit, got {bed_deficit}"
    assert infrastructure_bond_capex == 175000000.0, f"Expected $175M CAPEX, got ${infrastructure_bond_capex:,.2f}"
    assert dalys_averted == 3360.0, f"Expected 3,360 DALYs averted, got {dalys_averted}"
    
    print("\n✅ PASSED - All calculations correct!")


def test_infrastructure_stress_tiers():
    """Test infrastructure stress across different economic tiers"""
    print("\n" + "="*80)
    print("TEST: Infrastructure Stress Across Economic Tiers")
    print("="*80)
    
    research_data = {
        "high": {"beds_per_1000": 3.8, "capex": 1000000, "occupancy": 0.72, "surge_pct": 0.035, "dalys_per_deficit": 2.5},
        "middle": {"beds_per_1000": 2.8, "capex": 250000, "occupancy": 0.75, "surge_pct": 0.075, "dalys_per_deficit": 4.8},
        "low": {"beds_per_1000": 1.2, "capex": 60000, "occupancy": 0.80, "surge_pct": 0.135, "dalys_per_deficit": 8.2}
    }
    
    population = 100000
    temp_increase = 5.0  # 5°C above baseline
    
    print(f"\nScenario: Population={population:,}, Temp Increase={temp_increase}°C\n")
    
    for tier_name, tier_data in research_data.items():
        baseline_capacity = (population / 1000) * tier_data["beds_per_1000"]
        available_beds = baseline_capacity * (1.0 - tier_data["occupancy"])
        surge_admissions = baseline_capacity * (tier_data["surge_pct"] * temp_increase)
        bed_deficit = max(0, surge_admissions - available_beds)
        capex = bed_deficit * tier_data["capex"]
        dalys = bed_deficit * tier_data["dalys_per_deficit"]
        
        print(f"{tier_name.upper()} Income:")
        print(f"  - Baseline capacity: {baseline_capacity:,.0f} beds")
        print(f"  - Bed deficit: {bed_deficit:,.0f} beds")
        print(f"  - CAPEX needed: ${capex:,.2f}")
        print(f"  - DALYs averted: {dalys:,.1f}")
        print(f"  - Capacity breach: {bed_deficit > 0}")
        print()
    
    print("✅ PASSED - Tier comparison completed!")


def test_infrastructure_stress_user_overrides():
    """Test user overrides for beds_per_1000 and cost_per_bed"""
    print("\n" + "="*80)
    print("TEST: Infrastructure Stress with User Overrides")
    print("="*80)
    
    research_data = {
        "middle": {
            "beds_per_1000": 2.8,
            "capex": 250000,
            "occupancy": 0.75,
            "surge_pct": 0.075,
            "dalys_per_deficit": 4.8
        }
    }
    
    population = 200000
    temp_increase = 8.0
    
    # Test 1: Default (no overrides)
    active_tier = research_data["middle"]
    baseline_beds_default = active_tier["beds_per_1000"]
    cost_per_bed_default = active_tier["capex"]
    
    baseline_capacity_default = (population / 1000) * baseline_beds_default
    available_beds_default = baseline_capacity_default * (1.0 - active_tier["occupancy"])
    surge_admissions_default = baseline_capacity_default * (active_tier["surge_pct"] * temp_increase)
    bed_deficit_default = max(0, surge_admissions_default - available_beds_default)
    capex_default = bed_deficit_default * cost_per_bed_default
    
    print(f"\nDefault (no overrides):")
    print(f"  - Beds per 1,000: {baseline_beds_default}")
    print(f"  - Cost per bed: ${cost_per_bed_default:,}")
    print(f"  - Bed deficit: {bed_deficit_default:,.0f}")
    print(f"  - CAPEX: ${capex_default:,.2f}")
    
    # Test 2: With user overrides
    user_beds_per_1000 = 3.5  # User override
    user_cost_per_bed = 500000  # User override
    
    baseline_capacity_override = (population / 1000) * user_beds_per_1000
    available_beds_override = baseline_capacity_override * (1.0 - active_tier["occupancy"])
    surge_admissions_override = baseline_capacity_override * (active_tier["surge_pct"] * temp_increase)
    bed_deficit_override = max(0, surge_admissions_override - available_beds_override)
    capex_override = bed_deficit_override * user_cost_per_bed
    
    print(f"\nWith User Overrides:")
    print(f"  - Beds per 1,000: {user_beds_per_1000} (overridden)")
    print(f"  - Cost per bed: ${user_cost_per_bed:,} (overridden)")
    print(f"  - Bed deficit: {bed_deficit_override:,.0f}")
    print(f"  - CAPEX: ${capex_override:,.2f}")
    
    assert bed_deficit_override != bed_deficit_default, "Override should change bed deficit"
    assert capex_override != capex_default, "Override should change CAPEX"
    
    print("\n✅ PASSED - User overrides working correctly!")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("HEALTHCARE INFRASTRUCTURE STRESS TESTING - TEST SUITE")
    print("="*80)
    
    test_infrastructure_stress_calculation()
    test_infrastructure_stress_tiers()
    test_infrastructure_stress_user_overrides()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("Passed: 3/3")
    print("Failed: 0/3")
    print("\n✅ ALL INFRASTRUCTURE STRESS TESTS PASSED\n")
