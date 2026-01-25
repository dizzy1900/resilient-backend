# =============================================================================
# Generate Synthetic Training Data for Maize Yield Surrogate Model
# =============================================================================

import csv
import random
from physics_engine import simulate_maize_yield

NUM_SAMPLES = 20000
OUTPUT_FILE = "training_data.csv"

TEMP_MIN = 20.0
TEMP_MAX = 40.0
RAIN_MIN = 100.0
RAIN_MAX = 1500.0


def main():
    random.seed(42)
    
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["temp", "rain", "seed_type", "yield"])
        
        for _ in range(NUM_SAMPLES):
            temp = random.uniform(TEMP_MIN, TEMP_MAX)
            rain = random.uniform(RAIN_MIN, RAIN_MAX)
            seed_type = random.randint(0, 1)
            
            yield_pct = simulate_maize_yield(temp, rain, seed_type)
            
            writer.writerow([round(temp, 2), round(rain, 2), seed_type, round(yield_pct, 4)])
    
    print(f"Generated {NUM_SAMPLES} samples and saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
