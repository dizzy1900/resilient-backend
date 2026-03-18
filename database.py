"""Async SQLAlchemy database configuration.

Expects a PostgreSQL connection string via the DATABASE_URL environment
variable (e.g. from Supabase).  Falls back to SQLite for local development
when no URL is set.
"""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Default to SQLite for local dev if no URL is provided, but expect Postgres in prod
raw_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./resilient.db")

# If it's a standard postgresql:// URL from Supabase, convert it to the asyncpg driver
if raw_url.startswith("postgres://") or raw_url.startswith("postgresql://"):
    DATABASE_URL = raw_url.replace("postgres://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )
else:
    DATABASE_URL = raw_url

engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency that yields an async database session."""
    async with async_session() as session:
        yield session
