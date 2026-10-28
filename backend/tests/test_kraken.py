import json
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

from app.services.kraken import TICKER_URL, KrakenError, fetch_tickers, fetch_tickers_isolated
from app.services.price_rules import mid_from_ticker

FIXTURE = Path(__file__).parent / "fixtures" / "kraken_ticker_ok.json"
RESPONSE_KEYS = {
    "XXBTZUSD",
    "XETHZUSD",
    "SOLUSD",
    "XXRPZUSD",
    "BNBUSD",
    "ADAUSD",
    "XDGUSD",
    "TRXUSD",
    "AVAXUSD",
    "LINKUSD",
    "DOTUSD",
    "XLTCZUSD",
    "BCHUSD",
    "XXLMZUSD",
    "ATOMUSD",
}


def _ok_body() -> dict[str, Any]:
    body: dict[str, Any] = json.loads(FIXTURE.read_text())
    return body


class Sleeper:
    def __init__(self) -> None:
        self.delays: list[float] = []

    async def __call__(self, delay: float) -> None:
        self.delays.append(delay)


def _half() -> float:
    return 0.5


async def _fetch(sleeper: Sleeper, pairs: list[str] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient() as http:
        return await fetch_tickers(http, pairs or ["XXBTZUSD"], sleep=sleeper, jitter=_half)


def _router() -> respx.MockRouter:
    return respx.mock(assert_all_mocked=True, assert_all_called=False)


def test_fixture_has_the_15_response_keys_and_valid_mids() -> None:
    result = _ok_body()["result"]
    assert set(result) == RESPONSE_KEYS
    for entry in result.values():
        mid = mid_from_ticker(entry)
        assert mid is not None and mid > 0


async def test_success_returns_result_and_sends_pairs() -> None:
    pairs = sorted(RESPONSE_KEYS)
    with _router() as router:
        route = router.get(TICKER_URL).respond(200, json=_ok_body())
        result = await _fetch(Sleeper(), pairs)
    assert set(result) == RESPONSE_KEYS
    request = route.calls.last.request
    assert request.url.params["pair"] == ",".join(pairs)
    assert request.headers["user-agent"] == "birja-price-scheduler"


async def test_unknown_asset_pair_is_not_retried() -> None:
    sleeper = Sleeper()
    with _router() as router:
        route = router.get(TICKER_URL).respond(200, json={"error": ["EQuery:Unknown asset pair"]})
        with pytest.raises(KrakenError) as exc:
            await _fetch(sleeper)
    assert exc.value.retryable is False
    assert route.call_count == 1
    assert sleeper.delays == []


async def test_invalid_arguments_is_not_retried() -> None:
    with _router() as router:
        route = router.get(TICKER_URL).respond(200, json={"error": ["EGeneral:Invalid arguments"]})
        with pytest.raises(KrakenError) as exc:
            await _fetch(Sleeper())
    assert exc.value.retryable is False
    assert route.call_count == 1


async def test_rate_limit_error_then_success() -> None:
    sleeper = Sleeper()
    with _router() as router:
        route = router.get(TICKER_URL).mock(
            side_effect=[
                httpx.Response(200, json={"error": ["EAPI:Rate limit exceeded"]}),
                httpx.Response(200, json=_ok_body()),
            ]
        )
        result = await _fetch(sleeper)
    assert set(result) == RESPONSE_KEYS
    assert route.call_count == 2
    assert sleeper.delays == [1.5]


async def test_persistent_500_gives_up_after_three_calls() -> None:
    sleeper = Sleeper()
    with _router() as router:
        route = router.get(TICKER_URL).respond(500)
        with pytest.raises(KrakenError) as exc:
            await _fetch(sleeper)
    assert exc.value.retryable is True
    assert "500" in str(exc.value)
    assert route.call_count == 3
    assert sleeper.delays == [1.5, 2.5]


async def test_429_then_success() -> None:
    with _router() as router:
        route = router.get(TICKER_URL).mock(
            side_effect=[httpx.Response(429), httpx.Response(200, json=_ok_body())]
        )
        result = await _fetch(Sleeper())
    assert set(result) == RESPONSE_KEYS
    assert route.call_count == 2


async def test_timeout_then_success() -> None:
    with _router() as router:
        route = router.get(TICKER_URL).mock(
            side_effect=[httpx.ConnectTimeout("slow"), httpx.Response(200, json=_ok_body())]
        )
        result = await _fetch(Sleeper())
    assert set(result) == RESPONSE_KEYS
    assert route.call_count == 2


async def test_persistent_transport_error_reports_class_name() -> None:
    with _router() as router:
        router.get(TICKER_URL).mock(side_effect=httpx.ConnectError("boom"))
        with pytest.raises(KrakenError) as exc:
            await _fetch(Sleeper())
    assert "ConnectError" in str(exc.value)
    assert exc.value.retryable is True


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not json"),
        httpx.Response(200, json={"error": [], "result": []}),
        httpx.Response(200, json={"error": []}),
        httpx.Response(200, json=["list"]),
    ],
)
async def test_malformed_body_is_retried_then_fails(response: httpx.Response) -> None:
    with _router() as router:
        route = router.get(TICKER_URL).mock(return_value=response)
        with pytest.raises(KrakenError) as exc:
            await _fetch(Sleeper())
    assert exc.value.retryable is True
    assert route.call_count == 3


async def test_400_is_not_retried() -> None:
    with _router() as router:
        route = router.get(TICKER_URL).respond(400)
        with pytest.raises(KrakenError) as exc:
            await _fetch(Sleeper())
    assert exc.value.retryable is False
    assert route.call_count == 1


async def test_default_sleep_and_jitter_are_usable() -> None:
    with _router() as router:
        router.get(TICKER_URL).respond(200, json=_ok_body())
        async with httpx.AsyncClient() as http:
            result = await fetch_tickers(http, ["XXBTZUSD"])
    assert set(result) == RESPONSE_KEYS


UNKNOWN = {"error": ["EQuery:Unknown asset pair"]}


def _ticker_side_effect(bad: set[str], calls: list[str]) -> Any:
    """Kraken-like: the batch fails if any pair is unknown, single pairs answer alone."""
    full = _ok_body()["result"]

    def respond(request: httpx.Request) -> httpx.Response:
        pairs = request.url.params["pair"].split(",")
        calls.append(request.url.params["pair"])
        if bad & set(pairs):
            return httpx.Response(200, json=UNKNOWN)
        return httpx.Response(200, json={"error": [], "result": {p: full[p] for p in pairs}})

    return respond


async def _isolated(pairs: list[str]) -> dict[str, Any]:
    async with httpx.AsyncClient() as http:
        return await fetch_tickers_isolated(http, pairs, sleep=Sleeper(), jitter=_half)


async def test_isolated_one_unknown_pair_keeps_the_others(
    caplog: pytest.LogCaptureFixture,
) -> None:
    pairs = sorted(RESPONSE_KEYS)
    calls: list[str] = []
    with _router() as router:
        router.get(TICKER_URL).mock(side_effect=_ticker_side_effect({"DOTUSD"}, calls))
        with caplog.at_level("WARNING", logger="app.services.kraken"):
            result = await _isolated(pairs)
    assert set(result) == RESPONSE_KEYS - {"DOTUSD"}
    assert len(calls) == 1 + len(pairs)  # one batch, then exactly one call per pair
    assert "price pair unavailable: pair=DOTUSD" in caplog.text
    assert "pair=BCHUSD" not in caplog.text


async def test_isolated_all_pairs_unknown_raises() -> None:
    calls: list[str] = []
    with _router() as router:
        router.get(TICKER_URL).mock(side_effect=_ticker_side_effect({"A", "B"}, calls))
        with pytest.raises(KrakenError, match="all pairs unavailable"):
            await _isolated(["A", "B"])
    assert calls == ["A,B", "A", "B"]


async def test_isolated_single_pair_unknown_is_not_refetched() -> None:
    calls: list[str] = []
    with _router() as router:
        router.get(TICKER_URL).mock(side_effect=_ticker_side_effect({"A"}, calls))
        with pytest.raises(KrakenError, match="Unknown asset pair"):
            await _isolated(["A"])
    assert calls == ["A"]


async def test_isolated_other_errors_do_not_fan_out() -> None:
    with _router() as router:
        route = router.get(TICKER_URL).respond(400)
        with pytest.raises(KrakenError, match="http 400"):
            await _isolated(["XXBTZUSD", "XETHZUSD"])
    assert route.call_count == 1


async def test_isolated_success_is_one_call() -> None:
    with _router() as router:
        route = router.get(TICKER_URL).respond(200, json=_ok_body())
        result = await _isolated(["XXBTZUSD", "XETHZUSD"])
    assert set(result) == RESPONSE_KEYS
    assert route.call_count == 1
