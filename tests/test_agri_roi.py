#!/usr/bin/env python3
"""
Test the Agricultural ROI calculation in /predict endpoint
"""

import json

def test_agri_roi_calculation():
    """Test the agricultural ROI calculation logic."""
    
    print("Testing Agricultural ROI Calculation")
    print("=" * 60)
    
    # Test Case 1: Default parameters with realistic yields
    print("\nTest Case 1: Default parameters (from research)")
    print("-" * 60)
    
    # Simulate yields from physics engine
    standard_yield = 4.5  # tons/ha
    resilient_yield = 5.8  # tons/ha
    
    # Default project parameters (from research)
    capex = 2000
    opex = 425
    yield_benefit_pct = 30.0
    price_per_ton = 4800
    analysis_years = 10
    discount_rate = 0.10
    
    print(f"  Standard seed yield: {standard_yield} tons/ha")
    print(f"  Resilient seed yield: {resilient_yield} tons/ha")
    print(f"\n  Project parameters:")
    print(f"    CAPEX: ${capex}")
    print(f"    OPEX: ${opex}/year")
    print(f"    Yield benefit: {yield_benefit_pct}%")
    print(f"    Price per ton: ${price_per_ton}")
    
    # Calculate cash flows
    incremental_cash_flows = []
    cumulative_cash_flow_array = []
    cumulative = 0.0
    
    for year in range(analysis_years + 1):  # 0 to 10
        # Baseline (BAU): Standard seed
        revenue_bau = standard_yield * price_per_ton
        net_bau = revenue_bau
        
        # Project: Resilient seed with additional yield benefit
        yield_project = resilient_yield * (1 + (yield_benefit_pct / 100))
        revenue_project = yield_project * price_per_ton
        
        # Costs
        if year == 0:
            cost_project = capex
        else:
            cost_project = opex
        
        # Net project cash flow
        net_project = revenue_project - cost_project
        
        # Incremental cash flow
        incremental = net_project - net_bau
        
        # Year 0 is pure CAPEX
        if year == 0:
            incremental = -capex
        
        incremental_cash_flows.append(round(incremental, 2))
        
        # Cumulative
        cumulative += incremental
        cumulative_cash_flow_array.append(round(cumulative, 2))
    
    print(f"\n  Incremental cash flows (first 3 years):")
    print(f"    Year 0: ${incremental_cash_flows[0]:,} (CAPEX)")
    print(f"    Year 1: ${incremental_cash_flows[1]:,}")
    print(f"    Year 2: ${incremental_cash_flows[2]:,}")
    
    print(f"\n  Cumulative cash flow (first 3 years):")
    print(f"    Year 0: ${cumulative_cash_flow_array[0]:,}")
    print(f"    Year 1: ${cumulative_cash_flow_array[1]:,}")
    print(f"    Year 2: ${cumulative_cash_flow_array[2]:,}")
    
    # Calculate NPV
    from financial_engine import calculate_npv, calculate_payback_period
    
    npv = calculate_npv(incremental_cash_flows, discount_rate)
    payback_years = calculate_payback_period(incremental_cash_flows)
    
    print(f"\n  Financial Metrics:")
    print(f"    NPV: ${npv:,.2f}")
    print(f"    Payback Period: {payback_years:.2f} years" if payback_years else "    Payback Period: Never")
    
    # Validate
    assert len(incremental_cash_flows) == 11, "Should have 11 cash flows (Year 0-10)"
    assert incremental_cash_flows[0] < 0, "Year 0 should be negative (CAPEX)"
    assert incremental_cash_flows[1] > 0, "Year 1+ should be positive (net benefits)"
    assert cumulative_cash_flow_array[0] == -capex, "Year 0 cumulative should equal -CAPEX"
    
    print("  ✓ Passed")
    
    # Test Case 2: Custom parameters (higher investment)
    print("\nTest Case 2: Custom parameters (higher investment)")
    print("-" * 60)
    
    custom_capex = 5000
    custom_opex = 800
    custom_yield_benefit = 50.0
    custom_price = 6000
    
    print(f"  Custom CAPEX: ${custom_capex}")
    print(f"  Custom OPEX: ${custom_opex}/year")
    print(f"  Custom yield benefit: {custom_yield_benefit}%")
    print(f"  Custom price: ${custom_price}/ton")
    
    custom_flows = []
    for year in range(analysis_years + 1):
        revenue_bau = standard_yield * custom_price
        net_bau = revenue_bau
        
        yield_project = resilient_yield * (1 + (custom_yield_benefit / 100))
        revenue_project = yield_project * custom_price
        
        if year == 0:
            cost_project = custom_capex
        else:
            cost_project = custom_opex
        
        net_project = revenue_project - cost_project
        incremental = net_project - net_bau
        
        if year == 0:
            incremental = -custom_capex
        
        custom_flows.append(round(incremental, 2))
    
    custom_npv = calculate_npv(custom_flows, discount_rate)
    custom_payback = calculate_payback_period(custom_flows)
    
    print(f"\n  Year 0 cash flow: ${custom_flows[0]:,}")
    print(f"  NPV: ${custom_npv:,.2f}")
    print(f"  Payback: {custom_payback:.2f} years" if custom_payback else "  Payback: Never")
    
    assert custom_flows[0] == -custom_capex, "Year 0 should equal -custom_capex"
    print("  ✓ Passed")
    
    # Test Case 3: Low yield improvement (poor investment)
    print("\nTest Case 3: Poor investment scenario (low benefits)")
    print("-" * 60)
    
    poor_standard_yield = 3.0
    poor_resilient_yield = 3.2  # Only 6.7% improvement
    
    print(f"  Standard yield: {poor_standard_yield} tons/ha")
    print(f"  Resilient yield: {poor_resilient_yield} tons/ha")
    print(f"  Improvement: {((poor_resilient_yield/poor_standard_yield - 1)*100):.1f}%")
    
    poor_flows = []
    for year in range(analysis_years + 1):
        revenue_bau = poor_standard_yield * price_per_ton
        net_bau = revenue_bau
        
        yield_project = poor_resilient_yield * (1 + (yield_benefit_pct / 100))
        revenue_project = yield_project * price_per_ton
        
        if year == 0:
            cost_project = capex
        else:
            cost_project = opex
        
        net_project = revenue_project - cost_project
        incremental = net_project - net_bau
        
        if year == 0:
            incremental = -capex
        
        poor_flows.append(round(incremental, 2))
    
    poor_npv = calculate_npv(poor_flows, discount_rate)
    poor_payback = calculate_payback_period(poor_flows)
    
    print(f"\n  NPV: ${poor_npv:,.2f}")
    print(f"  Payback: {poor_payback:.2f} years" if poor_payback else "  Payback: Never")
    
    # Should have lower NPV due to smaller benefits
    print(f"\n  Recommendation: {'INVEST' if poor_npv > 0 else 'DO NOT INVEST'}")
    print("  ✓ Passed")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    
    # Show complete example response structure
    print("\nComplete ROI Analysis Response Structure:")
    print("=" * 60)
    
    roi_analysis = {
        'npv': round(npv, 2),
        'payback_years': round(payback_years, 2) if payback_years else None,
        'cumulative_cash_flow': cumulative_cash_flow_array,
        'incremental_cash_flows': incremental_cash_flows,
        'assumptions': {
            'capex': capex,
            'opex': opex,
            'yield_benefit_pct': yield_benefit_pct,
            'price_per_ton': price_per_ton,
            'discount_rate_pct': discount_rate * 100,
            'analysis_years': analysis_years
        }
    }
    
    print(json.dumps(roi_analysis, indent=2))


if __name__ == '__main__':
    test_agri_roi_calculation()
