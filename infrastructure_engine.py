# =============================================================================
# Infrastructure Engine - Flood Damage and ROI Analysis
# =============================================================================

from typing import Optional, Dict
from financial_engine import calculate_roi_metrics, generate_cash_flows


# Research-based depth-damage curve anchor points
# Source: Empirical flood damage studies
DEPTH_DAMAGE_CURVE = [
    (0.0, 0.0),    # 0m = 0% damage
    (0.5, 18.0),   # 0.5m = 18% damage
    (1.0, 29.0),   # 1.0m = 29% damage
    (2.0, 49.0),   # 2.0m = 49% damage
    (3.0, 60.0),   # 3.0m = 60% damage
]

# Business interruption threshold
INTERRUPTION_DEPTH_THRESHOLD_M = 0.3
INTERRUPTION_DAYS = 5


def calculate_damage_cost(flood_depth_m: float, asset_value: float) -> float:
    """
    Calculate flood damage cost using piecewise linear interpolation.
    
    Uses research-based depth-damage curve with anchor points:
    - 0.0m = 0% damage
    - 0.5m = 18% damage
    - 1.0m = 29% damage
    - 2.0m = 49% damage
    - 3.0m = 60% damage
    
    Args:
        flood_depth_m: Flood depth in meters
        asset_value: Total asset value (infrastructure value)
    
    Returns:
        Damage cost in currency units
    """
    if flood_depth_m <= 0:
        return 0.0
    
    # If depth exceeds maximum anchor point, use maximum damage %
    if flood_depth_m >= DEPTH_DAMAGE_CURVE[-1][0]:
        damage_pct = DEPTH_DAMAGE_CURVE[-1][1]
        return (damage_pct / 100.0) * asset_value
    
    # Find the two anchor points to interpolate between
    for i in range(len(DEPTH_DAMAGE_CURVE) - 1):
        depth_lower, damage_lower = DEPTH_DAMAGE_CURVE[i]
        depth_upper, damage_upper = DEPTH_DAMAGE_CURVE[i + 1]
        
        if depth_lower <= flood_depth_m <= depth_upper:
            # Linear interpolation
            # damage = damage_lower + (flood_depth - depth_lower) * slope
            slope = (damage_upper - damage_lower) / (depth_upper - depth_lower)
            damage_pct = damage_lower + (flood_depth_m - depth_lower) * slope
            
            return (damage_pct / 100.0) * asset_value
    
    # Should never reach here, but return 0 as fallback
    return 0.0


def calculate_business_interruption(flood_depth_m: float, daily_revenue: float) -> float:
    """
    Calculate business interruption cost due to flooding.
    
    If flood depth exceeds threshold (0.3m), assumes business downtime.
    
    Args:
        flood_depth_m: Flood depth in meters
        daily_revenue: Daily revenue of business
    
    Returns:
        Business interruption cost
    """
    if flood_depth_m > INTERRUPTION_DEPTH_THRESHOLD_M:
        return INTERRUPTION_DAYS * daily_revenue
    return 0.0


def calculate_intervention_depth(
    flood_depth_m: float,
    intervention_type: str,
    wall_height_m: float = 2.0,
    drainage_reduction_m: float = 0.3
) -> float:
    """
    Calculate effective flood depth after intervention.
    
    Args:
        flood_depth_m: Original flood depth in meters
        intervention_type: 'sea_wall' or 'drainage'
        wall_height_m: Height of sea wall (default: 2.0m)
        drainage_reduction_m: Flood depth reduction from drainage (default: 0.3m)
    
    Returns:
        Effective flood depth after intervention
    """
    if intervention_type == 'sea_wall':
        # Sea wall blocks water up to wall height
        return max(0.0, flood_depth_m - wall_height_m)
    elif intervention_type == 'drainage':
        # Improved drainage reduces flood depth
        return max(0.0, flood_depth_m - drainage_reduction_m)
    else:
        # No intervention
        return flood_depth_m


def calculate_infrastructure_roi(
    flood_depth_m: float,
    asset_value: float,
    daily_revenue: float,
    project_capex: float,
    project_opex: float,
    intervention_type: str,
    analysis_years: int = 20,
    discount_rate: float = 0.10,
    wall_height_m: float = 2.0,
    drainage_reduction_m: float = 0.3
) -> Dict:
    """
    Calculate ROI for flood protection infrastructure investment.
    
    Compares Business as Usual (BAU) with intervention scenario.
    
    Args:
        flood_depth_m: Expected flood depth in meters (baseline)
        asset_value: Total asset value at risk
        daily_revenue: Daily business revenue
        project_capex: Initial investment cost
        project_opex: Annual maintenance cost
        intervention_type: 'sea_wall' or 'drainage'
        analysis_years: Time horizon for analysis (default: 20)
        discount_rate: Discount rate as decimal (default: 0.10)
        wall_height_m: Sea wall height (default: 2.0m)
        drainage_reduction_m: Drainage flood reduction (default: 0.3m)
    
    Returns:
        Dictionary with ROI metrics and damage analysis
    """
    # ========== Baseline (Business as Usual) ==========
    # Calculate damage without intervention
    damage_bau = calculate_damage_cost(flood_depth_m, asset_value)
    interruption_bau = calculate_business_interruption(flood_depth_m, daily_revenue)
    total_loss_bau = damage_bau + interruption_bau
    
    # ========== Intervention Scenario ==========
    # Calculate effective flood depth after intervention
    effective_depth = calculate_intervention_depth(
        flood_depth_m,
        intervention_type,
        wall_height_m,
        drainage_reduction_m
    )
    
    # Calculate damage with intervention
    damage_intervention = calculate_damage_cost(effective_depth, asset_value)
    interruption_intervention = calculate_business_interruption(effective_depth, daily_revenue)
    total_loss_intervention = damage_intervention + interruption_intervention
    
    # ========== ROI Calculation ==========
    # Annual avoided loss (benefit)
    annual_avoided_loss = total_loss_bau - total_loss_intervention
    
    # Generate cash flows for analysis period
    # Year 0: -CAPEX (initial investment)
    # Years 1-N: Avoided loss - OPEX (net annual benefit)
    cash_flows = []
    
    # Year 0: Initial investment
    cash_flows.append(-project_capex)
    
    # Years 1 to analysis_years
    for year in range(1, analysis_years + 1):
        net_benefit = annual_avoided_loss - project_opex
        cash_flows.append(net_benefit)
    
    # Calculate financial metrics using financial engine
    roi_metrics = calculate_roi_metrics(cash_flows, discount_rate)
    
    # ========== Response Structure ==========
    return {
        'baseline_scenario': {
            'flood_depth_m': round(flood_depth_m, 2),
            'asset_damage': round(damage_bau, 2),
            'business_interruption': round(interruption_bau, 2),
            'total_annual_loss': round(total_loss_bau, 2)
        },
        'intervention_scenario': {
            'type': intervention_type,
            'effective_flood_depth_m': round(effective_depth, 2),
            'asset_damage': round(damage_intervention, 2),
            'business_interruption': round(interruption_intervention, 2),
            'total_annual_loss': round(total_loss_intervention, 2)
        },
        'financial_analysis': {
            'annual_avoided_loss': round(annual_avoided_loss, 2),
            'project_capex': project_capex,
            'project_opex': project_opex,
            'npv': roi_metrics['npv'],
            'bcr': roi_metrics['bcr'],
            'payback_years': roi_metrics['payback_period_years'],
            'analysis_years': analysis_years,
            'discount_rate_pct': discount_rate * 100
        },
        'recommendation': {
            'invest': roi_metrics['npv'] > 0 and roi_metrics['bcr'] > 1.0,
            'reason': _get_recommendation_reason(roi_metrics['npv'], roi_metrics['bcr'])
        }
    }


# Default downtime reduction when an intervention is in place (e.g. Sea Wall, Sponge City)
DOWNTIME_REDUCTION_WITH_INTERVENTION = 0.80  # 80% reduction


def calculate_avoided_business_interruption(
    daily_revenue: float,
    expected_downtime_days: int,
    has_intervention: bool,
    downtime_reduction_pct: float = DOWNTIME_REDUCTION_WITH_INTERVENTION,
) -> Dict:
    """
    Calculate baseline business interruption cost and avoided loss when an intervention
    reduces effective downtime (Cascading Network Failures / Business Interruption).

    Math:
      baseline_interruption = daily_revenue * expected_downtime_days
      If intervention: adapted_downtime_days = expected_downtime_days * (1 - downtime_reduction_pct)
      adapted_interruption = daily_revenue * adapted_downtime_days
      avoided_business_interruption = baseline_interruption - adapted_interruption

    Args:
        daily_revenue: Daily revenue (USD).
        expected_downtime_days: Expected downtime days without intervention.
        has_intervention: True if user selected an intervention (e.g. Sea Wall, Sponge City).
        downtime_reduction_pct: Fraction of downtime avoided with intervention (default 0.80).

    Returns:
        Dict with baseline_interruption, adapted_interruption, avoided_business_interruption (all >= 0).
    """
    baseline_interruption = daily_revenue * max(0, expected_downtime_days)
    if not has_intervention or expected_downtime_days <= 0:
        return {
            'baseline_interruption': round(baseline_interruption, 2),
            'adapted_interruption': round(baseline_interruption, 2),
            'avoided_business_interruption': 0.0,
        }
    adapted_downtime_days = max(0, expected_downtime_days * (1.0 - downtime_reduction_pct))
    adapted_interruption = daily_revenue * adapted_downtime_days
    avoided = baseline_interruption - adapted_interruption
    return {
        'baseline_interruption': round(baseline_interruption, 2),
        'adapted_interruption': round(adapted_interruption, 2),
        'avoided_business_interruption': round(avoided, 2),
    }


def _get_recommendation_reason(npv: float, bcr: float) -> str:
    """Generate investment recommendation reason based on NPV and BCR."""
    if npv > 0 and bcr > 1.0:
        return f"Positive NPV (${npv:,.0f}) and BCR > 1 ({bcr:.2f}) indicate strong investment"
    elif npv > 0:
        return f"Positive NPV (${npv:,.0f}) but BCR < 1, marginal investment"
    elif bcr > 1.0:
        return f"BCR > 1 ({bcr:.2f}) but negative NPV, benefits don't justify costs"
    else:
        return f"Negative NPV (${npv:,.0f}) and BCR < 1 ({bcr:.2f}), poor investment"
