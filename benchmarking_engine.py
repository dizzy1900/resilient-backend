#!/usr/bin/env python3
"""
Benchmarking Engine - 'Rating Agency' Logic for AdaptMetric Assets

This module benchmarks climate adaptation assets against their peers,
assigning credit ratings, sector ranks, and percentiles to create
a 'Rated Universe' for investment decision-making.
"""

import json
import statistics
from typing import Any
from collections import defaultdict


def load_data(filepath: str) -> list[dict]:
    """Load the enriched atlas JSON data."""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_metrics(asset: dict) -> dict:
    """
    Extract benchmarking metrics from an asset based on its project type.
    
    Returns normalized metrics for comparison:
    - npv_usd: Net Present Value
    - roi_pct: Return on Investment percentage
    - default_probability: Probability of default from Monte Carlo
    """
    project_type = asset.get('project_type', 'unknown')
    mc = asset.get('monte_carlo_analysis', {})
    
    # Default probability is available for all types
    default_prob = mc.get('default_probability', 0.0)
    
    if project_type == 'agriculture':
        fa = asset.get('financial_analysis', {})
        npv = fa.get('npv_usd', 0.0)
        capex = fa.get('assumptions', {}).get('capex', 1.0)  # Avoid div by zero
        roi_pct = (npv / capex) * 100 if capex > 0 else 0.0
        
    elif project_type == 'coastal':
        # For coastal: use monte carlo mean_npv and derive ROI from VaR
        npv = mc.get('mean_npv', 0.0)
        var_95 = mc.get('VaR_95', 1.0)
        # ROI approximation: risk-adjusted return based on VaR
        roi_pct = ((npv - var_95) / max(var_95, 1.0)) * 100 if var_95 > 0 else npv * 10
        
    elif project_type == 'flood':
        # For flood: use monte carlo mean_npv  
        npv = mc.get('mean_npv', 0.0)
        var_95 = mc.get('VaR_95', 1.0)
        roi_pct = ((npv - var_95) / max(var_95, 1.0)) * 100 if var_95 > 0 else npv * 10
        
    else:
        npv = mc.get('mean_npv', 0.0)
        roi_pct = 0.0
    
    return {
        'npv_usd': npv,
        'roi_pct': roi_pct,
        'default_probability': default_prob
    }


def assign_credit_rating(default_probability: float) -> dict:
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
    dp_pct = default_probability * 100  # Convert to percentage if decimal
    
    # Handle both decimal (0.01) and percentage (1.0) formats
    if default_probability <= 1.0:
        dp_pct = default_probability * 100
    else:
        dp_pct = default_probability
    
    if dp_pct < 1:
        return {'rating': 'AAA', 'grade': 'Prime', 'investment_grade': True}
    elif dp_pct < 5:
        return {'rating': 'AA', 'grade': 'High Grade', 'investment_grade': True}
    elif dp_pct < 10:
        return {'rating': 'A', 'grade': 'Upper Medium', 'investment_grade': True}
    elif dp_pct < 20:
        return {'rating': 'BBB', 'grade': 'Investment Grade', 'investment_grade': True}
    elif dp_pct < 30:
        return {'rating': 'BB', 'grade': 'Speculative', 'investment_grade': False}
    elif dp_pct < 50:
        return {'rating': 'B', 'grade': 'Highly Speculative', 'investment_grade': False}
    else:
        return {'rating': 'C', 'grade': 'Junk', 'investment_grade': False}


def calculate_group_statistics(assets: list[dict]) -> dict:
    """
    Calculate mean and standard deviation for key metrics within a group.
    """
    npv_values = [extract_metrics(a)['npv_usd'] for a in assets]
    roi_values = [extract_metrics(a)['roi_pct'] for a in assets]
    dp_values = [extract_metrics(a)['default_probability'] for a in assets]
    
    def safe_stats(values: list) -> dict:
        if len(values) < 2:
            return {'mean': values[0] if values else 0.0, 'std_dev': 0.0}
        return {
            'mean': statistics.mean(values),
            'std_dev': statistics.stdev(values)
        }
    
    return {
        'npv_usd': safe_stats(npv_values),
        'roi_pct': safe_stats(roi_values),
        'default_probability': safe_stats(dp_values),
        'count': len(assets)
    }


def calculate_percentile(value: float, all_values: list[float], higher_is_better: bool = True) -> float:
    """
    Calculate the percentile rank of a value within a distribution.
    Returns a value between 0 and 100.
    """
    if not all_values or len(all_values) == 1:
        return 100.0 if higher_is_better else 0.0
    
    sorted_values = sorted(all_values)
    
    if higher_is_better:
        # Count how many values are less than the current value
        count_below = sum(1 for v in sorted_values if v < value)
    else:
        # For metrics where lower is better (like default_probability)
        count_below = sum(1 for v in sorted_values if v > value)
    
    return round((count_below / len(all_values)) * 100, 1)


def benchmark_assets(assets: list[dict]) -> list[dict]:
    """
    Main benchmarking function that processes all assets and adds market intelligence.
    """
    # Group assets by project_type
    groups = defaultdict(list)
    for i, asset in enumerate(assets):
        ptype = asset.get('project_type', 'unknown')
        groups[ptype].append((i, asset))
    
    # Calculate statistics for each group
    group_stats = {}
    for ptype, group_assets in groups.items():
        group_stats[ptype] = calculate_group_statistics([a for _, a in group_assets])
    
    # Process each asset
    rated_assets = []
    
    for ptype, group_assets in groups.items():
        # Extract metrics for ranking
        metrics_list = [(i, asset, extract_metrics(asset)) for i, asset in group_assets]
        
        # Sort by NPV (primary) and ROI (secondary) for ranking - higher is better
        sorted_by_npv = sorted(metrics_list, key=lambda x: x[2]['npv_usd'], reverse=True)
        sorted_by_roi = sorted(metrics_list, key=lambda x: x[2]['roi_pct'], reverse=True)
        
        # Create lookup for ranks
        npv_rank = {item[0]: rank + 1 for rank, item in enumerate(sorted_by_npv)}
        roi_rank = {item[0]: rank + 1 for rank, item in enumerate(sorted_by_roi)}
        
        # Get all values for percentile calculations
        all_npv = [m[2]['npv_usd'] for m in metrics_list]
        all_roi = [m[2]['roi_pct'] for m in metrics_list]
        all_dp = [m[2]['default_probability'] for m in metrics_list]
        
        group_size = len(group_assets)
        
        for idx, asset, metrics in metrics_list:
            # Credit rating based on default probability
            credit = assign_credit_rating(metrics['default_probability'])
            
            # Calculate percentiles
            npv_percentile = calculate_percentile(metrics['npv_usd'], all_npv, higher_is_better=True)
            roi_percentile = calculate_percentile(metrics['roi_pct'], all_roi, higher_is_better=True)
            risk_percentile = calculate_percentile(metrics['default_probability'], all_dp, higher_is_better=False)
            
            # Composite score (weighted average of percentiles)
            composite_score = round(
                (npv_percentile * 0.4) + (roi_percentile * 0.3) + (risk_percentile * 0.3),
                1
            )
            
            # Build market intelligence object
            market_intelligence = {
                'credit_rating': credit['rating'],
                'credit_grade': credit['grade'],
                'investment_grade': credit['investment_grade'],
                'sector_rank': {
                    'by_npv': npv_rank[idx],
                    'by_roi': roi_rank[idx],
                    'total_in_sector': group_size
                },
                'percentiles': {
                    'npv': npv_percentile,
                    'roi': roi_percentile,
                    'risk': risk_percentile,
                    'composite': composite_score
                },
                'sector_statistics': group_stats[ptype],
                'metrics_used': {
                    'npv_usd': round(metrics['npv_usd'], 2),
                    'roi_pct': round(metrics['roi_pct'], 2),
                    'default_probability_pct': round(metrics['default_probability'] * 100, 2)
                },
                'benchmark_summary': f"Rank #{npv_rank[idx]} of {group_size} | {int(npv_percentile)}th Percentile"
            }
            
            # Add market_intelligence to asset
            enriched_asset = asset.copy()
            enriched_asset['market_intelligence'] = market_intelligence
            rated_assets.append((idx, enriched_asset))
    
    # Sort back to original order
    rated_assets.sort(key=lambda x: x[0])
    return [asset for _, asset in rated_assets]


def save_rated_universe(assets: list[dict], output_path: str):
    """Save the rated universe as a pure JSON array."""
    with open(output_path, 'w') as f:
        json.dump(assets, f, indent=2)
    print(f"Saved {len(assets)} rated assets to {output_path}")


def print_examples(assets: list[dict], count: int = 5):
    """Print example ratings for verification."""
    print("\n" + "="*60)
    print("SAMPLE RATED ASSETS")
    print("="*60)
    
    for asset in assets[:count]:
        name = asset.get('target', {}).get('name', 'Unknown')
        ptype = asset.get('project_type', 'unknown').title()
        mi = asset.get('market_intelligence', {})
        
        rating = mi.get('credit_rating', 'N/A')
        grade = mi.get('credit_grade', '')
        rank = mi.get('sector_rank', {})
        percentiles = mi.get('percentiles', {})
        
        print(f"\n{name} ({ptype})")
        print(f"  Rating: {rating} ({grade})")
        print(f"  NPV Rank: #{rank.get('by_npv', 'N/A')} of {rank.get('total_in_sector', 'N/A')}")
        print(f"  Percentile: {percentiles.get('npv', 0)}th (NPV) | {percentiles.get('composite', 0)}th (Composite)")
        print(f"  Investment Grade: {'Yes' if mi.get('investment_grade') else 'No'}")


def print_summary_statistics(assets: list[dict]):
    """Print summary statistics across all rated assets."""
    print("\n" + "="*60)
    print("RATING DISTRIBUTION SUMMARY")
    print("="*60)
    
    # Count ratings
    rating_counts = defaultdict(int)
    sector_counts = defaultdict(int)
    
    for asset in assets:
        mi = asset.get('market_intelligence', {})
        rating = mi.get('credit_rating', 'N/A')
        ptype = asset.get('project_type', 'unknown')
        rating_counts[rating] += 1
        sector_counts[ptype] += 1
    
    print("\nBy Credit Rating:")
    for rating in ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'C']:
        if rating in rating_counts:
            print(f"  {rating}: {rating_counts[rating]} assets")
    
    print("\nBy Sector:")
    for sector, count in sorted(sector_counts.items()):
        print(f"  {sector.title()}: {count} assets")
    
    # Investment grade vs speculative
    ig_count = sum(1 for a in assets if a.get('market_intelligence', {}).get('investment_grade', False))
    print(f"\nInvestment Grade: {ig_count} ({ig_count/len(assets)*100:.1f}%)")
    print(f"Speculative Grade: {len(assets) - ig_count} ({(len(assets)-ig_count)/len(assets)*100:.1f}%)")


def main():
    """Main execution function."""
    input_path = '/workspace/adaptmetric-backend/global_atlas_satellite_enriched.json'
    output_path = '/workspace/adaptmetric-backend/global_atlas_rated.json'
    
    print("="*60)
    print("ADAPTMETRIC BENCHMARKING ENGINE")
    print("Creating Rated Universe")
    print("="*60)
    
    # Load data
    print(f"\nLoading data from {input_path}...")
    assets = load_data(input_path)
    print(f"Loaded {len(assets)} assets")
    
    # Run benchmarking
    print("\nRunning benchmarking analysis...")
    rated_assets = benchmark_assets(assets)
    
    # Print examples
    print_examples(rated_assets, count=5)
    
    # Print summary
    print_summary_statistics(rated_assets)
    
    # Save output
    print(f"\nSaving rated universe to {output_path}...")
    save_rated_universe(rated_assets, output_path)
    
    print("\n" + "="*60)
    print("BENCHMARKING COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
