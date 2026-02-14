# Model Validation Whitepaper (Backtest Summary)

This report backtests the `physics_engine.py` yield model using deterministic, year-seeded historical simulations.

## Backtest Configuration
- Targets: 5 locations (Iowa/maize, Ghana/cocoa, Vietnam/rice, Brazil/soy, Ukraine/wheat)
- Years simulated: 2004–2023 (20 years per target; 100 simulations total)
- Determinism: climate inputs are generated from a deterministic seed `seed = int(year * lat)` (see `historical_runner.py`)

## Lowest Yield Year by Location (Drought-Year Identification)
The lowest-yield year is interpreted as the most severe stress year (often drought shock in the synthetic climate generator).

| Location | Crop | Lowest Yield Year | Yield (%) |
|---|---|---:|---:|
| Brazil | Soy | 2012 | 25.97 |
| Ghana | Cocoa | 2022 | 93.96 |
| Iowa, USA | Maize | 2018 | 24.60 |
| Ukraine | Wheat | 2013 | 42.01 |
| Vietnam | Rice | 2013 | 30.55 |

## Yield Volatility Score by Crop (Standard Deviation)
Volatility Score is computed as the sample standard deviation of annual `yield_pct` values across the 20 simulated years for each crop.

| Crop | Volatility Score (Std Dev, %) | Mean Yield (%) | N (years) |
|---|---:|---:|---:|
| Cocoa | 1.97 | 99.20 | 20 |
| Maize | 18.75 | 92.68 | 20 |
| Rice | 21.42 | 88.84 | 20 |
| Soy | 24.52 | 82.22 | 20 |
| Wheat | 15.64 | 93.97 | 20 |

## Notes / Interpretation
- This backtest is deterministic and repeatable; rerunning the orchestrator should reproduce identical results for the same code version.
- Because the climate generator includes rare, deterministic shock events, the lowest-yield years highlight years where combined heat + rainfall stress was greatest for each location.
