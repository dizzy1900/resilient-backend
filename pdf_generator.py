"""Server-side PDF generation for TCFD and investor reports.

Uses Jinja2 to render HTML templates and WeasyPrint to convert them into
PDF byte streams.  Primary entry points:
- ``generate_tcfd_pdf`` — TCFD Green Bond Term Sheet
- ``generate_investor_report_pdf`` — Climate Resilience Investor Report
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

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


# ---------------------------------------------------------------------------
# Investor Report
# ---------------------------------------------------------------------------

_DRIVER_LABEL_RE = re.compile(r"\s*\(.*?\)\s*$")


def _clean_driver_label(raw: str) -> str:
    """Strip shock-magnitude suffixes from sensitivity driver labels.

    ``"Water Stress (-20%)"`` → ``"Water Stress"``
    ``"Market Price (-15%)"`` → ``"Market Price"``
    """
    return _DRIVER_LABEL_RE.sub("", raw).strip()


def build_investor_report_data(
    simulation_result: Dict[str, Any],
    score_data: Dict[str, Any],
    forecast_data: Dict[str, Any],
    location_name: str,
    project_type: str,
) -> Dict[str, Any]:
    """Assemble the flat template-variable dict for ``investor_report.html``.

    Parameters
    ----------
    simulation_result:
        Full simulation result dict (headless runner / ``/simulate`` endpoint).
        Expected nested keys: ``financial_analysis``, ``monte_carlo_analysis``,
        ``adaptation_analysis``, ``sensitivity_analysis``, ``executive_summary``.
    score_data:
        Dict returned by ``resilient_score.calculate_resilient_score()``.
        Expected keys: ``resilient_score``, ``score_label``, ``avoided_loss_usd``,
        ``avoided_loss_roi_pct``, ``avoided_loss_5yr`` … ``20yr``,
        ``confidence_level``, ``intervention_name``.
    forecast_data:
        Dict returned by the ``/api/v1/forecast/temporal`` endpoint.
        Expected keys: ``forecast`` (list), ``stranded_asset_year``.
    location_name:
        Human-readable location string (e.g. ``"Kumasi Region, Ghana"``).
    project_type:
        Project type label (e.g. ``"Agriculture — Cocoa"``).

    Returns
    -------
    Dict[str, Any]
        Flat dict whose keys map 1-to-1 onto the Jinja2 variables expected by
        ``investor_report.html``.
    """
    financial = simulation_result.get("financial_analysis", {})
    monte_carlo = simulation_result.get("monte_carlo_analysis", {})
    adaptation = simulation_result.get("adaptation_analysis", {})
    sensitivity = simulation_result.get("sensitivity_analysis", {})

    # --- sensitivity ranking: normalise driver labels ---
    raw_ranking: List[Dict[str, Any]] = sensitivity.get("sensitivity_ranking", [])
    sensitivity_ranking = [
        {
            "driver": _clean_driver_label(item.get("driver", "Unknown")),
            "impact_pct": float(item.get("impact_pct", 0.0)),
        }
        for item in raw_ranking
    ]

    # primary driver: prefer the pre-computed field, fall back to first ranking entry
    raw_primary = sensitivity.get(
        "primary_driver",
        raw_ranking[0].get("driver", "Unknown") if raw_ranking else "Unknown",
    )
    primary_risk_driver = _clean_driver_label(raw_primary)

    # --- forecast rows ---
    forecast: List[Dict[str, Any]] = forecast_data.get("forecast", [])

    # --- stranded asset year ---
    stranded_asset_year: Optional[int] = forecast_data.get("stranded_asset_year")

    return {
        # identity
        "location_name": location_name,
        "project_type": project_type,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        # score (from score_data)
        "resilient_score": int(score_data.get("resilient_score", 0)),
        "score_label": score_data.get("score_label", "REVIEW"),
        "confidence_level": score_data.get("confidence_level", "Low"),
        # avoided loss (from score_data)
        "avoided_loss_usd": float(score_data.get("avoided_loss_usd", 0.0)),
        "avoided_loss_roi_pct": float(score_data.get("avoided_loss_roi_pct", 0.0)),
        "avoided_loss_5yr": float(score_data.get("avoided_loss_5yr", 0.0)),
        "avoided_loss_10yr": float(score_data.get("avoided_loss_10yr", 0.0)),
        "avoided_loss_15yr": float(score_data.get("avoided_loss_15yr", 0.0)),
        "avoided_loss_20yr": float(score_data.get("avoided_loss_20yr", 0.0)),
        # financial (from simulation_result)
        "npv_usd": float(financial.get("npv_usd", 0.0)),
        "default_probability": float(monte_carlo.get("default_probability", 0.0)),
        "intervention_cost": float(adaptation.get("intervention_cost", 0.0)),
        "intervention_name": score_data.get(
            "intervention_name",
            adaptation.get("intervention_name", "Climate Adaptation"),
        ),
        # narrative
        "executive_summary": simulation_result.get("executive_summary", ""),
        # risk
        "primary_risk_driver": primary_risk_driver,
        "sensitivity_ranking": sensitivity_ranking,
        # forecast
        "forecast": forecast,
        "stranded_asset_year": stranded_asset_year,
    }


def generate_investor_report_pdf(report_data: Dict[str, Any]) -> bytes:
    """Render the Climate Resilience Investor Report as a PDF.

    Parameters
    ----------
    report_data:
        Flat dict of template variables, typically produced by
        ``build_investor_report_data()``.  All keys listed in
        ``templates/investor_report.html`` must be present.

    Returns
    -------
    bytes
        The rendered PDF document as a byte string.
    """
    template = _jinja_env.get_template("investor_report.html")

    html_string = template.render(**report_data)

    pdf_bytes: bytes = HTML(string=html_string).write_pdf()
    return pdf_bytes
