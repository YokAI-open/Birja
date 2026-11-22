"""Terminal strategy evidence; never a publicly readable financial ledger."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PortfolioClosureIntent(Base):
    __tablename__ = "portfolio_closure_intents"
    __table_args__ = (
        UniqueConstraint("user_id", "intent_key", name="uq_portfolio_closure_intent_owner_key"),
        UniqueConstraint(
            "id", "portfolio_id", "user_id", name="uq_portfolio_closure_intent_lineage"
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_portfolio_closure_intent_owner",
        ),
        CheckConstraint("policy_version='freeze_at_closure_v1'", name="policy_known"),
        CheckConstraint("outcome IN ('closed','confirmation_changed')", name="outcome_known"),
        CheckConstraint(
            "confirmation_name=public.portfolio_display_name(confirmation_name)",
            name="confirmation_canonical",
        ),
        CheckConstraint("isfinite(recorded_at)", name="recorded_finite"),
        CheckConstraint("substr(intent_key::text,15,1)='4'", name="intent_uuid4"),
        Index("ix_portfolio_closure_intent_owner_recorded", "user_id", "recorded_at", "id"),
        Index("ix_portfolio_closure_intent_root", "portfolio_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    portfolio_id: Mapped[int] = mapped_column(BigInteger)
    intent_key: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    confirmation_name: Mapped[str] = mapped_column(Text)
    policy_version: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PortfolioLifecycleClosure(Base):
    __tablename__ = "portfolio_lifecycle_closures"
    __table_args__ = (
        UniqueConstraint("portfolio_id", name="uq_portfolio_lifecycle_root"),
        UniqueConstraint("intent_id", name="uq_portfolio_lifecycle_intent"),
        UniqueConstraint(
            "portfolio_id", "user_id", "closed_at", name="uq_portfolio_lifecycle_boundary"
        ),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_portfolio_lifecycle_owner",
        ),
        ForeignKeyConstraint(
            ["intent_id", "portfolio_id", "user_id"],
            [
                "portfolio_closure_intents.id",
                "portfolio_closure_intents.portfolio_id",
                "portfolio_closure_intents.user_id",
            ],
            name="fk_portfolio_lifecycle_intent",
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("policy_version='freeze_at_closure_v1'", name="policy_known"),
        CheckConstraint("isfinite(closed_at)", name="closed_finite"),
        CheckConstraint(
            "(provenance='retained_boundary' AND confirmation_name IS NULL "
            "AND intent_id IS NULL) OR (provenance='owner_confirmation' "
            "AND confirmation_name IS NOT NULL AND intent_id IS NOT NULL "
            "AND confirmation_name=public.portfolio_display_name(confirmation_name))",
            name="provenance_exact",
        ),
        Index("ix_portfolio_lifecycle_owner", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    portfolio_id: Mapped[int] = mapped_column(BigInteger)
    closed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    policy_version: Mapped[str] = mapped_column(Text)
    provenance: Mapped[str] = mapped_column(Text)
    confirmation_name: Mapped[str | None] = mapped_column(Text)
    intent_id: Mapped[int | None] = mapped_column(BigInteger)
