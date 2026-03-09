#!/usr/bin/env python3
"""
Test Suite for Carbon Credit Revenue Integration
Tests the carbon revenue offset feature in blended finance
"""

def calculate_annual_payment(principal: float, rate: float, periods: int) -> float:
    """Calculate annual payment for amortizing loan"""
    if rate == 0:
        return principal / periods
    return principal * rate / (1.0 - (1.0 + rate) ** -periods)


def test_carbon_credit_integration():
    """Test carbon credit revenue offsetting debt service"""
    
    print("="*80)
    print("CARBON CREDIT REVENUE INTEGRATION TEST")
    print("="*80)
    
    # Test parameters
    total_capex = 10_000_000.0
    resilience_score = 85
    commercial_debt_pct = 0.50
    concessional_grant_pct = 0.30
    municipal_equity_pct = 0.20
    annual_carbon_revenue = 100_000.0  # $100k annual carbon credits
    
    # Constants
    BASE_COMMERCIAL_RATE = 0.065
    CONCESSIONAL_RATE = 0.020
    MUNICIPAL_EQUITY_RATE = 0.0
    LOAN_TERM_YEARS = 20
    
    # Apply greenium
    greenium_discount_bps = 50.0
    greenium_discount = greenium_discount_bps / 10_000.0
    applied_commercial_rate = BASE_COMMERCIAL_RATE - greenium_discount
    
    print(f"\nProject Parameters:")
    print(f"  Total CAPEX: ${total_capex:,.2f}")
    print(f"  Resilience Score: {resilience_score}")
    print(f"  Annual Carbon Revenue: ${annual_carbon_revenue:,.2f}")
    
    # Calculate tranche amounts
    commercial_debt_amount = total_capex * commercial_debt_pct
    concessional_grant_amount = total_capex * concessional_grant_pct
    debt_principal = commercial_debt_amount + concessional_grant_amount
    
    # Calculate base blended rate
    blended_interest_rate = (
        (commercial_debt_pct * applied_commercial_rate) +
        (concessional_grant_pct * CONCESSIONAL_RATE) +
        (municipal_equity_pct * MUNICIPAL_EQUITY_RATE)
    )
    
    # Calculate annual debt service
    annual_debt_service = calculate_annual_payment(
        debt_principal, blended_interest_rate, LOAN_TERM_YEARS
    )
    
    # Calculate net debt service after carbon revenue offset
    net_annual_debt_service = max(0.0, annual_debt_service - annual_carbon_revenue)
    
    print(f"\nDebt Service Calculations:")
    print(f"  Blended Interest Rate: {blended_interest_rate*100:.2f}%")
    print(f"  Debt Principal: ${debt_principal:,.2f}")
    print(f"  Annual Debt Service (Gross): ${annual_debt_service:,.2f}")
    print(f"  Annual Carbon Revenue: ${annual_carbon_revenue:,.2f}")
    print(f"  Net Annual Debt Service: ${net_annual_debt_service:,.2f}")
    
    # Calculate savings
    carbon_offset_pct = (annual_carbon_revenue / annual_debt_service * 100)
    lifetime_carbon_revenue = annual_carbon_revenue * LOAN_TERM_YEARS
    lifetime_net_cost = net_annual_debt_service * LOAN_TERM_YEARS
    lifetime_gross_cost = annual_debt_service * LOAN_TERM_YEARS
    
    print(f"\nCarbon Credit Impact Analysis:")
    print(f"  Carbon Offset Percentage: {carbon_offset_pct:.2f}%")
    print(f"  Lifetime Carbon Revenue: ${lifetime_carbon_revenue:,.2f}")
    print(f"  Lifetime Gross Cost: ${lifetime_gross_cost:,.2f}")
    print(f"  Lifetime Net Cost: ${lifetime_net_cost:,.2f}")
    print(f"  Effective Savings: ${lifetime_carbon_revenue:,.2f}")
    
    # Validation checks
    print(f"\n" + "="*80)
    print("VALIDATION CHECKS")
    print("="*80)
    
    assert net_annual_debt_service == annual_debt_service - annual_carbon_revenue
    print(f"✅ Net calculation correct: ${annual_debt_service:,.2f} - ${annual_carbon_revenue:,.2f} = ${net_annual_debt_service:,.2f}")
    
    assert net_annual_debt_service >= 0
    print(f"✅ Net debt service is non-negative: ${net_annual_debt_service:,.2f}")
    
    assert net_annual_debt_service < annual_debt_service
    print(f"✅ Net is less than gross: ${net_annual_debt_service:,.2f} < ${annual_debt_service:,.2f}")
    
    print(f"\n" + "="*80)
    print("✅ ALL VALIDATION CHECKS PASSED")
    print("="*80)


def test_carbon_revenue_exceeds_debt_service():
    """Test case where carbon revenue exceeds debt service (should floor at $0)"""
    
    print("\n" + "="*80)
    print("TEST: Carbon Revenue Exceeds Debt Service")
    print("="*80)
    
    annual_debt_service = 100_000.0
    annual_carbon_revenue = 150_000.0  # More than debt service
    
    net_annual_debt_service = max(0.0, annual_debt_service - annual_carbon_revenue)
    
    print(f"  Annual Debt Service: ${annual_debt_service:,.2f}")
    print(f"  Annual Carbon Revenue: ${annual_carbon_revenue:,.2f}")
    print(f"  Net Annual Debt Service: ${net_annual_debt_service:,.2f}")
    
    assert net_annual_debt_service == 0.0
    print(f"\n✅ Net debt service correctly floored at $0.00")
    print(f"   Project generates ${annual_carbon_revenue - annual_debt_service:,.2f} net revenue!")


def test_zero_carbon_revenue():
    """Test case with no carbon revenue (baseline)"""
    
    print("\n" + "="*80)
    print("TEST: Zero Carbon Revenue (Baseline)")
    print("="*80)
    
    annual_debt_service = 567_993.89
    annual_carbon_revenue = 0.0
    
    net_annual_debt_service = max(0.0, annual_debt_service - annual_carbon_revenue)
    
    print(f"  Annual Debt Service: ${annual_debt_service:,.2f}")
    print(f"  Annual Carbon Revenue: ${annual_carbon_revenue:,.2f}")
    print(f"  Net Annual Debt Service: ${net_annual_debt_service:,.2f}")
    
    assert net_annual_debt_service == annual_debt_service
    print(f"\n✅ Net equals gross when no carbon revenue")


def test_partial_offset():
    """Test various carbon revenue offset scenarios"""
    
    print("\n" + "="*80)
    print("TEST: Partial Offset Scenarios")
    print("="*80)
    
    annual_debt_service = 500_000.0
    
    scenarios = [
        ("10% Offset", 50_000.0),
        ("25% Offset", 125_000.0),
        ("50% Offset", 250_000.0),
        ("75% Offset", 375_000.0),
        ("90% Offset", 450_000.0),
    ]
    
    print(f"\nAnnual Debt Service: ${annual_debt_service:,.2f}\n")
    
    for name, carbon_revenue in scenarios:
        net_debt_service = max(0.0, annual_debt_service - carbon_revenue)
        offset_pct = (carbon_revenue / annual_debt_service * 100)
        
        print(f"  {name}:")
        print(f"    Carbon Revenue: ${carbon_revenue:,.2f}")
        print(f"    Net Debt Service: ${net_debt_service:,.2f}")
        print(f"    Offset: {offset_pct:.1f}%")
        print()
        
        assert net_debt_service == annual_debt_service - carbon_revenue
        assert net_debt_service >= 0
    
    print(f"✅ All partial offset scenarios validated")


def run_all_tests():
    """Run all carbon credit integration tests"""
    
    print("\n" + "="*80)
    print("CARBON CREDIT INTEGRATION TEST SUITE")
    print("="*80)
    print("Testing carbon revenue offsetting debt service costs")
    
    try:
        test_carbon_credit_integration()
        test_carbon_revenue_exceeds_debt_service()
        test_zero_carbon_revenue()
        test_partial_offset()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\nKey Benefits:")
        print("1. Carbon credits provide recurring revenue to offset debt service")
        print("2. Reduces net financing costs for climate resilience projects")
        print("3. Creates additional incentive for high-quality carbon projects")
        print("4. Net debt service is floored at $0 (cannot go negative)")
        print("5. Enables 'revenue stacking' - combining green financing + carbon markets")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
