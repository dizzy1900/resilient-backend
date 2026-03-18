"""Shared utilities used by multiple routers."""

from __future__ import annotations

from fastapi.responses import JSONResponse


def legacy_error(status_code: int, message: str, code: str) -> JSONResponse:
    """Return a JSON error response matching the legacy Flask format."""
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message, "code": code},
    )


# Material Degradation Curves: interventions that reduce OPEX climate penalty by 85%
_OPEX_INTERVENTION_NAMES = frozenset(
    s.lower().replace(" ", "_").replace("-", "_")
    for s in ("Sea Wall", "Drainage Upgrade", "Sponge City")
)


def has_opex_intervention(intervention: str) -> bool:
    """True if intervention protects asset and reduces OPEX climate penalty (85% reduction)."""
    if not intervention or not isinstance(intervention, str):
        return False
    normalized = intervention.strip().lower().replace(" ", "_").replace("-", "_")
    return normalized in _OPEX_INTERVENTION_NAMES or normalized == "sponge_city"
