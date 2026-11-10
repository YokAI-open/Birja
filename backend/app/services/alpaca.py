"""Bounded IEX-only latest quote boundary."""

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

import httpx

from app.services.stock_admission import ProductAdmission
from app.services.stock_quote_rules import StockMapping, ValidatedStockQuote

LATEST_QUOTES_URL = "https://data.alpaca.markets/v2/stocks/quotes/latest"


class AlpacaError(Exception):
    def __init__(self, reason: str, *, retryable: bool = False) -> None:
        super().__init__(reason)
        self.retryable = retryable


@dataclass(frozen=True)
class QuoteBatch:
    quotes: tuple[ValidatedStockQuote, ...]
    rejected: dict[str, str]


async def fetch_iex_quotes(
    http: httpx.AsyncClient,
    symbols: Sequence[StockMapping],
    admission: ProductAdmission,
    now: Callable[[], datetime],
    *,
    attempts: int = 3,
    sleep: Callable[[float], Awaitable[None]] | None = None,
    jitter: Callable[[], float] | None = None,
    max_bytes: int = 262144,
    budget_seconds: float = 10,
) -> QuoteBatch:
    return QuoteBatch((), {symbol.symbol: "unavailable" for symbol in symbols})
