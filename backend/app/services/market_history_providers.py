"""Fixed-host historical data adapters with bounded response parsing."""

import json
import re
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import httpx

from app.services.market_history import HistoryBar, HistoryBatch, HistoryWindow, validate_close
from app.services.stock_catalog_sources import SYMBOL_PATTERN

KRAKEN_OHLC_URL = "https://api.kraken.com/0/public/OHLC"
IEX_BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
MAX_HISTORY_RESPONSE_BYTES = 256 * 1024
_IEX_ROWS = 1000
_IEX_PAGES = 2
_KRAKEN_ROWS = 720
_JSON_CHUNK_SIZE = 8192
_CLOSE_PATTERN = re.compile(r"[0-9]{1,18}(?:\.[0-9]{1,12})?")
_UTC_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6}0{0,3})?(?:Z|\+00:00)"
)
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

BeforeHistoryAttempt = Callable[[], Awaitable[None]]


class HistoryProviderError(ValueError):
    """Sanitized provider failure without response values or credentials."""

    def __init__(self, reason: str, *, status: int | None = None) -> None:
        super().__init__(reason)
        self.status = status


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = dict(pairs)
    if len(pairs) != len(result):
        raise HistoryProviderError("duplicate history object keys")
    return result


def _invalid_constant(_value: str) -> object:
    raise HistoryProviderError("invalid history number")


async def _get_json(
    http: httpx.AsyncClient,
    url: str,
    params: dict[str, str | int],
    before_attempt: BeforeHistoryAttempt | None,
    max_bytes: int,
) -> dict[str, Any]:
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_HISTORY_RESPONSE_BYTES:
        raise HistoryProviderError("invalid history body limit")
    if before_attempt is not None:
        await before_attempt()
    try:
        async with http.stream(
            "GET",
            url,
            params=params,
            headers={"Accept-Encoding": "identity"},
            follow_redirects=False,
        ) as response:
            if response.status_code != 200:
                raise HistoryProviderError(
                    "history HTTP request failed", status=response.status_code
                )
            encoding = response.headers.get("Content-Encoding", "identity")
            if encoding.lower() != "identity":
                raise HistoryProviderError("unexpected history response encoding")
            content = bytearray()
            async for chunk in response.aiter_bytes(chunk_size=_JSON_CHUNK_SIZE):
                if len(content) + len(chunk) > max_bytes:
                    raise HistoryProviderError("history response exceeds byte limit")
                content.extend(chunk)
    except httpx.HTTPError:
        raise HistoryProviderError("history transport failure") from None
    try:
        body = json.loads(
            content,
            parse_float=Decimal,
            parse_constant=_invalid_constant,
            object_pairs_hook=_unique_keys,
        )
    except ValueError, ArithmeticError, RecursionError:
        raise HistoryProviderError("invalid history JSON") from None
    if not isinstance(body, dict):
        raise HistoryProviderError("invalid history body")
    return body


def _kraken_bar(row: object) -> HistoryBar:
    if not isinstance(row, list) or len(row) != 8:
        raise HistoryProviderError("invalid Kraken history row")
    epoch = row[0]
    close = row[4]
    if type(epoch) is not int or not isinstance(close, str) or not _CLOSE_PATTERN.fullmatch(close):
        raise HistoryProviderError("invalid Kraken historical close")
    try:
        return HistoryBar(_EPOCH + timedelta(seconds=epoch), validate_close(Decimal(close)))
    except ValueError, ArithmeticError:
        raise HistoryProviderError("invalid Kraken history row") from None


async def fetch_kraken_history(
    http: httpx.AsyncClient,
    pair: str,
    window: HistoryWindow,
    *,
    before_attempt: BeforeHistoryAttempt | None = None,
    max_bytes: int = MAX_HISTORY_RESPONSE_BYTES,
) -> HistoryBatch:
    if window.source != "kraken" or not re.fullmatch(r"[A-Z0-9]{2,24}USD", pair):
        raise HistoryProviderError("invalid Kraken history request")
    body = await _get_json(
        http,
        KRAKEN_OHLC_URL,
        {
            "pair": pair,
            "interval": window.interval_minutes,
            "since": (window.request_start_at - _EPOCH) // timedelta(seconds=1),
        },
        before_attempt,
        max_bytes,
    )
    result = body.get("result")
    if body.get("error") != [] or not isinstance(result, dict):
        raise HistoryProviderError("invalid Kraken history result")
    if set(result) != {pair, "last"} or type(result["last"]) is not int or result["last"] < 0:
        raise HistoryProviderError("unexpected Kraken history identity")
    rows = result[pair]
    if not isinstance(rows, list) or not 1 <= len(rows) <= _KRAKEN_ROWS:
        raise HistoryProviderError("invalid Kraken history row count")
    bars = tuple(_kraken_bar(row) for row in rows)
    if any(left.starts_at > right.starts_at for left, right in zip(bars, bars[1:], strict=False)):
        raise HistoryProviderError("unordered Kraken history rows")
    return HistoryBatch(bars[:-1])


def _iex_bar(row: object) -> HistoryBar:
    if not isinstance(row, dict):
        raise HistoryProviderError("invalid IEX history row")
    stamp, close = row.get("t"), row.get("c")
    if not isinstance(stamp, str) or not _UTC_TIMESTAMP.fullmatch(stamp):
        raise HistoryProviderError("invalid IEX history timestamp")
    try:
        return HistoryBar(datetime.fromisoformat(stamp).astimezone(UTC), validate_close(close))
    except ValueError, ArithmeticError:
        raise HistoryProviderError("invalid IEX history row") from None


async def fetch_iex_history(
    http: httpx.AsyncClient,
    symbol: str,
    window: HistoryWindow,
    *,
    before_attempt: BeforeHistoryAttempt | None = None,
    max_bytes: int = MAX_HISTORY_RESPONSE_BYTES,
) -> HistoryBatch:
    if (
        window.source != "alpaca_iex"
        or window.reference_session is None
        or not re.fullmatch(SYMBOL_PATTERN, symbol)
    ):
        raise HistoryProviderError("invalid IEX history request")
    params: dict[str, str | int] = {
        "symbols": symbol,
        "timeframe": f"{window.interval_minutes}Min",
        "start": window.request_start_at.isoformat(),
        "end": window.end_at.isoformat(),
        "asof": window.reference_session.isoformat(),
        "feed": "iex",
        "currency": "USD",
        "adjustment": "split",
        "sort": "asc",
        "limit": _IEX_ROWS,
    }
    bars: list[HistoryBar] = []
    cursors: set[str] = set()
    for _ in range(_IEX_PAGES):
        body = await _get_json(http, IEX_BARS_URL, params, before_attempt, max_bytes)
        by_symbol = body.get("bars")
        if not isinstance(by_symbol, dict) or not set(by_symbol) <= {symbol}:
            raise HistoryProviderError("unexpected IEX history identity")
        rows = by_symbol.get(symbol, [])
        if not isinstance(rows, list) or len(rows) > _IEX_ROWS:
            raise HistoryProviderError("invalid IEX history row count")
        bars.extend(_iex_bar(row) for row in rows)
        cursor = body.get("next_page_token")
        if cursor is None:
            return HistoryBatch(tuple(bars))
        if (
            not isinstance(cursor, str)
            or not 1 <= len(cursor) <= 512
            or not cursor.isascii()
            or not cursor.isprintable()
            or cursor in cursors
        ):
            raise HistoryProviderError("invalid IEX history cursor")
        cursors.add(cursor)
        params["page_token"] = cursor
    return HistoryBatch(tuple(bars), complete=False)
