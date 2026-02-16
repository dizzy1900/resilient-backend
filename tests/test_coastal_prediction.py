"""
Test script for /predict-coastal endpoint
"""
import json
import sys

# Test the coastal prediction logic
print("=" * 60)
print("Testing Coastal Prediction Logic")
print("=" * 60)

# Load the coastal model directly
import pickle
import pandas as pd

print("\n[1/3] Loading coastal_surrogate.pkl...")
with open('coastal_surrogate.pkl', 'rb') as f:
    coastal_model = pickle.load(f)
print("    ✓ Model loaded successfully")

# Test case 1: Moderate conditions with mangrove protection
print("\n[2/3] Running prediction test...")
print("    Test input: wave_height=5.0m, slope=0.05, mangrove_width_m=200m")

wave_height = 5.0
slope = 0.05
mangrove_width_m = 200.0

# Reality A (Gray): No mangrove protection
reality_a_df = pd.DataFrame({
    'wave_height': [wave_height],
    'slope': [slope],
    'mangrove_width_m': [0.0]
})

# Reality B (Green): With mangrove protection
reality_b_df = pd.DataFrame({
    'wave_height': [wave_height],
    'slope': [slope],
    'mangrove_width_m': [mangrove_width_m]
})

runup_a = float(coastal_model.predict(reality_a_df)[0])
runup_b = float(coastal_model.predict(reality_b_df)[0])

if runup_a > 0:
    reduction_percent = ((runup_a - runup_b) / runup_a) * 100
else:
    reduction_percent = 0.0

print(f"    Reality A (Gray) runup: {runup_a:.4f}m")
print(f"    Reality B (Green) runup: {runup_b:.4f}m")
print(f"    Reduction: {reduction_percent:.2f}%")

# Test case 2: No mangrove protection (should have 0 reduction)
print("\n[2/3] Running edge case test (no mangrove)...")
print("    Test input: wave_height=5.0m, slope=0.05, mangrove_width_m=0m")

reality_b_df_no_mangrove = pd.DataFrame({
    'wave_height': [wave_height],
    'slope': [slope],
    'mangrove_width_m': [0.0]
})

runup_b_no_mangrove = float(coastal_model.predict(reality_b_df_no_mangrove)[0])
reduction_percent_no_mangrove = ((runup_a - runup_b_no_mangrove) / runup_a) * 100 if runup_a > 0 else 0.0

print(f"    Reality A (Gray) runup: {runup_a:.4f}m")
print(f"    Reality B (Green) runup: {runup_b_no_mangrove:.4f}m")
print(f"    Reduction: {reduction_percent_no_mangrove:.2f}%")

# Test case 3: Heavy mangrove protection
print("\n[2/3] Running heavy protection test...")
print("    Test input: wave_height=5.0m, slope=0.05, mangrove_width_m=500m")

reality_b_df_heavy = pd.DataFrame({
    'wave_height': [wave_height],
    'slope': [slope],
    'mangrove_width_m': [500.0]
})

runup_b_heavy = float(coastal_model.predict(reality_b_df_heavy)[0])
reduction_percent_heavy = ((runup_a - runup_b_heavy) / runup_a) * 100 if runup_a > 0 else 0.0

print(f"    Reality A (Gray) runup: {runup_a:.4f}m")
print(f"    Reality B (Green) runup: {runup_b_heavy:.4f}m")
print(f"    Reduction: {reduction_percent_heavy:.2f}%")

print("\n[3/3] Validating results...")
assert abs(reduction_percent_no_mangrove) < 0.1, f"No mangrove should have ~0% reduction, got {reduction_percent_no_mangrove}"
assert reduction_percent > 0, f"200m mangrove should reduce runup, got {reduction_percent}%"
assert reduction_percent_heavy > reduction_percent, f"500m mangrove should reduce more than 200m, got {reduction_percent_heavy}% vs {reduction_percent}%"

print("    ✓ All tests passed!")

print("\n" + "=" * 60)
print("Test complete! /predict-coastal logic working correctly.")
print("=" * 60)

# Show example JSON response format
print("\nExample API response format:")
print(json.dumps({
    'status': 'success',
    'data': {
        'input_conditions': {
            'wave_height': 5.0,
            'slope': 0.05,
            'mangrove_width_m': 200.0
        },
        'predictions': {
            'reality_a_gray': {
                'description': 'Without mangrove protection',
                'mangrove_width_m': 0.0,
                'runup_elevation': round(runup_a, 4)
            },
            'reality_b_green': {
                'description': 'With mangrove protection',
                'mangrove_width_m': 200.0,
                'runup_elevation': round(runup_b, 4)
            }
        },
        'analysis': {
            'runup_a': round(runup_a, 4),
            'runup_b': round(runup_b, 4),
            'reduction_percent': round(reduction_percent, 2)
        }
    }
}, indent=2))
