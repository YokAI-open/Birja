"""Fake Ticker source for dev and CI e2e (never a route, refused in prod by Settings).

Produces Kraken-shaped entries for the 15 seeded pairs so the full stack can run
without calling Kraken. Values move at most 0.5% around a base mid, changing each
minute so the UI visibly updates, far below the 25% spike rule.
"""

from collections.abc import Callable, Sequence
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

from app.services.kraken import TickerSource

BASE_MIDS: dict[str, Decimal] = {
    "XXBTZUSD": Decimal("81042"),
    "XETHZUSD": Decimal("2361"),
    "SOLUSD": Decimal("102.2"),
    "XXRPZUSD": Decimal("1.329"),
    "BNBUSD": Decimal("747"),
    "ADAUSD": Decimal("0.2066"),
    "XDGUSD": Decimal("0.07998"),
    "TRXUSD": Decimal("0.3308"),
    "AVAXUSD": Decimal("9.015"),
    "LINKUSD": Decimal("11.75"),
    "DOTUSD": Decimal("1.008"),
    "XLTCZUSD": Decimal("57.65"),
    "BCHUSD": Decimal("297.1"),
    "XXLMZUSD": Decimal("0.1716"),
    "ATOMUSD": Decimal("1.632"),
}

_QUANTUM = Decimal("1e-8")


def fake_tickers(pairs: Sequence[str], now: datetime) -> dict[str, Any]:
    step = (int(now.timestamp()) // 60) % 11 - 5
    factor = 1 + Decimal(step) / 1000
    result: dict[str, Any] = {}
    for pair in pairs:
        base = BASE_MIDS.get(pair)
        if base is None:
            continue
        mid = base * factor
        bid = (mid * Decimal("0.9995")).quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
        ask = (mid * Decimal("1.0005")).quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
        result[pair] = {
            "a": [str(ask), "1", "1.000"],
            "b": [str(bid), "1", "1.000"],
            "c": [str(mid), "0.1"],
        }
    return result


def make_fake_source(now: Callable[[], datetime]) -> TickerSource:
    async def source(pairs: Sequence[str]) -> dict[str, Any]:
        return fake_tickers(pairs, now())

    return source
