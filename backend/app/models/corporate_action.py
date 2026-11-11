"""Durable corporate-action identity and append-only economic accounting.

These records establish neither provider permission nor executable stock orders.
Runtime immutability is enforced by migration-owned SQL privileges.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def safe(column: str, *, positive: bool = False) -> CheckConstraint:
    return CheckConstraint(
        f"{column} BETWEEN {1 if positive else 0} AND 9007199254740991",
        name=f"{column}_safe",
    )


def bounded(column: str, limit: int = 256) -> CheckConstraint:
    return CheckConstraint(f"length({column}) BETWEEN 1 AND {limit}", name=f"{column}_length")


def object_json(column: str, limit: int = 16384) -> CheckConstraint:
    return CheckConstraint(
        f"jsonb_typeof({column}) = 'object' AND octet_length({column}::text) <= {limit}",
        name=f"{column}_bounded",
    )


class StockActionEvent(Base):
    __tablename__ = "stock_action_events"
    __table_args__ = (
        UniqueConstraint("id", "coin_id", name="uq_stock_action_events_id_coin"),
        CheckConstraint(
            "economic_key ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'",
            name="economic_identity",
        ),
        ForeignKeyConstraint(
            ["current_revision_id", "id"],
            ["stock_action_revisions.id", "stock_action_revisions.event_id"],
            name="fk_stock_action_events_current_revision",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
        ),
        Index("ix_stock_action_events_current_revision_id", "current_revision_id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey("stock_instruments.coin_id"), index=True)
    economic_key: Mapped[str] = mapped_column(Text, unique=True)
    current_revision_id: Mapped[int | None] = mapped_column(BigInteger)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StockActionSource(Base):
    __tablename__ = "stock_action_sources"
    __table_args__ = (
        UniqueConstraint(
            "provider", "product", "provider_event_id", name="uq_stock_action_source_identity"
        ),
        UniqueConstraint("id", "event_id", name="uq_stock_action_sources_id_event"),
        bounded("provider", 64),
        bounded("product", 64),
        bounded("provider_event_id", 256),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("stock_action_events.id"), index=True)
    provider: Mapped[str] = mapped_column(Text)
    product: Mapped[str] = mapped_column(Text)
    provider_event_id: Mapped[str] = mapped_column(Text)


class StockActionRevision(Base):
    __tablename__ = "stock_action_revisions"
    __table_args__ = (
        UniqueConstraint("event_id", "ordinal", name="uq_stock_action_revision_ordinal"),
        UniqueConstraint("event_id", "fingerprint", name="uq_stock_action_revision_fingerprint"),
        UniqueConstraint("id", "event_id", name="uq_stock_action_revisions_id_event"),
        UniqueConstraint("id", "source_id", name="uq_stock_action_revisions_id_source"),
        ForeignKeyConstraint(
            ["source_id", "event_id"],
            ["stock_action_sources.id", "stock_action_sources.event_id"],
            name="fk_stock_action_revision_source_event",
        ),
        Index("ix_stock_action_revisions_source_id", "source_id"),
        safe("ordinal", positive=True),
        safe("admission_generation", positive=True),
        CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint_sha256"),
        CheckConstraint(
            "mutation_kind IN ('insert','update','delete','snapshot')", name="mutation_kind_known"
        ),
        CheckConstraint(
            (
                "classification IN "
                "('supported_dividend','supported_forward_split','unsupported','uncertain','cancelled')"
            ),
            name="classification_known",
        ),
        object_json("normalized_terms"),
        object_json("calendar_provenance"),
        bounded("source_mutation_id"),
        bounded("reason", 1024),
        bounded("units", 128),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("stock_action_events.id"), index=True)
    source_id: Mapped[int] = mapped_column(BigInteger)
    ordinal: Mapped[int] = mapped_column(BigInteger)
    fingerprint: Mapped[str] = mapped_column(Text)
    mutation_kind: Mapped[str] = mapped_column(Text)
    source_mutation_id: Mapped[str | None] = mapped_column(Text)
    source_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    admission_generation: Mapped[int] = mapped_column(BigInteger)
    normalized_terms: Mapped[dict[str, Any]] = mapped_column(JSONB)
    classification: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    verified_cutoff: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    units: Mapped[str | None] = mapped_column(Text)
    calendar_provenance: Mapped[dict[str, Any] | None] = mapped_column(JSONB)


class StockActionObservation(Base):
    __tablename__ = "stock_action_observations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["revision_id", "source_id"],
            ["stock_action_revisions.id", "stock_action_revisions.source_id"],
            name="fk_stock_action_observation_revision_source",
        ),
        Index("ix_stock_action_observations_revision_id", "revision_id"),
        Index(
            "uq_stock_action_observation_mutation",
            "source_id",
            "mutation_id",
            unique=True,
            postgresql_where=text("mutation_id IS NOT NULL"),
        ),
        safe("admission_generation", positive=True),
        bounded("mutation_id"),
        bounded("source_kind", 64),
        bounded("cycle_id", 128),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("stock_action_sources.id"), index=True)
    revision_id: Mapped[int] = mapped_column(BigInteger)
    mutation_id: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    admission_generation: Mapped[int] = mapped_column(BigInteger)
    source_kind: Mapped[str] = mapped_column(Text)
    cycle_id: Mapped[str] = mapped_column(Text)


class StockActionState(Base):
    __tablename__ = "stock_action_state"
    __table_args__ = (
        safe("epoch", positive=True),
        safe("unit_epoch"),
        safe("sequence"),
        safe("admission_generation", positive=True),
        CheckConstraint("health IN ('unknown','reconciling','current')", name="health_known"),
        CheckConstraint(
            "checked_at IS NULL OR valid_until IS NULL OR checked_at < valid_until", name="validity"
        ),
        CheckConstraint(
            ("coverage_start IS NULL OR covered_until IS NULL OR coverage_start <= covered_until"),
            name="coverage_order",
        ),
        CheckConstraint(
            (
                "journal_start_at IS NULL OR complete_from IS NULL OR journal_start_at "
                "<= complete_from"
            ),
            name="journal_order",
        ),
        object_json("staged_continuation", 32768),
        bounded("cursor", 4096),
    )
    coin_id: Mapped[int] = mapped_column(ForeignKey("stock_instruments.coin_id"), primary_key=True)
    epoch: Mapped[int] = mapped_column(BigInteger, server_default="1")
    unit_epoch: Mapped[int] = mapped_column(BigInteger, server_default="0")
    sequence: Mapped[int] = mapped_column(BigInteger, server_default="0")
    health: Mapped[str] = mapped_column(Text, server_default="unknown")
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    admission_generation: Mapped[int] = mapped_column(BigInteger)
    coverage_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    covered_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cursor: Mapped[str | None] = mapped_column(Text)
    staged_continuation: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    journal_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    complete_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    quote_not_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_blocking_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StockSplitApplication(Base):
    __tablename__ = "stock_split_applications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["revision_id", "economic_event_id"],
            ["stock_action_revisions.id", "stock_action_revisions.event_id"],
            name="fk_stock_split_revision_event",
        ),
        Index("ix_stock_split_applications_revision_id", "revision_id"),
        CheckConstraint(
            (
                "new_rate ~ '^[0-9]{1,12}(\\.[0-9]{1,8})?$' AND old_rate ~ "
                "'^[0-9]{1,12}(\\.[0-9]{1,8})?$'"
            ),
            name="rates_decimal",
        ),
        CheckConstraint(
            (
                "CASE WHEN new_rate ~ '^[0-9]{1,12}(\\.[0-9]{1,8})?$' AND old_rate ~ "
                "'^[0-9]{1,12}(\\.[0-9]{1,8})?$' THEN new_rate::numeric > "
                "old_rate::numeric AND old_rate::numeric > 0 ELSE false END"
            ),
            name="forward_rates",
        ),
        safe("prior_unit_epoch"),
        safe("new_unit_epoch"),
        safe("sequence_boundary"),
        CheckConstraint("new_unit_epoch = prior_unit_epoch + 1", name="unit_transition"),
        CheckConstraint(
            "before_digest ~ '^[0-9a-f]{64}$' AND after_digest ~ '^[0-9a-f]{64}$'",
            name="digests_sha256",
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    economic_event_id: Mapped[int] = mapped_column(
        ForeignKey("stock_action_events.id"), unique=True
    )
    revision_id: Mapped[int] = mapped_column(BigInteger)
    new_rate: Mapped[str] = mapped_column(Text)
    old_rate: Mapped[str] = mapped_column(Text)
    cutoff: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    prior_unit_epoch: Mapped[int] = mapped_column(BigInteger)
    new_unit_epoch: Mapped[int] = mapped_column(BigInteger)
    sequence_boundary: Mapped[int] = mapped_column(BigInteger)
    before_digest: Mapped[str] = mapped_column(Text)
    after_digest: Mapped[str] = mapped_column(Text)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class StockOwnershipMovement(Base):
    __tablename__ = "stock_ownership_movements"
    __table_args__ = (
        UniqueConstraint("trade_id", name="uq_stock_ownership_trade"),
        UniqueConstraint("application_id", "user_id", name="uq_stock_ownership_application_user"),
        UniqueConstraint("coin_id", "sequence", name="uq_stock_ownership_sequence"),
        UniqueConstraint("coin_id", "causal_key", "user_id", name="uq_stock_ownership_cause"),
        safe("sequence", positive=True),
        safe("unit_epoch"),
        bounded("causal_key", 256),
        CheckConstraint("cause_kind IN ('fill','split','opening')", name="cause_known"),
        CheckConstraint(
            (
                "(cause_kind='fill' AND trade_id IS NOT NULL AND application_id IS "
                "NULL) OR (cause_kind='split' AND application_id IS NOT NULL AND "
                "trade_id IS NULL) OR (cause_kind='opening' AND trade_id IS NULL AND "
                "application_id IS NULL)"
            ),
            name="cause_references",
        ),
        CheckConstraint(
            (
                "quantity > '-1000000000000'::numeric AND quantity < "
                "'1000000000000'::numeric AND quantity = trunc(quantity) AND quantity "
                "<> 0"
            ),
            name="quantity_whole_finite",
        ),
        CheckConstraint(
            (
                "before_quantity >= 0 AND before_quantity < '1000000000000'::numeric "
                "AND before_quantity = trunc(before_quantity) AND after_quantity >= 0 "
                "AND after_quantity < '1000000000000'::numeric AND after_quantity = "
                "trunc(after_quantity)"
            ),
            name="holdings_whole_finite",
        ),
        CheckConstraint(
            (
                "before_basis >= 0 AND before_basis < '1000000000000'::numeric AND "
                "before_basis = round(before_basis,2) AND after_basis >= 0 AND "
                "after_basis < '1000000000000'::numeric AND after_basis = "
                "round(after_basis,2)"
            ),
            name="basis_finite_cents",
        ),
        CheckConstraint("before_quantity + quantity = after_quantity", name="quantity_equation"),
        CheckConstraint(
            ("(before_quantity > 0 OR before_basis=0) AND (after_quantity > 0 OR after_basis=0)"),
            name="empty_basis",
        ),
        CheckConstraint(
            "cause_kind <> 'split' OR (quantity > 0 AND before_basis = after_basis)",
            name="split_conserves_basis",
        ),
        CheckConstraint(
            ("cause_kind <> 'opening' OR (before_quantity=0 AND before_basis=0 AND quantity>0)"),
            name="opening_baseline",
        ),
        Index("ix_stock_ownership_user_economic_id", "user_id", "economic_at", "id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey("stock_instruments.coin_id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sequence: Mapped[int] = mapped_column(BigInteger)
    economic_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    before_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    after_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    before_basis: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    after_basis: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    unit_epoch: Mapped[int] = mapped_column(BigInteger)
    cause_kind: Mapped[str] = mapped_column(Text)
    trade_id: Mapped[int | None] = mapped_column(ForeignKey("trades.id"), index=True)
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_split_applications.id"), index=True
    )
    causal_key: Mapped[str] = mapped_column(Text)


class StockDividendEntitlement(Base):
    __tablename__ = "stock_dividend_entitlements"
    __table_args__ = (
        UniqueConstraint("id", "event_id", "user_id", name="uq_stock_entitlement_id_event_user"),
        ForeignKeyConstraint(
            ["supersedes_id", "event_id", "user_id"],
            [
                "stock_dividend_entitlements.id",
                "stock_dividend_entitlements.event_id",
                "stock_dividend_entitlements.user_id",
            ],
            name="fk_stock_entitlement_supersedes_owner_event",
        ),
        ForeignKeyConstraint(
            ["revision_id", "event_id"],
            ["stock_action_revisions.id", "stock_action_revisions.event_id"],
            name="fk_stock_entitlement_revision_event",
        ),
        UniqueConstraint(
            "event_id",
            "user_id",
            "revision_id",
            "fingerprint",
            name="uq_stock_entitlement_revision_fingerprint",
        ),
        Index("ix_stock_dividend_entitlements_revision_id", "revision_id"),
        safe("unit_epoch"),
        safe("last_movement_sequence"),
        safe("version", positive=True),
        bounded("cutoff_rule", 128),
        bounded("units_basis", 128),
        CheckConstraint("fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint_sha256"),
        CheckConstraint(
            (
                "eligible_quantity >= 0 AND eligible_quantity < "
                "'1000000000000'::numeric AND "
                "eligible_quantity=trunc(eligible_quantity)"
            ),
            name="eligible_whole_finite",
        ),
        CheckConstraint("state IN ('eligible','held','cancelled')", name="state_known"),
        CheckConstraint(
            "supersedes_id IS NULL OR supersedes_id <> id", name="no_self_supersession"
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("stock_action_events.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    revision_id: Mapped[int] = mapped_column(BigInteger)
    cutoff: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cutoff_rule: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(BigInteger)
    units_basis: Mapped[str] = mapped_column(Text)
    unit_epoch: Mapped[int] = mapped_column(BigInteger)
    last_movement_sequence: Mapped[int] = mapped_column(BigInteger)
    eligible_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    state: Mapped[str] = mapped_column(Text)
    supersedes_id: Mapped[int | None] = mapped_column(
        ForeignKey("stock_dividend_entitlements.id"), index=True
    )
    fingerprint: Mapped[str] = mapped_column(Text)


class StockActionResolution(Base):
    __tablename__ = "stock_action_resolutions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["event_id", "coin_id"],
            ["stock_action_events.id", "stock_action_events.coin_id"],
            name="fk_stock_resolution_event_coin",
        ),
        ForeignKeyConstraint(
            ["expected_revision", "event_id"],
            ["stock_action_revisions.id", "stock_action_revisions.event_id"],
            name="fk_stock_resolution_revision_event",
        ),
        UniqueConstraint("coin_id", "decision_key", name="uq_stock_action_resolution_decision"),
        safe("expected_revision", positive=True),
        safe("admission_generation", positive=True),
        safe("epoch", positive=True),
        bounded("decision", 128),
        bounded("decision_key", 256),
        bounded("actor_ref", 256),
        object_json("evidence"),
        CheckConstraint(
            (
                "evidence_hash ~ '^[0-9a-f]{64}$' AND before_digest ~ '^[0-9a-f]{64}$' "
                "AND after_digest ~ '^[0-9a-f]{64}$'"
            ),
            name="digests_sha256",
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("stock_action_events.id"), index=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey("stock_instruments.coin_id"), index=True)
    expected_revision: Mapped[int] = mapped_column(
        ForeignKey("stock_action_revisions.id"), index=True
    )
    admission_generation: Mapped[int] = mapped_column(BigInteger)
    epoch: Mapped[int] = mapped_column(BigInteger)
    decision: Mapped[str] = mapped_column(Text)
    decision_key: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB)
    evidence_hash: Mapped[str] = mapped_column(Text)
    before_digest: Mapped[str] = mapped_column(Text)
    after_digest: Mapped[str] = mapped_column(Text)
    actor_ref: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
