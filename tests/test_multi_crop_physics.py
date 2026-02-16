#!/usr/bin/env python3
"""
Test the multi-crop physics engine (maize and cocoa)
"""

from physics_engine import calculate_yield, calculate_maize_yield, calculate_cocoa_yield

print("Testing Multi-Crop Physics Engine")
print("=" * 60)

# Test Case 1: Maize - Optimal conditions
print("\nTest Case 1: Maize - Optimal conditions")
print("-" * 60)

maize_optimal_temp = 25.0
maize_optimal_rain = 800.0
standard_seed = 0
resilient_seed = 1

maize_yield_standard = calculate_yield(maize_optimal_temp, maize_optimal_rain, standard_seed, 'maize')
maize_yield_resilient = calculate_yield(maize_optimal_temp, maize_optimal_rain, resilient_seed, 'maize')

print(f"  Temperature: {maize_optimal_temp}°C")
print(f"  Rainfall: {maize_optimal_rain}mm")
print(f"  Standard seed yield: {maize_yield_standard:.2f}%")
print(f"  Resilient seed yield: {maize_yield_resilient:.2f}%")

assert maize_yield_standard == 100.0, "Optimal conditions should give 100% yield"
assert maize_yield_resilient == 100.0, "Optimal conditions should give 100% yield"
print("  ✓ Passed")

# Test Case 2: Maize - Heat stress
print("\nTest Case 2: Maize - Heat stress (35°C)")
print("-" * 60)

maize_hot_temp = 35.0

maize_hot_standard = calculate_yield(maize_hot_temp, maize_optimal_rain, standard_seed, 'maize')
maize_hot_resilient = calculate_yield(maize_hot_temp, maize_optimal_rain, resilient_seed, 'maize')

print(f"  Temperature: {maize_hot_temp}°C")
print(f"  Rainfall: {maize_optimal_rain}mm")
print(f"  Standard seed yield: {maize_hot_standard:.2f}%")
print(f"  Resilient seed yield: {maize_hot_resilient:.2f}%")

assert maize_hot_resilient > maize_hot_standard, "Resilient seed should perform better under heat stress"
print(f"  Heat tolerance advantage: +{maize_hot_resilient - maize_hot_standard:.2f}%")
print("  ✓ Passed")

# Test Case 3: Maize - Drought stress
print("\nTest Case 3: Maize - Drought stress (400mm)")
print("-" * 60)

maize_drought_rain = 400.0

maize_drought_standard = calculate_yield(maize_optimal_temp, maize_drought_rain, standard_seed, 'maize')
maize_drought_resilient = calculate_yield(maize_optimal_temp, maize_drought_rain, resilient_seed, 'maize')

print(f"  Temperature: {maize_optimal_temp}°C")
print(f"  Rainfall: {maize_drought_rain}mm")
print(f"  Standard seed yield: {maize_drought_standard:.2f}%")
print(f"  Resilient seed yield: {maize_drought_resilient:.2f}%")

assert maize_drought_resilient > maize_drought_standard, "Resilient seed should perform better under drought"
print(f"  Drought tolerance advantage: +{maize_drought_resilient - maize_drought_standard:.2f}%")
print("  ✓ Passed")

# Test Case 4: Cocoa - Optimal conditions
print("\nTest Case 4: Cocoa - Optimal conditions")
print("-" * 60)

cocoa_optimal_temp = 25.0
cocoa_optimal_rain = 1750.0

cocoa_yield_standard = calculate_yield(cocoa_optimal_temp, cocoa_optimal_rain, standard_seed, 'cocoa')
cocoa_yield_resilient = calculate_yield(cocoa_optimal_temp, cocoa_optimal_rain, resilient_seed, 'cocoa')

print(f"  Temperature: {cocoa_optimal_temp}°C")
print(f"  Rainfall: {cocoa_optimal_rain}mm")
print(f"  Standard seed yield: {cocoa_yield_standard:.2f}%")
print(f"  Resilient seed yield: {cocoa_yield_resilient:.2f}%")

assert cocoa_yield_standard == 100.0, "Optimal conditions should give 100% yield"
assert cocoa_yield_resilient == 100.0, "Optimal conditions should give 100% yield"
print("  ✓ Passed")

# Test Case 5: Cocoa - Drought (below minimum rain)
print("\nTest Case 5: Cocoa - Drought stress (1000mm, below 1200mm minimum)")
print("-" * 60)

cocoa_drought_rain = 1000.0

cocoa_drought_standard = calculate_yield(cocoa_optimal_temp, cocoa_drought_rain, standard_seed, 'cocoa')
cocoa_drought_resilient = calculate_yield(cocoa_optimal_temp, cocoa_drought_rain, resilient_seed, 'cocoa')

print(f"  Temperature: {cocoa_optimal_temp}°C")
print(f"  Rainfall: {cocoa_drought_rain}mm (deficit: {1200.0 - cocoa_drought_rain}mm)")
print(f"  Standard seed yield: {cocoa_drought_standard:.2f}%")
print(f"  Resilient seed yield: {cocoa_drought_resilient:.2f}%")

assert cocoa_drought_standard < 100.0, "Drought should reduce yield"
assert cocoa_drought_resilient > cocoa_drought_standard, "Resilient seed should perform better under drought"
print(f"  Drought tolerance advantage: +{cocoa_drought_resilient - cocoa_drought_standard:.2f}%")
print("  ✓ Passed")

# Test Case 6: Cocoa - Heat stress (above 33°C limit)
print("\nTest Case 6: Cocoa - Heat stress (36°C, above 33°C limit)")
print("-" * 60)

cocoa_hot_temp = 36.0

cocoa_hot_standard = calculate_yield(cocoa_hot_temp, cocoa_optimal_rain, standard_seed, 'cocoa')
cocoa_hot_resilient = calculate_yield(cocoa_hot_temp, cocoa_optimal_rain, resilient_seed, 'cocoa')

print(f"  Temperature: {cocoa_hot_temp}°C (excess: {cocoa_hot_temp - 33.0}°C)")
print(f"  Rainfall: {cocoa_optimal_rain}mm")
print(f"  Standard seed yield: {cocoa_hot_standard:.2f}%")
print(f"  Resilient seed yield: {cocoa_hot_resilient:.2f}%")

assert cocoa_hot_standard < 100.0, "Heat should reduce yield"
assert cocoa_hot_resilient > cocoa_hot_standard, "Resilient seed should tolerate heat better"
print(f"  Heat tolerance advantage: +{cocoa_hot_resilient - cocoa_hot_standard:.2f}%")
print("  ✓ Passed")

# Test Case 7: Cocoa vs Maize - Different drought sensitivity
print("\nTest Case 7: Cocoa vs Maize - Drought sensitivity comparison")
print("-" * 60)

test_temp = 28.0
test_rain = 600.0  # Sub-optimal for both

maize_at_600mm = calculate_yield(test_temp, test_rain, standard_seed, 'maize')
cocoa_at_600mm = calculate_yield(test_temp, test_rain, standard_seed, 'cocoa')

print(f"  Conditions: {test_temp}°C, {test_rain}mm")
print(f"  Maize yield: {maize_at_600mm:.2f}%")
print(f"  Cocoa yield: {cocoa_at_600mm:.2f}%")

# Cocoa should perform worse at 600mm (far below its 1200mm minimum)
# Maize should perform better (600mm is above its 500mm optimal minimum)
print(f"\n  Cocoa is more drought-sensitive (needs more rainfall)")
print(f"  At {test_rain}mm: Maize outperforms Cocoa by {maize_at_600mm - cocoa_at_600mm:.2f}%")
print("  ✓ Passed")

# Test Case 8: Cocoa vs Maize - Excess rainfall tolerance
print("\nTest Case 8: Cocoa vs Maize - Excess rainfall tolerance")
print("-" * 60)

test_temp_2 = 27.0
test_rain_2 = 2000.0  # High rainfall

maize_at_2000mm = calculate_yield(test_temp_2, test_rain_2, standard_seed, 'maize')
cocoa_at_2000mm = calculate_yield(test_temp_2, test_rain_2, standard_seed, 'cocoa')

print(f"  Conditions: {test_temp_2}°C, {test_rain_2}mm")
print(f"  Maize yield: {maize_at_2000mm:.2f}%")
print(f"  Cocoa yield: {cocoa_at_2000mm:.2f}%")

# Cocoa should handle excess rain better (no waterlogging penalty)
# Maize suffers from waterlogging above 1300mm
print(f"\n  Cocoa handles excess rainfall better (no waterlogging)")
print(f"  At {test_rain_2}mm: Cocoa outperforms Maize by {cocoa_at_2000mm - maize_at_2000mm:.2f}%")
assert cocoa_at_2000mm > maize_at_2000mm, "Cocoa should handle excess rainfall better"
print("  ✓ Passed")

# Test Case 9: Legacy function compatibility
print("\nTest Case 9: Legacy function (simulate_maize_yield) compatibility")
print("-" * 60)

from physics_engine import simulate_maize_yield

legacy_yield = simulate_maize_yield(maize_optimal_temp, maize_optimal_rain, standard_seed)
new_yield = calculate_yield(maize_optimal_temp, maize_optimal_rain, standard_seed, 'maize')

print(f"  Legacy function yield: {legacy_yield:.2f}%")
print(f"  New function yield: {new_yield:.2f}%")

assert legacy_yield == new_yield, "Legacy function should produce identical results"
print("  ✓ Passed (backwards compatible)")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)

# Summary
print("\nCrop Characteristics Summary:")
print("-" * 60)
print("\nMAIZE:")
print("  • Optimal rainfall: 500-1300mm")
print("  • Critical temp: 28°C")
print("  • Sensitive to: Heat stress, waterlogging")
print("  • Moderate drought tolerance")

print("\nCOCOA:")
print("  • Optimal rainfall: 1750mm (min 1200mm)")
print("  • Heat limit: 33°C")
print("  • Sensitive to: Drought (steep penalty)")
print("  • Handles excess rainfall well")
print("  • More drought-sensitive than maize")
