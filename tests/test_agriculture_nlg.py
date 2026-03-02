#!/usr/bin/env python3
"""
Test suite for Agriculture Module NLG
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlg_engine import generate_deterministic_summary

def test_agriculture_with_adaptation():
    """Test agriculture summary with crop adaptation investment"""
    print("\n" + "="*80)
    print("TEST: Agriculture with Crop Adaptation")
    print("="*80)
    
    data = {
        'transition_capex': 250000,
        'avoided_revenue_loss': 1500000,
        'risk_reduction_pct': 35.5
    }
    
    summary = generate_deterministic_summary(
        module_name='agriculture',
        location_name='Central Valley, California',
        data=data
    )
    
    print(f"Location: Central Valley, California")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: ${data['transition_capex']:,}")
    print(f"  - Avoided Loss: ${data['avoided_revenue_loss']:,}")
    print(f"  - Risk Reduction: {data['risk_reduction_pct']}%")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Central Valley, California" in summary, "Should mention location"
    assert "agricultural yield disruption" in summary, "Should mention agricultural disruption"
    assert "$250,000" in summary or "$0.2 million" in summary, "Should mention CAPEX"
    assert "35.5%" in summary, "Should mention risk reduction percentage"
    assert "$1.5 million" in summary, "Should mention avoided loss"
    assert "avoided revenue loss" in summary, "Should mention avoided revenue loss"
    
    print("\n✅ PASSED")


def test_agriculture_high_value():
    """Test agriculture summary with high-value adaptation (millions)"""
    print("\n" + "="*80)
    print("TEST: Agriculture High-Value Scenario")
    print("="*80)
    
    data = {
        'transition_capex': 3500000,
        'avoided_revenue_loss': 12000000,
        'risk_reduction_pct': 58.2
    }
    
    summary = generate_deterministic_summary(
        module_name='agriculture',
        location_name='Midwest Region',
        data=data
    )
    
    print(f"Location: Midwest Region")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: ${data['transition_capex']:,}")
    print(f"  - Avoided Loss: ${data['avoided_revenue_loss']:,}")
    print(f"  - Risk Reduction: {data['risk_reduction_pct']}%")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Midwest Region" in summary, "Should mention location"
    assert "$3.5 million" in summary, "Should format CAPEX in millions"
    assert "$12.0 million" in summary, "Should format avoided loss in millions"
    assert "58.2%" in summary, "Should mention risk reduction"
    
    print("\n✅ PASSED")


def test_agriculture_no_adaptation():
    """Test agriculture summary when no adaptation is modeled"""
    print("\n" + "="*80)
    print("TEST: Agriculture Baseline (No Adaptation)")
    print("="*80)
    
    data = {
        'transition_capex': 0,
        'avoided_revenue_loss': 0,
        'risk_reduction_pct': 0
    }
    
    summary = generate_deterministic_summary(
        module_name='agriculture',
        location_name='Great Plains',
        data=data
    )
    
    print(f"Location: Great Plains")
    print(f"\nExtracted Data:")
    print(f"  - CAPEX: ${data['transition_capex']}")
    print(f"  - Avoided Loss: ${data['avoided_revenue_loss']}")
    print(f"  - Risk Reduction: {data['risk_reduction_pct']}%")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions
    assert "Great Plains" in summary, "Should mention location"
    assert "agricultural yield disruption" in summary, "Should mention disruption"
    assert "highly vulnerable" in summary or "severe climate shocks" in summary, "Should mention vulnerability"
    assert "dashboard" in summary, "Should guide user to dashboard"
    
    print("\n✅ PASSED")


def test_agriculture_type_casting():
    """Test agriculture module handles string numbers correctly"""
    print("\n" + "="*80)
    print("TEST: Agriculture Type Casting Resilience")
    print("="*80)
    
    # Simulate frontend passing strings instead of floats
    data = {
        'transition_capex': "500000",
        'avoided_revenue_loss': "2500000",
        'risk_reduction_pct': "42.3"
    }
    
    summary = generate_deterministic_summary(
        module_name='agriculture',
        location_name='Iowa',
        data=data
    )
    
    print(f"Location: Iowa")
    print(f"\nExtracted Data (as strings):")
    print(f"  - CAPEX: '{data['transition_capex']}' (type: {type(data['transition_capex'])})")
    print(f"  - Avoided Loss: '{data['avoided_revenue_loss']}' (type: {type(data['avoided_revenue_loss'])})")
    print(f"  - Risk Reduction: '{data['risk_reduction_pct']}' (type: {type(data['risk_reduction_pct'])})")
    print(f"\nGenerated Summary:")
    print(summary)
    
    # Assertions - should still work despite string inputs
    assert "Iowa" in summary, "Should mention location"
    assert "$0.5 million" in summary or "$500,000" in summary, "Should parse CAPEX correctly"
    assert "$2.5 million" in summary, "Should parse avoided loss correctly"
    assert "42.3%" in summary, "Should parse risk reduction correctly"
    
    print("\n✅ PASSED - Type casting worked!")


if __name__ == '__main__':
    print("\n" + "="*80)
    print("AGRICULTURE MODULE NLG - TEST SUITE")
    print("="*80)
    
    test_agriculture_with_adaptation()
    test_agriculture_high_value()
    test_agriculture_no_adaptation()
    test_agriculture_type_casting()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print("Passed: 4/4")
    print("Failed: 0/4")
    print("\n✅ ALL AGRICULTURE TESTS PASSED\n")
