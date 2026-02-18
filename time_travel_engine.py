#!/usr/bin/env python3
"""Time Travel Engine for AdaptMetric
=====================================

Creates time-series forecasts by running climate simulations across multiple decades.
Transforms static snapshot data into 4D temporal analysis with stranded asset detection.

Usage:
    python time_travel_engine.py [--input global_atlas_rated.json] [--output global_atlas_4d.json]

Output:
    JSON array with temporal_analysis containing:
    - history: Array of {year, npv, default_prob} for 2030, 2040, 2050
    - stranded_asset_year: Year when NPV crosses zero (null if never)
"""

import argparse
import json
import os
import subprocess
import sys
from copy import deepcopy
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Configuration
USE_MOCK_DATA = os.environ.get("ATLAS_USE_MOCK_DATA", "1") not in {"0", "false", "False"}
SIMULATION_YEARS = [2030, 2040, 2050]  # Run all years with consistent climate stress

# Environmental scaling factors per decade (simplified climate projections)
# These approximate IPCC scenarios for temperature and precipitation changes
CLIMATE_DELTAS = {
    2030: {"temp_delta": 0.5, "rain_pct_change": -5.0},
    2040: {"temp_delta": 1.0, "rain_pct_change": -10.0},
    2050: {"temp_delta": 1.5, "rain_pct_change": -15.0},
}


def build_headless_command(
    lat: float,
    lon: float,
    scenario_year: int,
    project_type: str,
    crop_type: Optional[str] = None,
    slr_projection: float = 1.0,
    rain_intensity: float = 25.0,
) -> List[str]:
    """Build command to run headless_runner.py for a specific year.
    
    Climate stress is scaled based on scenario year:
    - 2030: 33% of 2050 impact
    - 2040: 67% of 2050 impact  
    - 2050: Full impact
    """
    # Climate progression scale (linear from present to 2050)
    year_scale = (scenario_year - 2025) / (2050 - 2025)  # 0.2 for 2030, 0.6 for 2040, 1.0 for 2050
    
    cmd = [
        sys.executable,
        str(Path(__file__).resolve().parent / "headless_runner.py"),
        "--lat", str(lat),
        "--lon", str(lon),
        "--scenario_year", str(scenario_year),
        "--project_type", project_type,
    ]

    if project_type == "agriculture":
        if crop_type:
            cmd += ["--crop_type", crop_type]
        # Apply progressive climate stress for agriculture
        # By 2050: +2°C temp, -20% rainfall
        temp_delta = 2.0 * year_scale
        rain_pct_change = -20.0 * year_scale
        cmd += ["--temp_delta", str(temp_delta)]
        cmd += ["--rain_pct_change", str(rain_pct_change)]
    
    if project_type == "coastal":
        # Scale SLR projection based on year (meters)
        # By 2050: 1.0m SLR
        scaled_slr = slr_projection * year_scale
        cmd += ["--slr_projection", str(scaled_slr)]
    
    if project_type == "flood":
        # Scale rain intensity increase based on year
        # By 2050: 25% increase in extreme rainfall
        scaled_intensity = rain_intensity * year_scale
        cmd += ["--rain_intensity", str(scaled_intensity)]

    if USE_MOCK_DATA:
        cmd.append("--use-mock-data")

    return cmd


def run_simulation(
    lat: float,
    lon: float,
    scenario_year: int,
    project_type: str,
    crop_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a single simulation for a location and year."""
    cmd = build_headless_command(
        lat=lat,
        lon=lon,
        scenario_year=scenario_year,
        project_type=project_type,
        crop_type=crop_type,
    )

    proc = subprocess.run(cmd, capture_output=True, text=True)
    stdout = (proc.stdout or "").strip()

    try:
        result = json.loads(stdout) if stdout else {"success": False, "error": "No stdout"}
    except json.JSONDecodeError:
        result = {"success": False, "error": "Invalid JSON"}

    return result


def extract_metrics(simulation_result: Dict[str, Any], year: int) -> Dict[str, Any]:
    """Extract NPV and default probability from simulation result."""
    npv = 0.0
    default_prob = 0.0

    if simulation_result.get("success"):
        # Get NPV from financial_analysis
        financial = simulation_result.get("financial_analysis", {})
        npv = financial.get("npv_usd", 0.0)

        # Get default probability from monte_carlo_analysis if available
        monte_carlo = simulation_result.get("monte_carlo_analysis", {})
        default_prob = monte_carlo.get("default_probability", 0.0)

    return {
        "year": year,
        "npv": round(npv, 2),
        "default_prob": round(default_prob, 2),
    }


def calculate_stranded_asset_year(history: List[Dict[str, Any]]) -> Optional[int]:
    """
    Calculate the year when NPV crosses zero using linear interpolation.
    
    Returns:
        The interpolated year when NPV becomes negative, or None if it never does.
    """
    # Sort history by year
    sorted_history = sorted(history, key=lambda x: x["year"])
    
    # Look for zero crossing
    for i in range(len(sorted_history) - 1):
        current = sorted_history[i]
        next_point = sorted_history[i + 1]
        
        npv_current = current["npv"]
        npv_next = next_point["npv"]
        year_current = current["year"]
        year_next = next_point["year"]
        
        # Check for zero crossing (positive to negative)
        if npv_current >= 0 and npv_next < 0:
            # Linear interpolation to find crossing point
            # y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
            # Solve for x when y = 0
            # 0 = npv_current + (npv_next - npv_current) * (year - year_current) / (year_next - year_current)
            # year = year_current - npv_current * (year_next - year_current) / (npv_next - npv_current)
            
            if npv_next != npv_current:  # Avoid division by zero
                crossing_year = year_current - npv_current * (year_next - year_current) / (npv_next - npv_current)
                return int(round(crossing_year))
    
    # Check if already negative at start
    if sorted_history and sorted_history[0]["npv"] < 0:
        return sorted_history[0]["year"]
    
    # NPV never crosses zero (safe asset)
    return None


def process_location(location: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single location through all simulation years."""
    result = deepcopy(location)
    
    # Extract location info
    loc_info = location.get("location", {})
    lat = loc_info.get("lat", 0.0)
    lon = loc_info.get("lon", 0.0)
    project_type = location.get("project_type", "agriculture")
    
    # Get crop type if available
    crop_type = None
    if project_type == "agriculture":
        crop_analysis = location.get("crop_analysis", {})
        crop_type = crop_analysis.get("crop_type")
        if not crop_type:
            target = location.get("target", {})
            crop_type = target.get("crop_type")
    
    # Build history by running simulations for all years with climate stress
    history = []
    
    # Run simulations for 2030, 2040, and 2050 with progressive climate stress
    for year in SIMULATION_YEARS:
        sim_result = run_simulation(
            lat=lat,
            lon=lon,
            scenario_year=year,
            project_type=project_type,
            crop_type=crop_type,
        )
        
        # Extract metrics from simulation
        metrics = extract_metrics(sim_result, year)
        history.append(metrics)
    
    # Sort history by year
    history = sorted(history, key=lambda x: x["year"])
    
    # Calculate stranded asset year
    stranded_year = calculate_stranded_asset_year(history)
    
    # Add temporal analysis to result
    result["temporal_analysis"] = {
        "history": history,
        "stranded_asset_year": stranded_year,
    }
    
    return result


def process_location_wrapper(args: Tuple[int, Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
    """Wrapper for multiprocessing that includes index for progress tracking."""
    idx, location = args
    result = process_location(location)
    return idx, result


def main():
    parser = argparse.ArgumentParser(
        description="Time Travel Engine - Create temporal forecasts for climate risk analysis"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="global_atlas_rated.json",
        help="Input JSON file with rated atlas data",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="global_atlas_4d.json",
        help="Output JSON file with temporal analysis",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Number of parallel workers (0 = auto)",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run sequentially instead of parallel (for debugging)",
    )

    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    input_path = repo_root / args.input
    output_path = repo_root / args.output

    # Load input data
    print(f"Loading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        atlas_data = json.load(f)

    print(f"Processing {len(atlas_data)} locations for years {SIMULATION_YEARS + [2050]}...")

    # Process locations
    if args.sequential:
        results = []
        for i, location in enumerate(atlas_data):
            print(f"  [{i+1}/{len(atlas_data)}] Processing {location.get('target', {}).get('name', 'Unknown')}...")
            result = process_location(location)
            results.append(result)
    else:
        workers = args.workers if args.workers > 0 else min(cpu_count(), len(atlas_data))
        print(f"Using {workers} parallel workers...")
        
        with Pool(processes=workers) as pool:
            indexed_results = list(pool.imap_unordered(
                process_location_wrapper,
                enumerate(atlas_data)
            ))
        
        # Sort by original index to maintain order
        indexed_results.sort(key=lambda x: x[0])
        results = [r[1] for r in indexed_results]

    # Calculate summary statistics
    stranded_count = sum(1 for r in results if r.get("temporal_analysis", {}).get("stranded_asset_year") is not None)
    safe_count = len(results) - stranded_count
    
    print(f"\nTemporal Analysis Summary:")
    print(f"  Total locations: {len(results)}")
    print(f"  Assets with stranding risk: {stranded_count}")
    print(f"  Safe assets (NPV never negative): {safe_count}")

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")

    print(f"\nWrote {len(results)} results to {output_path}")


if __name__ == "__main__":
    main()
