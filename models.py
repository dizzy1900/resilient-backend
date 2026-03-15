"""SQLAlchemy ORM models for the Auth Engine and Supply Chain Network."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class SupplyChainNode(Base):
    """Supply chain network node (supplier, manufacturer, port, distribution center)."""
    __tablename__ = "supply_chain_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    network_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    node_id: Mapped[str] = mapped_column(String(255), nullable=False)  # User-defined node identifier
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    node_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Supplier, Manufacturer, Port, Distribution
    baseline_status: Mapped[str] = mapped_column(String(50), default="Secure", nullable=False)  # Secure, Warning, Critical
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Unique constraint on network_id + node_id
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )


class SupplyChainEdge(Base):
    """Supply chain network edge (directed flow between nodes)."""
    __tablename__ = "supply_chain_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    network_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    source_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    target_node_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )
