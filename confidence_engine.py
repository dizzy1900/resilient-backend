#!/usr/bin/env python3
"""
Confidence Engine

Calculates prediction confidence scores based on Monte Carlo analysis results.
Uses Coefficient of Variation (CV) = std_dev_npv / mean_npv to determine stability.

Scoring:
- CV < 0.2: 'High' (Very stable prediction)
- 0.2 <= CV < 0.5: 'Medium' (Standard volatility)
- CV >= 0.5: 'Low' (Highly uncertain outcome)
"""

import json
import sys
from pathlib import Path
from typing import Literal

ConfidenceLevel = Literal["High", "Medium", "Low"]


def calculate_confidence(mean_npv: float, std_dev_npv: float) -> ConfidenceLevel:
    """
    Calculate confidence level based on Coefficient of Variation.
    
    Args:
        mean_npv: Mean NPV from Monte Carlo simulation
        std_dev_npv: Standard deviation of NPV from Monte Carlo simulation
    
    Returns:
        Confidence level: 'High', 'Medium', or 'Low'
    """
    # Handle edge case where mean_npv is zero or negative
    if mean_npv <= 0:
        return "Low"
    
    cv = std_dev_npv / mean_npv
    
    if cv < 0.2:
        return "High"
    elif cv < 0.5:
        return "Medium"
    else:
        return "Low"


def process_portfolio(input_path: str, output_path: str) -> dict:
    """
    Process portfolio JSON to add confidence scores.
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file
    
    Returns:
        Summary statistics of the processing
    """
    # Load input data
    with open(input_path, 'r') as f:
        portfolio = json.load(f)
    
    stats = {"High": 0, "Medium": 0, "Low": 0, "total": 0}
    
    for entry in portfolio:
        stats["total"] += 1
        
        # Extract Monte Carlo analysis data
        monte_carlo = entry.get("monte_carlo_analysis", {})
        mean_npv = monte_carlo.get("mean_npv", 0)
        std_dev_npv = monte_carlo.get("std_dev_npv", 0)
        
        # Calculate confidence score
        confidence = calculate_confidence(mean_npv, std_dev_npv)
        stats[confidence] += 1
        
        # Update executive_summary with confidence note
        if "executive_summary" in entry:
            # Remove any existing confidence note first (for idempotency)
            summary = entry["executive_summary"]
            for level in ["High", "Medium", "Low"]:
                marker = f" (Model Confidence: {level})"
                if summary.endswith(marker):
                    summary = summary[:-len(marker)]
            entry["executive_summary"] = f"{summary} (Model Confidence: {confidence})"
        
        # Add confidence_score to market_intelligence
        if "market_intelligence" in entry:
            entry["market_intelligence"]["confidence_score"] = confidence
        else:
            entry["market_intelligence"] = {"confidence_score": confidence}
    
    # Save output as pure JSON array
    with open(output_path, 'w') as f:
        json.dump(portfolio, f, indent=2)
    
    return stats


def main():
    """Main entry point for the confidence engine."""
    # Default paths
    base_path = Path(__file__).parent
    input_path = base_path / "global_atlas_final_portfolio.json"
    output_path = base_path / "global_atlas_complete.json"
    
    # Allow command line overrides
    if len(sys.argv) >= 2:
        input_path = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    print(f"Processing: {input_path}")
    print(f"Output: {output_path}")
    
    stats = process_portfolio(str(input_path), str(output_path))
    
    print(f"\nConfidence Score Summary:")
    print(f"  Total entries: {stats['total']}")
    print(f"  High confidence:   {stats['High']:3d} ({100*stats['High']/stats['total']:.1f}%)")
    print(f"  Medium confidence: {stats['Medium']:3d} ({100*stats['Medium']/stats['total']:.1f}%)")
    print(f"  Low confidence:    {stats['Low']:3d} ({100*stats['Low']/stats['total']:.1f}%)")
    print(f"\nOutput saved to: {output_path}")


if __name__ == "__main__":
    main()
