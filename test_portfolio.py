#!/usr/bin/env python3
"""
Integration test script for Macro-Portfolio Risk Analysis endpoint.

Tests the /api/v1/portfolio/analyze endpoint with various portfolio scenarios.
"""

import requests
import json

# Base URL - adjust if running on different host/port
BASE_URL = "http://localhost:8000"


def test_diverse_portfolio():
    """Test diverse portfolio with all hazard types."""
    print("\n" + "="*80)
    print("TEST 1: Diverse Portfolio (All Hazard Types)")
    print("="*80)
    
    payload = {
        "assets": [
            {
                "id": "PROP-001",
                "property_name": "Manhattan Data Center",
                "location": "New York, NY",
                "asset_value": 50000000.0,
                "primary_hazard": "Flood"
            },
            {
                "id": "PROP-002",
                "property_name": "Phoenix Warehouse",
                "location": "Phoenix, AZ",
                "asset_value": 10000000.0,
                "primary_hazard": "Heat"
            },
            {
                "id": "PROP-003",
                "property_name": "Miami Beach Hotel",
                "location": "Miami, FL",
                "asset_value": 30000000.0,
                "primary_hazard": "Coastal"
            },
            {
                "id": "PROP-004",
                "property_name": "Dallas Distribution Hub",
                "location": "Dallas, TX",
                "asset_value": 15000000.0,
                "primary_hazard": "Supply Chain"
            }
        ]
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/portfolio/analyze",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 PORTFOLIO SUMMARY:")
        print(f"  • Total Portfolio Value: ${result['summary']['total_portfolio_value']:,.2f}")
        print(f"  • Total Value at Risk: ${result['summary']['total_value_at_risk']:,.2f}")
        print(f"  • Average Resilience Score: {result['summary']['average_resilience_score']:.2f}/100")
        
        print(f"\n📈 VAR BY HAZARD (Donut Chart Data):")
        for hazard, var in result['visualizations']['var_by_hazard'].items():
            print(f"  • {hazard}: ${var:,.2f}")
        
        print(f"\n🚨 TOP AT-RISK ASSETS:")
        for i, asset in enumerate(result['visualizations']['top_at_risk_assets'], 1):
            print(f"  {i}. {asset['property_name']} - ${asset['value_at_risk']:,.2f} ({asset['status']})")
    else:
        print(f"❌ Error: {response.text}")


def test_single_hazard_concentration():
    """Test portfolio concentrated in single hazard type."""
    print("\n" + "="*80)
    print("TEST 2: Coastal Asset Concentration")
    print("="*80)
    
    payload = {
        "assets": [
            {
                "id": "COAST-001",
                "property_name": "Malibu Resort",
                "location": "Malibu, CA",
                "asset_value": 75000000.0,
                "primary_hazard": "Coastal"
            },
            {
                "id": "COAST-002",
                "property_name": "Charleston Marina",
                "location": "Charleston, SC",
                "asset_value": 25000000.0,
                "primary_hazard": "Coastal"
            },
            {
                "id": "COAST-003",
                "property_name": "Outer Banks Condos",
                "location": "Outer Banks, NC",
                "asset_value": 40000000.0,
                "primary_hazard": "Coastal"
            }
        ]
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/portfolio/analyze",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n📊 PORTFOLIO SUMMARY:")
        print(f"  • Total Portfolio Value: ${result['summary']['total_portfolio_value']:,.2f}")
        print(f"  • Total Value at Risk: ${result['summary']['total_value_at_risk']:,.2f}")
        print(f"  • VaR %: {(result['summary']['total_value_at_risk'] / result['summary']['total_portfolio_value']) * 100:.1f}%")
        print(f"  • Average Resilience Score: {result['summary']['average_resilience_score']:.2f}/100")
        
        if result['summary']['average_resilience_score'] < 40:
            print(f"\n⚠️  CRITICAL: Portfolio has high coastal concentration risk!")
    else:
        print(f"❌ Error: {response.text}")


def test_large_portfolio():
    """Test large portfolio with 10+ assets."""
    print("\n" + "="*80)
    print("TEST 3: Large Portfolio (10 Assets)")
    print("="*80)
    
    payload = {
        "assets": [
            {"id": f"ASSET-{i:03d}", "property_name": f"Property {i}", "location": "Various", 
             "asset_value": 5000000.0 + (i * 1000000), 
             "primary_hazard": ["Flood", "Heat", "Coastal", "Supply Chain"][i % 4]}
            for i in range(1, 11)
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/portfolio/analyze",
        json=payload
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n📊 PORTFOLIO SUMMARY:")
        print(f"  • Total Assets: {len(result['ledger'])}")
        print(f"  • Total Portfolio Value: ${result['summary']['total_portfolio_value']:,.2f}")
        print(f"  • Total Value at Risk: ${result['summary']['total_value_at_risk']:,.2f}")
        print(f"  • Average Resilience Score: {result['summary']['average_resilience_score']:.2f}/100")
        
        print(f"\n🚨 TOP 5 AT-RISK ASSETS:")
        for i, asset in enumerate(result['visualizations']['top_at_risk_assets'], 1):
            print(f"  {i}. {asset['id']} - ${asset['value_at_risk']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


def test_high_value_single_asset():
    """Test portfolio with single high-value asset."""
    print("\n" + "="*80)
    print("TEST 4: High-Value Single Asset")
    print("="*80)
    
    payload = {
        "assets": [
            {
                "id": "HQ-001",
                "property_name": "Global Headquarters",
                "location": "San Francisco, CA",
                "asset_value": 500000000.0,
                "primary_hazard": "Flood"
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/portfolio/analyze",
        json=payload
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n📊 ASSET ANALYSIS:")
        asset = result['ledger'][0]
        print(f"  • Asset Value: ${asset['asset_value']:,.2f}")
        print(f"  • Value at Risk: ${asset['value_at_risk']:,.2f}")
        print(f"  • Resilience Score: {asset['resilience_score']:.2f}/100")
        print(f"  • Status: {asset['status']}")
        
        if asset['status'] == "Critical":
            print(f"\n⚠️  ALERT: Single-point concentration risk - immediate risk mitigation required!")
    else:
        print(f"❌ Error: {response.text}")


def test_status_distribution():
    """Test portfolio with mix of Critical, Warning, and Secure assets."""
    print("\n" + "="*80)
    print("TEST 5: Status Distribution Analysis")
    print("="*80)
    
    payload = {
        "assets": [
            {"id": "CRIT-1", "property_name": "Critical Asset 1", "location": "Miami", 
             "asset_value": 20000000.0, "primary_hazard": "Coastal"},  # 0 score - Critical
            {"id": "CRIT-2", "property_name": "Critical Asset 2", "location": "Houston", 
             "asset_value": 15000000.0, "primary_hazard": "Flood"},  # 25 score - Critical
            {"id": "WARN-1", "property_name": "Warning Asset 1", "location": "Chicago", 
             "asset_value": 10000000.0, "primary_hazard": "Supply Chain"},  # 50 score - Warning
            {"id": "SECURE-1", "property_name": "Secure Asset 1", "location": "Phoenix", 
             "asset_value": 8000000.0, "primary_hazard": "Heat"}  # 75 score - Secure
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/portfolio/analyze",
        json=payload
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        
        # Count status distribution
        status_counts = {"Critical": 0, "Warning": 0, "Secure": 0}
        for asset in result['ledger']:
            status_counts[asset['status']] += 1
        
        print(f"\n📊 STATUS DISTRIBUTION:")
        print(f"  • Critical: {status_counts['Critical']} assets")
        print(f"  • Warning: {status_counts['Warning']} assets")
        print(f"  • Secure: {status_counts['Secure']} assets")
        
        print(f"\n📈 RESILIENCE METRICS:")
        print(f"  • Average Score: {result['summary']['average_resilience_score']:.2f}/100")
        print(f"  • Total VaR: ${result['summary']['total_value_at_risk']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


if __name__ == "__main__":
    print("\n🏢 MACRO-PORTFOLIO RISK ANALYSIS - TESTING")
    print("="*80)
    print("Testing POST /api/v1/portfolio/analyze endpoint")
    print("Make sure the API server is running on http://localhost:8000")
    print("="*80)
    
    try:
        # Test 1: Diverse portfolio
        test_diverse_portfolio()
        
        # Test 2: Coastal concentration
        test_single_hazard_concentration()
        
        # Test 3: Large portfolio
        test_large_portfolio()
        
        # Test 4: High-value single asset
        test_high_value_single_asset()
        
        # Test 5: Status distribution
        test_status_distribution()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running: python api.py or uvicorn api:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
