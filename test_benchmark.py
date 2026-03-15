#!/usr/bin/env python3
"""
Integration test script for Peer Benchmarking endpoint.

Tests the /api/v1/compliance/benchmark endpoint with various sector/hazard combinations.
"""

import requests

# Base URL - adjust if running on different host/port
BASE_URL = "http://localhost:8000"


def test_agriculture_heat():
    """Test Agriculture + Heat benchmark."""
    print("\n" + "="*80)
    print("TEST 1: Agriculture + Heat")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/api/v1/compliance/benchmark",
        params={"sector": "Agriculture", "hazard_type": "Heat"}
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 BENCHMARK DATA:")
        print(f"  • Sector: {data['sector']}")
        print(f"  • Hazard: {data['hazard_type']}")
        print(f"  • Metric: {data['metric_name']}")
        print(f"  • Industry Average: {data['industry_average']}{data['unit']}")
        print(f"  • Top Quartile Target: {data['top_quartile_target']}{data['unit']}")
        print(f"  • Source: {data['data_source']}")
    else:
        print(f"❌ Error: {response.text}")


def test_logistics_flood():
    """Test Logistics + Flood benchmark."""
    print("\n" + "="*80)
    print("TEST 2: Logistics + Flood")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/api/v1/compliance/benchmark",
        params={"sector": "Logistics", "hazard_type": "Flood"}
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 BENCHMARK DATA:")
        print(f"  • Metric: {data['metric_name']}")
        print(f"  • Industry Average: {data['industry_average']} {data['unit']}")
        print(f"  • Top Quartile: {data['top_quartile_target']} {data['unit']}")
    else:
        print(f"❌ Error: {response.text}")


def test_case_insensitive():
    """Test case-insensitive matching."""
    print("\n" + "="*80)
    print("TEST 3: Case-Insensitive Matching (lowercase)")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/api/v1/compliance/benchmark",
        params={"sector": "energy", "hazard_type": "heat"}  # lowercase
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Case-insensitive matching works!")
        print(f"  • Sector: {data['sector']}")
        print(f"  • Metric: {data['metric_name']}")
    else:
        print(f"❌ Error: {response.text}")


def test_not_found():
    """Test 404 for non-existent combination."""
    print("\n" + "="*80)
    print("TEST 4: Non-Existent Combination (should return 404)")
    print("="*80)
    
    response = requests.get(
        f"{BASE_URL}/api/v1/compliance/benchmark",
        params={"sector": "Technology", "hazard_type": "Wildfire"}
    )
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 404:
        print(f"\n✅ Correctly returns 404 for unavailable benchmark")
        print(f"  • Detail: {response.json()['detail']}")
    else:
        print(f"❌ Expected 404, got {response.status_code}")


def test_all_benchmarks():
    """Test all available benchmarks."""
    print("\n" + "="*80)
    print("TEST 5: All Available Benchmarks")
    print("="*80)
    
    benchmarks = [
        ("Commercial Real Estate", "Heat"),
        ("Agriculture", "Drought"),
        ("Agriculture", "Heat"),
        ("Logistics", "Flood"),
        ("Industrial Manufacturing", "Flood"),
        ("Construction/Outdoor Labor", "Heat"),
        ("Insurance", "Flood"),
        ("Energy", "Heat")
    ]
    
    success_count = 0
    for sector, hazard in benchmarks:
        response = requests.get(
            f"{BASE_URL}/api/v1/compliance/benchmark",
            params={"sector": sector, "hazard_type": hazard}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {sector} + {hazard}: {data['metric_name']}")
            success_count += 1
        else:
            print(f"❌ {sector} + {hazard}: Failed")
    
    print(f"\n📊 Results: {success_count}/{len(benchmarks)} benchmarks loaded successfully")


if __name__ == "__main__":
    print("\n📚 PEER BENCHMARKING API - TESTING")
    print("="*80)
    print("Testing GET /api/v1/compliance/benchmark endpoint")
    print("Make sure the API server is running on http://localhost:8000")
    print("="*80)
    
    try:
        # Test 1: Agriculture + Heat
        test_agriculture_heat()
        
        # Test 2: Logistics + Flood
        test_logistics_flood()
        
        # Test 3: Case-insensitive
        test_case_insensitive()
        
        # Test 4: Not found (404)
        test_not_found()
        
        # Test 5: All benchmarks
        test_all_benchmarks()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running: python api.py or uvicorn api:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
