import pickle
import numpy as np

# Load the trained model
with open('ag_surrogate.pkl', 'rb') as f:
    model = pickle.load(f)

# Hot/Dry scenario: Temp=35, Rain=400
temp = 35
rain = 400

# Predict for seed_type=0
X_seed0 = np.array([[temp, rain, 0]])
yield_seed0 = model.predict(X_seed0)[0]

# Predict for seed_type=1
X_seed1 = np.array([[temp, rain, 1]])
yield_seed1 = model.predict(X_seed1)[0]

# Calculate avoided loss (assuming higher yield = lower loss)
avoided_loss = yield_seed1 - yield_seed0

print(f"Hot/Dry Scenario (Temp={temp}°C, Rain={rain}mm)")
print(f"Yield with seed_type=0: {yield_seed0:.2f}")
print(f"Yield with seed_type=1: {yield_seed1:.2f}")
print(f"Avoided Loss (difference): {avoided_loss:.2f}")
