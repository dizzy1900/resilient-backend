"""
Unit tests for the Commodity Price Shock Engine.

Tests the price shock calculation logic, elasticity modeling, and
recommendation generation for climate-induced supply disruptions.
"""

import pytest
from price_shock_engine import (
    calculate_price_shock,
    get_crop_info,
    get_all_crops,
    BASELINE_PRICES,
    SUPPLY_ELASTICITY,
)


class TestPriceShockCalculation:
    """Test core price shock calculation logic."""

    def test_maize_yield_loss_30_percent(self):
        """Test 30% yield loss in maize causes appropriate price shock."""
        result = calculate_price_shock(
            crop_type="maize",
            baseline_yield_tons=1000.0,
            stressed_yield_tons=700.0  # 30% loss
        )
        
        # Expected: 30% supply drop / 0.25 elasticity = 120% price increase
        assert result["yield_loss_pct"] == 30.0
        assert result["baseline_price"] == 180.0  # USD/ton
        
        # 120% increase: 180 * 2.2 = 396
        assert result["price_increase_pct"] == pytest.approx(120.0, rel=0.01)
        assert result["shocked_price"] == pytest.approx(396.0, rel=0.01)
        
        # Revenue impact: 700 tons * $396 = $277,200 vs baseline 1000 * $180 = $180,000
        # Net gain: $97,200 (price shock compensates for yield loss)
        assert result["revenue_impact"]["baseline_revenue_usd"] == 180000.0
        assert result["revenue_impact"]["stressed_revenue_usd"] == pytest.approx(277200.0, rel=0.01)
        assert result["revenue_impact"]["net_revenue_change_usd"] > 0  # Farmer benefits from price shock
        
        # Should recommend urgent forward contract
        assert "URGENT" in result["forward_contract_recommendation"]

    def test_wheat_moderate_yield_loss(self):
        """Test 10% yield loss in wheat."""
        result = calculate_price_shock(
            crop_type="wheat",
            baseline_yield_tons=500.0,
            stressed_yield_tons=450.0  # 10% loss
        )
        
        # 10% supply drop / 0.30 elasticity = 33.3% price increase
        assert result["yield_loss_pct"] == 10.0
        assert result["baseline_price"] == 220.0
        assert result["price_increase_pct"] == pytest.approx(33.33, rel=0.01)
        assert result["shocked_price"] == pytest.approx(293.33, rel=0.01)
        
        # Should recommend monitoring
        assert "MODERATE" in result["forward_contract_recommendation"] or "HIGH" in result["forward_contract_recommendation"]

    def test_soybeans_low_yield_loss(self):
        """Test 3% yield loss in soybeans (minimal impact)."""
        result = calculate_price_shock(
            crop_type="soybeans",
            baseline_yield_tons=800.0,
            stressed_yield_tons=776.0  # 3% loss
        )
        
        # 3% supply drop / 0.35 elasticity = 8.57% price increase
        assert result["yield_loss_pct"] == 3.0
        assert result["baseline_price"] == 450.0
        assert result["price_increase_pct"] == pytest.approx(8.57, rel=0.01)
        
        # Should recommend low risk / no action
        assert "LOW RISK" in result["forward_contract_recommendation"]

    def test_cocoa_highly_inelastic(self):
        """Test cocoa (highly inelastic, elasticity 0.15)."""
        result = calculate_price_shock(
            crop_type="cocoa",
            baseline_yield_tons=100.0,
            stressed_yield_tons=85.0  # 15% loss
        )
        
        # 15% supply drop / 0.15 elasticity = 100% price increase (doubles!)
        assert result["yield_loss_pct"] == 15.0
        assert result["baseline_price"] == 2500.0
        assert result["price_increase_pct"] == pytest.approx(100.0, rel=0.01)
        assert result["shocked_price"] == pytest.approx(5000.0, rel=0.01)
        
        # High yield loss should trigger urgent recommendation
        assert "HIGH RISK" in result["forward_contract_recommendation"] or "URGENT" in result["forward_contract_recommendation"]

    def test_rice_most_inelastic(self):
        """Test rice (most inelastic, elasticity 0.20)."""
        result = calculate_price_shock(
            crop_type="rice",
            baseline_yield_tons=2000.0,
            stressed_yield_tons=1800.0  # 10% loss
        )
        
        # 10% supply drop / 0.20 elasticity = 50% price increase
        assert result["yield_loss_pct"] == 10.0
        assert result["price_increase_pct"] == pytest.approx(50.0, rel=0.01)
        assert result["shocked_price"] == pytest.approx(675.0, rel=0.01)  # 450 * 1.5

    def test_zero_yield_loss(self):
        """Test scenario with no yield loss (prices unchanged)."""
        result = calculate_price_shock(
            crop_type="maize",
            baseline_yield_tons=1000.0,
            stressed_yield_tons=1000.0  # No loss
        )
        
        assert result["yield_loss_pct"] == 0.0
        assert result["price_increase_pct"] == 0.0
        assert result["shocked_price"] == result["baseline_price"]
        assert result["revenue_impact"]["net_revenue_change_usd"] == 0.0

    def test_complete_yield_failure(self):
        """Test complete crop failure (stressed yield = 0)."""
        result = calculate_price_shock(
            crop_type="maize",
            baseline_yield_tons=1000.0,
            stressed_yield_tons=0.0  # Total failure
        )
        
        # 100% supply drop / 0.25 elasticity = 400% price increase
        assert result["yield_loss_pct"] == 100.0
        assert result["price_increase_pct"] == pytest.approx(400.0, rel=0.01)
        assert result["shocked_price"] == pytest.approx(900.0, rel=0.01)  # 180 * 5
        
        # Revenue: 0 tons * any price = $0 (total loss despite price shock)
        assert result["revenue_impact"]["stressed_revenue_usd"] == 0.0
        assert result["revenue_impact"]["net_revenue_change_usd"] < 0

    def test_case_insensitive_crop_names(self):
        """Test that crop names are case-insensitive."""
        result1 = calculate_price_shock("MAIZE", 1000.0, 900.0)
        result2 = calculate_price_shock("maize", 1000.0, 900.0)
        result3 = calculate_price_shock("Maize", 1000.0, 900.0)
        
        assert result1["shocked_price"] == result2["shocked_price"] == result3["shocked_price"]

    def test_crop_aliases(self):
        """Test that crop aliases work (e.g., 'corn' = 'maize', 'soy' = 'soybeans')."""
        maize_result = calculate_price_shock("maize", 1000.0, 900.0)
        corn_result = calculate_price_shock("corn", 1000.0, 900.0)
        
        assert maize_result["baseline_price"] == corn_result["baseline_price"]
        assert maize_result["shocked_price"] == corn_result["shocked_price"]
        
        soy_result = calculate_price_shock("soy", 800.0, 750.0)
        soybeans_result = calculate_price_shock("soybeans", 800.0, 750.0)
        
        assert soy_result["baseline_price"] == soybeans_result["baseline_price"]


class TestInputValidation:
    """Test input validation and error handling."""

    def test_invalid_crop_type(self):
        """Test error handling for unsupported crop."""
        with pytest.raises(ValueError, match="not recognized"):
            calculate_price_shock(
                crop_type="banana",  # Not in our database
                baseline_yield_tons=1000.0,
                stressed_yield_tons=900.0
            )

    def test_negative_baseline_yield(self):
        """Test error handling for negative baseline yield."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_price_shock(
                crop_type="maize",
                baseline_yield_tons=-100.0,
                stressed_yield_tons=900.0
            )

    def test_negative_stressed_yield(self):
        """Test error handling for negative stressed yield."""
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_price_shock(
                crop_type="maize",
                baseline_yield_tons=1000.0,
                stressed_yield_tons=-50.0
            )

    def test_zero_baseline_yield(self):
        """Test error handling for zero baseline yield."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_price_shock(
                crop_type="maize",
                baseline_yield_tons=0.0,
                stressed_yield_tons=0.0
            )


class TestRevenueImpact:
    """Test revenue impact calculations."""

    def test_revenue_increase_despite_yield_loss(self):
        """Test that high price shock can increase revenue despite yield loss."""
        # 20% yield loss in maize (highly inelastic)
        result = calculate_price_shock(
            crop_type="maize",
            baseline_yield_tons=1000.0,
            stressed_yield_tons=800.0
        )
        
        # 20% supply drop / 0.25 elasticity = 80% price increase
        # Baseline: 1000 tons * $180 = $180,000
        # Stressed: 800 tons * $324 = $259,200
        # Net gain: $79,200
        assert result["revenue_impact"]["net_revenue_change_usd"] > 0
        assert result["revenue_impact"]["net_revenue_change_pct"] > 0

    def test_revenue_decrease_with_severe_loss(self):
        """Test that extreme yield loss reduces revenue even with price shock."""
        # 60% yield loss
        result = calculate_price_shock(
            crop_type="maize",
            baseline_yield_tons=1000.0,
            stressed_yield_tons=400.0
        )
        
        # 60% supply drop / 0.25 elasticity = 240% price increase
        # Baseline: 1000 tons * $180 = $180,000
        # Stressed: 400 tons * $612 = $244,800
        # Net gain: $64,800 (price shock still compensates!)
        # But with higher elasticity crops, this would be a loss
        
        # For potatoes (elasticity 0.60, more elastic):
        potato_result = calculate_price_shock(
            crop_type="potato",
            baseline_yield_tons=1000.0,
            stressed_yield_tons=400.0
        )
        
        # 60% supply drop / 0.60 elasticity = 100% price increase
        # Baseline: 1000 tons * $350 = $350,000
        # Stressed: 400 tons * $700 = $280,000
        # Net loss: -$70,000
        assert potato_result["revenue_impact"]["net_revenue_change_usd"] < 0


class TestRecommendations:
    """Test forward contract recommendation generation."""

    def test_urgent_recommendation(self):
        """Test urgent recommendation for severe yield loss (>30%)."""
        result = calculate_price_shock("maize", 1000.0, 600.0)  # 40% loss
        assert "URGENT" in result["forward_contract_recommendation"]
        assert "70-80%" in result["forward_contract_recommendation"]

    def test_high_risk_recommendation(self):
        """Test high risk recommendation for moderate-high yield loss (15-30%)."""
        result = calculate_price_shock("wheat", 1000.0, 800.0)  # 20% loss
        assert "HIGH RISK" in result["forward_contract_recommendation"]
        assert "50-60%" in result["forward_contract_recommendation"]

    def test_moderate_risk_recommendation(self):
        """Test moderate risk recommendation for low-moderate yield loss (5-15%)."""
        result = calculate_price_shock("soybeans", 1000.0, 920.0)  # 8% loss
        assert "MODERATE RISK" in result["forward_contract_recommendation"]
        assert "30-40%" in result["forward_contract_recommendation"]

    def test_low_risk_recommendation(self):
        """Test low risk recommendation for minimal yield loss (<5%)."""
        result = calculate_price_shock("maize", 1000.0, 970.0)  # 3% loss
        assert "LOW RISK" in result["forward_contract_recommendation"]
        assert "No immediate hedging" in result["forward_contract_recommendation"]


class TestCropInfo:
    """Test crop information utility functions."""

    def test_get_crop_info(self):
        """Test retrieval of crop price and elasticity info."""
        info = get_crop_info("maize")
        
        assert info["crop_type"] == "maize"
        assert info["baseline_price_usd_per_ton"] == 180.0
        assert info["supply_elasticity"] == 0.25
        assert "elasticity_interpretation" in info

    def test_get_all_crops(self):
        """Test retrieval of all crop information."""
        all_crops = get_all_crops()
        
        assert len(all_crops) == len(BASELINE_PRICES)
        assert "maize" in all_crops
        assert "wheat" in all_crops
        assert "cocoa" in all_crops
        
        # Verify structure
        for crop, info in all_crops.items():
            assert "baseline_price_usd_per_ton" in info
            assert "supply_elasticity" in info

    def test_invalid_crop_info(self):
        """Test error handling for invalid crop in get_crop_info."""
        with pytest.raises(ValueError, match="not recognized"):
            get_crop_info("invalid_crop")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_yield_loss(self):
        """Test handling of very small yield losses (<0.1%)."""
        result = calculate_price_shock(
            crop_type="maize",
            baseline_yield_tons=10000.0,
            stressed_yield_tons=9999.0  # 0.01% loss
        )
        
        assert result["yield_loss_pct"] == pytest.approx(0.01, rel=0.01)
        assert result["price_increase_pct"] < 0.1

    def test_yield_increase(self):
        """Test scenario where stressed yield exceeds baseline (negative loss)."""
        result = calculate_price_shock(
            crop_type="maize",
            baseline_yield_tons=1000.0,
            stressed_yield_tons=1200.0  # 20% gain
        )
        
        # Should show negative yield loss (i.e., yield gain)
        assert result["yield_loss_pct"] == -20.0
        
        # Price should decrease (negative price change)
        assert result["price_increase_pct"] < 0
        assert result["shocked_price"] < result["baseline_price"]

    def test_large_baseline_yield(self):
        """Test with very large baseline yield (millions of tons)."""
        result = calculate_price_shock(
            crop_type="wheat",
            baseline_yield_tons=10_000_000.0,
            stressed_yield_tons=9_000_000.0  # 10% loss
        )
        
        assert result["yield_loss_pct"] == 10.0
        assert result["yield_loss_tons"] == 1_000_000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
