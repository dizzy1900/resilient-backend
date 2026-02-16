"""
Test the flood prediction logic directly without the API
"""

import pickle
import pandas as pd
import numpy as np

# Load the flood model
print("Loading flood model...")
with open('flood_surrogate.pkl', 'rb') as f:
    flood_model = pickle.load(f)

print("Model loaded successfully!\n")

# Define intervention factors
INTERVENTION_FACTORS = {
    'green_roof': 0.30,
    'permeable_pavement': 0.40,
    'bioswales': 0.25,
    'rain_gardens': 0.20,
    'none': 0.0
}

def test_flood_prediction(rain_intensity, current_imperviousness, intervention_type, slope_pct=2.0):
    """Test flood prediction with intervention."""
    
    print("=" * 60)
    print(f"Test: {intervention_type.upper()}")
    print("=" * 60)
    
    # Scenario A (Baseline)
    baseline_df = pd.DataFrame({
        'rain_intensity_mm_hr': [rain_intensity],
        'impervious_pct': [current_imperviousness],
        'slope_pct': [slope_pct]
    })
    
    # Scenario B (Intervention)
    reduction_factor = INTERVENTION_FACTORS[intervention_type]
    intervention_imperviousness = max(0.0, current_imperviousness - reduction_factor)
    
    intervention_df = pd.DataFrame({
        'rain_intensity_mm_hr': [rain_intensity],
        'impervious_pct': [intervention_imperviousness],
        'slope_pct': [slope_pct]
    })
    
    # Predictions
    depth_baseline = float(flood_model.predict(baseline_df)[0])
    depth_intervention = float(flood_model.predict(intervention_df)[0])
    avoided_depth_cm = depth_baseline - depth_intervention
    percentage_improvement = (avoided_depth_cm / depth_baseline * 100) if depth_baseline > 0 else 0
    
    # Calculate damage using FEMA HAZUS
    import math
    
    def calculate_damage_pct(depth_cm):
        depth_ft = depth_cm / 30.48
        if depth_ft <= 0:
            return 0.0
        damage_pct = 0.72 * (1 - math.exp(-0.1332 * depth_ft))
        return min(damage_pct, 1.0) * 100
    
    baseline_damage = calculate_damage_pct(depth_baseline)
    intervention_damage = calculate_damage_pct(depth_intervention)
    avoided_damage_pct = baseline_damage - intervention_damage
    
    # Economic value
    NUM_BUILDINGS = 50
    AVG_BUILDING_VALUE = 500000
    avoided_damage_usd = (avoided_damage_pct / 100) * NUM_BUILDINGS * AVG_BUILDING_VALUE
    
    # Print results
    print(f"\nInputs:")
    print(f"  Rain Intensity:      {rain_intensity} mm/hr")
    print(f"  Current Impervious:  {current_imperviousness * 100:.1f}%")
    print(f"  Intervention Type:   {intervention_type}")
    print(f"  Slope:               {slope_pct}%")
    
    print(f"\nImperviousness Change:")
    print(f"  Baseline:            {current_imperviousness * 100:.1f}%")
    print(f"  After Intervention:  {intervention_imperviousness * 100:.1f}%")
    print(f"  Reduction:           {(current_imperviousness - intervention_imperviousness) * 100:.1f}%")
    
    print(f"\nFlood Depth Predictions:")
    print(f"  Baseline:            {depth_baseline:.2f} cm")
    print(f"  With Intervention:   {depth_intervention:.2f} cm")
    print(f"  Avoided Depth:       {avoided_depth_cm:.2f} cm")
    print(f"  Improvement:         {percentage_improvement:.1f}%")
    
    print(f"\nDamage Analysis:")
    print(f"  Baseline Damage:     {baseline_damage:.2f}%")
    print(f"  Intervention Damage: {intervention_damage:.2f}%")
    print(f"  Avoided Damage:      {avoided_damage_pct:.2f}%")
    
    print(f"\nEconomic Value:")
    print(f"  Avoided Loss:        ${avoided_damage_usd:,.2f}")
    print(f"  (Based on {NUM_BUILDINGS} buildings @ ${AVG_BUILDING_VALUE:,} each)")
    
    return {
        'depth_baseline': depth_baseline,
        'depth_intervention': depth_intervention,
        'avoided_depth': avoided_depth_cm,
        'avoided_loss': avoided_damage_usd
    }


# Run test cases
print("\n" + "=" * 60)
print("FLOOD PREDICTION TESTS")
print("=" * 60 + "\n")

# Test 1: Green Roof
test1 = test_flood_prediction(
    rain_intensity=100.0,
    current_imperviousness=0.7,
    intervention_type='green_roof',
    slope_pct=2.0
)

print("\n")

# Test 2: Permeable Pavement
test2 = test_flood_prediction(
    rain_intensity=80.0,
    current_imperviousness=0.8,
    intervention_type='permeable_pavement',
    slope_pct=3.0
)

print("\n")

# Test 3: Rain Gardens
test3 = test_flood_prediction(
    rain_intensity=120.0,
    current_imperviousness=0.6,
    intervention_type='rain_gardens',
    slope_pct=1.5
)

print("\n")

# Test 4: No Intervention (should show zero difference)
test4 = test_flood_prediction(
    rain_intensity=50.0,
    current_imperviousness=0.5,
    intervention_type='none',
    slope_pct=2.0
)

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"\n1. Green Roof:           Avoided ${test1['avoided_loss']:,.2f}")
print(f"2. Permeable Pavement:   Avoided ${test2['avoided_loss']:,.2f}")
print(f"3. Rain Gardens:         Avoided ${test3['avoided_loss']:,.2f}")
print(f"4. No Intervention:      Avoided ${test4['avoided_loss']:,.2f}")
print("\n✓ All tests completed successfully!")
