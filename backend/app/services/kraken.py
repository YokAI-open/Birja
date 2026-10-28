"""Kraken public Ticker client with bounded retries (PRICE-03).

Kraken reports many failures as HTTP 200 with a non-empty ``error`` array, so
the body is always checked. Errors carry only Kraken's error strings, a status
code or an exception class name: never headers or URLs.
"""

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable, Sequence
from typing import Any

import httpx

TICKER_URL = "https://api.kraken.com/0/public/Ticker"
USER_AGENT = "birja-price-scheduler"
UNKNOWN_PAIR_ERROR = "Unknown asset pair"
NON_RETRYABLE_ERRORS = (UNKNOWN_PAIR_ERROR, "EGeneral:Invalid arguments")

logger = logging.getLogger(__name__)

_JITTER = random.SystemRandom().random

TickerSource = Callable[[Sequence[str]], Awaitable[dict[str, Any]]]


class KrakenError(Exception):
    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable


def _check(response: httpx.Response) -> dict[str, Any]:
    """Return the result dict or raise KrakenError with the right retryable flag."""
    status = response.status_code
    if status == 429 or status >= 500:
        raise KrakenError(f"http {status}", retryable=True)
    if status >= 400:
        raise KrakenError(f"http {status}", retryable=False)
    try:
        body = response.json()
    except ValueError:
        raise KrakenError("invalid json", retryable=True) from None
    if not isinstance(body, dict):
        raise KrakenError("unexpected body", retryable=True)
    errors = body.get("error")
    if errors:
        text = "; ".join(str(e) for e in errors) if isinstance(errors, list) else str(errors)
        fatal = any(marker in text for marker in NON_RETRYABLE_ERRORS)
        raise KrakenError(text, retryable=not fatal)
    result = body.get("result")
    if not isinstance(result, dict):
        raise KrakenError("missing result", retryable=True)
    return result


async def fetch_tickers(
    http: httpx.AsyncClient,
    pairs: Sequence[str],
    *,
    attempts: int = 3,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    jitter: Callable[[], float] = _JITTER,
) -> dict[str, Any]:
    """GET the Ticker for ``pairs``; returns body["result"] keyed by Kraken's response key."""
    last = KrakenError("no attempts made", retryable=True)
    for attempt in range(attempts):
        try:
            response = await http.get(
                TICKER_URL,
                params={"pair": ",".join(pairs)},
                headers={"User-Agent": USER_AGENT},
            )
            return _check(response)
        except httpx.TransportError as exc:  # includes timeouts
            last = KrakenError(type(exc).__name__, retryable=True)
        except KrakenError as exc:
            if not exc.retryable:
                raise
            last = exc
        if attempt < attempts - 1:
            await sleep(min(8, 2**attempt) + jitter())
    raise KrakenError(str(last), retryable=True)


async def fetch_tickers_isolated(
    http: httpx.AsyncClient,
    pairs: Sequence[str],
    *,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    jitter: Callable[[], float] = _JITTER,
) -> dict[str, Any]:
    """Like ``fetch_tickers``, but one unknown pair cannot fail the whole batch.

    Kraken rejects the entire multi-pair request when any pair is unknown (delisted or
    renamed). Then each pair is fetched on its own, once (at most one call per pair),
    and the successes are merged. Raises only when every pair fails.
    """
    try:
        return await fetch_tickers(http, pairs, sleep=sleep, jitter=jitter)
    except KrakenError as exc:
        if len(pairs) < 2 or UNKNOWN_PAIR_ERROR not in str(exc):
            raise
    merged: dict[str, Any] = {}
    for pair in pairs:
        try:
            merged.update(await fetch_tickers(http, [pair], attempts=1))
        except KrakenError:
            logger.warning("price pair unavailable: pair=%s", pair)
    if not merged:
        raise KrakenError("all pairs unavailable", retryable=False)
    return merged
