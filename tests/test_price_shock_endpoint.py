"""
Integration tests for the /api/v1/finance/price-shock endpoint.

Tests the FastAPI endpoint for commodity price shock calculations.
"""

import pytest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


class TestPriceShockEndpoint:
    """Test the POST /api/v1/finance/price-shock endpoint."""

    def test_successful_price_shock_calculation(self):
        """Test successful price shock calculation with valid inputs."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 700.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "baseline_price" in data
        assert "shocked_price" in data
        assert "price_increase_pct" in data
        assert "price_increase_usd" in data
        assert "yield_loss_pct" in data
        assert "yield_loss_tons" in data
        assert "elasticity" in data
        assert "forward_contract_recommendation" in data
        assert "revenue_impact" in data
        
        # Verify values
        assert data["baseline_price"] == 180.0
        assert data["yield_loss_pct"] == 30.0
        assert data["elasticity"] == 0.25
        assert data["shocked_price"] > data["baseline_price"]
        assert data["price_increase_pct"] > 0

    def test_multiple_crop_types(self):
        """Test price shock for different crop types."""
        crops = ["maize", "wheat", "soybeans", "rice", "cocoa", "coffee"]
        
        for crop in crops:
            response = client.post(
                "/api/v1/finance/price-shock",
                json={
                    "crop_type": crop,
                    "baseline_yield_tons": 1000.0,
                    "stressed_yield_tons": 900.0
                }
            )
            
            assert response.status_code == 200, f"Failed for crop: {crop}"
            data = response.json()
            assert data["baseline_price"] > 0
            assert data["elasticity"] > 0

    def test_severe_yield_loss(self):
        """Test severe yield loss (40%) triggers urgent recommendation."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 600.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["yield_loss_pct"] == 40.0
        assert "URGENT" in data["forward_contract_recommendation"]
        assert "70-80%" in data["forward_contract_recommendation"]

    def test_moderate_yield_loss(self):
        """Test moderate yield loss (10%) triggers appropriate recommendation."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "wheat",
                "baseline_yield_tons": 500.0,
                "stressed_yield_tons": 450.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["yield_loss_pct"] == 10.0
        assert "RISK" in data["forward_contract_recommendation"]

    def test_minimal_yield_loss(self):
        """Test minimal yield loss (<5%) triggers low risk recommendation."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "soybeans",
                "baseline_yield_tons": 800.0,
                "stressed_yield_tons": 776.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["yield_loss_pct"] == 3.0
        assert "LOW RISK" in data["forward_contract_recommendation"]

    def test_zero_yield_loss(self):
        """Test scenario with no yield loss (prices unchanged)."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 1000.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["yield_loss_pct"] == 0.0
        assert data["price_increase_pct"] == 0.0
        assert data["shocked_price"] == data["baseline_price"]

    def test_complete_crop_failure(self):
        """Test complete crop failure (stressed yield = 0)."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "rice",
                "baseline_yield_tons": 2000.0,
                "stressed_yield_tons": 0.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["yield_loss_pct"] == 100.0
        assert data["revenue_impact"]["stressed_revenue_usd"] == 0.0
        assert data["revenue_impact"]["net_revenue_change_usd"] < 0

    def test_revenue_impact_calculation(self):
        """Test that revenue impact is calculated correctly."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 800.0
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        revenue = data["revenue_impact"]
        assert "baseline_revenue_usd" in revenue
        assert "stressed_revenue_usd" in revenue
        assert "net_revenue_change_usd" in revenue
        assert "net_revenue_change_pct" in revenue
        
        # Verify calculation
        baseline_revenue = 1000.0 * data["baseline_price"]
        stressed_revenue = 800.0 * data["shocked_price"]
        
        assert revenue["baseline_revenue_usd"] == pytest.approx(baseline_revenue, rel=0.01)
        assert revenue["stressed_revenue_usd"] == pytest.approx(stressed_revenue, rel=0.01)

    def test_case_insensitive_crop_names(self):
        """Test that crop names are case-insensitive."""
        test_cases = ["maize", "MAIZE", "Maize", "MaIzE"]
        
        results = []
        for crop_name in test_cases:
            response = client.post(
                "/api/v1/finance/price-shock",
                json={
                    "crop_type": crop_name,
                    "baseline_yield_tons": 1000.0,
                    "stressed_yield_tons": 900.0
                }
            )
            assert response.status_code == 200
            results.append(response.json())
        
        # All should return same shocked price
        shocked_prices = [r["shocked_price"] for r in results]
        assert len(set(shocked_prices)) == 1

    def test_crop_aliases(self):
        """Test that crop aliases work correctly."""
        # Test maize/corn alias
        maize_response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 900.0
            }
        )
        
        corn_response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "corn",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 900.0
            }
        )
        
        assert maize_response.status_code == 200
        assert corn_response.status_code == 200
        assert maize_response.json()["shocked_price"] == corn_response.json()["shocked_price"]

    def test_invalid_crop_type(self):
        """Test error handling for invalid crop type."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "banana",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 900.0
            }
        )
        
        assert response.status_code == 400
        assert "not recognized" in response.json()["detail"].lower()

    def test_negative_baseline_yield(self):
        """Test error handling for negative baseline yield."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": -100.0,
                "stressed_yield_tons": 900.0
            }
        )
        
        assert response.status_code == 422  # Pydantic validation error (gt=0)

    def test_negative_stressed_yield(self):
        """Test error handling for negative stressed yield."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": -50.0
            }
        )
        
        assert response.status_code == 422  # Pydantic validation error (ge=0)

    def test_zero_baseline_yield(self):
        """Test error handling for zero baseline yield."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 0.0,
                "stressed_yield_tons": 0.0
            }
        )
        
        assert response.status_code == 422  # Pydantic validation error (gt=0)

    def test_missing_required_fields(self):
        """Test error handling for missing required fields."""
        # Missing crop_type
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 900.0
            }
        )
        assert response.status_code == 422
        
        # Missing baseline_yield_tons
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "stressed_yield_tons": 900.0
            }
        )
        assert response.status_code == 422
        
        # Missing stressed_yield_tons
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 1000.0
            }
        )
        assert response.status_code == 422

    def test_large_scale_commercial_farm(self):
        """Test with large-scale commercial farm yields (thousands of tons)."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "wheat",
                "baseline_yield_tons": 50000.0,
                "stressed_yield_tons": 42000.0  # 16% loss
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["yield_loss_pct"] == 16.0
        assert data["yield_loss_tons"] == 8000.0
        assert data["revenue_impact"]["baseline_revenue_usd"] > 10_000_000  # Over $10M

    def test_smallholder_farmer(self):
        """Test with smallholder farmer yields (small tonnage)."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "maize",
                "baseline_yield_tons": 5.0,
                "stressed_yield_tons": 3.5  # 30% loss
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["yield_loss_pct"] == 30.0
        assert data["yield_loss_tons"] == 1.5

    def test_highly_inelastic_crop(self):
        """Test highly inelastic crop (cocoa, elasticity 0.15)."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "cocoa",
                "baseline_yield_tons": 100.0,
                "stressed_yield_tons": 90.0  # 10% loss
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["elasticity"] == 0.15
        # 10% supply drop / 0.15 elasticity = 66.7% price increase
        assert data["price_increase_pct"] == pytest.approx(66.67, rel=0.01)

    def test_more_elastic_crop(self):
        """Test more elastic crop (potato, elasticity 0.60)."""
        response = client.post(
            "/api/v1/finance/price-shock",
            json={
                "crop_type": "potato",
                "baseline_yield_tons": 1000.0,
                "stressed_yield_tons": 900.0  # 10% loss
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["elasticity"] == 0.60
        # 10% supply drop / 0.60 elasticity = 16.7% price increase
        assert data["price_increase_pct"] == pytest.approx(16.67, rel=0.01)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
