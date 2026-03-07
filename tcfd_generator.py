"""
TCFD Report Generator - Green Bond Financial Terms Section

This module generates professional term sheet sections for Green Bond issuances
based on blended finance structures and climate resilience scores.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class BlendedFinanceResponse(BaseModel):
    """Response model for blended finance calculations"""
    total_capex: float
    resilience_score: int
    commercial_debt_pct: float
    concessional_grant_pct: float
    municipal_equity_pct: float
    commercial_rate_applied: float
    concessional_rate: float
    municipal_rate: float
    greenium_discount_bps: float
    blended_interest_rate: float
    annual_debt_service: float
    total_greenium_savings: float
    loan_term_years: int = 20


def generate_green_bond_term_sheet(
    blended_finance_data: BlendedFinanceResponse,
    location_name: str,
    module_name: str,
    currency: str = "USD"
) -> Dict[str, Any]:
    """
    Generate a professional Green Bond Term Sheet section for TCFD reports.
    
    Args:
        blended_finance_data: The blended finance calculation results
        location_name: Name of the location/issuer (e.g., "Mumbai Metropolitan Region")
        module_name: Climate resilience module (e.g., "Urban Flood Defense", "Coastal Protection")
        currency: Currency code (default: "USD")
    
    Returns:
        Dictionary containing formatted term sheet data ready for PDF generation
    """
    
    # Format currency amounts
    total_principal = f"${blended_finance_data.total_capex:,.2f}"
    if currency != "USD":
        total_principal = f"{blended_finance_data.total_capex:,.2f} {currency}"
    
    # Calculate percentage format for blended rate
    blended_coupon_pct = blended_finance_data.blended_interest_rate * 100
    
    # Determine climate performance covenant threshold
    covenant_threshold = 60
    covenant_status = "COMPLIANT" if blended_finance_data.resilience_score >= covenant_threshold else "AT RISK"
    
    # Calculate greenium impact
    greenium_bps = blended_finance_data.greenium_discount_bps
    lifetime_savings = f"${blended_finance_data.total_greenium_savings:,.2f}"
    if currency != "USD":
        lifetime_savings = f"{blended_finance_data.total_greenium_savings:,.2f} {currency}"
    
    # Build the term sheet structure
    term_sheet = {
        "title": "Green Bond Financial Terms",
        "subtitle": "Climate-Linked Resilience Financing",
        
        "core_terms": {
            "Issuer": location_name,
            "Total Principal": total_principal,
            "Blended Coupon": f"{blended_coupon_pct:.2f}%",
            "Tenor": f"{blended_finance_data.loan_term_years} years",
            "Use of Proceeds": f"Climate Resilience Infrastructure — {module_name}",
            "Climate Performance Covenant": f"Maintain Resilience Score ≥ {covenant_threshold}/100",
        },
        
        "capital_structure": {
            "title": "Blended Capital Structure",
            "tranches": [
                {
                    "name": "Commercial Debt",
                    "percentage": f"{blended_finance_data.commercial_debt_pct * 100:.1f}%",
                    "rate": f"{blended_finance_data.commercial_rate_applied * 100:.2f}%",
                    "amount": f"${blended_finance_data.total_capex * blended_finance_data.commercial_debt_pct:,.2f}"
                },
                {
                    "name": "Concessional Grant/Debt",
                    "percentage": f"{blended_finance_data.concessional_grant_pct * 100:.1f}%",
                    "rate": f"{blended_finance_data.concessional_rate * 100:.2f}%",
                    "amount": f"${blended_finance_data.total_capex * blended_finance_data.concessional_grant_pct:,.2f}"
                },
                {
                    "name": "Municipal Equity",
                    "percentage": f"{blended_finance_data.municipal_equity_pct * 100:.1f}%",
                    "rate": f"{blended_finance_data.municipal_rate * 100:.2f}%",
                    "amount": f"${blended_finance_data.total_capex * blended_finance_data.municipal_equity_pct:,.2f}"
                }
            ]
        },
        
        "greenium_analysis": {
            "title": "Climate Premium (Greenium) Impact",
            "discount_applied": f"{greenium_bps:.0f} basis points" if greenium_bps > 0 else "None",
            "lifetime_savings": lifetime_savings,
            "current_resilience_score": f"{blended_finance_data.resilience_score}/100",
            "covenant_status": covenant_status,
        },
        
        "financial_metrics": {
            "title": "Debt Service Metrics",
            "annual_debt_service": f"${blended_finance_data.annual_debt_service:,.2f}",
            "effective_rate": f"{blended_coupon_pct:.2f}%",
            "total_interest_cost": f"${(blended_finance_data.annual_debt_service * blended_finance_data.loan_term_years) - blended_finance_data.total_capex:,.2f}",
        }
    }
    
    # Add currency info if not USD
    if currency != "USD":
        term_sheet["currency"] = currency
    
    return term_sheet


def format_term_sheet_as_text(term_sheet: Dict[str, Any]) -> str:
    """
    Convert term sheet dictionary to formatted text representation.
    
    Useful for plain text reports or as input to PDF generators.
    
    Args:
        term_sheet: Output from generate_green_bond_term_sheet()
    
    Returns:
        Formatted multi-line string
    """
    
    lines = []
    lines.append("=" * 80)
    lines.append(term_sheet["title"].center(80))
    lines.append(term_sheet["subtitle"].center(80))
    lines.append("=" * 80)
    lines.append("")
    
    # Core Terms
    lines.append("CORE TERMS")
    lines.append("-" * 80)
    for key, value in term_sheet["core_terms"].items():
        lines.append(f"{key:.<40} {value}")
    lines.append("")
    
    # Capital Structure
    lines.append(term_sheet["capital_structure"]["title"].upper())
    lines.append("-" * 80)
    for tranche in term_sheet["capital_structure"]["tranches"]:
        lines.append(f"{tranche['name']:.<30} {tranche['percentage']:>8} @ {tranche['rate']:>7} = {tranche['amount']:>20}")
    lines.append("")
    
    # Greenium Analysis
    lines.append(term_sheet["greenium_analysis"]["title"].upper())
    lines.append("-" * 80)
    lines.append(f"{'Discount Applied':.<40} {term_sheet['greenium_analysis']['discount_applied']}")
    lines.append(f"{'Lifetime Savings':.<40} {term_sheet['greenium_analysis']['lifetime_savings']}")
    lines.append(f"{'Current Resilience Score':.<40} {term_sheet['greenium_analysis']['current_resilience_score']}")
    lines.append(f"{'Covenant Status':.<40} {term_sheet['greenium_analysis']['covenant_status']}")
    lines.append("")
    
    # Financial Metrics
    lines.append(term_sheet["financial_metrics"]["title"].upper())
    lines.append("-" * 80)
    lines.append(f"{'Annual Debt Service':.<40} {term_sheet['financial_metrics']['annual_debt_service']}")
    lines.append(f"{'Effective Blended Rate':.<40} {term_sheet['financial_metrics']['effective_rate']}")
    lines.append(f"{'Total Interest Cost (Lifetime)':.<40} {term_sheet['financial_metrics']['total_interest_cost']}")
    lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


def generate_green_bond_html_table(term_sheet: Dict[str, Any]) -> str:
    """
    Generate an HTML table representation of the Green Bond Term Sheet.
    
    Useful for web-based reports or HTML-to-PDF conversion.
    
    Args:
        term_sheet: Output from generate_green_bond_term_sheet()
    
    Returns:
        HTML string with styled table
    """
    
    html = f"""
    <div class="green-bond-term-sheet" style="font-family: Arial, sans-serif; max-width: 800px; margin: 20px auto;">
        <h2 style="text-align: center; color: #2c5f2d; border-bottom: 3px solid #2c5f2d; padding-bottom: 10px;">
            {term_sheet['title']}
        </h2>
        <p style="text-align: center; color: #666; font-style: italic; margin-bottom: 30px;">
            {term_sheet['subtitle']}
        </p>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <thead>
                <tr style="background-color: #2c5f2d; color: white;">
                    <th colspan="2" style="padding: 12px; text-align: left; font-size: 14px;">CORE TERMS</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add core terms rows
    for i, (key, value) in enumerate(term_sheet["core_terms"].items()):
        bg_color = "#f9f9f9" if i % 2 == 0 else "white"
        html += f"""
                <tr style="background-color: {bg_color};">
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: 600;">{key}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{value}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <thead>
                <tr style="background-color: #2c5f2d; color: white;">
                    <th style="padding: 12px; text-align: left;">Tranche</th>
                    <th style="padding: 12px; text-align: right;">Allocation</th>
                    <th style="padding: 12px; text-align: right;">Rate</th>
                    <th style="padding: 12px; text-align: right;">Amount</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add capital structure rows
    for i, tranche in enumerate(term_sheet["capital_structure"]["tranches"]):
        bg_color = "#f9f9f9" if i % 2 == 0 else "white"
        html += f"""
                <tr style="background-color: {bg_color};">
                    <td style="padding: 10px; border-bottom: 1px solid #ddd;">{tranche['name']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{tranche['percentage']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">{tranche['rate']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; font-weight: 600;">{tranche['amount']}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <thead>
                <tr style="background-color: #2c5f2d; color: white;">
                    <th colspan="2" style="padding: 12px; text-align: left; font-size: 14px;">GREENIUM IMPACT ANALYSIS</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add greenium analysis rows
    greenium = term_sheet["greenium_analysis"]
    rows = [
        ("Discount Applied", greenium["discount_applied"]),
        ("Lifetime Savings", greenium["lifetime_savings"]),
        ("Current Resilience Score", greenium["current_resilience_score"]),
        ("Covenant Status", greenium["covenant_status"])
    ]
    
    for i, (key, value) in enumerate(rows):
        bg_color = "#f9f9f9" if i % 2 == 0 else "white"
        # Highlight covenant status
        value_style = ""
        if key == "Covenant Status":
            if value == "COMPLIANT":
                value_style = "color: green; font-weight: bold;"
            else:
                value_style = "color: orange; font-weight: bold;"
        
        html += f"""
                <tr style="background-color: {bg_color};">
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: 600;">{key}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; {value_style}">{value}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
        
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #2c5f2d; color: white;">
                    <th colspan="2" style="padding: 12px; text-align: left; font-size: 14px;">DEBT SERVICE METRICS</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add financial metrics rows
    metrics = term_sheet["financial_metrics"]
    metric_rows = [
        ("Annual Debt Service", metrics["annual_debt_service"]),
        ("Effective Blended Rate", metrics["effective_rate"]),
        ("Total Interest Cost (Lifetime)", metrics["total_interest_cost"])
    ]
    
    for i, (key, value) in enumerate(metric_rows):
        bg_color = "#f9f9f9" if i % 2 == 0 else "white"
        html += f"""
                <tr style="background-color: {bg_color};">
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; font-weight: 600;">{key}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; font-weight: 600;">{value}</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html
