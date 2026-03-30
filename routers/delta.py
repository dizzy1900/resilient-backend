"""Delta endpoints — portfolio risk sweep delta via delta_engine."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from delta_engine import calculate_sweep_delta

router = APIRouter(prefix="/api/v1/delta", tags=["Delta"])


class SweepDeltaResponse(BaseModel):
    risk_delta: str
    direction: str
    severity: str
    new_stranded_assets: int
    message: str


_MOCK_PREVIOUS = {
    "risk_score": 45.2,
    "stranded_assets": ["asset_1"],
}

_MOCK_CURRENT = {
    "risk_score": 50.4,
    "stranded_assets": ["asset_1", "asset_2", "asset_3"],
}


@router.get("/sweep", response_model=SweepDeltaResponse)
def get_sweep_delta() -> SweepDeltaResponse:
    """Return a sweep delta summary comparing two mock portfolio risk states."""
    result = calculate_sweep_delta(_MOCK_PREVIOUS, _MOCK_CURRENT)
    return SweepDeltaResponse(**result)
