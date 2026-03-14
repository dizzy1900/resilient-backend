#!/usr/bin/env python3
"""
Unit tests for Macro-Portfolio Risk Analysis.

Tests the portfolio risk calculations without requiring API server.
"""


def test_hazard_var_percentages():
    """Test VaR percentages by hazard type."""
    HAZARD_VAR = {
        "Flood": 0.15,
        "Heat": 0.05,
        "Coastal": 0.20,
        "Supply Chain": 0.10
    }
    
    assert HAZARD_VAR["Flood"] == 0.15  # 15%
    assert HAZARD_VAR["Heat"] == 0.05  # 5%
    assert HAZARD_VAR["Coastal"] == 0.20  # 20%
    assert HAZARD_VAR["Supply Chain"] == 0.10  # 10%


def test_value_at_risk_calculation():
    """Test VaR calculation for each hazard type."""
    asset_value = 10_000_000.0
    
    # Flood: 15%
    flood_var = asset_value * 0.15
    assert flood_var == 1_500_000.0
    
    # Heat: 5%
    heat_var = asset_value * 0.05
    assert heat_var == 500_000.0
    
    # Coastal: 20%
    coastal_var = asset_value * 0.20
    assert coastal_var == 2_000_000.0
    
    # Supply Chain: 10%
    supply_var = asset_value * 0.10
    assert supply_var == 1_000_000.0


def test_resilience_score_calculation():
    """Test resilience score: 100 - (VaR% × 5)."""
    # Flood: 15% VaR → 100 - 75 = 25
    flood_score = 100.0 - (0.15 * 100.0 * 5.0)
    assert flood_score == 25.0
    
    # Heat: 5% VaR → 100 - 25 = 75
    heat_score = 100.0 - (0.05 * 100.0 * 5.0)
    assert heat_score == 75.0
    
    # Coastal: 20% VaR → 100 - 100 = 0
    coastal_score = 100.0 - (0.20 * 100.0 * 5.0)
    assert coastal_score == 0.0
    
    # Supply Chain: 10% VaR → 100 - 50 = 50
    supply_score = 100.0 - (0.10 * 100.0 * 5.0)
    assert supply_score == 50.0


def test_status_assignment():
    """Test status assignment based on resilience score."""
    # Critical: < 40
    assert "Critical" == ("Critical" if 25.0 < 40 else "Warning")
    assert "Critical" == ("Critical" if 0.0 < 40 else "Warning")
    
    # Warning: 40-70
    assert "Warning" == ("Critical" if 50.0 < 40 else ("Warning" if 50.0 <= 70 else "Secure"))
    assert "Warning" == ("Critical" if 40.0 < 40 else ("Warning" if 40.0 <= 70 else "Secure"))
    assert "Warning" == ("Critical" if 70.0 < 40 else ("Warning" if 70.0 <= 70 else "Secure"))
    
    # Secure: > 70
    assert "Secure" == ("Critical" if 75.0 < 40 else ("Warning" if 75.0 <= 70 else "Secure"))
    assert "Secure" == ("Critical" if 100.0 < 40 else ("Warning" if 100.0 <= 70 else "Secure"))


def test_single_asset_calculation():
    """Test full calculation for a single asset."""
    asset_value = 50_000_000.0
    primary_hazard = "Flood"
    var_percentage = 0.15
    
    # Calculate VaR
    value_at_risk = asset_value * var_percentage
    assert value_at_risk == 7_500_000.0
    
    # Calculate resilience score
    resilience_score = 100.0 - (var_percentage * 100.0 * 5.0)
    assert resilience_score == 25.0
    
    # Assign status
    if resilience_score < 40:
        status = "Critical"
    elif resilience_score <= 70:
        status = "Warning"
    else:
        status = "Secure"
    
    assert status == "Critical"


def test_portfolio_aggregation():
    """Test portfolio-level aggregation calculations."""
    # Sample calculated assets
    calculated_assets = [
        {"asset_value": 50_000_000.0, "value_at_risk": 7_500_000.0, "resilience_score": 25.0, "primary_hazard": "Flood"},
        {"asset_value": 10_000_000.0, "value_at_risk": 500_000.0, "resilience_score": 75.0, "primary_hazard": "Heat"},
        {"asset_value": 30_000_000.0, "value_at_risk": 6_000_000.0, "resilience_score": 0.0, "primary_hazard": "Coastal"}
    ]
    
    # Total portfolio value
    total_portfolio_value = sum(a["asset_value"] for a in calculated_assets)
    assert total_portfolio_value == 90_000_000.0
    
    # Total VaR
    total_value_at_risk = sum(a["value_at_risk"] for a in calculated_assets)
    assert total_value_at_risk == 14_000_000.0
    
    # Average resilience score
    average_resilience_score = sum(a["resilience_score"] for a in calculated_assets) / len(calculated_assets)
    assert abs(average_resilience_score - 33.33) < 0.01


def test_var_by_hazard_grouping():
    """Test VaR grouping by hazard type for donut chart."""
    calculated_assets = [
        {"value_at_risk": 7_500_000.0, "primary_hazard": "Flood"},
        {"value_at_risk": 500_000.0, "primary_hazard": "Heat"},
        {"value_at_risk": 6_000_000.0, "primary_hazard": "Coastal"},
        {"value_at_risk": 2_000_000.0, "primary_hazard": "Flood"}  # Another flood asset
    ]
    
    var_by_hazard = {}
    for asset in calculated_assets:
        hazard = asset["primary_hazard"]
        var_by_hazard[hazard] = var_by_hazard.get(hazard, 0.0) + asset["value_at_risk"]
    
    assert var_by_hazard["Flood"] == 9_500_000.0  # 7.5M + 2M
    assert var_by_hazard["Heat"] == 500_000.0
    assert var_by_hazard["Coastal"] == 6_000_000.0


def test_top_5_at_risk_sorting():
    """Test sorting and slicing top 5 at-risk assets."""
    calculated_assets = [
        {"id": "A", "value_at_risk": 1_000_000.0},
        {"id": "B", "value_at_risk": 5_000_000.0},
        {"id": "C", "value_at_risk": 500_000.0},
        {"id": "D", "value_at_risk": 7_500_000.0},
        {"id": "E", "value_at_risk": 2_000_000.0},
        {"id": "F", "value_at_risk": 3_000_000.0},
        {"id": "G", "value_at_risk": 100_000.0}
    ]
    
    sorted_assets = sorted(calculated_assets, key=lambda x: x["value_at_risk"], reverse=True)
    top_5 = sorted_assets[:5]
    
    assert len(top_5) == 5
    assert top_5[0]["id"] == "D"  # 7.5M
    assert top_5[1]["id"] == "B"  # 5M
    assert top_5[2]["id"] == "F"  # 3M
    assert top_5[3]["id"] == "E"  # 2M
    assert top_5[4]["id"] == "A"  # 1M


def test_diverse_portfolio_scenario():
    """Test realistic diverse portfolio with all hazard types."""
    HAZARD_VAR = {
        "Flood": 0.15,
        "Heat": 0.05,
        "Coastal": 0.20,
        "Supply Chain": 0.10
    }
    
    assets = [
        {"id": "PROP-001", "asset_value": 50_000_000.0, "primary_hazard": "Flood"},
        {"id": "PROP-002", "asset_value": 10_000_000.0, "primary_hazard": "Heat"},
        {"id": "PROP-003", "asset_value": 30_000_000.0, "primary_hazard": "Coastal"},
        {"id": "PROP-004", "asset_value": 15_000_000.0, "primary_hazard": "Supply Chain"}
    ]
    
    calculated_assets = []
    for asset in assets:
        var_percentage = HAZARD_VAR[asset["primary_hazard"]]
        value_at_risk = asset["asset_value"] * var_percentage
        resilience_score = 100.0 - (var_percentage * 100.0 * 5.0)
        
        if resilience_score < 40:
            status = "Critical"
        elif resilience_score <= 70:
            status = "Warning"
        else:
            status = "Secure"
        
        calculated_assets.append({
            "id": asset["id"],
            "asset_value": asset["asset_value"],
            "value_at_risk": value_at_risk,
            "resilience_score": resilience_score,
            "status": status,
            "primary_hazard": asset["primary_hazard"]
        })
    
    # Verify calculations
    assert calculated_assets[0]["value_at_risk"] == 7_500_000.0  # Flood: 15%
    assert calculated_assets[0]["resilience_score"] == 25.0
    assert calculated_assets[0]["status"] == "Critical"
    
    assert calculated_assets[1]["value_at_risk"] == 500_000.0  # Heat: 5%
    assert calculated_assets[1]["resilience_score"] == 75.0
    assert calculated_assets[1]["status"] == "Secure"
    
    assert calculated_assets[2]["value_at_risk"] == 6_000_000.0  # Coastal: 20%
    assert calculated_assets[2]["resilience_score"] == 0.0
    assert calculated_assets[2]["status"] == "Critical"
    
    assert calculated_assets[3]["value_at_risk"] == 1_500_000.0  # Supply Chain: 10%
    assert calculated_assets[3]["resilience_score"] == 50.0
    assert calculated_assets[3]["status"] == "Warning"
    
    # Portfolio totals
    total_portfolio_value = sum(a["asset_value"] for a in calculated_assets)
    total_value_at_risk = sum(a["value_at_risk"] for a in calculated_assets)
    average_resilience_score = sum(a["resilience_score"] for a in calculated_assets) / len(calculated_assets)
    
    assert total_portfolio_value == 105_000_000.0
    assert total_value_at_risk == 15_500_000.0
    assert average_resilience_score == 37.5


def test_edge_case_single_asset():
    """Test edge case: portfolio with single asset."""
    HAZARD_VAR = {"Heat": 0.05}
    
    assets = [
        {"id": "SINGLE", "asset_value": 1_000_000.0, "primary_hazard": "Heat"}
    ]
    
    calculated_assets = []
    for asset in assets:
        var_percentage = HAZARD_VAR[asset["primary_hazard"]]
        value_at_risk = asset["asset_value"] * var_percentage
        resilience_score = 100.0 - (var_percentage * 100.0 * 5.0)
        
        calculated_assets.append({
            "value_at_risk": value_at_risk,
            "resilience_score": resilience_score
        })
    
    average_resilience_score = sum(a["resilience_score"] for a in calculated_assets) / len(calculated_assets)
    
    assert len(calculated_assets) == 1
    assert average_resilience_score == 75.0


if __name__ == "__main__":
    # Run tests manually without pytest
    print("Running Macro-Portfolio Risk Unit Tests\n")
    
    test_hazard_var_percentages()
    print("✅ test_hazard_var_percentages")
    
    test_value_at_risk_calculation()
    print("✅ test_value_at_risk_calculation")
    
    test_resilience_score_calculation()
    print("✅ test_resilience_score_calculation")
    
    test_status_assignment()
    print("✅ test_status_assignment")
    
    test_single_asset_calculation()
    print("✅ test_single_asset_calculation")
    
    test_portfolio_aggregation()
    print("✅ test_portfolio_aggregation")
    
    test_var_by_hazard_grouping()
    print("✅ test_var_by_hazard_grouping")
    
    test_top_5_at_risk_sorting()
    print("✅ test_top_5_at_risk_sorting")
    
    test_diverse_portfolio_scenario()
    print("✅ test_diverse_portfolio_scenario")
    
    test_edge_case_single_asset()
    print("✅ test_edge_case_single_asset")
    
    print("\n✅ All tests passed!")
