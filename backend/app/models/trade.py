import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Holding(Base):
    """One row per user and coin: quantity held and its USD cost basis (D-07)."""

    __tablename__ = "holdings"
    # The UNIQUE index serves the (user, coin) lookup and covers the user_id FK.
    __table_args__ = (
        UniqueConstraint("user_id", "coin_id", name="uq_holdings_user_coin"),
        CheckConstraint("quantity >= 0", name="quantity_non_negative"),
        CheckConstraint("cost_basis >= 0", name="cost_basis_non_negative"),
        CheckConstraint("cost_basis = round(cost_basis, 2)", name="cost_basis_cents"),
        CheckConstraint("quantity > 0 OR cost_basis = 0", name="empty_has_no_cost"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    coin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("coins.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, server_default="0")


class Trade(Base):
    """Append-only fill record with the exact price and as-of used (D-03)."""

    __tablename__ = "trades"
    # Equality on user first, then the history seek/order boundary.
    __table_args__ = (
        Index("ix_trades_user_created_id", "user_id", "created_at", "id"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_trades_user_idempotency_key"),
        CheckConstraint("side IN ('buy', 'sell')", name="side_known"),
        CheckConstraint("input_kind IN ('usd', 'quantity')", name="input_kind_known"),
        CheckConstraint("NOT (side = 'sell' AND input_kind = 'usd')", name="sell_by_quantity"),
        CheckConstraint("input_value > 0", name="input_value_positive"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("mid_price > 0", name="mid_positive"),
        CheckConstraint("exec_price > 0", name="exec_positive"),
        CheckConstraint("fee >= 0", name="fee_non_negative"),
        CheckConstraint("cash_after >= 0", name="cash_after_non_negative"),
        CheckConstraint(
            "(side = 'buy' AND cash_delta < 0) OR (side = 'sell' AND cash_delta >= 0)",
            name="cash_delta_sign",
        ),
        CheckConstraint(
            "fee = round(fee, 2) AND cash_delta = round(cash_delta, 2) "
            "AND cash_after = round(cash_after, 2)",
            name="cents",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    coin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("coins.id"), nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    input_kind: Mapped[str] = mapped_column(Text, nullable=False)
    input_value: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    mid_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    price_as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exec_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    cash_delta: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    cash_after: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    idempotency_key: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
