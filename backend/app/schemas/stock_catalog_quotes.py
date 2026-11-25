"""Display evidence and owned trade contracts for exact catalog identities."""

from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from app.schemas.portfolios import PortfolioId
from app.schemas.stock_catalog import CatalogId, CatalogIdInput, StockCatalogItem
from app.schemas.stock_trades import ExpectedPrice, Money, Side, WholeQuantity


class CatalogQuoteReason(StrEnum):
    READY = "ready"
    MISSING_PERMISSION = "missing_permission"
    MAPPING_REVIEW = "mapping_review"
    IDENTITY_REVIEW = "identity_review"
    MARKET_CLOSED = "market_closed"
    SESSION_UNAVAILABLE = "session_unavailable"
    QUOTE_UNAVAILABLE = "quote_unavailable"
    PRICE_DISABLED = "price_disabled"
    THROTTLED = "throttled"
    SOURCE_ERROR = "source_error"
    FAILED_CHECK = "failed_check"
    QUEUE_FULL = "queue_full"


CatalogExecutionReason = Literal[
    "available",
    "read_only",
    "permission_unavailable",
    "market_closed",
    "session_unavailable",
    "halted",
    "status_unavailable",
    "action_unavailable",
    "units_changed",
    "quote_unavailable",
    "quote_stale",
]


class CatalogQuoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    listing_version: CatalogIdInput


class CatalogOrderIn(CatalogQuoteIn):
    side: Side
    quantity: WholeQuantity


PreviewToken = Annotated[
    str, Field(pattern=r"^[1-9][0-9]{0,18}\.(?:0|[1-9][0-9]{0,15})\.[a-f0-9]{64}$")
]


class CatalogConfirmIn(CatalogOrderIn):
    expected_exec_price: ExpectedPrice
    idempotency_key: UUID
    preview_token: PreviewToken | None = None


class CatalogConfirmRequest(CatalogConfirmIn):
    preview_token: PreviewToken


class CatalogSessionOut(BaseModel):
    state: Literal["open", "closed", "unknown"]
    opens_at: AwareDatetime | None
    closes_at: AwareDatetime | None
    next_open_at: AwareDatetime | None


class CatalogPriceOut(BaseModel):
    bid: Money
    ask: Money
    mid: Money
    event_at: AwareDatetime
    collected_at: AwareDatetime
    valid_until: AwareDatetime
    source: Literal["alpaca"] = "alpaca"
    feed: Literal["iex"] = "iex"
    currency: Literal["USD"] = "USD"


class CatalogQuoteOut(BaseModel):
    listing: StockCatalogItem
    session: CatalogSessionOut
    quote: CatalogPriceOut | None
    reason: CatalogQuoteReason
    read_only: bool
    execution_reason: CatalogExecutionReason


class CatalogTradeContextOut(CatalogQuoteOut):
    portfolio_id: PortfolioId
    cash: Money
    held_quantity: Money
    buy_max_quantity: Money


class CatalogEconomics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    catalog_id: CatalogId
    listing_version: CatalogId
    portfolio_id: PortfolioId
    symbol: str = Field(pattern=r"^[A-Z0-9][A-Z0-9.$^+/=-]{0,13}$")
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


class CatalogPreviewOut(CatalogEconomics):
    valid_until: AwareDatetime
    preview_token: PreviewToken


class CatalogFillOut(CatalogEconomics):
    schema_version: Literal[1] = 1
    trade_id: CatalogId
    executed_at: AwareDatetime


class CatalogPriceChangedOut(BaseModel):
    code: Literal["price_changed"] = "price_changed"
    previous_exec_price: Money
    previous_cash_delta: Money
    exec_price_change: Money
    cash_delta_change: Money
    quote: CatalogPreviewOut
