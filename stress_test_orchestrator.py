#!/usr/bin/env python3
# =============================================================================
# Stress Test Orchestrator - Parallel Monte Carlo Analysis
# =============================================================================
"""
Orchestrates Monte Carlo stress testing across all locations in the Global Atlas.
Runs simulations in parallel and merges risk-adjusted metrics into output.
"""

import json
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from monte_carlo_engine import run_simulation


INPUT_FILE = "final_global_atlas.json"
OUTPUT_FILE = "global_atlas_risk_adjusted.json"
ITERATIONS = 50
MAX_WORKERS = 8  # Parallel workers


def process_location(args: Tuple[int, Dict[str, Any]]) -> Tuple[int, Dict[str, Any]]:
    """
    Process a single location with Monte Carlo simulation.
    
    Args:
        args: Tuple of (index, location_data)
    
    Returns:
        Tuple of (index, monte_carlo_analysis_result)
    """
    idx, location = args
    try:
        mc_result = run_simulation(location, iterations=ITERATIONS)
        return (idx, mc_result)
    except Exception as e:
        return (idx, {
            'error': str(e),
            'mean_npv': None,
            'VaR_95': None,
            'default_probability': None
        })


def run_stress_tests(atlas_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run Monte Carlo simulations on all locations in parallel.
    
    Args:
        atlas_data: List of location objects from the Atlas
    
    Returns:
        Updated atlas with monte_carlo_analysis appended to each location
    """
    total = len(atlas_data)
    results = {}
    
    print(f"\n{'='*60}")
    print(f"MONTE CARLO STRESS TEST ORCHESTRATOR")
    print(f"{'='*60}")
    print(f"Input:        {INPUT_FILE}")
    print(f"Locations:    {total}")
    print(f"Iterations:   {ITERATIONS} per location")
    print(f"Workers:      {MAX_WORKERS}")
    print(f"{'='*60}\n")
    
    # Prepare work items
    work_items = [(i, loc) for i, loc in enumerate(atlas_data)]
    
    # Run in parallel
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_location, item): item[0] for item in work_items}
        
        completed = 0
        for future in as_completed(futures):
            idx, mc_result = future.result()
            results[idx] = mc_result
            completed += 1
            
            # Progress indicator
            if completed % 10 == 0 or completed == total:
                pct = (completed / total) * 100
                print(f"Progress: {completed}/{total} ({pct:.0f}%) locations processed")
    
    # Merge results back into atlas
    for i, location in enumerate(atlas_data):
        location['monte_carlo_analysis'] = results.get(i, {'error': 'No result'})
    
    return atlas_data


def generate_summary(atlas_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate summary statistics for the risk-adjusted atlas."""
    
    mean_npvs = []
    var_95s = []
    default_probs = []
    
    for loc in atlas_data:
        mc = loc.get('monte_carlo_analysis', {})
        if mc.get('mean_npv') is not None:
            mean_npvs.append(mc['mean_npv'])
        if mc.get('VaR_95') is not None:
            var_95s.append(mc['VaR_95'])
        if mc.get('default_probability') is not None:
            default_probs.append(mc['default_probability'])
    
    import numpy as np
    
    return {
        'total_locations': len(atlas_data),
        'successful_simulations': len(mean_npvs),
        'aggregate_metrics': {
            'portfolio_mean_npv': round(np.mean(mean_npvs), 2) if mean_npvs else None,
            'portfolio_var_95': round(np.mean(var_95s), 2) if var_95s else None,
            'avg_default_probability': round(np.mean(default_probs), 2) if default_probs else None,
            'high_risk_locations': sum(1 for p in default_probs if p > 5),  # >5% default risk
            'low_risk_locations': sum(1 for p in default_probs if p == 0)
        },
        'simulation_parameters': {
            'iterations_per_location': ITERATIONS,
            'yield_volatility_std': '15%',
            'price_volatility_range': '+/- 10%',
            'capex_overrun_range': '+/- 5%'
        }
    }


def main():
    """Main execution function."""
    
    start_time = datetime.now()
    
    # Load input data
    input_path = Path(INPUT_FILE)
    if not input_path.exists():
        print(f"ERROR: {INPUT_FILE} not found!")
        print("Run: python batch_orchestrator_v2.py to generate it first.")
        sys.exit(1)
    
    print(f"Loading {INPUT_FILE}...")
    with open(input_path, 'r') as f:
        atlas_data = json.load(f)
    
    # Validate
    if not isinstance(atlas_data, list) or len(atlas_data) == 0:
        print("ERROR: Invalid atlas data format!")
        sys.exit(1)
    
    # Run stress tests
    risk_adjusted_atlas = run_stress_tests(atlas_data)
    
    # Generate summary
    summary = generate_summary(risk_adjusted_atlas)
    
    # Build final output
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'source_file': INPUT_FILE,
            'output_file': OUTPUT_FILE,
            'processing_time_seconds': (datetime.now() - start_time).total_seconds()
        },
        'summary': summary,
        'locations': risk_adjusted_atlas
    }
    
    # Save output
    output_path = Path(OUTPUT_FILE)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    # Print results
    print(f"\n{'='*60}")
    print("STRESS TEST COMPLETE")
    print(f"{'='*60}")
    print(f"Output saved to: {OUTPUT_FILE}")
    print(f"Processing time: {summary['total_locations']} locations in {output_data['metadata']['processing_time_seconds']:.2f}s")
    print(f"\nPortfolio Risk Summary:")
    print(f"  - Avg Mean NPV:          ${summary['aggregate_metrics']['portfolio_mean_npv']:,.2f}")
    print(f"  - Avg VaR (95%):         ${summary['aggregate_metrics']['portfolio_var_95']:,.2f}")
    print(f"  - Avg Default Prob:      {summary['aggregate_metrics']['avg_default_probability']:.2f}%")
    print(f"  - High Risk Locations:   {summary['aggregate_metrics']['high_risk_locations']}")
    print(f"  - Low Risk Locations:    {summary['aggregate_metrics']['low_risk_locations']}")
    print(f"{'='*60}\n")
    
    return output_path


if __name__ == "__main__":
    main()
