"""Server-side PDF generation for TCFD reports.

Uses Jinja2 to render an HTML template and WeasyPrint to convert it into a
PDF byte stream.  The primary entry point is ``generate_tcfd_pdf``.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# Template directory lives alongside this module.
_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=True,
)


def generate_tcfd_pdf(report_data: Dict[str, Any]) -> bytes:
    """Render a TCFD Green Bond Term Sheet as a PDF.

    Parameters
    ----------
    report_data:
        Dictionary returned by
        ``tcfd_generator.generate_green_bond_term_sheet()``.  Expected
        top-level keys: ``title``, ``subtitle``, ``core_terms``,
        ``capital_structure``, ``greenium_analysis``, ``financial_metrics``.

    Returns
    -------
    bytes
        The rendered PDF document as a byte string.
    """

    template = _jinja_env.get_template("tcfd_report.html")

    html_string = template.render(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        **report_data,
    )

    pdf_bytes: bytes = HTML(string=html_string).write_pdf()
    return pdf_bytes
