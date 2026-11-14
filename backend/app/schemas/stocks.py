"""Immutable discovery contract; monetary values serialize as decimal strings."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.schemas.stock_trades import UnavailableCode


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class StockAdmission(FrozenModel):
    state: Literal["approved", "unavailable"]
    generation: int | None = None
    valid_until: AwareDatetime | None = None


class StockAttribution(FrozenModel):
    label: Literal["IEX prices"] = "IEX prices"
    explanation: str = (
        "Single-venue IEX prices, not consolidated US market prices. "
        "Birja uses simulated execution. Orders require an open market and current verified data."
    )
    required_text: str = ""


class StockQuoteOut(FrozenModel):
    bid: Decimal
    ask: Decimal
    mid: Decimal
    event_at: AwareDatetime
    collected_at: AwareDatetime
    source: Literal["alpaca"] = "alpaca"
    feed: Literal["iex"] = "iex"
    age_seconds: int


class StockSessionOut(FrozenModel):
    state: Literal["open", "closed", "unknown"] = "unknown"
    opens_at: AwareDatetime | None = None
    closes_at: AwareDatetime | None = None
    next_open_at: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None
    timezone: Literal["America/New_York"] = "America/New_York"


class StockStatus(FrozenModel):
    state: Literal["normal", "halted", "frozen", "unknown"] = "unknown"
    observed_at: datetime | None = None
    valid_until: datetime | None = None


class StockActionOut(FrozenModel):
    state: Literal["current", "unknown", "reconciling", "suspended"] = "unknown"
    reason: Literal[
        "none",
        "monitor_unavailable",
        "source_gap",
        "unsupported",
        "fractional",
        "conflicting",
        "identity_change",
        "post_split_quote_missing",
    ] = "monitor_unavailable"
    epoch: int = Field(default=0, ge=0, le=9007199254740991, strict=True)
    checked_at: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None


class StockItem(FrozenModel):
    id: int
    symbol: str
    company_name: str
    listing_exchange: Literal["NYSE", "NASDAQ"]
    currency: Literal["USD"] = "USD"
    quote: StockQuoteOut | None = None
    session: StockSessionOut = StockSessionOut()
    status: StockStatus = StockStatus()
    action: StockActionOut = StockActionOut()
    valuation_reason: Literal[
        "available", "action_unavailable", "post_split_quote_missing", "quote_unavailable"
    ] = "action_unavailable"
    execution_enabled: bool = False
    execution_reason: UnavailableCode | Literal["available", "phase_disabled"] = "phase_disabled"
    quote_reason: Literal[
        "permission_unavailable", "missing", "stale", "session_unavailable", "recent"
    ]
    session_reason: Literal["open", "closed", "unknown"]
    status_reason: Literal["normal", "halted", "frozen", "unknown"] = "unknown"


class StocksResponse(FrozenModel):
    server_now: AwareDatetime
    admission: StockAdmission
    attribution: StockAttribution
    items: tuple[StockItem, ...]
