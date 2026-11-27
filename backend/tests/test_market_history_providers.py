from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
import pytest

from app.services.market_history import (
    HistoryWindow,
    crypto_history_window,
    equity_history_window,
    normalize_history,
)
from app.services.market_history_providers import (
    COIN_METRICS_HISTORY_URL,
    IEX_BARS_URL,
    KRAKEN_OHLC_URL,
    MAX_HISTORY_RESPONSE_BYTES,
    HistoryProviderError,
    fetch_coin_metrics_history,
    fetch_iex_history,
    fetch_kraken_history,
)
from app.services.stock_sessions import RegularSession

_NOW = datetime(2026, 11, 24, 16, 2, tzinfo=UTC)
_PAIR = "XXBTZUSD"


def _window() -> HistoryWindow:
    day = _NOW.date()
    row = RegularSession(
        "NASDAQ",
        day,
        _NOW.replace(hour=14, minute=30),
        _NOW.replace(hour=21, minute=0),
        date(2026, 1, 1),
        date(2026, 12, 31),
        5,
    )
    window = equity_history_window(
        "1D", _NOW, "NASDAQ", [row], calendar_generation=5, identity_since=None
    )
    assert window is not None
    return window


def _row(start: datetime, price: str) -> list[object]:
    return [int(start.timestamp()), "1", "1", "1", price, "1", "1", 2]


@pytest.mark.parametrize(
    ("range", "frequency", "metric", "interval"),
    [
        ("1D", "1m", "ReferenceRateUSD", 5),
        ("1W", "1h", "ReferenceRateUSD", 60),
        ("1M", "1d", "PriceUSD", 1440),
    ],
)
async def test_coin_metrics_uses_observation_times_and_daily_closing_dates(
    range, frequency, metric, interval
) -> None:
    window = crypto_history_window(range, _NOW, "coin_metrics")
    published_at = window.end_at
    provider_time = published_at - window.step if range == "1M" else published_at
    attempts = 0

    async def reserve() -> None:
        nonlocal attempts
        attempts += 1

    def upstream(request: httpx.Request) -> httpx.Response:
        assert attempts == 1
        assert str(request.url).split("?")[0] == COIN_METRICS_HISTORY_URL
        assert dict(request.url.params) == {
            "assets": "btc",
            "metrics": metric,
            "frequency": frequency,
            "start_time": (
                window.request_start_at + (timedelta() if range == "1M" else window.step)
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time": provider_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "page_size": "1500",
        }
        stamps = [provider_time]
        if range == "1D":
            stamps.insert(0, provider_time - timedelta(minutes=1))
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "asset": "btc",
                        "time": stamp.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
                        metric: "65000.12345678901255",
                    }
                    for stamp in stamps
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        batch = await fetch_coin_metrics_history(client, "btc", window, before_attempt=reserve)
    series = normalize_history(window, batch)
    assert series.source == "coin_metrics"
    assert series.interval_minutes == interval
    assert series.as_of == published_at
    assert len(series.points) == 1
    assert series.points[0].close == Decimal("65000.123456789013")
    assert series.points[0].starts_at == published_at - timedelta(minutes=interval)


@pytest.mark.parametrize(
    ("asset", "price", "sort_times"),
    [("eth", "65000", True), ("btc", "0", True), ("btc", "65000", False)],
)
async def test_coin_metrics_rejects_wrong_asset_bad_price_or_unordered_data(
    asset, price, sort_times
) -> None:
    window = crypto_history_window("1D", _NOW, "coin_metrics")
    stamps = [window.end_at - window.step, window.end_at]
    if not sort_times:
        stamps.reverse()
    rows = [
        {"asset": asset, "time": stamp.isoformat(), "ReferenceRateUSD": price} for stamp in stamps
    ]
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json={"data": rows}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(HistoryProviderError):
            await fetch_coin_metrics_history(client, "btc", window)


async def test_coin_metrics_does_not_follow_pagination_and_marks_partial() -> None:
    window = crypto_history_window("1W", _NOW, "coin_metrics")
    attempts = 0

    def upstream(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "asset": "btc",
                        "time": window.end_at.isoformat(),
                        "ReferenceRateUSD": "60000",
                    }
                ],
                "next_page_url": "https://community-api.coinmetrics.io/next",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        batch = await fetch_coin_metrics_history(client, "btc", window)
    assert attempts == 1
    assert normalize_history(window, batch).coverage == "partial"


@pytest.mark.asyncio
async def test_kraken_selects_exact_usd_pair_and_always_discards_last_row() -> None:
    window = crypto_history_window("1D", _NOW)
    pair = _PAIR
    paid = False

    async def reserve() -> None:
        nonlocal paid
        paid = True

    def upstream(request: httpx.Request) -> httpx.Response:
        assert paid
        assert request.method == "GET" and str(request.url).split("?")[0] == KRAKEN_OHLC_URL
        assert request.url.params["pair"] == pair and request.url.params["interval"] == "5"
        assert request.url.params["since"] == str(int(window.request_start_at.timestamp()))
        assert request.headers["Accept-Encoding"] == "identity"
        return httpx.Response(
            200,
            json={
                "error": [],
                "result": {
                    pair: [
                        _row(window.slots[-2].start, "65000.12345678"),
                        _row(window.slots[-1].start, "900000"),
                    ],
                    "last": 1,
                },
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        batch = await fetch_kraken_history(client, pair, window, before_attempt=reserve)
    assert len(batch.bars) == 1
    assert batch.bars[0].close == Decimal("65000.12345678")
    assert normalize_history(window, batch).timeliness == "delayed"


@pytest.mark.parametrize(
    ("returned_key", "close"),
    [("XETHZUSD", "12"), (_PAIR, "0"), (_PAIR, "-1"), (_PAIR, "1E200")],
)
@pytest.mark.asyncio
async def test_kraken_rejects_mismatched_pair_and_invalid_close(
    returned_key: str, close: str
) -> None:
    window = crypto_history_window("1D", _NOW)
    payload = {"error": [], "result": {returned_key: [_row(window.start_at, close)], "last": 1}}
    transport = httpx.MockTransport(lambda _: httpx.Response(200, json=payload))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(HistoryProviderError):
            await fetch_kraken_history(client, _PAIR, window)


@pytest.mark.asyncio
async def test_iex_split_adjustment_exact_identity_and_bounded_pages() -> None:
    window = _window()
    requests = 0
    booked = 0

    async def reserve() -> None:
        nonlocal booked
        booked += 1

    def upstream(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        assert booked == requests
        assert request.method == "GET" and str(request.url).split("?")[0] == IEX_BARS_URL
        assert request.url.params == httpx.QueryParams(
            {
                "symbols": "AAPL",
                "timeframe": "5Min",
                "feed": "iex",
                "currency": "USD",
                "adjustment": "split",
                "asof": "2026-11-24",
                "start": window.request_start_at.isoformat(),
                "end": window.end_at.isoformat(),
                "limit": "1000",
                "sort": "asc",
                **({"page_token": "cursor-1"} if requests == 2 else {}),
            }
        )
        stamp = window.slots[-3 + requests].start.isoformat()
        return httpx.Response(
            200,
            content=(
                f'{{"bars":{{"AAPL":[{{"t":"{stamp}","c":123.123456789012}}]}},'
                f'"next_page_token":"cursor-{requests}"}}'
            ).encode(),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        batch = await fetch_iex_history(client, "AAPL", window, before_attempt=reserve)
    assert requests == booked == 2 and batch.complete is False
    assert all(bar.close == Decimal("123.123456789012") for bar in batch.bars)
    assert normalize_history(window, batch).coverage == "partial"


@pytest.mark.parametrize(
    "body",
    [
        b'{"bars":{"MSFT":[]}}',
        b'{"bars":{"AAPL":[],"AAPL":[]}}',
        b'{"bars":{"AAPL":[{"t":"2026-11-24T15:55:00","c":120}]}}',
        b'{"bars":{"AAPL":[{"t":"2026-11-24T15:55:00Z","c":"120"}]}}',
        b'{"bars":{"AAPL":[{"t":"2026-11-24T15:55:00Z","c":false}]}}',
        b'{"bars":{"AAPL":[{"t":"2026-11-24T15:55:00Z","c":NaN}]}}',
        b'{"bars":{"AAPL":[{"t":"2026-11-24T15:55:00.000000001Z","c":120}]}}',
    ],
)
@pytest.mark.asyncio
async def test_iex_rejects_malformed_and_wrong_identity(body: bytes) -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    ) as client:
        with pytest.raises(HistoryProviderError):
            await fetch_iex_history(client, "AAPL", _window())


@pytest.mark.asyncio
async def test_iex_raw_row_count_and_repeated_cursor() -> None:
    bodies = [
        {"bars": {"AAPL": [{"t": "2026-11-24T15:55:00Z", "c": 120}] * 1001}},
        {"bars": {}, "next_page_token": "repeat"},
    ]
    for body, reason in zip(bodies, ("row count", "cursor"), strict=True):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _, body=body: httpx.Response(200, json=body))
        ) as client:
            with pytest.raises(HistoryProviderError, match=reason):
                await fetch_iex_history(client, "AAPL", _window())


class _Stream(httpx.AsyncByteStream):
    streamed = 0

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for _ in range(48):
            self.streamed += 8192
            yield b" " * 8192


@pytest.mark.parametrize("limit", [15000, MAX_HISTORY_RESPONSE_BYTES])
@pytest.mark.asyncio
async def test_history_stops_streaming_at_byte_limit(limit: int) -> None:
    stream = _Stream()
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, stream=stream))
    ) as client:
        with pytest.raises(HistoryProviderError, match="byte limit"):
            await fetch_iex_history(client, "AAPL", _window(), max_bytes=limit)
    assert limit < stream.streamed <= limit + 8192


@pytest.mark.asyncio
async def test_iex_does_not_follow_redirect_with_private_headers() -> None:
    def upstream(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "data.alpaca.markets"
        return httpx.Response(302, headers={"location": "https://redirect.example/"})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(upstream), follow_redirects=True
    ) as client:
        with pytest.raises(HistoryProviderError) as result:
            await fetch_iex_history(client, "AAPL", _window())
    assert result.value.status == 302


@pytest.mark.asyncio
async def test_iex_does_not_fetch_without_attempt_reservation() -> None:
    def upstream(_request: httpx.Request) -> httpx.Response:
        pytest.fail("blocked attempt reached upstream")

    async def reserve() -> None:
        raise RuntimeError("fixture budget exhausted")

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        with pytest.raises(RuntimeError, match="fixture budget exhausted"):
            await fetch_iex_history(client, "AAPL", _window(), before_attempt=reserve)
