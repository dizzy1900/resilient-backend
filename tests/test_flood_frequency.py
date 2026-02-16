#!/usr/bin/env python3
"""
Test script for calculate_flood_frequency function
"""

from coastal_engine import calculate_flood_frequency

print("Testing calculate_flood_frequency function")
print("=" * 60)

# Test Case 1: No sea level rise (baseline)
print("\nTest Case 1: No sea level rise (slr_meters = 0.0)")
print("-" * 60)
slr_meters = 0.0
result = calculate_flood_frequency(slr_meters)

print(f"SLR: {slr_meters}m")
print(f"\nStorm Chart Data:")
for item in result['storm_chart_data']:
    print(f"  {item['period']}: current={item['current_depth']}m, future={item['future_depth']}m")

# Verify structure
assert 'storm_chart_data' in result, "Missing storm_chart_data"
assert len(result['storm_chart_data']) == 4, "Should have 4 storm periods"

# Verify baseline values are correct
expected_baseline = {
    '1yr': 0.6,
    '10yr': 1.2,
    '50yr': 1.9,
    '100yr': 2.5
}

for item in result['storm_chart_data']:
    period = item['period']
    assert item['current_depth'] == expected_baseline[period], f"Wrong baseline for {period}"
    assert item['future_depth'] == expected_baseline[period], f"Future should equal current when SLR=0"

# Verify sort order
periods = [item['period'] for item in result['storm_chart_data']]
assert periods == ['1yr', '10yr', '50yr', '100yr'], "Storm periods should be sorted by severity"

print("  ✓ All baseline values correct")
print("  ✓ Sort order correct")

# Test Case 2: With sea level rise (0.5m)
print("\nTest Case 2: With sea level rise (slr_meters = 0.5)")
print("-" * 60)
slr_meters = 0.5
result = calculate_flood_frequency(slr_meters)

print(f"SLR: {slr_meters}m")
print(f"\nStorm Chart Data:")
for item in result['storm_chart_data']:
    print(f"  {item['period']}: current={item['current_depth']}m, future={item['future_depth']}m (Δ={item['future_depth'] - item['current_depth']}m)")

# Verify calculations
expected_results = {
    '1yr': (0.6, 1.1),
    '10yr': (1.2, 1.7),
    '50yr': (1.9, 2.4),
    '100yr': (2.5, 3.0)
}

for item in result['storm_chart_data']:
    period = item['period']
    expected_current, expected_future = expected_results[period]
    assert item['current_depth'] == expected_current, f"Wrong current depth for {period}"
    assert item['future_depth'] == expected_future, f"Wrong future depth for {period}"
    
    # Verify the difference is exactly the SLR
    diff = item['future_depth'] - item['current_depth']
    assert abs(diff - slr_meters) < 0.01, f"Difference should be {slr_meters}m"

print("  ✓ All calculations correct")

# Test Case 3: Higher sea level rise (1.0m)
print("\nTest Case 3: Higher sea level rise (slr_meters = 1.0)")
print("-" * 60)
slr_meters = 1.0
result = calculate_flood_frequency(slr_meters)

print(f"SLR: {slr_meters}m")
print(f"\nStorm Chart Data:")
for item in result['storm_chart_data']:
    print(f"  {item['period']}: current={item['current_depth']}m, future={item['future_depth']}m (Δ={item['future_depth'] - item['current_depth']}m)")

# Verify 1yr storm future depth
item_1yr = result['storm_chart_data'][0]
assert item_1yr['period'] == '1yr', "First item should be 1yr"
assert item_1yr['current_depth'] == 0.6, "1yr current should be 0.6m"
assert item_1yr['future_depth'] == 1.6, "1yr future should be 1.6m"

# Verify 100yr storm future depth
item_100yr = result['storm_chart_data'][3]
assert item_100yr['period'] == '100yr', "Last item should be 100yr"
assert item_100yr['current_depth'] == 2.5, "100yr current should be 2.5m"
assert item_100yr['future_depth'] == 3.5, "100yr future should be 3.5m"

print("  ✓ All calculations correct")

# Test Case 4: Rounding verification
print("\nTest Case 4: Rounding verification (slr_meters = 0.333)")
print("-" * 60)
slr_meters = 0.333
result = calculate_flood_frequency(slr_meters)

print(f"SLR: {slr_meters}m")
print(f"\nStorm Chart Data:")
for item in result['storm_chart_data']:
    future_depth = item['future_depth']
    # Check that it's rounded to 2 decimal places
    assert len(str(future_depth).split('.')[-1]) <= 2, f"Future depth should be rounded to 2 decimals"
    print(f"  {item['period']}: current={item['current_depth']}m, future={future_depth}m")

# Verify specific rounding
item_1yr = result['storm_chart_data'][0]
expected_future = round(0.6 + 0.333, 2)
assert item_1yr['future_depth'] == expected_future, f"1yr future should be {expected_future}m"

print("  ✓ Rounding correct")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)

# Show example output
print("\nExample Output Structure:")
import json
example = calculate_flood_frequency(0.5)
print(json.dumps(example, indent=2))
