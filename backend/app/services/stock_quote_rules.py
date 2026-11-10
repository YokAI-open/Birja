"""Exact stock quote values and the regular-session consumer contract."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol

CURATED_SYMBOLS = frozenset(
    ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "AMD", "COST", "JPM", "V", "JNJ", "PG", "KO", "XOM", "CVX", "HD", "MCD", "DIS"]
)


class RegularSessionBounds(Protocol):
    @property
    def session_date(self) -> date: ...

    @property
    def opens_at(self) -> datetime | None: ...

    @property
    def closes_at(self) -> datetime | None: ...


@dataclass(frozen=True)
class StockMapping:
    coin_id: int
    symbol: str
    provider_asset_id: str | None
    provider_verified_at: datetime | None
    listing_exchange: str


@dataclass(frozen=True)
class RawStockQuote:
    mapping: StockMapping
    bid: object
    ask: object
    event_at: object
    conditions: object
    bid_exchange: object = "V"
    ask_exchange: object = "V"
    tape: object = "C"
    bid_size: object = 1
    ask_size: object = 1
    source: str = "alpaca"
    feed: str = "iex"


@dataclass(frozen=True)
class ValidatedStockQuote:
    coin_id: int
    symbol: str
    bid: Decimal
    ask: Decimal
    mid: Decimal
    event_at: datetime
    collected_at: datetime
    session_date: date
    admission_generation: int
    source: str = "alpaca"
    feed: str = "iex"


def validate_quote(
    raw: RawStockQuote, collected_at: datetime, admission_generation: int
) -> ValidatedStockQuote | None:
    return None


def quote_eligibility(
    quote: ValidatedStockQuote, session: RegularSessionBounds | None, now: datetime
) -> bool:
    return False
