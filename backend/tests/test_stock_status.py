"""Finite synthetic status proofs do not activate a provider transport."""

from datetime import timedelta

from app.services.stock_status_rules import StatusBatch, StatusEvent, normalize_status_batch
from app.services.stock_trading_rules import status_current
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
