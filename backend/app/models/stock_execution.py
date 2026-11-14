"""Immutable stock receipts and independently leased status evidence."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    Text,
    false,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.corporate_action import bounded, object_json, safe


class StockFillFacts(Base):
    __tablename__ = "stock_fill_facts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["trade_id", "coin_id", "user_id"],
            ["trades.id", "trades.coin_id", "trades.user_id"],
            name="fk_stock_fill_trade_owner_coin",
        ),
        Index("ix_stock_fill_facts_user_id", "user_id"),
        Index("ix_stock_fill_facts_coin_id", "coin_id"),
        bounded("provider_asset_id", 128),
        bounded("symbol", 32),
        bounded("company_name", 256),
        CheckConstraint("listing_exchange IN ('NYSE','NASDAQ')", name="exchange_known"),
        CheckConstraint("source='alpaca' AND feed='iex'", name="source_feed"),
        CheckConstraint("schema_version=1", name="version_known"),
        CheckConstraint("bid>0 AND bid<1e12 AND ask>=bid AND ask<1e12", name="prices_finite"),
        CheckConstraint("exact_mid=(bid+ask)/2", name="exact_mid"),
        CheckConstraint(
            "held_after>=0 AND held_after<1e12 AND held_after=trunc(held_after)", name="whole_after"
        ),
        CheckConstraint(
            "event_at<=collected_at AND collected_at<=observed_at "
            "AND opens_at<=event_at AND event_at<closes_at AND opens_at<closes_at",
            name="source_times",
        ),
        object_json("authority", 8192),
    )
    trade_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey("stock_instruments.coin_id"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    provider_asset_id: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str] = mapped_column(Text)
    company_name: Mapped[str] = mapped_column(Text)
    listing_exchange: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    feed: Mapped[str] = mapped_column(Text)
    bid: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    ask: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    exact_mid: Mapped[Decimal] = mapped_column(Numeric(21, 9))
    held_after: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    session_date: Mapped[date] = mapped_column(Date)
    opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    authority: Mapped[dict[str, Any]] = mapped_column(JSONB)
    schema_version: Mapped[int] = mapped_column(BigInteger, server_default="1")


class StockStatusEvidence(Base):
    __tablename__ = "stock_status_evidence"
    __table_args__ = (
        bounded("provider_asset_id", 128),
        bounded("source_ref", 2048),
        CheckConstraint("state IN ('normal','halted','frozen','unknown')", name="state_known"),
        CheckConstraint("source='alpaca'", name="source_known"),
        safe("admission_generation"),
        safe("continuity_generation"),
        safe("sequence"),
        CheckConstraint(
            "event_at IS NULL OR observed_at IS NULL OR event_at<=observed_at", name="event_order"
        ),
        CheckConstraint(
            "valid_until IS NULL OR (observed_at IS NOT NULL AND observed_at<valid_until "
            "AND valid_until<=observed_at+interval '60 seconds')",
            name="lease_bound",
        ),
        CheckConstraint(
            "NOT continuity_current OR (bootstrap_verified AND valid_until IS NOT NULL "
            "AND event_at IS NOT NULL AND session_date IS NOT NULL "
            "AND admission_generation>0 AND continuity_generation>0)",
            name="verified_continuity",
        ),
    )
    coin_id: Mapped[int] = mapped_column(ForeignKey("stock_instruments.coin_id"), primary_key=True)
    provider_asset_id: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text, server_default="unknown")
    event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    session_date: Mapped[date | None] = mapped_column(Date)
    admission_generation: Mapped[int] = mapped_column(BigInteger, server_default="0")
    continuity_generation: Mapped[int] = mapped_column(BigInteger, server_default="0")
    sequence: Mapped[int] = mapped_column(BigInteger, server_default="0")
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bootstrap_verified: Mapped[bool] = mapped_column(Boolean, server_default=false())
    continuity_current: Mapped[bool] = mapped_column(Boolean, server_default=false())
    source: Mapped[str] = mapped_column(Text, server_default="alpaca")
    source_ref: Mapped[str] = mapped_column(Text)
