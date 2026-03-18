"""Export endpoints — PDF generation for TCFD reports."""

from __future__ import annotations

from io import BytesIO
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from tcfd_generator import BlendedFinanceResponse, generate_green_bond_term_sheet
from pdf_generator import generate_tcfd_pdf

router = APIRouter(tags=["Export"])


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


@router.post("/api/v1/export/pdf")
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
