"""Exact stock API contracts, independent from legacy crypto input coercion."""

import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    PlainSerializer,
)

MAX_SAFE = 9007199254740991
Side = Literal["buy", "sell"]
Money = Annotated[
    Decimal,
    Field(allow_inf_nan=False),
    PlainSerializer(lambda value: format(value, "f"), return_type=str, when_used="json"),
]


def _whole(value: object) -> Decimal:
    if not isinstance(value, str) or re.fullmatch(r"[1-9][0-9]{0,11}", value) is None:
        raise ValueError("Quantity must be a positive whole-share string of at most 12 digits.")
    return Decimal(value)


def _price(value: object) -> Decimal:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,8})?", value) is None
    ):
        raise ValueError("Expected price must be a plain NUMERIC(20,8) string.")
    result = Decimal(value)
    if result <= 0:
        raise ValueError("Expected price must be positive.")
    return result


WholeQuantity = Annotated[Money, BeforeValidator(_whole)]
ExpectedPrice = Annotated[Money, BeforeValidator(_price)]
Identifier = Annotated[str, Field(pattern=r"^[1-9][0-9]{0,18}$", strict=True)]
Generation = Annotated[int, Field(ge=0, le=MAX_SAFE, strict=True)]
RowHash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$", strict=True)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class QuoteIn(Contract):
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.\-]{0,9}$", strict=True)
    side: Side
    quantity: WholeQuantity


class TradeIn(QuoteIn):
    expected_exec_price: ExpectedPrice
    idempotency_key: UUID


class AdmissionIdentity(Contract):
    """Exact semantically evaluated row, never caller-supplied authorization."""

    product: Literal["reference", "quotes", "actions", "status", "calendar"]
    generation: Generation
    row_hash: RowHash
    valid_until: AwareDatetime


class AuthorityIdentity(Contract):
    admissions: tuple[AdmissionIdentity, ...]
    calendar_generation: Generation
    safety_epoch: Generation
    unit_epoch: Generation
    status_admission_generation: Generation
    continuity_generation: Generation
    status_sequence: Generation


class SessionFacts(Contract):
    state: Literal["open", "closed", "unknown"]
    session_date: date
    opens_at: AwareDatetime | None
    closes_at: AwareDatetime | None
    valid_until: AwareDatetime | None
    next_open_at: AwareDatetime | None = None
    timezone: Literal["America/New_York"] = "America/New_York"


class StatusFacts(Contract):
    state: Literal["normal", "halted", "frozen", "unknown"] = "unknown"
    event_at: AwareDatetime | None = None
    observed_at: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None
    bootstrap_verified: bool = False
    continuity_current: bool = False


class ActionFacts(Contract):
    state: Literal["current", "unknown", "reconciling", "suspended"] = "unknown"
    reason: str = Field(default="monitor_unavailable", max_length=64)
    valid_until: AwareDatetime | None = None
    next_blocking_at: AwareDatetime | None = None


class QuoteFacts(Contract):
    bid: Money
    ask: Money
    exact_mid: Money
    source: Literal["alpaca"] = "alpaca"
    feed: Literal["iex"] = "iex"
    event_at: AwareDatetime
    collected_at: AwareDatetime
    session_date: date
    admission_generation: Generation
    unit_epoch: Generation


class EconomicFacts(Contract):
    coin_id: Identifier
    provider_asset_id: str = Field(min_length=1, max_length=128)
    symbol: str = Field(min_length=1, max_length=10)
    company_name: str = Field(min_length=1, max_length=256)
    listing_exchange: Literal["NYSE", "NASDAQ"]
    currency: Literal["USD"] = "USD"
    side: Side
    quantity: Money
    bid: Money
    ask: Money
    exact_mid: Money
    exec_price: Money
    source: Literal["alpaca"] = "alpaca"
    feed: Literal["iex"] = "iex"
    event_at: AwareDatetime
    collected_at: AwareDatetime
    observed_at: AwareDatetime
    age_seconds: int = Field(ge=0, strict=True)
    notional: Money
    fee: Money = Field(default=Decimal("0"), ge=0, le=0)
    cash_delta: Money
    cash_before: Money
    cash_after: Money
    held_before: Money
    held_after: Money
    session_date: date
    session_opens_at: AwareDatetime
    session_closes_at: AwareDatetime
    authority: AuthorityIdentity


class QuoteOut(EconomicFacts):
    valid_until: AwareDatetime


class FillOut(EconomicFacts):
    """Saved historical projection; no renewed execution deadline."""

    schema_version: Literal[1] = 1
    trade_id: Identifier
    executed_at: AwareDatetime


UnavailableCode = Literal[
    "permission_unavailable",
    "action_unavailable",
    "units_changed",
    "halted",
    "frozen",
    "status_unavailable",
    "session_unavailable",
    "market_closed",
    "quote_unavailable",
    "quote_stale",
    "receipt_unavailable",
]
RangeCode = Literal[
    "invalid_quantity", "insufficient_cash", "insufficient_holding", "numeric_range"
]


class RefusalOut(Contract):
    code: UnavailableCode | RangeCode | Literal["idempotency_conflict"]


class PriceChangedOut(Contract):
    code: Literal["price_changed"] = "price_changed"
    previous_exec_price: Money
    previous_cash_delta: Money
    exec_price_change: Money
    cash_delta_change: Money
    quote: QuoteOut


class ContextOut(Contract):
    coin_id: Identifier
    provider_asset_id: str = Field(min_length=1, max_length=128)
    symbol: str = Field(min_length=1, max_length=10)
    company_name: str = Field(min_length=1, max_length=256)
    listing_exchange: Literal["NYSE", "NASDAQ"]
    observed_at: AwareDatetime
    cash: Money
    held_quantity: Money
    buy_max_quantity: Money
    quote: QuoteFacts | None
    session: SessionFacts
    status: StatusFacts
    action: ActionFacts
    authority: AuthorityIdentity | None
    execution_enabled: bool = False
    execution_reason: UnavailableCode | Literal["available"]
    valid_until: AwareDatetime | None
