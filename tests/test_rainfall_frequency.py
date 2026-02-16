#!/usr/bin/env python3
"""
Test script for calculate_rainfall_frequency function
"""

from flood_engine import calculate_rainfall_frequency

print("Testing calculate_rainfall_frequency function")
print("=" * 60)

# Test Case 1: No intensity increase (baseline)
print("\nTest Case 1: No intensity increase (0%)")
print("-" * 60)
intensity_increase_pct = 0.0
result = calculate_rainfall_frequency(intensity_increase_pct)

print(f"Intensity increase: {intensity_increase_pct}%")
print(f"\nRain Chart Data:")
for item in result['rain_chart_data']:
    print(f"  {item['period']}: baseline={item['baseline_mm']}mm, future={item['future_mm']}mm")

# Verify structure
assert 'rain_chart_data' in result, "Missing rain_chart_data"
assert len(result['rain_chart_data']) == 4, "Should have 4 storm periods"

# Verify baseline values are correct
expected_baseline = {
    '1yr': 70.0,
    '10yr': 121.5,
    '50yr': 159.7,
    '100yr': 179.4
}

for item in result['rain_chart_data']:
    period = item['period']
    assert item['baseline_mm'] == expected_baseline[period], f"Wrong baseline for {period}"
    assert item['future_mm'] == expected_baseline[period], f"Future should equal baseline when increase=0"

# Verify sort order
periods = [item['period'] for item in result['rain_chart_data']]
assert periods == ['1yr', '10yr', '50yr', '100yr'], "Storm periods should be sorted by severity"

print("  ✓ All baseline values correct")
print("  ✓ Sort order correct")

# Test Case 2: 10% intensity increase
print("\nTest Case 2: 10% intensity increase")
print("-" * 60)
intensity_increase_pct = 10.0
result = calculate_rainfall_frequency(intensity_increase_pct)

print(f"Intensity increase: {intensity_increase_pct}%")
print(f"\nRain Chart Data:")
for item in result['rain_chart_data']:
    increase = item['future_mm'] - item['baseline_mm']
    print(f"  {item['period']}: baseline={item['baseline_mm']}mm, future={item['future_mm']}mm (Δ={increase:.2f}mm)")

# Verify calculations
expected_results = {
    '1yr': (70.0, 77.0),      # 70 * 1.1 = 77
    '10yr': (121.5, 133.65),  # 121.5 * 1.1 = 133.65
    '50yr': (159.7, 175.67),  # 159.7 * 1.1 = 175.67
    '100yr': (179.4, 197.34)  # 179.4 * 1.1 = 197.34
}

for item in result['rain_chart_data']:
    period = item['period']
    expected_baseline, expected_future = expected_results[period]
    assert item['baseline_mm'] == expected_baseline, f"Wrong baseline for {period}"
    assert item['future_mm'] == expected_future, f"Wrong future for {period}"

print("  ✓ All calculations correct")

# Test Case 3: 25% intensity increase
print("\nTest Case 3: 25% intensity increase")
print("-" * 60)
intensity_increase_pct = 25.0
result = calculate_rainfall_frequency(intensity_increase_pct)

print(f"Intensity increase: {intensity_increase_pct}%")
print(f"\nRain Chart Data:")
for item in result['rain_chart_data']:
    increase = item['future_mm'] - item['baseline_mm']
    pct_increase = (increase / item['baseline_mm']) * 100
    print(f"  {item['period']}: baseline={item['baseline_mm']}mm, future={item['future_mm']}mm ({pct_increase:.1f}% increase)")

# Verify 1yr storm
item_1yr = result['rain_chart_data'][0]
assert item_1yr['period'] == '1yr', "First item should be 1yr"
assert item_1yr['baseline_mm'] == 70.0, "1yr baseline should be 70.0mm"
assert item_1yr['future_mm'] == 87.5, "1yr future should be 87.5mm (70 * 1.25)"

# Verify 100yr storm
item_100yr = result['rain_chart_data'][3]
assert item_100yr['period'] == '100yr', "Last item should be 100yr"
assert item_100yr['baseline_mm'] == 179.4, "100yr baseline should be 179.4mm"
assert item_100yr['future_mm'] == 224.25, "100yr future should be 224.25mm (179.4 * 1.25)"

print("  ✓ All calculations correct")

# Test Case 4: Rounding verification
print("\nTest Case 4: Rounding verification (15% increase)")
print("-" * 60)
intensity_increase_pct = 15.0
result = calculate_rainfall_frequency(intensity_increase_pct)

print(f"Intensity increase: {intensity_increase_pct}%")
print(f"\nRain Chart Data:")
for item in result['rain_chart_data']:
    # Check that it's rounded to 2 decimal places
    baseline_decimals = len(str(item['baseline_mm']).split('.')[-1]) if '.' in str(item['baseline_mm']) else 0
    future_decimals = len(str(item['future_mm']).split('.')[-1]) if '.' in str(item['future_mm']) else 0
    
    assert baseline_decimals <= 2, f"Baseline should be rounded to 2 decimals"
    assert future_decimals <= 2, f"Future should be rounded to 2 decimals"
    
    print(f"  {item['period']}: baseline={item['baseline_mm']}mm, future={item['future_mm']}mm")

print("  ✓ Rounding correct")

# Test Case 5: Zero increase edge case
print("\nTest Case 5: Negative values not allowed (but test zero)")
print("-" * 60)
intensity_increase_pct = 0.0
result = calculate_rainfall_frequency(intensity_increase_pct)

for item in result['rain_chart_data']:
    assert item['baseline_mm'] == item['future_mm'], "At 0%, baseline should equal future"

print(f"  All values equal at 0% increase")
print("  ✓ Passed")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)

# Show example output structure
print("\nExample Output Structure:")
import json
example = calculate_rainfall_frequency(10.0)
print(json.dumps(example, indent=2))
