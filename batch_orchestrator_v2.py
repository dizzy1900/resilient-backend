#!/usr/bin/env python3
"""Batch Orchestrator v2 - Run 100 global targets in parallel.

Reads global_targets_100.csv and executes headless_runner.py for each target
using multiprocessing. Output JSON structure is identical to final_global_atlas.json
for frontend compatibility.
"""

import csv
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CHUNK_SIZE = int(os.environ.get("ATLAS_CHUNK_SIZE", "100"))


SCENARIO_YEAR = int(os.environ.get("ATLAS_SCENARIO_YEAR", "2050"))
USE_MOCK_DATA = os.environ.get("ATLAS_USE_MOCK_DATA", "1") not in {"0", "false", "False"}

# Sensible non-zero defaults (can be overridden via env vars)
DEFAULT_SLR_PROJECTION_M = float(os.environ.get("ATLAS_SLR_PROJECTION_M", "1.0"))
DEFAULT_RAIN_INTENSITY_INCREASE_PCT = float(os.environ.get("ATLAS_RAIN_INTENSITY_INCREASE_PCT", "25.0"))


@dataclass(frozen=True)
class Target:
    name: str
    lat: float
    lon: float
    project_type: str
    crop_type: Optional[str]


def read_targets(csv_path: Path) -> List[Target]:
    """Read targets from CSV file.
    
    Args:
        csv_path: Path to CSV file with columns: name, lat, lon, project_type, crop_type
    
    Returns:
        List of Target objects
    """
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"name", "lat", "lon", "project_type", "crop_type"}
        if set(reader.fieldnames or []) != required:
            raise ValueError(
                f"{csv_path} must have columns exactly {sorted(required)}; got {reader.fieldnames}"
            )

        targets: List[Target] = []
        for row in reader:
            crop_type = (row.get("crop_type") or "").strip() or None
            targets.append(
                Target(
                    name=(row["name"] or "").strip(),
                    lat=float(row["lat"]),
                    lon=float(row["lon"]),
                    project_type=(row["project_type"] or "").strip(),
                    crop_type=crop_type,
                )
            )

    if not targets:
        raise ValueError(f"No targets found in {csv_path}")

    if len(targets) > CHUNK_SIZE:
        logger.warning(
            "CSV %s contains %d targets (> %d). They will be processed in chunks.",
            csv_path, len(targets), CHUNK_SIZE,
        )

    return targets


def build_headless_command(target: Target) -> List[str]:
    """Build the command line for headless_runner.py."""
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "headless_runner.py"),
        "--lat",
        str(target.lat),
        "--lon",
        str(target.lon),
        "--scenario_year",
        str(SCENARIO_YEAR),
        "--project_type",
        target.project_type,
    ]

    if target.project_type == "agriculture":
        if target.crop_type:
            cmd += ["--crop_type", target.crop_type]

    if target.project_type == "coastal":
        cmd += ["--slr_projection", str(DEFAULT_SLR_PROJECTION_M)]

    if target.project_type == "flood":
        cmd += ["--rain_intensity", str(DEFAULT_RAIN_INTENSITY_INCREASE_PCT)]

    if USE_MOCK_DATA:
        cmd.append("--use-mock-data")

    return cmd


def run_one_target(target: Target) -> Dict[str, Any]:
    """Execute headless_runner.py for a single target.
    
    Returns a dict with the runner output merged with target and runner metadata,
    matching the structure in final_global_atlas.json.
    """
    cmd = build_headless_command(target)

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    try:
        result = json.loads(stdout) if stdout else {
            "success": False,
            "error": "No stdout",
            "message": "headless_runner produced no stdout",
        }
    except json.JSONDecodeError as e:
        result = {
            "success": False,
            "error": "Invalid JSON output",
            "message": str(e),
            "raw_stdout": stdout,
        }

    # Enrich with target metadata and subprocess info
    # This structure matches final_global_atlas.json exactly
    result["target"] = {
        "name": target.name,
        "lat": target.lat,
        "lon": target.lon,
        "project_type": target.project_type,
        "crop_type": target.crop_type,
    }
    result["runner"] = {
        "returncode": proc.returncode,
        "stderr": stderr,
        "cmd": cmd,
    }

    return result


def main() -> None:
    """Main entry point - read CSV, run all targets in parallel, write JSON."""
    repo_root = Path(__file__).resolve().parent
    targets_csv = repo_root / "global_targets_100.csv"
    out_json = repo_root / "global_atlas_v2.json"

    print(f"Reading targets from {targets_csv}...")
    targets = read_targets(targets_csv)
    print(f"Loaded {len(targets)} targets")

    # Process in chunks to stay within resource limits.
    workers = min(cpu_count(), len(targets))
    print(f"Running with {workers} parallel workers...")

    results: List[Dict[str, Any]] = []
    for i in range(0, len(targets), CHUNK_SIZE):
        chunk = targets[i : i + CHUNK_SIZE]
        print(f"Processing chunk {i // CHUNK_SIZE + 1} ({len(chunk)} targets)...")
        with Pool(processes=workers) as pool:
            results.extend(pool.imap_unordered(run_one_target, chunk))

    # Deterministic order for diffing/debugging (sort by project_type, then name)
    results.sort(key=lambda r: (
        r.get("target", {}).get("project_type", ""),
        r.get("target", {}).get("name", "")
    ))

    # Count successes and failures
    successes = sum(1 for r in results if r.get("success", False))
    failures = len(results) - successes

    with out_json.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    print(f"Wrote {len(results)} results to {out_json}")
    print(f"  - Successes: {successes}")
    print(f"  - Failures: {failures}")

    if failures > 0:
        print("\nFailed targets:")
        for r in results:
            if not r.get("success", False):
                target = r.get("target", {})
                error = r.get("error", "Unknown error")
                print(f"  - {target.get('name', 'Unknown')}: {error}")


if __name__ == "__main__":
    main()
