#!/usr/bin/env python3
"""
Portfolio Correlation Engine

Calculates correlation of each asset's return trajectory against the global average,
classifying assets as Hedge, Neutral, or Concentrator for portfolio diversification insights.
"""

import json
import numpy as np
from typing import List, Dict, Tuple, Optional


def load_atlas(filepath: str) -> List[Dict]:
    """Load the global atlas JSON data."""
    with open(filepath, 'r') as f:
        return json.load(f)


def extract_return_vector(asset: Dict) -> Optional[np.ndarray]:
    """
    Extract NPV trajectory as a return vector from temporal_analysis.
    Returns normalized returns (percentage changes) for 2030 -> 2040 -> 2050.
    """
    temporal = asset.get('temporal_analysis', {})
    history = temporal.get('history', [])
    
    if len(history) < 3:
        return None
    
    # Sort by year to ensure correct order
    history_sorted = sorted(history, key=lambda x: x['year'])
    
    # Extract NPV values for 2030, 2040, 2050
    npv_values = [entry['npv'] for entry in history_sorted]
    
    # Calculate returns (percentage change between periods)
    # We use the raw NPV values as the "trajectory" for correlation
    # This captures the direction and magnitude of change
    return np.array(npv_values)


def build_return_vectors(assets: List[Dict]) -> Tuple[List[np.ndarray], List[int]]:
    """
    Build return vectors for all assets.
    Returns vectors and corresponding asset indices.
    """
    vectors = []
    indices = []
    
    for i, asset in enumerate(assets):
        vec = extract_return_vector(asset)
        if vec is not None:
            vectors.append(vec)
            indices.append(i)
    
    return vectors, indices


def calculate_global_average_excluding(vectors: List[np.ndarray], exclude_idx: int) -> np.ndarray:
    """
    Calculate the global average trajectory excluding one asset.
    This creates the 'market' benchmark for comparison.
    """
    other_vectors = [v for i, v in enumerate(vectors) if i != exclude_idx]
    return np.mean(other_vectors, axis=0)


def calculate_correlation(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate Pearson correlation between two vectors.
    Handles edge cases where vectors have zero variance.
    """
    # Check for zero variance (constant vectors)
    if np.std(vec1) == 0 or np.std(vec2) == 0:
        return 0.0
    
    # Calculate Pearson correlation
    correlation = np.corrcoef(vec1, vec2)[0, 1]
    
    # Handle NaN cases
    if np.isnan(correlation):
        return 0.0
    
    return correlation


def classify_correlation(correlation: float) -> Tuple[str, str]:
    """
    Classify correlation into portfolio fit category.
    Returns (category, summary_text).
    """
    if correlation < 0:
        return (
            "Hedge",
            "**PORTFOLIO FIT: Excellent.** This asset provides a natural hedge against "
            "global climate trends, diversifying risk."
        )
    elif correlation > 0.8:
        return (
            "Concentrator",
            "**PORTFOLIO FIT: Caution.** Highly correlated with broader market risks; "
            "offers little diversification."
        )
    else:
        return (
            "Neutral",
            "**PORTFOLIO FIT: Neutral.** Performance moves in line with the broader sector."
        )


def calculate_portfolio_correlations(assets: List[Dict]) -> List[Dict]:
    """
    Calculate portfolio correlations for all assets and update summaries.
    """
    # Build return vectors
    vectors, valid_indices = build_return_vectors(assets)
    
    if len(vectors) < 2:
        print("Warning: Not enough valid assets for correlation analysis")
        return assets
    
    print(f"Processing {len(vectors)} assets with valid temporal data...")
    
    # Create a mapping from valid_indices position to original asset index
    valid_set = set(valid_indices)
    
    # Calculate correlations for each asset
    for vec_idx, asset_idx in enumerate(valid_indices):
        asset = assets[asset_idx]
        
        # Get this asset's vector
        asset_vector = vectors[vec_idx]
        
        # Calculate global average excluding this asset
        global_avg = calculate_global_average_excluding(vectors, vec_idx)
        
        # Calculate correlation
        correlation = calculate_correlation(asset_vector, global_avg)
        
        # Classify and get summary text
        category, portfolio_fit_text = classify_correlation(correlation)
        
        # Add portfolio correlation data to asset
        asset['portfolio_correlation'] = {
            'correlation_vs_global': round(correlation, 4),
            'classification': category,
            'return_vector': asset_vector.tolist()
        }
        
        # Prepend portfolio fit to executive summary
        existing_summary = asset.get('executive_summary', '')
        asset['executive_summary'] = f"{portfolio_fit_text} {existing_summary}"
    
    # Handle assets without valid temporal data
    for i, asset in enumerate(assets):
        if i not in valid_set:
            asset['portfolio_correlation'] = {
                'correlation_vs_global': None,
                'classification': 'Insufficient Data',
                'return_vector': None
            }
            existing_summary = asset.get('executive_summary', '')
            asset['executive_summary'] = (
                "**PORTFOLIO FIT: Unknown.** Insufficient temporal data for correlation analysis. "
                + existing_summary
            )
    
    return assets


def save_atlas(assets: List[Dict], filepath: str):
    """Save the updated atlas as a pure JSON array."""
    with open(filepath, 'w') as f:
        json.dump(assets, f, indent=2)
    print(f"Saved {len(assets)} assets to {filepath}")


def print_correlation_summary(assets: List[Dict]):
    """Print a summary of correlation classifications."""
    hedge_count = 0
    neutral_count = 0
    concentrator_count = 0
    unknown_count = 0
    
    correlations = []
    
    for asset in assets:
        pc = asset.get('portfolio_correlation', {})
        classification = pc.get('classification', 'Unknown')
        corr = pc.get('correlation_vs_global')
        
        if classification == 'Hedge':
            hedge_count += 1
        elif classification == 'Neutral':
            neutral_count += 1
        elif classification == 'Concentrator':
            concentrator_count += 1
        else:
            unknown_count += 1
        
        if corr is not None:
            correlations.append(corr)
    
    print("\n" + "="*60)
    print("PORTFOLIO CORRELATION ANALYSIS SUMMARY")
    print("="*60)
    print(f"\nTotal Assets: {len(assets)}")
    print(f"\nClassification Breakdown:")
    print(f"  🛡️  Hedge (corr < 0):        {hedge_count:3d} assets")
    print(f"  ⚖️  Neutral (0 ≤ corr ≤ 0.8): {neutral_count:3d} assets")
    print(f"  ⚠️  Concentrator (corr > 0.8): {concentrator_count:3d} assets")
    if unknown_count > 0:
        print(f"  ❓ Unknown:                  {unknown_count:3d} assets")
    
    if correlations:
        print(f"\nCorrelation Statistics:")
        print(f"  Mean:   {np.mean(correlations):.4f}")
        print(f"  Median: {np.median(correlations):.4f}")
        print(f"  Std:    {np.std(correlations):.4f}")
        print(f"  Min:    {np.min(correlations):.4f}")
        print(f"  Max:    {np.max(correlations):.4f}")
    
    print("="*60 + "\n")


def main():
    """Main entry point."""
    input_file = 'global_atlas_final.json'
    output_file = 'global_atlas_final_portfolio.json'
    
    print(f"Loading data from {input_file}...")
    assets = load_atlas(input_file)
    print(f"Loaded {len(assets)} assets")
    
    print("\nCalculating portfolio correlations...")
    updated_assets = calculate_portfolio_correlations(assets)
    
    print_correlation_summary(updated_assets)
    
    print(f"Saving to {output_file}...")
    save_atlas(updated_assets, output_file)
    
    print("Done!")


if __name__ == '__main__':
    main()
