# Model Validation Whitepaper (Backtest Summary)

This report backtests the `physics_engine.py` yield model using deterministic, year-seeded historical simulations.

## Backtest Configuration
- Targets: 5 locations (Iowa/maize, Ghana/cocoa, Vietnam/rice, Brazil/soy, Ukraine/wheat)
- Years simulated: 2004–2023 (20 years per target; 100 simulations total)
- Determinism: climate inputs are generated from a deterministic seed `seed = year * lat` (see `historical_runner.py`)

## Lowest Yield Year by Location (Drought-Year Identification)
The lowest-yield year is interpreted as the most severe stress year (often drought shock in the synthetic climate generator).

| Location | Crop | Lowest Yield Year | Yield (%) |
|---|---|---:|---:|
| Brazil | Soy | 2009 | 38.11 |
| Ghana | Cocoa | 2006 | 87.15 |
| Iowa, USA | Maize | 2019 | 43.87 |
| Ukraine | Wheat | 2013 | 42.01 |
| Vietnam | Rice | 2021 | 42.67 |

## Yield Volatility Score by Crop (Standard Deviation)
Volatility Score is computed as the sample standard deviation of annual `yield_pct` values across the 20 simulated years for each crop.

| Crop | Volatility Score (Std Dev, %) | Mean Yield (%) | N (years) |
|---|---:|---:|---:|
| Cocoa | 4.01 | 97.66 | 20 |
| Maize | 13.45 | 95.15 | 20 |
| Rice | 14.41 | 93.12 | 20 |
| Soy | 20.64 | 79.43 | 20 |
| Wheat | 15.64 | 93.97 | 20 |

## Notes / Interpretation
- This backtest is deterministic and repeatable; rerunning the orchestrator should reproduce identical results for the same code version.
- Because the climate generator includes rare, deterministic shock events, the lowest-yield years highlight years where combined heat + rainfall stress was greatest for each location.
