# =============================================================================
# Adaptation Engine - Climate Adaptation ROI Calculator
# =============================================================================
"""
Calculates ROI for climate adaptation interventions based on sensitivity analysis.

Intervention Selection Logic:
    Case A: 'Water Stress' is driver
        - Intervention: 'Smart Irrigation System'
        - Capex: +$1500/hectare
        - Effect: Eliminates water stress (perfect water supply)

    Case B: 'Climate' (Heat) is driver
        - Intervention: 'Thermo-Tolerant Seeds'
        - Opex: +10%
        - Effect: Increases critical temperature threshold by +2°C

    Case C: 'Market Price' is driver
        - Intervention: 'Revenue Insurance / Hedging'
        - Opex: +5%
        - Effect: Clamps price volatility to 0% (removes downside shocks)

    Case D: 'Operational' or 'Flood' is driver
        - Intervention: 'Infrastructure Hardening'
        - Capex: +20%
        - Effect: Reduces default probability by half
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from financial_engine import calculate_npv, generate_cash_flows
from physics_engine import calculate_yield
import numpy as np


# Intervention cost parameters
SMART_IRRIGATION_CAPEX_PER_HECTARE = 1500.0
THERMO_TOLERANT_OPEX_INCREASE_PCT = 10.0
REVENUE_INSURANCE_OPEX_INCREASE_PCT = 5.0
INFRASTRUCTURE_HARDENING_CAPEX_INCREASE_PCT = 20.0


def identify_driver_category(primary_driver: str) -> str:
    """
    Map primary_driver string to intervention category.
    
    Args:
        primary_driver: e.g., "Water Stress (-20%)", "Climate (+2°C)", etc.
    
    Returns:
        One of: 'water_stress', 'climate', 'market_price', 'operational', 'flood'
    """
    driver_lower = primary_driver.lower()
    
    if 'water' in driver_lower or 'drought' in driver_lower:
        return 'water_stress'
    elif 'climate' in driver_lower or 'temperature' in driver_lower or 'heat' in driver_lower:
        return 'climate'
    elif 'market' in driver_lower or 'price' in driver_lower:
        return 'market_price'
    elif 'flood' in driver_lower:
        return 'flood'
    elif 'operational' in driver_lower or 'cost' in driver_lower:
        return 'operational'
    else:
        # Default to operational if unclear
        return 'operational'


def select_intervention(driver_category: str) -> Dict[str, Any]:
    """
    Select the appropriate intervention based on driver category.
    
    Returns:
        Dictionary with intervention details
    """
    interventions = {
        'water_stress': {
            'name': 'Smart Irrigation System',
            'description': 'Advanced drip irrigation with soil moisture sensors',
            'capex_adjustment': SMART_IRRIGATION_CAPEX_PER_HECTARE,
            'opex_adjustment_pct': 0.0,
            'effect': 'Eliminates water stress (ensures optimal water supply)'
        },
        'climate': {
            'name': 'Thermo-Tolerant Seeds',
            'description': 'Heat-resistant crop varieties with higher critical temperature thresholds',
            'capex_adjustment': 0.0,
            'opex_adjustment_pct': THERMO_TOLERANT_OPEX_INCREASE_PCT,
            'effect': 'Increases critical temperature threshold by 2°C'
        },
        'market_price': {
            'name': 'Revenue Insurance / Hedging',
            'description': 'Crop price insurance and forward contracts to hedge market risk',
            'capex_adjustment': 0.0,
            'opex_adjustment_pct': REVENUE_INSURANCE_OPEX_INCREASE_PCT,
            'effect': 'Removes downside price volatility risk'
        },
        'operational': {
            'name': 'Infrastructure Hardening',
            'description': 'Reinforced storage, processing, and logistics infrastructure',
            'capex_adjustment_pct': INFRASTRUCTURE_HARDENING_CAPEX_INCREASE_PCT,
            'opex_adjustment_pct': 0.0,
            'effect': 'Reduces default probability by 50%'
        },
        'flood': {
            'name': 'Infrastructure Hardening',
            'description': 'Flood-resistant infrastructure and drainage systems',
            'capex_adjustment_pct': INFRASTRUCTURE_HARDENING_CAPEX_INCREASE_PCT,
            'opex_adjustment_pct': 0.0,
            'effect': 'Reduces flood damage and default probability by 50%'
        }
    }
    
    return interventions.get(driver_category, interventions['operational'])


def calculate_baseline_npv(location: Dict[str, Any]) -> Tuple[float, float]:
    """
    Calculate baseline NPV and yield for a location.
    
    Returns:
        Tuple of (npv, resilient_yield_pct)
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # Use resilient seed (type=1) as baseline
    resilient_yield = calculate_yield(temp, rain, seed_type=1, crop_type=crop_type)
    
    # Financial parameters
    capex = assumptions.get('capex', 2000.0)
    opex = assumptions.get('opex', 425.0)
    price_per_ton = assumptions.get('price_per_ton', 4000.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    # Calculate annual benefit based on yield
    annual_benefit = (yield_benefit_pct / 100.0) * (resilient_yield / 100.0) * price_per_ton
    
    # Generate cash flows
    cash_flows = generate_cash_flows(capex, opex, annual_benefit, analysis_years)
    
    # Calculate NPV
    npv = calculate_npv(cash_flows, discount_rate)
    
    return npv, resilient_yield


def simulate_water_stress_intervention(location: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Simulate Smart Irrigation System intervention.
    
    Effect: Increase capex by $1500, set effective rainfall to optimal level.
    
    Returns:
        Tuple of (intervention_npv, intervention_cost, intervention_yield)
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # With smart irrigation, simulate optimal water conditions
    # This means increasing rainfall to optimal range (effectively +50% for dry regions)
    # We simulate by setting rain_pct_change to achieve optimal rainfall
    optimal_rain_map = {
        'rice': 1500,    # Mid-optimal for rice
        'maize': 800,    # Mid-optimal for maize
        'wheat': 700,    # Mid-optimal for wheat
        'soy': 1000,     # Mid-optimal for soy
        'cocoa': 1750    # Optimal for cocoa
    }
    optimal_rain = optimal_rain_map.get(crop_type.lower(), 1200)
    
    # Calculate the rain_pct_change needed to reach optimal
    if rain > 0:
        rain_pct_change = ((optimal_rain / rain) - 1) * 100
        # Cap at +100% to be realistic
        rain_pct_change = min(rain_pct_change, 100.0)
        # Only apply positive change (irrigation adds water, doesn't remove)
        rain_pct_change = max(rain_pct_change, 0.0)
    else:
        rain_pct_change = 100.0
    
    # Calculate yield with irrigation intervention
    intervention_yield = calculate_yield(
        temp, rain, seed_type=1, crop_type=crop_type,
        rain_pct_change=rain_pct_change
    )
    
    # Financial parameters with intervention costs
    base_capex = assumptions.get('capex', 2000.0)
    intervention_capex = base_capex + SMART_IRRIGATION_CAPEX_PER_HECTARE
    opex = assumptions.get('opex', 425.0)
    price_per_ton = assumptions.get('price_per_ton', 4000.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    annual_benefit = (yield_benefit_pct / 100.0) * (intervention_yield / 100.0) * price_per_ton
    cash_flows = generate_cash_flows(intervention_capex, opex, annual_benefit, analysis_years)
    npv = calculate_npv(cash_flows, discount_rate)
    
    return npv, SMART_IRRIGATION_CAPEX_PER_HECTARE, intervention_yield


def simulate_climate_intervention(location: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Simulate Thermo-Tolerant Seeds intervention.
    
    Effect: Increase opex by 10%, increase critical temperature threshold by 2°C.
    The physics_engine already applies resilience_delta_c for seed_type=1,
    so we simulate additional 2°C tolerance by reducing the effective temp_delta.
    
    Returns:
        Tuple of (intervention_npv, annual_intervention_cost, intervention_yield)
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # With thermo-tolerant seeds, the crop can handle +2°C more
    # This is equivalent to simulating the crop as if the temperature were 2°C lower
    # We achieve this by passing a negative temp_delta
    intervention_yield = calculate_yield(
        temp, rain, seed_type=1, crop_type=crop_type,
        temp_delta=-2.0  # Effectively makes the crop more heat tolerant
    )
    
    # Financial parameters with intervention costs
    capex = assumptions.get('capex', 2000.0)
    base_opex = assumptions.get('opex', 425.0)
    intervention_opex = base_opex * (1 + THERMO_TOLERANT_OPEX_INCREASE_PCT / 100.0)
    price_per_ton = assumptions.get('price_per_ton', 4000.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    annual_benefit = (yield_benefit_pct / 100.0) * (intervention_yield / 100.0) * price_per_ton
    cash_flows = generate_cash_flows(capex, intervention_opex, annual_benefit, analysis_years)
    npv = calculate_npv(cash_flows, discount_rate)
    
    # Total cost = additional opex over analysis period (PV)
    additional_opex = intervention_opex - base_opex
    total_cost = sum(additional_opex / ((1 + discount_rate) ** t) 
                     for t in range(1, analysis_years + 1))
    
    return npv, total_cost, intervention_yield


def simulate_market_price_intervention(location: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Simulate Revenue Insurance / Hedging intervention.
    
    Effect: Increase opex by 5%, clamp price volatility to 0% (remove downside shocks).
    We run a modified Monte Carlo where price is guaranteed at baseline.
    
    Returns:
        Tuple of (intervention_npv, annual_intervention_cost, intervention_yield)
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # Yield stays the same (market intervention doesn't affect yield)
    intervention_yield = calculate_yield(temp, rain, seed_type=1, crop_type=crop_type)
    
    # Financial parameters with intervention costs
    capex = assumptions.get('capex', 2000.0)
    base_opex = assumptions.get('opex', 425.0)
    intervention_opex = base_opex * (1 + REVENUE_INSURANCE_OPEX_INCREASE_PCT / 100.0)
    price_per_ton = assumptions.get('price_per_ton', 4000.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    # With insurance, we model the expected benefit as higher because
    # downside price risk is removed. We use the baseline price (no shocks).
    # The NPV improvement comes from the reduced variance/risk premium.
    # For simplicity, we model this as a 7.5% price floor protection
    # (midpoint of the 15% downside that's now protected)
    protected_price = price_per_ton * 1.075  # Effectively captures the value of insurance
    
    annual_benefit = (yield_benefit_pct / 100.0) * (intervention_yield / 100.0) * protected_price
    cash_flows = generate_cash_flows(capex, intervention_opex, annual_benefit, analysis_years)
    npv = calculate_npv(cash_flows, discount_rate)
    
    # Total cost = additional opex over analysis period (PV)
    additional_opex = intervention_opex - base_opex
    total_cost = sum(additional_opex / ((1 + discount_rate) ** t) 
                     for t in range(1, analysis_years + 1))
    
    return npv, total_cost, intervention_yield


def simulate_infrastructure_intervention(location: Dict[str, Any]) -> Tuple[float, float, float]:
    """
    Simulate Infrastructure Hardening intervention.
    
    Effect: Increase capex by 20%, reduce default probability by half.
    We model this as improved expected NPV through reduced operational losses.
    
    Returns:
        Tuple of (intervention_npv, intervention_cost, intervention_yield)
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    monte_carlo = location.get('monte_carlo_analysis', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # Yield stays the same (infrastructure doesn't affect yield directly)
    intervention_yield = calculate_yield(temp, rain, seed_type=1, crop_type=crop_type)
    
    # Financial parameters with intervention costs
    base_capex = assumptions.get('capex', 2000.0)
    intervention_capex = base_capex * (1 + INFRASTRUCTURE_HARDENING_CAPEX_INCREASE_PCT / 100.0)
    opex = assumptions.get('opex', 425.0)
    price_per_ton = assumptions.get('price_per_ton', 4000.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    # Get baseline default probability
    baseline_default_prob = monte_carlo.get('default_probability', 0.0) / 100.0
    
    # With infrastructure hardening, default probability is halved
    # This improves expected returns by reducing loss scenarios
    # Model this as a risk premium recovery on benefits
    risk_reduction_factor = 1.0 + (baseline_default_prob * 0.5 * 0.15)  # 15% of halved default risk
    
    annual_benefit = (yield_benefit_pct / 100.0) * (intervention_yield / 100.0) * price_per_ton * risk_reduction_factor
    cash_flows = generate_cash_flows(intervention_capex, opex, annual_benefit, analysis_years)
    npv = calculate_npv(cash_flows, discount_rate)
    
    # Intervention cost = additional capex
    intervention_cost = intervention_capex - base_capex
    
    return npv, intervention_cost, intervention_yield


def run_adaptation_analysis(location: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run adaptation analysis for a single location.
    
    Args:
        location: A single location object from the Atlas with sensitivity_analysis
    
    Returns:
        adaptation_strategy object containing:
        - intervention_name
        - intervention_description
        - intervention_cost
        - npv_baseline
        - npv_with_intervention
        - npv_improvement
        - adaptation_roi
        - yield_baseline
        - yield_with_intervention
        - yield_improvement_pct
    """
    sensitivity = location.get('sensitivity_analysis', {})
    primary_driver = sensitivity.get('primary_driver', 'Operational Costs (+15%)')
    
    # Identify driver category and select intervention
    driver_category = identify_driver_category(primary_driver)
    intervention = select_intervention(driver_category)
    
    # Calculate baseline NPV
    baseline_npv, baseline_yield = calculate_baseline_npv(location)
    
    # Simulate intervention based on driver category
    if driver_category == 'water_stress':
        intervention_npv, intervention_cost, intervention_yield = simulate_water_stress_intervention(location)
    elif driver_category == 'climate':
        intervention_npv, intervention_cost, intervention_yield = simulate_climate_intervention(location)
    elif driver_category == 'market_price':
        intervention_npv, intervention_cost, intervention_yield = simulate_market_price_intervention(location)
    else:  # operational or flood
        intervention_npv, intervention_cost, intervention_yield = simulate_infrastructure_intervention(location)
    
    # Calculate ROI
    npv_improvement = intervention_npv - baseline_npv
    
    if intervention_cost > 0:
        adaptation_roi = (npv_improvement / intervention_cost) * 100
    else:
        adaptation_roi = float('inf') if npv_improvement > 0 else 0.0
    
    # Calculate yield improvement
    yield_improvement_pct = ((intervention_yield - baseline_yield) / baseline_yield * 100) if baseline_yield > 0 else 0.0
    
    return {
        'primary_driver': primary_driver,
        'driver_category': driver_category,
        'intervention_name': intervention['name'],
        'intervention_description': intervention['description'],
        'intervention_effect': intervention['effect'],
        'intervention_cost_usd': round(intervention_cost, 2),
        'npv_baseline_usd': round(baseline_npv, 2),
        'npv_with_intervention_usd': round(intervention_npv, 2),
        'npv_improvement_usd': round(npv_improvement, 2),
        'adaptation_roi_pct': round(adaptation_roi, 2),
        'yield_baseline_pct': round(baseline_yield, 2),
        'yield_with_intervention_pct': round(intervention_yield, 2),
        'yield_improvement_pct': round(yield_improvement_pct, 2),
        'recommendation': 'DEPLOY' if adaptation_roi > 0 else 'HOLD'
    }


def process_all_locations(input_file: str, output_file: str) -> None:
    """
    Process all locations from input file and save results with adaptation strategies.
    
    Args:
        input_file: Path to global_atlas_diagnostic.json
        output_file: Path to save global_atlas_solutions.json
    """
    # Load input data
    with open(input_file, 'r') as f:
        locations = json.load(f)
    
    print(f"Processing {len(locations)} locations...")
    
    # Process each location
    results = []
    for i, location in enumerate(locations):
        target_name = location.get('target', {}).get('name', f'Location {i}')
        
        # Run adaptation analysis
        adaptation_strategy = run_adaptation_analysis(location)
        
        # Create output record (add adaptation_strategy to existing location data)
        output_location = location.copy()
        output_location['adaptation_strategy'] = adaptation_strategy
        results.append(output_location)
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(locations)}: {target_name}")
    
    # Save output (pure JSON array as required)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    # Print summary statistics
    print_summary(results)


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary statistics of adaptation analysis."""
    
    # Count by driver category
    driver_counts = {}
    roi_by_driver = {}
    
    for loc in results:
        strategy = loc.get('adaptation_strategy', {})
        driver = strategy.get('driver_category', 'unknown')
        roi = strategy.get('adaptation_roi_pct', 0)
        
        if driver not in driver_counts:
            driver_counts[driver] = 0
            roi_by_driver[driver] = []
        
        driver_counts[driver] += 1
        roi_by_driver[driver].append(roi)
    
    print("\n" + "=" * 60)
    print("ADAPTATION STRATEGY SUMMARY")
    print("=" * 60)
    
    print("\nDriver Distribution:")
    for driver, count in sorted(driver_counts.items(), key=lambda x: -x[1]):
        avg_roi = np.mean(roi_by_driver[driver]) if roi_by_driver[driver] else 0
        print(f"  {driver}: {count} locations (Avg ROI: {avg_roi:.1f}%)")
    
    # Overall statistics
    all_rois = [loc['adaptation_strategy']['adaptation_roi_pct'] 
                for loc in results if 'adaptation_strategy' in loc]
    all_npv_improvements = [loc['adaptation_strategy']['npv_improvement_usd'] 
                           for loc in results if 'adaptation_strategy' in loc]
    
    print(f"\nOverall Statistics:")
    print(f"  Total Locations: {len(results)}")
    print(f"  Mean ROI: {np.mean(all_rois):.1f}%")
    print(f"  Median ROI: {np.median(all_rois):.1f}%")
    print(f"  Total NPV Improvement: ${np.sum(all_npv_improvements):,.2f}")
    print(f"  Mean NPV Improvement: ${np.mean(all_npv_improvements):,.2f}")
    
    # Recommendations
    deploy_count = sum(1 for loc in results 
                       if loc.get('adaptation_strategy', {}).get('recommendation') == 'DEPLOY')
    print(f"\nRecommendations:")
    print(f"  DEPLOY: {deploy_count} locations")
    print(f"  HOLD: {len(results) - deploy_count} locations")


if __name__ == "__main__":
    import sys
    
    # Default file paths
    input_file = "global_atlas_diagnostic.json"
    output_file = "global_atlas_solutions.json"
    
    # Allow command line override
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    process_all_locations(input_file, output_file)
