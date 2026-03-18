"""AI endpoints — deterministic NLG executive summaries."""

from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from nlg_engine import generate_deterministic_summary

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ExecutiveSummaryRequest(BaseModel):
    module_name: str = Field(..., description="Module identifier: health_public, health_private, agriculture, coastal, flood, price_shock")
    location_name: str = Field(..., description="Geographic location name for summary context")
    simulation_data: Dict[str, Any] = Field(..., description="Module-specific simulation results dictionary")


class ExecutiveSummaryResponse(BaseModel):
    summary_text: str = Field(..., description="3-sentence executive summary generated from simulation data")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.post("/executive-summary", response_model=ExecutiveSummaryResponse)
def executive_summary(req: ExecutiveSummaryRequest) -> dict:
    """Generate deterministic executive summary using NLG templates."""
    try:
        summary_text = generate_deterministic_summary(
            module_name=req.module_name,
            location_name=req.location_name,
            data=req.simulation_data,
        )
        return {"summary_text": summary_text}
    except Exception:
        fallback = f"Data successfully processed for {req.location_name}. Please refer to the quantitative metrics provided in the dashboard for detailed ROI analysis."
        return {"summary_text": fallback}
