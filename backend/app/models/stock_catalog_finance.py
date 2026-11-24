"""Permanent stock identities and scoped financial evidence."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _issue_references(prefix: str) -> tuple[ForeignKeyConstraint, ForeignKeyConstraint]:
    return (
        ForeignKeyConstraint(
            ["catalog_id", "coin_id"],
            ["stock_catalog_instruments.catalog_id", "stock_catalog_instruments.coin_id"],
            name=f"fk_{prefix}_binding",
        ),
        ForeignKeyConstraint(
            ["listing_id", "catalog_id"],
            ["stock_catalog_listings.id", "stock_catalog_listings.security_id"],
            name=f"fk_{prefix}_listing",
        ),
    )


class StockCatalogInstrument(Base):
    __tablename__ = "stock_catalog_instruments"
    __table_args__ = (
        UniqueConstraint("catalog_id", "coin_id", name="uq_sc_instrument_catalog_coin"),
        ForeignKeyConstraint(
            ["listing_id", "catalog_id"],
            ["stock_catalog_listings.id", "stock_catalog_listings.security_id"],
            name="fk_sc_instrument_listing",
        ),
        CheckConstraint("isfinite(promoted_at)", name="promoted_finite"),
    )

    catalog_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    coin_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("stock_instruments.coin_id", name="fk_sc_instrument_coin"),
        unique=True,
    )
    listing_id: Mapped[int] = mapped_column(BigInteger)
    admission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_instrument_admission")
    )
    promoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StockCatalogFinancialQuote(Base):
    __tablename__ = "stock_catalog_financial_quotes"
    __table_args__ = (
        *_issue_references("sc_fin_quote"),
        CheckConstraint(
            "execution_admission_id IS NOT NULL OR mark_admission_id IS NOT NULL",
            name="scope",
        ),
        CheckConstraint(
            "length(provider_asset_id) >= 1 AND length(provider_asset_id) <= 128 "
            "AND source = 'alpaca' AND feed = 'iex'",
            name="provider",
        ),
        CheckConstraint("bid > 0 AND bid <= ask AND ask < 1e12", name="prices"),
        CheckConstraint(
            "unit_epoch >= 0 AND unit_epoch <= 9007199254740991 AND calendar_generation > 0",
            name="units",
        ),
        CheckConstraint(
            "isfinite(opens_at) AND opens_at <= event_at AND event_at < closes_at "
            "AND isfinite(closes_at) AND isfinite(session_date) "
            "AND event_at <= collected_at AND collected_at <= observed_at "
            "AND observed_at < valid_until AND isfinite(valid_until)",
            name="times",
        ),
        Index("ix_sc_fin_quotes_due", "observed_at", "coin_id"),
    )

    coin_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    catalog_id: Mapped[int] = mapped_column(BigInteger)
    listing_id: Mapped[int] = mapped_column(BigInteger)
    provider_asset_id: Mapped[str] = mapped_column(Text)
    provider_admission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_fin_quote_provider")
    )
    execution_admission_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_fin_quote_execution")
    )
    mark_admission_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_fin_quote_mark")
    )
    source: Mapped[str] = mapped_column(Text, server_default="alpaca")
    feed: Mapped[str] = mapped_column(Text, server_default="iex")
    bid: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    ask: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    unit_epoch: Mapped[int] = mapped_column(BigInteger)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    session_date: Mapped[date] = mapped_column(Date)
    calendar_generation: Mapped[int] = mapped_column(BigInteger)
    opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StockCatalogStatus(Base):
    __tablename__ = "stock_catalog_status"
    __table_args__ = (
        *_issue_references("sc_status"),
        CheckConstraint(
            "state IN ('normal', 'halted') AND report_digest ~ '^[a-f0-9]{64}$'",
            name="report",
        ),
        CheckConstraint(
            "isfinite(event_at) AND event_at <= observed_at AND observed_at < valid_until "
            "AND isfinite(valid_until) AND valid_until <= event_at + interval '120 seconds' "
            "AND isfinite(session_date)",
            name="times",
        ),
    )

    coin_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    catalog_id: Mapped[int] = mapped_column(BigInteger)
    listing_id: Mapped[int] = mapped_column(BigInteger)
    admission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_status_admission")
    )
    report_digest: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    session_date: Mapped[date] = mapped_column(Date)


class StockCatalogActionCoverage(Base):
    __tablename__ = "stock_catalog_action_coverage"
    __table_args__ = (
        *_issue_references("sc_action_coverage"),
        CheckConstraint(
            "(coverage_start IS NULL AND covered_until IS NULL) "
            "OR (coverage_start IS NOT NULL AND covered_until IS NOT NULL "
            "AND isfinite(coverage_start) AND coverage_start <= covered_until "
            "AND isfinite(covered_until))",
            name="window",
        ),
        CheckConstraint(
            "isfinite(journal_origin) AND isfinite(observed_at) AND journal_origin <= observed_at "
            "AND (valid_until IS NULL OR (isfinite(valid_until) AND observed_at < valid_until "
            "AND coverage_start IS NOT NULL AND coverage_start <= journal_origin "
            "AND journal_origin <= covered_until))",
            name="lease",
        ),
        CheckConstraint(
            "cursor IS NULL OR (length(cursor) >= 1 AND length(cursor) <= 4096)",
            name="cursor",
        ),
        Index("ix_sc_action_coverage_due", "valid_until", "coin_id"),
    )

    coin_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    catalog_id: Mapped[int] = mapped_column(BigInteger)
    listing_id: Mapped[int] = mapped_column(BigInteger)
    admission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("stock_catalog_admissions.id", name="fk_sc_action_coverage_admission"),
    )
    journal_origin: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    coverage_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    covered_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StockCatalogFillEvidence(Base):
    __tablename__ = "stock_catalog_fill_evidence"
    __table_args__ = (
        *_issue_references("sc_fill_evidence"),
        CheckConstraint(
            "unit_epoch >= 0 AND unit_epoch <= 9007199254740991 "
            "AND action_epoch > 0 AND action_epoch <= 9007199254740991",
            name="epochs",
        ),
        CheckConstraint(
            "report_digest ~ '^[a-f0-9]{64}$' AND isfinite(report_event_at) "
            "AND report_event_at < report_valid_until AND isfinite(report_valid_until) "
            "AND report_valid_until <= report_event_at + interval '120 seconds' "
            "AND isfinite(quote_valid_until)",
            name="report",
        ),
        Index("ix_sc_fill_evidence_coin", "coin_id"),
    )

    trade_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("stock_fill_facts.trade_id", name="fk_sc_fill_evidence_receipt"),
        primary_key=True,
    )
    coin_id: Mapped[int] = mapped_column(BigInteger)
    catalog_id: Mapped[int] = mapped_column(BigInteger)
    listing_id: Mapped[int] = mapped_column(BigInteger)
    provider_admission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_fill_evidence_provider")
    )
    execution_admission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_fill_evidence_execution")
    )
    halt_admission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_fill_evidence_halt")
    )
    action_admission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_catalog_admissions.id", name="fk_sc_fill_evidence_action")
    )
    unit_epoch: Mapped[int] = mapped_column(BigInteger)
    action_epoch: Mapped[int] = mapped_column(BigInteger)
    report_digest: Mapped[str] = mapped_column(Text)
    report_event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    report_valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quote_valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))
