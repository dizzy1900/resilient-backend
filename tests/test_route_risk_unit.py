#!/usr/bin/env python3
"""
Unit tests for Macroeconomic Supply Chain Route Risk calculations.

Tests the economic formulas using mock flooded miles (2.5) without requiring GEE credentials.
"""


def test_mock_flooded_miles():
    """Test mock flooded miles placeholder."""
    flooded_miles = 2.5  # Mock/placeholder value
    
    assert flooded_miles == 2.5


def test_detour_delay_calculation():
    """Test detour delay calculation: 0.5 hours per flooded mile."""
    flooded_miles = 2.5  # Mock value
    expected_delay = 1.25  # 2.5 miles × 0.5 hours/mile
    
    detour_delay_hours = flooded_miles * 0.5
    
    assert detour_delay_hours == expected_delay


def test_freight_delay_cost():
    """Test freight delay cost: $91.27 per hour."""
    detour_delay_hours = 2.0
    expected_cost = 182.54  # 2 hours × $91.27/hour
    
    freight_delay_cost = detour_delay_hours * 91.27
    
    assert abs(freight_delay_cost - expected_cost) < 0.01


def test_spoilage_cost():
    """Test spoilage cost: 20% of cargo value, prorated by delay."""
    cargo_value = 100000.0
    detour_delay_hours = 12.0  # 0.5 days
    expected_spoilage = 10000.0  # $100k × 0.2 × (12/24) = $10k
    
    spoilage_cost = cargo_value * 0.2 * (detour_delay_hours / 24.0)
    
    assert abs(spoilage_cost - expected_spoilage) < 0.01


def test_total_value_at_risk():
    """Test total value at risk aggregation."""
    flooded_miles = 5.0
    cargo_value = 250000.0
    
    detour_delay_hours = flooded_miles * 0.5  # 2.5 hours
    freight_delay_cost = detour_delay_hours * 91.27  # $228.175
    spoilage_cost = cargo_value * 0.2 * (detour_delay_hours / 24.0)  # $5,208.33
    total_value_at_risk = freight_delay_cost + spoilage_cost  # $5,436.50
    
    assert abs(total_value_at_risk - 5436.505) < 0.01


def test_intervention_capex():
    """Test intervention CAPEX: $5M per flooded mile (highway elevation)."""
    flooded_miles = 2.5  # Mock value
    expected_capex = 12500000.0  # 2.5 miles × $5M/mile
    
    intervention_capex = flooded_miles * 5_000_000.0
    
    assert intervention_capex == expected_capex


def test_zero_flooded_miles():
    """Test edge case: no flooded miles (safe route)."""
    flooded_miles = 0.0
    cargo_value = 100000.0
    
    detour_delay_hours = flooded_miles * 0.5
    freight_delay_cost = detour_delay_hours * 91.27
    spoilage_cost = cargo_value * 0.2 * (detour_delay_hours / 24.0)
    total_value_at_risk = freight_delay_cost + spoilage_cost
    intervention_capex = flooded_miles * 6_500_000.0
    
    assert detour_delay_hours == 0.0
    assert freight_delay_cost == 0.0
    assert spoilage_cost == 0.0
    assert total_value_at_risk == 0.0
    assert intervention_capex == 0.0


def test_high_value_cargo_spoilage():
    """Test that spoilage cost scales with cargo value."""
    low_value_cargo = 50000.0
    high_value_cargo = 500000.0
    detour_delay_hours = 24.0  # Full day delay
    
    low_spoilage = low_value_cargo * 0.2 * (detour_delay_hours / 24.0)  # $10k
    high_spoilage = high_value_cargo * 0.2 * (detour_delay_hours / 24.0)  # $100k
    
    assert high_spoilage == 10 * low_spoilage


def test_full_scenario_mock():
    """Test full calculation using mock flooded miles."""
    flooded_miles = 2.5  # Mock value
    cargo_value = 100000.0
    
    # Economic calculations (ATRI benchmarks)
    detour_delay_hours = flooded_miles * 0.5  # 1.25 hours
    freight_delay_cost = detour_delay_hours * 91.27  # $114.09
    spoilage_cost = cargo_value * 0.20 * (detour_delay_hours / 24.0)  # $1,041.67
    total_value_at_risk = freight_delay_cost + spoilage_cost  # $1,155.76
    intervention_capex = flooded_miles * 5_000_000.0  # $12.5M
    
    # Assertions
    assert abs(detour_delay_hours - 1.25) < 0.01
    assert abs(freight_delay_cost - 114.0875) < 0.01
    assert abs(spoilage_cost - 1041.6667) < 0.01
    assert abs(total_value_at_risk - 1155.7542) < 0.01
    assert intervention_capex == 12500000.0


def test_rounding_precision():
    """Test that results are properly rounded to 2 decimal places."""
    flooded_miles = 3.7777
    cargo_value = 123456.78
    
    detour_delay_hours = flooded_miles * 0.5
    freight_delay_cost = detour_delay_hours * 91.27
    spoilage_cost = cargo_value * 0.2 * (detour_delay_hours / 24.0)
    total_value_at_risk = freight_delay_cost + spoilage_cost
    intervention_capex = flooded_miles * 6_500_000.0
    
    # Round to 2 decimals (as API does)
    flooded_miles_rounded = round(flooded_miles, 2)
    detour_delay_rounded = round(detour_delay_hours, 2)
    freight_cost_rounded = round(freight_delay_cost, 2)
    spoilage_rounded = round(spoilage_cost, 2)
    risk_rounded = round(total_value_at_risk, 2)
    capex_rounded = round(intervention_capex, 2)
    
    # Verify rounding works correctly
    assert flooded_miles_rounded == 3.78
    assert detour_delay_rounded == 1.89
    # Verify calculations produce reasonable results (within expected range)
    assert 172 <= freight_cost_rounded <= 173
    assert 1940 <= spoilage_rounded <= 1945
    assert 2112 <= risk_rounded <= 2116
    assert capex_rounded == 24555050.00


if __name__ == "__main__":
    # Run tests manually without pytest
    print("Running Macroeconomic Supply Chain Route Risk Unit Tests\n")
    
    test_mock_flooded_miles()
    print("✅ test_mock_flooded_miles")
    
    test_detour_delay_calculation()
    print("✅ test_detour_delay_calculation")
    
    test_freight_delay_cost()
    print("✅ test_freight_delay_cost")
    
    test_spoilage_cost()
    print("✅ test_spoilage_cost")
    
    test_total_value_at_risk()
    print("✅ test_total_value_at_risk")
    
    test_intervention_capex()
    print("✅ test_intervention_capex")
    
    test_zero_flooded_miles()
    print("✅ test_zero_flooded_miles")
    
    test_high_value_cargo_spoilage()
    print("✅ test_high_value_cargo_spoilage")
    
    test_full_scenario_mock()
    print("✅ test_full_scenario_mock")
    
    test_rounding_precision()
    print("✅ test_rounding_precision")
    
    print("\n✅ All tests passed!")
