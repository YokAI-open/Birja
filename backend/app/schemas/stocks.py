"""Immutable discovery contract; monetary values serialize as decimal strings."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


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
        "Birja uses simulated execution; stock trading is not enabled yet."
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
    # No persisted, verified halt/action facts exist in Phase7. An open calendar
    # and a granted status product must never be promoted to normal trading.
    state: Literal["unknown"] = "unknown"
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
    execution_enabled: Literal[False] = False
    execution_reason: Literal["phase_disabled"] = "phase_disabled"
    quote_reason: Literal[
        "permission_unavailable", "missing", "stale", "session_unavailable", "recent"
    ]
    session_reason: Literal["open", "closed", "unknown"]
    status_reason: Literal["unknown"] = "unknown"


class StocksResponse(FrozenModel):
    server_now: AwareDatetime
    admission: StockAdmission
    attribution: StockAttribution
    items: tuple[StockItem, ...]
