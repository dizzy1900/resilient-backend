# =============================================================================
# Monte Carlo Engine - Financial Stress Testing
# =============================================================================
"""
Simulates financial outcomes under various risk scenarios:
- Yield Volatility: Random normal variation (std_dev = 15% of base yield)
- Market Risk: Price volatility (+/- 10%)
- Execution Risk: CAPEX overruns (+/- 5%)
"""

import numpy as np
from typing import Dict, Any, List
from financial_engine import calculate_npv


def run_simulation(base_data: Dict[str, Any], iterations: int = 50) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation on a single location's financial model.
    
    Args:
        base_data: A single location object from the Atlas containing
                   financial_analysis and crop_analysis data
        iterations: Number of simulation runs (default: 50)
    
    Returns:
        Dictionary with:
        - mean_npv: Average NPV across all simulations
        - VaR_95: Value at Risk (5th percentile worst-case)
        - default_probability: Percentage of runs where NPV < 0
        - simulation_count: Number of iterations run
        - risk_factors: Description of risk factors applied
    """
    # Extract base assumptions
    financial = base_data.get('financial_analysis', {})
    assumptions = financial.get('assumptions', {})
    crop_analysis = base_data.get('crop_analysis', {})
    
    # Base parameters
    base_capex = assumptions.get('capex', 2000.0)
    base_opex = assumptions.get('opex', 425.0)
    base_price = assumptions.get('price_per_ton', 5000.0)
    base_yield_benefit = assumptions.get('yield_benefit_pct', 30.0)
    discount_rate = assumptions.get('discount_rate_pct', 10.0) / 100.0
    analysis_years = assumptions.get('analysis_years', 10)
    
    # Get yield percentages from crop analysis
    base_resilient_yield = crop_analysis.get('resilient_yield_pct', 100.0) / 100.0
    
    # Store NPV results
    npv_results: List[float] = []
    
    # Set seed for reproducibility (but allow different results per location)
    location = base_data.get('location', {})
    seed = int(abs(hash((location.get('lat', 0), location.get('lon', 0)))) % (2**31))
    rng = np.random.default_rng(seed)
    
    for _ in range(iterations):
        # 1. Yield Volatility: Normal variation (mean=base, std_dev=15%)
        yield_multiplier = rng.normal(loc=1.0, scale=0.15)
        yield_multiplier = max(0.1, yield_multiplier)  # Floor at 10% to avoid negative
        stressed_yield = base_resilient_yield * yield_multiplier
        
        # 2. Price Volatility: +/- 10% (uniform distribution for market risk)
        price_multiplier = rng.uniform(0.90, 1.10)
        stressed_price = base_price * price_multiplier
        
        # 3. CAPEX Overruns: +/- 5% (execution risk)
        capex_multiplier = rng.uniform(0.95, 1.05)
        stressed_capex = base_capex * capex_multiplier
        
        # 4. Recalculate annual benefit with stressed parameters
        # Annual benefit = yield_benefit_pct * stressed_yield * price
        # Simplified: benefit scales with yield and price
        stressed_annual_benefit = (base_yield_benefit / 100.0) * stressed_yield * stressed_price
        
        # 5. Generate stressed cash flows
        cash_flows = []
        
        # Year 0: Initial CAPEX (negative)
        cash_flows.append(-stressed_capex)
        
        # Years 1 to N: Net annual cash flow (benefit - opex)
        for year in range(1, analysis_years + 1):
            net_annual = stressed_annual_benefit - base_opex
            cash_flows.append(net_annual)
        
        # 6. Calculate stressed NPV
        npv = calculate_npv(cash_flows, discount_rate)
        npv_results.append(npv)
    
    # Calculate statistics
    npv_array = np.array(npv_results)
    
    mean_npv = float(np.mean(npv_array))
    var_95 = float(np.percentile(npv_array, 5))  # 5th percentile = worst 5% outcomes
    default_count = np.sum(npv_array < 0)
    default_probability = float(default_count / iterations * 100)
    
    return {
        'mean_npv': round(mean_npv, 2),
        'VaR_95': round(var_95, 2),
        'default_probability': round(default_probability, 2),
        'simulation_count': iterations,
        'std_dev_npv': round(float(np.std(npv_array)), 2),
        'min_npv': round(float(np.min(npv_array)), 2),
        'max_npv': round(float(np.max(npv_array)), 2),
        'risk_factors': {
            'yield_volatility_std': '15%',
            'price_volatility_range': '+/- 10%',
            'capex_overrun_range': '+/- 5%'
        }
    }


if __name__ == "__main__":
    # Test with sample data
    sample_location = {
        "location": {"lat": -12.5, "lon": -55.7},
        "crop_analysis": {
            "resilient_yield_pct": 85.57
        },
        "financial_analysis": {
            "npv_usd": 1079668.7,
            "assumptions": {
                "capex": 2000.0,
                "opex": 425.0,
                "yield_benefit_pct": 30.0,
                "price_per_ton": 5000.0,
                "discount_rate_pct": 10.0,
                "analysis_years": 10
            }
        }
    }
    
    result = run_simulation(sample_location, iterations=50)
    print("Monte Carlo Simulation Results:")
    print(f"  Mean NPV: ${result['mean_npv']:,.2f}")
    print(f"  VaR 95%:  ${result['VaR_95']:,.2f}")
    print(f"  Default Probability: {result['default_probability']:.1f}%")
    print(f"  Std Dev NPV: ${result['std_dev_npv']:,.2f}")
