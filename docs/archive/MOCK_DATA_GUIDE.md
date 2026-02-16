# Mock Data Mode for Cloud Agent Testing

## Overview

The mock data system allows Cloud Agents to run thousands of tests per minute **without hitting the Google Earth Engine API**. This is essential for Code Fortification sprints, unit testing, and load testing.

## Problem Statement

**Before Mock Data:**
- Each test hits Google Earth Engine API
- Rate limits: ~1,000 requests per day
- Slow response times (2-5 seconds per request)
- Requires GEE credentials
- External dependency failures

**With Mock Data:**
- Zero API calls
- Unlimited test runs
- Instant response (<0.1s per request)
- No credentials needed
- Fully deterministic results

## Architecture

### Components

1. **`mock_data.py`** - Mock data generator
   - Deterministic weather data based on lat/lon
   - Realistic climate zone modeling
   - Reproducible results (same input = same output)

2. **`headless_runner.py --use-mock-data`** - CLI flag
   - Bypasses GEE entirely
   - Uses mock data for all calculations
   - Safe for high-volume testing

3. **`test_mock_mode.sh`** - Validation script
   - Tests reproducibility
   - Validates high-volume scenarios
   - Compares mock vs fallback modes

## Quick Start

### Basic Usage

```bash
# Run with mock data (no GEE API calls)
python headless_runner.py \
  --lat 40.7 \
  --lon -74.0 \
  --scenario_year 2050 \
  --project_type agriculture \
  --use-mock-data
```

### Output Comparison

**With Mock Data:**
```json
{
  "climate_conditions": {
    "temperature_c": 13.8,
    "rainfall_mm": 1143.1,
    "data_source": "mock_data",
    "climate_zone": "temperate"
  }
}
```

**Without Mock Data (GEE or fallback):**
```json
{
  "climate_conditions": {
    "temperature_c": 20.0,
    "rainfall_mm": 700.0,
    "data_source": "fallback_climate_zone"
  }
}
```

## Mock Data Features

### 1. Deterministic Results

Same coordinates always produce same weather data:

```bash
# Run 1
python headless_runner.py --lat 40.7 --lon -74.0 --project_type agriculture --use-mock-data
# Temperature: 13.8°C, Rain: 1143.1mm

# Run 2 (identical)
python headless_runner.py --lat 40.7 --lon -74.0 --project_type agriculture --use-mock-data
# Temperature: 13.8°C, Rain: 1143.1mm
```

### 2. Realistic Climate Zones

Mock data respects geographic climate patterns:

| Location | Climate Zone | Temp Range | Rain Range |
|----------|-------------|------------|------------|
| Equator (0°) | Tropical | 25-31°C | 1200-2800mm |
| 25°N/S | Subtropical | 20-28°C | 500-1500mm |
| 45°N/S | Temperate | 13-23°C | 300-1100mm |
| 60°N/S | Cold | 4-16°C | 200-800mm |
| 75°N/S | Polar | -13-3°C | 50-350mm |

### 3. Geographic Variations

Mock data includes:
- **Coastal effects**: More rainfall near coasts
- **Latitude effects**: Seasonal variation increases with latitude
- **Elevation proxy**: Highland cooling in temperate zones
- **Monsoon patterns**: Tropical wet/dry seasons

### 4. Monthly Climate Data

Generate monthly breakdowns:

```python
from mock_data import get_mock_monthly_data

monthly = get_mock_monthly_data(40.7, -74.0)
# Returns:
# - rainfall_monthly_mm: [103.2, 118.6, 125.2, ...]
# - temp_monthly_celsius: [6.3, 7.3, 10.1, ...]
# - soil_moisture_monthly: [0.6879, 0.7907, 0.8350, ...]
```

## Use Cases

### Use Case 1: Unit Testing

Test edge cases without API dependencies:

```bash
# Tropical region
python headless_runner.py --lat 0 --lon 0 --project_type agriculture --use-mock-data

# Polar region
python headless_runner.py --lat 80 --lon 0 --project_type agriculture --use-mock-data

# Multiple temperature scenarios
for temp in 1.0 2.0 3.0 4.0 5.0; do
  python headless_runner.py \
    --lat 40.7 --lon -74.0 \
    --project_type agriculture \
    --temp_delta $temp \
    --use-mock-data
done
```

### Use Case 2: Load Testing

Run 1,000+ tests per minute:

```bash
# High-volume simulation
for i in {1..1000}; do
  lat=$(echo "scale=2; -90 + ($i * 0.18)" | bc)
  lon=$(echo "scale=2; -180 + ($i * 0.36)" | bc)
  
  python headless_runner.py \
    --lat $lat --lon $lon \
    --project_type agriculture \
    --use-mock-data \
    > result_${i}.json
done
```

### Use Case 3: Code Fortification Sprint

Cloud Agents can run extensive tests:

```bash
# Run comprehensive test suite
./test_mock_mode.sh

# Results:
# - 100 location variations: 5 seconds
# - 1000 rapid runs: 30 seconds
# - All climate zones: 2 seconds
# Total: No API rate limits, no external dependencies
```

### Use Case 4: Regression Testing

Verify calculations remain consistent:

```bash
# Baseline
python headless_runner.py [...] --use-mock-data > baseline.json

# After code changes
python headless_runner.py [...] --use-mock-data > after_changes.json

# Compare
diff baseline.json after_changes.json
```

## API Reference

### Mock Data Functions

#### `get_mock_weather(lat, lon)`

Returns basic weather data.

**Parameters:**
- `lat` (float): Latitude (-90 to 90)
- `lon` (float): Longitude (-180 to 180)

**Returns:**
```python
{
    'max_temp_celsius': 13.8,
    'total_precip_mm': 1143.1,
    'data_source': 'mock_data',
    'climate_zone': 'temperate',
    'location': {'lat': 40.7, 'lon': -74.0}
}
```

#### `get_mock_coastal_params(lat, lon)`

Returns coastal parameters for flood analysis.

**Returns:**
```python
{
    'slope_pct': 5.83,
    'max_wave_height': 2.54,
    'data_source': 'mock_data',
    'location': {'lat': 40.7, 'lon': -74.0}
}
```

#### `get_mock_monthly_data(lat, lon)`

Returns 12-month climate breakdown.

**Returns:**
```python
{
    'rainfall_monthly_mm': [103.2, 118.6, ...],
    'soil_moisture_monthly': [0.6879, 0.7907, ...],
    'temp_monthly_celsius': [6.3, 7.3, ...],
    'data_source': 'mock_data'
}
```

#### `get_mock_elevation(lat, lon)`

Returns elevation estimate.

**Returns:** `float` (meters above sea level)

## Testing & Validation

### Run Full Test Suite

```bash
./test_mock_mode.sh
```

**Tests included:**
1. ✓ Reproducibility (determinism)
2. ✓ High-volume (100 runs)
3. ✓ All project types
4. ✓ Climate zone coverage
5. ✓ Stress test (1000 runs)
6. ✓ Mock vs fallback comparison

### Manual Testing

```python
# Test in Python REPL
from mock_data import get_mock_weather

# New York
weather_ny = get_mock_weather(40.7, -74.0)
print(f"NYC: {weather_ny['max_temp_celsius']}°C")

# Reproducibility test
weather_ny_2 = get_mock_weather(40.7, -74.0)
assert weather_ny == weather_ny_2, "Not deterministic!"

# Different location should differ
weather_london = get_mock_weather(51.5, -0.1)
assert weather_ny != weather_london, "All locations identical!"
```

## Performance Comparison

| Metric | GEE Mode | Fallback Mode | Mock Data Mode |
|--------|----------|---------------|----------------|
| **API Calls** | 1 per request | 0 | 0 |
| **Response Time** | 2-5 seconds | <0.1s | <0.1s |
| **Rate Limit** | ~1000/day | Unlimited | Unlimited |
| **Credentials** | Required | Not required | Not required |
| **Reproducibility** | ❌ Varies | ✓ Fixed | ✓ Fixed |
| **Realism** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ |
| **Testing** | ❌ Not suitable | ⚠️ Limited | ✓ Excellent |

## Best Practices

### DO:
✓ Use mock data for unit tests  
✓ Use mock data for load testing  
✓ Use mock data for CI/CD pipelines  
✓ Use mock data for rapid prototyping  
✓ Validate calculations with real GEE data periodically  

### DON'T:
✗ Use mock data for production analysis  
✗ Use mock data for client-facing reports  
✗ Assume mock data matches real GEE exactly  
✗ Skip validation against real data  

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Unit Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install dependencies
        run: |
          python -m pip install -r requirements.txt
      
      - name: Run mock data tests
        run: |
          # Run 100 test scenarios with mock data
          for i in {1..100}; do
            python headless_runner.py \
              --lat $((i - 50)) \
              --lon $((i * 2 - 100)) \
              --project_type agriculture \
              --use-mock-data \
              || exit 1
          done
      
      - name: Validate reproducibility
        run: ./test_mock_mode.sh
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    stages {
        stage('Mock Data Tests') {
            steps {
                sh '''
                    python headless_runner.py \
                      --lat 40.7 --lon -74.0 \
                      --project_type agriculture \
                      --use-mock-data \
                      --temp_delta 2.0 \
                      > test_output.json
                    
                    # Validate output structure
                    cat test_output.json | jq -e '.success == true'
                '''
            }
        }
    }
}
```

## Limitations

1. **Not Real GEE Data**
   - Mock data is based on climate zone approximations
   - Does not reflect real-time weather conditions
   - Missing microclimate variations

2. **Simplified Geography**
   - No actual elevation data
   - Coastal proximity is heuristic-based
   - No terrain complexity

3. **Fixed Patterns**
   - Deterministic = no natural variability
   - Same location always returns same values
   - No inter-annual variation

4. **Limited Spatial Features**
   - No actual satellite imagery
   - No land cover classification
   - No flood mask generation

## Troubleshooting

### Issue: Mock data values seem unrealistic

**Solution:** Check climate zone classification:

```python
from mock_data import get_climate_zone, get_mock_weather

lat, lon = 40.7, -74.0
zone = get_climate_zone(lat)
print(f"Climate zone: {zone}")  # Should be 'temperate'

weather = get_mock_weather(lat, lon)
print(f"Temperature: {weather['max_temp_celsius']}°C")
print(f"Rainfall: {weather['total_precip_mm']}mm")
```

### Issue: Results not reproducible

**Solution:** Ensure exact same coordinates:

```bash
# This is deterministic
python headless_runner.py --lat 40.7 --lon -74.0 --use-mock-data

# This will differ (different coordinates)
python headless_runner.py --lat 40.71 --lon -74.01 --use-mock-data
```

### Issue: Want more variability in tests

**Solution:** Vary coordinates systematically:

```bash
# Test 100 locations in a grid
for lat in {-80..80..16}; do
  for lon in {-160..160..32}; do
    python headless_runner.py \
      --lat $lat --lon $lon \
      --use-mock-data \
      --project_type agriculture
  done
done
```

## Future Enhancements

Potential improvements:

- [ ] Add noise parameter for inter-annual variability
- [ ] Support for historical year simulation
- [ ] Integration with real elevation datasets
- [ ] Machine learning-based weather patterns
- [ ] Cache mock data for faster repeated calls

## Support

For issues or questions:
1. Run `./test_mock_mode.sh` to validate setup
2. Check `mock_data.py` docstrings for API details
3. Compare mock vs fallback modes for sanity checking

---

**Last Updated:** 2026-02-13  
**Version:** 1.0.0  
**Related Files:**
- `mock_data.py` - Mock data generator
- `headless_runner.py` - CLI with `--use-mock-data` flag
- `test_mock_mode.sh` - Validation test suite
