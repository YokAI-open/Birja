"""Finite synthetic status proofs do not activate a provider transport."""

from dataclasses import replace
from datetime import timedelta

import pytest

from app.services.stock_status_rules import StatusBatch, StatusEvent, normalize_status_batch
from app.services.stock_trading_rules import MAX_SAFE, status_current
from tests.test_stock_trading_rules import NOW


def batch(**changes):
    fields = dict(
        events=(
            StatusEvent(
                16,
                "fixture-aapl",
                "normal",
                NOW - timedelta(hours=1),
                NOW.date(),
                10,
                "synthetic-baseline",
            ),
        ),
        observed_at=NOW,
        admission_generation=1,
        continuity_generation=1,
        baseline_verified=True,
        contiguous=True,
        complete=True,
        end_marker=True,
    )
    fields.update(changes)
    return StatusBatch(**fields)


def test_verified_complete_baseline_accepts_old_unchanged_normal_event():
    result = normalize_status_batch(
        batch(), {}, {16: "fixture-aapl"}, admission_until=NOW + timedelta(hours=1), now=NOW
    )[16]
    assert result.state == "normal"
    assert status_current(result, NOW)
    assert result.valid_until == NOW + timedelta(seconds=60)


def normalize(value, previous=None, *, now=NOW, deadline=None):
    return normalize_status_batch(
        value,
        previous or {},
        {16: "fixture-aapl"},
        admission_until=deadline or NOW + timedelta(hours=1),
        now=now,
    )[16]


@pytest.mark.parametrize(
    "change",
    [
        {"baseline_verified": False},
        {"baseline_verified": 1},
        {"complete": False},
        {"contiguous": False},
        {"end_marker": False},
        {"lost": True},
        {"reconnected": True},
        {"admission_generation": 0},
        {"continuity_generation": 0},
        {"admission_generation": True},
        {"observed_at": NOW + timedelta(seconds=1)},
        {"observed_at": NOW.replace(tzinfo=None)},
        {"events": ()},
    ],
)
def test_missing_or_ambiguous_proof_cannot_mint_normal(change):
    result = normalize(batch(**change))
    assert result.state == "unknown"
    assert not result.bootstrap_verified and not result.continuity_current
    assert result.valid_until is None


def test_strict_expiry_and_admission_cap():
    assert normalize(batch(), now=NOW + timedelta(seconds=60)).state == "unknown"
    assert normalize(batch(), deadline=NOW).state == "unknown"
    result = normalize(batch(), deadline=NOW + timedelta(seconds=12))
    assert result.valid_until == NOW + timedelta(seconds=12)
    assert not status_current(result, result.valid_until)


def test_duplicate_frame_is_idempotent_without_extending_lease():
    first = normalize(batch())
    assert normalize(batch(), {16: first}, now=NOW + timedelta(seconds=1)) == first


def test_contiguous_halt_and_explicit_resume_keep_monotone_source_order():
    first = normalize(batch())
    halted_frame = replace(batch().events[0], state="halted", event_at=NOW, sequence=11)
    halted = normalize(batch(events=(halted_frame,), baseline_verified=False), {16: first})
    assert halted.state == "halted" and status_current(halted, NOW)
    resumed_frame = replace(
        halted_frame, state="normal", event_at=NOW + timedelta(seconds=1), sequence=12
    )
    resumed = normalize(
        batch(
            events=(resumed_frame,), baseline_verified=False, observed_at=NOW + timedelta(seconds=1)
        ),
        {16: halted},
        now=NOW + timedelta(seconds=1),
    )
    assert resumed.state == "normal" and resumed.sequence == 12
    older = replace(resumed_frame, event_at=NOW - timedelta(seconds=1))
    refused = normalize(batch(events=(older,), baseline_verified=False), {16: halted})
    assert refused.state == "unknown" and refused.valid_until is None


@pytest.mark.parametrize("state", ["frozen", "halted"])
def test_later_hold_is_not_cleared_by_older_bootstrap(state):
    old = replace(normalize(batch()), state=state, event_at=NOW)
    result = normalize(batch(continuity_generation=2), {16: old})
    assert result.state == "unknown" and not result.continuity_current


def test_loss_clears_current_baseline_and_resume_needs_new_verified_baseline():
    normal = normalize(batch())
    lost = normalize(batch(lost=True), {16: normal})
    assert lost.state == "unknown" and lost.continuity_generation == 2
    frame = replace(batch().events[0], event_at=NOW, sequence=11)
    assert (
        normalize(
            batch(events=(frame,), baseline_verified=False, continuity_generation=2), {16: lost}
        ).state
        == "unknown"
    )
    restored = normalize(batch(events=(frame,), continuity_generation=3), {16: lost})
    assert restored.state == "normal" and restored.continuity_generation == 3


@pytest.mark.parametrize(
    "change",
    [
        {"state": "unreviewed-code"},
        {"state": "unknown"},
        {"sequence": True},
        {"sequence": MAX_SAFE + 1},
        {"coin_id": True},
        {"coin_id": 17},
        {"provider_asset_id": "another-asset"},
        {"event_at": NOW + timedelta(seconds=1)},
        {"event_at": NOW.replace(tzinfo=None)},
        {"source_ref": ""},
        {"source_ref": " " * 3000 + "x"},
    ],
)
def test_bad_frame_cannot_authorize_status(change):
    result = normalize(batch(events=(replace(batch().events[0], **change),)))
    assert result.state == "unknown" and not result.bootstrap_verified


def test_bounded_events_bytes_and_scope():
    frame = replace(batch().events[0], source_ref="x" * 2048)
    assert normalize(batch(events=(frame,) * 1001)).state == "unknown"
    assert (
        normalize(batch(events=tuple(replace(frame, sequence=i) for i in range(1000)))).state
        == "unknown"
    )
    with pytest.raises(ValueError, match="bounded"):
        normalize_status_batch(
            batch(),
            {},
            {i: str(i) for i in range(1, 22)},
            admission_until=NOW + timedelta(hours=1),
            now=NOW,
        )


def test_generation_cannot_wrap_on_loss():
    old = replace(normalize(batch()), continuity_generation=MAX_SAFE)
    with pytest.raises(ValueError, match="generation"):
        normalize(batch(lost=True), {16: old})
