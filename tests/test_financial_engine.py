#!/usr/bin/env python3
"""
Test script for financial_engine.py
"""

from financial_engine import calculate_npv, calculate_bcr, calculate_payback_period, calculate_roi_metrics

print("Testing Financial Engine")
print("=" * 60)

# Test Case 1: Simple Investment Example
print("\nTest Case 1: Simple Investment ($100k initial, $15k annual benefit, 20 years)")
print("-" * 60)

# 20 years of benefits to ensure positive NPV
cash_flows = [-100000] + [15000] * 20
discount_rate = 0.10

npv = calculate_npv(cash_flows, discount_rate)
bcr = calculate_bcr(cash_flows, discount_rate)
payback = calculate_payback_period(cash_flows)

print(f"  Cash flows: {cash_flows[:3]}... (21 years total)")
print(f"  Discount rate: {discount_rate*100}%")
print(f"\n  NPV: ${npv:,.2f}")
print(f"  BCR: {bcr:.2f}")
print(f"  Payback Period: {payback:.2f} years")

# Verify NPV calculation manually for first few years
# Year 0: -100000 / 1.0 = -100000
# Year 1: 15000 / 1.1 = 13636.36
# Year 2: 15000 / 1.21 = 12396.69
print(f"\n  Manual verification:")
print(f"    Year 0 PV: ${-100000 / (1.1**0):,.2f}")
print(f"    Year 1 PV: ${15000 / (1.1**1):,.2f}")
print(f"    Year 2 PV: ${15000 / (1.1**2):,.2f}")

assert npv > 0, "NPV should be positive for this investment"
assert bcr > 1, "BCR should be greater than 1 for a good investment"
assert payback is not None and payback < 21, "Should pay back within analysis period"
print("  ✓ Passed")

# Test Case 2: Calculate using helper function
print("\nTest Case 2: Using calculate_roi_metrics")
print("-" * 60)

metrics = calculate_roi_metrics(cash_flows, discount_rate)
print(f"  Metrics returned:")
print(f"    NPV: ${metrics['npv']:,.2f}")
print(f"    BCR: {metrics['bcr']:.2f}")
print(f"    Payback: {metrics['payback_period_years']} years")

assert 'npv' in metrics, "Missing NPV"
assert 'bcr' in metrics, "Missing BCR"
assert 'payback_period_years' in metrics, "Missing payback_period_years"
print("  ✓ Passed")

# Test Case 3: Negative NPV Example
print("\nTest Case 3: Poor Investment (negative NPV)")
print("-" * 60)

poor_cash_flows = [-100000, 5000, 5000, 5000, 5000, 5000]
poor_metrics = calculate_roi_metrics(poor_cash_flows, 0.10)

print(f"  Cash flows: {poor_cash_flows}")
print(f"  NPV: ${poor_metrics['npv']:,.2f}")
print(f"  BCR: {poor_metrics['bcr']:.2f}")
print(f"  Payback: {poor_metrics['payback_period_years']} years")

assert poor_metrics['npv'] < 0, "NPV should be negative for poor investment"
assert poor_metrics['bcr'] < 1, "BCR should be less than 1 for poor investment"
print("  ✓ Passed")

# Test Case 4: Payback Period Calculation
print("\nTest Case 4: Payback Period Edge Cases")
print("-" * 60)

# Quick payback
quick_payback = [-100, 60, 60]
quick_period = calculate_payback_period(quick_payback)
print(f"  Quick payback: {quick_payback}")
print(f"  Payback period: {quick_period:.2f} years")
assert quick_period < 2, "Should pay back in less than 2 years"

# Never pays back
no_payback = [-100, 10, 10, 10]
no_period = calculate_payback_period(no_payback)
print(f"\n  No payback: {no_payback}")
print(f"  Payback period: {no_period}")
assert no_period is None, "Should return None when never pays back"

# Immediate payback (Year 0 positive)
immediate = [100, 50, 50]
immediate_period = calculate_payback_period(immediate)
print(f"\n  Immediate payback: {immediate}")
print(f"  Payback period: {immediate_period} years")
assert immediate_period == 0.0, "Should return 0 for immediate payback"

print("  ✓ All edge cases passed")

# Test Case 5: BCR Calculation
print("\nTest Case 5: BCR Calculation Verification")
print("-" * 60)

# Simple case: 100k cost, 150k benefits (PV)
test_flows = [-100000, 50000, 50000, 50000]
test_bcr = calculate_bcr(test_flows, 0.10)

# Manual calculation:
# PV Costs = 100000
# PV Benefits = 50000/1.1 + 50000/1.21 + 50000/1.331
#             = 45454.55 + 41322.31 + 37565.74 = 124342.60
# BCR = 124342.60 / 100000 = 1.24

print(f"  Cash flows: {test_flows}")
print(f"  BCR: {test_bcr:.2f}")
print(f"  Expected: ~1.24")
assert abs(test_bcr - 1.24) < 0.01, f"BCR should be ~1.24, got {test_bcr}"
print("  ✓ Passed")

# Test Case 6: Fractional Payback Period
print("\nTest Case 6: Fractional Payback Period")
print("-" * 60)

# Should pay back somewhere in year 2
fractional_flows = [-100, 40, 40, 40]
fractional_payback = calculate_payback_period(fractional_flows)

print(f"  Cash flows: {fractional_flows}")
print(f"  Cumulative at Year 0: ${-100}")
print(f"  Cumulative at Year 1: ${-100 + 40}")
print(f"  Cumulative at Year 2: ${-100 + 40 + 40}")
print(f"  Payback period: {fractional_payback:.2f} years")

# After year 1: cumulative = -60
# Need 60 more, get 40 in year 2
# Fraction = 60/40 = 1.5
# Payback = 1 + 1.5 = 2.5 years
expected = 2.5
assert abs(fractional_payback - expected) < 0.01, f"Expected {expected}, got {fractional_payback}"
print("  ✓ Passed")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)

# Show example usage
print("\nExample Usage:")
print("-" * 60)

example_cash_flows = [-100000, 15000, 15000, 15000, 15000, 15000]
example_rate = 0.10

example_metrics = calculate_roi_metrics(example_cash_flows, example_rate)

print(f"Investment: ${example_cash_flows[0]:,}")
print(f"Annual benefit: ${example_cash_flows[1]:,} for {len(example_cash_flows)-1} years")
print(f"Discount rate: {example_rate*100}%")
print(f"\nFinancial Metrics:")
print(f"  NPV: ${example_metrics['npv']:,}")
print(f"  BCR: {example_metrics['bcr']}")
print(f"  Payback: {example_metrics['payback_period_years']} years")

if example_metrics['npv'] > 0:
    print(f"\n✓ Recommendation: INVEST (positive NPV)")
else:
    print(f"\n✗ Recommendation: DO NOT INVEST (negative NPV)")
