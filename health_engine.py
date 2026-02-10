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
