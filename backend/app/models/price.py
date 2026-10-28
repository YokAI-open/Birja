from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Integer,
    Numeric,
    Text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Coin(Base):
    """The curated coin list (D-01), kept as data."""

    __tablename__ = "coins"
    __table_args__ = (
        CheckConstraint("symbol = upper(symbol)", name="symbol_upper"),
        CheckConstraint("length(symbol) BETWEEN 1 AND 10", name="symbol_length"),
        CheckConstraint("length(name) BETWEEN 1 AND 64", name="name_length"),
        CheckConstraint("length(kraken_pair) BETWEEN 1 AND 32", name="kraken_pair_length"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    symbol: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # Both the Ticker request pair and the key in Kraken's response.
    kraken_pair: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())


class Price(Base):
    """Latest good mid price per coin (D-05: mid only, no history)."""

    __tablename__ = "prices"
    __table_args__ = (
        CheckConstraint("mid > 0", name="mid_positive"),
        CheckConstraint("source IN ('kraken', 'fake')", name="source_known"),
    )

    coin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("coins.id"), primary_key=True)
    mid: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
