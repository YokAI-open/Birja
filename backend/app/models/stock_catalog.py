"""Versioned stock discovery evidence, independent of the financial ledger."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class StockCatalogGeneration(Base):
    __tablename__ = "stock_catalog_generations"
    __table_args__ = (
        CheckConstraint("manifest_sha256 ~ '^[0-9a-f]{64}$'", name="digest"),
        CheckConstraint("mode IN ('fixture', 'live')", name="mode_known"),
        CheckConstraint(
            "isfinite(published_at) AND isfinite(valid_until) AND published_at < valid_until",
            name="validity",
        ),
        CheckConstraint(
            "jsonb_typeof(sources) = 'object' AND octet_length(sources::text) <= 8192",
            name="sources_bounded",
        ),
        CheckConstraint(
            "jsonb_typeof(coverage) = 'object' AND octet_length(coverage::text) <= 4096",
            name="coverage_bounded",
        ),
        Index(
            "uq_stock_catalog_generations_active",
            "is_active",
            unique=True,
            postgresql_where=text("is_active"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    manifest_sha256: Mapped[str] = mapped_column(Text, unique=True)
    mode: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=false())
    sources: Mapped[dict[str, Any]] = mapped_column(JSONB)
    coverage: Mapped[dict[str, Any]] = mapped_column(JSONB)


class StockCatalogSecurity(Base):
    __tablename__ = "stock_catalog_securities"
    __table_args__ = (
        CheckConstraint(
            "length(identity_key) >= 1 AND length(identity_key) <= 192 "
            "AND identity_key = btrim(identity_key)",
            name="identity_key",
        ),
        CheckConstraint("isfinite(created_at)", name="created_at_finite"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    identity_key: Mapped[str] = mapped_column(Text, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StockCatalogAdmission(Base):
    """Independent operator-reviewed authority used by the catalog publisher."""

    __tablename__ = "stock_catalog_admissions"
    __table_args__ = (
        CheckConstraint("artifact ~ '^[a-zA-Z0-9_.:-]{1,96}$'", name="artifact_key"),
        CheckConstraint(
            "length(reference) >= 1 AND length(reference) <= 2048 AND reference = btrim(reference)",
            name="reference_length",
        ),
        CheckConstraint(
            "isfinite(reviewed_at) AND isfinite(valid_until) AND reviewed_at < valid_until "
            "AND (revoked_at IS NULL OR (isfinite(revoked_at) AND reviewed_at <= revoked_at))",
            name="validity",
        ),
        CheckConstraint(
            "jsonb_typeof(fields) = 'object' AND octet_length(fields::text) <= 16384",
            name="fields_bounded",
        ),
        CheckConstraint(
            "jsonb_typeof(scope) = 'object' AND octet_length(scope::text) <= 16384",
            name="scope_bounded",
        ),
        Index("ix_stock_catalog_admissions_lookup", "artifact", "is_fixture", "valid_until"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    artifact: Mapped[str] = mapped_column(Text)
    reference: Mapped[str] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fields: Mapped[dict[str, Any]] = mapped_column(JSONB)
    scope: Mapped[dict[str, Any]] = mapped_column(JSONB)
    is_fixture: Mapped[bool] = mapped_column(Boolean, server_default=false())


class StockCatalogListing(Base):
    """A listing version tied to a stable share-class identity."""

    __tablename__ = "stock_catalog_listings"
    __table_args__ = (
        UniqueConstraint("generation_id", "security_id"),
        UniqueConstraint("id", "security_id"),
        CheckConstraint("listing_exchange IN ('NYSE', 'NASDAQ')", name="venue_known"),
        CheckConstraint(
            "source IN ('nasdaqlisted', 'otherlisted')"
            " OR (source = 'openfigi_nyse' AND listing_exchange = 'NYSE')",
            name="source_known",
        ),
        CheckConstraint("state IN ('active', 'review', 'retired')", name="state_known"),
        CheckConstraint(
            "classification IN ('common_stock', 'ordinary_shares', 'out_of_scope') "
            "OR classification IS NULL",
            name="classification_known",
        ),
        CheckConstraint(
            "state <> 'active' OR (classification IS NOT NULL "
            "AND classification IN ('common_stock', 'ordinary_shares') "
            "AND evidence_digest IS NOT NULL AND evidence_at IS NOT NULL)",
            name="active_evidence",
        ),
        CheckConstraint(
            "ticker ~ '^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$' AND normalized_ticker = ticker",
            name="ticker_shape",
        ),
        CheckConstraint(
            "length(company_name) >= 1 AND length(company_name) <= 256 "
            "AND length(normalized_name) BETWEEN 1 AND 512 "
            "AND (share_class IS NULL OR length(share_class) BETWEEN 1 AND 64)",
            name="name_bounds",
        ),
        CheckConstraint(
            "length(reason) >= 1 AND length(reason) <= 128 AND length(row_key) BETWEEN 1 AND 128 "
            "AND row_digest ~ '^[0-9a-f]{64}$'",
            name="source_shape",
        ),
        CheckConstraint(
            "isfinite(valid_until) AND ((evidence_digest IS NULL AND evidence_at IS NULL) "
            "OR (evidence_digest IS NOT NULL AND evidence_at IS NOT NULL "
            "AND evidence_digest ~ '^[0-9a-f]{64}$' AND isfinite(evidence_at) "
            "AND evidence_at < valid_until))",
            name="evidence_validity",
        ),
        CheckConstraint(
            "num_nonnulls(provider_asset_id, provider_symbol, provider_evidence_digest, "
            "provider_verified_at, provider_valid_until, provider_admission_id, "
            "unit_evidence_digest, unit_evidence_at, currency, units_per_share) = 0 OR ("
            "num_nonnulls(provider_asset_id, provider_symbol, provider_evidence_digest, "
            "provider_verified_at, provider_valid_until, provider_admission_id, "
            "unit_evidence_digest, unit_evidence_at, currency, units_per_share) = 10 "
            "AND state = 'active' AND length(provider_asset_id) BETWEEN 1 AND 128 "
            "AND provider_symbol ~ '^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$' "
            "AND provider_evidence_digest ~ '^[0-9a-f]{64}$' "
            "AND unit_evidence_digest ~ '^[0-9a-f]{64}$' "
            "AND isfinite(unit_evidence_at) AND isfinite(provider_verified_at) "
            "AND isfinite(provider_valid_until) AND unit_evidence_at <= provider_verified_at "
            "AND provider_verified_at < provider_valid_until "
            "AND provider_valid_until <= valid_until "
            "AND currency = 'USD' AND units_per_share = 1)",
            name="provider_mapping",
        ),
        Index(
            "uq_stock_catalog_listings_active_ticker",
            "generation_id",
            "listing_exchange",
            "normalized_ticker",
            unique=True,
            postgresql_where=text("state = 'active'"),
        ),
        Index(
            "uq_stock_catalog_listings_provider_asset",
            "generation_id",
            "provider_asset_id",
            unique=True,
            postgresql_where=text("provider_asset_id IS NOT NULL"),
        ),
        Index("ix_stock_catalog_listings_security", "security_id"),
        Index("ix_stock_catalog_listings_ticker", "generation_id", "normalized_ticker"),
        Index("ix_stock_catalog_listings_name", "generation_id", "normalized_name"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    generation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_generations.id")
    )
    security_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("stock_catalog_securities.id"))
    ticker: Mapped[str] = mapped_column(Text)
    normalized_ticker: Mapped[str] = mapped_column(Text)
    company_name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    listing_exchange: Mapped[str] = mapped_column(Text)
    share_class: Mapped[str | None] = mapped_column(Text)
    classification: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    row_key: Mapped[str] = mapped_column(Text)
    row_digest: Mapped[str] = mapped_column(Text)
    evidence_digest: Mapped[str | None] = mapped_column(Text)
    evidence_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    directory_admission_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id")
    )
    name_admission_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id")
    )
    classification_admission_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id")
    )
    provider_asset_id: Mapped[str | None] = mapped_column(Text)
    provider_symbol: Mapped[str | None] = mapped_column(Text)
    provider_evidence_digest: Mapped[str | None] = mapped_column(Text)
    provider_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    provider_admission_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id")
    )
    unit_evidence_digest: Mapped[str | None] = mapped_column(Text)
    unit_evidence_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    currency: Mapped[str | None] = mapped_column(Text)
    units_per_share: Mapped[int | None] = mapped_column(SmallInteger)


class StockCatalogAlias(Base):
    __tablename__ = "stock_catalog_aliases"
    __table_args__ = (
        ForeignKeyConstraint(
            ("listing_id", "security_id"),
            ("stock_catalog_listings.id", "stock_catalog_listings.security_id"),
        ),
        UniqueConstraint("listing_id", "namespace", "normalized_symbol"),
        CheckConstraint(
            "namespace IN ('act', 'cqs', 'nasdaq', 'openfigi', 'former')",
            name="namespace_known",
        ),
        CheckConstraint(
            "symbol ~ '^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$' AND symbol = normalized_symbol",
            name="symbol_shape",
        ),
        CheckConstraint(
            "isfinite(verified_at) AND isfinite(valid_until) AND verified_at < valid_until",
            name="validity",
        ),
        Index("ix_stock_catalog_aliases_symbol", "normalized_symbol"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    listing_id: Mapped[int] = mapped_column(BigInteger)
    security_id: Mapped[int] = mapped_column(BigInteger)
    namespace: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str] = mapped_column(Text)
    normalized_symbol: Mapped[str] = mapped_column(Text)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
