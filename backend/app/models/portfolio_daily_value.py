from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Identity,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PortfolioDailyValue(Base):
    __tablename__ = "portfolio_daily_values"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "utc_day", name="uq_portfolio_daily_values_portfolio_day"),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_portfolio_daily_values_owner",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "isfinite(captured_at) AND (captured_at AT TIME ZONE 'UTC')::date=utc_day"
            " AND (captured_at AT TIME ZONE 'UTC')::time>=TIME '22:00'",
            name="utc_capture",
        ),
        CheckConstraint(
            "starting_cash>=0 AND starting_cash<'Infinity'::numeric", name="starting_cash_valid"
        ),
        CheckConstraint("total_value>=0 AND total_value<'Infinity'::numeric", name="total_valid"),
        CheckConstraint("valuation_complete=(total_value IS NOT NULL)", name="completeness"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(BigInteger)
    user_id: Mapped[int] = mapped_column(BigInteger)
    utc_day: Mapped[date] = mapped_column(Date)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    starting_cash: Mapped[Decimal] = mapped_column(Numeric(20, 8))
    total_value: Mapped[Decimal | None] = mapped_column(Numeric(48, 2))
    valuation_complete: Mapped[bool]
