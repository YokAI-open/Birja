from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.fake_prices import BASE_MIDS, fake_tickers, make_fake_source
from app.services.price_rules import mid_from_ticker

NOW = datetime(2026, 10, 28, 12, 0, 5, tzinfo=UTC)


def test_every_entry_is_accepted_and_close_to_base() -> None:
    result = fake_tickers(list(BASE_MIDS), NOW)
    assert set(result) == set(BASE_MIDS)
    for pair, entry in result.items():
        mid = mid_from_ticker(entry)
        assert mid is not None
        assert abs(mid - BASE_MIDS[pair]) / BASE_MIDS[pair] <= Decimal("0.0051")


def test_same_minute_is_deterministic() -> None:
    later = datetime(2026, 10, 28, 12, 0, 50, tzinfo=UTC)
    assert fake_tickers(["XXBTZUSD"], NOW) == fake_tickers(["XXBTZUSD"], later)


def test_values_change_across_minutes() -> None:
    next_min = datetime(2026, 10, 28, 12, 1, 5, tzinfo=UTC)
    assert fake_tickers(["XXBTZUSD"], NOW) != fake_tickers(["XXBTZUSD"], next_min)


def test_unknown_pair_omitted() -> None:
    assert list(fake_tickers(["XXBTZUSD", "NOPEUSD"], NOW)) == ["XXBTZUSD"]


@pytest.mark.asyncio
async def test_make_fake_source_is_async_callable() -> None:
    source = make_fake_source(lambda: NOW)
    result = await source(["SOLUSD"])
    assert list(result) == ["SOLUSD"]
