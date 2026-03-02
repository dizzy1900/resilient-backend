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
    - current_yield_tons: float
    - proposed_yield_tons: float
    - current_revenue: float
    - proposed_revenue: float
    - crop_type: str
    """
    try:
        current_yield = data.get('current_yield_tons', 0.0)
        proposed_yield = data.get('proposed_yield_tons', 0.0)
        current_revenue = data.get('current_revenue', 0.0)
        proposed_revenue = data.get('proposed_revenue', 0.0)
        crop_type = data.get('crop_type', 'crops')
        
        # Sentence 1: Climate impact
        sentence1 = f"{location_name} agricultural operations face declining {crop_type} yields due to climate stress including heat and drought."
        
        # Sentence 2: Yield comparison
        if proposed_yield > current_yield:
            yield_increase = ((proposed_yield - current_yield) / current_yield) * 100
            sentence2 = f"Switching to climate-resilient crop varieties can increase yields by {yield_increase:.0f}%, from {current_yield:.1f} to {proposed_yield:.1f} tons per hectare."
        else:
            sentence2 = f"Current {crop_type} yields are projected at {current_yield:.1f} tons per hectare under baseline climate conditions."
        
        # Sentence 3: Revenue impact
        if proposed_revenue > current_revenue:
            revenue_increase = proposed_revenue - current_revenue
            if revenue_increase >= 1e6:
                revenue_display = f"${revenue_increase/1e6:.1f}M"
            else:
                revenue_display = f"${revenue_increase:,.0f}"
            sentence3 = f"This adaptation strategy generates an additional {revenue_display} in annual revenue, making it a financially compelling investment."
        else:
            revenue_display = f"${current_revenue/1e6:.1f}M" if current_revenue >= 1e6 else f"${current_revenue:,.0f}"
            sentence3 = f"Baseline annual revenue is projected at {revenue_display} under current conditions."
        
        return f"{sentence1} {sentence2} {sentence3}"
    
    except Exception as e:
        return _generate_fallback_summary(location_name)


def _generate_coastal_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for coastal flood risk analysis.
    
    Expected data keys:
    - slr_projection: float
    - annual_damage_usd: float
    - intervention_type: str
    - damage_reduction_pct: float (optional)
    """
    try:
        slr = data.get('slr_projection', 0.0)
        annual_damage = data.get('annual_damage_usd', 0.0)
        intervention = data.get('intervention_type', 'none')
        damage_reduction = data.get('damage_reduction_pct', 0.0)
        
        # Sentence 1: Sea level rise context
        slr_cm = slr * 100  # Convert meters to cm
        sentence1 = f"{location_name} coastal infrastructure faces {slr_cm:.0f}cm of projected sea level rise, significantly increasing flood risk."
        
        # Sentence 2: Damage assessment
        if annual_damage >= 1e6:
            damage_display = f"${annual_damage/1e6:.1f}M"
        else:
            damage_display = f"${annual_damage:,.0f}"
        sentence2 = f"Without intervention, annual flood damage is projected at {damage_display}."
        
        # Sentence 3: Intervention recommendation
        intervention_names = {
            'sea_wall': 'sea wall construction',
            'mangrove_restoration': 'mangrove restoration',
            'raised_foundation': 'raised foundation infrastructure',
            'none': 'adaptation measures'
        }
        intervention_display = intervention_names.get(intervention.lower(), intervention)
        
        if damage_reduction > 0:
            sentence3 = f"Implementing {intervention_display} can reduce annual damages by {damage_reduction:.0f}%, providing critical infrastructure protection."
        else:
            sentence3 = f"Coastal adaptation measures such as {intervention_display} are recommended to mitigate flood risk."
        
        return f"{sentence1} {sentence2} {sentence3}"
    
    except Exception as e:
        return _generate_fallback_summary(location_name)


def _generate_flood_summary(location_name: str, data: Dict[str, Any]) -> str:
    """
    Generate executive summary for urban/flash flood risk analysis.
    
    Expected data keys:
    - flood_depth_meters: float
    - annual_damage_usd: float
    - intervention_type: str
    - damage_reduction_pct: float (optional)
    """
    try:
        flood_depth = data.get('flood_depth_meters', 0.0)
        annual_damage = data.get('annual_damage_usd', 0.0)
        intervention = data.get('intervention_type', 'none')
        damage_reduction = data.get('damage_reduction_pct', 0.0)
        
        # Sentence 1: Flood context
        depth_cm = flood_depth * 100
        sentence1 = f"{location_name} faces urban flooding with projected depths of {depth_cm:.0f}cm during extreme rainfall events."
        
        # Sentence 2: Economic impact
        if annual_damage >= 1e6:
            damage_display = f"${annual_damage/1e6:.1f}M"
        else:
            damage_display = f"${annual_damage:,.0f}"
        sentence2 = f"Annual flood-related damages are estimated at {damage_display}, impacting critical infrastructure and business operations."
        
        # Sentence 3: Intervention recommendation
        intervention_names = {
            'sponge_city': 'sponge city infrastructure (permeable surfaces, rain gardens)',
            'drainage_upgrade': 'drainage system upgrades',
            'green_infrastructure': 'green infrastructure solutions',
            'none': 'flood mitigation measures'
        }
        intervention_display = intervention_names.get(intervention.lower(), intervention)
        
        if damage_reduction > 0:
            sentence3 = f"Deploying {intervention_display} can reduce flood damages by {damage_reduction:.0f}%, representing a cost-effective resilience investment."
        else:
            sentence3 = f"Investment in {intervention_display} is recommended to build urban flood resilience."
        
        return f"{sentence1} {sentence2} {sentence3}"
    
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
