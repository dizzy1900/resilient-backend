#!/usr/bin/env python3
"""FastAPI Simulation Service — AdaptMetric Climate Resilience Engine

Thin wrapper: creates the FastAPI app, configures CORS & startup events,
and includes all APIRouter modules from the routers/ package.

Run locally:
  uvicorn api:app --reload --port 8000

Or:
  python api.py
"""

from __future__ import annotations

import os
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from database import Base, engine

# Router imports
from routers.agriculture import router as agriculture_router
from routers.simulation import router as simulation_router
from routers.finance import router as finance_router
from routers.prediction import router as prediction_router
from routers.coastal import router as coastal_router
from routers.flood import router as flood_router
from routers.health import router as health_router
from routers.network import router as network_router
from routers.supply_chain import router as supply_chain_router
from routers.portfolio import router as portfolio_router
from routers.macro import router as macro_router
from routers.spatial import router as spatial_router
from routers.compliance import router as compliance_router
from routers.ai import router as ai_router
from routers.export import router as export_router
from routers.forecast import router as forecast_router

# Compliance loader (startup event)
from routers.compliance import load_industry_benchmarks

# ---------------------------------------------------------------------------
# App creation
# ---------------------------------------------------------------------------

app = FastAPI(title="AdaptMetric Simulation API", version="0.1.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://platform.resilient.global",
        "http://localhost:5173",  # Lovable's preview window
        "*",  # TODO: remove after debugging
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(agriculture_router)
app.include_router(simulation_router)
app.include_router(finance_router)
app.include_router(prediction_router)
app.include_router(coastal_router)
app.include_router(flood_router)
app.include_router(health_router)
app.include_router(network_router)
app.include_router(supply_chain_router)
app.include_router(portfolio_router)
app.include_router(macro_router)
app.include_router(spatial_router)
app.include_router(compliance_router)
app.include_router(ai_router)
app.include_router(export_router)
app.include_router(forecast_router)

# ---------------------------------------------------------------------------
# Startup events
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def _create_auth_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("startup")
async def _load_benchmark_data():
    """Load industry benchmark CSV data on application startup."""
    load_industry_benchmarks()


# ---------------------------------------------------------------------------
# Root / health-check endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health() -> dict:
    return {
        "status": "awake",
        "environment": "production",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/")
def root() -> dict:
    return {"message": "AdaptMetric Simulation API", "version": "0.1.0"}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
