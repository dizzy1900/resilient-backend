"""Opportunities endpoint — climate-event-driven leverageable ideas."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/opportunities", tags=["Opportunities"])


class Opportunity(BaseModel):
    id: str
    title: str
    description: str
    action_type: str
    urgency: str


_OPPORTUNITIES: List[Opportunity] = [
    Opportunity(
        id="opp-001",
        title="Hedge West Africa Cocoa",
        description=(
            "ReliefWeb reports severe drought in Ghana. "
            "Recommend increasing drought-resistant seedling subsidy by 15%."
        ),
        action_type="Intervention",
        urgency="High",
    ),
    Opportunity(
        id="opp-002",
        title="Redirect Coastal Infrastructure Budget — Bangladesh Delta",
        description=(
            "Cyclone season onset detected via Sentinel-2 imagery. "
            "Recommend reallocating 20% of coastal capex to flood barrier reinforcement."
        ),
        action_type="Reallocation",
        urgency="High",
    ),
    Opportunity(
        id="opp-003",
        title="Activate Parametric Insurance Trigger — Sahel Crop Failure",
        description=(
            "NDVI anomaly index fell below 0.3 across three Sahel grid cells. "
            "Recommend triggering parametric insurance payout to protect smallholder positions."
        ),
        action_type="Risk Transfer",
        urgency="High",
    ),
]


@router.get("/generate", response_model=List[Opportunity])
def generate_opportunities() -> List[Opportunity]:
    """Return a list of climate-event-driven leverageable ideas."""
    return _OPPORTUNITIES
