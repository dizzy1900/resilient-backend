#!/usr/bin/env python3
"""
Initialize database tables for Supply Chain Network.

This script creates the supply_chain_nodes and supply_chain_edges tables.
Run this once before using the supply chain endpoints.

Usage:
    python3 init_supply_chain_db.py
"""

import asyncio
from database import engine, Base
from models import SupplyChainNode, SupplyChainEdge, User


async def init_db():
    """Create all tables."""
    print("Creating database tables...")
    
    async with engine.begin() as conn:
        # Create all tables defined in Base metadata
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database tables created successfully:")
    print("  - supply_chain_nodes")
    print("  - supply_chain_edges")
    print("  - users")
    print("\nYou can now use the supply chain endpoints:")
    print("  POST /api/v1/supply-chain/upload")
    print("  POST /api/v1/supply-chain/simulate-cascade")


if __name__ == "__main__":
    asyncio.run(init_db())
