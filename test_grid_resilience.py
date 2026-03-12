#!/usr/bin/env python3
"""
Integration test script for Energy & Grid Resilience endpoint.

Tests the /api/v1/network/grid-resilience endpoint with various facility scenarios.
"""

import requests
import json

# Base URL - adjust if running on different host/port
BASE_URL = "http://localhost:8000"

def test_moderate_heat_scenario():
    """Test moderate heat increase (5°C) for typical office building."""
    print("\n" + "="*80)
    print("TEST 1: Moderate Heat Scenario - Office Building")
    print("="*80)
    
    payload = {
        "facility_sqft": 50000.0,  # 50,000 sq ft office
        "baseline_temp_c": 25.0,
        "projected_temp_c": 30.0  # +5°C increase
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/grid-resilience",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Temperature Anomaly: {result['temp_anomaly']:.2f}°C")
        print(f"  • HVAC Demand Spike: {result['hvac_spike_pct']:.2f}%")
        print(f"  • Grid Failure Probability: {result['grid_failure_probability']:.1%}")
        print(f"  • Expected Downtime: {result['expected_downtime_hours']:.2f} hours")
        print(f"  • Downtime Loss: ${result['downtime_loss']:,.2f}")
        print(f"\n🔋 MICROGRID SIZING:")
        print(f"  • Solar Capacity: {result['required_solar_kw']:,.0f} kW")
        print(f"  • Battery Storage: {result['required_bess_kwh']:,.0f} kWh")
        print(f"  • Total CAPEX: ${result['microgrid_capex']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


def test_extreme_heat_scenario():
    """Test extreme heat increase (15°C) for data center."""
    print("\n" + "="*80)
    print("TEST 2: Extreme Heat Scenario - Data Center")
    print("="*80)
    
    payload = {
        "facility_sqft": 100000.0,  # 100,000 sq ft data center
        "baseline_temp_c": 25.0,
        "projected_temp_c": 40.0  # +15°C extreme increase
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/grid-resilience",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Temperature Anomaly: {result['temp_anomaly']:.2f}°C")
        print(f"  • HVAC Demand Spike: {result['hvac_spike_pct']:.2f}%")
        print(f"  • Grid Failure Probability: {result['grid_failure_probability']:.1%}")
        print(f"  • Expected Downtime: {result['expected_downtime_hours']:.2f} hours")
        print(f"  • Downtime Loss: ${result['downtime_loss']:,.2f}")
        print(f"\n🔋 MICROGRID SIZING:")
        print(f"  • Solar Capacity: {result['required_solar_kw']:,.0f} kW")
        print(f"  • Battery Storage: {result['required_bess_kwh']:,.0f} kWh")
        print(f"  • Total CAPEX: ${result['microgrid_capex']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


def test_small_facility():
    """Test small facility (retail store)."""
    print("\n" + "="*80)
    print("TEST 3: Small Facility - Retail Store")
    print("="*80)
    
    payload = {
        "facility_sqft": 10000.0,  # 10,000 sq ft retail
        "baseline_temp_c": 24.0,
        "projected_temp_c": 32.0  # +8°C
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/grid-resilience",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Downtime Loss: ${result['downtime_loss']:,.2f}")
        print(f"  • Microgrid CAPEX: ${result['microgrid_capex']:,.2f}")
        print(f"  • ROI Analysis: CAPEX / Annual Loss = {result['microgrid_capex'] / (result['downtime_loss'] * 2):.1f} years")
    else:
        print(f"❌ Error: {response.text}")


def test_large_manufacturing_facility():
    """Test large manufacturing facility."""
    print("\n" + "="*80)
    print("TEST 4: Large Manufacturing Facility")
    print("="*80)
    
    payload = {
        "facility_sqft": 250000.0,  # 250,000 sq ft manufacturing
        "baseline_temp_c": 26.0,
        "projected_temp_c": 38.0  # +12°C
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/grid-resilience",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Temperature Anomaly: {result['temp_anomaly']:.2f}°C")
        print(f"  • Grid Failure Probability: {result['grid_failure_probability']:.1%}")
        print(f"  • Expected Downtime: {result['expected_downtime_hours']:.2f} hours")
        print(f"  • Downtime Loss: ${result['downtime_loss']:,.2f}")
        print(f"\n🔋 MICROGRID SIZING:")
        print(f"  • Solar Capacity: {result['required_solar_kw']:,.0f} kW ({result['required_solar_kw']/1000:.1f} MW)")
        print(f"  • Battery Storage: {result['required_bess_kwh']:,.0f} kWh ({result['required_bess_kwh']/1000:.1f} MWh)")
        print(f"  • Total CAPEX: ${result['microgrid_capex']:,.2f}")
    else:
        print(f"❌ Error: {response.text}")


def test_no_temperature_change():
    """Test edge case: no temperature change."""
    print("\n" + "="*80)
    print("TEST 5: No Temperature Change (Baseline Scenario)")
    print("="*80)
    
    payload = {
        "facility_sqft": 50000.0,
        "baseline_temp_c": 25.0,
        "projected_temp_c": 25.0  # No change
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/grid-resilience",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Temperature Anomaly: {result['temp_anomaly']:.2f}°C")
        print(f"  • Downtime Loss: ${result['downtime_loss']:,.2f}")
        
        if result['downtime_loss'] == 0.0:
            print("  ✅ Correctly shows zero risk with no temperature change")
    else:
        print(f"❌ Error: {response.text}")


def test_extreme_capping():
    """Test extreme temperature with probability capping."""
    print("\n" + "="*80)
    print("TEST 6: Extreme Temperature with Probability Capping")
    print("="*80)
    
    payload = {
        "facility_sqft": 50000.0,
        "baseline_temp_c": 25.0,
        "projected_temp_c": 50.0  # Extreme +25°C
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/grid-resilience",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"  • Temperature Anomaly: {result['temp_anomaly']:.2f}°C")
        print(f"  • HVAC Demand Spike: {result['hvac_spike_pct']:.2f}%")
        print(f"  • Grid Failure Probability: {result['grid_failure_probability']:.1%}")
        
        if result['grid_failure_probability'] == 1.0:
            print("  ✅ Correctly capped at 100% probability")
        
        print(f"  • Expected Downtime: {result['expected_downtime_hours']:.2f} hours (max 12 hours)")
    else:
        print(f"❌ Error: {response.text}")


def test_default_values():
    """Test endpoint with default values."""
    print("\n" + "="*80)
    print("TEST 7: Default Values Test")
    print("="*80)
    
    payload = {
        "projected_temp_c": 30.0  # Only required field
        # facility_sqft defaults to 50000.0
        # baseline_temp_c defaults to 25.0
    }
    
    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(
        f"{BASE_URL}/api/v1/network/grid-resilience",
        json=payload
    )
    
    print(f"\nResponse status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nResponse data:")
        print(json.dumps(result, indent=2))
        
        print(f"\n✅ Endpoint accepts default values correctly")
    else:
        print(f"❌ Error: {response.text}")


if __name__ == "__main__":
    print("\n⚡ ENERGY & GRID RESILIENCE - TESTING")
    print("="*80)
    print("Testing POST /api/v1/network/grid-resilience endpoint")
    print("Make sure the API server is running on http://localhost:8000")
    print("="*80)
    
    try:
        # Test 1: Moderate heat
        test_moderate_heat_scenario()
        
        # Test 2: Extreme heat
        test_extreme_heat_scenario()
        
        # Test 3: Small facility
        test_small_facility()
        
        # Test 4: Large manufacturing
        test_large_manufacturing_facility()
        
        # Test 5: No temperature change
        test_no_temperature_change()
        
        # Test 6: Extreme capping
        test_extreme_capping()
        
        # Test 7: Default values
        test_default_values()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server")
        print("Make sure the server is running: python api.py or uvicorn api:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
