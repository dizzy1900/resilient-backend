#!/usr/bin/env python3
"""
Portfolio Optimizer - Tiered Intervention Strategy Analyzer

Compares multiple adaptation strategies (tiers) for agriculture and coastal projects,
calculates ROI for each, and recommends the optimal intervention path.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class InterventionTier:
    """Represents a single intervention tier with cost and effect."""
    name: str
    cost: float
    stress_reduction_pct: float  # For agriculture: water/heat stress reduction
    # For coastal: relative reduction in default probability


# Define intervention tiers
AGRICULTURE_TIERS = [
    InterventionTier("Regenerative", cost=200, stress_reduction_pct=10),
    InterventionTier("Genetics", cost=600, stress_reduction_pct=25),
    InterventionTier("Infrastructure", cost=2500, stress_reduction_pct=60),
]

COASTAL_TIERS = [
    InterventionTier("Nature-Based", cost=1_000_000, stress_reduction_pct=10),
    InterventionTier("Hybrid", cost=5_000_000, stress_reduction_pct=30),
    InterventionTier("Hard Wall", cost=20_000_000, stress_reduction_pct=80),
]


def calculate_agriculture_stress(location: Dict[str, Any]) -> float:
    """
    Calculate the stress level for an agriculture project.
    
    Stress is derived from:
    - Yield loss (100 - standard_yield_pct)
    - Water stress sensitivity from sensitivity analysis
    - Climate sensitivity
    
    Returns a stress value between 0 and 100.
    """
    stress = 0.0
    
    # Get yield loss as baseline stress
    crop_analysis = location.get("crop_analysis", {})
    standard_yield = crop_analysis.get("standard_yield_pct", 100)
    yield_loss = 100 - standard_yield
    stress += yield_loss
    
    # Add water stress sensitivity
    sensitivity = location.get("sensitivity_analysis", {})
    for ranking in sensitivity.get("sensitivity_ranking", []):
        driver = ranking.get("driver", "")
        if "Water Stress" in driver:
            impact = abs(ranking.get("impact_pct", 0))
            # Scale water stress impact (typically 0-100% range)
            stress += impact * 0.3
            break
    
    # Cap stress at 100%
    return min(stress, 100.0)


def calculate_coastal_risk(location: Dict[str, Any]) -> float:
    """
    Calculate the risk level for a coastal project.
    
    Risk is derived from:
    - Default probability from Monte Carlo
    - Flood depth and elevation relative to water level
    - Water stress sensitivity
    
    Returns a risk value between 0 and 100.
    """
    risk = 0.0
    
    # Get default probability as baseline risk
    monte_carlo = location.get("monte_carlo_analysis", {})
    default_prob = monte_carlo.get("default_probability", 0)
    risk += default_prob
    
    # Add flood risk factors
    flood_risk = location.get("flood_risk", {})
    input_conditions = location.get("input_conditions", {})
    
    elevation = flood_risk.get("elevation_m", 100)
    total_water_level = input_conditions.get("total_water_level_m", 0)
    
    # Calculate elevation margin (how close to flooding)
    margin = elevation - total_water_level
    if margin < 5:
        risk += (5 - margin) * 10  # Add risk for low margin
    
    # Add water stress sensitivity
    sensitivity = location.get("sensitivity_analysis", {})
    for ranking in sensitivity.get("sensitivity_ranking", []):
        driver = ranking.get("driver", "")
        if "Water Stress" in driver:
            impact = abs(ranking.get("impact_pct", 0))
            risk += impact * 0.2
            break
    
    # Cap risk at 100%
    return min(risk, 100.0)


def calculate_avoided_loss(
    location: Dict[str, Any],
    stress_or_risk: float,
    reduction_pct: float,
    tier_name: str
) -> float:
    """
    Calculate the NPV benefit (avoided loss) from applying an intervention.
    
    Incorporates threshold effects: higher stress locations benefit disproportionately
    from more aggressive interventions due to non-linear damage curves.
    
    Args:
        location: The location data
        stress_or_risk: Current stress (agriculture) or risk (coastal) level
        reduction_pct: Percentage reduction from the intervention tier
        tier_name: Name of the intervention tier
    
    Returns:
        Estimated avoided loss in USD
    """
    project_type = location.get("project_type", "")
    
    # Get baseline NPV for scaling
    financial = location.get("financial_analysis", {})
    monte_carlo = location.get("monte_carlo_analysis", {})
    
    baseline_npv = financial.get("npv_usd", 0) or monte_carlo.get("mean_npv", 0)
    
    # Non-linear stress response: high stress locations benefit more from aggressive interventions
    # This models threshold effects in climate adaptation
    stress_factor = stress_or_risk / 100
    
    # Effectiveness multiplier based on stress level and tier aggression
    # Higher tiers become more effective at higher stress levels
    if tier_name in ["Infrastructure", "Hard Wall"]:
        # Tier 3: Most effective at high stress (exponential scaling)
        effectiveness_mult = 1 + (stress_factor ** 1.5) * 3
    elif tier_name in ["Genetics", "Hybrid"]:
        # Tier 2: Moderately effective at medium-high stress
        effectiveness_mult = 1 + (stress_factor ** 1.2) * 1.5
    else:
        # Tier 1: Linear scaling (baseline)
        effectiveness_mult = 1 + stress_factor * 0.5
    
    if project_type == "agriculture":
        # For agriculture: benefit scales with yield protection
        stress_value = stress_factor * baseline_npv
        avoided_loss = stress_value * (reduction_pct / 100) * effectiveness_mult
        
        # Factor in existing avoided loss percentage
        crop_analysis = location.get("crop_analysis", {})
        existing_avoided = crop_analysis.get("avoided_loss_pct", 0)
        
        # Boost benefit if there's already significant yield improvement potential
        if existing_avoided > 5:
            avoided_loss *= (1 + existing_avoided / 100)
        
        # High stress locations (>30%) need robust solutions - threshold effect
        if stress_or_risk > 30 and tier_name in ["Genetics", "Infrastructure"]:
            avoided_loss *= 1.5
        if stress_or_risk > 50 and tier_name == "Infrastructure":
            avoided_loss *= 2.0
            
    elif project_type == "coastal":
        # For coastal: benefit scales with risk reduction
        var_95 = monte_carlo.get("VaR_95", 0)
        risk_value = max(baseline_npv, abs(var_95)) * stress_factor
        
        # Higher-risk coastal locations have more to gain
        default_prob = monte_carlo.get("default_probability", 0)
        risk_multiplier = 1 + (default_prob / 50)
        
        avoided_loss = risk_value * (reduction_pct / 100) * risk_multiplier * effectiveness_mult
        
        # High risk locations (>30%) need robust solutions - threshold effect
        if stress_or_risk > 30 and tier_name in ["Hybrid", "Hard Wall"]:
            avoided_loss *= 1.5
        if stress_or_risk > 50 and tier_name == "Hard Wall":
            avoided_loss *= 2.0
        
    else:
        avoided_loss = 0
    
    return round(avoided_loss, 2)


def calculate_roi(benefit: float, cost: float) -> float:
    """Calculate ROI as (Benefit - Cost) / Cost * 100."""
    if cost <= 0:
        return 0.0
    return round(((benefit - cost) / cost) * 100, 2)


def analyze_location(location: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Analyze a single location and generate adaptation portfolio.
    
    Returns the adaptation_portfolio object or None if not applicable.
    """
    project_type = location.get("project_type", "")
    
    if project_type == "agriculture":
        tiers = AGRICULTURE_TIERS
        stress_or_risk = calculate_agriculture_stress(location)
    elif project_type == "coastal":
        tiers = COASTAL_TIERS
        stress_or_risk = calculate_coastal_risk(location)
    else:
        return None
    
    options = []
    best_option = None
    best_roi = float('-inf')
    
    for tier in tiers:
        benefit = calculate_avoided_loss(location, stress_or_risk, tier.stress_reduction_pct, tier.name)
        roi = calculate_roi(benefit, tier.cost)
        
        option = {
            "tier": tier.name,
            "cost": tier.cost,
            "roi": roi,
            "benefit": benefit
        }
        options.append(option)
        
        if roi > best_roi:
            best_roi = roi
            best_option = tier.name
    
    return {
        "options": options,
        "recommended_strategy": best_option,
        "stress_level": round(stress_or_risk, 2),
        "analysis_timestamp": datetime.now(timezone.utc).isoformat()
    }


def optimize_portfolio(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the portfolio optimization tournament across all locations.
    
    Args:
        input_path: Path to the input JSON file
        output_path: Path to save the optimized output
    
    Returns:
        Summary statistics of the optimization run
    """
    # Load data
    with open(input_path, 'r') as f:
        locations = json.load(f)
    
    # Statistics tracking
    stats = {
        "total_locations": len(locations),
        "agriculture_analyzed": 0,
        "coastal_analyzed": 0,
        "skipped": 0,
        "recommendations": {
            "Regenerative": 0,
            "Genetics": 0,
            "Infrastructure": 0,
            "Nature-Based": 0,
            "Hybrid": 0,
            "Hard Wall": 0
        }
    }
    
    # Process each location
    for location in locations:
        portfolio = analyze_location(location)
        
        if portfolio:
            location["adaptation_portfolio"] = portfolio
            
            # Update stats
            project_type = location.get("project_type", "")
            if project_type == "agriculture":
                stats["agriculture_analyzed"] += 1
            elif project_type == "coastal":
                stats["coastal_analyzed"] += 1
            
            recommended = portfolio.get("recommended_strategy")
            if recommended in stats["recommendations"]:
                stats["recommendations"][recommended] += 1
        else:
            stats["skipped"] += 1
    
    # Save output
    with open(output_path, 'w') as f:
        json.dump(locations, f, indent=2)
    
    return stats


def print_summary(stats: Dict[str, Any], output_path: str):
    """Print a formatted summary of the optimization results."""
    print("\n" + "=" * 60)
    print("PORTFOLIO OPTIMIZATION COMPLETE")
    print("=" * 60)
    print(f"\nTotal Locations: {stats['total_locations']}")
    print(f"Agriculture Projects Analyzed: {stats['agriculture_analyzed']}")
    print(f"Coastal Projects Analyzed: {stats['coastal_analyzed']}")
    print(f"Skipped (unknown type): {stats['skipped']}")
    
    print("\n" + "-" * 40)
    print("RECOMMENDED STRATEGIES BY TIER:")
    print("-" * 40)
    
    # Agriculture tiers
    print("\nAgriculture:")
    for tier in ["Regenerative", "Genetics", "Infrastructure"]:
        count = stats["recommendations"][tier]
        print(f"  {tier}: {count} locations")
    
    # Coastal tiers
    print("\nCoastal:")
    for tier in ["Nature-Based", "Hybrid", "Hard Wall"]:
        count = stats["recommendations"][tier]
        print(f"  {tier}: {count} locations")
    
    print(f"\nOutput saved to: {output_path}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Portfolio Optimizer - Tiered Intervention Strategy Analyzer"
    )
    parser.add_argument(
        "--input", "-i",
        default="global_atlas_satellite_enriched.json",
        help="Input JSON file path (default: global_atlas_satellite_enriched.json)"
    )
    parser.add_argument(
        "--output", "-o",
        default="global_atlas_optimized.json",
        help="Output JSON file path (default: global_atlas_optimized.json)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress summary output"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    base_dir = Path(__file__).parent
    input_path = base_dir / args.input if not Path(args.input).is_absolute() else Path(args.input)
    output_path = base_dir / args.output if not Path(args.output).is_absolute() else Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    print(f"Loading data from: {input_path}")
    stats = optimize_portfolio(str(input_path), str(output_path))
    
    if not args.quiet:
        print_summary(stats, str(output_path))
    
    return 0


if __name__ == "__main__":
    exit(main())
