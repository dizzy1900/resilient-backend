# =============================================================================
# Health Engine - Climate Health Impact Analysis
# =============================================================================

from typing import Dict


def calculate_productivity_loss(temp_c: float, humidity_pct: float) -> Dict:
    """
    Calculate worker productivity loss due to heat stress using WBGT proxy.
    
    Uses simplified Wet Bulb Globe Temperature (WBGT) approximation for MVP.
    WBGT combines temperature and humidity to assess heat stress risk.
    
    Args:
        temp_c: Temperature in Celsius
        humidity_pct: Relative humidity as percentage (0-100)
    
    Returns:
        Dictionary with WBGT estimate and productivity loss percentage
    """
    # Simplified WBGT approximation
    # Full WBGT requires black globe temp and natural wet bulb temp
    # This proxy uses: WBGT ≈ 0.7*Temp + 0.1*Humidity
    wbgt_estimate = (temp_c * 0.7) + (humidity_pct / 10.0)
    
    # Productivity loss thresholds (research-based)
    # Source: ILO heat stress productivity guidelines
    LOW_THRESHOLD = 26.0   # Below this: no productivity loss
    HIGH_THRESHOLD = 32.0  # Above this: maximum loss (50% cap for safety)
    
    # Calculate productivity loss percentage
    if wbgt_estimate < LOW_THRESHOLD:
        # Safe working conditions
        loss_pct = 0.0
    elif wbgt_estimate > HIGH_THRESHOLD:
        # Dangerous heat stress - maximum loss
        loss_pct = 50.0
    else:
        # Linear interpolation between thresholds
        # loss = 0% at 26°C WBGT, 50% at 32°C WBGT
        range_wbgt = HIGH_THRESHOLD - LOW_THRESHOLD  # 6°C range
        excess_wbgt = wbgt_estimate - LOW_THRESHOLD
        loss_pct = (excess_wbgt / range_wbgt) * 50.0
    
    # Determine heat stress category
    if wbgt_estimate < 26.0:
        category = "Low"
        recommendation = "Normal work possible"
    elif wbgt_estimate < 28.0:
        category = "Moderate"
        recommendation = "Light work affected, breaks recommended"
    elif wbgt_estimate < 30.0:
        category = "High"
        recommendation = "Heavy work significantly affected"
    elif wbgt_estimate < 32.0:
        category = "Very High"
        recommendation = "All work affected, frequent breaks required"
    else:
        category = "Extreme"
        recommendation = "Work should be limited or stopped"
    
    return {
        'wbgt_estimate': round(wbgt_estimate, 1),
        'productivity_loss_pct': round(loss_pct, 1),
        'heat_stress_category': category,
        'recommendation': recommendation,
        'inputs': {
            'temperature_c': temp_c,
            'humidity_pct': humidity_pct
        }
    }


def calculate_malaria_risk(temp_c: float, precip_mm: float) -> Dict:
    """
    Calculate malaria transmission risk based on temperature and precipitation.
    
    Malaria mosquitoes (Anopheles) require specific climate conditions:
    - Temperature: 16-34°C optimal range for parasite development
    - Precipitation: >80mm for breeding site availability
    
    Args:
        temp_c: Average temperature in Celsius
        precip_mm: Total precipitation in millimeters
    
    Returns:
        Dictionary with malaria risk score and assessment
    """
    # Temperature suitability for malaria transmission
    # Plasmodium parasite development requires 16-34°C
    TEMP_MIN = 16.0  # Below this: parasite development too slow
    TEMP_MAX = 34.0  # Above this: mosquito survival compromised
    
    temp_suitable = TEMP_MIN <= temp_c <= TEMP_MAX
    
    # Precipitation threshold for mosquito breeding
    # Anopheles mosquitoes need standing water for larvae
    PRECIP_THRESHOLD = 80.0  # mm
    
    rain_suitable = precip_mm > PRECIP_THRESHOLD
    
    # Calculate risk score
    if temp_suitable and rain_suitable:
        # Both conditions met: High risk
        risk_score = 100
        risk_category = "High"
        description = "Climate conditions highly suitable for malaria transmission"
    elif temp_suitable or rain_suitable:
        # One condition met: Moderate risk
        risk_score = 50
        risk_category = "Moderate"
        if temp_suitable:
            description = "Temperature suitable but insufficient rainfall for mosquito breeding"
        else:
            description = "Adequate rainfall but temperature outside optimal range"
    else:
        # Neither condition met: Low risk
        risk_score = 0
        risk_category = "Low"
        description = "Climate conditions not suitable for malaria transmission"
    
    # Additional risk factors context
    risk_factors = []
    if temp_suitable:
        risk_factors.append("Temperature in optimal range (16-34°C)")
    if rain_suitable:
        risk_factors.append(f"Precipitation sufficient ({precip_mm:.0f}mm > 80mm threshold)")
    
    mitigation_measures = []
    if risk_score >= 50:
        mitigation_measures = [
            "Use insecticide-treated bed nets",
            "Indoor residual spraying",
            "Eliminate standing water",
            "Prophylactic medication for high-risk areas",
            "Early diagnosis and treatment"
        ]
    
    return {
        'risk_score': risk_score,
        'risk_category': risk_category,
        'description': description,
        'climate_suitability': {
            'temperature_suitable': temp_suitable,
            'precipitation_suitable': rain_suitable,
            'temperature_c': temp_c,
            'precipitation_mm': precip_mm
        },
        'risk_factors': risk_factors,
        'mitigation_measures': mitigation_measures
    }


def calculate_health_economic_impact(
    workforce_size: int,
    daily_wage: float,
    productivity_loss_pct: float,
    malaria_risk_score: int
) -> Dict:
    """
    Calculate economic impact of climate-related health risks.
    
    Args:
        workforce_size: Number of workers
        daily_wage: Average daily wage per worker
        productivity_loss_pct: Productivity loss from heat stress
        malaria_risk_score: Malaria risk score (0-100)
    
    Returns:
        Dictionary with economic impact metrics
    """
    # Heat stress economic impact
    daily_productivity_loss = (workforce_size * daily_wage) * (productivity_loss_pct / 100.0)
    
    # Annual productivity loss (assuming 250 working days/year)
    working_days_per_year = 250
    annual_productivity_loss = daily_productivity_loss * working_days_per_year
    
    # Malaria economic impact (absenteeism + healthcare costs)
    # High malaria risk areas lose ~10 working days per worker per year
    # Moderate risk: ~5 days, Low risk: 0 days
    if malaria_risk_score >= 75:
        malaria_days_lost = 10
    elif malaria_risk_score >= 25:
        malaria_days_lost = 5
    else:
        malaria_days_lost = 0
    
    malaria_economic_loss = workforce_size * daily_wage * malaria_days_lost
    
    # Healthcare costs for malaria (if high risk)
    # Average treatment cost per case: ~$50
    # Prevalence: ~20% of population in high-risk areas
    if malaria_risk_score >= 50:
        prevalence_pct = 0.20 if malaria_risk_score >= 75 else 0.10
        treatment_cost_per_case = 50.0
        healthcare_costs = workforce_size * prevalence_pct * treatment_cost_per_case
    else:
        healthcare_costs = 0.0
    
    # Total annual health-related economic loss
    total_annual_loss = annual_productivity_loss + malaria_economic_loss + healthcare_costs
    
    return {
        'heat_stress_impact': {
            'daily_productivity_loss': round(daily_productivity_loss, 2),
            'annual_productivity_loss': round(annual_productivity_loss, 2),
            'affected_workers': workforce_size,
            'loss_per_worker_daily': round(daily_wage * (productivity_loss_pct / 100.0), 2)
        },
        'malaria_impact': {
            'estimated_days_lost_per_worker': malaria_days_lost,
            'annual_absenteeism_cost': round(malaria_economic_loss, 2),
            'annual_healthcare_costs': round(healthcare_costs, 2)
        },
        'total_economic_impact': {
            'annual_loss': round(total_annual_loss, 2),
            'daily_loss_average': round(total_annual_loss / working_days_per_year, 2),
            'per_worker_annual_loss': round(total_annual_loss / workforce_size, 2)
        }
    }


def calculate_public_health_impact(
    population: int,
    gdp_per_capita: float,
    wbgt: float,
    malaria_risk_score: int,
    intervention_type: str = "none"
) -> Dict:
    """
    Calculate public health impact using DALYs (Disability-Adjusted Life Years).
    
    DALYs measure the burden of disease by combining years of life lost due to
    premature mortality and years lived with disability. This function calculates
    baseline DALYs from heat stress and malaria, applies intervention efficacy,
    and monetizes the health benefit using WHO standard (GDP per capita × 2).
    
    Args:
        population: Total population size
        gdp_per_capita: GDP per capita in USD for monetization
        wbgt: Wet Bulb Globe Temperature (°C)
        malaria_risk_score: Malaria risk score (0-100)
        intervention_type: Type of public health intervention
            - "urban_cooling_center": Reduces heat DALYs by 40%
            - "mosquito_eradication": Reduces malaria DALYs by 70%
            - "none": No intervention (baseline only)
    
    Returns:
        Dictionary with baseline DALYs, averted DALYs, and economic value
    
    References:
        - WHO Global Health Estimates (GHE) 2019
        - GBD 2019 (Global Burden of Disease Study)
        - WHO-CHOICE cost-effectiveness thresholds
    """
    # ========================================================================
    # SCIENTIFIC BASELINES (per 1,000 people)
    # ========================================================================
    # Source: WHO Global Health Estimates, heat-related mortality and morbidity
    # Heatwave conditions (WBGT > 30°C) cause cardiovascular stress, heat stroke,
    # respiratory complications, and exacerbate chronic conditions
    BASELINE_HEAT_DALYS_PER_1000 = 1.82
    
    # Source: WHO GBD 2019, malaria burden in high-transmission areas
    # Includes mortality (cerebral malaria, severe anemia) and morbidity
    # (fever, weakness, organ damage, neurological sequelae)
    BASELINE_MALARIA_DALYS_PER_1000 = 105.0
    
    # ========================================================================
    # INTERVENTION EFFICACY
    # ========================================================================
    # Urban cooling centers: Provide air-conditioned refuge during heatwaves,
    # reducing exposure to extreme heat for vulnerable populations (elderly, children)
    URBAN_COOLING_CENTER_EFFICACY = 0.40  # 40% reduction in heat DALYs
    
    # Mosquito eradication: Indoor residual spraying, larviciding, vector control
    # programs significantly reduce malaria transmission
    MOSQUITO_ERADICATION_EFFICACY = 0.70  # 70% reduction in malaria DALYs
    
    # ========================================================================
    # BASELINE DALY CALCULATION
    # ========================================================================
    # Calculate baseline heat-related DALYs
    # Heat stress is triggered when WBGT > 26°C (ILO threshold)
    if wbgt > 26.0:
        # Scale heat DALYs based on WBGT severity
        # At WBGT 26°C: minimal DALYs
        # At WBGT 32°C+: maximum DALYs
        heat_severity_factor = min((wbgt - 26.0) / 6.0, 1.0)  # 0.0 to 1.0
        baseline_heat_dalys_per_1000 = BASELINE_HEAT_DALYS_PER_1000 * heat_severity_factor
    else:
        baseline_heat_dalys_per_1000 = 0.0
    
    # Calculate baseline malaria DALYs based on risk score
    # Risk score 0-100 maps to 0-100% of baseline malaria burden
    baseline_malaria_dalys_per_1000 = BASELINE_MALARIA_DALYS_PER_1000 * (malaria_risk_score / 100.0)
    
    # Total baseline DALYs per 1,000 people
    baseline_dalys_per_1000 = baseline_heat_dalys_per_1000 + baseline_malaria_dalys_per_1000
    
    # Scale to actual population
    baseline_dalys_lost = (baseline_dalys_per_1000 / 1000.0) * population
    
    # ========================================================================
    # INTERVENTION EFFICACY APPLICATION
    # ========================================================================
    heat_reduction_factor = 0.0
    malaria_reduction_factor = 0.0
    intervention_description = "No intervention applied (baseline scenario)"
    
    intervention_lower = intervention_type.lower()
    
    if intervention_lower == "urban_cooling_center":
        heat_reduction_factor = URBAN_COOLING_CENTER_EFFICACY
        intervention_description = "Urban cooling centers reduce heat-related DALYs by 40%"
    
    elif intervention_lower == "mosquito_eradication":
        malaria_reduction_factor = MOSQUITO_ERADICATION_EFFICACY
        intervention_description = "Mosquito eradication programs reduce malaria DALYs by 70%"
    
    # Calculate post-intervention DALYs
    post_intervention_heat_dalys = baseline_heat_dalys_per_1000 * (1 - heat_reduction_factor)
    post_intervention_malaria_dalys = baseline_malaria_dalys_per_1000 * (1 - malaria_reduction_factor)
    post_intervention_dalys_per_1000 = post_intervention_heat_dalys + post_intervention_malaria_dalys
    
    # Scale to actual population
    post_intervention_dalys_lost = (post_intervention_dalys_per_1000 / 1000.0) * population
    
    # Calculate averted DALYs
    dalys_averted = baseline_dalys_lost - post_intervention_dalys_lost
    
    # ========================================================================
    # MONETIZATION (WHO Standard)
    # ========================================================================
    # WHO-CHOICE (CHOosing Interventions that are Cost-Effective) guidelines
    # recommend valuing one DALY at 2× GDP per capita for cost-effectiveness analysis
    # This represents the economic value of a healthy life year
    value_per_daly = gdp_per_capita * 2.0
    
    # Calculate total economic value preserved
    economic_value_preserved_usd = dalys_averted * value_per_daly
    
    # ========================================================================
    # RETURN COMPREHENSIVE ANALYSIS
    # ========================================================================
    return {
        'baseline_dalys_lost': round(baseline_dalys_lost, 2),
        'post_intervention_dalys_lost': round(post_intervention_dalys_lost, 2),
        'dalys_averted': round(dalys_averted, 2),
        'economic_value_preserved_usd': round(economic_value_preserved_usd, 2),
        'intervention_type': intervention_type,
        'intervention_description': intervention_description,
        'breakdown': {
            'heat_dalys_per_1000_baseline': round(baseline_heat_dalys_per_1000, 2),
            'malaria_dalys_per_1000_baseline': round(baseline_malaria_dalys_per_1000, 2),
            'total_dalys_per_1000_baseline': round(baseline_dalys_per_1000, 2),
            'heat_reduction_pct': round(heat_reduction_factor * 100, 1),
            'malaria_reduction_pct': round(malaria_reduction_factor * 100, 1),
        },
        'monetization': {
            'gdp_per_capita_usd': round(gdp_per_capita, 2),
            'value_per_daly_usd': round(value_per_daly, 2),
            'methodology': "WHO-CHOICE standard: 2× GDP per capita per DALY"
        },
        'population_parameters': {
            'population_size': population,
            'baseline_dalys_per_1000': round(baseline_dalys_per_1000, 2),
            'post_intervention_dalys_per_1000': round(post_intervention_dalys_per_1000, 2)
        }
    }
