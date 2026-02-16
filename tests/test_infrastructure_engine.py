#!/usr/bin/env python3
"""
Test the infrastructure_engine.py functions
"""

from infrastructure_engine import (
    calculate_damage_cost,
    calculate_business_interruption,
    calculate_intervention_depth,
    calculate_infrastructure_roi
)

print("Testing Infrastructure Engine")
print("=" * 60)

# Test Case 1: Damage cost at anchor points
print("\nTest Case 1: Damage cost at depth-damage curve anchor points")
print("-" * 60)

asset_value = 1_000_000  # $1M asset

anchor_tests = [
    (0.0, 0.0),
    (0.5, 18.0),
    (1.0, 29.0),
    (2.0, 49.0),
    (3.0, 60.0)
]

for depth, expected_pct in anchor_tests:
    damage = calculate_damage_cost(depth, asset_value)
    expected_damage = (expected_pct / 100) * asset_value
    print(f"  Depth {depth}m: ${damage:,.0f} ({expected_pct}%)")
    assert abs(damage - expected_damage) < 1.0, f"Expected {expected_damage}, got {damage}"

print("  ✓ All anchor points correct")

# Test Case 2: Interpolation between anchor points
print("\nTest Case 2: Linear interpolation between anchor points")
print("-" * 60)

# Test 0.75m (between 0.5m=18% and 1.0m=29%)
depth_test = 0.75
damage_test = calculate_damage_cost(depth_test, asset_value)
# Expected: 18% + (0.25/0.5) * (29-18) = 18 + 5.5 = 23.5%
expected_pct = 23.5
expected_damage = (expected_pct / 100) * asset_value

print(f"  Depth {depth_test}m: ${damage_test:,.0f}")
print(f"  Expected: ${expected_damage:,.0f} ({expected_pct}%)")
assert abs(damage_test - expected_damage) < 100, "Interpolation failed"
print("  ✓ Interpolation correct")

# Test Case 3: Damage above maximum depth
print("\nTest Case 3: Damage cost above maximum depth (>3m)")
print("-" * 60)

depth_extreme = 5.0
damage_extreme = calculate_damage_cost(depth_extreme, asset_value)
max_damage = (60.0 / 100) * asset_value  # Caps at 60%

print(f"  Depth {depth_extreme}m: ${damage_extreme:,.0f}")
print(f"  Maximum damage: ${max_damage:,.0f} (60%)")
assert damage_extreme == max_damage, "Should cap at maximum damage"
print("  ✓ Correctly caps at maximum")

# Test Case 4: Business interruption
print("\nTest Case 4: Business interruption calculation")
print("-" * 60)

daily_revenue = 50_000

# No interruption (below threshold)
depth_low = 0.2
interruption_low = calculate_business_interruption(depth_low, daily_revenue)
print(f"  Depth {depth_low}m (below 0.3m threshold): ${interruption_low:,.0f}")
assert interruption_low == 0.0, "Should be no interruption below threshold"

# With interruption (above threshold)
depth_high = 0.5
interruption_high = calculate_business_interruption(depth_high, daily_revenue)
expected_interruption = 5 * daily_revenue  # 5 days downtime
print(f"  Depth {depth_high}m (above 0.3m threshold): ${interruption_high:,.0f}")
print(f"  Expected (5 days × ${daily_revenue:,}): ${expected_interruption:,.0f}")
assert interruption_high == expected_interruption, "Should calculate 5 days downtime"
print("  ✓ Business interruption correct")

# Test Case 5: Intervention depth - sea wall
print("\nTest Case 5: Sea wall intervention depth")
print("-" * 60)

original_depth = 2.5
wall_height = 2.0

effective_depth_wall = calculate_intervention_depth(original_depth, 'sea_wall', wall_height_m=wall_height)
expected_effective = max(0.0, original_depth - wall_height)

print(f"  Original flood depth: {original_depth}m")
print(f"  Sea wall height: {wall_height}m")
print(f"  Effective depth: {effective_depth_wall}m")
print(f"  Expected: {expected_effective}m")
assert effective_depth_wall == expected_effective, "Sea wall calculation wrong"
print("  ✓ Sea wall reduces depth correctly")

# Test Case 6: Intervention depth - drainage
print("\nTest Case 6: Drainage intervention depth")
print("-" * 60)

original_depth_2 = 0.8
drainage_reduction = 0.3

effective_depth_drainage = calculate_intervention_depth(original_depth_2, 'drainage', drainage_reduction_m=drainage_reduction)
expected_effective_2 = max(0.0, original_depth_2 - drainage_reduction)

print(f"  Original flood depth: {original_depth_2}m")
print(f"  Drainage reduction: {drainage_reduction}m")
print(f"  Effective depth: {effective_depth_drainage}m")
print(f"  Expected: {expected_effective_2}m")
assert effective_depth_drainage == expected_effective_2, "Drainage calculation wrong"
print("  ✓ Drainage reduces depth correctly")

# Test Case 7: Complete infrastructure ROI - sea wall
print("\nTest Case 7: Complete infrastructure ROI - sea wall investment")
print("-" * 60)

flood_depth = 1.5  # 1.5m flood
asset_value_roi = 5_000_000  # $5M asset
daily_revenue_roi = 100_000  # $100k daily revenue
capex = 500_000  # $500k initial investment
opex = 25_000  # $25k annual maintenance

roi_result = calculate_infrastructure_roi(
    flood_depth_m=flood_depth,
    asset_value=asset_value_roi,
    daily_revenue=daily_revenue_roi,
    project_capex=capex,
    project_opex=opex,
    intervention_type='sea_wall',
    analysis_years=20,
    discount_rate=0.10,
    wall_height_m=2.0
)

print(f"  Scenario: {flood_depth}m flood, ${asset_value_roi:,} asset")
print(f"\n  Baseline (No protection):")
print(f"    Asset damage: ${roi_result['baseline_scenario']['asset_damage']:,.0f}")
print(f"    Business interruption: ${roi_result['baseline_scenario']['business_interruption']:,.0f}")
print(f"    Total annual loss: ${roi_result['baseline_scenario']['total_annual_loss']:,.0f}")

print(f"\n  With Sea Wall (2.0m):")
print(f"    Effective depth: {roi_result['intervention_scenario']['effective_flood_depth_m']}m")
print(f"    Asset damage: ${roi_result['intervention_scenario']['asset_damage']:,.0f}")
print(f"    Business interruption: ${roi_result['intervention_scenario']['business_interruption']:,.0f}")
print(f"    Total annual loss: ${roi_result['intervention_scenario']['total_annual_loss']:,.0f}")

print(f"\n  Financial Analysis:")
print(f"    Annual avoided loss: ${roi_result['financial_analysis']['annual_avoided_loss']:,.0f}")
print(f"    CAPEX: ${roi_result['financial_analysis']['project_capex']:,.0f}")
print(f"    OPEX: ${roi_result['financial_analysis']['project_opex']:,.0f}/year")
print(f"    NPV (20 years): ${roi_result['financial_analysis']['npv']:,.0f}")
print(f"    BCR: {roi_result['financial_analysis']['bcr']:.2f}")
print(f"    Payback: {roi_result['financial_analysis']['payback_years']:.2f} years")

print(f"\n  Recommendation: {'INVEST' if roi_result['recommendation']['invest'] else 'DO NOT INVEST'}")
print(f"  Reason: {roi_result['recommendation']['reason']}")

assert 'npv' in roi_result['financial_analysis'], "Missing NPV"
assert 'bcr' in roi_result['financial_analysis'], "Missing BCR"
print("\n  ✓ Complete ROI calculation successful")

# Test Case 8: Drainage system ROI
print("\nTest Case 8: Drainage system ROI")
print("-" * 60)

flood_depth_drain = 0.6  # 0.6m flood (flash flood)
asset_value_drain = 2_000_000
daily_revenue_drain = 40_000
capex_drain = 150_000
opex_drain = 10_000

roi_drainage = calculate_infrastructure_roi(
    flood_depth_m=flood_depth_drain,
    asset_value=asset_value_drain,
    daily_revenue=daily_revenue_drain,
    project_capex=capex_drain,
    project_opex=opex_drain,
    intervention_type='drainage',
    analysis_years=15,
    discount_rate=0.10,
    drainage_reduction_m=0.3
)

print(f"  Scenario: {flood_depth_drain}m flash flood, ${asset_value_drain:,} asset")
print(f"\n  Baseline total loss: ${roi_drainage['baseline_scenario']['total_annual_loss']:,.0f}")
print(f"  With drainage total loss: ${roi_drainage['intervention_scenario']['total_annual_loss']:,.0f}")
print(f"  Annual avoided loss: ${roi_drainage['financial_analysis']['annual_avoided_loss']:,.0f}")
print(f"\n  NPV: ${roi_drainage['financial_analysis']['npv']:,.0f}")
print(f"  BCR: {roi_drainage['financial_analysis']['bcr']:.2f}")
print(f"  Recommendation: {'INVEST' if roi_drainage['recommendation']['invest'] else 'DO NOT INVEST'}")

print("\n  ✓ Drainage ROI calculation successful")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)

# Summary
print("\nInfrastructure Engine Summary:")
print("-" * 60)
print("\nDepth-Damage Curve (Research-Based):")
print("  • 0.0m = 0% damage")
print("  • 0.5m = 18% damage")
print("  • 1.0m = 29% damage")
print("  • 2.0m = 49% damage")
print("  • 3.0m = 60% damage (maximum)")
print("  • Uses linear interpolation between points")

print("\nBusiness Interruption:")
print("  • Threshold: 0.3m flood depth")
print("  • Downtime: 5 days")
print("  • Cost: 5 × daily_revenue")

print("\nIntervention Types:")
print("  • Sea Wall: Blocks water up to wall height")
print("  • Drainage: Reduces flood depth by 0.3m")

print("\nROI Metrics:")
print("  • NPV: Net Present Value of investment")
print("  • BCR: Benefit-Cost Ratio")
print("  • Payback Period: Years to recover investment")
print("  • Recommendation: Invest if NPV > 0 and BCR > 1")
