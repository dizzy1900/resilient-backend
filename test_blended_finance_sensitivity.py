#!/usr/bin/env python3
"""
Test Suite for Blended Finance Sensitivity Analysis
Tests the rate shock feature for interest rate stress testing
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_base_case_no_shock():
    """Test 1: Base case without rate shock"""
    print("\n" + "="*80)
    print("TEST 1: Base Case (No Rate Shock)")
    print("="*80)
    
    payload = {
        "total_capex": 10_000_000.0,
        "resilience_score": 85,
        "tranches": {
            "commercial_debt_pct": 0.50,
            "concessional_grant_pct": 0.30,
            "municipal_equity_pct": 0.20
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/finance/blended-structure", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"   Blended Rate: {data['blended_interest_rate']*100:.2f}%")
        print(f"   Annual Debt Service: ${data['annual_debt_service']:,.2f}")
        print(f"   Greenium Savings: ${data['total_greenium_savings']:,.2f}")
        print(f"   Sensitivity Analysis: {data.get('sensitivity_analysis', 'None')}")
        return data['annual_debt_service']
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_with_100_bps_shock():
    """Test 2: 100 basis points (+1%) rate shock"""
    print("\n" + "="*80)
    print("TEST 2: Rate Shock +100 bps (+1%)")
    print("="*80)
    
    payload = {
        "total_capex": 10_000_000.0,
        "resilience_score": 85,
        "tranches": {
            "commercial_debt_pct": 0.50,
            "concessional_grant_pct": 0.30,
            "municipal_equity_pct": 0.20
        },
        "rate_shock_bps": 100
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/finance/blended-structure", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"   Base Blended Rate: {data['blended_interest_rate']*100:.2f}%")
        print(f"   Base Annual Payment: ${data['annual_debt_service']:,.2f}")
        
        if data.get('sensitivity_analysis'):
            sa = data['sensitivity_analysis']
            print(f"\n   SENSITIVITY ANALYSIS:")
            print(f"   Rate Shock: +{sa['rate_shock_bps']} bps")
            print(f"   Stressed Commercial Rate: {sa['stressed_commercial_rate']*100:.2f}%")
            print(f"   Stressed Blended Rate: {sa['stressed_blended_rate']*100:.2f}%")
            print(f"   Base Annual Payment: ${sa['base_annual_payment']:,.2f}")
            print(f"   Stressed Annual Payment: ${sa['stressed_annual_payment']:,.2f}")
            print(f"   Debt Service Delta: ${sa['debt_service_delta']:,.2f}")
            print(f"   Payment Increase: {sa['payment_increase_pct']:.2f}%")
            print(f"   Lifetime Cost Increase: ${sa['lifetime_cost_increase']:,.2f}")
        else:
            print("   ⚠️  No sensitivity analysis in response")
        
        return data
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_with_200_bps_shock():
    """Test 3: 200 basis points (+2%) severe rate shock"""
    print("\n" + "="*80)
    print("TEST 3: Severe Rate Shock +200 bps (+2%)")
    print("="*80)
    
    payload = {
        "total_capex": 5_000_000.0,
        "resilience_score": 65,
        "tranches": {
            "commercial_debt_pct": 0.60,
            "concessional_grant_pct": 0.25,
            "municipal_equity_pct": 0.15
        },
        "rate_shock_bps": 200
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/finance/blended-structure", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"   Resilience Score: {data['input_resilience_score']}")
        print(f"   Greenium Discount: {data['greenium_discount_bps']} bps")
        print(f"   Base Blended Rate: {data['blended_interest_rate']*100:.2f}%")
        
        if data.get('sensitivity_analysis'):
            sa = data['sensitivity_analysis']
            print(f"\n   SENSITIVITY ANALYSIS:")
            print(f"   Rate Shock: +{sa['rate_shock_bps']} bps")
            print(f"   Stressed Blended Rate: {sa['stressed_blended_rate']*100:.2f}%")
            print(f"   Payment Increase: {sa['payment_increase_pct']:.2f}%")
            print(f"   Annual Cost Increase: ${sa['debt_service_delta']:,.2f}")
            print(f"   20-Year Cost Increase: ${sa['lifetime_cost_increase']:,.2f}")
        
        return data
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_negative_rate_shock():
    """Test 4: Negative rate shock (rate decrease scenario)"""
    print("\n" + "="*80)
    print("TEST 4: Negative Rate Shock -50 bps (-0.5%)")
    print("="*80)
    
    payload = {
        "total_capex": 3_000_000.0,
        "resilience_score": 45,
        "tranches": {
            "commercial_debt_pct": 0.70,
            "concessional_grant_pct": 0.20,
            "municipal_equity_pct": 0.10
        },
        "rate_shock_bps": -50
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/finance/blended-structure", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        
        if data.get('sensitivity_analysis'):
            sa = data['sensitivity_analysis']
            print(f"   Rate Shock: {sa['rate_shock_bps']} bps")
            print(f"   Base Annual Payment: ${sa['base_annual_payment']:,.2f}")
            print(f"   Stressed Annual Payment: ${sa['stressed_annual_payment']:,.2f}")
            print(f"   Debt Service Delta: ${sa['debt_service_delta']:,.2f}")
            print(f"   Payment Change: {sa['payment_increase_pct']:.2f}%")
        
        return data
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def test_high_commercial_debt_shock():
    """Test 5: High commercial debt percentage with rate shock"""
    print("\n" + "="*80)
    print("TEST 5: High Commercial Debt (90%) with +150 bps Shock")
    print("="*80)
    
    payload = {
        "total_capex": 8_000_000.0,
        "resilience_score": 80,
        "tranches": {
            "commercial_debt_pct": 0.90,
            "concessional_grant_pct": 0.05,
            "municipal_equity_pct": 0.05
        },
        "rate_shock_bps": 150
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/finance/blended-structure", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"   Commercial Debt Amount: ${data['commercial_debt_amount']:,.2f}")
        print(f"   Commercial Debt %: 90%")
        
        if data.get('sensitivity_analysis'):
            sa = data['sensitivity_analysis']
            print(f"\n   SENSITIVITY ANALYSIS:")
            print(f"   Rate Shock: +{sa['rate_shock_bps']} bps")
            print(f"   Payment Increase: {sa['payment_increase_pct']:.2f}%")
            print(f"   Annual Cost Increase: ${sa['debt_service_delta']:,.2f}")
            print(f"   ⚠️  High commercial debt amplifies rate risk!")
        
        return data
    else:
        print(f"❌ Failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None


def run_all_tests():
    """Run all sensitivity analysis tests"""
    print("\n" + "="*80)
    print("BLENDED FINANCE SENSITIVITY ANALYSIS TEST SUITE")
    print("="*80)
    print("Testing rate shock feature for interest rate stress testing")
    
    try:
        test_base_case_no_shock()
        test_with_100_bps_shock()
        test_with_200_bps_shock()
        test_negative_rate_shock()
        test_high_commercial_debt_shock()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80)
        print("\nKey Insights:")
        print("1. Sensitivity analysis only appears when rate_shock_bps is provided")
        print("2. Rate shocks apply to commercial debt portion only")
        print("3. Higher commercial debt % = higher rate risk exposure")
        print("4. Greenium discounts provide cushion against rate increases")
        print("5. Negative rate shocks show downside savings potential")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")


if __name__ == "__main__":
    run_all_tests()
