#!/usr/bin/env python3
"""
Test suite for Coastal and Flood Module NLG
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlg_engine import generate_deterministic_summary

def test_coastal_with_intervention():
    """Test coastal summary with defense infrastructure investment"""
    print("\n" + "="*80)
    print("TEST: Coastal with Defense Infrastructure")
    print("="*80)
    
    data = {
        'intervention_capex': 5000000,
        'avoided_damage_usd': 25000000
    }
    
    summary = generate_deterministic_summary(
        module_name='coastal',
        location_name='Miami Beach',
        data=data
    )
    
    print(f"Location: Miami Beach")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: ${data['intervention_capex']:,}")
    print(f"  - Avoided Damage: ${data['avoided_damage_usd']:,}")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Miami Beach" in summary, "Should mention location"
    assert "sea-level rise" in summary or "coastal inundation" in summary, "Should mention coastal hazards"
    assert "$5.0 million" in summary, "Should mention CAPEX"
    assert "$25.0 million" in summary, "Should mention avoided damage"
    assert "avoided structural damage" in summary, "Should mention avoided damage"
    
    print("\n✅ PASSED")


def test_coastal_nested_data():
    """Test coastal summary with nested data structure"""
    print("\n" + "="*80)
    print("TEST: Coastal with Nested Data Structure")
    print("="*80)
    
    data = {
        'data': {
            'capex': 2500000,
            'avoided_loss': 15000000
        }
    }
    
    summary = generate_deterministic_summary(
        module_name='coastal',
        location_name='Charleston',
        data=data
    )
    
    print(f"Location: Charleston")
    print(f"\nExtracted Data (nested):")
    print(f"  - CAPEX: ${data['data']['capex']:,}")
    print(f"  - Avoided Loss: ${data['data']['avoided_loss']:,}")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Charleston" in summary, "Should mention location"
    assert "$2.5 million" in summary, "Should extract CAPEX from nested data"
    assert "$15.0 million" in summary, "Should extract avoided loss from nested data"
    
    print("\n✅ PASSED - Nested data extraction worked!")


def test_coastal_nested_analysis():
    """Test coastal summary with data nested in analysis dict (like flood module)"""
    print("\n" + "="*80)
    print("TEST: Coastal with Analysis Dict (Deep Nested)")
    print("="*80)
    
    data = {
        'analysis': {
            'avoided_loss': 20000000,
            'intervention_capex': 4000000
        }
    }
    
    summary = generate_deterministic_summary(
        module_name='coastal',
        location_name='New York Harbor',
        data=data
    )
    
    print(f"Location: New York Harbor")
    print(f"\nExtracted Data (nested in analysis):")
    print(f"  - CAPEX: ${data['analysis']['intervention_capex']:,}")
    print(f"  - Avoided Loss: ${data['analysis']['avoided_loss']:,}")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "New York Harbor" in summary, "Should mention location"
    assert "$4.0 million" in summary, "Should extract CAPEX from analysis dict"
    assert "$20.0 million" in summary, "Should extract avoided loss from analysis dict"
    assert "avoided structural damage" in summary, "Should show intervention sentence"
    
    print("\n✅ PASSED - Deep nested analysis extraction worked!")


def test_coastal_null_capex():
    """Test coastal summary with null/None CAPEX but valid avoided_loss"""
    print("\n" + "="*80)
    print("TEST: Coastal with Null CAPEX (Avoided Loss Valid)")
    print("="*80)
    
    data = {
        'analysis': {
            'avoided_loss': 30000000
        },
        'intervention_capex': None  # This should NOT crash or reset avoided_loss to 0
    }
    
    summary = generate_deterministic_summary(
        module_name='coastal',
        location_name='San Francisco Bay',
        data=data
    )
    
    print(f"Location: San Francisco Bay")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: {data['intervention_capex']} (None/null)")
    print(f"  - Avoided Loss: ${data['analysis']['avoided_loss']:,}")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "San Francisco Bay" in summary, "Should mention location"
    assert "$30.0 million" in summary, "Should extract avoided loss despite null CAPEX"
    assert "avoided structural damage" in summary, "Should show intervention sentence"
    # Should NOT mention CAPEX amount since it's null
    assert "safeguards long-term asset value" in summary, "Should show alternative sentence"
    
    print("\n✅ PASSED - Null CAPEX didn't crash or reset avoided_loss!")


def test_coastal_no_intervention():
    """Test coastal summary when no intervention is modeled"""
    print("\n" + "="*80)
    print("TEST: Coastal Baseline (No Intervention)")
    print("="*80)
    
    data = {
        'intervention_capex': 0,
        'avoided_damage_usd': 0
    }
    
    summary = generate_deterministic_summary(
        module_name='coastal',
        location_name='Norfolk',
        data=data
    )
    
    print(f"Location: Norfolk")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: ${data['intervention_capex']}")
    print(f"  - Avoided Damage: ${data['avoided_damage_usd']}")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Norfolk" in summary, "Should mention location"
    assert "highly vulnerable" in summary or "storm surges" in summary, "Should mention vulnerability"
    assert "dashboard" in summary, "Should guide user to dashboard"
    
    print("\n✅ PASSED")


def test_flood_with_intervention():
    """Test flood summary with mitigation assets investment"""
    print("\n" + "="*80)
    print("TEST: Flood with Mitigation Assets")
    print("="*80)
    
    data = {
        'intervention_capex': 3000000,
        'analysis': {
            'avoided_loss': 18000000
        }
    }
    
    summary = generate_deterministic_summary(
        module_name='flood',
        location_name='Houston',
        data=data
    )
    
    print(f"Location: Houston")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: ${data['intervention_capex']:,}")
    print(f"  - Avoided Loss (nested in analysis): ${data['analysis']['avoided_loss']:,}")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Houston" in summary, "Should mention location"
    assert "extreme precipitation" in summary or "localized flooding" in summary, "Should mention flood hazards"
    assert "$3.0 million" in summary, "Should mention CAPEX"
    assert "$18.0 million" in summary, "Should extract avoided loss from analysis dict"
    assert "avoided economic disruption" in summary, "Should mention avoided disruption"
    
    print("\n✅ PASSED - Nested analysis extraction worked!")


def test_flood_root_level_avoided_loss():
    """Test flood summary with avoided_loss at root level (not in analysis)"""
    print("\n" + "="*80)
    print("TEST: Flood with Root-Level Avoided Loss")
    print("="*80)
    
    data = {
        'intervention_capex': 1500000,
        'avoided_loss': 8000000
    }
    
    summary = generate_deterministic_summary(
        module_name='flood',
        location_name='New Orleans',
        data=data
    )
    
    print(f"Location: New Orleans")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: ${data['intervention_capex']:,}")
    print(f"  - Avoided Loss (root): ${data['avoided_loss']:,}")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "New Orleans" in summary, "Should mention location"
    assert "$1.5 million" in summary, "Should mention CAPEX"
    assert "$8.0 million" in summary, "Should extract avoided loss from root"
    
    print("\n✅ PASSED - Root-level extraction worked!")


def test_flood_no_intervention():
    """Test flood summary when no mitigation is modeled"""
    print("\n" + "="*80)
    print("TEST: Flood Baseline (No Intervention)")
    print("="*80)
    
    data = {
        'intervention_capex': 0,
        'analysis': {
            'avoided_loss': 0
        }
    }
    
    summary = generate_deterministic_summary(
        module_name='flood',
        location_name='Phoenix',
        data=data
    )
    
    print(f"Location: Phoenix")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: ${data['intervention_capex']}")
    print(f"  - Avoided Loss: ${data['analysis']['avoided_loss']}")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Phoenix" in summary, "Should mention location"
    assert "operational downtime" in summary or "stormwater management" in summary, "Should mention risks"
    assert "dashboard" in summary or "ROI" in summary, "Should guide user to dashboard"
    
    print("\n✅ PASSED")


def test_flood_type_casting():
    """Test flood module handles string numbers in nested structure"""
    print("\n" + "="*80)
    print("TEST: Flood Type Casting with Nested Strings")
    print("="*80)
    
    # Simulate frontend passing strings in nested structure
    data = {
        'data': {
            'capex': "2000000",
            'analysis': {
                'avoided_loss': "12000000"
            }
        }
    }
    
    summary = generate_deterministic_summary(
        module_name='flood',
        location_name='Austin',
        data=data
    )
    
    print(f"Location: Austin")
    print(f"\nExtracted Data (nested strings):")
    print(f"  - CAPEX: '{data['data']['capex']}' (type: {type(data['data']['capex'])})")
    print(f"  - Avoided Loss: '{data['data']['analysis']['avoided_loss']}' (type: {type(data['data']['analysis']['avoided_loss'])})")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions - should still work despite string inputs
    assert "Austin" in summary, "Should mention location"
    assert "$2.0 million" in summary, "Should parse CAPEX correctly"
    assert "$12.0 million" in summary, "Should parse avoided loss correctly"
    
    print("\n✅ PASSED - Complex nested type casting worked!")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("COASTAL AND FLOOD MODULE NLG - TEST SUITE")
    print("="*80)
    
    # Coastal tests
    test_coastal_with_intervention()
    test_coastal_nested_data()
    test_coastal_nested_analysis()
    test_coastal_null_capex()
    test_coastal_no_intervention()
    
    # Flood tests
    test_flood_with_intervention()
    test_flood_root_level_avoided_loss()
    test_flood_no_intervention()
    test_flood_type_casting()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("Passed: 9/9")
    print("Failed: 0/9")
    print("\n✅ ALL COASTAL AND FLOOD TESTS PASSED\n")
