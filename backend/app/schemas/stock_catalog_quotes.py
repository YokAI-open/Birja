"""Display quotes and a read-only portfolio context for catalog identities."""

from enum import StrEnum
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict

from app.schemas.portfolios import PortfolioId
from app.schemas.stock_catalog import CatalogIdInput, StockCatalogItem
from app.schemas.stock_trades import Money


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


class CatalogQuoteIn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    listing_version: CatalogIdInput


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


class CatalogTradeContextOut(CatalogQuoteOut):
    portfolio_id: PortfolioId
    read_only: Literal[True] = True
