#!/usr/bin/env python3
"""
Test the health_engine.py functions
"""

from health_engine import calculate_productivity_loss, calculate_malaria_risk, calculate_health_economic_impact

print("Testing Health Engine")
print("=" * 60)

# Test Case 1: Safe working conditions (low WBGT)
print("\nTest Case 1: Safe working conditions (cool temperature)")
print("-" * 60)

temp_safe = 22.0  # 22°C
humidity_safe = 50.0  # 50%

productivity_safe = calculate_productivity_loss(temp_safe, humidity_safe)

print(f"  Temperature: {temp_safe}°C")
print(f"  Humidity: {humidity_safe}%")
print(f"  WBGT estimate: {productivity_safe['wbgt_estimate']}°C")
print(f"  Productivity loss: {productivity_safe['productivity_loss_pct']}%")
print(f"  Heat stress category: {productivity_safe['heat_stress_category']}")
print(f"  Recommendation: {productivity_safe['recommendation']}")

assert productivity_safe['productivity_loss_pct'] == 0.0, "No loss expected for low WBGT"
assert productivity_safe['heat_stress_category'] == "Low"
print("  ✓ Passed")

# Test Case 2: Moderate heat stress
print("\nTest Case 2: Moderate heat stress")
print("-" * 60)

temp_moderate = 30.0  # 30°C
humidity_moderate = 60.0  # 60%

productivity_moderate = calculate_productivity_loss(temp_moderate, humidity_moderate)

print(f"  Temperature: {temp_moderate}°C")
print(f"  Humidity: {humidity_moderate}%")
print(f"  WBGT estimate: {productivity_moderate['wbgt_estimate']}°C")
print(f"  Productivity loss: {productivity_moderate['productivity_loss_pct']}%")
print(f"  Heat stress category: {productivity_moderate['heat_stress_category']}")

# WBGT = 30*0.7 + 60/10 = 21 + 6 = 27°C
expected_wbgt = 27.0
assert abs(productivity_moderate['wbgt_estimate'] - expected_wbgt) < 0.1
assert productivity_moderate['productivity_loss_pct'] > 0.0
assert productivity_moderate['productivity_loss_pct'] < 50.0
print("  ✓ Passed")

# Test Case 3: Extreme heat stress
print("\nTest Case 3: Extreme heat stress (dangerous conditions)")
print("-" * 60)

temp_extreme = 38.0  # 38°C
humidity_extreme = 80.0  # 80%

productivity_extreme = calculate_productivity_loss(temp_extreme, humidity_extreme)

print(f"  Temperature: {temp_extreme}°C")
print(f"  Humidity: {humidity_extreme}%")
print(f"  WBGT estimate: {productivity_extreme['wbgt_estimate']}°C")
print(f"  Productivity loss: {productivity_extreme['productivity_loss_pct']}%")
print(f"  Heat stress category: {productivity_extreme['heat_stress_category']}")
print(f"  Recommendation: {productivity_extreme['recommendation']}")

assert productivity_extreme['productivity_loss_pct'] == 50.0, "Should cap at 50%"
assert productivity_extreme['heat_stress_category'] == "Extreme"
print("  ✓ Passed")

# Test Case 4: WBGT threshold boundaries
print("\nTest Case 4: WBGT threshold boundaries")
print("-" * 60)

# At 26°C WBGT threshold
# If temp=25°C, humidity=10%, WBGT = 25*0.7 + 10/10 = 17.5 + 1 = 18.5
# Need WBGT = 26: 26 = T*0.7 + H/10, so if H=60, T = (26-6)/0.7 = 28.57°C
temp_threshold = 28.6
humidity_threshold = 60.0

productivity_threshold = calculate_productivity_loss(temp_threshold, humidity_threshold)

print(f"  At 26°C WBGT (threshold):")
print(f"    Temperature: {temp_threshold}°C, Humidity: {humidity_threshold}%")
print(f"    WBGT: {productivity_threshold['wbgt_estimate']}°C")
print(f"    Productivity loss: {productivity_threshold['productivity_loss_pct']}%")

assert productivity_threshold['wbgt_estimate'] >= 26.0
print("  ✓ Threshold working correctly")

# Test Case 5: Malaria risk - high risk conditions
print("\nTest Case 5: Malaria risk - high risk (suitable temp + rain)")
print("-" * 60)

temp_malaria_high = 25.0  # 25°C (in 16-34°C range)
precip_malaria_high = 120.0  # 120mm (>80mm)

malaria_high = calculate_malaria_risk(temp_malaria_high, precip_malaria_high)

print(f"  Temperature: {temp_malaria_high}°C (suitable: 16-34°C)")
print(f"  Precipitation: {precip_malaria_high}mm (threshold: >80mm)")
print(f"  Risk score: {malaria_high['risk_score']}")
print(f"  Risk category: {malaria_high['risk_category']}")
print(f"  Description: {malaria_high['description']}")
print(f"  Risk factors: {', '.join(malaria_high['risk_factors'])}")

assert malaria_high['risk_score'] == 100, "Should be high risk"
assert malaria_high['risk_category'] == "High"
assert malaria_high['climate_suitability']['temperature_suitable'] == True
assert malaria_high['climate_suitability']['precipitation_suitable'] == True
print("  ✓ Passed")

# Test Case 6: Malaria risk - low risk (cold)
print("\nTest Case 6: Malaria risk - low risk (temperature too cold)")
print("-" * 60)

temp_malaria_low = 10.0  # 10°C (below 16°C)
precip_malaria_adequate = 150.0  # 150mm

malaria_low = calculate_malaria_risk(temp_malaria_low, precip_malaria_adequate)

print(f"  Temperature: {temp_malaria_low}°C (below 16°C threshold)")
print(f"  Precipitation: {precip_malaria_adequate}mm")
print(f"  Risk score: {malaria_low['risk_score']}")
print(f"  Risk category: {malaria_low['risk_category']}")

assert malaria_low['risk_score'] == 50, "Should be moderate (rain suitable only)"
assert malaria_low['risk_category'] == "Moderate"
print("  ✓ Passed")

# Test Case 7: Malaria risk - low risk (dry)
print("\nTest Case 7: Malaria risk - low risk (insufficient rainfall)")
print("-" * 60)

temp_malaria_ok = 22.0  # 22°C (suitable)
precip_malaria_low = 50.0  # 50mm (below 80mm)

malaria_dry = calculate_malaria_risk(temp_malaria_ok, precip_malaria_low)

print(f"  Temperature: {temp_malaria_ok}°C (suitable)")
print(f"  Precipitation: {precip_malaria_low}mm (below 80mm threshold)")
print(f"  Risk score: {malaria_dry['risk_score']}")
print(f"  Risk category: {malaria_dry['risk_category']}")

assert malaria_dry['risk_score'] == 50, "Should be moderate (temp suitable only)"
print("  ✓ Passed")

# Test Case 8: Economic impact calculation
print("\nTest Case 8: Economic impact of health risks")
print("-" * 60)

workforce = 1000
wage = 20.0  # $20/day
productivity_loss = 25.0  # 25%
malaria_risk = 100  # High risk

economic_impact = calculate_health_economic_impact(
    workforce_size=workforce,
    daily_wage=wage,
    productivity_loss_pct=productivity_loss,
    malaria_risk_score=malaria_risk
)

print(f"  Workforce: {workforce} workers")
print(f"  Daily wage: ${wage}")
print(f"  Productivity loss: {productivity_loss}%")
print(f"  Malaria risk: {malaria_risk} (High)")

print(f"\n  Heat Stress Impact:")
print(f"    Daily productivity loss: ${economic_impact['heat_stress_impact']['daily_productivity_loss']:,.0f}")
print(f"    Annual productivity loss: ${economic_impact['heat_stress_impact']['annual_productivity_loss']:,.0f}")

print(f"\n  Malaria Impact:")
print(f"    Days lost per worker: {economic_impact['malaria_impact']['estimated_days_lost_per_worker']}")
print(f"    Annual absenteeism cost: ${economic_impact['malaria_impact']['annual_absenteeism_cost']:,.0f}")
print(f"    Annual healthcare costs: ${economic_impact['malaria_impact']['annual_healthcare_costs']:,.0f}")

print(f"\n  Total Economic Impact:")
print(f"    Annual loss: ${economic_impact['total_economic_impact']['annual_loss']:,.0f}")
print(f"    Per worker annual loss: ${economic_impact['total_economic_impact']['per_worker_annual_loss']:,.0f}")

# Verify daily heat stress loss = 1000 * 20 * 0.25 = $5,000
expected_daily_loss = workforce * wage * (productivity_loss / 100.0)
assert abs(economic_impact['heat_stress_impact']['daily_productivity_loss'] - expected_daily_loss) < 0.01
print("\n  ✓ Economic calculations correct")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)

# Summary
print("\nHealth Engine Summary:")
print("-" * 60)

print("\nWBGT (Wet Bulb Globe Temperature) Proxy:")
print("  • Formula: WBGT ≈ 0.7×Temp + 0.1×Humidity")
print("  • Low threshold: 26°C (0% productivity loss)")
print("  • High threshold: 32°C (50% maximum loss)")
print("  • Categories: Low, Moderate, High, Very High, Extreme")

print("\nMalaria Risk Assessment:")
print("  • Temperature range: 16-34°C (suitable for parasite)")
print("  • Precipitation threshold: >80mm (mosquito breeding)")
print("  • Risk scores: 0 (Low), 50 (Moderate), 100 (High)")
print("  • Mitigation: Bed nets, spraying, eliminate standing water")

print("\nEconomic Impact:")
print("  • Heat stress: Daily productivity loss × 250 working days")
print("  • Malaria: Absenteeism (5-10 days/worker) + healthcare ($50/case)")
print("  • Total annual loss includes both heat and disease impacts")

print("\nUse Cases:")
print("  • Outdoor work planning (construction, agriculture)")
print("  • Labor productivity forecasting")
print("  • Public health risk assessment")
print("  • Economic loss estimation")
print("  • Climate adaptation planning")
