"""Exact stock quote values and the regular-session consumer contract."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation, localcontext
from typing import Protocol

CURATED_SYMBOLS = frozenset(
    [
        "AAPL",
        "MSFT",
        "NVDA",
        "AMZN",
        "GOOGL",
        "META",
        "TSLA",
        "AVGO",
        "AMD",
        "COST",
        "JPM",
        "V",
        "JNJ",
        "PG",
        "KO",
        "XOM",
        "CVX",
        "HD",
        "MCD",
        "DIS",
    ]
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


def utc(value: object) -> bool:
    return isinstance(value, datetime) and value.utcoffset() == timedelta(0)


def verified_mapping(mapping: StockMapping, now: datetime) -> bool:
    return (
        type(mapping.coin_id) is int
        and mapping.coin_id > 0
        and mapping.symbol in CURATED_SYMBOLS
        and isinstance(mapping.provider_asset_id, str)
        and 0 < len(mapping.provider_asset_id.strip()) <= 128
        and utc(mapping.provider_verified_at)
        and mapping.provider_verified_at is not None
        and mapping.provider_verified_at <= now
        and mapping.listing_exchange in ("NYSE", "NASDAQ")
    )


def _side(value: object) -> Decimal | None:
    if type(value) is int:
        value = Decimal(value)
    if not isinstance(value, Decimal) or not value.is_finite():
        return None
    if not Decimal("0") < value < Decimal("1e12"):
        return None
    try:
        if value.quantize(Decimal("1e-8")) != value:
            return None
    except InvalidOperation:
        return None
    return value


def validate_quote(
    raw: RawStockQuote, collected_at: datetime, admission_generation: int
) -> ValidatedStockQuote | None:
    if (
        not utc(collected_at)
        or not verified_mapping(raw.mapping, collected_at)
        or type(admission_generation) is not int
        or admission_generation <= 0
        or raw.source != "alpaca"
        or raw.feed != "iex"
        or raw.conditions not in (["R"], ["R", "R"])
        or raw.bid_exchange != "V"
        or raw.ask_exchange != "V"
        or raw.tape != ("C" if raw.mapping.listing_exchange == "NASDAQ" else "A")
        or type(raw.bid_size) is not int
        or type(raw.ask_size) is not int
        or not 0 < raw.bid_size <= 4294967295
        or not 0 < raw.ask_size <= 4294967295
        or not isinstance(raw.event_at, datetime)
        or not utc(raw.event_at)
        or not timedelta(0) <= collected_at - raw.event_at < timedelta(seconds=120)
    ):
        return None
    bid, ask = _side(raw.bid), _side(raw.ask)
    if bid is None or ask is None or bid > ask:
        return None
    with localcontext() as context:
        context.prec = 40
        mid = ((bid + ask) / 2).quantize(Decimal("1e-8"), rounding=ROUND_HALF_EVEN)
    return ValidatedStockQuote(
        raw.mapping.coin_id,
        raw.mapping.symbol,
        bid,
        ask,
        mid,
        raw.event_at,
        collected_at,
        raw.event_at.date(),
        admission_generation,
    )


def quote_eligibility(
    quote: ValidatedStockQuote, session: RegularSessionBounds | None, now: datetime
) -> bool:
    # Session authority/review is evaluated by07-08 before passing these bounds.
    # This predicate establishes neither permission nor halt/action eligibility.
    if session is None or not utc(now) or not utc(quote.event_at):
        return False
    opens, closes = session.opens_at, session.closes_at
    return (
        opens is not None
        and closes is not None
        and utc(opens)
        and utc(closes)
        and session.session_date == quote.session_date == quote.event_at.date()
        and opens <= quote.event_at <= now < closes
        and timedelta(0) <= now - quote.event_at < timedelta(seconds=120)
    )
