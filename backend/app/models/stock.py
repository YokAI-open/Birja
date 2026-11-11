"""Stock discovery storage; runtime sessions carry no review authority."""

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
    Identity,
    Numeric,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StockInstrument(Base):
    __tablename__ = "stock_instruments"
    __table_args__ = (
        CheckConstraint("listing_exchange IN ('NYSE', 'NASDAQ')", name="exchange_known"),
        CheckConstraint("currency = 'USD'", name="usd_only"),
        CheckConstraint("security_type = 'common_stock'", name="common_stock_only"),
        CheckConstraint("length(source) BETWEEN 1 AND 64", name="source_length"),
        CheckConstraint("length(source_ref) BETWEEN 1 AND 2048", name="source_ref_length"),
        CheckConstraint(
            "provider_asset_id IS NULL OR length(provider_asset_id) BETWEEN 1 AND 128",
            name="provider_id_length",
        ),
        CheckConstraint(
            "provider_verified_at IS NULL OR provider_asset_id IS NOT NULL",
            name="verification_identity",
        ),
    )

    coin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("coins.id"), primary_key=True)
    provider_asset_id: Mapped[str | None] = mapped_column(Text, unique=True)
    provider_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    listing_exchange: Mapped[str] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(Text, server_default="USD")
    security_type: Mapped[str] = mapped_column(Text, server_default="common_stock")
    source: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(Text)


class StockQuote(Base):
    __tablename__ = "stock_quotes"
    __table_args__ = (
        CheckConstraint(
            "bid > 0 AND bid < 'Infinity'::numeric AND "
            "ask > 0 AND ask < 'Infinity'::numeric AND mid > 0 AND mid < 'Infinity'::numeric",
            name="finite_positive",
        ),
        CheckConstraint(
            "bid <= ask AND mid = trunc((bid + ask) / 2, 8) + CASE WHEN "
            "mod((bid + ask) * 50000000, 1) = 0.5 AND "
            "mod(trunc((bid + ask) * 50000000), 2) = 1 "
            "THEN 0.00000001 ELSE 0 END",
            name="spread_mid",
        ),
        CheckConstraint("source = 'alpaca' AND feed = 'iex'", name="source_feed"),
        CheckConstraint("event_at <= collected_at", name="event_not_future"),
        CheckConstraint("admission_generation > 0", name="generation_positive"),
        CheckConstraint("unit_epoch BETWEEN 0 AND 9007199254740991", name="unit_epoch_safe"),
    )

    coin_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_instruments.coin_id"), primary_key=True
    )
    bid: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    ask: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    mid: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    source: Mapped[str] = mapped_column(Text)
    feed: Mapped[str] = mapped_column(Text)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    session_date: Mapped[date] = mapped_column(Date)
    admission_generation: Mapped[int] = mapped_column(BigInteger)
    unit_epoch: Mapped[int] = mapped_column(BigInteger, server_default="0")


class StockSession(Base):
    __tablename__ = "stock_sessions"
    __table_args__ = (
        UniqueConstraint("exchange", "session_date", name="uq_stock_sessions_exchange_date"),
        CheckConstraint("exchange IN ('NYSE', 'NASDAQ')", name="exchange_known"),
        CheckConstraint(
            "(opens_at IS NULL AND closes_at IS NULL) OR (opens_at IS NOT NULL AND "
            "closes_at IS NOT NULL AND opens_at < closes_at AND "
            "closes_at - opens_at <= interval '1 day')",
            name="boundaries",
        ),
        CheckConstraint(
            "coverage_start <= session_date AND session_date <= coverage_end AND "
            "coverage_end - coverage_start <= 135",
            name="coverage",
        ),
        CheckConstraint("calendar_admission_generation > 0", name="generation_positive"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    exchange: Mapped[str] = mapped_column(Text)
    session_date: Mapped[date] = mapped_column(Date)
    opens_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closes_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    coverage_start: Mapped[date] = mapped_column(Date)
    coverage_end: Mapped[date] = mapped_column(Date)
    calendar_admission_generation: Mapped[int] = mapped_column(BigInteger)


class StockDataAdmission(Base):
    """Only migration-owner administration may establish or renew this evidence.

    Calendar JSON retains official scope/source/version, review_valid_until,
    coverage dates and exceptional overrides. Plan 07-05 validates its exact
    semantic shape; JSON size/type constraints bound stored evidence here.
    """

    __tablename__ = "stock_data_admissions"
    __table_args__ = (
        CheckConstraint(
            "product IN ('reference', 'quotes', 'actions', 'status', 'calendar')",
            name="product_known",
        ),
        CheckConstraint("state IN ('denied', 'approved', 'revoked')", name="state_known"),
        CheckConstraint("generation > 0", name="generation_positive"),
        CheckConstraint(
            "valid_from IS NULL OR valid_until IS NULL OR valid_from < valid_until", name="validity"
        ),
        CheckConstraint(
            "state <> 'approved' OR (reviewed_at IS NOT NULL AND valid_from IS NOT NULL "
            "AND valid_until IS NOT NULL AND evidence_ref IS NOT NULL "
            "AND terms_version IS NOT NULL)",
            name="approved_evidence",
        ),
        CheckConstraint(
            "evidence_ref IS NULL OR length(evidence_ref) BETWEEN 1 AND 2048",
            name="evidence_ref_length",
        ),
        CheckConstraint(
            "terms_version IS NULL OR length(terms_version) BETWEEN 1 AND 256",
            name="terms_version_length",
        ),
        CheckConstraint("length(attribution) <= 2048", name="attribution_length"),
        CheckConstraint(
            "jsonb_typeof(scope) = 'object' AND octet_length(scope::text) <= 16384",
            name="scope_bounded",
        ),
        CheckConstraint(
            "jsonb_typeof(quota) = 'object' AND octet_length(quota::text) <= 4096",
            name="quota_bounded",
        ),
        CheckConstraint(
            "jsonb_typeof(allowed_fields) = 'array' AND octet_length(allowed_fields::text) <= 4096",
            name="fields_bounded",
        ),
        CheckConstraint(
            "jsonb_typeof(calendar) = 'object' AND octet_length(calendar::text) <= 32768",
            name="calendar_bounded",
        ),
        CheckConstraint(
            "product = 'calendar' OR calendar = '{}'::jsonb", name="calendar_product_only"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    product: Mapped[str] = mapped_column(Text, unique=True)
    state: Mapped[str] = mapped_column(Text, server_default="denied")
    generation: Mapped[int] = mapped_column(BigInteger, server_default="1")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evidence_ref: Mapped[str | None] = mapped_column(Text)
    terms_version: Mapped[str | None] = mapped_column(Text)
    collection_allowed: Mapped[bool] = mapped_column(Boolean, server_default=false())
    display_allowed: Mapped[bool] = mapped_column(Boolean, server_default=false())
    derived_allowed: Mapped[bool] = mapped_column(Boolean, server_default=false())
    retention_allowed: Mapped[bool] = mapped_column(Boolean, server_default=false())
    scope: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    quota: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    allowed_fields: Mapped[list[str]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    attribution: Mapped[str] = mapped_column(Text, server_default="")
    calendar: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
