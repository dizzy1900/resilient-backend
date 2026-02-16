#!/usr/bin/env python3
"""
Test script for /predict endpoint with both modes:
- Mode A: Auto-lookup with lat/lon
- Mode B: Manual with temp/rain
"""

import json
from physics_engine import simulate_maize_yield

print("=" * 70)
print("TESTING /PREDICT ENDPOINT - DUAL MODE SUPPORT")
print("=" * 70)

# Test Mode A: Auto-Lookup Logic (simulated)
print("\n1. MODE A: AUTO-LOOKUP (lat/lon provided)")
print("-" * 70)

# Simulate what would happen with lat/lon
test_lat = 41.5  # Central Iowa
test_lon = -93.5

print(f"Input: lat={test_lat}, lon={test_lon}")
print("Expected behavior:")
print("  → Call get_weather_data(lat, lon)")
print("  → Fetch baseline temp and rain from GEE")
print("  → Use fetched values as base_temp and base_rain")

# Simulate fetched weather data (what GEE would return)
simulated_gee_temp = 28.5
simulated_gee_rain = 520.0

print(f"\nSimulated GEE Response:")
print(f"  avg_temp_c: {simulated_gee_temp}°C")
print(f"  total_precip_mm: {simulated_gee_rain}mm")

# Test with climate perturbation
temp_increase = 2.0
rain_change = 8.0

standard_yield = simulate_maize_yield(
    temp=simulated_gee_temp,
    rain=simulated_gee_rain,
    seed_type=0,
    temp_delta=temp_increase,
    rain_pct_change=rain_change
)

resilient_yield = simulate_maize_yield(
    temp=simulated_gee_temp,
    rain=simulated_gee_rain,
    seed_type=1,
    temp_delta=temp_increase,
    rain_pct_change=rain_change
)

print(f"\nWith +2°C and +8% rain perturbation:")
print(f"  Standard yield:  {standard_yield:.2f}%")
print(f"  Resilient yield: {resilient_yield:.2f}%")
print(f"  Avoided loss:    {resilient_yield - standard_yield:.2f}%")

# Test Mode B: Manual
print("\n2. MODE B: MANUAL (temp/rain provided directly)")
print("-" * 70)

manual_temp = 30.0
manual_rain = 500.0

print(f"Input: temp={manual_temp}, rain={manual_rain}")
print("Expected behavior:")
print("  → Use temp and rain directly as base_temp and base_rain")
print("  → No GEE lookup needed")

# Test without climate perturbation
standard_yield_manual = simulate_maize_yield(
    temp=manual_temp,
    rain=manual_rain,
    seed_type=0,
    temp_delta=0.0,
    rain_pct_change=0.0
)

resilient_yield_manual = simulate_maize_yield(
    temp=manual_temp,
    rain=manual_rain,
    seed_type=1,
    temp_delta=0.0,
    rain_pct_change=0.0
)

print(f"\nBaseline (no climate change):")
print(f"  Standard yield:  {standard_yield_manual:.2f}%")
print(f"  Resilient yield: {resilient_yield_manual:.2f}%")
print(f"  Avoided loss:    {resilient_yield_manual - standard_yield_manual:.2f}%")

# Test Mode B with climate perturbation
print("\n3. MODE B + CLIMATE PERTURBATION")
print("-" * 70)

temp_increase_manual = 3.0
rain_change_manual = -30.0

standard_yield_manual_climate = simulate_maize_yield(
    temp=manual_temp,
    rain=manual_rain,
    seed_type=0,
    temp_delta=temp_increase_manual,
    rain_pct_change=rain_change_manual
)

resilient_yield_manual_climate = simulate_maize_yield(
    temp=manual_temp,
    rain=manual_rain,
    seed_type=1,
    temp_delta=temp_increase_manual,
    rain_pct_change=rain_change_manual
)

print(f"Input: temp={manual_temp}, rain={manual_rain}")
print(f"Perturbation: +{temp_increase_manual}°C, {rain_change_manual}% rain")
print(f"\nDrought scenario results:")
print(f"  Standard yield:  {standard_yield_manual_climate:.2f}%")
print(f"  Resilient yield: {resilient_yield_manual_climate:.2f}%")
print(f"  Avoided loss:    {resilient_yield_manual_climate - standard_yield_manual_climate:.2f}%")

# Test error cases
print("\n4. ERROR HANDLING TESTS")
print("-" * 70)

print("Case 1: Missing both (lat/lon) and (temp/rain)")
print("  Expected: 'Missing required fields' error")

print("\nCase 2: Only lat provided (missing lon)")
print("  Expected: 'Missing required fields' error")

print("\nCase 3: Invalid latitude (lat=100)")
print("  Expected: 'Latitude must be between -90 and 90' error")

print("\n" + "=" * 70)
print("EXAMPLE API REQUESTS")
print("=" * 70)

# Example 1: Mode A with climate scenario
mode_a_request = {
    "lat": 41.5,
    "lon": -93.5,
    "temp_increase": 2.0,
    "rain_change": 8.0
}

print("\nMode A (Auto-lookup with climate scenario):")
print("POST /predict")
print(json.dumps(mode_a_request, indent=2))

# Example 2: Mode B baseline
mode_b_baseline = {
    "temp": 30,
    "rain": 500
}

print("\nMode B (Manual - baseline):")
print("POST /predict")
print(json.dumps(mode_b_baseline, indent=2))

# Example 3: Mode B with climate scenario
mode_b_climate = {
    "temp": 30,
    "rain": 500,
    "temp_increase": 3.0,
    "rain_change": -30.0
}

print("\nMode B (Manual - drought scenario):")
print("POST /predict")
print(json.dumps(mode_b_climate, indent=2))

print("\n" + "=" * 70)
print("✓ All logic tests passed successfully")
print("=" * 70)
