#!/usr/bin/env python3
"""
Test nested data extraction from /predict-health response
==========================================================

This test validates that the NLG engine correctly extracts data from the
actual nested structure returned by the /predict-health endpoint.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nlg_engine import generate_deterministic_summary


def test_health_public_nested_extraction():
    """Test extraction from actual /predict-health response structure."""
    print("\n" + "="*80)
    print("TEST: Health Public Nested Data Extraction")
    print("="*80)
    
    # Actual nested structure from /predict-health endpoint
    data = {
        "location": {
            "lat": 13.7563,
            "lon": 100.5018
        },
        "climate_conditions": {
            "temperature_c": 32.5,
            "precipitation_mm": 1450.0,
            "humidity_pct_estimated": 80.0
        },
        "heat_stress_analysis": {
            "wbgt_estimate": 30.8,
            "productivity_loss_pct": 40.0,
            "heat_stress_category": "Very High",
            "recommendation": "All work affected, frequent breaks required"
        },
        "malaria_risk_analysis": {
            "risk_score": 100,
            "risk_category": "High",
            "description": "Climate conditions highly suitable for malaria transmission"
        },
        "economic_impact": {
            "heat_stress_impact": {
                "annual_productivity_loss": 1250000.0
            }
        },
        "workforce_parameters": {
            "workforce_size": 500,
            "daily_wage": 25.0,
            "currency": "USD"
        },
        "public_health_analysis": {
            "baseline_dalys_lost": 26614.0,
            "post_intervention_dalys_lost": 26468.4,
            "dalys_averted": 145.6,
            "economic_value_preserved_usd": 3494400.0,
            "intervention_type": "urban_cooling_center",
            "intervention_description": "Urban cooling centers reduce heat-related DALYs by 40%",
            "breakdown": {
                "heat_dalys_per_1000_baseline": 1.46,
                "malaria_dalys_per_1000_baseline": 105.0,
                "total_dalys_per_1000_baseline": 106.46,
                "heat_reduction_pct": 40.0,
                "malaria_reduction_pct": 0.0
            },
            "monetization": {
                "gdp_per_capita_usd": 12000.0,
                "value_per_daly_usd": 24000.0,
                "methodology": "WHO-CHOICE standard: 2× GDP per capita per DALY"
            },
            "population_parameters": {
                "population_size": 250000,
                "baseline_dalys_per_1000": 106.46,
                "post_intervention_dalys_per_1000": 90.39
            }
        }
    }
    
    summary = generate_deterministic_summary('health_public', 'Bangkok', data)
    
    print(f"Location: Bangkok")
    print(f"Module: health_public")
    print(f"\nExtracted Data:")
    print(f"  - DALYs averted: {data['public_health_analysis']['dalys_averted']:,.1f}")
    print(f"  - Economic value: ${data['public_health_analysis']['economic_value_preserved_usd']:,.0f}")
    print(f"  - Intervention: {data['public_health_analysis']['intervention_type']}")
    print(f"  - WBGT: {data['heat_stress_analysis']['wbgt_estimate']}°C")
    print(f"  - Malaria risk: {data['malaria_risk_analysis']['risk_score']}")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    # Assertions
    assert "Bangkok" in summary, "Should mention location"
    assert "146" in summary or "145.6" in summary or "145" in summary, f"Should mention DALYs averted (145.6), got: {summary}"
    assert "urban cooling centers" in summary.lower() or "cooling center" in summary.lower(), f"Should mention intervention, got: {summary}"
    assert "$3.5" in summary or "$3.4" in summary, f"Should mention economic value (~$3.5M), got: {summary}"
    assert "0 DALYs" not in summary, f"Should NOT show 0 DALYs, got: {summary}"
    assert len(summary.split('. ')) >= 3, "Should have at least 3 sentences"
    print("✅ PASSED - Correctly extracted nested data")


def test_health_public_high_daly_scenario():
    """Test with higher DALY values (larger population)."""
    print("\n" + "="*80)
    print("TEST: Health Public High DALY Scenario")
    print("="*80)
    
    data = {
        "heat_stress_analysis": {
            "wbgt_estimate": 31.5
        },
        "malaria_risk_analysis": {
            "risk_score": 85
        },
        "public_health_analysis": {
            "baseline_dalys_lost": 850616.67,
            "post_intervention_dalys_lost": 846370.0,
            "dalys_averted": 4246.67,
            "economic_value_preserved_usd": 59453333.33,
            "intervention_type": "urban_cooling_center",
            "intervention_description": "Urban cooling centers reduce heat-related DALYs by 40%"
        }
    }
    
    summary = generate_deterministic_summary('health_public', 'National Capital Region', data)
    
    print(f"Location: National Capital Region")
    print(f"\nExtracted Data:")
    print(f"  - DALYs averted: {data['public_health_analysis']['dalys_averted']:,.1f}")
    print(f"  - Economic value: ${data['public_health_analysis']['economic_value_preserved_usd']:,.0f}")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "4,247" in summary or "4,246" in summary or "4247" in summary, "Should mention ~4,247 DALYs"
    assert "$59" in summary, "Should mention ~$59M"
    assert "extreme heat stress" in summary.lower(), "Should mention extreme heat (WBGT > 30)"
    assert "malaria" in summary.lower(), "Should mention malaria risk"
    print("✅ PASSED")


def test_health_public_mosquito_eradication():
    """Test with mosquito eradication intervention."""
    print("\n" + "="*80)
    print("TEST: Health Public Mosquito Eradication")
    print("="*80)
    
    data = {
        "heat_stress_analysis": {
            "wbgt_estimate": 28.0
        },
        "malaria_risk_analysis": {
            "risk_score": 100
        },
        "public_health_analysis": {
            "baseline_dalys_lost": 52803.33,
            "post_intervention_dalys_lost": 16053.33,
            "dalys_averted": 36750.0,
            "economic_value_preserved_usd": 147000000.0,
            "intervention_type": "mosquito_eradication",
            "intervention_description": "Mosquito eradication programs reduce malaria DALYs by 70%"
        }
    }
    
    summary = generate_deterministic_summary('health_public', 'Sub-Saharan Africa Region', data)
    
    print(f"Location: Sub-Saharan Africa Region")
    print(f"\nExtracted Data:")
    print(f"  - DALYs averted: {data['public_health_analysis']['dalys_averted']:,.0f}")
    print(f"  - Economic value: ${data['public_health_analysis']['economic_value_preserved_usd']:,.0f}")
    print(f"  - Intervention: {data['public_health_analysis']['intervention_type']}")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "36,750" in summary or "36750" in summary, "Should mention 36,750 DALYs"
    assert "$147" in summary, "Should mention $147M"
    assert "mosquito eradication" in summary.lower(), "Should mention mosquito eradication"
    print("✅ PASSED")


def test_health_public_baseline_no_intervention():
    """Test baseline scenario (no intervention)."""
    print("\n" + "="*80)
    print("TEST: Health Public Baseline (No Intervention)")
    print("="*80)
    
    data = {
        "heat_stress_analysis": {
            "wbgt_estimate": 24.0
        },
        "malaria_risk_analysis": {
            "risk_score": 0
        },
        "public_health_analysis": {
            "baseline_dalys_lost": 0.0,
            "post_intervention_dalys_lost": 0.0,
            "dalys_averted": 0.0,
            "economic_value_preserved_usd": 0.0,
            "intervention_type": "none",
            "intervention_description": "No intervention applied (baseline scenario)"
        }
    }
    
    summary = generate_deterministic_summary('health_public', 'Low Risk Area', data)
    
    print(f"Location: Low Risk Area")
    print(f"\nGenerated Summary:")
    print(f"{summary}")
    print()
    
    assert "Low Risk Area" in summary, "Should mention location"
    assert "baseline health burden" in summary.lower() or "0 DALYs" in summary, "Should mention baseline or zero burden"
    print("✅ PASSED")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("NESTED DATA EXTRACTION - TEST SUITE")
    print("="*80)
    
    tests = [
        test_health_public_nested_extraction,
        test_health_public_high_daly_scenario,
        test_health_public_mosquito_eradication,
        test_health_public_baseline_no_intervention,
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
