#!/usr/bin/env python3
"""
Resilient Score Engine

Calculates a composite Resilient Score (0-1000) from simulation results.
The score combines avoided-loss ROI, confidence level, and market outlook
into a single investment-grade metric.

Score Bands:
- 750-1000: STRONG BUY
- 500-749:  BUY
- 250-499:  HOLD
- 0-249:    REVIEW
"""

from typing import Dict, Any


def extract_score_inputs(simulation_result: dict) -> dict:
    """
    Safely extract all scoring inputs from a raw simulation result dictionary.

    Uses .get() with fallback defaults for optional fields:
    - baseline_npv defaults to npv_usd * 0.7
    - intervention_npv defaults to npv_usd
    - intervention_cost defaults to 50000
    - outlook defaults to "Stable"
    - intervention_name defaults to "Climate Adaptation"

    Args:
        simulation_result: Raw dictionary returned by the simulation pipeline.

    Returns:
        Dictionary with normalised scoring inputs.
    """
    financial = simulation_result.get("financial_analysis", {})
    adaptation = simulation_result.get("adaptation_analysis", {})
    monte_carlo = simulation_result.get("monte_carlo_analysis", {})
    market = simulation_result.get("market_intelligence", {})

    npv_usd = financial.get("npv_usd", 0.0)

    return {
        "npv_usd": npv_usd,
        "baseline_npv": adaptation.get("baseline_npv", npv_usd * 0.7),
        "intervention_npv": adaptation.get("intervention_npv", npv_usd),
        "intervention_cost": adaptation.get("intervention_cost", 50000),
        "confidence_level": monte_carlo.get("confidence_level", "Low"),
        "outlook": market.get("outlook", "Stable"),
        "default_probability": monte_carlo.get("default_probability", 0.0),
        "intervention_name": adaptation.get("intervention_name", "Climate Adaptation"),
    }


def calculate_resilient_score(simulation_result: dict) -> Dict[str, Any]:
    """
    Calculate the Resilient Score from a simulation result dictionary.

    The score is built from three components:
    1. Base score (0-800) derived from avoided-loss ROI.
    2. Confidence bonus (0-100) based on Monte Carlo confidence level.
    3. Outlook bonus (0-100) based on market outlook.

    Args:
        simulation_result: Raw dictionary returned by the simulation pipeline.

    Returns:
        Dictionary containing the resilient_score (0-1000), score_label,
        avoided-loss projections, and a breakdown of scoring components.
    """
    inputs = extract_score_inputs(simulation_result)

    npv_usd = inputs["npv_usd"]
    baseline_npv = inputs["baseline_npv"]
    intervention_npv = inputs["intervention_npv"]
    intervention_cost = inputs["intervention_cost"]
    confidence_level = inputs["confidence_level"]
    outlook = inputs["outlook"]
    intervention_name = inputs["intervention_name"]

    # --- avoided loss ---
    avoided_loss_usd = intervention_npv - baseline_npv

    if intervention_cost != 0:
        avoided_loss_roi_pct = (avoided_loss_usd / intervention_cost) * 100
    else:
        avoided_loss_roi_pct = 0.0

    # temporal projections
    avoided_loss_5yr = avoided_loss_usd * 0.35
    avoided_loss_10yr = avoided_loss_usd * 0.65
    avoided_loss_15yr = avoided_loss_usd * 0.85
    avoided_loss_20yr = avoided_loss_usd * 1.0

    # --- base score (0-800) ---
    roi = avoided_loss_roi_pct
    if roi < 0:
        base_score = 0
    elif roi <= 50:
        base_score = roi * 4
    elif roi <= 200:
        base_score = 200 + (roi - 50) * 2
    elif roi <= 500:
        base_score = 500 + (roi - 200) * 1
    else:
        base_score = 800
    base_score = min(int(base_score), 800)

    # --- confidence bonus (0-100) ---
    confidence_map = {"High": 100, "Medium": 50, "Low": 0}
    confidence_bonus = confidence_map.get(confidence_level, 0)

    # --- outlook bonus (0-100) ---
    outlook_map = {"Positive": 100, "Stable": 50, "Negative Watch": 0}
    outlook_bonus = outlook_map.get(outlook, 0)

    # --- final score ---
    resilient_score = min(1000, round(base_score + confidence_bonus + outlook_bonus))

    # --- label ---
    if resilient_score >= 750:
        score_label = "STRONG BUY"
    elif resilient_score >= 500:
        score_label = "BUY"
    elif resilient_score >= 250:
        score_label = "HOLD"
    else:
        score_label = "REVIEW"

    return {
        "resilient_score": resilient_score,
        "score_label": score_label,
        "avoided_loss_usd": avoided_loss_usd,
        "avoided_loss_roi_pct": avoided_loss_roi_pct,
        "avoided_loss_5yr": avoided_loss_5yr,
        "avoided_loss_10yr": avoided_loss_10yr,
        "avoided_loss_15yr": avoided_loss_15yr,
        "avoided_loss_20yr": avoided_loss_20yr,
        "confidence_level": confidence_level,
        "outlook": outlook,
        "intervention_name": intervention_name,
        "score_breakdown": {
            "base_score": base_score,
            "confidence_bonus": confidence_bonus,
            "outlook_bonus": outlook_bonus,
        },
    }


if __name__ == "__main__":
    import json

    sample_simulation = {
        "financial_analysis": {
            "npv_usd": 1_200_000,
        },
        "adaptation_analysis": {
            "baseline_npv": 840_000,
            "intervention_npv": 1_200_000,
            "intervention_cost": 120_000,
            "intervention_name": "Flood Barrier System",
        },
        "monte_carlo_analysis": {
            "confidence_level": "High",
            "default_probability": 0.05,
        },
        "market_intelligence": {
            "outlook": "Positive",
        },
    }

    result = calculate_resilient_score(sample_simulation)
    print(json.dumps(result, indent=2))
