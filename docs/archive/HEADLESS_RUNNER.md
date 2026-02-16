# Headless Runner for Cloud Agents

## Overview

`headless_runner.py` is a standalone CLI tool that runs AdaptMetric climate impact calculations **without starting a web server**. It's designed for Cloud Agents that need to execute calculations programmatically and receive results as JSON.

## Key Features

- ✅ **No web server required** - Direct calculation execution
- ✅ **CLI argument-based** - All inputs via command-line flags
- ✅ **JSON output** - Structured results to stdout for easy parsing
- ✅ **Multiple project types** - Agriculture, Coastal, Flood, Health
- ✅ **Fallback weather data** - Works even when Google Earth Engine is unavailable

## Installation

No additional dependencies needed - uses the same environment as main.py:

```bash
cd adaptmetric-backend
source .venv/bin/activate  # or use .venv/bin/python directly
```

## Usage

### Basic Syntax

```bash
python headless_runner.py --lat <LAT> --lon <LON> --scenario_year <YEAR> --project_type <TYPE> [OPTIONS]
```

### Required Arguments

- `--lat` - Latitude coordinate (-90 to 90)
- `--lon` - Longitude coordinate (-180 to 180)
- `--scenario_year` - Future year for climate projections (e.g., 2050)
- `--project_type` - Type of analysis: `agriculture`, `coastal`, `flood`, or `health`

### Project-Specific Optional Arguments

#### Agriculture Projects
- `--crop_type` - `maize` or `cocoa` (default: maize)
- `--temp_delta` - Temperature increase in °C (default: 0.0)
- `--rain_pct_change` - Rainfall change percentage (default: 0.0)

#### Coastal Projects
- `--mangrove_width` - Mangrove buffer width in meters (default: 0.0)
- `--slr_projection` - Sea level rise projection in meters (default: 0.0)

#### Flood Projects
- `--rain_intensity` - Rain intensity increase percentage (default: 0.0)

#### Health Projects
- `--workforce_size` - Number of workers (default: 100)
- `--daily_wage` - Daily wage per worker in USD (default: 15.0)

### Testing & Development Flags

#### Mock Data Mode (Recommended for Testing)
- `--use-mock-data` - Use deterministic mock data instead of Google Earth Engine

**Why use mock data?**
- ✓ Zero API calls to Google Earth Engine
- ✓ Unlimited test runs (no rate limits)
- ✓ Deterministic results (same input = same output)
- ✓ Instant response time (<0.1s vs 2-5s)
- ✓ Safe for high-volume testing (1000+ runs/minute)

**When to use mock data:**
- Unit testing and integration tests
- Code fortification sprints
- Load testing and benchmarking
- CI/CD pipelines
- Local development without GEE credentials

**Example:**
```bash
python headless_runner.py \
  --lat 40.7 --lon -74.0 \
  --scenario_year 2050 \
  --project_type agriculture \
  --use-mock-data
```

See [MOCK_DATA_GUIDE.md](MOCK_DATA_GUIDE.md) for detailed documentation.

## Examples

### Example 1: Maize Yield Analysis (New York, 2050)

```bash
python headless_runner.py \
  --lat 40.7 \
  --lon -74.0 \
  --scenario_year 2050 \
  --project_type agriculture \
  --crop_type maize \
  --temp_delta 2.0 \
  --rain_pct_change -10.0
```

**Output:**
```json
{
  "project_type": "agriculture",
  "location": {"lat": 40.7, "lon": -74.0},
  "scenario_year": 2050,
  "climate_conditions": {
    "temperature_c": 20.0,
    "rainfall_mm": 700.0,
    "temp_delta": 2.0,
    "rain_pct_change": -10.0,
    "data_source": "fallback_climate_zone"
  },
  "crop_analysis": {
    "crop_type": "maize",
    "standard_yield_pct": 100.0,
    "resilient_yield_pct": 100.0,
    "avoided_loss_pct": 0.0,
    "percentage_improvement": 0.0,
    "recommendation": "standard"
  },
  "financial_analysis": {
    "npv_usd": 880206.22,
    "payback_years": 0.01,
    "incremental_cash_flows": [-2000.0, 143575.0, ...],
    "assumptions": {...}
  },
  "execution_timestamp": "2026-02-13T16:53:47.829686",
  "success": true
}
```

### Example 2: Cocoa Production (Tropical Region, 2050)

```bash
python headless_runner.py \
  --lat -2.5 \
  --lon 28.8 \
  --scenario_year 2050 \
  --project_type agriculture \
  --crop_type cocoa \
  --temp_delta 3.0 \
  --rain_pct_change -15.0
```

### Example 3: Health Impact Analysis (West Africa, 2050)

```bash
python headless_runner.py \
  --lat 13.5 \
  --lon 2.1 \
  --scenario_year 2050 \
  --project_type health \
  --workforce_size 250 \
  --daily_wage 12.0
```

**Output:**
```json
{
  "project_type": "health",
  "location": {"lat": 13.5, "lon": 2.1},
  "scenario_year": 2050,
  "productivity_analysis": {
    "wbgt_estimate": 27.9,
    "productivity_loss_pct": 16.2,
    "heat_stress_category": "Moderate",
    "recommendation": "Light work affected, breaks recommended"
  },
  "malaria_risk": {
    "risk_score": 100,
    "risk_category": "High",
    "description": "Climate conditions highly suitable for malaria transmission"
  },
  "economic_impact": {
    "total_economic_impact": {
      "annual_loss": 154000.0,
      "daily_loss_average": 616.0,
      "per_worker_annual_loss": 616.0
    }
  },
  "success": true
}
```

### Example 4: Coastal Flood Risk (Miami, 2050)

```bash
python headless_runner.py \
  --lat 25.8 \
  --lon -80.2 \
  --scenario_year 2050 \
  --project_type coastal \
  --slr_projection 1.5
```

### Example 5: Flash Flood Risk (Urban Area, 2050)

```bash
python headless_runner.py \
  --lat 34.0 \
  --lon -118.2 \
  --scenario_year 2050 \
  --project_type flood \
  --rain_intensity 25.0
```

## Output Format

All results are returned as JSON with the following structure:

```json
{
  "project_type": "agriculture|coastal|flood|health",
  "location": {"lat": 0.0, "lon": 0.0},
  "scenario_year": 2050,
  "success": true|false,
  "execution_timestamp": "ISO-8601 timestamp",
  ... project-specific results ...
}
```

### Error Handling

If an error occurs, the output includes error details:

```json
{
  "success": false,
  "error": "Error category",
  "message": "Detailed error message",
  "execution_timestamp": "ISO-8601 timestamp"
}
```

Exit codes:
- `0` - Success
- `1` - Error occurred

## Integration with Cloud Agents

### Capturing Output

```bash
# Capture JSON output
result=$(python headless_runner.py --lat 40.7 --lon -74.0 --scenario_year 2050 --project_type agriculture)

# Parse with jq
echo "$result" | jq '.crop_analysis.resilient_yield_pct'

# Save to file
python headless_runner.py [...args...] > result.json
```

### Batch Processing

```bash
# Run multiple scenarios
for temp_delta in 1.0 2.0 3.0; do
  python headless_runner.py \
    --lat 40.7 --lon -74.0 \
    --scenario_year 2050 \
    --project_type agriculture \
    --temp_delta $temp_delta \
    > "result_temp_${temp_delta}.json"
done
```

### Error Handling in Scripts

```bash
#!/bin/bash
if python headless_runner.py [...args...] > result.json; then
  echo "Success!"
  cat result.json | jq '.financial_analysis.npv_usd'
else
  echo "Failed!"
  cat result.json | jq '.error'
  exit 1
fi
```

## Architecture

The headless runner:

1. **Imports calculation engines directly** - Bypasses Flask/web server layer
2. **Uses fallback weather data** - Works offline with climate zone approximations
3. **Outputs to stdout only** - Clean JSON for piping/parsing
4. **Validates inputs** - Ensures coordinate ranges and required fields
5. **Handles errors gracefully** - Returns structured error JSON

## Comparison: Headless vs Web Server

| Feature | Headless Runner | Flask API (main.py) |
|---------|----------------|---------------------|
| **Startup time** | Instant | ~2-3 seconds |
| **Dependencies** | Core engines only | Flask, CORS, threading |
| **Input method** | CLI arguments | HTTP POST JSON |
| **Output method** | JSON to stdout | HTTP JSON response |
| **Use case** | Automation, batch jobs | Web frontend, interactive |
| **Concurrent requests** | Multiple processes | Single server, multiple threads |

## Google Earth Engine Credentials

The headless runner can use real GEE data if credentials are configured. See **[CREDENTIALS_SETUP.md](CREDENTIALS_SETUP.md)** for detailed setup instructions.

**Quick setup:**
- **Cloud Agents:** Set `WARP_GEE_CREDENTIALS` secret in Factory
- **Local dev:** Place `credentials.json` in `~/.adaptmetric/`
- **Testing:** Use `--use-mock-data` flag (no credentials needed)

Check credential status:
```bash
python gee_credentials.py
```

## Limitations

1. **Google Earth Engine** - Requires credentials or use `--use-mock-data` for testing
2. **No spatial analysis** - Simplified analysis compared to full GEE-enabled API
3. **No database** - No persistence of results
4. **Single calculation per run** - No batch endpoint (use shell scripting for batches)

## Future Enhancements

- [ ] Support for batch input via JSON file
- [ ] Optional CSV output format
- [ ] Integration with GEE when credentials available
- [ ] Caching of weather data for repeated locations
- [ ] Progress indicators for long-running calculations

## Troubleshooting

### Issue: "Module not found" errors

**Solution:** Ensure you're running from the adaptmetric-backend directory and using the virtual environment:

```bash
cd adaptmetric-backend
.venv/bin/python headless_runner.py --help
```

### Issue: GEE warnings in stderr

**Solution:** This is expected behavior when GEE credentials are not configured. The script falls back to climate zone approximations. To suppress warnings:

```bash
python headless_runner.py [...args...] 2>/dev/null
```

### Issue: Invalid JSON output

**Solution:** Check stderr for errors:

```bash
python headless_runner.py [...args...] 2>&1 | tee debug.log
```

## Support

For questions or issues:
1. Check the main.py implementation for API equivalents
2. Review physics_engine.py and financial_engine.py for calculation details
3. Run with `--help` for argument reference

---

**Last Updated:** 2026-02-13  
**Version:** 1.0.0
