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
    REPLAY_URL,
    REST_URL,
    ActionBudget,
    fetch_action_snapshot,
    recheck_action_ids,
    replay_action_mutations,
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


async def test_rest_continuation_resumes_the_validated_next_page():
    with respx.mock() as router:
        route = router.get(REST_URL).respond(200, content=EMPTY)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await fetch_action_snapshot(
                http,
                [MAPPING],
                action_admitted,
                lambda: NOW,
                ActionBudget(),
                start=NOW.date(),
                end=NOW.date(),
                page_token="next-reviewed-page",
            )
    assert route.calls.last.request.url.params.get("page_token") == "next-reviewed-page"
    assert batch.complete


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


async def replay(http, budget=None, **kwargs):
    return await replay_action_mutations(
        http,
        [MAPPING],
        kwargs.pop("evidence", action_admitted),
        lambda: NOW,
        budget or ActionBudget(),
        since_id=kwargs.pop("since_id", CURSOR),
        until_id=kwargs.pop("until_id", LAST),
        **kwargs,
    )


@pytest.mark.parametrize(
    "body,reason",
    [
        (frame(), "source_gap"),
        (frame()[:-1], "truncated_frame"),
        (frame() + b"data: {", "truncated_frame"),
        (frame().replace(b"data:", b"unknown:"), "invalid_framing"),
        (b"data: []\n\n", "invalid_frame"),
        (b"data: {}\n\n", "invalid_frame"),
        (frame().replace(b'"us"', b'"non_us"'), "invalid_envelope"),
        (frame().replace(b'"insert"', b'"cancel"'), "invalid_envelope"),
        (
            frame().replace(
                b"cash_dividend_corporateaction_event", b"unknown_corporateaction_event"
            ),
            "unknown_schema",
        ),
        (
            frame().replace(b'"at": "2026-11-10T14:00:00Z"', b'"at": "2026-11-10T16:00:00Z"'),
            "invalid_envelope",
        ),
        (frame().replace(b'"at": "2026-11-10T14:00:00Z"', b'"at": "invalid"'), "invalid_timestamp"),
        (
            frame().replace(b'"at": "2026-11-10T14:00:00Z"', b'"at": "2026-02-31T14:00:00Z"'),
            "invalid_timestamp",
        ),
        (frame().replace(CURSOR.encode(), b"not-an-id"), "invalid_cursor"),
        (frame().replace(b'"ca":', b'"extra": true, "ca":'), "invalid_envelope"),
        (frame().replace(b'"rate": "0.24000001"', b'"rate": "1e99999999999999"'), "invalid_rate"),
        (frame().replace(b'"rate": "0.24000001"', b'"rate": 0.24'), "invalid_rate"),
        (frame() + frame(CURSOR, "update"), "cursor_conflict"),
        (frame(LAST) + frame(CURSOR), "cursor_order"),
        (frame("01J9RPMV5TKB8WX3M4F1KZ7QH4"), "outside_window"),
    ],
)
async def test_replay_adversarial_protocol_is_incomplete(body, reason):
    with respx.mock() as router:
        router.get(REPLAY_URL).respond(
            200, content=body, headers={"Content-Type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await replay(http)
    assert not batch.complete and batch.reason == reason


async def test_replay_unrelated_terminal_witness_discarded_and_update_retained():
    body = b": heartbeat\n\n" + frame(CURSOR, "update") + frame(LAST, symbol="ZZZZ")
    with respx.mock() as router:
        route = router.get(REPLAY_URL).respond(
            200,
            content=body.replace(b"\n", b"\r\n"),
            headers={"Content-Type": "text/event-stream; charset=utf-8"},
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await replay(http)
    assert batch.complete and batch.continuation == LAST and len(batch.records) == 1
    assert batch.observations[0].mutation == "update"
    assert "ZZZZ" not in repr(batch)
    assert route.calls.last.request.headers["accept"] == "text/event-stream"


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"since_id": "bad"}, "invalid_cursor"),
        ({"until_id": None}, "invalid_cursor"),
        ({"since_id": LAST, "until_id": CURSOR}, "invalid_window"),
        ({"until_id": "7ZZZZZZZZZZZZZZZZZZZZZZZZZ"}, "invalid_window"),
        ({"since": NOW}, "invalid_window"),
    ],
)
async def test_replay_invalid_windows_make_no_attempts(kwargs, reason):
    async with httpx.AsyncClient(trust_env=False) as http:
        batch = await replay(http, **kwargs)
    assert batch.reason == reason and batch.attempt_count == 0


async def test_replay_timestamp_until_normal_close_and_inclusive_empty_window():
    for body in (frame(), b""):
        with respx.mock() as router:
            route = router.get(REPLAY_URL).respond(
                200, content=body, headers={"Content-Type": "text/event-stream"}
            )
            async with httpx.AsyncClient(trust_env=False) as http:
                batch = await replay_action_mutations(
                    http,
                    [MAPPING],
                    action_admitted,
                    lambda: NOW,
                    ActionBudget(),
                    since=NOW - timedelta(hours=2),
                    until=NOW - timedelta(minutes=30),
                )
        assert batch.complete and batch.reason == "historical_until_close"
        assert set(route.calls.last.request.url.params) == {"since", "until", "region"}


@pytest.mark.parametrize(
    "mode,reason",
    [
        ("frame", "frame_limit"),
        ("mutation", "mutation_budget"),
        ("response", "response_limit"),
        ("total", "byte_budget"),
    ],
)
async def test_replay_all_stream_bounds_count_discarded_data(mode, reason):
    budget = ActionBudget()
    body = frame() + frame(LAST, symbol="ZZZZ")
    if mode == "frame":
        budget.max_frame_bytes = 30
    elif mode == "mutation":
        budget.max_mutations = 1
    elif mode == "response":
        budget.max_response_bytes = 100
    else:
        budget.max_total_bytes = 100
    with respx.mock() as router:
        router.get(REPLAY_URL).respond(
            200, content=body, headers={"Content-Type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await replay(http, budget)
    assert not batch.complete and batch.reason == reason and batch.attempt_count == 1


@pytest.mark.parametrize(
    "status,content_type,reason",
    [
        (403, "text/event-stream", "replay_unavailable"),
        (302, "text/event-stream", "replay_unavailable"),
        (200, "application/json", "content_type"),
    ],
)
async def test_replay_unavailable_or_wrong_type_never_renews_coverage(status, content_type, reason):
    with respx.mock() as router:
        router.get(REPLAY_URL).respond(
            status, content=frame(LAST), headers={"Content-Type": content_type}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await replay(http)
    assert batch.reason == reason and not batch.complete and not batch.records


async def test_replay_requires_distinct_all_us_ingress_permission():
    evidence = action_admitted()
    evidence = replace(
        evidence, scope={**evidence.scope, "capabilities": ["rest"], "all_us_replay_ingress": False}
    )
    async with httpx.AsyncClient(trust_env=False) as http:
        batch = await replay(http, evidence=lambda: evidence)
    assert batch.reason == "admission" and not batch.records and batch.attempt_count == 0


@pytest.mark.parametrize("mode", ["revoke", "disconnect", "timeout", "cancel"])
async def test_replay_awaited_stream_revocation_disconnect_timeout_and_cancellation(mode):
    evidence = action_admitted()

    class Body(httpx.AsyncByteStream):
        async def __aiter__(self):
            nonlocal evidence
            yield frame()
            if mode == "revoke":
                evidence = replace(evidence, collection_allowed=False)
            elif mode == "disconnect":
                raise httpx.ReadError("private-value")
            elif mode == "timeout":
                await asyncio.sleep(0.05)
            else:
                raise asyncio.CancelledError
            yield frame(LAST)

    with respx.mock() as router:
        router.get(REPLAY_URL).respond(
            200, stream=Body(), headers={"Content-Type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            budget = ActionBudget(attempt_seconds=0.01)
            if mode == "cancel":
                with pytest.raises(asyncio.CancelledError):
                    await replay(http, budget, evidence=lambda: evidence)
                assert not budget._busy
                return
            batch = await replay(http, budget, evidence=lambda: evidence)
    assert not batch.complete and not budget._busy and "private-value" not in repr(batch)
    assert (
        batch.reason
        == {"revoke": "admission", "disconnect": "source_gap", "timeout": "replay_timeout"}[mode]
    )
    if mode == "revoke":
        assert not batch.records and batch.continuation is None


@pytest.mark.parametrize(
    "budget_changes",
    [
        {"max_attempts": 9},
        {"max_pages": False},
        {"attempt_seconds": 6},
        {"total_seconds": float("nan")},
        {"max_frame_bytes": 0},
    ],
)
async def test_rest_invalid_budget_never_contacts_provider(budget_changes):
    async with httpx.AsyncClient(trust_env=False) as http:
        batch = await rest(http, ActionBudget(**budget_changes))
    assert batch.reason == "invalid_budget" and batch.attempt_count == 0


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"start": NOW}, "invalid_window"),
        ({"end": NOW.date() - timedelta(days=1)}, "invalid_window"),
        ({"mappings": []}, "invalid_request"),
        ({"mappings": [MAPPING, MAPPING]}, "invalid_request"),
        ({"mappings": [replace(MAPPING, provider_asset_id=None)]}, "invalid_request"),
        ({"evidence": lambda: None}, "admission"),
    ],
)
async def test_rest_invalid_scope_and_windows_are_zero_attempts(kwargs, reason):
    async with httpx.AsyncClient(trust_env=False) as http:
        batch = await rest(http, **kwargs)
    assert batch.reason == reason and batch.attempt_count == 0


@pytest.mark.parametrize("ids", [{}, {"bad": "AAPL"}, {EVENT_ID: "NVDA"}])
async def test_rest_invalid_known_ids_make_no_attempt(ids):
    async with httpx.AsyncClient(trust_env=False) as http:
        batch = await recheck_action_ids(
            http, [MAPPING], action_admitted, lambda: NOW, ActionBudget(), ids=ids
        )
    assert not batch.complete and batch.attempt_count == 0
    assert batch.reason in ("invalid_ids", "invalid_identity")


@pytest.mark.parametrize(
    "body,reason",
    [
        (BODY.replace(EVENT_ID.encode(), EVENT_ID.upper().encode()), "invalid_identity"),
        (BODY.replace(b'[{"id"', b'[null,{"id"'), "invalid_record"),
        (b'{"corporate_actions":{"cash_dividends":{}},"next_page_token":null}', "invalid_body"),
        (
            b'{"corporate_actions":{"cash_dividends":['
            + b"null," * 1000
            + b'null]},"next_page_token":null}',
            "record_limit",
        ),
        (BODY.replace(b"037833100", b'has\\"quote\\\\backslash[]'), "pages_exhausted"),
    ],
)
async def test_rest_additional_parser_limits_and_escaped_string_brackets(body, reason):
    with respx.mock() as router:
        router.get(REST_URL).respond(200, content=body)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http)
    assert batch.reason == reason
    assert batch.complete == (reason == "pages_exhausted")


@pytest.mark.parametrize(
    "kind,reason", [("status", "http_retry_exhausted"), ("transport", "transport")]
)
async def test_rest_retry_is_at_most_one_for_status_and_transport(kind, reason):
    clock = Clock()
    with respx.mock() as router:
        responses = (
            [httpx.Response(503), httpx.Response(503)]
            if kind == "status"
            else [httpx.ConnectError("private-value"), httpx.ReadError("private-value")]
        )
        route = router.get(REST_URL).mock(side_effect=responses)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http, ActionBudget(monotonic=clock), sleep=clock.sleep)
    assert batch.reason == reason and batch.attempt_count == route.call_count == 2
    assert "private-value" not in repr(batch)


async def test_rest_cadence_exhaustion_and_elapsed_clock_are_not_late_requests():
    clock = Clock()
    budget = ActionBudget(monotonic=clock, total_seconds=2)
    with respx.mock() as router:
        route = router.get(REST_URL).respond(200, content=EMPTY.replace(b"null", b'"next"'))
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http, budget, sleep=clock.sleep)
            clock.value = 3
            expired = await rest(http, budget, sleep=clock.sleep)
    assert batch.reason == expired.reason == "cycle_budget" and route.call_count == 1


async def test_rest_zero_cadence_wait_and_async_authority_and_lease_reload():
    clock = Clock()
    count = 0

    async def evidence():
        nonlocal count
        count += 1
        return action_admitted()

    async def lease():
        return True

    async def response(request):
        clock.value += 5
        return httpx.Response(
            200, content=EMPTY.replace(b"null", b'"next"') if clock.value == 5 else EMPTY
        )

    with respx.mock() as router:
        router.get(REST_URL).mock(side_effect=response)
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(
                http,
                ActionBudget(monotonic=clock),
                sleep=clock.sleep,
                evidence=evidence,
                lease=lease,
            )
    assert batch.complete and count > 4 and clock.sleeps == []


async def test_rest_second_lease_recheck_and_evidence_change_clear_partial_data():
    evidence = action_admitted()
    lease_calls = 0

    async def lease():
        nonlocal lease_calls
        lease_calls += 1
        return lease_calls != 2

    async with httpx.AsyncClient(trust_env=False) as http:
        batch = await rest(http, lease=lease)
    assert batch.reason == "lease" and batch.attempt_count == 0

    class Body(httpx.AsyncByteStream):
        async def __aiter__(self):
            nonlocal evidence
            evidence = replace(evidence, attribution="Changed valid attribution")
            yield BODY

    with respx.mock() as router:
        router.get(REST_URL).respond(200, stream=Body())
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http, evidence=lambda: evidence)
    assert batch.reason == "admission_changed" and not batch.records


async def test_rest_cycle_timeout_in_authority_and_concurrent_budget_rejected():
    async def evidence():
        await asyncio.sleep(0.05)
        return action_admitted()

    budget = ActionBudget(total_seconds=0.01)
    async with httpx.AsyncClient(trust_env=False) as http:
        batch = await rest(http, budget, evidence=evidence)
        assert batch.reason == "cycle_budget" and not budget._busy
        budget._busy = True
        concurrent = await rest(http, budget)
    assert concurrent.reason == "concurrent_budget" and budget._busy


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"since": NOW, "until": NOW + timedelta(seconds=1)},
        {"since": NOW, "until": NOW - timedelta(seconds=1)},
    ],
)
async def test_replay_timestamp_invalid_or_future_terminal_is_no_request(kwargs):
    async with httpx.AsyncClient(trust_env=False) as http:
        batch = await replay_action_mutations(
            http, [MAPPING], action_admitted, lambda: NOW, ActionBudget(), **kwargs
        )
    assert batch.reason == "invalid_window" and batch.attempt_count == 0


async def test_replay_partial_call_actual_type_and_sse_metadata_and_outside_timestamp():
    body = frame(LAST).replace(
        b"cash_dividend_corporateaction_event", b"equity_partial_call_corporateaction_event"
    )
    body = b"id: " + LAST.encode() + b"\nevent: message\n" + body
    with respx.mock() as router:
        router.get(REPLAY_URL).respond(
            200, content=body, headers={"Content-Type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await replay(http)
            outside = await replay_action_mutations(
                http,
                [MAPPING],
                action_admitted,
                lambda: NOW,
                ActionBudget(),
                since=NOW - timedelta(minutes=20),
                until=NOW - timedelta(minutes=10),
            )
    assert batch.complete and batch.records[0].event_type == "partial_call"
    assert batch.records[0].identity_changed
    assert outside.reason == "outside_window" and not outside.complete


@pytest.mark.parametrize("url", [REST_URL, REPLAY_URL])
async def test_reject_content_encoding_before_decoder_allocation(url):
    # Server disregarding Accept-Encoding identity must not activate an
    # unbounded HTTPX decompressor before our byte/frame checks.
    class Encoded(httpx.AsyncByteStream):
        async def __aiter__(self):
            raise AssertionError("Compressed body must not be read")
            yield b""

    with respx.mock() as router:
        router.get(url).respond(200, stream=Encoded(), headers={"Content-Encoding": "gzip"})
        async with httpx.AsyncClient(trust_env=False) as http:
            batch = await rest(http) if url == REST_URL else await replay(http)
    assert not batch.complete and batch.reason == "content_encoding"
