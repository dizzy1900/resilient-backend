#!/usr/bin/env python3
"""
Simple Test Suite for Blended Finance Structuring Logic
========================================================

Tests the calculation logic without importing the full API module.
"""


def calculate_blended_finance(total_capex, resilience_score, commercial_pct, concessional_pct, equity_pct):
    """Calculate blended finance metrics."""
    
    # Validate tranches sum to 1.0
    tranches_sum = commercial_pct + concessional_pct + equity_pct
    if not (0.99 <= tranches_sum <= 1.01):
        raise ValueError(f"Tranches must sum to 1.0. Current sum: {tranches_sum:.4f}")
    
    # Base rates
    BASE_COMMERCIAL_RATE = 0.065  # 6.5%
    CONCESSIONAL_RATE = 0.020     # 2.0%
    MUNICIPAL_EQUITY_RATE = 0.0   # 0.0%
    LOAN_TERM_YEARS = 20
    
    # Apply Greenium discount
    greenium_discount_bps = 0.0
    if resilience_score >= 80:
        greenium_discount_bps = 50.0
    elif resilience_score >= 60:
        greenium_discount_bps = 25.0
    
    greenium_discount = greenium_discount_bps / 10_000.0
    applied_commercial_rate = BASE_COMMERCIAL_RATE - greenium_discount
    
    # Calculate tranche amounts
    commercial_debt_amount = total_capex * commercial_pct
    concessional_grant_amount = total_capex * concessional_pct
    municipal_equity_amount = total_capex * equity_pct
    
    # Calculate blended rate
    blended_rate = (
        commercial_pct * applied_commercial_rate +
        concessional_pct * CONCESSIONAL_RATE +
        equity_pct * MUNICIPAL_EQUITY_RATE
    )
    
    # Debt principal (excludes equity)
    debt_principal = commercial_debt_amount + concessional_grant_amount
    
    # Calculate annual payment
    def calc_payment(principal, rate, periods):
        if rate == 0:
            return principal / periods
        return principal * rate / (1.0 - (1.0 + rate) ** -periods)
    
    annual_debt_service = calc_payment(debt_principal, blended_rate, LOAN_TERM_YEARS)
    
    # Calculate greenium savings
    if commercial_debt_amount > 0:
        base_payment = calc_payment(commercial_debt_amount, BASE_COMMERCIAL_RATE, LOAN_TERM_YEARS)
        discounted_payment = calc_payment(commercial_debt_amount, applied_commercial_rate, LOAN_TERM_YEARS)
        annual_savings = base_payment - discounted_payment
        total_greenium_savings = annual_savings * LOAN_TERM_YEARS
    else:
        total_greenium_savings = 0.0
    
    return {
        "commercial_debt_amount": commercial_debt_amount,
        "concessional_grant_amount": concessional_grant_amount,
        "municipal_equity_amount": municipal_equity_amount,
        "base_commercial_rate": BASE_COMMERCIAL_RATE,
        "applied_commercial_rate": applied_commercial_rate,
        "concessional_rate": CONCESSIONAL_RATE,
        "greenium_discount_bps": greenium_discount_bps,
        "blended_interest_rate": blended_rate,
        "annual_debt_service": annual_debt_service,
        "total_greenium_savings": total_greenium_savings,
        "debt_principal": debt_principal
    }


def test_high_resilience():
    """Test high resilience score (85) - 50 bps discount."""
    print("\n" + "="*80)
    print("TEST 1: High Resilience Score (85) - 50 bps discount")
    print("="*80)
    
    result = calculate_blended_finance(
        total_capex=10_000_000.0,
        resilience_score=85,
        commercial_pct=0.50,
        concessional_pct=0.30,
        equity_pct=0.20
    )
    
    print(f"Input:")
    print(f"  Total CAPEX: $10,000,000")
    print(f"  Resilience Score: 85")
    print(f"  Tranches: 50% Commercial / 30% Concessional / 20% Equity")
    print()
    print(f"Tranche Amounts:")
    print(f"  Commercial Debt: ${result['commercial_debt_amount']:,.2f}")
    print(f"  Concessional Grant: ${result['concessional_grant_amount']:,.2f}")
    print(f"  Municipal Equity: ${result['municipal_equity_amount']:,.2f}")
    print()
    print(f"Interest Rates:")
    print(f"  Base Commercial Rate: {result['base_commercial_rate']*100:.2f}%")
    print(f"  Applied Commercial Rate: {result['applied_commercial_rate']*100:.2f}% (after {result['greenium_discount_bps']:.0f} bps discount)")
    print(f"  Concessional Rate: {result['concessional_rate']*100:.2f}%")
    print(f"  Blended Rate: {result['blended_interest_rate']*100:.4f}%")
    print()
    print(f"Financial Metrics:")
    print(f"  Debt Principal: ${result['debt_principal']:,.2f}")
    print(f"  Annual Debt Service: ${result['annual_debt_service']:,.2f}")
    print(f"  Total Greenium Savings (20 years): ${result['total_greenium_savings']:,.2f}")
    
    # Assertions
    assert result['greenium_discount_bps'] == 50.0, "Expected 50 bps discount"
    assert abs(result['applied_commercial_rate'] - 0.060) < 0.0001, "Expected 6.0% applied rate"
    assert result['debt_principal'] == 8_000_000.0, "Expected $8M debt principal"
    print("\n✅ All assertions passed")


def test_medium_resilience():
    """Test medium resilience score (65) - 25 bps discount."""
    print("\n" + "="*80)
    print("TEST 2: Medium Resilience Score (65) - 25 bps discount")
    print("="*80)
    
    result = calculate_blended_finance(
        total_capex=5_000_000.0,
        resilience_score=65,
        commercial_pct=0.60,
        concessional_pct=0.25,
        equity_pct=0.15
    )
    
    print(f"Input:")
    print(f"  Total CAPEX: $5,000,000")
    print(f"  Resilience Score: 65")
    print(f"  Tranches: 60% Commercial / 25% Concessional / 15% Equity")
    print()
    print(f"Interest Rates:")
    print(f"  Applied Commercial Rate: {result['applied_commercial_rate']*100:.2f}% (after {result['greenium_discount_bps']:.0f} bps discount)")
    print(f"  Blended Rate: {result['blended_interest_rate']*100:.4f}%")
    print()
    print(f"Financial Metrics:")
    print(f"  Annual Debt Service: ${result['annual_debt_service']:,.2f}")
    print(f"  Total Greenium Savings: ${result['total_greenium_savings']:,.2f}")
    
    # Assertions
    assert result['greenium_discount_bps'] == 25.0, "Expected 25 bps discount"
    assert abs(result['applied_commercial_rate'] - 0.0625) < 0.0001, "Expected 6.25% applied rate"
    print("\n✅ All assertions passed")


def test_low_resilience():
    """Test low resilience score (45) - No discount."""
    print("\n" + "="*80)
    print("TEST 3: Low Resilience Score (45) - No discount")
    print("="*80)
    
    result = calculate_blended_finance(
        total_capex=3_000_000.0,
        resilience_score=45,
        commercial_pct=0.70,
        concessional_pct=0.20,
        equity_pct=0.10
    )
    
    print(f"Input:")
    print(f"  Total CAPEX: $3,000,000")
    print(f"  Resilience Score: 45")
    print(f"  Tranches: 70% Commercial / 20% Concessional / 10% Equity")
    print()
    print(f"Interest Rates:")
    print(f"  Applied Commercial Rate: {result['applied_commercial_rate']*100:.2f}% (no discount)")
    print(f"  Blended Rate: {result['blended_interest_rate']*100:.4f}%")
    print()
    print(f"Financial Metrics:")
    print(f"  Annual Debt Service: ${result['annual_debt_service']:,.2f}")
    print(f"  Total Greenium Savings: ${result['total_greenium_savings']:,.2f}")
    
    # Assertions
    assert result['greenium_discount_bps'] == 0.0, "Expected no discount"
    assert result['applied_commercial_rate'] == 0.065, "Expected base 6.5% rate"
    assert result['total_greenium_savings'] == 0.0, "Expected zero savings"
    print("\n✅ All assertions passed")


def test_invalid_tranches():
    """Test invalid tranches (don't sum to 1.0)."""
    print("\n" + "="*80)
    print("TEST 4: Invalid Tranches (sum != 1.0)")
    print("="*80)
    
    try:
        calculate_blended_finance(
            total_capex=10_000_000.0,
            resilience_score=80,
            commercial_pct=0.50,
            concessional_pct=0.30,
            equity_pct=0.30  # Sum = 1.10
        )
        print("❌ Should have raised ValueError")
    except ValueError as e:
        print(f"✅ Correctly rejected: {e}")


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*80)
    print("TEST 5: Edge Cases")
    print("="*80)
    
    # Test 5a: 100% equity (no debt)
    print("\n5a. 100% Equity (no debt):")
    result = calculate_blended_finance(
        total_capex=1_000_000.0,
        resilience_score=90,
        commercial_pct=0.0,
        concessional_pct=0.0,
        equity_pct=1.0
    )
    print(f"  Debt Principal: ${result['debt_principal']:,.2f}")
    print(f"  Annual Debt Service: ${result['annual_debt_service']:,.2f}")
    print(f"  Greenium Savings: ${result['total_greenium_savings']:,.2f}")
    assert result['debt_principal'] == 0.0, "Expected zero debt"
    assert result['annual_debt_service'] == 0.0, "Expected zero debt service"
    assert result['total_greenium_savings'] == 0.0, "Expected zero savings"
    print("  ✅ Passed")
    
    # Test 5b: Resilience score exactly 80
    print("\n5b. Resilience Score = 80 (boundary):")
    result = calculate_blended_finance(
        total_capex=1_000_000.0,
        resilience_score=80,
        commercial_pct=0.50,
        concessional_pct=0.30,
        equity_pct=0.20
    )
    assert result['greenium_discount_bps'] == 50.0, "Expected 50 bps at threshold"
    print(f"  Greenium Discount: {result['greenium_discount_bps']:.0f} bps")
    print("  ✅ Passed")
    
    # Test 5c: Resilience score exactly 60
    print("\n5c. Resilience Score = 60 (boundary):")
    result = calculate_blended_finance(
        total_capex=1_000_000.0,
        resilience_score=60,
        commercial_pct=0.50,
        concessional_pct=0.30,
        equity_pct=0.20
    )
    assert result['greenium_discount_bps'] == 25.0, "Expected 25 bps at threshold"
    print(f"  Greenium Discount: {result['greenium_discount_bps']:.0f} bps")
    print("  ✅ Passed")


def generate_sample_payloads():
    """Generate sample JSON payloads for API testing."""
    print("\n" + "="*80)
    print("SAMPLE API PAYLOADS")
    print("="*80)
    
    import json
    
    payloads = [
        {
            "name": "High Resilience (85)",
            "payload": {
                "total_capex": 10000000.0,
                "resilience_score": 85,
                "tranches": {
                    "commercial_debt_pct": 0.50,
                    "concessional_grant_pct": 0.30,
                    "municipal_equity_pct": 0.20
                }
            }
        },
        {
            "name": "Medium Resilience (65)",
            "payload": {
                "total_capex": 5000000.0,
                "resilience_score": 65,
                "tranches": {
                    "commercial_debt_pct": 0.60,
                    "concessional_grant_pct": 0.25,
                    "municipal_equity_pct": 0.15
                }
            }
        },
        {
            "name": "Low Resilience (45)",
            "payload": {
                "total_capex": 3000000.0,
                "resilience_score": 45,
                "tranches": {
                    "commercial_debt_pct": 0.70,
                    "concessional_grant_pct": 0.20,
                    "municipal_equity_pct": 0.10
                }
            }
        }
    ]
    
    for item in payloads:
        print(f"\n{item['name']}:")
        print("```json")
        print(json.dumps(item['payload'], indent=2))
        print("```")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("BLENDED FINANCE STRUCTURING - LOGIC TESTS")
    print("="*80)
    
    try:
        test_high_resilience()
        test_medium_resilience()
        test_low_resilience()
        test_invalid_tranches()
        test_edge_cases()
        generate_sample_payloads()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
