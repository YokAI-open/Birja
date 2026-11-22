"""Permanent creation bindings and explicit once-only onboarding provenance."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PortfolioCreation(Base):
    __tablename__ = "portfolio_creations"
    __table_args__ = (
        UniqueConstraint("user_id", "creation_key", name="uq_portfolio_creation_owner_key"),
        UniqueConstraint("portfolio_id", name="uq_portfolio_creation_root"),
        UniqueConstraint("id", "portfolio_id", "user_id", name="uq_portfolio_creation_lineage"),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_portfolio_creation_owner",
        ),
        CheckConstraint("origin IN ('initial','explicit')", name="origin_known"),
        CheckConstraint("amount=10000", name="fixed_grant"),
        CheckConstraint("payload_version=1", name="payload_version_known"),
        CheckConstraint(
            "jsonb_typeof(canonical_payload)='object' AND "
            "canonical_payload ?& ARRAY['name','description'] AND "
            "canonical_payload - ARRAY['name','description'] = '{}'::jsonb AND "
            "jsonb_typeof(canonical_payload->'name')='string' AND "
            "jsonb_typeof(canonical_payload->'description')='string'",
            name="payload_shape",
        ),
        Index("ix_portfolio_creation_owner_created", "user_id", "created_at", "id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    creation_key: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    portfolio_id: Mapped[int] = mapped_column(BigInteger)
    origin: Mapped[str] = mapped_column(Text)
    payload_version: Mapped[int] = mapped_column(SmallInteger)
    canonical_payload: Mapped[dict[str, str]] = mapped_column(JSONB)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PortfolioInitialization(Base):
    __tablename__ = "portfolio_initializations"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_portfolio_initialization_user"),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_portfolio_initialization_owner",
        ),
        ForeignKeyConstraint(
            ["creation_id", "portfolio_id", "user_id"],
            [
                "portfolio_creations.id",
                "portfolio_creations.portfolio_id",
                "portfolio_creations.user_id",
            ],
            name="fk_portfolio_initialization_creation",
        ),
        CheckConstraint(
            "(origin='legacy' AND portfolio_id IS NULL AND creation_id IS NULL) OR "
            "(origin='initial' AND portfolio_id IS NOT NULL AND creation_id IS NOT NULL)",
            name="provenance_exact",
        ),
        Index("ix_portfolio_initialization_root", "portfolio_id"),
        Index("ix_portfolio_initialization_creation", "creation_id"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    origin: Mapped[str] = mapped_column(Text)
    portfolio_id: Mapped[int | None] = mapped_column(BigInteger)
    creation_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
