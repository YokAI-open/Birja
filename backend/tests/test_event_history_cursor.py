"""Strict full-tuple cursor and exact event wire contracts."""

import base64
import json
from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas.event_history import EventHistoryItem, EventHistoryPage
from app.services import history
from app.services.event_history import (
    EventHistoryCursor,
    InvalidCursor,
    decode_cursor,
    encode_cursor,
)


def test_mixed_cursor_roundtrip_preserves_all_order_columns():
    value = EventHistoryCursor(
        datetime(2026, 11, 12, 15, 1, 2, 123456, UTC), 4, 9223372036854775807
    )
    assert decode_cursor(encode_cursor(value)) == value


STAMP = "2026-11-12T15:01:02.123456Z"
VALID = {"v": 2, "recorded_at": STAMP, "kind_rank": 4, "source_id": "9223372036854775807"}


def token(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        "",
        "x" * 513,
        "!",
        "e30=",
        "e31",
        "a",
        token(b"\xff"),
        token(b"{"),
        token([]),
        token(None),
        token({}),
        token(b'"text"'),
        token(json.dumps(VALID).encode()),
        token({**VALID, "other": 1}),
        token(
            b'{"v":2,"v":2,"recorded_at":"2026-11-12T15:01:02.123456Z","kind_rank":4,"source_id":"1"}'
        ),
        *[token({**VALID, "v": v}) for v in (True, 1, "2", 2.0, None)],
        *[
            token({**VALID, "recorded_at": v})
            for v in (
                None,
                1,
                "bad",
                "2026-02-30T15:01:02.123456Z",
                STAMP[:-1],
                "2026-11-12T15:01:02Z",
                "2026-11-12T15:01:02.123456+00:00",
            )
        ],
        *[token({**VALID, "kind_rank": v}) for v in (None, True, "4", 4.0, 0, 5)],
        *[
            token({**VALID, "source_id": v})
            for v in (None, True, 1, "0", "-1", "01", "+1", "1e2", "1.0", "9223372036854775808")
        ],
        history.encode_cursor(history.HistoryCursor(datetime(2026, 11, 12, tzinfo=UTC), 1)),
    ],
)
def test_mixed_cursor_rejects_malformed_or_legacy(value):
    with pytest.raises(InvalidCursor):
        decode_cursor(value)


@pytest.mark.parametrize("rank", [1, 2, 3, 4])
def test_cursor_all_ranks_timezone_and_legacy_unchanged(rank):
    dt = datetime(2026, 11, 12, 18, 1, 2, 123456, timezone(timedelta(hours=3)))
    value = EventHistoryCursor(dt, rank, 1)
    assert decode_cursor(encode_cursor(value)) == value
    legacy = history.HistoryCursor(dt, 1)
    assert history.decode_cursor(history.encode_cursor(legacy)) == legacy
    with pytest.raises(history.InvalidCursor):
        history.decode_cursor(encode_cursor(value))


@pytest.mark.parametrize(
    "stamp,rank,identifier",
    [
        (datetime(2026, 11, 12), 4, 1),
        (datetime(2026, 11, 12, tzinfo=UTC), 4, True),
        (datetime(2026, 11, 12, tzinfo=UTC), 0, 1),
        (datetime(2026, 11, 12, tzinfo=UTC), 4, 0),
    ],
)
def test_mixed_encoder_rejects_invalid_tuple(stamp, rank, identifier):
    with pytest.raises(InvalidCursor):
        encode_cursor(EventHistoryCursor(stamp, rank, identifier))


TERMS = dict(
    eligible_quantity="2",
    rate=".5",
    cutoff=STAMP,
    ex_date="2026-11-01",
    record_date=None,
    payable_date="2026-11-12",
)
TERMS["rate"] = "0.5"
BASE = dict(
    recorded_at=STAMP, symbol="AAPL", name="Saved Apple", cash_delta="0.00", asset_type="stock"
)
DIVIDEND = dict(
    BASE,
    kind="dividend",
    id="dividend:1",
    payment_reference="dividend:1",
    credited_amount="1.00",
    credited_at=STAMP,
    **TERMS,
)
DIVIDEND["cash_delta"] = "1.00"
TRADE = dict(
    BASE,
    kind="trade",
    id="trade:1",
    side="buy",
    quantity="2",
    exec_price="10.1",
    fee="0",
    filled_at=STAMP,
    source="alpaca",
    feed="iex",
    quote_at=STAMP,
)
TRADE["cash_delta"] = "-20.20"
SPLIT = dict(
    BASE,
    kind="split",
    id="split:1",
    ratio_new="3",
    ratio_old="2",
    quantity_before="2",
    quantity_after="3",
    cost_basis_before="20.20",
    cost_basis_after="20.20",
    effective_at=STAMP,
)
CORRECTION = dict(
    BASE,
    kind="dividend_correction",
    id="dividend_correction:1",
    payment_reference="dividend:1",
    decision_reference="dividend_correction:1",
    outcome="applied",
    reason="target_applied",
    desired_total="1.50",
    cumulative_applied_before="1.00",
    proposed_delta="0.50",
    applied_delta="0.50",
    terms=dict(TERMS, rate="0.75"),
    original=DIVIDEND,
)
CORRECTION["cash_delta"] = "0.50"
ADAPTER = TypeAdapter(EventHistoryItem)


@pytest.mark.parametrize(
    "item",
    [
        TRADE,
        DIVIDEND,
        SPLIT,
        CORRECTION,
        dict(TRADE, asset_type="crypto", source=None, feed=None, quote_at=None, quantity="0.01"),
        dict(TRADE, side="sell", cash_delta="0"),
        dict(
            CORRECTION,
            outcome="held_uncertain",
            reason="terms_unverified",
            desired_total=None,
            proposed_delta=None,
            terms=None,
            applied_delta="0",
            cash_delta="0",
        ),
        dict(
            CORRECTION,
            outcome="held_unaffordable",
            reason="insufficient_cash",
            desired_total="0.50",
            proposed_delta="-0.50",
            applied_delta="0",
            cash_delta="0",
            terms=dict(TERMS, rate="0.25"),
        ),
        dict(
            CORRECTION,
            outcome="verified_no_change",
            reason="target_unchanged",
            desired_total="1.00",
            proposed_delta="0",
            applied_delta="0",
            cash_delta="0",
            terms=TERMS,
        ),
    ],
)
def test_exact_event_schema_accepts_every_kind_outcome(item):
    assert ADAPTER.validate_python(item).model_dump(mode="json") == item
    page = EventHistoryPage(items=[ADAPTER.validate_python(item)], next_cursor=None)
    assert page.model_dump(mode="json")["items"] == [item]


@pytest.mark.parametrize(
    "item,changes",
    [
        *[
            (DIVIDEND, {"rate": v})
            for v in (
                1,
                "NaN",
                "Infinity",
                "1e2",
                "+1",
                "01",
                "-0",
                "0.123456789",
                "1000000000000",
                "-1",
            )
        ],
        (DIVIDEND, {"rate": "0.001"}),
        (DIVIDEND, {"eligible_quantity": "1.5"}),
        (DIVIDEND, {"cash_delta": "0.001"}),
        (DIVIDEND, {"name": " "}),
        (DIVIDEND, {"name": "evil\nname"}),
        (DIVIDEND, {"id": "dividend:01"}),
        (DIVIDEND, {"id": "dividend:9223372036854775808"}),
        (DIVIDEND, {"ex_date": "2026-02-30"}),
        (DIVIDEND, {"ex_date": "20261101"}),
        (DIVIDEND, {"recorded_at": STAMP[:-1]}),
        (DIVIDEND, {"recorded_at": "2026-02-30T00:00:00.000000Z"}),
        (DIVIDEND, {"payment_reference": "dividend:2"}),
        (DIVIDEND, {"cash_delta": "2"}),
        (DIVIDEND, {"credited_at": "2026-11-13T00:00:00.000000Z"}),
        (DIVIDEND, {"extra": True}),
        (TRADE, {"quantity": "0"}),
        (TRADE, {"exec_price": "0"}),
        (TRADE, {"filled_at": "2026-11-13T00:00:00.000000Z"}),
        (TRADE, {"cash_delta": "0"}),
        (TRADE, {"side": "sell", "cash_delta": "-1"}),
        (TRADE, {"quantity": "1.5"}),
        (TRADE, {"source": None}),
        (TRADE, {"feed": None}),
        (TRADE, {"quote_at": None}),
        (TRADE, {"quote_at": "2026-11-13T00:00:00.000000Z"}),
        (TRADE, {"fee": "1"}),
        (TRADE, {"asset_type": "crypto"}),
        (TRADE, {"asset_type": "crypto", "source": None}),
        (TRADE, {"asset_type": "crypto", "source": None, "feed": None}),
        (SPLIT, {"ratio_old": "0"}),
        (SPLIT, {"ratio_new": "2"}),
        (SPLIT, {"quantity_before": "0"}),
        (SPLIT, {"quantity_after": "4"}),
        (SPLIT, {"cash_delta": "1"}),
        (SPLIT, {"cost_basis_after": "1"}),
        (SPLIT, {"effective_at": "2026-11-13T00:00:00.000000Z"}),
        (CORRECTION, {"payment_reference": "dividend:2"}),
        (CORRECTION, {"decision_reference": "dividend_correction:2"}),
        (CORRECTION, {"recorded_at": "2026-11-11T00:00:00.000000Z"}),
        (CORRECTION, {"reason": "target_unchanged"}),
        (CORRECTION, {"cash_delta": "1"}),
        (CORRECTION, {"outcome": "held_uncertain", "reason": "terms_unverified"}),
        (CORRECTION, {"desired_total": None}),
        (CORRECTION, {"proposed_delta": None}),
        (CORRECTION, {"terms": None}),
        (CORRECTION, {"desired_total": "2"}),
        (CORRECTION, {"proposed_delta": "0"}),
        (CORRECTION, {"applied_delta": "0", "cash_delta": "0"}),
        (CORRECTION, {"applied_delta": "1", "cash_delta": "1"}),
        (CORRECTION, {"outcome": "held_unaffordable", "reason": "insufficient_cash"}),
        (
            CORRECTION,
            {
                "outcome": "held_unaffordable",
                "reason": "insufficient_cash",
                "applied_delta": "0",
                "cash_delta": "0",
            },
        ),
        (
            CORRECTION,
            {
                "outcome": "verified_no_change",
                "reason": "target_unchanged",
                "applied_delta": "0",
                "cash_delta": "0",
            },
        ),
    ],
)
def test_exact_event_schema_rejects_malformed_values(item, changes):
    with pytest.raises(ValidationError):
        ADAPTER.validate_python({**item, **changes})
