"""Export endpoints — PDF generation for TCFD and investor reports."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from tcfd_generator import BlendedFinanceResponse, generate_green_bond_term_sheet
from pdf_generator import (
    generate_tcfd_pdf,
    generate_investor_report_pdf,
    build_investor_report_data,
)

router = APIRouter(prefix="/api/v1/export", tags=["Export"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class PDFExportRequest(BaseModel):
    """Request body for TCFD PDF export."""

    blended_finance_data: BlendedFinanceResponse = Field(
        ..., description="Blended finance calculation results"
    )
    location_name: str = Field(
        ..., description="Issuer / location name (e.g. 'Mumbai Metropolitan Region')"
    )
    module_name: str = Field(
        ..., description="Climate resilience module (e.g. 'Urban Flood Defense')"
    )
    currency: str = Field("USD", description="Currency code")
    filename: Optional[str] = Field(
        None, description="Optional PDF filename for the download"
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/pdf")
def export_tcfd_pdf(req: PDFExportRequest) -> StreamingResponse:
    """Generate and return a TCFD Green Bond Term Sheet as a PDF."""

    try:
        term_sheet = generate_green_bond_term_sheet(
            blended_finance_data=req.blended_finance_data,
            location_name=req.location_name,
            module_name=req.module_name,
            currency=req.currency,
        )

        pdf_bytes = generate_tcfd_pdf(term_sheet)

        filename = req.filename or "tcfd_green_bond_term_sheet.pdf"

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")


class InvestorReportRequest(BaseModel):
    """Request body for the Climate Resilience Investor Report PDF."""

    simulation_result: Dict[str, Any] = Field(
        ..., description="Full result dict from /api/v1/simulate or /api/v1/forecast"
    )
    score_data: Dict[str, Any] = Field(
        ..., description="Resilient score dict from resilient_score.calculate_resilient_score()"
    )
    forecast_data: Dict[str, Any] = Field(
        ..., description="Temporal forecast dict from /api/v1/forecast/temporal"
    )
    location_name: str = Field(..., description="Human-readable location (e.g. 'Kumasi Region, Ghana')")
    project_type: str = Field("Agriculture", description="Project type label (e.g. 'Agriculture — Cocoa')")
    filename: Optional[str] = Field(None, description="Optional PDF filename for the download")


@router.post("/investor-report")
def export_investor_report(req: InvestorReportRequest) -> StreamingResponse:
    """Generate and return a Climate Resilience Investor Report as a PDF."""

    try:
        report_data = build_investor_report_data(
            simulation_result=req.simulation_result,
            score_data=req.score_data,
            forecast_data=req.forecast_data,
            location_name=req.location_name,
            project_type=req.project_type,
        )

        pdf_bytes = generate_investor_report_pdf(report_data)

        filename = req.filename or "resilient_investor_report.pdf"

        return StreamingResponse(
            BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")
