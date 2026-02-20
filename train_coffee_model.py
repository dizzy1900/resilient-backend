"""
Train a Random Forest Regressor to predict Arabica coffee yield impacts
based on climate change factors.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib


def generate_synthetic_data(n_samples: int = 10000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate synthetic, biologically accurate training data for Arabica coffee yield prediction.
    
    Features:
        - baseline_temp_c: Baseline temperature (15-28°C)
        - temp_anomaly_c: Temperature anomaly (0-4°C)
        - rainfall_mm: Annual rainfall (800-3000mm)
        - rain_anomaly_mm: Rainfall anomaly (-500 to +500mm)
        - elevation_m: Elevation (400-2500m)
        - soil_ph: Soil pH (4.5-7.5)
    
    Target:
        - yield_impact_pct: Yield impact percentage (0.0-1.0)
    """
    np.random.seed(random_state)
    
    # Generate features
    baseline_temp_c = np.random.uniform(15, 28, n_samples)
    temp_anomaly_c = np.random.uniform(0, 4, n_samples)
    rainfall_mm = np.random.uniform(800, 3000, n_samples)
    rain_anomaly_mm = np.random.uniform(-500, 500, n_samples)
    elevation_m = np.random.uniform(400, 2500, n_samples)
    soil_ph = np.random.uniform(4.5, 7.5, n_samples)
    
    # Calculate derived values
    effective_temp = baseline_temp_c + temp_anomaly_c
    effective_rainfall = rainfall_mm + rain_anomaly_mm
    
    # Initialize yield impact at optimal (1.0)
    yield_impact_pct = np.ones(n_samples)
    
    # Apply biological rules
    
    # 1. Temperature scoring (optimal: 18-21°C)
    temp_score = np.where(
        (effective_temp >= 18) & (effective_temp <= 21),
        1.0,
        np.where(
            effective_temp < 18,
            1.0 - 0.08 * (18 - effective_temp),  # Penalty for cold
            1.0 - 0.12 * (effective_temp - 21)   # Steeper penalty for heat
        )
    )
    
    # 2. Severe non-linear drop when temp > 23°C
    high_temp_penalty = np.where(
        effective_temp > 23,
        np.exp(-0.3 * (effective_temp - 23) ** 1.5),  # Non-linear exponential drop
        1.0
    )
    
    # 3. Elevation scoring (optimal: 1000-2000m)
    elevation_score = np.where(
        (elevation_m >= 1000) & (elevation_m <= 2000),
        1.0,
        np.where(
            elevation_m < 1000,
            0.7 + 0.3 * (elevation_m / 1000),
            1.0 - 0.15 * ((elevation_m - 2000) / 500)
        )
    )
    
    # 4. Rainfall scoring (optimal: 1500-2000mm)
    rainfall_score = np.where(
        (effective_rainfall >= 1500) & (effective_rainfall <= 2000),
        1.0,
        np.where(
            effective_rainfall < 1500,
            0.5 + 0.5 * (effective_rainfall / 1500),
            1.0 - 0.1 * ((effective_rainfall - 2000) / 500)
        )
    )
    
    # 5. Soil pH scoring (optimal: 6.0-6.5)
    ph_score = np.where(
        (soil_ph >= 6.0) & (soil_ph <= 6.5),
        1.0,
        1.0 - 0.1 * np.minimum(np.abs(soil_ph - 6.25), 2.0)
    )
    
    # 6. Critical condition: Low elevation + High temp → near 0.2 yield
    critical_stress = (elevation_m < 800) & (effective_temp > 22)
    critical_penalty = np.where(critical_stress, 0.2, 1.0)
    
    # Combine all factors
    yield_impact_pct = (
        temp_score * 
        high_temp_penalty * 
        elevation_score * 
        rainfall_score * 
        ph_score * 
        critical_penalty
    )
    
    # Clip to valid range and add slight noise for realism
    noise = np.random.normal(0, 0.02, n_samples)
    yield_impact_pct = np.clip(yield_impact_pct + noise, 0.0, 1.0)
    
    # Create DataFrame
    df = pd.DataFrame({
        'baseline_temp_c': baseline_temp_c,
        'temp_anomaly_c': temp_anomaly_c,
        'rainfall_mm': rainfall_mm,
        'rain_anomaly_mm': rain_anomaly_mm,
        'elevation_m': elevation_m,
        'soil_ph': soil_ph,
        'yield_impact_pct': yield_impact_pct
    })
    
    return df


def main():
    print("=" * 60)
    print("Arabica Coffee Yield Impact Prediction Model Training")
    print("=" * 60)
    
    # Step 1: Generate synthetic data
    print("\n[Step 1] Generating 10,000 rows of synthetic training data...")
    df = generate_synthetic_data(n_samples=10000, random_state=42)
    print(f"  Data shape: {df.shape}")
    print(f"  Target range: [{df['yield_impact_pct'].min():.3f}, {df['yield_impact_pct'].max():.3f}]")
    print(f"  Target mean: {df['yield_impact_pct'].mean():.3f}")
    
    # Prepare features and target
    feature_cols = [
        'baseline_temp_c', 'temp_anomaly_c', 'rainfall_mm',
        'rain_anomaly_mm', 'elevation_m', 'soil_ph'
    ]
    X = df[feature_cols]
    y = df['yield_impact_pct']
    
    # Step 2: Split data (80/20)
    print("\n[Step 2] Splitting data into train/test sets (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  Training samples: {len(X_train)}")
    print(f"  Test samples: {len(X_test)}")
    
    # Step 3: Train model
    print("\n[Step 3] Training RandomForestRegressor (n_estimators=100)...")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    print("  Training complete.")
    
    # Step 4: Evaluate model
    print("\n[Step 4] Evaluating model performance...")
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    mae_train = mean_absolute_error(y_train, y_pred_train)
    mae_test = mean_absolute_error(y_test, y_pred_test)
    
    print(f"  MAE (Train): {mae_train:.4f}")
    print(f"  MAE (Test):  {mae_test:.4f}")
    
    # Feature importances
    print("\n  Feature Importances:")
    print("  " + "-" * 40)
    importances = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for _, row in importances.iterrows():
        bar = "█" * int(row['importance'] * 40)
        print(f"  {row['feature']:<18} {row['importance']:.4f} {bar}")
    
    # Step 5: Save model
    model_path = 'coffee_model.pkl'
    print(f"\n[Step 5] Saving model to {model_path}...")
    joblib.dump(model, model_path)
    print(f"  Model saved successfully.")
    
    print("\n" + "=" * 60)
    print("Training pipeline complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
