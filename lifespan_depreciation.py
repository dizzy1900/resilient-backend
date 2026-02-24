"""
Dynamic Asset Depreciation: climate penalty and intervention rescue.

Used by api.py. Thresholds are configurable.
"""
from __future__ import annotations

# Coastal: sea level rise (m) -> years penalty
COASTAL_SLR_PENALTY_0_5M = 5   # years if sea_level_rise > 0.5 m
COASTAL_SLR_PENALTY_1_0M = 12  # years if sea_level_rise > 1.0 m
# Flood/Agri: global warming (°C) -> years penalty
FLOOD_GW_PENALTY_1_5C = 4      # years if global_warming > 1.5 °C
FLOOD_GW_PENALTY_2_0C = 10     # years if global_warming > 2.0 °C
INTERVENTION_RESCUE_FRACTION = 0.2  # residual penalty after intervention (80% reduction)


def coastal_lifespan_penalty(sea_level_rise_m: float) -> int:
    """Climate penalty (years) for coastal assets from sea level rise."""
    if sea_level_rise_m > 1.0:
        return COASTAL_SLR_PENALTY_1_0M
    if sea_level_rise_m > 0.5:
        return COASTAL_SLR_PENALTY_0_5M
    return 0


def flood_lifespan_penalty(global_warming_c: float) -> int:
    """Climate penalty (years) for flood/agri assets from global warming."""
    if global_warming_c > 2.0:
        return FLOOD_GW_PENALTY_2_0C
    if global_warming_c > 1.5:
        return FLOOD_GW_PENALTY_1_5C
    return 0


def apply_lifespan_depreciation(
    initial_lifespan_years: int,
    raw_penalty: int,
    has_intervention_rescue: bool,
) -> tuple[int, float]:
    """Apply penalty and optional 80% intervention rescue. Returns (adjusted_lifespan, lifespan_penalty)."""
    lifespan_penalty = raw_penalty * INTERVENTION_RESCUE_FRACTION if has_intervention_rescue else raw_penalty
    adjusted_lifespan = max(1, initial_lifespan_years - lifespan_penalty)
    return adjusted_lifespan, round(lifespan_penalty, 2)


def coastal_has_intervention_rescue(intervention: str) -> bool:
    """True if intervention (e.g. Sea Wall) triggers 80% penalty reduction."""
    s = (intervention or "").strip().lower()
    return "sea wall" in s or "seawall" in s


def flood_has_intervention_rescue(intervention_type: str) -> bool:
    """True if intervention (e.g. Sponge City) triggers 80% penalty reduction."""
    s = (intervention_type or "").strip().lower()
    return "sponge" in s or s in ("sponge_city", "sponge city")
