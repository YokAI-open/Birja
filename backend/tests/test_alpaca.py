"""External I/O is mocked exclusively at HTTP; no actual provider requests."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import httpx
import pytest
import respx

from app.services.alpaca import LATEST_QUOTES_URL, AlpacaError, fetch_iex_quotes
from tests.test_stock_admission import admitted
from tests.test_stock_quote_rules import MAPPING, NOW

BODY = (
    b'{"quotes":{"AAPL":{"bp":100.00000001,"ap":100.00000002,'
    b'"t":"2026-11-10T14:59:59.123456789Z","c":["R"],'
    b'"bx":"V","ax":"V","bs":1,"as":2,"z":"C"}}}'
)


class Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, seconds: float) -> None:
        self.delays.append(seconds)


async def test_exact_raw_json_explicit_feed_and_no_redirects() -> None:
    with respx.mock(assert_all_mocked=True) as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, content=BODY)
        async with httpx.AsyncClient() as http:
            result = await fetch_iex_quotes(http, [MAPPING], admitted(), lambda: NOW)
    assert result.rejected == {}
    (quote,) = result.quotes
    assert quote.bid == Decimal("100.00000001")
    assert quote.ask == Decimal("100.00000002")
    assert quote.event_at.microsecond == 123456  # floor nanoseconds, never make an event newer
    assert quote.collected_at == NOW
    assert dict(route.calls.last.request.url.params) == {
        "symbols": "AAPL",
        "feed": "iex",
        "currency": "USD",
    }


@pytest.mark.parametrize("status", [401, 403, 302])
async def test_fatal_status_never_retries_or_exposes_body(status: int) -> None:
    sleeper = Sleeper()
    with respx.mock(assert_all_mocked=True) as router:
        route = router.get(LATEST_QUOTES_URL).respond(
            status, text="secret-token", headers={"Location": "https://evil.invalid"}
        )
        async with httpx.AsyncClient() as http:
            with pytest.raises(AlpacaError) as exc:
                await fetch_iex_quotes(http, [MAPPING], admitted(), lambda: NOW, sleep=sleeper)
    assert "secret-token" not in str(exc.value)
    assert not exc.value.retryable
    assert route.call_count == 1 and sleeper.delays == []


async def test_rate_limit_retry_after_and_timeout_are_bounded() -> None:
    sleeper = Sleeper()
    with respx.mock(assert_all_mocked=True) as router:
        route = router.get(LATEST_QUOTES_URL).mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": "2"}),
                httpx.ConnectTimeout("secret-token"),
                httpx.Response(200, content=BODY),
            ]
        )
        async with httpx.AsyncClient() as http:
            result = await fetch_iex_quotes(
                http, [MAPPING], admitted(), lambda: NOW, sleep=sleeper, jitter=lambda: 0
            )
    assert len(result.quotes) == 1 and route.call_count == 3
    assert sleeper.delays == [2, 2]


@pytest.mark.parametrize(
    "body",
    [
        b"NaN",
        b'{"quotes":NaN}',
        b'{"quotes":[]}',
        b'{"quotes":{},"quotes":{}}',
        b'{"quotes":{"BAD":{}}}',
        b'{"quotes":{},"feed":"sip"}',
        b'{"quotes":{},"currency":"EUR"}',
        b"[" * 20 + b"]" * 20,
    ],
)
async def test_hostile_body_is_sanitized_failure(body: bytes) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        router.get(LATEST_QUOTES_URL).respond(200, content=body)
        async with httpx.AsyncClient() as http:
            with pytest.raises(AlpacaError):
                await fetch_iex_quotes(http, [MAPPING], admitted(), lambda: NOW)


@pytest.mark.parametrize(
    "body,reason",
    [
        (b'{"quotes":{}}', "missing"),
        (BODY.replace(b"100.00000001", b"0"), "invalid"),
        (BODY.replace(b"2026-11-10", b"2026-11-09"), "invalid"),
        (BODY.replace(b"14:59:59.123456789", b"15:00:00.000000001"), "invalid"),
        (BODY.replace(b'["R"]', b"[]"), "invalid"),
    ],
)
async def test_per_symbol_refusals_do_not_fabricate_quotes(body: bytes, reason: str) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        router.get(LATEST_QUOTES_URL).respond(200, content=body)
        async with httpx.AsyncClient() as http:
            result = await fetch_iex_quotes(http, [MAPPING], admitted(), lambda: NOW)
    assert not result.quotes and result.rejected == {"AAPL": reason}


async def test_partial_batch_keeps_valid_symbol() -> None:
    msft = replace(MAPPING, coin_id=17, symbol="MSFT", provider_asset_id="synthetic-msft")
    with respx.mock(assert_all_mocked=True) as router:
        router.get(LATEST_QUOTES_URL).respond(200, content=BODY)
        async with httpx.AsyncClient() as http:
            result = await fetch_iex_quotes(http, [MAPPING, msft], admitted(), lambda: NOW)
    assert [q.symbol for q in result.quotes] == ["AAPL"]
    assert result.rejected == {"MSFT": "missing"}


async def test_denied_unverified_duplicate_and_uncurated_never_call_http() -> None:
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: pytest.fail("must not call"))
    ) as http:
        for mappings, evidence in [
            ([MAPPING], replace(admitted(), state="revoked")),
            ([replace(MAPPING, provider_asset_id=None)], admitted()),
            ([replace(MAPPING, symbol="FAKE")], admitted()),
            ([MAPPING, MAPPING], admitted()),
        ]:
            with pytest.raises(AlpacaError):
                await fetch_iex_quotes(http, mappings, evidence, lambda: NOW)


async def test_stream_limit_and_retry_budget_stop_work() -> None:
    with respx.mock(assert_all_mocked=True) as router:
        route = router.get(LATEST_QUOTES_URL).respond(200, content=BODY)
        async with httpx.AsyncClient() as http:
            with pytest.raises(AlpacaError, match="response_limit"):
                await fetch_iex_quotes(http, [MAPPING], admitted(), lambda: NOW, max_bytes=50)
        assert route.call_count == 1
    with respx.mock(assert_all_mocked=True) as router:
        route = router.get(LATEST_QUOTES_URL).respond(429, headers={"Retry-After": "3600"})
        async with httpx.AsyncClient() as http:
            with pytest.raises(AlpacaError, match="budget"):
                await fetch_iex_quotes(http, [MAPPING], admitted(), lambda: NOW, sleep=Sleeper())
        assert route.call_count == 1


async def test_permission_expiring_during_await_never_returns_quotes() -> None:
    evidence = replace(admitted(), valid_until=NOW + timedelta(seconds=1))
    times = iter([NOW, NOW, NOW + timedelta(seconds=1)])
    with respx.mock(assert_all_mocked=True) as router:
        router.get(LATEST_QUOTES_URL).respond(200, content=BODY)
        async with httpx.AsyncClient() as http:
            with pytest.raises(AlpacaError, match="admission"):
                await fetch_iex_quotes(http, [MAPPING], evidence, lambda: next(times))
