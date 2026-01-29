"""
Train Flood Surrogate Model using Rational Method
Based on Urban Flood Model Parameters with dynamic composite C-value calculation
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import pickle

# Runoff Coefficients from EPA SWMM / Urban Flood Model Parameters
C_CONCRETE = 0.95  # Standard asphalt/concrete (impervious)
C_GREEN = 0.10     # Grass/pervious surfaces

# Manning's n for simplified depth calculation
MANNINGS_N = 0.016  # Smooth asphalt/concrete channel

# Standard assumptions for simplified Manning's equation
CHANNEL_WIDTH_M = 10.0  # Assumed channel width in meters
SLOPE_DEFAULT = 0.01    # Default channel slope (1%)


def calculate_composite_runoff_coefficient(impervious_pct):
    """
    Calculate composite runoff coefficient based on impervious percentage.
    
    C_composite = (C_concrete × impervious_pct) + (C_green × pervious_pct)
    
    Args:
        impervious_pct: Fraction of impervious area (0.0 to 1.0)
    
    Returns:
        Composite runoff coefficient
    """
    pervious_pct = 1.0 - impervious_pct
    return (C_CONCRETE * impervious_pct) + (C_GREEN * pervious_pct)


def rational_method_peak_flow(rain_intensity_mm_hr, composite_c, area_ha=1.0):
    """
    Calculate peak runoff using Rational Method: Q = C * I * A
    
    Args:
        rain_intensity_mm_hr: Rainfall intensity in mm/hr
        composite_c: Composite runoff coefficient
        area_ha: Catchment area in hectares (default 1.0)
    
    Returns:
        Peak flow in cubic meters per second (m³/s)
    """
    # Convert mm/hr to m/s
    rain_intensity_m_s = (rain_intensity_mm_hr / 1000.0) / 3600.0
    
    # Convert hectares to m²
    area_m2 = area_ha * 10000.0
    
    # Q = C * I * A
    q_m3_s = composite_c * rain_intensity_m_s * area_m2
    
    return q_m3_s


def calculate_flood_depth(q_m3_s, slope_pct, width_m=CHANNEL_WIDTH_M, n=MANNINGS_N):
    """
    Calculate flood depth using simplified Manning's equation.
    
    Manning's equation: Q = (1/n) * A * R^(2/3) * S^(1/2)
    For rectangular channel: R ≈ depth for shallow wide channels
    Simplified: depth ≈ (Q * n / (width * S^(1/2)))^(3/5)
    
    Args:
        q_m3_s: Peak flow in m³/s
        slope_pct: Channel slope as percentage (0-10)
        width_m: Channel width in meters
        n: Manning's roughness coefficient
    
    Returns:
        Flood depth in centimeters
    """
    # Convert slope percentage to decimal
    slope = slope_pct / 100.0
    
    # Avoid division by zero
    if slope <= 0:
        slope = SLOPE_DEFAULT
    
    # Simplified Manning's equation for depth
    # depth = (Q * n / (width * sqrt(S)))^(3/5)
    depth_m = (q_m3_s * n / (width_m * np.sqrt(slope))) ** (3.0 / 5.0)
    
    # Convert to centimeters
    depth_cm = depth_m * 100.0
    
    return depth_cm


def generate_synthetic_flood_data(n_samples=20000):
    """
    Generate synthetic catchment scenarios using physics-based calculations.
    
    Args:
        n_samples: Number of synthetic samples to generate
    
    Returns:
        DataFrame with inputs and physics-based target
    """
    np.random.seed(42)
    
    # Generate random inputs
    rain_intensity_mm_hr = np.random.uniform(10, 150, n_samples)
    impervious_pct = np.random.uniform(0.0, 1.0, n_samples)
    slope_pct = np.random.uniform(0.1, 10.0, n_samples)  # Avoid zero slope
    
    # Calculate physics-based targets
    flood_depth_cm = np.zeros(n_samples)
    
    for i in range(n_samples):
        # Calculate composite runoff coefficient dynamically
        c_composite = calculate_composite_runoff_coefficient(impervious_pct[i])
        
        # Apply Rational Method
        q = rational_method_peak_flow(rain_intensity_mm_hr[i], c_composite)
        
        # Calculate flood depth using Manning's equation
        depth = calculate_flood_depth(q, slope_pct[i])
        
        flood_depth_cm[i] = depth
    
    # Create DataFrame
    df = pd.DataFrame({
        'rain_intensity_mm_hr': rain_intensity_mm_hr,
        'impervious_pct': impervious_pct,
        'slope_pct': slope_pct,
        'flood_depth_cm': flood_depth_cm
    })
    
    return df


def train_flood_surrogate():
    """
    Train RandomForestRegressor to predict flood depth from catchment parameters.
    """
    print("=" * 60)
    print("Training Flood Surrogate Model")
    print("=" * 60)
    
    # Generate synthetic data
    print("\n1. Generating 20,000 synthetic catchment scenarios...")
    df = generate_synthetic_flood_data(n_samples=20000)
    
    print(f"   Generated {len(df)} samples")
    print(f"\n   Input ranges:")
    print(f"   - Rain intensity: {df['rain_intensity_mm_hr'].min():.1f} - {df['rain_intensity_mm_hr'].max():.1f} mm/hr")
    print(f"   - Impervious %:   {df['impervious_pct'].min():.2f} - {df['impervious_pct'].max():.2f}")
    print(f"   - Slope %:        {df['slope_pct'].min():.2f} - {df['slope_pct'].max():.2f}")
    print(f"\n   Target range:")
    print(f"   - Flood depth:    {df['flood_depth_cm'].min():.2f} - {df['flood_depth_cm'].max():.2f} cm")
    
    # Prepare features and target
    X = df[['rain_intensity_mm_hr', 'impervious_pct', 'slope_pct']].values
    y = df['flood_depth_cm'].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    print("\n2. Training RandomForestRegressor...")
    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    print("\n3. Evaluating model performance...")
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    print(f"\n   Training Metrics:")
    print(f"   - R² Score: {train_r2:.4f}")
    print(f"   - MAE:      {train_mae:.4f} cm")
    print(f"   - RMSE:     {train_rmse:.4f} cm")
    
    print(f"\n   Test Metrics:")
    print(f"   - R² Score: {test_r2:.4f}")
    print(f"   - MAE:      {test_mae:.4f} cm")
    print(f"   - RMSE:     {test_rmse:.4f} cm")
    
    # Feature importance
    print("\n4. Feature Importance:")
    feature_names = ['rain_intensity_mm_hr', 'impervious_pct', 'slope_pct']
    for name, importance in zip(feature_names, model.feature_importances_):
        print(f"   - {name:25s}: {importance:.4f}")
    
    # Save model
    print("\n5. Saving model to flood_surrogate.pkl...")
    with open('flood_surrogate.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    print("\n✓ Training complete!")
    print("=" * 60)
    
    return model, df


if __name__ == "__main__":
    model, data = train_flood_surrogate()
    
    # Test prediction
    print("\n" + "=" * 60)
    print("Test Prediction Example")
    print("=" * 60)
    
    test_input = np.array([[100.0, 0.7, 2.0]])  # rain=100mm/hr, 70% impervious, 2% slope
    prediction = model.predict(test_input)[0]
    
    print(f"\nInput:")
    print(f"  - Rain intensity: 100.0 mm/hr")
    print(f"  - Impervious:     70%")
    print(f"  - Slope:          2%")
    print(f"\nPredicted flood depth: {prediction:.2f} cm")
