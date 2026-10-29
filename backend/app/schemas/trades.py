from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, model_validator

from app.services import trading

# NUMERIC(20,8) values can be Decimal("0E-8") or 1E-8; format(..., "f") always gives plain
# notation, which the frontend's decimal-string guards require.
Money = Annotated[
    Decimal, PlainSerializer(lambda v: format(v, "f"), return_type=str, when_used="json")
]


class QuoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(pattern=r"^[A-Za-z0-9]{1,10}$")
    side: Literal["buy", "sell"]
    amount_usd: Decimal | None = Field(
        None, gt=0, max_digits=14, decimal_places=2, description="USD to spend, buys only"
    )
    quantity: Decimal | None = Field(
        None, gt=0, max_digits=20, decimal_places=8, description="Coin quantity"
    )

    @model_validator(mode="after")
    def _exactly_one_input(self) -> Self:
        if (self.amount_usd is None) == (self.quantity is None):
            raise ValueError("Send exactly one of amount_usd or quantity.")
        if self.amount_usd is not None and self.side == "sell":
            raise ValueError("Sells are by quantity only.")
        return self

    def to_order(self) -> trading.Order:
        if self.amount_usd is not None:
            return trading.Order(self.symbol.upper(), self.side, "usd", self.amount_usd)
        # the validator guarantees quantity is set when amount_usd is not
        return trading.Order(
            self.symbol.upper(), self.side, "quantity", cast(Decimal, self.quantity)
        )


class TradeIn(QuoteIn):
    expected_mid: Decimal = Field(gt=0, max_digits=20, decimal_places=8)
    idempotency_key: UUID


class QuoteOut(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    input_kind: Literal["usd", "quantity"]
    input_value: Money
    mid: Money
    as_of: datetime
    age_seconds: int
    exec_price: Money
    quantity: Money
    notional: Money
    fee: Money
    cash_delta: Money
    cash_before: Money
    cash_after: Money
    held_before: Money
    held_after: Money
    whole_position: bool

    @classmethod
    def from_quote(cls, q: trading.Quote) -> Self:
        p = q.plan
        return cls(
            symbol=q.symbol,
            side=p.side,
            input_kind=p.kind,
            input_value=p.input_value,
            mid=p.mid,
            as_of=q.as_of,
            age_seconds=q.age_seconds,
            exec_price=p.exec_price,
            quantity=p.quantity,
            notional=p.notional,
            fee=p.fee,
            cash_delta=p.cash_delta,
            cash_before=p.cash_before,
            cash_after=p.cash_after,
            held_before=p.held_before,
            held_after=p.held_after,
            whole_position=p.whole_position,
        )


class FillOut(BaseModel):
    trade_id: int
    created_at: datetime
    symbol: str
    side: Literal["buy", "sell"]
    input_kind: Literal["usd", "quantity"]
    input_value: Money
    mid: Money
    as_of: datetime
    exec_price: Money
    quantity: Money
    notional: Money
    fee: Money
    cash_delta: Money
    cash_after: Money

    @classmethod
    def from_fill(cls, f: trading.Fill) -> Self:
        return cls(**{name: getattr(f, name) for name in cls.model_fields})


class HoldingOut(BaseModel):
    symbol: str
    quantity: Money
