"""Public protocol fixtures; external network is always mocked.

Reviewed 2026-11-11:
https://docs.alpaca.markets/us/reference/corporateactions-1
https://docs.alpaca.markets/us/reference/subscribetocorporateactionseventssse
https://raw.githubusercontent.com/alpacahq/cli/main/api/specs/market-data-api.json
Source SHA256: 2856fc7ed4dc6aa55a7b5db453a3cb8c5e9270b56e0679ded695bd926ec4e7dc
REST uses corporate_actions.{cash_dividends,forward_splits,...} numeric rates;
SSE data is an ARRAY of envelopes with string rates, action/at/event_id/region/ca.
since_id/until_id are inclusive ULIDs. Replay host is stream.data.alpaca.markets.
"""

import asyncio
import json
from dataclasses import FrozenInstanceError, replace
from datetime import date, timedelta
from decimal import Decimal

import httpx
import pytest
import respx

from app.services.alpaca_actions import (
    REST_URL,
    ActionBudget,
    fetch_action_snapshot,
    recheck_action_ids,
    replay_action_mutations,
    REPLAY_URL,
)
from app.services.stock_quote_rules import StockMapping
from tests.test_stock_admission import action_admitted
from tests.test_stock_quote_rules import NOW

EVENT_ID = "1dbc7685-9517-4a77-a236-8527d49cefdc"
BODY = (
    b'{"corporate_actions":{"cash_dividends":[{"id":"'
    + EVENT_ID.encode()
    + b'","symbol":"AAPL","cusip":"037833100","rate":0.24000001,'
    b'"process_date":"2026-11-10","ex_date":"2026-11-10",'
    b'"record_date":"2026-11-10","payable_date":"2026-11-15",'
    b'"foreign":false,"special":false,"currency":"USD"}]},"next_page_token":null}'
)
MAPPING = StockMapping(16, "AAPL", "asset-aapl", NOW, "NASDAQ")
EMPTY = b'{"corporate_actions":{},"next_page_token":null}'


class Clock:
    def __init__(self):
        self.value = 0.0
        self.sleeps = []

    def __call__(self):
        return self.value

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.value += seconds


async def rest(http, budget=None, **kwargs):
    return await fetch_action_snapshot(
        http,
        kwargs.pop("mappings", [MAPPING]),
        kwargs.pop("evidence", action_admitted),
        kwargs.pop("now", lambda: NOW),
        budget or ActionBudget(),
        start=kwargs.pop("start", NOW.date()),
        end=kwargs.pop("end", NOW.date()),
        **kwargs,
    )


async def test_rest_exact_decimal_current_schema_and_query() -> None:
    with respx.mock(assert_all_mocked=True, assert_all_called=False) as router:
        route = router.get(REST_URL).respond(200, content=BODY)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await fetch_action_snapshot(
                http,
                [MAPPING],
                lambda: action_admitted(),
                lambda: NOW,
                ActionBudget(),
                start=date(2026, 11, 10),
                end=date(2026, 11, 10),
            )
    assert batch.complete and batch.attempt_count == 1
    assert batch.records[0].rate == Decimal("0.24000001")
    assert batch.records[0].currency == "USD"
    # No inferred ordinary subtype, due-bill absence or verified economic dates.
    assert batch.records[0].subtype is None
    assert batch.records[0].due_bills is None
    assert not batch.records[0].dates_verified
    assert dict(route.calls.last.request.url.params) == {
        "symbols": "AAPL",
        "start": "2026-11-10",
        "end": "2026-11-10",
        "region": "us",
        "data_quality": "all",
        "limit": "1000",
        "sort": "asc",
    }
    with pytest.raises(FrozenInstanceError):
        batch.complete = False


@pytest.mark.parametrize(
    "body,reason",
    [
        (b"{}", "invalid_body"),
        (b"[]", "invalid_body"),
        (b'{"corporate_actions":{},"corporate_actions":{},"next_page_token":null}', "invalid_json"),
        (b"[" * 9 + b"]" * 9, "response_depth"),
        (BODY.replace(b"0.24000001", b"1e999999999"), "invalid_json"),
        (BODY.replace(b"0.24000001", b"NaN"), "invalid_json"),
        (BODY.replace(b"0.24000001", b"1" * 70), "invalid_json"),
        (BODY[:-1], "invalid_json"),
        (BODY.replace(b"cash_dividends", b"new_unknown_type"), "unknown_schema"),
        (BODY.replace(EVENT_ID.encode(), b"not-a-uuid"), "invalid_identity"),
        (BODY.replace(b"AAPL", b"UNKNOWN"), "unexpected_identity"),
        (BODY.replace(b"USD", b"USDX"), "invalid_currency"),
        (BODY.replace(b"2026-11-15", b"2026-02-31"), "invalid_date"),
        (BODY.replace(b"2026-11-15", b"not-a-date"), "invalid_date"),
        (BODY.replace(b"0.24000001", b"-1"), "invalid_rate"),
        (BODY.replace(b"false", b'"false"'), "invalid_record"),
        (BODY.replace(b'"symbol":"AAPL"', b'"symbol":" AAPL"'), "invalid_symbol"),
        (BODY.replace(b'"symbol":"AAPL"', b'"symbol":true'), "invalid_symbol"),
        (BODY.replace(b'"symbol":"AAPL",', b""), "invalid_symbol"),
        (BODY.replace(b'"rate":0.24000001,', b'"sub_type":"ordinary",'), "invalid_subtype"),
        (BODY.replace(b'"next_page_token":null', b'"next_page_token":""'), "invalid_cursor"),
        (BODY.replace(b'"next_page_token":null', b'"next_page_token":12'), "invalid_cursor"),
        (
            BODY.replace(b'"process_date":"2026-11-10"', b'"process_date":"2026-11-11"'),
            "outside_window",
        ),
    ],
)
async def test_rest_hostile_payload_is_fixed_failure(body, reason):
    with respx.mock() as router:
        router.get(REST_URL).respond(200, content=body)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http)
    assert not batch.complete and batch.records == () and batch.reason == reason


@pytest.mark.parametrize(
    "replacement,expected", [(b'""', None), (b'"EUR"', "EUR"), (b"null", None)]
)
async def test_rest_currency_is_not_inferred(replacement, expected):
    with respx.mock() as router:
        router.get(REST_URL).respond(200, content=BODY.replace(b'"USD"', replacement))
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http)
    assert batch.complete and batch.records[0].currency == expected
    assert not batch.records[0].cancelled


async def test_rest_incomplete_fields_are_not_economic_proof():
    body = json.loads(BODY)
    entry = body["corporate_actions"]["cash_dividends"][0]
    entry.pop("ex_date")
    entry["due_bill_on_date"] = "2026-11-10"
    with respx.mock() as router:
        router.get(REST_URL).respond(200, json=body)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http)
    assert batch.complete and batch.records[0].ex_date is None
    assert batch.records[0].due_bills is True and not batch.records[0].dates_verified


async def test_rest_known_ids_are_exclusive_missing_is_uncertain():
    with respx.mock() as router:
        route = router.get(REST_URL).respond(200, content=EMPTY)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await recheck_action_ids(
                http,
                [MAPPING],
                action_admitted,
                lambda: NOW,
                ActionBudget(),
                ids={EVENT_ID: "AAPL"},
            )
    assert dict(route.calls.last.request.url.params) == {"ids": EVENT_ID, "limit": "1000"}
    assert not batch.complete and not batch.records
    assert batch.coverage[-1].reason == "missing_or_uncertain"
    assert batch.coverage[-1].start == EVENT_ID


async def test_rest_pagination_inclusive_bounds_and_opaque_cursor():
    clock = Clock()
    with respx.mock() as router:
        route = router.get(REST_URL).mock(
            side_effect=[
                httpx.Response(200, content=BODY.replace(b"null", b'"https://evil.invalid/?x=1"')),
                httpx.Response(200, content=EMPTY),
            ]
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            budget = ActionBudget(monotonic=clock)
            batch = await rest(http, budget, sleep=clock.sleep)
    assert batch.complete and len(batch.records) == 1 and budget.pages == 2
    assert clock.sleeps == [3]
    assert route.calls[1].request.url.params["page_token"] == "https://evil.invalid/?x=1"
    assert route.calls[1].request.url.host == "data.alpaca.markets"


@pytest.mark.parametrize(
    "mode,reason",
    [
        ("loop", "cursor_loop"),
        ("duplicate", "duplicate_identity"),
        ("page", "page_budget"),
        ("attempt", "attempt_budget"),
        ("bytes", "byte_budget"),
    ],
)
async def test_rest_shared_page_attempt_byte_and_cursor_bounds(mode, reason):
    clock = Clock()
    first = BODY.replace(b"null", b'"cursor"')
    second = first if mode == "duplicate" else EMPTY.replace(b"null", b'"cursor"')
    budget = ActionBudget(monotonic=clock)
    if mode == "page":
        budget.max_pages = 1
    if mode == "attempt":
        budget.max_attempts = 1
    if mode == "bytes":
        budget.max_total_bytes = len(first)
    with respx.mock(assert_all_called=False) as router:
        route = router.get(REST_URL).mock(
            side_effect=[httpx.Response(200, content=first), httpx.Response(200, content=second)]
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http, budget, sleep=clock.sleep)
    assert not batch.complete and batch.reason == reason
    assert len(batch.records) == 1 and batch.continuation == "cursor"
    assert route.call_count == (1 if mode in ("page", "attempt") else 2)


@pytest.mark.parametrize("status", [301, 302, 401, 403, 404, 418])
async def test_rest_non200_no_redirect_or_secret_body(status):
    with respx.mock() as router:
        route = router.get(REST_URL).respond(
            status, text="secret-value", headers={"Location": "https://evil.invalid"}
        )
        async with httpx.AsyncClient(trust_env=False, follow_redirects=True) as http:
            batch = await rest(http)
    assert batch.reason == "http_status" and batch.attempt_count == route.call_count == 1
    assert "secret-value" not in repr(batch)


@pytest.mark.parametrize(
    "header,reason,calls",
    [
        ("2", "pages_exhausted", 2),
        ("6", "retry_after", 1),
        ("-1", "retry_after", 1),
        ("secret-value", "retry_after", 1),
    ],
)
async def test_rest_one_retry_counted_and_retry_after_bounded(header, reason, calls):
    clock = Clock()
    with respx.mock(assert_all_called=False) as router:
        route = router.get(REST_URL).mock(
            side_effect=[
                httpx.Response(429, headers={"Retry-After": header}),
                httpx.Response(200, content=EMPTY),
            ]
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http, ActionBudget(monotonic=clock), sleep=clock.sleep)
    assert batch.reason == reason and batch.attempt_count == route.call_count == calls


async def test_rest_shared_budget_exhaustion_prevents_new_known_id_call():
    clock = Clock()
    budget = ActionBudget(monotonic=clock, max_attempts=1)
    with respx.mock() as router:
        route = router.get(REST_URL).respond(200, content=EMPTY)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await rest(http, budget)).complete
            batch = await recheck_action_ids(
                http,
                [MAPPING],
                action_admitted,
                lambda: NOW,
                budget,
                ids={EVENT_ID: "AAPL"},
                sleep=clock.sleep,
            )
    assert not batch.complete and batch.reason == "attempt_budget" and route.call_count == 1


@pytest.mark.parametrize("change", ["generation", "rights", "scope", "lease", "time", "bytes"])
async def test_rest_rechecks_after_awaited_body(change):
    evidence = action_admitted()
    permitted = True
    current = NOW

    class Body(httpx.AsyncByteStream):
        async def __aiter__(self):
            nonlocal evidence, permitted, current
            if change == "generation":
                evidence = replace(evidence, generation=5)
            elif change == "rights":
                evidence = replace(evidence, retention_allowed=False)
            elif change == "scope":
                evidence = replace(evidence, scope={**evidence.scope, "account": "other"})
            elif change == "lease":
                permitted = False
            elif change == "time":
                current += timedelta(hours=9)
            yield BODY if change != "bytes" else BODY * 1000

    with respx.mock() as router:
        router.get(REST_URL).respond(200, stream=Body())
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(
                http, evidence=lambda: evidence, lease=lambda: permitted, now=lambda: current
            )
    assert not batch.complete and batch.records == ()
    assert batch.reason in ("admission", "lease", "response_limit")


async def test_rest_headers_and_body_share_attempt_timeout():
    class Body(httpx.AsyncByteStream):
        async def __aiter__(self):
            await asyncio.sleep(0.05)
            yield EMPTY

    with respx.mock() as router:
        router.get(REST_URL).respond(200, stream=Body())
        async with httpx.AsyncClient(trust_env=False) as http:
            budget = ActionBudget(attempt_seconds=0.01)
            batch = await rest(http, budget)
    assert batch.reason == "attempt_timeout" and not budget._busy


CURSOR = "01J9RPMV5TKB8WX3M4F1KZ7QH2"
LAST = "01J9RPMV5TKB8WX3M4F1KZ7QH3"


def frame(cursor=CURSOR, mutation="insert", symbol="AAPL"):
    entry = json.loads(BODY)["corporate_actions"]["cash_dividends"][0]
    entry["rate"] = "0.24000001"
    entry["symbol"] = symbol
    value = [
        {
            "event_id": cursor,
            "action": mutation,
            "at": "2026-11-10T14:00:00Z",
            "event_type": "cash_dividend_corporateaction_event",
            "region": "us",
            "ca": entry,
        }
    ]
    return b"data: " + json.dumps(value).encode() + b"\n\n"


async def test_replay_inclusive_terminal_witness_deduplicates_but_preserves_mutations():
    stream = frame() + frame() + frame(LAST, "delete")
    with respx.mock(assert_all_called=False) as router:
        route = router.get(REPLAY_URL).respond(
            200, content=stream, headers={"Content-Type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await replay_action_mutations(
                http,
                [MAPPING],
                action_admitted,
                lambda: NOW,
                ActionBudget(),
                since_id=CURSOR,
                until_id=LAST,
            )
    assert batch.complete and len(batch.observations) == 2
    assert [row.mutation for row in batch.observations] == ["insert", "delete"]
    assert batch.records[-1].cancelled and batch.continuation == LAST
    assert batch.records[0].rate == Decimal("0.24000001")
    assert dict(route.calls.last.request.url.params) == {
        "since_id": CURSOR,
        "until_id": LAST,
        "region": "us",
    }
