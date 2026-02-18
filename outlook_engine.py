#!/usr/bin/env python3
"""
Outlook Engine - Credit Rating Outlook Calculator for AdaptMetric Assets

This module calculates credit rating outlooks by analyzing temporal rating
trajectories across 2030, 2040, and 2050 projections to warn investors
of potential future downgrades or upgrades.
"""

import json
from typing import Optional

# Rating scale in order from best to worst (for comparison)
RATING_ORDER = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'C']


def load_data(filepath: str) -> list[dict]:
    """Load the 4D atlas JSON data with temporal analysis."""
    with open(filepath, 'r') as f:
        return json.load(f)


def assign_credit_rating(default_probability: float) -> str:
    """
    Assign credit rating based on default probability.
    
    Rating Scale:
    - AAA (Prime): < 1%
    - AA (High Grade): < 5%
    - A (Upper Medium): < 10%
    - BBB (Investment Grade): < 20%
    - BB (Speculative): < 30%
    - B (Highly Speculative): < 50%
    - C (Junk): >= 50%
    """
    # Handle both decimal (0.01) and percentage (1.0) formats
    if default_probability <= 1.0:
        dp_pct = default_probability * 100
    else:
        dp_pct = default_probability
    
    if dp_pct < 1:
        return 'AAA'
    elif dp_pct < 5:
        return 'AA'
    elif dp_pct < 10:
        return 'A'
    elif dp_pct < 20:
        return 'BBB'
    elif dp_pct < 30:
        return 'BB'
    elif dp_pct < 50:
        return 'B'
    else:
        return 'C'


def get_rating_index(rating: str) -> int:
    """Get numeric index of rating (lower is better)."""
    try:
        return RATING_ORDER.index(rating)
    except ValueError:
        return len(RATING_ORDER)  # Unknown ratings are worst


def calculate_historical_ratings(temporal_analysis: dict) -> dict:
    """
    Calculate ratings for each year in the temporal history.
    
    Returns dict with year -> rating mapping.
    """
    history = temporal_analysis.get('history', [])
    ratings = {}
    
    for entry in history:
        year = entry.get('year')
        default_prob = entry.get('default_prob', 0.0)
        if year:
            ratings[year] = assign_credit_rating(default_prob)
    
    return ratings


def determine_outlook(ratings: dict) -> dict:
    """
    Determine credit rating outlook based on trajectory from 2030 to 2050.
    
    Returns:
        dict with 'outlook' and optionally 'projected_downgrade_year'
    """
    rating_2030 = ratings.get(2030)
    rating_2040 = ratings.get(2040)
    rating_2050 = ratings.get(2050)
    
    if not all([rating_2030, rating_2050]):
        return {'outlook': 'Unknown', 'projected_downgrade_year': None}
    
    idx_2030 = get_rating_index(rating_2030)
    idx_2040 = get_rating_index(rating_2040) if rating_2040 else idx_2030
    idx_2050 = get_rating_index(rating_2050)
    
    result = {}
    
    # Compare 2030 to 2050 (higher index = worse rating)
    if idx_2030 == idx_2050:
        result['outlook'] = 'Stable'
        result['projected_downgrade_year'] = None
    elif idx_2030 < idx_2050:
        # Rating worsens over time (e.g., AA to B)
        result['outlook'] = 'Negative Watch'
        # Estimate when downgrade occurs based on trajectory
        result['projected_downgrade_year'] = estimate_downgrade_year(
            idx_2030, idx_2040, idx_2050
        )
    else:
        # Rating improves over time (e.g., B to BB)
        result['outlook'] = 'Positive'
        result['projected_downgrade_year'] = None
    
    # Add rating trajectory for transparency
    result['rating_trajectory'] = {
        '2030': rating_2030,
        '2040': rating_2040,
        '2050': rating_2050
    }
    
    return result


def estimate_downgrade_year(idx_2030: int, idx_2040: int, idx_2050: int) -> Optional[int]:
    """
    Estimate when the first downgrade occurs based on rating trajectory.
    
    Uses linear interpolation between data points to estimate
    when the rating first changes.
    """
    # If rating changed by 2040
    if idx_2040 > idx_2030:
        # Linear interpolation between 2030 and 2040
        change_ratio = (idx_2040 - idx_2030) / max(idx_2050 - idx_2030, 1)
        # Estimate year when first notch downgrade happens
        years_to_first_change = int(10 * (1 / max(idx_2040 - idx_2030, 1)))
        return min(2030 + max(years_to_first_change, 1), 2040)
    elif idx_2050 > idx_2030:
        # Change happens between 2040 and 2050
        # Estimate midpoint
        return 2045 if idx_2050 > idx_2040 else 2038
    
    return None


def process_asset(asset: dict) -> dict:
    """
    Process a single asset to add outlook information.
    """
    temporal = asset.get('temporal_analysis', {})
    
    if not temporal or not temporal.get('history'):
        # No temporal data - return asset unchanged
        return asset
    
    # Calculate historical ratings
    historical_ratings = calculate_historical_ratings(temporal)
    
    # Determine outlook
    outlook_data = determine_outlook(historical_ratings)
    
    # Update market_intelligence with outlook
    updated_asset = asset.copy()
    
    if 'market_intelligence' not in updated_asset:
        updated_asset['market_intelligence'] = {}
    
    updated_asset['market_intelligence']['outlook'] = outlook_data['outlook']
    updated_asset['market_intelligence']['projected_downgrade_year'] = outlook_data['projected_downgrade_year']
    updated_asset['market_intelligence']['rating_trajectory'] = outlook_data['rating_trajectory']
    
    return updated_asset


def generate_outlook_report(assets: list[dict]) -> None:
    """Print summary of outlook distribution."""
    outlook_counts = {'Stable': 0, 'Negative Watch': 0, 'Positive': 0, 'Unknown': 0}
    downgrade_years = []
    
    for asset in assets:
        mi = asset.get('market_intelligence', {})
        outlook = mi.get('outlook', 'Unknown')
        outlook_counts[outlook] = outlook_counts.get(outlook, 0) + 1
        
        if mi.get('projected_downgrade_year'):
            downgrade_years.append(mi['projected_downgrade_year'])
    
    print("\n" + "="*60)
    print("CREDIT RATING OUTLOOK SUMMARY")
    print("="*60)
    
    print("\nOutlook Distribution:")
    for outlook, count in sorted(outlook_counts.items()):
        if count > 0:
            pct = (count / len(assets)) * 100
            print(f"  {outlook}: {count} assets ({pct:.1f}%)")
    
    if downgrade_years:
        print(f"\nProjected Downgrade Timeline:")
        print(f"  Earliest: {min(downgrade_years)}")
        print(f"  Latest: {max(downgrade_years)}")
        print(f"  Average: {sum(downgrade_years)/len(downgrade_years):.0f}")
    
    # Show examples of each outlook type
    print("\nSample Assets by Outlook:")
    shown = {'Stable': False, 'Negative Watch': False, 'Positive': False}
    
    for asset in assets:
        mi = asset.get('market_intelligence', {})
        outlook = mi.get('outlook')
        if outlook in shown and not shown[outlook]:
            name = asset.get('target', {}).get('name', 'Unknown')
            trajectory = mi.get('rating_trajectory', {})
            print(f"\n  [{outlook}] {name}")
            print(f"    2030: {trajectory.get('2030')} → 2040: {trajectory.get('2040')} → 2050: {trajectory.get('2050')}")
            if mi.get('projected_downgrade_year'):
                print(f"    Projected Downgrade: {mi['projected_downgrade_year']}")
            shown[outlook] = True


def save_final_atlas(assets: list[dict], output_path: str) -> None:
    """Save the final atlas as a pure JSON array."""
    with open(output_path, 'w') as f:
        json.dump(assets, f, indent=2)
    print(f"\nSaved {len(assets)} assets with outlook data to {output_path}")


def main():
    """Main execution function."""
    input_path = '/workspace/adaptmetric-backend/global_atlas_4d.json'
    output_path = '/workspace/adaptmetric-backend/global_atlas_final.json'
    
    print("="*60)
    print("ADAPTMETRIC OUTLOOK ENGINE")
    print("Credit Rating Outlook Calculator")
    print("="*60)
    
    # Load data
    print(f"\nLoading data from {input_path}...")
    assets = load_data(input_path)
    print(f"Loaded {len(assets)} assets with temporal analysis")
    
    # Process each asset
    print("\nCalculating credit rating outlooks...")
    processed_assets = [process_asset(asset) for asset in assets]
    
    # Generate report
    generate_outlook_report(processed_assets)
    
    # Save output
    save_final_atlas(processed_assets, output_path)
    
    print("\n" + "="*60)
    print("OUTLOOK ENGINE COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
