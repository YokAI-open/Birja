"""Immutable dividend originals and append-only decisions; SQL owns cash effects."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
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
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.corporate_action import bounded, safe


def fingerprint(column: str) -> CheckConstraint:
    return CheckConstraint(f"{column} ~ '^[0-9a-f]{{64}}$'", name=f"{column}_sha256")


def money(column: str, *, signed: bool = False) -> CheckConstraint:
    lower = f"{column}>-1e12" if signed else f"{column}>=0"
    return CheckConstraint(
        f"{lower} AND {column}<1e12 AND {column}=trunc({column},2)",
        name=f"{column}_finite_cents",
    )


class StockDividendPayment(Base):
    __tablename__ = "stock_dividend_payments"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_stock_dividend_payment_event_user"),
        UniqueConstraint(
            "id",
            "event_id",
            "user_id",
            "coin_id",
            name="uq_stock_dividend_payment_owner_event_coin",
        ),
        ForeignKeyConstraint(
            ["event_id", "coin_id"],
            ["stock_action_events.id", "stock_action_events.coin_id"],
            name="fk_dividend_payment_event_coin",
        ),
        ForeignKeyConstraint(
            ["revision_id", "event_id", "revision_fingerprint"],
            [
                "stock_action_revisions.id",
                "stock_action_revisions.event_id",
                "stock_action_revisions.fingerprint",
            ],
            name="fk_dividend_payment_revision_identity",
        ),
        ForeignKeyConstraint(
            ["entitlement_id", "event_id", "user_id", "revision_id", "entitlement_fingerprint"],
            [
                "stock_dividend_entitlements.id",
                "stock_dividend_entitlements.event_id",
                "stock_dividend_entitlements.user_id",
                "stock_dividend_entitlements.revision_id",
                "stock_dividend_entitlements.fingerprint",
            ],
            name="fk_dividend_payment_entitlement_identity",
        ),
        fingerprint("revision_fingerprint"),
        fingerprint("entitlement_fingerprint"),
        bounded("symbol", 32),
        bounded("company_name", 256),
        bounded("cutoff_rule", 128),
        bounded("units_basis", 128),
        safe("unit_epoch"),
        CheckConstraint(
            "eligible_quantity>=0 AND eligible_quantity<1e12 "
            "AND eligible_quantity=trunc(eligible_quantity)",
            name="eligible_whole_finite",
        ),
        CheckConstraint("rate>=0 AND rate<1e12", name="rate_finite"),
        money("original_amount"),
        money("cash_after"),
        Index("ix_stock_dividend_payment_owner_recorded_id", "user_id", "recorded_at", "id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    event_id: Mapped[int] = mapped_column(BigInteger)
    coin_id: Mapped[int] = mapped_column(ForeignKey("stock_instruments.coin_id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    revision_id: Mapped[int] = mapped_column(BigInteger, index=True)
    revision_fingerprint: Mapped[str] = mapped_column(Text)
    entitlement_id: Mapped[int] = mapped_column(BigInteger, index=True)
    entitlement_fingerprint: Mapped[str] = mapped_column(Text)
    symbol: Mapped[str] = mapped_column(Text)
    company_name: Mapped[str] = mapped_column(Text)
    cutoff: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cutoff_rule: Mapped[str] = mapped_column(Text)
    units_basis: Mapped[str] = mapped_column(Text)
    unit_epoch: Mapped[int] = mapped_column(BigInteger)
    eligible_quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    rate: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    ex_date: Mapped[date] = mapped_column(Date)
    record_date: Mapped[date] = mapped_column(Date)
    payable_date: Mapped[date] = mapped_column(Date)
    original_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cash_after: Mapped[Decimal] = mapped_column(Numeric(20, 8))


class StockDividendDecision(Base):
    __tablename__ = "stock_dividend_decisions"
    __table_args__ = (
        UniqueConstraint(
            "id", "payment_id", "user_id", "event_id", name="uq_stock_dividend_decision_lineage"
        ),
        ForeignKeyConstraint(
            ["payment_id", "event_id", "user_id", "coin_id"],
            [
                "stock_dividend_payments.id",
                "stock_dividend_payments.event_id",
                "stock_dividend_payments.user_id",
                "stock_dividend_payments.coin_id",
            ],
            name="fk_dividend_decision_payment_owner",
        ),
        ForeignKeyConstraint(
            ["revision_id", "event_id", "revision_fingerprint"],
            [
                "stock_action_revisions.id",
                "stock_action_revisions.event_id",
                "stock_action_revisions.fingerprint",
            ],
            name="fk_dividend_decision_revision_identity",
        ),
        ForeignKeyConstraint(
            ["entitlement_id", "event_id", "user_id", "revision_id", "entitlement_fingerprint"],
            [
                "stock_dividend_entitlements.id",
                "stock_dividend_entitlements.event_id",
                "stock_dividend_entitlements.user_id",
                "stock_dividend_entitlements.revision_id",
                "stock_dividend_entitlements.fingerprint",
            ],
            name="fk_dividend_decision_entitlement_identity",
        ),
        ForeignKeyConstraint(
            ["previous_decision_id", "payment_id", "user_id", "event_id"],
            [
                "stock_dividend_decisions.id",
                "stock_dividend_decisions.payment_id",
                "stock_dividend_decisions.user_id",
                "stock_dividend_decisions.event_id",
            ],
            name="fk_dividend_decision_previous_owner",
        ),
        ForeignKeyConstraint(
            ["previous_application_id", "payment_id", "user_id", "event_id"],
            [
                "stock_dividend_decisions.id",
                "stock_dividend_decisions.payment_id",
                "stock_dividend_decisions.user_id",
                "stock_dividend_decisions.event_id",
            ],
            name="fk_dividend_decision_application_owner",
        ),
        fingerprint("revision_fingerprint"),
        fingerprint("entitlement_fingerprint"),
        bounded("status_identity", 256),
        bounded("symbol", 32),
        bounded("company_name", 256),
        bounded("cutoff_rule", 128),
        bounded("units_basis", 128),
        safe("unit_epoch"),
        CheckConstraint(
            "outcome IN ('applied','held_uncertain','held_unaffordable','verified_no_change')",
            name="outcome_known",
        ),
        CheckConstraint(
            "(outcome='applied' AND reason='target_applied') OR "
            "(outcome='verified_no_change' AND reason='target_unchanged') OR "
            "(outcome='held_uncertain' AND reason='terms_unverified') OR "
            "(outcome='held_unaffordable' AND reason='insufficient_cash')",
            name="reason_matches_outcome",
        ),
        CheckConstraint(
            "(entitlement_id IS NULL)=(entitlement_fingerprint IS NULL)",
            name="entitlement_null_pair",
        ),
        CheckConstraint(
            "outcome='held_uncertain' OR (entitlement_id IS NOT NULL "
            "AND desired_total IS NOT NULL AND proposed_delta IS NOT NULL "
            "AND eligible_quantity IS NOT NULL AND rate IS NOT NULL "
            "AND cutoff IS NOT NULL AND cutoff_rule IS NOT NULL "
            "AND units_basis IS NOT NULL AND unit_epoch IS NOT NULL "
            "AND ex_date IS NOT NULL AND record_date IS NOT NULL "
            "AND payable_date IS NOT NULL)",
            name="verified_terms_required",
        ),
        CheckConstraint(
            "outcome<>'held_uncertain' OR (desired_total IS NULL "
            "AND proposed_delta IS NULL AND eligible_quantity IS NULL "
            "AND rate IS NULL AND cutoff IS NULL AND cutoff_rule IS NULL "
            "AND units_basis IS NULL AND unit_epoch IS NULL AND ex_date IS NULL "
            "AND record_date IS NULL AND payable_date IS NULL)",
            name="uncertainty_no_invented_terms",
        ),
        CheckConstraint(
            "proposed_delta=desired_total-cumulative_applied_before", name="target_delta_equation"
        ),
        CheckConstraint(
            "(outcome='applied' AND applied_delta=proposed_delta "
            "AND applied_delta<>0) OR (outcome<>'applied' AND applied_delta=0)",
            name="applied_effect",
        ),
        CheckConstraint("outcome<>'verified_no_change' OR proposed_delta=0", name="no_change_zero"),
        CheckConstraint(
            "outcome<>'held_unaffordable' OR (proposed_delta<0 AND cash_after < -proposed_delta)",
            name="unaffordable_negative",
        ),
        CheckConstraint(
            "previous_decision_id IS NULL OR previous_decision_id<id",
            name="previous_decision_precedes",
        ),
        CheckConstraint(
            "previous_application_id IS NULL OR previous_application_id<id",
            name="previous_application_precedes",
        ),
        CheckConstraint(
            "eligible_quantity>=0 AND eligible_quantity<1e12 "
            "AND eligible_quantity=trunc(eligible_quantity)",
            name="eligible_whole_finite",
        ),
        CheckConstraint("rate>=0 AND rate<1e12", name="rate_finite"),
        money("desired_total"),
        money("cumulative_applied_before"),
        money("proposed_delta", signed=True),
        money("applied_delta", signed=True),
        money("cash_after"),
        Index("ix_stock_dividend_decision_owner_recorded_id", "user_id", "recorded_at", "id"),
        Index("ix_stock_dividend_decision_payment_id", "payment_id", "id"),
        Index("ix_stock_dividend_decision_event_id", "event_id"),
        Index("ix_stock_dividend_decision_revision_id", "revision_id"),
        Index("ix_stock_dividend_decision_entitlement_id", "entitlement_id"),
        Index("ix_stock_dividend_decision_previous_decision_id", "previous_decision_id"),
        Index("ix_stock_dividend_decision_previous_application_id", "previous_application_id"),
        Index(
            "uq_stock_dividend_decision_applied_target",
            "payment_id",
            "revision_id",
            "entitlement_id",
            "revision_fingerprint",
            "entitlement_fingerprint",
            unique=True,
            postgresql_where=text("outcome IN ('applied','verified_no_change')"),
        ),
        Index(
            "uq_stock_dividend_decision_held_status",
            "payment_id",
            "revision_fingerprint",
            "entitlement_id",
            "status_identity",
            unique=True,
            postgresql_nulls_not_distinct=True,
            postgresql_where=text("outcome IN ('held_uncertain','held_unaffordable')"),
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    payment_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_id: Mapped[int] = mapped_column(BigInteger)
    coin_id: Mapped[int] = mapped_column(ForeignKey("stock_instruments.coin_id"), index=True)
    revision_id: Mapped[int] = mapped_column(BigInteger)
    revision_fingerprint: Mapped[str] = mapped_column(Text)
    entitlement_id: Mapped[int | None] = mapped_column(BigInteger)
    entitlement_fingerprint: Mapped[str | None] = mapped_column(Text)
    previous_decision_id: Mapped[int | None] = mapped_column(BigInteger)
    previous_application_id: Mapped[int | None] = mapped_column(BigInteger)
    desired_total: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    cumulative_applied_before: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    proposed_delta: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    applied_delta: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    outcome: Mapped[str] = mapped_column(Text)
    reason: Mapped[str] = mapped_column(Text)
    status_identity: Mapped[str] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cash_after: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    symbol: Mapped[str] = mapped_column(Text)
    company_name: Mapped[str] = mapped_column(Text)
    cutoff: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cutoff_rule: Mapped[str | None] = mapped_column(Text)
    units_basis: Mapped[str | None] = mapped_column(Text)
    unit_epoch: Mapped[int | None] = mapped_column(BigInteger)
    eligible_quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    rate: Mapped[Decimal | None] = mapped_column(Numeric(20, 8))
    ex_date: Mapped[date | None] = mapped_column(Date)
    record_date: Mapped[date | None] = mapped_column(Date)
    payable_date: Mapped[date | None] = mapped_column(Date)
