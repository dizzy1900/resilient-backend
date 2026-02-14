#!/usr/bin/env python3
"""Backtest orchestrator for model validation.

Runs 5 fixed target locations across 20 historical years (100 simulations total),
executing `historical_runner.py` in parallel using multiprocessing.

Output:
  - validation_data.json (list of 100 results)

Notes on year range:
  We use Python's range semantics (start inclusive, end exclusive):
    years = 2004..2023 (20 years)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from multiprocessing import cpu_count, get_context
from typing import Any


@dataclass(frozen=True)
class Target:
    name: str
    lat: float
    lon: float
    crop_type: str


TARGETS: list[Target] = [
    Target(name="Iowa, USA", lat=41.5868, lon=-93.6250, crop_type="maize"),
    Target(name="Ghana", lat=6.7000, lon=-1.6000, crop_type="cocoa"),
    Target(name="Vietnam", lat=10.0452, lon=105.7469, crop_type="rice"),
    Target(name="Brazil", lat=-12.5425, lon=-55.7217, crop_type="soy"),
    Target(name="Ukraine", lat=49.0000, lon=31.0000, crop_type="wheat"),
]

START_YEAR = 2004
END_YEAR_EXCLUSIVE = 2024  # exclusive; yields 20 years: 2004..2023

OUTPUT_FILE = "validation_data.json"


def _repo_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _historical_runner_path() -> str:
    return os.path.join(_repo_root(), "historical_runner.py")


def _run_one(job: tuple[Target, int]) -> dict[str, Any]:
    target, year = job

    cmd = [
        sys.executable,
        _historical_runner_path(),
        "--lat",
        str(target.lat),
        "--lon",
        str(target.lon),
        "--year",
        str(year),
        "--crop_type",
        target.crop_type,
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "historical_runner.py failed for "
            f"target={target.name}, year={year}: {proc.stderr.strip()}"
        )

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse historical_runner output for target={target.name}, year={year}. "
            f"stdout={proc.stdout!r}"
        ) from e

    # Enrich output with target metadata so downstream analysis doesn't need to
    # re-derive crop and name from lat/lon.
    payload["target"] = {
        "name": target.name,
        "crop_type": target.crop_type,
        "lat": target.lat,
        "lon": target.lon,
    }

    return payload


def main() -> None:
    jobs: list[tuple[Target, int]] = []

    for t in TARGETS:
        for year in range(START_YEAR, END_YEAR_EXCLUSIVE):
            jobs.append((t, year))

    expected = len(TARGETS) * (END_YEAR_EXCLUSIVE - START_YEAR)
    if expected != 100:
        raise RuntimeError(f"Expected 100 simulations but computed {expected}")

    # Keep a conservative default to avoid overwhelming small machines.
    processes = min(max(2, cpu_count() - 1), 8)

    ctx = get_context("spawn")
    with ctx.Pool(processes=processes) as pool:
        results = list(pool.imap_unordered(_run_one, jobs))

    # Stable ordering (by location then year) for diff-friendly output.
    results.sort(key=lambda r: (r["target"]["name"], r["year"]))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    print(f"Wrote {len(results)} results to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
