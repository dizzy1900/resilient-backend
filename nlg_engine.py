#!/usr/bin/env python3
"""
Deterministic Natural Language Generator (NLG) for Executive Summaries
=======================================================================

This module generates executive summaries using deterministic Python f-strings
to avoid LLM token costs and hallucination risks. All text is template-based
with dynamic value insertion.

Supported Modules:
- health_public: Public health DALY analysis (population-level)
- health_private: Private sector workplace cooling CBA
- agriculture: Crop yield and revenue analysis
- coastal: Coastal flood risk and infrastructure
- flood: Urban/flash flood risk
- price_shock: Commodity price shock from climate stress

Design Philosophy:
- Zero LLM calls (deterministic, no hallucination)
- Template-based with f-strings
- Graceful degradation for missing data
- 3-sentence format for conciseness
"""

from typing import Dict, Any, Optional


def generate_deterministic_summary(
    module_name: str,
    location_name: str,
    data: Dict[str, Any]
) -> str:
    """
    Generate a 3-sentence executive summary using deterministic NLG templates.
    
    Args:
        module_name: Module identifier (health_public, health_private, etc.)
        location_name: Geographic location name
        data: Simulation data dictionary with module-specific metrics
    
    Returns:
        3-sentence executive summary string
    
    Examples:
        >>> data = {
        ...     'dalys_averted': 4107.0,
        ...     'economic_value_preserved_usd': 98568000.0,
        ...     'intervention_type': 'urban_cooling_center'
        ... }
        >>> generate_deterministic_summary('health_public', 'Bangkok', data)
    """
    module_lower = module_name.lower()
    
    # Route to appropriate module-specific generator
    if module_lower == "health_public":
        return _generate_health_public_summary(location_name, data)
    
    elif module_lower == "health_private":
        return _generate_health_private_summary(location_name, data)
    
    elif module_lower == "agriculture":
        return _generate_agriculture_summary(location_name, data)
    
    elif module_lower == "coastal":
        return _generate_coastal_summary(location_name, data)
    
    elif module_lower == "flood":
        return _generate_flood_summary(location_name, data)
    
    elif module_lower == "price_shock":
        return _generate_price_shock_summary(location_name, data)
    
    else:
        # Fallback for unknown modules
        return _generate_fallback_summary(location_name)


def _generate_health_public_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for public health DALY analysis.
    
    Expected data structure (from /predict-health response):
    {
        "public_health_analysis": {
            "dalys_averted": float,
            "economic_value_preserved_usd": float,
            "intervention_type": str
        }
    }
    """
    try:
        # 1. Extract and forcefully clean the nested data
        public_health_data = data.get('public_health_analysis', {})
        
        try:
            dalys_averted = float(public_health_data.get('dalys_averted', 0))
        except (ValueError, TypeError):
            dalys_averted = 0.0
        
        # Grab the intervention, whatever it is
        raw_intervention = str(public_health_data.get('intervention_type', '')).strip().lower()
        
        # 2. Format the intervention string (Catch both snake_case and UI Display Names)
        if 'cooling' in raw_intervention:
            intervention_text = "Urban Cooling Centers"
        elif 'mosquito' in raw_intervention or 'eradication' in raw_intervention:
            intervention_text = "Mosquito Eradication"
        else:
            intervention_text = "the selected public health intervention"
        
        # 3. Format the economic value
        try:
            economic_value = float(public_health_data.get('economic_value_preserved_usd', 0))
        except (ValueError, TypeError):
            economic_value = 0.0
        
        if economic_value >= 1_000_000:
            econ_str = f"${economic_value / 1_000_000:.1f} million"
        else:
            econ_str = f"${economic_value:,.0f}"
        
        # 4. Build the sentences
        sentence_1 = f"{location_name} faces economic disruption from projected climate hazards."
        
        # Debug log to catch hidden formatting issues
        print(f"[NLG DEBUG] DALYs: {dalys_averted} (type: {type(dalys_averted)}), Intervention: '{raw_intervention}'")
        
        # REMOVED THE STRICT STRING CHECK. If math > 0, print the sentence!
        if dalys_averted > 0.0:
            sentence_2 = f"Implementing {intervention_text} will avert {dalys_averted:.1f} Disability-Adjusted Life Years (DALYs)."
        else:
            sentence_2 = "Climate health risks require assessment and intervention planning."
        
        sentence_3 = f"This preserves {econ_str} in macroeconomic value, making it a highly favorable public sector investment."
        
        summary_text = f"{sentence_1} {sentence_2} {sentence_3}"
        
        return summary_text
    
    except Exception as e:
        # Graceful degradation on parsing errors
        print(f"[NLG ERROR] Exception in health_public summary: {e}")
        return _generate_fallback_summary(location_name)


def _generate_health_private_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for private sector workplace cooling CBA.
    
    Expected data keys:
    - npv_10yr_at_10pct_discount: float
    - payback_period_years: float
    - intervention_capex: float
    - intervention_type: str
    - avoided_annual_economic_loss_usd: float (optional)
    """
    try:
        npv = data.get('npv_10yr_at_10pct_discount', None)
        payback = data.get('payback_period_years', None)
        capex = data.get('intervention_capex', 0.0)
        intervention_type = data.get('intervention_type', 'cooling system')
        avoided_loss = data.get('avoided_annual_economic_loss_usd', 0.0)
        
        # Sentence 1: Context
        sentence1 = f"{location_name} workplace operations face significant productivity losses from climate-induced heat stress."
        
        # Sentence 2: Intervention description
        intervention_names = {
            'hvac_retrofit': 'HVAC cooling system retrofit',
            'passive_cooling': 'passive cooling infrastructure',
            'urban_cooling_center': 'cooling facilities',
        }
        intervention_display = intervention_names.get(intervention_type.lower(), intervention_type)
        
        if capex > 0:
            capex_display = f"${capex/1e6:.1f}M" if capex >= 1e6 else f"${capex:,.0f}"
            sentence2 = f"Installing {intervention_display} (CAPEX: {capex_display}) can reduce worker heat exposure."
        else:
            sentence2 = f"Implementing {intervention_display} can reduce worker heat exposure and improve productivity."
        
        # Sentence 3: ROI recommendation
        if npv is not None and npv > 0:
            npv_display = f"${npv/1e6:.1f}M" if npv >= 1e6 else f"${npv:,.0f}"
            if payback is not None and payback < 3.0:
                sentence3 = f"With a 10-year NPV of {npv_display} and {payback:.1f}-year payback period, this represents an excellent investment opportunity."
            else:
                sentence3 = f"With a 10-year NPV of {npv_display}, this investment is financially attractive despite a longer payback period."
        elif npv is not None and npv <= 0:
            sentence3 = f"Based on negative NPV analysis, this intervention is not recommended as operating costs exceed productivity gains."
        else:
            # No financial analysis available
            if avoided_loss > 0:
                loss_display = f"${avoided_loss/1e6:.1f}M" if avoided_loss >= 1e6 else f"${avoided_loss:,.0f}"
                sentence3 = f"The intervention would avoid {loss_display} in annual economic losses."
            else:
                sentence3 = "Please refer to the quantitative metrics provided in the dashboard for detailed ROI analysis."
        
        return f"{sentence1} {sentence2} {sentence3}"
    
    except Exception as e:
        return _generate_fallback_summary(location_name)


def _generate_agriculture_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for agriculture risk analysis.
    
    Expected data keys:
    - transition_capex: float
    - avoided_revenue_loss: float
    - risk_reduction_pct: float
    """
    try:
        # 1. Forcefully clean the data
        try:
            capex = float(data.get('transition_capex', 0))
            avoided_loss = float(data.get('avoided_revenue_loss', 0))
            risk_reduction = float(data.get('risk_reduction_pct', 0))
        except (ValueError, TypeError):
            capex, avoided_loss, risk_reduction = 0.0, 0.0, 0.0
        
        # 2. Format currency strings
        if avoided_loss >= 1_000_000:
            loss_str = f"${avoided_loss / 1_000_000:.1f} million"
        else:
            loss_str = f"${avoided_loss:,.0f}"
        
        if capex >= 1_000_000:
            capex_str = f"${capex / 1_000_000:.1f} million"
        else:
            capex_str = f"${capex:,.0f}"
        
        # 3. Build the sentences
        sentence_1 = f"{location_name} faces agricultural yield disruption and commodity price volatility from projected climate hazards."
        
        if avoided_loss > 0.0 or risk_reduction > 0.0:
            sentence_2 = f"Implementing the proposed crop adaptation requires a capital expenditure of {capex_str} and reduces climate risk by {risk_reduction:.1f}%."
            sentence_3 = f"This adaptation secures {loss_str} in avoided revenue loss, protecting local supply chains and financial stability."
        else:
            sentence_2 = "Without targeted crop adaptation or irrigation investments, agricultural yields remain highly vulnerable to severe climate shocks."
            sentence_3 = "Please utilize the dashboard to model specific seed transitions or infrastructure upgrades to mitigate these projected losses."
        
        summary_text = f"{sentence_1} {sentence_2} {sentence_3}"
        
        return summary_text
    
    except Exception as e:
        return _generate_fallback_summary(location_name)


def _generate_coastal_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for coastal flood risk analysis.
    
    Expected data keys:
    - intervention_capex or capex: float
    - avoided_damage_usd or avoided_loss: float
    """
    try:
        # 1. Forcefully extract the nested data
        coastal_data = data.get('data', data) if isinstance(data.get('data'), dict) else data
        analysis_data = coastal_data.get('analysis', {})
        
        # 2. Safely extract Avoided Loss ONLY
        try:
            loss_val = analysis_data.get('avoided_loss', 
                                        analysis_data.get('avoided_damage_usd',
                                        coastal_data.get('avoided_loss', 
                                        coastal_data.get('avoided_damage_usd', 0))))
            avoided_damage = float(0 if loss_val is None else loss_val)
        except (ValueError, TypeError):
            avoided_damage = 0.0
        
        # 3. Safely extract Capex ONLY
        try:
            capex_val = analysis_data.get('intervention_capex',
                                         analysis_data.get('capex',
                                         coastal_data.get('intervention_capex', 
                                         coastal_data.get('capex', 0))))
            capex = float(0 if capex_val is None else capex_val)
        except (ValueError, TypeError):
            capex = 0.0
        
        # 4. Format currency strings
        damage_str = f"${avoided_damage / 1_000_000:.1f} million" if avoided_damage >= 1_000_000 else f"${avoided_damage:,.0f}"
        capex_str = f"${capex / 1_000_000:.1f} million" if capex >= 1_000_000 else f"${capex:,.0f}"
        
        # 5. Build the sentences dynamically based on available data
        sentence_1 = f"{location_name} faces critical asset exposure from projected sea-level rise and coastal inundation hazards."
        
        if avoided_damage > 0.0:
            if capex > 0:
                sentence_2 = f"Implementing the proposed coastal defense infrastructure requires a capital expenditure of {capex_str}."
                sentence_3 = f"This adaptation secures {damage_str} in avoided structural damage, effectively safeguarding long-term asset value."
            else:
                # Fallback if Capex is missing but Avoided Loss exists
                sentence_2 = f"Implementing the proposed coastal defense infrastructure secures {damage_str} in avoided structural damage."
                sentence_3 = "This adaptation effectively safeguards long-term asset value and reduces operational downtime."
        else:
            sentence_2 = "Without targeted seawall or coastal defense investments, waterfront assets remain highly vulnerable to storm surges."
            sentence_3 = "Please utilize the dashboard to model specific physical interventions to mitigate these projected physical risks."
        
        summary_text = f"{sentence_1} {sentence_2} {sentence_3}"
        
        return summary_text
    
    except Exception as e:
        return _generate_fallback_summary(location_name)


def _generate_flood_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for urban/flash flood risk analysis.
    
    Expected data keys:
    - intervention_capex or capex: float
    - analysis.avoided_loss or avoided_loss: float (nested in analysis dict)
    """
    try:
        # 1. Forcefully extract the nested data
        flood_data = data.get('data', data) if isinstance(data.get('data'), dict) else data
        
        # Dig into the analysis dictionary where the metrics live
        analysis_data = flood_data.get('analysis', {})
        
        try:
            capex = float(flood_data.get('intervention_capex', flood_data.get('capex', 0)))
            # Check both analysis dict and root for avoided_loss
            avoided_loss = float(analysis_data.get('avoided_loss', flood_data.get('avoided_loss', 0)))
        except (ValueError, TypeError):
            capex, avoided_loss = 0.0, 0.0
        
        # 2. Format currency strings
        if avoided_loss >= 1_000_000:
            loss_str = f"${avoided_loss / 1_000_000:.1f} million"
        else:
            loss_str = f"${avoided_loss:,.0f}"
        
        if capex >= 1_000_000:
            capex_str = f"${capex / 1_000_000:.1f} million"
        else:
            capex_str = f"${capex:,.0f}"
        
        # 3. Build the sentences
        sentence_1 = f"{location_name} is highly vulnerable to extreme precipitation events and subsequent localized flooding."
        
        if avoided_loss > 0.0:
            sentence_2 = f"Deploying the specified flood mitigation assets requires an upfront investment of {capex_str}."
            sentence_3 = f"This resilience measure preserves {loss_str} in avoided economic disruption and physical property damage."
        else:
            sentence_2 = "Without robust stormwater management or floodgate installations, local operations face severe operational downtime risks."
            sentence_3 = "Please utilize the dashboard to calculate the ROI of specific flood mitigation scenarios."
        
        summary_text = f"{sentence_1} {sentence_2} {sentence_3}"
        
        return summary_text
    
    except Exception as e:
        return _generate_fallback_summary(location_name)


def _generate_price_shock_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for commodity price shock analysis.
    
    Expected data keys:
    - crop_type: str
    - yield_loss_pct: float
    - price_increase_pct: float
    - revenue_impact_usd: float
    """
    try:
        crop = data.get('crop_type', 'commodity')
        yield_loss = data.get('yield_loss_pct', 0.0)
        price_increase = data.get('price_increase_pct', 0.0)
        revenue_impact = data.get('revenue_impact_usd', 0.0)
        
        # Sentence 1: Yield shock context
        sentence1 = f"{location_name} {crop} production faces a {yield_loss:.0f}% yield loss from climate-induced stress."
        
        # Sentence 2: Price dynamics
        sentence2 = f"This supply disruption triggers a {price_increase:.1f}% commodity price increase through supply-demand elasticity."
        
        # Sentence 3: Revenue impact
        if revenue_impact >= 0:
            # Positive revenue impact (producer benefits from higher prices)
            if revenue_impact >= 1e6:
                revenue_display = f"${revenue_impact/1e6:.1f}M"
            else:
                revenue_display = f"${revenue_impact:,.0f}"
            sentence3 = f"Net revenue impact is positive at {revenue_display}, as price gains offset yield losses for producers."
        else:
            # Negative revenue impact
            loss = abs(revenue_impact)
            if loss >= 1e6:
                loss_display = f"${loss/1e6:.1f}M"
            else:
                loss_display = f"${loss:,.0f}"
            sentence3 = f"Producers face a net revenue loss of {loss_display} as yield declines exceed price compensation."
        
        return f"{sentence1} {sentence2} {sentence3}"
    
    except Exception as e:
        return _generate_fallback_summary(location_name)


def _generate_fallback_summary(location_name: str) -> str:
    """
    Generate fallback summary when module is unknown or data parsing fails.
    
    Args:
        location_name: Geographic location name
    
    Returns:
        Generic 1-sentence fallback message
    """
    return f"Data successfully processed for {location_name}. Please refer to the quantitative metrics provided in the dashboard for detailed ROI analysis."


# ============================================================================
# UTILITY FUNCTIONS FOR VALUE FORMATTING
# ============================================================================

def format_currency(value: float, threshold_m: float = 1e6, threshold_b: float = 1e9) -> str:
    """
    Format currency with M/B suffixes for readability.
    
    Args:
        value: Numeric value in USD
        threshold_m: Threshold for million suffix (default: 1M)
        threshold_b: Threshold for billion suffix (default: 1B)
    
    Returns:
        Formatted string with $ symbol and appropriate suffix
    
    Examples:
        >>> format_currency(1500000)
        '$1.5M'
        >>> format_currency(2500000000)
        '$2.5B'
        >>> format_currency(50000)
        '$50,000'
    """
    if value >= threshold_b:
        return f"${value/1e9:.1f}B"
    elif value >= threshold_m:
        return f"${value/1e6:.1f}M"
    else:
        return f"${value:,.0f}"


def format_percentage(value: float, decimals: int = 0) -> str:
    """
    Format percentage for readability.
    
    Args:
        value: Numeric value (0-100 scale or 0-1 scale, auto-detected)
        decimals: Number of decimal places (default: 0)
    
    Returns:
        Formatted percentage string with % symbol
    
    Examples:
        >>> format_percentage(25.5)
        '26%'
        >>> format_percentage(0.255, decimals=1)
        '25.5%'
    """
    # Auto-detect 0-1 scale vs 0-100 scale
    if value < 1.5:
        value = value * 100
    
    if decimals == 0:
        return f"{value:.0f}%"
    else:
        return f"{value:.{decimals}f}%"
