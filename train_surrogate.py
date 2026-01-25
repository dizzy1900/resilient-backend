# =============================================================================
# Train Surrogate Model for Maize Yield Prediction
# =============================================================================

import pickle
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

INPUT_FILE = "training_data.csv"
MODEL_FILE = "ag_surrogate.pkl"


def main():
    # Load training data
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} samples from {INPUT_FILE}")
    
    # Prepare features and target
    X = df[["temp", "rain", "seed_type"]]
    y = df["yield"]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    print(f"Mean Absolute Error: {mae:.4f}")
    
    # Save model
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model, f)
    print(f"Model saved to {MODEL_FILE}")


if __name__ == "__main__":
    main()
