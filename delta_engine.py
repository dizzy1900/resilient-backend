#!/usr/bin/env python3
"""
Delta Engine

Calculates sweep deltas between two portfolio risk states,
surfacing directional movement, severity, and stranded asset changes.
"""

from __future__ import annotations


def calculate_sweep_delta(previous_state: dict, current_state: dict) -> dict:
    """
    Compare two portfolio risk states and return a structured delta summary.

    Args:
        previous_state: Dict containing at minimum 'risk_score' and 'stranded_assets'.
        current_state:  Dict containing at minimum 'risk_score' and 'stranded_assets'.

    Returns:
        A summary dict with risk_delta, direction, severity, new_stranded_assets,
        and a human-readable message.
    """
    prev_score: float = previous_state["risk_score"]
    curr_score: float = current_state["risk_score"]

    # Percentage change (relative to previous score)
    if prev_score == 0:
        pct_change = 0.0
    else:
        pct_change = ((curr_score - prev_score) / abs(prev_score)) * 100

    abs_change = abs(pct_change)

    # Direction
    if pct_change > 0:
        direction = "escalated"
    elif pct_change < 0:
        direction = "deescalated"
    else:
        direction = "unchanged"

    # Severity
    if abs_change > 10:
        severity = "critical"
    elif abs_change > 5:
        severity = "moderate"
    else:
        severity = "low"

    # Stranded assets delta
    prev_stranded: int = len(previous_state.get("stranded_assets", []))
    curr_stranded: int = len(current_state.get("stranded_assets", []))
    new_stranded = max(curr_stranded - prev_stranded, 0)

    # Format risk_delta string
    sign = "+" if pct_change >= 0 else ""
    risk_delta = f"{sign}{pct_change:.1f}%"

    # Human-readable message
    direction_label = {
        "escalated": "escalated",
        "deescalated": "de-escalated",
        "unchanged": "remained unchanged",
    }[direction]

    if new_stranded > 0:
        asset_clause = f" {new_stranded} new asset{'s' if new_stranded != 1 else ''} flagged as stranded."
    else:
        asset_clause = ""

    message = (
        f"Portfolio risk has {direction_label} {severity}ly.{asset_clause}"
        if direction != "unchanged"
        else f"Portfolio risk is unchanged.{asset_clause}"
    )

    return {
        "risk_delta": risk_delta,
        "direction": direction,
        "severity": severity,
        "new_stranded_assets": new_stranded,
        "message": message,
    }
