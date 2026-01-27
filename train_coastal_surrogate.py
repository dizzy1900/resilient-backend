"""
Coastal Runup Surrogate Model Training
Based on Stockdon equation with mangrove attenuation
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import warnings
warnings.filterwarnings('ignore')


def generate_synthetic_data(n_samples=10000):
    """
    Generate synthetic coastal transect data.
    
    Parameters:
    - n_samples: Number of samples to generate
    
    Returns:
    - DataFrame with features and target
    """
    np.random.seed(42)
    
    # Generate random inputs
    wave_height = np.random.uniform(1.0, 10.0, n_samples)  # 1-10 meters
    slope = np.random.uniform(1.0, 10.0, n_samples) / 100.0  # 1-10% as decimal
    mangrove_width_m = np.random.uniform(0.0, 500.0, n_samples)  # 0-500 meters
    
    # Create DataFrame
    data = pd.DataFrame({
        'wave_height': wave_height,
        'slope': slope,
        'mangrove_width_m': mangrove_width_m
    })
    
    return data


def calculate_runup_physics(data):
    """
    Calculate runup elevation using Stockdon equation with mangrove attenuation.
    
    Parameters:
    - data: DataFrame with wave_height, slope, mangrove_width_m columns
    
    Returns:
    - Series with runup_elevation values
    """
    # Base runup using Stockdon equation: R = 0.71 * slope * H
    base_runup = 0.71 * data['slope'] * data['wave_height']
    
    # Apply mangrove attenuation
    # Dense mangrove forest (Rhizophora): 40-50% reduction per 100m width
    # Using 45% as the typical value for dense forest
    attenuation_rate = 0.45  # 45% reduction per 100m
    
    # Calculate attenuation factor based on mangrove width
    # For every 100m of mangrove, reduce runup by 45%
    # Formula: runup * (1 - attenuation_rate)^(width / 100)
    attenuation_factor = np.power(1 - attenuation_rate, data['mangrove_width_m'] / 100.0)
    
    # Final runup with attenuation
    runup_elevation = base_runup * attenuation_factor
    
    return runup_elevation


def train_surrogate_model(X, y):
    """
    Train a Random Forest Regressor to predict runup elevation.
    
    Parameters:
    - X: Feature matrix
    - y: Target vector (runup_elevation)
    
    Returns:
    - Trained model and metrics
    """
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train Random Forest
    rf_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train, y_train)
    
    # Evaluate
    y_pred_train = rf_model.predict(X_train)
    y_pred_test = rf_model.predict(X_test)
    
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    print(f"\nModel Performance:")
    print(f"  Training R²: {train_r2:.4f}")
    print(f"  Test R²: {test_r2:.4f}")
    print(f"  Test RMSE: {test_rmse:.4f} meters")
    
    return rf_model


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("Coastal Runup Surrogate Model Training")
    print("=" * 60)
    
    # Step 1: Generate synthetic data
    print("\n[1/4] Generating 10,000 synthetic coastal transects...")
    data = generate_synthetic_data(n_samples=10000)
    print(f"    Generated {len(data)} samples")
    print(f"    Features: wave_height, slope, mangrove_width_m")
    
    # Step 2: Calculate runup using physics
    print("\n[2/4] Calculating runup elevation using physics...")
    runup_elevation = calculate_runup_physics(data)
    data['runup_elevation'] = runup_elevation
    
    print(f"    Runup range: {runup_elevation.min():.3f} - {runup_elevation.max():.3f} meters")
    print(f"    Mean runup: {runup_elevation.mean():.3f} meters")
    
    # Show effect of mangrove attenuation
    with_mangrove = data[data['mangrove_width_m'] > 0]
    without_mangrove = data[data['mangrove_width_m'] == 0]
    if len(without_mangrove) > 0:
        avg_runup_no_mangrove = without_mangrove['runup_elevation'].mean()
        avg_runup_with_mangrove = with_mangrove['runup_elevation'].mean()
        reduction = (1 - avg_runup_with_mangrove / avg_runup_no_mangrove) * 100
        print(f"    Mangrove attenuation: {reduction:.1f}% average reduction")
    
    # Step 3: Train model
    print("\n[3/4] Training Random Forest Regressor...")
    X = data[['wave_height', 'slope', 'mangrove_width_m']].values
    y = data['runup_elevation'].values
    
    model = train_surrogate_model(X, y)
    
    # Step 4: Save model
    print("\n[4/4] Saving model to coastal_surrogate.pkl...")
    with open('coastal_surrogate.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    print("    ✓ Model saved successfully!")
    
    # Save training data for reference
    data.to_csv('coastal_training_data.csv', index=False)
    print("    \nTraining data saved to coastal_training_data.csv")
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
