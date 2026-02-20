# =============================================================================
# Sensitivity Engine - Diagnostic Stress Testing
# =============================================================================
"""
Runs 4 distinct stress tests on each location to identify primary risk drivers:
1. Climate Shock: +2°C temperature increase
2. Water Shock: -20% rainfall decrease
3. Market Shock: -15% crop price decrease
4. Operational Shock: +15% opex/capex increase
"""

from typing import Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from financial_engine import calculate_npv, generate_cash_flows
from physics_engine import calculate_yield


def calculate_baseline_npv(location: Dict[str, Any]) -> Tuple[float, float]:
    """
    Calculate baseline NPV for a location using its current parameters.
    
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
    
    # Use resilient seed (type=1) as the baseline for investment analysis
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


def run_climate_shock(location: Dict[str, Any], temp_increase: float = 2.0) -> float:
    """
    Climate Shock: Increase temperature by specified amount.
    Returns NPV under climate shock conditions.
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # Apply temperature shock via temp_delta
    shocked_yield = calculate_yield(
        temp, rain, seed_type=1, crop_type=crop_type, 
        temp_delta=temp_increase
    )
    
    # Financial parameters
    capex = assumptions.get('capex', 2000.0)
    opex = assumptions.get('opex', 425.0)
    price_per_ton = assumptions.get('price_per_ton', 4000.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    annual_benefit = (yield_benefit_pct / 100.0) * (shocked_yield / 100.0) * price_per_ton
    cash_flows = generate_cash_flows(capex, opex, annual_benefit, analysis_years)
    
    return calculate_npv(cash_flows, discount_rate)


def run_water_shock(location: Dict[str, Any], rainfall_change_pct: float = -20.0) -> float:
    """
    Water Shock: Decrease rainfall by specified percentage.
    Returns NPV under water stress conditions.
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # Apply rainfall shock via rain_pct_change
    shocked_yield = calculate_yield(
        temp, rain, seed_type=1, crop_type=crop_type,
        rain_pct_change=rainfall_change_pct
    )
    
    # Financial parameters
    capex = assumptions.get('capex', 2000.0)
    opex = assumptions.get('opex', 425.0)
    price_per_ton = assumptions.get('price_per_ton', 4000.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    annual_benefit = (yield_benefit_pct / 100.0) * (shocked_yield / 100.0) * price_per_ton
    cash_flows = generate_cash_flows(capex, opex, annual_benefit, analysis_years)
    
    return calculate_npv(cash_flows, discount_rate)


def run_market_shock(location: Dict[str, Any], price_change_pct: float = -15.0) -> float:
    """
    Market Shock: Decrease crop price by specified percentage.
    Returns NPV under market stress conditions.
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # Calculate yield at baseline (no climate shock)
    baseline_yield = calculate_yield(temp, rain, seed_type=1, crop_type=crop_type)
    
    # Financial parameters with shocked price
    capex = assumptions.get('capex', 2000.0)
    opex = assumptions.get('opex', 425.0)
    base_price = assumptions.get('price_per_ton', 4000.0)
    shocked_price = base_price * (1 + price_change_pct / 100.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    annual_benefit = (yield_benefit_pct / 100.0) * (baseline_yield / 100.0) * shocked_price
    cash_flows = generate_cash_flows(capex, opex, annual_benefit, analysis_years)
    
    return calculate_npv(cash_flows, discount_rate)


def run_operational_shock(location: Dict[str, Any], cost_increase_pct: float = 15.0) -> float:
    """
    Operational Shock: Increase opex and capex by specified percentage.
    Returns NPV under operational cost stress conditions.
    """
    climate = location.get('climate_conditions', {})
    crop_analysis = location.get('crop_analysis', {})
    financial = location.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    
    temp = climate.get('temperature_c', 25.0)
    rain = climate.get('rainfall_mm', 1000.0)
    crop_type = crop_analysis.get('crop_type', 'rice')
    
    # Calculate yield at baseline
    baseline_yield = calculate_yield(temp, rain, seed_type=1, crop_type=crop_type)
    
    # Financial parameters with shocked costs
    base_capex = assumptions.get('capex', 2000.0)
    base_opex = assumptions.get('opex', 425.0)
    shocked_capex = base_capex * (1 + cost_increase_pct / 100.0)
    shocked_opex = base_opex * (1 + cost_increase_pct / 100.0)
    price_per_ton = assumptions.get('price_per_ton', 4000.0)
    yield_benefit_pct = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    annual_benefit = (yield_benefit_pct / 100.0) * (baseline_yield / 100.0) * price_per_ton
    cash_flows = generate_cash_flows(shocked_capex, shocked_opex, annual_benefit, analysis_years)
    
    return calculate_npv(cash_flows, discount_rate)


def run_sensitivity_analysis(location: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run all 4 stress tests on a single location.
    
    Args:
        location: A single location object from the Atlas
    
    Returns:
        Dictionary with:
        - primary_driver: The shock that caused the largest NPV drop
        - driver_impact_pct: The percentage impact of the primary driver
        - sensitivity_ranking: Ordered list of all shocks by impact
    """
    # Calculate baseline NPV
    baseline_npv, _ = calculate_baseline_npv(location)
    
    # Run all 4 shocks
    climate_npv = run_climate_shock(location)
    water_npv = run_water_shock(location)
    market_npv = run_market_shock(location)
    operational_npv = run_operational_shock(location)
    
    # Calculate percentage drops (positive = NPV decreased)
    def calc_drop_pct(shocked_npv: float, baseline: float) -> float:
        if baseline == 0:
            return 0.0 if shocked_npv >= 0 else 100.0
        return round(((baseline - shocked_npv) / abs(baseline)) * 100, 2)
    
    shocks = [
        {
            "driver": "Climate (+2°C)",
            "shocked_npv": round(climate_npv, 2),
            "impact_pct": calc_drop_pct(climate_npv, baseline_npv)
        },
        {
            "driver": "Water Stress (-20%)",
            "shocked_npv": round(water_npv, 2),
            "impact_pct": calc_drop_pct(water_npv, baseline_npv)
        },
        {
            "driver": "Market Price (-15%)",
            "shocked_npv": round(market_npv, 2),
            "impact_pct": calc_drop_pct(market_npv, baseline_npv)
        },
        {
            "driver": "Operational Costs (+15%)",
            "shocked_npv": round(operational_npv, 2),
            "impact_pct": calc_drop_pct(operational_npv, baseline_npv)
        }
    ]
    
    # Sort by impact (highest impact first)
    sensitivity_ranking = sorted(shocks, key=lambda x: x['impact_pct'], reverse=True)
    
    # Get primary driver
    primary = sensitivity_ranking[0]
    
    return {
        "baseline_npv": round(baseline_npv, 2),
        "primary_driver": primary['driver'],
        "driver_impact_pct": primary['impact_pct'],
        "sensitivity_ranking": sensitivity_ranking
    }


def run_parallel_sensitivity(locations: List[Dict[str, Any]], max_workers: int = 10) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis on all locations in parallel.
    
    Args:
        locations: List of location objects from the Atlas
        max_workers: Number of parallel threads
    
    Returns:
        List of sensitivity analysis results in the same order as input
    """
    results = [None] * len(locations)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_idx = {
            executor.submit(run_sensitivity_analysis, loc): idx 
            for idx, loc in enumerate(locations)
        }
        
        # Collect results
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                # Handle errors gracefully
                results[idx] = {
                    "baseline_npv": 0.0,
                    "primary_driver": "Error",
                    "driver_impact_pct": 0.0,
                    "sensitivity_ranking": [],
                    "error": str(e)
                }
    
    return results


if __name__ == "__main__":
    # Test with sample data
    sample_location = {
        "location": {"lat": 31.8612, "lon": 117.284},
        "climate_conditions": {
            "temperature_c": 23.3,
            "rainfall_mm": 796.9
        },
        "crop_analysis": {
            "crop_type": "rice",
            "resilient_yield_pct": 64.75
        },
        "financial_analysis": {
            "npv_usd": 840053.01,
            "assumptions": {
                "capex": 2000.0,
                "opex": 425.0,
                "yield_benefit_pct": 30.0,
                "price_per_ton": 4000.0,
                "discount_rate_pct": 10.0,
                "analysis_years": 10
            }
        }
    }
    
    result = run_sensitivity_analysis(sample_location)
    print("Sensitivity Analysis Results:")
    print(f"  Baseline NPV: ${result['baseline_npv']:,.2f}")
    print(f"  Primary Driver: {result['primary_driver']}")
    print(f"  Driver Impact: {result['driver_impact_pct']:.1f}%")
    print("\n  Sensitivity Ranking:")
    for shock in result['sensitivity_ranking']:
        print(f"    - {shock['driver']}: {shock['impact_pct']:.1f}% (NPV: ${shock['shocked_npv']:,.2f})")
