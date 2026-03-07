#!/usr/bin/env python3
"""
Unit test for sensitivity analysis logic (no server required)
"""

def calculate_annual_payment(principal: float, rate: float, periods: int) -> float:
    """Calculate annual payment for amortizing loan: PMT = P * r / (1 - (1+r)^-n)"""
    if rate == 0:
        return principal / periods
    return principal * rate / (1.0 - (1.0 + rate) ** -periods)


def test_sensitivity_analysis_logic():
    """Test the sensitivity analysis calculation logic"""
    
    # Test parameters
    total_capex = 10_000_000.0
    resilience_score = 85
    commercial_debt_pct = 0.50
    concessional_grant_pct = 0.30
    municipal_equity_pct = 0.20
    rate_shock_bps = 100
    
    # Constants
    BASE_COMMERCIAL_RATE = 0.065
    CONCESSIONAL_RATE = 0.020
    MUNICIPAL_EQUITY_RATE = 0.0
    LOAN_TERM_YEARS = 20
    
    # Apply greenium
    greenium_discount_bps = 50.0  # 85 score gets 50 bps
    greenium_discount = greenium_discount_bps / 10_000.0
    applied_commercial_rate = BASE_COMMERCIAL_RATE - greenium_discount
    
    print("="*80)
    print("SENSITIVITY ANALYSIS LOGIC TEST")
    print("="*80)
    print(f"\nInput Parameters:")
    print(f"  Total CAPEX: ${total_capex:,.2f}")
    print(f"  Resilience Score: {resilience_score}")
    print(f"  Commercial Debt: {commercial_debt_pct*100:.0f}%")
    print(f"  Concessional Grant: {concessional_grant_pct*100:.0f}%")
    print(f"  Municipal Equity: {municipal_equity_pct*100:.0f}%")
    print(f"  Rate Shock: +{rate_shock_bps} bps")
    
    # Calculate tranche amounts
    commercial_debt_amount = total_capex * commercial_debt_pct
    concessional_grant_amount = total_capex * concessional_grant_pct
    municipal_equity_amount = total_capex * municipal_equity_pct
    
    print(f"\nTranche Amounts:")
    print(f"  Commercial Debt: ${commercial_debt_amount:,.2f}")
    print(f"  Concessional Grant: ${concessional_grant_amount:,.2f}")
    print(f"  Municipal Equity: ${municipal_equity_amount:,.2f}")
    
    # Calculate base blended rate
    blended_interest_rate = (
        (commercial_debt_pct * applied_commercial_rate) +
        (concessional_grant_pct * CONCESSIONAL_RATE) +
        (municipal_equity_pct * MUNICIPAL_EQUITY_RATE)
    )
    
    print(f"\nBase Case Interest Rates:")
    print(f"  Base Commercial Rate: {BASE_COMMERCIAL_RATE*100:.2f}%")
    print(f"  Applied Commercial Rate (after greenium): {applied_commercial_rate*100:.2f}%")
    print(f"  Concessional Rate: {CONCESSIONAL_RATE*100:.2f}%")
    print(f"  Blended Rate: {blended_interest_rate*100:.2f}%")
    
    # Calculate debt principal
    debt_principal = commercial_debt_amount + concessional_grant_amount
    
    # Calculate base annual debt service
    annual_debt_service = calculate_annual_payment(
        debt_principal, blended_interest_rate, LOAN_TERM_YEARS
    )
    
    print(f"\nBase Case Debt Service:")
    print(f"  Debt Principal: ${debt_principal:,.2f}")
    print(f"  Annual Payment: ${annual_debt_service:,.2f}")
    
    # Apply rate shock
    rate_shock_decimal = rate_shock_bps / 10_000.0
    stressed_commercial_rate = applied_commercial_rate + rate_shock_decimal
    
    # Calculate stressed blended rate
    stressed_blended_rate = (
        (commercial_debt_pct * stressed_commercial_rate) +
        (concessional_grant_pct * CONCESSIONAL_RATE) +
        (municipal_equity_pct * MUNICIPAL_EQUITY_RATE)
    )
    
    # Calculate stressed annual debt service
    stressed_annual_payment = calculate_annual_payment(
        debt_principal, stressed_blended_rate, LOAN_TERM_YEARS
    )
    
    # Calculate deltas
    debt_service_delta = stressed_annual_payment - annual_debt_service
    payment_increase_pct = (debt_service_delta / annual_debt_service * 100)
    lifetime_cost_increase = debt_service_delta * LOAN_TERM_YEARS
    
    print(f"\n" + "="*80)
    print("SENSITIVITY ANALYSIS RESULTS")
    print("="*80)
    print(f"Rate Shock: +{rate_shock_bps} bps (+{rate_shock_decimal*100:.2f}%)")
    print(f"Stressed Commercial Rate: {stressed_commercial_rate*100:.2f}%")
    print(f"Stressed Blended Rate: {stressed_blended_rate*100:.2f}%")
    print(f"\nBase Annual Payment: ${annual_debt_service:,.2f}")
    print(f"Stressed Annual Payment: ${stressed_annual_payment:,.2f}")
    print(f"Debt Service Delta: ${debt_service_delta:,.2f}")
    print(f"Payment Increase: {payment_increase_pct:.2f}%")
    print(f"Lifetime Cost Increase: ${lifetime_cost_increase:,.2f}")
    
    print(f"\n" + "="*80)
    print("VALIDATION CHECKS")
    print("="*80)
    
    # Validation checks
    assert debt_service_delta > 0, "Delta should be positive for positive rate shock"
    assert payment_increase_pct > 0, "Percentage increase should be positive"
    assert stressed_blended_rate > blended_interest_rate, "Stressed rate should be higher"
    
    # Check that rate shock only affects commercial portion
    expected_rate_increase = commercial_debt_pct * rate_shock_decimal
    actual_rate_increase = stressed_blended_rate - blended_interest_rate
    
    print(f"✅ Delta is positive: ${debt_service_delta:,.2f}")
    print(f"✅ Percentage increase is positive: {payment_increase_pct:.2f}%")
    print(f"✅ Stressed rate is higher: {stressed_blended_rate*100:.2f}% > {blended_interest_rate*100:.2f}%")
    print(f"✅ Rate shock affects only commercial portion:")
    print(f"   Expected rate increase: {expected_rate_increase*100:.4f}%")
    print(f"   Actual rate increase: {actual_rate_increase*100:.4f}%")
    
    assert abs(expected_rate_increase - actual_rate_increase) < 0.0001, "Rate increase mismatch"
    
    print(f"\n" + "="*80)
    print("✅ ALL VALIDATION CHECKS PASSED")
    print("="*80)
    
    print(f"\nKey Insights:")
    print(f"1. A {rate_shock_bps} bps shock increases annual payments by {payment_increase_pct:.2f}%")
    print(f"2. Over {LOAN_TERM_YEARS} years, this adds ${lifetime_cost_increase:,.2f} in costs")
    print(f"3. Rate shock only affects the {commercial_debt_pct*100:.0f}% commercial debt portion")
    print(f"4. Concessional and equity tranches provide rate stability")


if __name__ == "__main__":
    test_sensitivity_analysis_logic()
