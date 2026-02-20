#!/usr/bin/env python3
# =============================================================================
# Diagnostic Atlas Generator
# =============================================================================
"""
Orchestrates sensitivity analysis across all locations:
1. Load final_100_risk_narrative_atlas.json
2. Run 4 stress tests in parallel for all 100 locations
3. Append sensitivity_analysis to each location
4. Update executive summaries with primary risk driver
5. Save as global_atlas_diagnostic.json
"""

import json
import re
from datetime import datetime
from sensitivity_engine import run_parallel_sensitivity


def load_atlas(filepath: str) -> list:
    """Load the atlas JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def save_atlas(data: list, filepath: str) -> None:
    """Save the atlas as a pure JSON array."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def update_executive_summary(location: dict) -> str:
    """
    Update executive summary to include primary risk driver.
    
    Pattern: "INVESTABLE... Primary risk is [Driver] which accounts for [Impact]% of variance."
    """
    original_summary = location.get('executive_summary', '')
    sensitivity = location.get('sensitivity_analysis', {})
    
    primary_driver = sensitivity.get('primary_driver', 'Unknown')
    impact_pct = sensitivity.get('driver_impact_pct', 0.0)
    
    # Clean driver name for summary (remove technical notation)
    driver_clean = primary_driver.replace('(+2°C)', '').replace('(-20%)', '').replace('(-15%)', '').replace('(+15%)', '').strip()
    
    # Map to readable names
    driver_map = {
        'Climate': 'Climate Sensitivity',
        'Water Stress': 'Water Stress',
        'Market Price': 'Market Price',
        'Operational Costs': 'Operational Costs'
    }
    driver_readable = driver_map.get(driver_clean, driver_clean)
    
    # Create the risk driver statement
    risk_statement = f"Primary risk is {driver_readable} which accounts for {impact_pct:.1f}% of variance."
    
    # Insert after first sentence (usually the rating)
    # Find first period followed by space
    if ': ' in original_summary:
        # Find end of first sentence after the rating (e.g., "INVESTABLE: Location shows...")
        first_colon = original_summary.find(': ')
        rest = original_summary[first_colon + 2:]
        
        # Find first period in the rest
        period_match = re.search(r'\.\s', rest)
        if period_match:
            insert_pos = first_colon + 2 + period_match.end()
            updated = original_summary[:insert_pos] + risk_statement + " " + original_summary[insert_pos:]
        else:
            # No period found, append at end
            updated = original_summary + " " + risk_statement
    else:
        # No colon structure, append at end
        updated = original_summary + " " + risk_statement
    
    return updated


def main():
    print("=" * 60)
    print("DIAGNOSTIC ATLAS GENERATOR")
    print("=" * 60)
    
    # 1. Load the atlas
    input_file = "final_100_risk_narrative_atlas.json"
    print(f"\n[1/4] Loading {input_file}...")
    atlas = load_atlas(input_file)
    print(f"      Loaded {len(atlas)} locations")
    
    # 2. Run sensitivity analysis in parallel
    print(f"\n[2/4] Running sensitivity analysis (4 stress tests × {len(atlas)} locations)...")
    start_time = datetime.now()
    
    sensitivity_results = run_parallel_sensitivity(atlas, max_workers=20)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"      Completed in {elapsed:.2f} seconds")
    
    # 3. Append sensitivity analysis to each location
    print("\n[3/4] Appending sensitivity_analysis and updating summaries...")
    
    driver_counts = {}
    for i, location in enumerate(atlas):
        # Add sensitivity analysis
        location['sensitivity_analysis'] = sensitivity_results[i]
        
        # Update executive summary
        location['executive_summary'] = update_executive_summary(location)
        
        # Track driver distribution
        driver = sensitivity_results[i].get('primary_driver', 'Unknown')
        driver_counts[driver] = driver_counts.get(driver, 0) + 1
    
    # 4. Save the diagnostic atlas
    output_file = "global_atlas_diagnostic.json"
    print(f"\n[4/4] Saving to {output_file}...")
    save_atlas(atlas, output_file)
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print(f"\nPrimary Risk Driver Distribution:")
    for driver, count in sorted(driver_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(atlas)) * 100
        print(f"  {driver}: {count} locations ({pct:.1f}%)")
    
    # Sample output
    print(f"\n✓ Saved {len(atlas)} locations to {output_file}")
    print("\nSample entry (first location):")
    sample = atlas[0]
    sens = sample.get('sensitivity_analysis', {})
    print(f"  Location: {sample.get('target', {}).get('name', 'Unknown')}")
    print(f"  Primary Driver: {sens.get('primary_driver')}")
    print(f"  Impact: {sens.get('driver_impact_pct', 0):.1f}%")
    print(f"  Executive Summary: {sample.get('executive_summary', '')[:150]}...")


if __name__ == "__main__":
    main()
