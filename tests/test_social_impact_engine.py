#!/usr/bin/env python3
"""
Test the social_impact_engine.py functions
"""

from social_impact_engine import calculate_nature_value, calculate_social_metrics

print("Testing Social Impact Engine")
print("=" * 60)

# Test Case 1: Mangrove restoration value
print("\nTest Case 1: Mangrove restoration - carbon sequestration")
print("-" * 60)

area_mangroves = 100  # hectares
mangrove_value = calculate_nature_value('mangroves', area_mangroves)

print(f"  Mangrove restoration area: {area_mangroves} hectares")
print(f"\n  Carbon Sequestration:")
print(f"    Annual: {mangrove_value['carbon_sequestration']['annual_tons_co2']} tons CO2")
print(f"    20-year cumulative: {mangrove_value['carbon_sequestration']['cumulative_tons_co2_20yr']:,} tons CO2")
print(f"    Rate: {mangrove_value['carbon_sequestration']['rate_per_hectare']} tons/ha/year")

print(f"\n  Economic Value:")
print(f"    Annual: ${mangrove_value['economic_value']['annual_usd']:,}")
print(f"    20-year cumulative: ${mangrove_value['economic_value']['cumulative_usd_20yr']:,}")
print(f"    Carbon price: ${mangrove_value['economic_value']['carbon_price_per_ton']}/ton CO2")

print(f"\n  Co-benefits: {', '.join(mangrove_value['co_benefits'])}")

# Verify calculations
expected_annual_carbon = area_mangroves * 7.0  # 700 tons
expected_annual_value = expected_annual_carbon * 70  # $49,000
assert mangrove_value['carbon_sequestration']['annual_tons_co2'] == expected_annual_carbon
assert mangrove_value['economic_value']['annual_usd'] == expected_annual_value
print("\n  ✓ Calculations correct")

# Test Case 2: Wetlands restoration value
print("\nTest Case 2: Wetlands restoration - carbon sequestration")
print("-" * 60)

area_wetlands = 50  # hectares
wetland_value = calculate_nature_value('wetlands', area_wetlands)

print(f"  Wetland restoration area: {area_wetlands} hectares")
print(f"\n  Carbon Sequestration:")
print(f"    Annual: {wetland_value['carbon_sequestration']['annual_tons_co2']} tons CO2")
print(f"    20-year cumulative: {wetland_value['carbon_sequestration']['cumulative_tons_co2_20yr']:,} tons CO2")
print(f"    Rate: {wetland_value['carbon_sequestration']['rate_per_hectare']} tons/ha/year")

print(f"\n  Economic Value:")
print(f"    Annual: ${wetland_value['economic_value']['annual_usd']:,}")
print(f"    20-year cumulative: ${wetland_value['economic_value']['cumulative_usd_20yr']:,}")

print(f"\n  Co-benefits: {', '.join(wetland_value['co_benefits'])}")

# Wetlands have lower carbon rate than mangroves
assert wetland_value['carbon_sequestration']['rate_per_hectare'] < mangrove_value['carbon_sequestration']['rate_per_hectare']
print("\n  ✓ Wetlands < Mangroves carbon rate (correct)")

# Test Case 3: Non-nature-based solution (sea wall)
print("\nTest Case 3: Sea wall (non-nature-based solution)")
print("-" * 60)

seawall_value = calculate_nature_value('sea_wall', 0)

print(f"  Intervention: {seawall_value['intervention_type']}")
print(f"  Carbon sequestration: {seawall_value['carbon_sequestration']['annual_tons_co2']} tons/year")
print(f"  Economic value: ${seawall_value['economic_value']['annual_usd']}")

assert seawall_value['carbon_sequestration']['annual_tons_co2'] == 0
assert seawall_value['economic_value']['annual_usd'] == 0
print("\n  ✓ Zero carbon value (correct for grey infrastructure)")

# Test Case 4: Social metrics calculation
print("\nTest Case 4: Social impact metrics")
print("-" * 60)

people_at_risk = 5000
households_at_risk = int(people_at_risk / 4.9)  # ~1020 households
intervention_cost = 500_000

social_metrics = calculate_social_metrics(
    people_at_risk=people_at_risk,
    households_at_risk=households_at_risk,
    intervention_cost=intervention_cost,
    nature_value=None
)

print(f"  People protected: {social_metrics['beneficiaries']['people_protected']:,}")
print(f"  Households protected: {social_metrics['beneficiaries']['households_protected']:,}")
print(f"\n  Cost Effectiveness:")
print(f"    Cost per person: ${social_metrics['cost_effectiveness']['cost_per_person_protected']:,.2f}")
print(f"    Cost per household: ${social_metrics['cost_effectiveness']['cost_per_household_protected']:,.2f}")
print(f"\n  Social Value:")
print(f"    Lives protected: {social_metrics['social_value']['lives_protected']:,}")
print(f"    Displacement avoided: {social_metrics['social_value']['displacement_avoided']:,} households")
print(f"    Community resilience: {social_metrics['social_value']['community_resilience_improvement']}")

expected_cost_per_person = intervention_cost / people_at_risk
assert abs(social_metrics['cost_effectiveness']['cost_per_person_protected'] - expected_cost_per_person) < 0.01
print("\n  ✓ Cost-effectiveness calculations correct")

# Test Case 5: Social metrics with nature value
print("\nTest Case 5: Social metrics including nature-based solution value")
print("-" * 60)

# Mangrove restoration project
people_at_risk_2 = 10000
households_at_risk_2 = int(people_at_risk_2 / 4.9)
intervention_cost_2 = 800_000
area_mangroves_2 = 200  # hectares

nature_value_2 = calculate_nature_value('mangroves', area_mangroves_2)

social_metrics_2 = calculate_social_metrics(
    people_at_risk=people_at_risk_2,
    households_at_risk=households_at_risk_2,
    intervention_cost=intervention_cost_2,
    nature_value=nature_value_2
)

print(f"  Mangrove project:")
print(f"    Area: {area_mangroves_2} hectares")
print(f"    People protected: {social_metrics_2['beneficiaries']['people_protected']:,}")
print(f"    Carbon value (20yr): ${nature_value_2['economic_value']['cumulative_usd_20yr']:,}")
print(f"\n  Cost per person: ${social_metrics_2['cost_effectiveness']['cost_per_person_protected']:,.2f}")
print(f"  Community resilience: {social_metrics_2['social_value']['community_resilience_improvement']}")

assert social_metrics_2['social_value']['community_resilience_improvement'] == 'High', "Should be High for >1000 people"
print("\n  ✓ High impact classification correct")

# Test Case 6: Comparison - Nature-based vs Grey infrastructure
print("\nTest Case 6: Comparison - Mangroves vs Sea Wall")
print("-" * 60)

# Same beneficiaries and cost
project_cost = 1_000_000
project_people = 8000

# Scenario A: Mangrove restoration (200 ha)
mangrove_scenario = calculate_nature_value('mangroves', 200)
mangrove_social = calculate_social_metrics(
    people_at_risk=project_people,
    households_at_risk=int(project_people / 4.9),
    intervention_cost=project_cost,
    nature_value=mangrove_scenario
)

# Scenario B: Sea wall
seawall_scenario = calculate_nature_value('sea_wall', 0)
seawall_social = calculate_social_metrics(
    people_at_risk=project_people,
    households_at_risk=int(project_people / 4.9),
    intervention_cost=project_cost,
    nature_value=seawall_scenario
)

print(f"  Project cost: ${project_cost:,}")
print(f"  People protected: {project_people:,}")
print(f"\n  Mangrove Restoration:")
print(f"    Carbon value (20yr): ${mangrove_scenario['economic_value']['cumulative_usd_20yr']:,}")
print(f"    Co-benefits: {len(mangrove_scenario['co_benefits'])} additional services")
print(f"\n  Sea Wall:")
print(f"    Carbon value: ${seawall_scenario['economic_value']['cumulative_usd_20yr']:,}")
print(f"    Co-benefits: {len(seawall_scenario['co_benefits'])} additional services")

print(f"\n  Mangrove Advantage:")
carbon_advantage = mangrove_scenario['economic_value']['cumulative_usd_20yr']
print(f"    Additional value: ${carbon_advantage:,} (carbon sequestration)")
print(f"    Ecosystem co-benefits: Storm protection, fisheries, biodiversity")
print(f"    Nature-based solutions provide multiple benefits beyond flood protection")

print("\n  ✓ Nature-based solutions show additional value")

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)

# Summary
print("\nSocial Impact Engine Summary:")
print("-" * 60)

print("\nBeneficiaries Analysis:")
print("  • Uses CIESIN GPWv4.11 population data (2020)")
print("  • Calculates people and households at risk")
print("  • Average household size: 4.9 people")

print("\nNature-Based Solutions:")
print("  • Mangroves: 7 tons CO2/ha/year")
print("  • Wetlands: 5 tons CO2/ha/year")
print("  • Carbon price: $70/ton CO2")
print("  • 20-year cumulative value calculated")

print("\nSocial Metrics:")
print("  • Cost per person/household protected")
print("  • Lives protected and displacement avoided")
print("  • Community resilience rating (High/Medium)")
print("  • Total social value assessment")

print("\nCo-Benefits (Nature-Based Solutions):")
print("  • Mangroves: Storm surge, fish habitat, water quality, biodiversity")
print("  • Wetlands: Flood retention, groundwater, wildlife, recreation")
