#!/usr/bin/env python3
"""Historical runner for model validation backtests.

This script is intentionally deterministic: for a given (lat, lon, year, crop_type)
input, it will always return the same yield.

It generates a plausible growing-season temperature/rainfall pair from the inputs,
then calls the physics engine (process-based yield model).

Output JSON schema (to stdout):
  {"year": int, "yield_pct": float, "location": {"lat": float, "lon": float}}
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict, dataclass

from physics_engine import calculate_yield


@dataclass(frozen=True)
class Location:
    lat: float
    lon: float


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _seed_everything(seed: int) -> None:
    """Seed python (and numpy if installed) for determinism."""

    random.seed(seed)

    try:
        import numpy as np  # type: ignore

        # numpy requires 0 <= seed < 2**32
        np.random.seed(seed % (2**32 - 1))
    except Exception:
        # numpy is optional
        pass


def _baseline_climate_from_lat(lat: float) -> tuple[float, float]:
    """Very simple climate-zone baseline (temp_c, rain_mm) derived from latitude."""

    abs_lat = abs(lat)

    if abs_lat < 23.5:  # Tropical
        return 28.5, 1800.0
    if abs_lat < 35:  # Subtropical
        return 25.0, 1000.0
    if abs_lat < 50:  # Temperate
        return 20.0, 750.0

    # Cold
    return 15.0, 550.0


def _crop_baseline_adjustments(crop_type: str) -> tuple[float, float]:
    """(temp_delta_c, rain_delta_mm) per crop to approximate crop-specific seasons."""

    crop = crop_type.lower()

    if crop == "cocoa":
        return 0.5, 700.0
    if crop == "rice":
        return 0.0, 600.0
    if crop == "soy":
        return 0.0, 150.0
    if crop == "wheat":
        # Cooler-season crop
        return -2.0, -100.0

    # maize default
    return 0.0, 0.0


def _generate_historical_climate(*, lat: float, lon: float, year: int, crop_type: str) -> tuple[float, float]:
    """Generate (temp_c, rain_mm) deterministically based on (lat, lon, year).

    Crucial determinism requirement:
      seed = int(year * lat)

    We intentionally only use pseudo-randomness *after* seeding, so the output is
    stable for a given year/location.
    """

    # Deterministic seed, as requested.
    seed = int(year * lat)
    _seed_everything(seed)

    rng = random.Random(seed)

    base_temp_c, base_rain_mm = _baseline_climate_from_lat(lat)
    crop_temp_delta, crop_rain_delta = _crop_baseline_adjustments(crop_type)

    # Year-to-year variability (moderate).
    temp_c = base_temp_c + crop_temp_delta + rng.gauss(0.0, 3.0)
    rain_multiplier = 1.0 + _clamp(rng.gauss(0.0, 0.35), -0.75, 0.75)
    rain_mm = max(0.0, (base_rain_mm + crop_rain_delta) * rain_multiplier)

    # Rare shock events to create distinct "drought" / "flood" years.
    # These are still deterministic because they come from the seeded RNG.
    shock_roll = rng.random()
    if shock_roll < 0.12:
        # Drought shock: lower rain + higher temp.
        rain_mm *= rng.uniform(0.30, 0.60)
        temp_c += rng.uniform(1.5, 4.0)
    elif shock_roll < 0.20:
        # Flooding/waterlogging shock: higher rain.
        rain_mm *= rng.uniform(1.40, 1.90)
        temp_c += rng.uniform(-1.0, 1.0)

    # Minor coastal proxy from lon (kept small; used only to avoid identical climates
    # for identical lat+year combinations).
    temp_c += ((lon % 7) - 3) * 0.05
    rain_mm *= 1.0 + (((abs(lon) % 11) - 5) * 0.005)

    return round(temp_c, 2), round(rain_mm, 2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic historical yield simulation")

    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument(
        "--crop_type",
        type=str,
        required=True,
        choices=["maize", "cocoa", "rice", "soy", "wheat"],
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    temp_c, rain_mm = _generate_historical_climate(lat=args.lat, lon=args.lon, year=args.year, crop_type=args.crop_type)

    # Standard (non-resilient) seeds for baseline backtest.
    yield_pct = calculate_yield(temp=temp_c, rain=rain_mm, seed_type=0, crop_type=args.crop_type)

    out = {
        "year": int(args.year),
        "yield_pct": round(float(yield_pct), 2),
        "location": asdict(Location(lat=float(args.lat), lon=float(args.lon))),
    }

    print(json.dumps(out))


if __name__ == "__main__":
    main()
