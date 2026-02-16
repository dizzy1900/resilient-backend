"""
Test the trained coastal runup surrogate model with various scenarios
"""
import numpy as np
import pandas as pd
import pickle

def load_model():
    """Load the trained surrogate model."""
    with open('coastal_surrogate.pkl', 'rb') as f:
        model = pickle.load(f)
    return model

def create_test_scenarios():
    """
    Create diverse test scenarios representing different coastal conditions.
    
    Returns:
    - DataFrame with test scenarios
    """
    scenarios = [
        # Scenario 1: High waves, steep slope, no mangroves
        {
            'scenario': 'High Risk - No Protection',
            'wave_height': 8.0,
            'slope': 0.08,  # 8%
            'mangrove_width_m': 0.0
        },
        # Scenario 2: High waves, steep slope, with mangroves (100m)
        {
            'scenario': 'High Risk - Moderate Mangrove',
            'wave_height': 8.0,
            'slope': 0.08,
            'mangrove_width_m': 100.0
        },
        # Scenario 3: High waves, steep slope, dense mangroves (300m)
        {
            'scenario': 'High Risk - Dense Mangrove',
            'wave_height': 8.0,
            'slope': 0.08,
            'mangrove_width_m': 300.0
        },
        # Scenario 4: Moderate waves, gentle slope, no mangroves
        {
            'scenario': 'Moderate Risk - No Protection',
            'wave_height': 5.0,
            'slope': 0.04,  # 4%
            'mangrove_width_m': 0.0
        },
        # Scenario 5: Moderate waves, gentle slope, with mangroves
        {
            'scenario': 'Moderate Risk - With Mangrove',
            'wave_height': 5.0,
            'slope': 0.04,
            'mangrove_width_m': 150.0
        },
        # Scenario 6: Low waves, gentle slope, no mangroves
        {
            'scenario': 'Low Risk - No Protection',
            'wave_height': 2.0,
            'slope': 0.02,  # 2%
            'mangrove_width_m': 0.0
        },
        # Scenario 7: Extreme waves, steep slope, extensive mangroves
        {
            'scenario': 'Extreme Event - Max Protection',
            'wave_height': 10.0,
            'slope': 0.10,  # 10%
            'mangrove_width_m': 500.0
        },
        # Scenario 8: Custom test case
        {
            'scenario': 'Custom - Medium Conditions',
            'wave_height': 6.5,
            'slope': 0.055,  # 5.5%
            'mangrove_width_m': 200.0
        }
    ]
    
    return pd.DataFrame(scenarios)

def predict_runup(model, test_data):
    """
    Make predictions using the trained model.
    
    Parameters:
    - model: Trained surrogate model
    - test_data: DataFrame with test scenarios
    
    Returns:
    - DataFrame with predictions
    """
    # Extract features for prediction
    X_test = test_data[['wave_height', 'slope', 'mangrove_width_m']].values
    
    # Make predictions
    predictions = model.predict(X_test)
    
    # Add predictions to dataframe
    results = test_data.copy()
    results['predicted_runup_m'] = predictions
    
    return results

def display_results(results):
    """Display prediction results in a formatted table."""
    print("=" * 100)
    print("COASTAL RUNUP SURROGATE MODEL - TEST RESULTS")
    print("=" * 100)
    print()
    
    for idx, row in results.iterrows():
        print(f"Scenario {idx + 1}: {row['scenario']}")
        print(f"  Wave Height:      {row['wave_height']:.1f} m")
        print(f"  Slope:            {row['slope']*100:.1f}%")
        print(f"  Mangrove Width:   {row['mangrove_width_m']:.0f} m")
        print(f"  → Predicted Runup: {row['predicted_runup_m']:.4f} m")
        print()
    
    print("=" * 100)
    print("SUMMARY STATISTICS")
    print("=" * 100)
    print(f"  Average predicted runup:  {results['predicted_runup_m'].mean():.4f} m")
    print(f"  Min predicted runup:      {results['predicted_runup_m'].min():.4f} m")
    print(f"  Max predicted runup:      {results['predicted_runup_m'].max():.4f} m")
    print()
    
    # Analyze mangrove protection effect
    print("=" * 100)
    print("MANGROVE PROTECTION ANALYSIS")
    print("=" * 100)
    
    # Compare scenarios 1, 2, 3 (same conditions, different mangrove widths)
    if len(results) >= 3:
        no_mangrove = results.iloc[0]['predicted_runup_m']
        moderate_mangrove = results.iloc[1]['predicted_runup_m']
        dense_mangrove = results.iloc[2]['predicted_runup_m']
        
        reduction_moderate = (1 - moderate_mangrove / no_mangrove) * 100
        reduction_dense = (1 - dense_mangrove / no_mangrove) * 100
        
        print(f"  Baseline (no mangrove):        {no_mangrove:.4f} m")
        print(f"  With 100m mangrove:            {moderate_mangrove:.4f} m ({reduction_moderate:.1f}% reduction)")
        print(f"  With 300m mangrove:            {dense_mangrove:.4f} m ({reduction_dense:.1f}% reduction)")
        print()
    
    print("=" * 100)

def main():
    """Main testing pipeline."""
    print("\n🌊 Loading coastal surrogate model...")
    model = load_model()
    print("✓ Model loaded successfully!")
    print(f"  Model type: {type(model).__name__}")
    print(f"  Number of estimators: {model.n_estimators}")
    print()
    
    print("📊 Creating test scenarios...")
    test_data = create_test_scenarios()
    print(f"✓ Created {len(test_data)} test scenarios")
    print()
    
    print("🔮 Making predictions...")
    results = predict_runup(model, test_data)
    print("✓ Predictions complete!")
    print()
    
    # Display results
    display_results(results)
    
    # Save results
    results.to_csv('coastal_test_results.csv', index=False)
    print("💾 Results saved to coastal_test_results.csv")
    print()

if __name__ == "__main__":
    main()
