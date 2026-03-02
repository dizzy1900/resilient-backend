#!/usr/bin/env python3
"""
Test suite for Hospital Expansion NLG (Municipal Bond Narrative)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlg_engine import generate_deterministic_summary

def test_hospital_expansion_with_deficit():
    """Test hospital expansion narrative with bed deficit"""
    print("\n" + "="*80)
    print("TEST: Hospital Expansion with Bed Deficit (Municipal Bond Narrative)")
    print("="*80)
    
    data = {
        'public_health_analysis': {
            'dalys_averted': 3360.0,
            'economic_value_preserved_usd': 57120000.0,
            'intervention_type': 'hospital_expansion'
        },
        'infrastructure_stress_test': {
            'bed_deficit': 700.0,
            'infrastructure_bond_capex': 175000000.0,
            'applied_tier': 'middle'
        }
    }
    
    summary = generate_deterministic_summary(
        module_name='health_public',
        location_name='Bangkok Metropolitan Region',
        data=data
    )
    
    print(f"Location: Bangkok Metropolitan Region")
    print(f"\nExtracted Data:")
    print(f"  - DALYs averted: {data['public_health_analysis']['dalys_averted']:,.1f}")
    print(f"  - Economic value: ${data['public_health_analysis']['economic_value_preserved_usd']:,.2f}")
    print(f"  - Intervention: {data['public_health_analysis']['intervention_type']}")
    print(f"  - Bed deficit: {data['infrastructure_stress_test']['bed_deficit']:,.0f}")
    print(f"  - Bond CAPEX: ${data['infrastructure_stress_test']['infrastructure_bond_capex']:,.2f}")
    print(f"  - Applied tier: {data['infrastructure_stress_test']['applied_tier']}")
    
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Bangkok Metropolitan Region" in summary, "Should mention location"
    assert "Municipal Hospital Expansion" in summary or "hospital" in summary.lower(), "Should mention hospital expansion"
    assert "Middle-Income" in summary or "middle" in summary.lower(), "Should mention economic tier"
    assert "700" in summary, "Should mention bed deficit"
    assert "$175.0 million" in summary, "Should mention bond amount"
    assert "3360.0" in summary or "3,360" in summary, "Should mention DALYs averted"
    assert "$57.1 million" in summary, "Should mention economic value"
    assert "triage capacity breach" in summary or "triage" in summary.lower(), "Should mention triage capacity"
    
    print("\n✅ PASSED - Municipal bond narrative generated correctly!")


def test_hospital_expansion_no_deficit():
    """Test hospital expansion narrative with no bed deficit (sufficient capacity)"""
    print("\n" + "="*80)
    print("TEST: Hospital Expansion with No Bed Deficit (Sufficient Capacity)")
    print("="*80)
    
    data = {
        'public_health_analysis': {
            'dalys_averted': 0.0,
            'economic_value_preserved_usd': 0.0,
            'intervention_type': 'hospital_expansion'
        },
        'infrastructure_stress_test': {
            'bed_deficit': 0.0,
            'infrastructure_bond_capex': 0.0,
            'applied_tier': 'high'
        }
    }
    
    summary = generate_deterministic_summary(
        module_name='health_public',
        location_name='Tokyo',
        data=data
    )
    
    print(f"Location: Tokyo")
    print(f"\nExtracted Data:")
    print(f"  - DALYs averted: {data['public_health_analysis']['dalys_averted']}")
    print(f"  - Bed deficit: {data['infrastructure_stress_test']['bed_deficit']}")
    print(f"  - Bond CAPEX: ${data['infrastructure_stress_test']['infrastructure_bond_capex']}")
    
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Tokyo" in summary, "Should mention location"
    assert "Climate health risks require assessment" in summary or "assessment" in summary.lower(), "Should show fallback for no intervention"
    
    print("\n✅ PASSED - No deficit scenario handled correctly!")


def test_hospital_expansion_nested_structure():
    """Test hospital expansion with deeply nested data structure"""
    print("\n" + "="*80)
    print("TEST: Hospital Expansion with Deeply Nested Data")
    print("="*80)
    
    # Simulate complex nested structure from API
    data = {
        'data': {
            'public_health_analysis': {
                'dalys_averted': 467.0,
                'economic_value_preserved_usd': 2804400.0,
                'intervention_type': 'hospital_expansion'
            },
            'infrastructure_stress_test': {
                'bed_deficit': 57.0,
                'infrastructure_bond_capex': 3420000.0,
                'applied_tier': 'low'
            }
        }
    }
    
    summary = generate_deterministic_summary(
        module_name='health_public',
        location_name='Sub-Saharan Regional Hospital',
        data=data
    )
    
    print(f"Location: Sub-Saharan Regional Hospital")
    print(f"\nExtracted Data (deeply nested):")
    print(f"  - DALYs averted: {data['data']['public_health_analysis']['dalys_averted']:,.1f}")
    print(f"  - Bed deficit: {data['data']['infrastructure_stress_test']['bed_deficit']:,.0f}")
    print(f"  - Bond CAPEX: ${data['data']['infrastructure_stress_test']['infrastructure_bond_capex']:,.2f}")
    print(f"  - Applied tier: {data['data']['infrastructure_stress_test']['applied_tier']}")
    
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions - deep_find should locate the data
    assert "Sub-Saharan Regional Hospital" in summary, "Should mention location"
    assert "Low-Income" in summary or "low" in summary.lower(), "Should extract tier from nested data"
    assert "57" in summary, "Should extract bed deficit from nested data"
    assert "$3.4 million" in summary, "Should extract bond amount from nested data"
    assert "467.0" in summary, "Should extract DALYs from nested data"
    
    print("\n✅ PASSED - Deep_find extracted nested hospital expansion data!")


def test_non_hospital_interventions_still_work():
    """Test that existing interventions (cooling centers, mosquito) still work"""
    print("\n" + "="*80)
    print("TEST: Non-Hospital Interventions (Backward Compatibility)")
    print("="*80)
    
    # Test 1: Urban Cooling Centers
    data1 = {
        'public_health_analysis': {
            'dalys_averted': 145.6,
            'economic_value_preserved_usd': 3494400.0,
            'intervention_type': 'urban_cooling_center'
        }
    }
    
    summary1 = generate_deterministic_summary(
        module_name='health_public',
        location_name='Phoenix',
        data=data1
    )
    
    print(f"Test 1: Urban Cooling Centers")
    print(f"Summary: {summary1}")
    assert "Urban Cooling Centers" in summary1, "Should mention cooling centers"
    assert "145.6" in summary1, "Should mention DALYs"
    print("✅ Cooling centers work")
    
    # Test 2: Mosquito Eradication
    data2 = {
        'public_health_analysis': {
            'dalys_averted': 36750.0,
            'economic_value_preserved_usd': 147000000.0,
            'intervention_type': 'mosquito_eradication'
        }
    }
    
    summary2 = generate_deterministic_summary(
        module_name='health_public',
        location_name='Lagos',
        data=data2
    )
    
    print(f"\nTest 2: Mosquito Eradication")
    print(f"Summary: {summary2}")
    assert "Mosquito Eradication" in summary2, "Should mention mosquito eradication"
    assert "36750.0" in summary2, "Should mention DALYs"
    print("✅ Mosquito eradication works")
    
    print("\n✅ PASSED - Existing interventions backward compatible!")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("HOSPITAL EXPANSION NLG - TEST SUITE")
    print("="*80)
    
    test_hospital_expansion_with_deficit()
    test_hospital_expansion_no_deficit()
    test_hospital_expansion_nested_structure()
    test_non_hospital_interventions_still_work()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("Passed: 4/4")
    print("Failed: 0/4")
    print("\n✅ ALL HOSPITAL EXPANSION NLG TESTS PASSED\n")
