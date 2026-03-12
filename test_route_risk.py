#!/usr/bin/env python3
"""
Test script for Macroeconomic Supply Chain Route Risk endpoint.

Tests the /api/v1/network/route-risk endpoint with sample truck routes.
"""

import requests
import json

# Base URL - adjust if running on different host/port
BASE_URL = "http://localhost:8000"

def test_route_risk_new_york_to_newark():
    """Test route from New York City to Newark (crosses flood-prone areas)."""
    print("\n" + "="*80)
    print("TEST 1: NYC to Newark Route Risk")
    print("="*80)
    
    # Sample route: Manhattan → Jersey City → Newark
    # This route crosses the Hudson River and flood-prone coastal areas
    payload = {
        "route_linestring": {
            "type": "LineString",
            "coordinates": [
                [-74.0060, 40.7128],  # NYC (Manhattan)
                [-74.0377, 40.7178],  # Hudson River crossing
                [-74.0721, 40.7282],  # Jersey City
                [-74.1724, 40.7357]   # Newark
            ]
        },
        "cargo_value": 100000.0,  # $100k default
        "baseline_travel_hours": 1.5
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/route-risk",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Flooded Route Length: {result['flooded_miles']:.2f} miles")
        print(f"  • Detour Delay: {result['detour_delay_hours']:.2f} hours")
        print(f"  • Freight Delay Cost: ${result['freight_delay_cost']:,.2f}")
        print(f"  • Spoilage Cost: ${result['spoilage_cost']:,.2f}")
        print(f"  • Total Value at Risk: ${result['total_value_at_risk']:,.2f}")
        print(f"  • Intervention CAPEX: ${result['intervention_capex']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


def test_route_risk_high_value_cargo():
    """Test with high-value cargo ($500k) to see spoilage impact."""
    print("\n" + "="*80)
    print("TEST 2: High-Value Cargo Route (Miami to Fort Lauderdale)")
    print("="*80)
    
    # Miami to Fort Lauderdale (coastal route vulnerable to storm surge)
    payload = {
        "route_linestring": {
            "type": "LineString",
            "coordinates": [
                [-80.1918, 25.7617],  # Miami
                [-80.1373, 25.9026],  # North Miami
                [-80.1373, 26.1224]   # Fort Lauderdale
            ]
        },
        "cargo_value": 500000.0,  # $500k high-value cargo
        "baseline_travel_hours": 1.0
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/route-risk",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Flooded Route Length: {result['flooded_miles']:.2f} miles")
        print(f"  • Total Value at Risk: ${result['total_value_at_risk']:,.2f}")
        print(f"  • Spoilage Cost Impact: ${result['spoilage_cost']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


def test_route_risk_long_distance():
    """Test long-distance route (Houston to Dallas)."""
    print("\n" + "="*80)
    print("TEST 3: Long-Distance Route (Houston to Dallas)")
    print("="*80)
    
    # Houston to Dallas (passes through flood-prone East Texas)
    payload = {
        "route_linestring": {
            "type": "LineString",
            "coordinates": [
                [-95.3698, 29.7604],  # Houston
                [-95.6378, 30.3508],  # Conroe
                [-96.1089, 31.0877],  # Waco
                [-96.7970, 32.7767]   # Dallas
            ]
        },
        "cargo_value": 250000.0,
        "baseline_travel_hours": 4.5
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/route-risk",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Flooded Route Length: {result['flooded_miles']:.2f} miles")
        print(f"  • Detour Delay: {result['detour_delay_hours']:.2f} hours")
        print(f"  • Total Value at Risk: ${result['total_value_at_risk']:,.2f}")
        print(f"  • Intervention CAPEX: ${result['intervention_capex']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


def test_invalid_geometry():
    """Test error handling with invalid geometry."""
    print("\n" + "="*80)
    print("TEST 4: Invalid Geometry (Polygon instead of LineString)")
    print("="*80)
    
    payload = {
        "route_linestring": {
            "type": "Polygon",  # Wrong geometry type
            "coordinates": [[
                [-74.0060, 40.7128],
                [-74.0377, 40.7178],
                [-74.0721, 40.7282],
                [-74.0060, 40.7128]
            ]]
        },
        "cargo_value": 100000.0,
        "baseline_travel_hours": 1.5
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/route-risk",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 400:
        print("✅ Correctly rejected invalid geometry")
    else:
        print("❌ Should have returned 400 error")


if __name__ == "__main__":
    print("\n🚛 MACROECONOMIC SUPPLY CHAIN - ROUTE RISK TESTING")
    print("="*80)
    print("Testing POST /api/v1/network/route-risk endpoint")
    print("Make sure the API server is running on http://localhost:8000")
    print("="*80)
    
    try:
        # Test 1: NYC to Newark
        test_route_risk_new_york_to_newark()
        
        # Test 2: High-value cargo
        test_route_risk_high_value_cargo()
        
        # Test 3: Long-distance route
        test_route_risk_long_distance()
        
        # Test 4: Invalid geometry
        test_invalid_geometry()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running: python api.py or uvicorn api:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
