"""Network endpoints — route risk and grid resilience."""

from __future__ import annotations

from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/network", tags=["Network"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class RouteRiskRequest(BaseModel):
    route_geojson: Dict[str, Any] = Field(..., description="GeoJSON LineString geometry representing the truck route")
    cargo_value: float = Field(100000.0, description="Value of cargo in USD")


class RouteRiskResponse(BaseModel):
    flooded_miles: float
    detour_delay_hours: float
    freight_delay_cost: float
    spoilage_cost: float
    total_value_at_risk: float
    intervention_capex: float


class GridRiskRequest(BaseModel):
    facility_sqft: float = Field(50000.0, gt=0)
    baseline_temp_c: float = Field(25.0)
    projected_temp_c: float = Field(35.0)


class GridRiskResponse(BaseModel):
    temp_anomaly: float
    hvac_spike_pct: float
    downtime_loss: float
    required_solar_kw: float
    required_bess_kwh: float
    microgrid_capex: float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def calculate_flooded_miles(geojson: Dict[str, Any]) -> float:
    """Mock/placeholder for GEE flood hazard analysis."""
    return 2.5


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/route-risk", response_model=RouteRiskResponse)
def calculate_route_risk(req: RouteRiskRequest) -> dict:
    """Calculate economic risk for truck routes intersecting flood zones."""
    try:
        if req.route_geojson.get("type") != "LineString":
            raise HTTPException(status_code=400, detail="Invalid GeoJSON: Expected LineString geometry")

        coordinates = req.route_geojson.get("coordinates")
        if not coordinates or len(coordinates) < 2:
            raise HTTPException(status_code=400, detail="Invalid LineString: Must have at least 2 coordinate pairs")

        flooded_miles = calculate_flooded_miles(req.route_geojson)

        detour_delay_hours = flooded_miles * 0.5
        freight_delay_cost = detour_delay_hours * 91.27
        spoilage_cost = req.cargo_value * 0.20 * (detour_delay_hours / 24.0)
        total_value_at_risk = freight_delay_cost + spoilage_cost
        intervention_capex = flooded_miles * 5_000_000.0

        return {
            "flooded_miles": round(flooded_miles, 2),
            "detour_delay_hours": round(detour_delay_hours, 2),
            "freight_delay_cost": round(freight_delay_cost, 2),
            "spoilage_cost": round(spoilage_cost, 2),
            "total_value_at_risk": round(total_value_at_risk, 2),
            "intervention_capex": round(intervention_capex, 2),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route risk analysis failed: {str(e)}") from e


@router.post("/grid-resilience", response_model=GridRiskResponse)
def calculate_grid_resilience(req: GridRiskRequest) -> dict:
    """Calculate energy grid brownout risk and microgrid sizing for heatwaves."""
    try:
        temp_anomaly = req.projected_temp_c - req.baseline_temp_c
        hvac_spike_pct = temp_anomaly * 3.0
        grid_failure_probability = min((hvac_spike_pct / 100.0) * 1.5, 1.0)
        expected_downtime_hours = grid_failure_probability * 12.0
        downtime_loss = expected_downtime_hours * 25000.0

        required_solar_kw = req.facility_sqft * 0.01
        required_bess_kwh = required_solar_kw * 4.0
        solar_cost = required_solar_kw * 1780.0
        bess_cost = required_bess_kwh * 400.0
        microgrid_capex = solar_cost + bess_cost

        return {
            "temp_anomaly": round(temp_anomaly, 2),
            "hvac_spike_pct": round(hvac_spike_pct, 2),
            "downtime_loss": round(downtime_loss, 2),
            "required_solar_kw": round(required_solar_kw, 2),
            "required_bess_kwh": round(required_bess_kwh, 2),
            "microgrid_capex": round(microgrid_capex, 2),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grid resilience analysis failed: {str(e)}") from e
