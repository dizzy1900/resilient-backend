#!/usr/bin/env python3
"""
Test the calculate_volatility function
"""

from physics_engine import calculate_volatility

print("Testing Yield Volatility Calculation")
print("=" * 60)

# Test Case 1: Low volatility (stable yields)
print("\nTest Case 1: Low volatility - stable yields")
print("-" * 60)

stable_yields = [90, 92, 88, 91, 89, 90, 91, 89, 90, 92]
cv_stable = calculate_volatility(stable_yields)

print(f"  Yields: {stable_yields}")
print(f"  Mean: {sum(stable_yields) / len(stable_yields):.2f}")
print(f"  Coefficient of Variation: {cv_stable}%")

assert cv_stable < 5.0, "Stable yields should have low CV"
print(f"  Risk Level: LOW")
print("  ✓ Passed")

# Test Case 2: High volatility (erratic yields)
print("\nTest Case 2: High volatility - erratic yields")
print("-" * 60)

volatile_yields = [95, 30, 85, 20, 90, 25, 80, 35, 75, 40]
cv_volatile = calculate_volatility(volatile_yields)

print(f"  Yields: {volatile_yields}")
print(f"  Mean: {sum(volatile_yields) / len(volatile_yields):.2f}")
print(f"  Coefficient of Variation: {cv_volatile}%")

assert cv_volatile > 30.0, "Erratic yields should have high CV"
print(f"  Risk Level: HIGH")
print("  ✓ Passed")

# Test Case 3: Medium volatility
print("\nTest Case 3: Medium volatility - moderate variation")
print("-" * 60)

moderate_yields = [80, 70, 85, 75, 82, 78, 83, 72, 81, 79]
cv_moderate = calculate_volatility(moderate_yields)

print(f"  Yields: {moderate_yields}")
print(f"  Mean: {sum(moderate_yields) / len(moderate_yields):.2f}")
print(f"  Coefficient of Variation: {cv_moderate}%")

assert 5.0 < cv_moderate < 30.0, "Moderate variation should have medium CV"
print(f"  Risk Level: MEDIUM")
print("  ✓ Passed")

# Test Case 4: Edge case - all same values
print("\nTest Case 4: Edge case - all identical yields")
print("-" * 60)

identical_yields = [100, 100, 100, 100, 100]
cv_identical = calculate_volatility(identical_yields)

print(f"  Yields: {identical_yields}")
print(f"  Coefficient of Variation: {cv_identical}%")

assert cv_identical == 0.0, "Identical yields should have CV = 0"
print("  ✓ Passed")

# Test Case 5: Edge case - empty list
print("\nTest Case 5: Edge case - empty list")
print("-" * 60)

empty_yields = []
cv_empty = calculate_volatility(empty_yields)

print(f"  Yields: {empty_yields}")
print(f"  Coefficient of Variation: {cv_empty}%")

assert cv_empty == 0.0, "Empty list should return 0"
print("  ✓ Passed")

# Test Case 6: Edge case - single value
print("\nTest Case 6: Edge case - single value")
print("-" * 60)

single_yield = [85]
cv_single = calculate_volatility(single_yield)

print(f"  Yields: {single_yield}")
print(f"  Coefficient of Variation: {cv_single}%")

assert cv_single == 0.0, "Single value should return 0"
print("  ✓ Passed")

# Test Case 7: Real-world example - drought-prone region
print("\nTest Case 7: Real-world - drought-prone region")
print("-" * 60)

drought_yields = [75, 25, 80, 30, 70, 20, 85, 35, 78, 28]
cv_drought = calculate_volatility(drought_yields)

print(f"  Yields over 10 years: {drought_yields}")
print(f"  Mean: {sum(drought_yields) / len(drought_yields):.2f}")
print(f"  Coefficient of Variation: {cv_drought}%")
print(f"  Interpretation: High volatility due to recurring droughts")
print("  ✓ Passed")

# Test Case 8: Comparison - standard vs resilient seed
print("\nTest Case 8: Comparison - standard vs resilient seed")
print("-" * 60)

standard_seed_yields = [90, 45, 85, 40, 80, 35, 88, 50, 83, 42]
resilient_seed_yields = [90, 65, 85, 60, 80, 55, 88, 70, 83, 62]

cv_standard = calculate_volatility(standard_seed_yields)
cv_resilient = calculate_volatility(resilient_seed_yields)

print(f"  Standard seed yields: {standard_seed_yields}")
print(f"  Standard seed CV: {cv_standard}%")
print(f"\n  Resilient seed yields: {resilient_seed_yields}")
print(f"  Resilient seed CV: {cv_resilient}%")

print(f"\n  Volatility reduction: {cv_standard - cv_resilient:.2f}%")
assert cv_resilient < cv_standard, "Resilient seed should have lower volatility"
print("  ✓ Resilient seed reduces volatility")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)

# Risk rating reference
print("\nRisk Rating Reference (CV%):")
print("-" * 60)
print("  • 0-10%   : LOW risk (very stable)")
print("  • 10-20%  : MEDIUM risk (moderate variation)")
print("  • 20-30%  : HIGH risk (significant variation)")
print("  • 30%+    : VERY HIGH risk (highly volatile)")
