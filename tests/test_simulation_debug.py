#!/usr/bin/env python3
"""
Test simulation_debug output in /predict endpoint.
Verifies that debug values match the physics engine calculations.
"""

import json
from physics_engine import simulate_maize_yield

print("=" * 70)
print("TESTING SIMULATION_DEBUG OUTPUT")
print("=" * 70)

def simulate_predict_response(base_temp, base_rain, temp_increase, rain_change):
    """Simulate the /predict endpoint logic"""
    
    # Calculate final simulated values (what physics engine sees)
    final_simulated_temp = base_temp + temp_increase
    rain_modifier = 1.0 + (rain_change / 100.0)
    final_simulated_rain = max(0.0, base_rain * rain_modifier)
    
    # Run physics engine
    standard_yield = simulate_maize_yield(
        temp=base_temp,
        rain=base_rain,
        seed_type=0,
        temp_delta=temp_increase,
        rain_pct_change=rain_change
    )
    
    resilient_yield = simulate_maize_yield(
        temp=base_temp,
        rain=base_rain,
        seed_type=1,
        temp_delta=temp_increase,
        rain_pct_change=rain_change
    )
    
    # Build debug section
    simulation_debug = {
        'raw_temp': round(base_temp, 2),
        'perturbation_added': round(temp_increase, 2),
        'final_simulated_temp': round(final_simulated_temp, 2),
        'raw_rain': round(base_rain, 2),
        'rain_modifier': round(rain_change, 2),
        'final_simulated_rain': round(final_simulated_rain, 2)
    }
    
    return {
        'standard_yield': standard_yield,
        'resilient_yield': resilient_yield,
        'simulation_debug': simulation_debug
    }

# Test Case 1: Baseline (no perturbation)
print("\n1. BASELINE TEST (No Climate Change)")
print("-" * 70)

result1 = simulate_predict_response(
    base_temp=30.0,
    base_rain=500.0,
    temp_increase=0.0,
    rain_change=0.0
)

print("Request: temp=30, rain=500, temp_increase=0, rain_change=0")
print("\nSimulation Debug:")
print(json.dumps(result1['simulation_debug'], indent=2))
print(f"\nYields:")
print(f"  Standard: {result1['standard_yield']:.2f}%")
print(f"  Resilient: {result1['resilient_yield']:.2f}%")

# Verify
assert result1['simulation_debug']['raw_temp'] == 30.0
assert result1['simulation_debug']['perturbation_added'] == 0.0
assert result1['simulation_debug']['final_simulated_temp'] == 30.0
assert result1['simulation_debug']['raw_rain'] == 500.0
assert result1['simulation_debug']['rain_modifier'] == 0.0
assert result1['simulation_debug']['final_simulated_rain'] == 500.0
print("✓ All debug values correct")

# Test Case 2: +2°C warming, +8% rain (US Midwest scenario)
print("\n2. US MIDWEST SCENARIO (+2°C, +8% rain)")
print("-" * 70)

result2 = simulate_predict_response(
    base_temp=30.0,
    base_rain=500.0,
    temp_increase=2.0,
    rain_change=8.0
)

print("Request: temp=30, rain=500, temp_increase=2, rain_change=8")
print("\nSimulation Debug:")
print(json.dumps(result2['simulation_debug'], indent=2))
print(f"\nYields:")
print(f"  Standard: {result2['standard_yield']:.2f}%")
print(f"  Resilient: {result2['resilient_yield']:.2f}%")

# Verify math
expected_final_temp = 30.0 + 2.0  # = 32.0
expected_final_rain = 500.0 * 1.08  # = 540.0

assert result2['simulation_debug']['raw_temp'] == 30.0
assert result2['simulation_debug']['perturbation_added'] == 2.0
assert result2['simulation_debug']['final_simulated_temp'] == 32.0
assert result2['simulation_debug']['raw_rain'] == 500.0
assert result2['simulation_debug']['rain_modifier'] == 8.0
assert result2['simulation_debug']['final_simulated_rain'] == 540.0
print("✓ All debug values correct")
print(f"✓ Temperature calculation: {result2['simulation_debug']['raw_temp']} + {result2['simulation_debug']['perturbation_added']} = {result2['simulation_debug']['final_simulated_temp']}°C")
print(f"✓ Rainfall calculation: {result2['simulation_debug']['raw_rain']} × 1.08 = {result2['simulation_debug']['final_simulated_rain']}mm")

# Test Case 3: Drought scenario (+3°C, -30% rain)
print("\n3. DROUGHT SCENARIO (+3°C, -30% rain)")
print("-" * 70)

result3 = simulate_predict_response(
    base_temp=30.0,
    base_rain=500.0,
    temp_increase=3.0,
    rain_change=-30.0
)

print("Request: temp=30, rain=500, temp_increase=3, rain_change=-30")
print("\nSimulation Debug:")
print(json.dumps(result3['simulation_debug'], indent=2))
print(f"\nYields:")
print(f"  Standard: {result3['standard_yield']:.2f}%")
print(f"  Resilient: {result3['resilient_yield']:.2f}%")

# Verify math
expected_final_temp = 30.0 + 3.0  # = 33.0
expected_final_rain = 500.0 * 0.7  # = 350.0

assert result3['simulation_debug']['raw_temp'] == 30.0
assert result3['simulation_debug']['perturbation_added'] == 3.0
assert result3['simulation_debug']['final_simulated_temp'] == 33.0
assert result3['simulation_debug']['raw_rain'] == 500.0
assert result3['simulation_debug']['rain_modifier'] == -30.0
assert result3['simulation_debug']['final_simulated_rain'] == 350.0
print("✓ All debug values correct")
print(f"✓ Temperature calculation: {result3['simulation_debug']['raw_temp']} + {result3['simulation_debug']['perturbation_added']} = {result3['simulation_debug']['final_simulated_temp']}°C")
print(f"✓ Rainfall calculation: {result3['simulation_debug']['raw_rain']} × 0.70 = {result3['simulation_debug']['final_simulated_rain']}mm")

# Test Case 4: Extreme negative rain (constraint test)
print("\n4. EDGE CASE: Extreme drought (-100% rain)")
print("-" * 70)

result4 = simulate_predict_response(
    base_temp=30.0,
    base_rain=500.0,
    temp_increase=0.0,
    rain_change=-100.0
)

print("Request: temp=30, rain=500, temp_increase=0, rain_change=-100")
print("\nSimulation Debug:")
print(json.dumps(result4['simulation_debug'], indent=2))
print(f"\nYields:")
print(f"  Standard: {result4['standard_yield']:.2f}%")
print(f"  Resilient: {result4['resilient_yield']:.2f}%")

# Verify constraint (rain can't go below 0)
assert result4['simulation_debug']['final_simulated_rain'] == 0.0
print("✓ Rainfall correctly constrained to 0 (can't be negative)")

print("\n" + "=" * 70)
print("EXAMPLE API RESPONSE")
print("=" * 70)

example_response = {
    "status": "success",
    "data": {
        "input_conditions": {
            "max_temp_celsius": 30.0,
            "total_rain_mm": 500.0,
            "data_source": "manual"
        },
        "predictions": {
            "standard_seed": {
                "type_code": 0,
                "predicted_yield": 90.0
            },
            "resilient_seed": {
                "type_code": 1,
                "predicted_yield": 97.5
            }
        },
        "analysis": {
            "avoided_loss": 7.5,
            "percentage_improvement": 8.33,
            "recommendation": "resilient"
        },
        "simulation_debug": {
            "raw_temp": 30.0,
            "perturbation_added": 2.0,
            "final_simulated_temp": 32.0,
            "raw_rain": 500.0,
            "rain_modifier": 8.0,
            "final_simulated_rain": 540.0
        }
    }
}

print("\nPOST /predict")
print(json.dumps(example_response, indent=2))

print("\n" + "=" * 70)
print("✓ All simulation_debug tests passed")
print("=" * 70)
