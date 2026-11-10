"""Bounded IEX-only latest quote boundary."""

import asyncio
import json
import random
import re
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_quote_rules import (
    RawStockQuote,
    StockMapping,
    ValidatedStockQuote,
    validate_quote,
    verified_mapping,
)

LATEST_QUOTES_URL = "https://data.alpaca.markets/v2/stocks/quotes/latest"
_JITTER = random.SystemRandom().random
_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.(\d{1,9}))?(?:Z|\+00:00)$")


class AlpacaError(Exception):
    def __init__(self, reason: str, *, retryable: bool = False) -> None:
        super().__init__(reason)
        self.retryable = retryable


@dataclass(frozen=True)
class QuoteBatch:
    quotes: tuple[ValidatedStockQuote, ...]
    rejected: dict[str, str]


def _admitted(
    admission: ProductAdmission, now: datetime, *, account: str = "birja", server: str = "birja"
) -> None:
    if not evaluate_admission(
        admission, "quotes", "collection", now, account=account, server=server
    ).allowed:
        raise AlpacaError("admission")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def _number(token: str) -> Decimal:
    if len(token) > 128:
        raise ValueError("number_limit")
    try:
        value = Decimal(token)
    except ArithmeticError:
        raise ValueError("invalid_number") from None
    if not value.is_finite():
        raise ValueError("nonfinite")
    return value


def _constant(token: str) -> None:
    raise ValueError("nonfinite")


def _decode(raw: bytes) -> dict[str, Any]:
    # Check nesting before the JSON decoder recurses. Ignore brackets in strings.
    depth, in_string, escaped = 0, False, False
    for char in raw:
        if in_string:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                in_string = False
        elif char == 34:
            in_string = True
        elif char in (91, 123):
            depth += 1
            if depth > 8:
                raise AlpacaError("response_depth")
        elif char in (93, 125):
            depth -= 1
    try:
        body = json.loads(
            raw, parse_float=_number, parse_constant=_constant, object_pairs_hook=_pairs
        )
    except ValueError, RecursionError:
        raise AlpacaError("invalid_json") from None
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("quotes"), dict)
        or body.get("feed", "iex") != "iex"
        or body.get("currency", "USD") != "USD"
        or len(body["quotes"]) > 20
    ):
        raise AlpacaError("invalid_body")
    return body["quotes"]  # type: ignore[no-any-return]


def _event(value: object, now: datetime) -> datetime | None:
    if not isinstance(value, str):
        return None
    match = _STAMP.fullmatch(value)
    if match is None:
        return None
    try:
        event = datetime.fromisoformat(value)
    except ValueError:
        return None
    # datetime/PostgreSQL store microseconds. Floor nanoseconds conservatively,
    # but do not let a sub-microsecond future event become equal to current UTC.
    fraction = match.group(1) or ""
    if event == now and any(digit != "0" for digit in fraction[6:]):
        return None
    return event


def _batch(
    entries: dict[str, Any],
    symbols: Sequence[StockMapping],
    admission: ProductAdmission,
    collected_at: datetime,
) -> QuoteBatch:
    mappings = {mapping.symbol: mapping for mapping in symbols}
    if entries.keys() - mappings.keys():
        raise AlpacaError("unexpected_symbol")
    accepted: list[ValidatedStockQuote] = []
    rejected: dict[str, str] = {}
    for symbol, mapping in mappings.items():
        entry = entries.get(symbol)
        if entry is None:
            rejected[symbol] = "missing"
            continue
        quote = None
        if isinstance(entry, dict) and entry.get("S", symbol) == symbol:
            quote = validate_quote(
                RawStockQuote(
                    mapping,
                    entry.get("bp"),
                    entry.get("ap"),
                    _event(entry.get("t"), collected_at),
                    entry.get("c"),
                    entry.get("bx"),
                    entry.get("ax"),
                    entry.get("z"),
                    entry.get("bs"),
                    entry.get("as"),
                    entry.get("source", "alpaca"),
                    entry.get("feed", "iex"),
                ),
                collected_at,
                admission.generation,
            )
        if quote is None:
            rejected[symbol] = "invalid"
        else:
            accepted.append(quote)
    return QuoteBatch(tuple(accepted), rejected)


def _retry_after(value: str | None, now: datetime) -> float:
    if value is None:
        return 0
    try:
        seconds = Decimal(value)
        if seconds.is_finite() and seconds >= 0:
            return float(min(seconds, Decimal("3600")))
        return 0
    except ValueError, ArithmeticError:
        try:
            stamp = parsedate_to_datetime(value)
            return min(3600, max(0, (stamp - now).total_seconds()))
        except ValueError, TypeError, OverflowError:
            return 0


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
    account: str = "birja",
    server: str = "birja",
) -> QuoteBatch:
    """Use only a verified curated mapping; injected client owns private headers.

    Official schema: https://docs.alpaca.markets/us/reference/stocklatestquotes-1
    Conditions: alpacahq/cli api/specs/market-data-api.json stock_quote.c permits
    one flag for both sides or separate bid/ask flags. Only R/RR is accepted:
    NYSE Daily_TAQ_Client_Spec_v3.3 quote condition R = regular two-sided open.
    Unknown conditions fail closed; real permitted account coverage is07-14.
    """
    started = now()
    _admitted(admission, started, account=account, server=server)
    if (
        not 1 <= len(symbols) <= 20
        or len({m.symbol for m in symbols}) != len(symbols)
        or len({m.coin_id for m in symbols}) != len(symbols)
        or len({m.provider_asset_id for m in symbols}) != len(symbols)
        or not all(verified_mapping(m, started) for m in symbols)
        or type(attempts) is not int
        or not 1 <= attempts <= 3
        or type(max_bytes) is not int
        or not 1 <= max_bytes <= 1048576
        or not 0 < budget_seconds <= 10
    ):
        raise AlpacaError("invalid_request")
    max_bytes = min(max_bytes, admission.quota["max_response_bytes"])
    attempts = min(attempts, admission.quota["requests_per_minute"])
    sleep = sleep or asyncio.sleep
    jitter = jitter or _JITTER
    remaining = budget_seconds
    try:
        async with asyncio.timeout(budget_seconds):
            for attempt in range(attempts):
                _admitted(admission, now(), account=account, server=server)
                retry_after = 0.0
                try:
                    async with http.stream(
                        "GET",
                        LATEST_QUOTES_URL,
                        params={
                            "symbols": ",".join(m.symbol for m in symbols),
                            "feed": "iex",
                            "currency": "USD",
                        },
                        timeout=min(remaining, 5),
                        follow_redirects=False,
                    ) as response:
                        status = response.status_code
                        if status != 200:
                            if status == 429 or 500 <= status <= 599:
                                retry_after = _retry_after(
                                    response.headers.get("Retry-After"), now()
                                )
                                raise AlpacaError(f"http_{status}", retryable=True)
                            raise AlpacaError(f"http_{status}")
                        content = bytearray()
                        async for chunk in response.aiter_bytes(chunk_size=max_bytes + 1):
                            content.extend(chunk)
                            if len(content) > max_bytes:
                                raise AlpacaError("response_limit")
                    collected_at = now()
                    _admitted(admission, collected_at, account=account, server=server)
                    return _batch(_decode(bytes(content)), symbols, admission, collected_at)
                except httpx.TransportError as exc:
                    last = AlpacaError(type(exc).__name__, retryable=True)
                except AlpacaError as exc:
                    if not exc.retryable:
                        raise
                    last = exc
                if attempt == attempts - 1:
                    raise last
                delay = max(retry_after, 2**attempt + min(1, max(0, jitter())))
                if delay >= remaining:
                    raise AlpacaError("retry_budget", retryable=True)
                remaining -= delay
                await sleep(delay)
    except TimeoutError:
        raise AlpacaError("cycle_budget", retryable=True) from None
    raise AlpacaError("no_attempts")  # unreachable with validated attempts
