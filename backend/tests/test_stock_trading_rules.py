"""Independent evidence must default deny, even when a quote is recent."""

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.services.stock_trading_rules import (
    PRODUCTS,
    AdmissionEvidence,
    ExecutionEvidence,
    QuoteEvidence,
    StatusEvidence,
    ValuationEvidence,
    evaluate_execution,
    evaluate_valuation,
    lose_status_continuity,
    renew_status_continuity,
    status_current,
)

NOW = datetime(2026, 11, 11, 15, tzinfo=UTC)


def valid() -> ExecutionEvidence:
    return ExecutionEvidence(
        coin_id=16,
        provider_asset_id="fixture-aapl",
        admissions=tuple(
            AdmissionEvidence(
                p, 1, "a" * 64, NOW - timedelta(days=1), NOW + timedelta(days=1), True
            )
            for p in sorted(PRODUCTS)
        ),
        action_current=True,
        action_valid_until=NOW + timedelta(minutes=5),
        status=StatusEvidence(
            16,
            "fixture-aapl",
            "normal",
            NOW - timedelta(hours=1),
            NOW,
            NOW.date(),
            1,
            1,
            100,
            NOW + timedelta(seconds=60),
            True,
            True,
            "alpaca",
            "fixture-stream",
        ),
        session_state="open",
        session_date=NOW.date(),
        opens_at=NOW.replace(hour=14, minute=30),
        closes_at=NOW.replace(hour=21),
        session_valid_until=NOW + timedelta(hours=1),
        calendar_generation=1,
        quote=QuoteEvidence(
            16,
            "fixture-aapl",
            Decimal("100.00000000"),
            Decimal("100.00000001"),
            NOW - timedelta(seconds=1),
            NOW,
            NOW.date(),
            1,
            0,
        ),
    )


def test_empty_evidence_defaults_deny() -> None:
    decision = evaluate_execution(ExecutionEvidence(), datetime(2026, 11, 11, 15, tzinfo=UTC))
    assert not decision.allowed
    assert decision.reason == "permission_unavailable"


def test_complete_authority_binds_exact_immutable_snapshot_and_conservative_deadline() -> None:
    evidence = valid()
    decision = evaluate_execution(evidence, NOW)
    assert decision.allowed and decision.reason == "available"
    assert decision.evidence == evidence
    assert decision.valid_until == NOW + timedelta(seconds=60)
    with pytest.raises(FrozenInstanceError):
        evidence.coin_id = 17  # type: ignore[misc]


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"admissions": ()}, "permission_unavailable"),
        ({"action_current": False}, "action_unavailable"),
        ({"action_valid_until": NOW}, "action_unavailable"),
        ({"next_blocking_at": NOW}, "action_unavailable"),
        ({"unit_epoch": 1}, "units_changed"),
        ({"status": StatusEvidence()}, "status_unavailable"),
        ({"session_state": "unknown"}, "session_unavailable"),
        ({"session_valid_until": NOW}, "session_unavailable"),
        ({"calendar_generation": 2}, "session_unavailable"),
        ({"session_state": "closed"}, "market_closed"),
        ({"closes_at": NOW}, "market_closed"),
        ({"opens_at": NOW + timedelta(seconds=1)}, "market_closed"),
        ({"quote": QuoteEvidence()}, "quote_unavailable"),
    ],
)
def test_priority_and_strict_expiry(change: dict, reason: str) -> None:
    decision = evaluate_execution(replace(valid(), **change), NOW)
    assert not decision.allowed
    assert decision.reason == reason
    assert decision.evidence is None and decision.valid_until is None


@pytest.mark.parametrize("seconds,allowed", [(119, True), (120, False), (121, False)])
def test_quote_source_age_not_collection_time(seconds: int, allowed: bool) -> None:
    evidence = valid()
    evidence = replace(
        evidence, quote=replace(evidence.quote, event_at=NOW - timedelta(seconds=seconds))
    )
    decision = evaluate_execution(evidence, NOW)
    assert decision.allowed is allowed
    if not allowed:
        assert decision.reason == "quote_stale"


@pytest.mark.parametrize(
    "state,reason", [("halted", "halted"), ("frozen", "frozen"), ("unknown", "status_unavailable")]
)
def test_independent_status_cannot_be_replaced_by_recent_quote(state: str, reason: str) -> None:
    evidence = valid()
    decision = evaluate_execution(
        replace(evidence, status=replace(evidence.status, state=state)), NOW
    )
    assert not decision.allowed and decision.reason == reason


@pytest.mark.parametrize(
    "change",
    [
        {"bootstrap_verified": False},
        {"continuity_current": False},
        {"valid_until": NOW},
        {"valid_until": NOW + timedelta(seconds=61)},
        {"sequence": True},
        {"observed_at": NOW + timedelta(seconds=1)},
        {"event_at": NOW + timedelta(seconds=1)},
        {"source_ref": ""},
        {"continuity_generation": 0},
        {"admission_generation": 2},
        {"provider_asset_id": "other"},
        {"coin_id": 99},
    ],
)
def test_status_identity_bootstrap_continuity_and_lease(change: dict) -> None:
    evidence = valid()
    decision = evaluate_execution(replace(evidence, status=replace(evidence.status, **change)), NOW)
    assert decision.reason == "status_unavailable" and not decision.allowed


def test_event_age_is_not_quote_age_and_only_trusted_continuity_renews() -> None:
    status = valid().status
    assert status_current(status, NOW)  # event is one hour old; lease is current
    later = NOW + timedelta(seconds=30)
    trusted = renew_status_continuity(status, later, trusted_contiguous=True, sequence=101)
    assert trusted.valid_until == later + timedelta(seconds=60)
    assert trusted.event_at == status.event_at
    assert trusted.sequence == 101
    for rejected in (
        renew_status_continuity(status, later, sequence=101),
        renew_status_continuity(status, later, trusted_contiguous=True, sequence=102),
        renew_status_continuity(
            status, NOW + timedelta(seconds=60), trusted_contiguous=True, sequence=101
        ),
    ):
        assert rejected.state == "unknown" and not rejected.bootstrap_verified
        assert rejected.valid_until is None
        assert rejected.continuity_generation == status.continuity_generation + 1
    lost = lose_status_continuity(status)
    assert not status_current(lost, NOW)
    with pytest.raises(ValueError):
        lose_status_continuity(replace(status, continuity_generation=9007199254740991))


@pytest.mark.parametrize("product", sorted(PRODUCTS))
def test_every_admission_is_semantic_current_and_hash_bound(product: str) -> None:
    evidence = valid()
    for change in (
        {"valid_until": NOW},
        {"approved": False},
        {"row_hash": "bad"},
        {"generation": True},
    ):
        admissions = tuple(
            replace(row, **change) if row.product == product else row for row in evidence.admissions
        )
        decision = evaluate_execution(replace(evidence, admissions=admissions), NOW)
        assert decision.reason == "permission_unavailable" and not decision.allowed


def test_reason_priority_before_lower_priority_failures() -> None:
    evidence = replace(
        valid(),
        action_current=False,
        session_state="closed",
        status=StatusEvidence(),
        quote=QuoteEvidence(),
    )
    assert evaluate_execution(evidence, NOW).reason == "action_unavailable"
    assert (
        evaluate_execution(replace(evidence, admissions=()), NOW).reason == "permission_unavailable"
    )


@pytest.mark.parametrize(
    "change",
    [
        {"event_at": NOW - timedelta(days=1), "session_date": NOW.date() - timedelta(days=1)},
        {"event_at": NOW + timedelta(seconds=1)},
        {"bid": Decimal("NaN")},
        {"bid": Decimal("101")},
        {"ask": Decimal("Infinity")},
        {"ask": Decimal("100.000000001")},
        {"provider_asset_id": "other"},
        {"admission_generation": 2},
        {"feed": "sip"},
    ],
)
def test_invalid_or_previous_session_quote(change: dict) -> None:
    evidence = valid()
    assert (
        evaluate_execution(replace(evidence, quote=replace(evidence.quote, **change)), NOW).reason
        == "quote_unavailable"
    )


def mark(execution: ExecutionEvidence) -> ValuationEvidence:
    return ValuationEvidence(execution, NOW + timedelta(hours=1), NOW + timedelta(hours=2))


@pytest.mark.parametrize("state", ["garbage", "OPEN", "", None, True, 1])
@pytest.mark.parametrize("halted", [False, True])
def test_malformed_session_state_never_authorizes_execution_or_marks(
    state: object, halted: bool
) -> None:
    evidence = replace(valid(), session_state=state)
    if halted:
        evidence = replace(evidence, status=replace(evidence.status, state="halted"))
    execution = evaluate_execution(evidence, NOW)
    assert not execution.allowed
    assert execution.reason == ("halted" if halted else "session_unavailable")
    valuation = evaluate_valuation(mark(evidence), NOW)
    assert valuation.mode == "unavailable"
    assert valuation.reason == "session_unavailable"
    assert valuation.mid is None


def test_exact_midpoint_is_not_rounded_and_fresh_deadline_is_bounded() -> None:
    result = evaluate_valuation(mark(valid()), NOW)
    assert result.mode == "fresh"
    assert result.mid == Decimal("100.000000005")
    assert result.valid_until == NOW + timedelta(seconds=60)


@pytest.mark.parametrize("mode", ["closed", "halted"])
def test_historical_mark_can_outlive_execution_quote_age_but_not_authority(mode: str) -> None:
    evidence = valid()
    evidence = replace(evidence, quote=replace(evidence.quote, event_at=NOW - timedelta(hours=1)))
    if mode == "closed":
        evidence = replace(evidence, session_state="closed")
    else:
        evidence = replace(evidence, status=replace(evidence.status, state="halted"))
    result = evaluate_valuation(mark(evidence), NOW)
    assert result.mode == mode and result.mid == Decimal("100.000000005")
    assert result.event_at == NOW - timedelta(hours=1)
    assert not evaluate_execution(evidence, NOW).allowed
    assert (
        evaluate_valuation(replace(mark(evidence), retained_until=NOW), NOW).mode == "unavailable"
    )
    assert evaluate_valuation(mark(replace(evidence, action_current=False)), NOW).mid is None


@pytest.mark.parametrize("state", ["unknown", "frozen"])
def test_no_unknown_or_frozen_historical_fallback(state: str) -> None:
    evidence = valid()
    evidence = replace(
        evidence, session_state="closed", status=replace(evidence.status, state=state)
    )
    result = evaluate_valuation(mark(evidence), NOW)
    assert result.mode == "unavailable" and result.mid is None


@pytest.mark.parametrize(
    "change",
    [
        {"session_state": "unknown"},
        {"session_valid_until": NOW},
        {"calendar_generation": True},
        {"calendar_generation": 2},
    ],
)
def test_halt_mark_never_outlives_calendar_authority(change: dict) -> None:
    evidence = valid()
    evidence = replace(evidence, status=replace(evidence.status, state="halted"), **change)
    result = evaluate_valuation(mark(evidence), NOW)
    assert result.mode == "unavailable" and result.mid is None
    assert result.reason == "session_unavailable"
