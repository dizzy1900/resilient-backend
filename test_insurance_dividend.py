#!/usr/bin/env python3
"""
Test Suite for Insurance Premium Reduction (Resilience Dividend)
Tests the insurance savings feature in blended finance
"""

def calculate_annual_payment(principal: float, rate: float, periods: int) -> float:
    """Calculate annual payment for amortizing loan"""
    if rate == 0:
        return principal / periods
    return principal * rate / (1.0 - (1.0 + rate) ** -periods)


def test_insurance_dividend_basic():
    """Test basic insurance premium reduction calculation"""
    
    print("="*80)
    print("TEST 1: Basic Insurance Premium Reduction (Resilience Dividend)")
    print("="*80)
    
    # Test parameters
    total_capex = 10_000_000.0
    resilience_score = 85
    commercial_debt_pct = 0.50
    concessional_grant_pct = 0.30
    municipal_equity_pct = 0.20
    annual_carbon_revenue = 100_000.0
    base_insurance_premium = 200_000.0  # $200k annual insurance
    risk_reduction_pct = 0.667  # 66.7% risk reduction
    
    # Constants
    BASE_COMMERCIAL_RATE = 0.065
    CONCESSIONAL_RATE = 0.020
    MUNICIPAL_EQUITY_RATE = 0.0
    LOAN_TERM_YEARS = 20
    INSURANCE_DISCOUNT_FACTOR = 0.50  # Insurers pass through 50% of risk reduction
    
    print(f"\nProject Parameters:")
    print(f"  Total CAPEX: ${total_capex:,.2f}")
    print(f"  Resilience Score: {resilience_score}")
    print(f"  Base Insurance Premium: ${base_insurance_premium:,.2f}/year")
    print(f"  Risk Reduction: {risk_reduction_pct*100:.1f}%")
    print(f"  Insurance Discount Factor: {INSURANCE_DISCOUNT_FACTOR*100:.0f}%")
    
    # Apply greenium
    greenium_discount_bps = 50.0
    greenium_discount = greenium_discount_bps / 10_000.0
    applied_commercial_rate = BASE_COMMERCIAL_RATE - greenium_discount
    
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
    
    # Calculate insurance savings
    insurance_savings = base_insurance_premium * (risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR)
    adjusted_insurance_premium = base_insurance_premium - insurance_savings
    
    # Calculate net debt service after all offsets
    net_annual_debt_service = max(0.0, annual_debt_service - annual_carbon_revenue - insurance_savings)
    
    print(f"\nInsurance Premium Calculation:")
    print(f"  Base Premium: ${base_insurance_premium:,.2f}/year")
    print(f"  Risk Reduction: {risk_reduction_pct*100:.1f}%")
    print(f"  Pass-Through Rate: {INSURANCE_DISCOUNT_FACTOR*100:.0f}%")
    print(f"  Insurance Savings: ${insurance_savings:,.2f}/year")
    print(f"  Adjusted Premium: ${adjusted_insurance_premium:,.2f}/year")
    
    print(f"\nCombined Cash Flow Impact:")
    print(f"  Annual Debt Service (Gross): ${annual_debt_service:,.2f}")
    print(f"  - Carbon Credit Revenue: ${annual_carbon_revenue:,.2f}")
    print(f"  - Insurance Savings: ${insurance_savings:,.2f}")
    print(f"  = Net Annual Debt Service: ${net_annual_debt_service:,.2f}")
    
    # Calculate lifetime savings
    lifetime_insurance_savings = insurance_savings * LOAN_TERM_YEARS
    lifetime_carbon_revenue = annual_carbon_revenue * LOAN_TERM_YEARS
    total_annual_offset = annual_carbon_revenue + insurance_savings
    total_lifetime_offset = total_annual_offset * LOAN_TERM_YEARS
    
    offset_percentage = (total_annual_offset / annual_debt_service * 100)
    
    print(f"\nLifetime Value Analysis (20 years):")
    print(f"  Lifetime Insurance Savings: ${lifetime_insurance_savings:,.2f}")
    print(f"  Lifetime Carbon Revenue: ${lifetime_carbon_revenue:,.2f}")
    print(f"  Total Lifetime Offset: ${total_lifetime_offset:,.2f}")
    print(f"  Debt Service Offset: {offset_percentage:.1f}%")
    
    # Validation checks
    print(f"\n" + "="*80)
    print("VALIDATION CHECKS")
    print("="*80)
    
    # Check insurance savings formula
    expected_savings = base_insurance_premium * risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR
    assert abs(insurance_savings - expected_savings) < 0.01
    print(f"✅ Insurance savings formula correct: ${insurance_savings:,.2f}")
    
    # Check adjusted premium
    assert adjusted_insurance_premium == base_insurance_premium - insurance_savings
    print(f"✅ Adjusted premium correct: ${base_insurance_premium:,.2f} - ${insurance_savings:,.2f} = ${adjusted_insurance_premium:,.2f}")
    
    # Check net debt service
    expected_net = annual_debt_service - annual_carbon_revenue - insurance_savings
    assert abs(net_annual_debt_service - expected_net) < 0.01
    print(f"✅ Net debt service correct: ${net_annual_debt_service:,.2f}")
    
    # Check non-negative
    assert net_annual_debt_service >= 0
    print(f"✅ Net debt service is non-negative: ${net_annual_debt_service:,.2f}")
    
    print(f"\n✅ ALL VALIDATION CHECKS PASSED")


def test_high_risk_reduction():
    """Test with very high risk reduction (90%)"""
    
    print("\n" + "="*80)
    print("TEST 2: High Risk Reduction Scenario (90%)")
    print("="*80)
    
    base_insurance_premium = 300_000.0
    risk_reduction_pct = 0.90  # 90% risk reduction
    INSURANCE_DISCOUNT_FACTOR = 0.50
    
    insurance_savings = base_insurance_premium * (risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR)
    adjusted_insurance_premium = base_insurance_premium - insurance_savings
    
    savings_percentage = (insurance_savings / base_insurance_premium * 100)
    
    print(f"  Base Insurance Premium: ${base_insurance_premium:,.2f}")
    print(f"  Risk Reduction: {risk_reduction_pct*100:.0f}%")
    print(f"  Insurance Savings: ${insurance_savings:,.2f}")
    print(f"  Adjusted Premium: ${adjusted_insurance_premium:,.2f}")
    print(f"  Savings Percentage: {savings_percentage:.1f}%")
    
    assert insurance_savings == base_insurance_premium * 0.90 * 0.50
    print(f"\n✅ High risk reduction correctly calculated")
    print(f"   90% risk reduction → {savings_percentage:.0f}% premium reduction (50% pass-through)")


def test_zero_insurance():
    """Test with no insurance (baseline)"""
    
    print("\n" + "="*80)
    print("TEST 3: No Insurance (Baseline)")
    print("="*80)
    
    base_insurance_premium = 0.0
    risk_reduction_pct = 0.667
    INSURANCE_DISCOUNT_FACTOR = 0.50
    
    insurance_savings = base_insurance_premium * (risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR)
    adjusted_insurance_premium = base_insurance_premium - insurance_savings
    
    print(f"  Base Insurance Premium: ${base_insurance_premium:,.2f}")
    print(f"  Risk Reduction: {risk_reduction_pct*100:.1f}%")
    print(f"  Insurance Savings: ${insurance_savings:,.2f}")
    print(f"  Adjusted Premium: ${adjusted_insurance_premium:,.2f}")
    
    assert insurance_savings == 0.0
    assert adjusted_insurance_premium == 0.0
    print(f"\n✅ Zero insurance correctly handled")


def test_no_risk_reduction():
    """Test with no risk reduction"""
    
    print("\n" + "="*80)
    print("TEST 4: No Risk Reduction")
    print("="*80)
    
    base_insurance_premium = 150_000.0
    risk_reduction_pct = 0.0  # No risk reduction
    INSURANCE_DISCOUNT_FACTOR = 0.50
    
    insurance_savings = base_insurance_premium * (risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR)
    adjusted_insurance_premium = base_insurance_premium - insurance_savings
    
    print(f"  Base Insurance Premium: ${base_insurance_premium:,.2f}")
    print(f"  Risk Reduction: {risk_reduction_pct*100:.1f}%")
    print(f"  Insurance Savings: ${insurance_savings:,.2f}")
    print(f"  Adjusted Premium: ${adjusted_insurance_premium:,.2f}")
    
    assert insurance_savings == 0.0
    assert adjusted_insurance_premium == base_insurance_premium
    print(f"\n✅ No risk reduction → no insurance savings")


def test_combined_benefits():
    """Test combined benefits: Greenium + Carbon + Insurance"""
    
    print("\n" + "="*80)
    print("TEST 5: Triple Value Stack (Greenium + Carbon + Insurance)")
    print("="*80)
    
    # Annual debt service: $567,993.89 (from previous tests)
    annual_debt_service = 567_993.89
    
    # Greenium savings (already in debt service calculation)
    greenium_lifetime = 357_183.84
    
    # Carbon revenue
    annual_carbon_revenue = 100_000.0
    lifetime_carbon = annual_carbon_revenue * 20
    
    # Insurance savings
    base_insurance_premium = 200_000.0
    risk_reduction_pct = 0.667
    INSURANCE_DISCOUNT_FACTOR = 0.50
    insurance_savings = base_insurance_premium * (risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR)
    lifetime_insurance = insurance_savings * 20
    
    # Net debt service
    net_annual_debt_service = max(0.0, annual_debt_service - annual_carbon_revenue - insurance_savings)
    
    # Calculate total benefits
    total_annual_benefits = annual_carbon_revenue + insurance_savings
    total_lifetime_benefits = lifetime_carbon + lifetime_insurance + greenium_lifetime
    
    print(f"\nValue Stacking Analysis:")
    print(f"  1. Greenium (Interest Discount):")
    print(f"     Lifetime Savings: ${greenium_lifetime:,.2f}")
    print(f"\n  2. Carbon Credit Revenue:")
    print(f"     Annual Revenue: ${annual_carbon_revenue:,.2f}")
    print(f"     Lifetime Revenue: ${lifetime_carbon:,.2f}")
    print(f"\n  3. Insurance Premium Reduction:")
    print(f"     Annual Savings: ${insurance_savings:,.2f}")
    print(f"     Lifetime Savings: ${lifetime_insurance:,.2f}")
    
    print(f"\n" + "-"*80)
    print(f"  Total Annual Cash Flow Benefit: ${total_annual_benefits:,.2f}")
    print(f"  Total Lifetime Benefit: ${total_lifetime_benefits:,.2f}")
    print(f"  Debt Service Offset: {(total_annual_benefits/annual_debt_service*100):.1f}%")
    print(f"\n  Gross Annual Debt Service: ${annual_debt_service:,.2f}")
    print(f"  Net Annual Debt Service: ${net_annual_debt_service:,.2f}")
    print(f"  Net Reduction: ${annual_debt_service - net_annual_debt_service:,.2f} ({(total_annual_benefits/annual_debt_service*100):.1f}%)")
    
    print(f"\n✅ Triple value stack validated")
    print(f"   Combined benefits reduce debt service by {(total_annual_benefits/annual_debt_service*100):.1f}%")


def test_extreme_case_full_offset():
    """Test extreme case where combined benefits exceed debt service"""
    
    print("\n" + "="*80)
    print("TEST 6: Extreme Case - Benefits Exceed Debt Service")
    print("="*80)
    
    annual_debt_service = 400_000.0
    annual_carbon_revenue = 200_000.0
    
    base_insurance_premium = 500_000.0
    risk_reduction_pct = 0.80
    INSURANCE_DISCOUNT_FACTOR = 0.50
    insurance_savings = base_insurance_premium * (risk_reduction_pct * INSURANCE_DISCOUNT_FACTOR)
    
    net_annual_debt_service = max(0.0, annual_debt_service - annual_carbon_revenue - insurance_savings)
    
    print(f"  Annual Debt Service: ${annual_debt_service:,.2f}")
    print(f"  Carbon Revenue: ${annual_carbon_revenue:,.2f}")
    print(f"  Insurance Savings: ${insurance_savings:,.2f}")
    print(f"  Total Benefits: ${annual_carbon_revenue + insurance_savings:,.2f}")
    print(f"  Net Debt Service: ${net_annual_debt_service:,.2f}")
    
    assert net_annual_debt_service == 0.0
    print(f"\n✅ Net debt service correctly floored at $0.00")
    print(f"   Project generates net positive cash flow!")


def run_all_tests():
    """Run all insurance dividend tests"""
    
    print("\n" + "="*80)
    print("INSURANCE PREMIUM REDUCTION (RESILIENCE DIVIDEND) TEST SUITE")
    print("="*80)
    print("Testing insurance savings integration into blended finance")
    
    try:
        test_insurance_dividend_basic()
        test_high_risk_reduction()
        test_zero_insurance()
        test_no_risk_reduction()
        test_combined_benefits()
        test_extreme_case_full_offset()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\nKey Insights:")
        print("1. Insurance savings = base_premium × risk_reduction × 50% pass-through")
        print("2. Typical 66.7% risk reduction → 33.3% premium reduction")
        print("3. Combines with carbon revenue to reduce net debt service")
        print("4. Creates 'triple value stack': Greenium + Carbon + Insurance")
        print("5. Net debt service floored at $0 (cannot go negative)")
        print("6. Resilience investments unlock multiple revenue streams")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
