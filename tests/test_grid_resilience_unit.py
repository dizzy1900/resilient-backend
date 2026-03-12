#!/usr/bin/env python3
"""
Unit tests for Energy & Grid Resilience calculations.

Tests the energy and economic formulas without requiring external dependencies.
"""


def test_temperature_anomaly():
    """Test temperature anomaly calculation."""
    baseline_temp_c = 25.0
    projected_temp_c = 35.0
    expected_anomaly = 10.0
    
    temp_anomaly = projected_temp_c - baseline_temp_c
    
    assert temp_anomaly == expected_anomaly


def test_hvac_spike_calculation():
    """Test HVAC spike percentage: 3% per degree Celsius (ASHRAE)."""
    temp_anomaly = 10.0
    expected_spike_pct = 30.0  # 30% (as percentage, not decimal)
    
    hvac_spike_pct = temp_anomaly * 3.0
    
    assert abs(hvac_spike_pct - expected_spike_pct) < 0.001


def test_grid_failure_probability():
    """Test grid failure probability calculation (capped at 100%)."""
    # Test case 1: Normal case (not capped)
    hvac_spike_pct = 20.0  # 20% (as percentage)
    expected_prob = 0.30  # 30% (as decimal)
    
    grid_failure_probability = min((hvac_spike_pct / 100.0) * 1.5, 1.0)
    
    assert abs(grid_failure_probability - expected_prob) < 0.001
    
    # Test case 2: Capped at 100%
    hvac_spike_pct = 80.0  # 80% (as percentage)
    expected_prob_capped = 1.0  # 100% (capped)
    
    grid_failure_probability_capped = min((hvac_spike_pct / 100.0) * 1.5, 1.0)
    
    assert grid_failure_probability_capped == expected_prob_capped


def test_expected_downtime_hours():
    """Test expected downtime calculation: probability × 12 hours."""
    grid_failure_probability = 0.50  # 50%
    expected_downtime = 6.0  # 6 hours
    
    expected_downtime_hours = grid_failure_probability * 12.0
    
    assert expected_downtime_hours == expected_downtime


def test_downtime_loss():
    """Test downtime economic loss: $25,000 per hour (Fuji/Siemens benchmark)."""
    expected_downtime_hours = 8.0
    expected_loss = 200000.0  # $200k
    
    downtime_loss = expected_downtime_hours * 25000.0
    
    assert downtime_loss == expected_loss


def test_solar_sizing():
    """Test solar capacity sizing: 1% of facility size."""
    facility_sqft = 50000.0
    expected_solar_kw = 500.0
    
    required_solar_kw = facility_sqft * 0.01
    
    assert required_solar_kw == expected_solar_kw


def test_battery_sizing():
    """Test battery storage sizing: 4 hours of backup."""
    required_solar_kw = 500.0
    expected_bess_kwh = 2000.0
    
    required_bess_kwh = required_solar_kw * 4.0
    
    assert required_bess_kwh == expected_bess_kwh


def test_microgrid_capex():
    """Test microgrid CAPEX: $1,780/kW solar + $400/kWh battery (NREL ATB 2024)."""
    required_solar_kw = 500.0
    required_bess_kwh = 2000.0
    expected_capex = 1690000.0  # (500 × 1780) + (2000 × 400) = $890k + $800k
    
    solar_cost = required_solar_kw * 1780.0
    bess_cost = required_bess_kwh * 400.0
    microgrid_capex = solar_cost + bess_cost
    
    assert microgrid_capex == expected_capex


def test_full_scenario_moderate_heat():
    """Test full calculation for moderate heat scenario (default values)."""
    facility_sqft = 50000.0
    baseline_temp_c = 25.0
    projected_temp_c = 35.0  # Default value, +10°C
    
    # Temperature anomaly
    temp_anomaly = projected_temp_c - baseline_temp_c  # 10°C
    assert temp_anomaly == 10.0
    
    # HVAC spike (ASHRAE: 3% per °C)
    hvac_spike_pct = temp_anomaly * 3.0  # 30%
    assert abs(hvac_spike_pct - 30.0) < 0.001
    
    # Grid failure probability
    grid_failure_probability = min((hvac_spike_pct / 100.0) * 1.5, 1.0)  # 45%
    assert abs(grid_failure_probability - 0.45) < 0.001
    
    # Expected downtime
    expected_downtime_hours = grid_failure_probability * 12.0  # 5.4 hours
    assert abs(expected_downtime_hours - 5.4) < 0.01
    
    # Downtime loss (Fuji/Siemens: $25k/hr)
    downtime_loss = expected_downtime_hours * 25000.0  # $135,000
    assert abs(downtime_loss - 135000.0) < 1.0
    
    # Solar sizing
    required_solar_kw = facility_sqft * 0.01  # 500 kW
    assert required_solar_kw == 500.0
    
    # Battery sizing
    required_bess_kwh = required_solar_kw * 4.0  # 2000 kWh
    assert required_bess_kwh == 2000.0
    
    # Microgrid CAPEX (NREL ATB 2024)
    microgrid_capex = (required_solar_kw * 1780.0) + (required_bess_kwh * 400.0)
    assert microgrid_capex == 1690000.0


def test_full_scenario_extreme_heat():
    """Test full calculation for extreme heat scenario."""
    facility_sqft = 100000.0
    baseline_temp_c = 25.0
    projected_temp_c = 40.0
    
    # Temperature anomaly
    temp_anomaly = projected_temp_c - baseline_temp_c  # 15°C
    assert temp_anomaly == 15.0
    
    # HVAC spike (ASHRAE: 3% per °C)
    hvac_spike_pct = temp_anomaly * 3.0  # 45%
    assert abs(hvac_spike_pct - 45.0) < 0.001
    
    # Grid failure probability (should approach cap)
    grid_failure_probability = min((hvac_spike_pct / 100.0) * 1.5, 1.0)  # 67.5%
    assert abs(grid_failure_probability - 0.675) < 0.001
    
    # Expected downtime
    expected_downtime_hours = grid_failure_probability * 12.0  # 8.1 hours
    assert abs(expected_downtime_hours - 8.1) < 0.01
    
    # Downtime loss (Fuji/Siemens: $25k/hr)
    downtime_loss = expected_downtime_hours * 25000.0  # $202,500
    assert abs(downtime_loss - 202500.0) < 1.0
    
    # Solar sizing (larger facility)
    required_solar_kw = facility_sqft * 0.01  # 1000 kW
    assert required_solar_kw == 1000.0
    
    # Battery sizing
    required_bess_kwh = required_solar_kw * 4.0  # 4000 kWh
    assert required_bess_kwh == 4000.0
    
    # Microgrid CAPEX (NREL ATB 2024)
    microgrid_capex = (required_solar_kw * 1780.0) + (required_bess_kwh * 400.0)
    assert microgrid_capex == 3380000.0


def test_zero_temp_anomaly():
    """Test edge case: no temperature change."""
    facility_sqft = 50000.0
    baseline_temp_c = 25.0
    projected_temp_c = 25.0
    
    temp_anomaly = projected_temp_c - baseline_temp_c
    hvac_spike_pct = temp_anomaly * 0.027
    grid_failure_probability = min(hvac_spike_pct * 1.5, 1.0)
    expected_downtime_hours = grid_failure_probability * 12.0
    downtime_loss = expected_downtime_hours * 30000.0
    
    assert temp_anomaly == 0.0
    assert hvac_spike_pct == 0.0
    assert grid_failure_probability == 0.0
    assert expected_downtime_hours == 0.0
    assert downtime_loss == 0.0


def test_extreme_temperature_capping():
    """Test that extreme temperatures cap at 100% grid failure."""
    facility_sqft = 50000.0
    baseline_temp_c = 25.0
    projected_temp_c = 50.0  # Extreme +25°C anomaly
    
    temp_anomaly = projected_temp_c - baseline_temp_c  # 25°C
    hvac_spike_pct = temp_anomaly * 3.0  # 75% (ASHRAE)
    grid_failure_probability = min((hvac_spike_pct / 100.0) * 1.5, 1.0)  # Should cap at 100%
    
    # 75% × 1.5 = 112.5%, but capped at 100%
    assert grid_failure_probability == 1.0
    
    expected_downtime_hours = grid_failure_probability * 12.0
    assert expected_downtime_hours == 12.0  # Maximum downtime


def test_small_facility_sizing():
    """Test microgrid sizing for small facility."""
    facility_sqft = 10000.0  # Small facility
    
    required_solar_kw = facility_sqft * 0.01  # 100 kW
    required_bess_kwh = required_solar_kw * 4.0  # 400 kWh
    microgrid_capex = (required_solar_kw * 1780.0) + (required_bess_kwh * 400.0)
    
    assert required_solar_kw == 100.0
    assert required_bess_kwh == 400.0
    assert microgrid_capex == 338000.0  # $338k (NREL ATB 2024)


def test_large_facility_sizing():
    """Test microgrid sizing for large facility."""
    facility_sqft = 500000.0  # Large facility (e.g., data center)
    
    required_solar_kw = facility_sqft * 0.01  # 5000 kW = 5 MW
    required_bess_kwh = required_solar_kw * 4.0  # 20,000 kWh
    microgrid_capex = (required_solar_kw * 1780.0) + (required_bess_kwh * 400.0)
    
    assert required_solar_kw == 5000.0
    assert required_bess_kwh == 20000.0
    assert microgrid_capex == 16900000.0  # $16.9M (NREL ATB 2024)


def test_rounding_precision():
    """Test that results are properly rounded."""
    facility_sqft = 47382.5
    baseline_temp_c = 24.3
    projected_temp_c = 33.7
    
    temp_anomaly = projected_temp_c - baseline_temp_c
    hvac_spike_pct = temp_anomaly * 0.027
    grid_failure_probability = min(hvac_spike_pct * 1.5, 1.0)
    expected_downtime_hours = grid_failure_probability * 12.0
    downtime_loss = expected_downtime_hours * 30000.0
    required_solar_kw = facility_sqft * 0.01
    required_bess_kwh = required_solar_kw * 4.0
    microgrid_capex = (required_solar_kw * 2000.0) + (required_bess_kwh * 400.0)
    
    # Round to 2 decimals (as API does)
    temp_anomaly_rounded = round(temp_anomaly, 2)
    hvac_spike_rounded = round(hvac_spike_pct * 100, 2)
    prob_rounded = round(grid_failure_probability, 4)
    downtime_rounded = round(expected_downtime_hours, 2)
    loss_rounded = round(downtime_loss, 2)
    solar_rounded = round(required_solar_kw, 2)
    bess_rounded = round(required_bess_kwh, 2)
    capex_rounded = round(microgrid_capex, 2)
    
    # Verify rounding doesn't cause large errors
    assert temp_anomaly_rounded == 9.40
    assert 25.0 <= hvac_spike_rounded <= 26.0
    assert 0.35 <= prob_rounded <= 0.40  # Reasonable range
    assert downtime_rounded >= 4.0
    assert loss_rounded >= 100000.0
    assert solar_rounded > 470.0
    assert bess_rounded > 1880.0
    assert capex_rounded > 0  # Just verify it's positive


if __name__ == "__main__":
    # Run tests manually without pytest
    print("Running Energy & Grid Resilience Unit Tests\n")
    
    test_temperature_anomaly()
    print("✅ test_temperature_anomaly")
    
    test_hvac_spike_calculation()
    print("✅ test_hvac_spike_calculation")
    
    test_grid_failure_probability()
    print("✅ test_grid_failure_probability")
    
    test_expected_downtime_hours()
    print("✅ test_expected_downtime_hours")
    
    test_downtime_loss()
    print("✅ test_downtime_loss")
    
    test_solar_sizing()
    print("✅ test_solar_sizing")
    
    test_battery_sizing()
    print("✅ test_battery_sizing")
    
    test_microgrid_capex()
    print("✅ test_microgrid_capex")
    
    test_full_scenario_moderate_heat()
    print("✅ test_full_scenario_moderate_heat")
    
    test_full_scenario_extreme_heat()
    print("✅ test_full_scenario_extreme_heat")
    
    test_zero_temp_anomaly()
    print("✅ test_zero_temp_anomaly")
    
    test_extreme_temperature_capping()
    print("✅ test_extreme_temperature_capping")
    
    test_small_facility_sizing()
    print("✅ test_small_facility_sizing")
    
    test_large_facility_sizing()
    print("✅ test_large_facility_sizing")
    
    test_rounding_precision()
    print("✅ test_rounding_precision")
    
    print("\n✅ All tests passed!")
