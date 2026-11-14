"""Synthetic source economics, genuine calendar rules and exact all-owner math."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

import pytest

from app.services.corporate_action_rules import (
    NormalizedAction,
    SplitOwner,
    classify_action,
    dividend_cutoff,
    plan_forward_split,
)
from app.services.stock_action_rules import evaluate_action_state
from tests.test_stock_sessions import evidence

NOW = datetime(2026, 11, 10, 15, tzinfo=UTC)


def dividend(**changes) -> NormalizedAction:
    return replace(
        NormalizedAction(
            "synthetic-event",
            21,
            "AAPL",
            "cash_dividend",
            date(2026, 11, 9),
            NOW,
            currency="USD",
            rate=Decimal("0.25"),
            ex_date=date(2026, 11, 10),
            record_date=date(2026, 11, 10),
            payable_date=date(2026, 11, 20),
            subtype="ordinary",
            foreign=False,
            special=False,
            due_bills=False,
            identity_verified=True,
            dates_verified=True,
        ),
        **changes,
    )


def split(**changes) -> NormalizedAction:
    return replace(
        dividend(
            event_type="forward_split",
            currency=None,
            rate=None,
            new_rate=Decimal(2),
            old_rate=Decimal(1),
            economic_at=NOW,
            units="pre_split",
        ),
        **changes,
    )


def test_supported_ordinary_dividend_retains_exact_nullable_source_facts() -> None:
    action = dividend()
    result = classify_action(action)
    assert result.kind == "supported_dividend"
    assert result.action is action
    assert result.reason == "none"
    assert result.action.source_event_at is None


@pytest.mark.parametrize(
    "changes",
    [
        {"currency": None},
        {"currency": ""},
        {"currency": "EUR"},
        {"foreign": None},
        {"foreign": True},
        {"special": None},
        {"special": True},
        {"subtype": None},
        {"subtype": "return_of_capital"},
        {"due_bills": None},
        {"due_bills": True},
        {"identity_verified": False},
        {"dates_verified": False},
        {"rate": Decimal("NaN")},
        {"rate": Decimal("Infinity")},
        {"rate": Decimal("1e999999")},
        {"rate": Decimal("1e-999999")},
        {"rate": Decimal(0)},
        {"rate": True},
        {"rate": 1.5},
        {"ex_date": None},
        {"record_date": date(2026, 11, 9)},
        {"payable_date": date(2026, 11, 9)},
        {"process_date": "2026-11-09"},
        {"ex_date": NOW},
        {"observed_at": NOW.replace(tzinfo=None)},
    ],
)
def test_missing_conflicting_or_adversarial_dividend_is_held(changes) -> None:
    assert classify_action(dividend(**changes)).kind != "supported_dividend"


def test_identity_change_and_cancellation_never_apply_automatically() -> None:
    assert classify_action(dividend(identity_changed=True)).reason == "identity_change"
    assert classify_action(split(cancelled=True)).kind == "cancelled"
    assert not plan_forward_split(split(cancelled=True), []).allowed


@pytest.mark.parametrize(
    "units,order,allowed",
    [
        (None, None, False),
        ("old", 1, False),
        ("pre_split", None, False),
        ("pre_split", 0, False),
        ("pre_split", 1, True),
        ("post_split", 2, True),
    ],
)
def test_same_boundary_dividend_requires_explicit_units_and_order(units, order, allowed) -> None:
    result = classify_action(dividend(same_boundary_split=True, units=units, economic_order=order))
    assert (result.kind == "supported_dividend") is allowed


@pytest.mark.parametrize("day,hour", [("2026-03-06", 14), ("2026-03-09", 13), ("2026-11-27", 14)])
def test_cutoff_is_genuine_open_with_dst_and_early_close(day, hour) -> None:
    now = datetime.fromisoformat(day + "T15:00:00+00:00")
    action = dividend(
        process_date=now.date(),
        ex_date=now.date(),
        record_date=now.date(),
        payable_date=now.date() + timedelta(days=7),
        observed_at=now,
    )
    cutoff = dividend_cutoff(action, "NASDAQ", now, evidence(now))
    assert cutoff is not None and cutoff.cutoff == now.replace(hour=hour, minute=30)
    assert cutoff.exclusive and cutoff.rule == "exclusive-regular-session-open"
    assert cutoff.calendar_generation == evidence(now).generation


def test_holiday_or_missing_authority_never_guesses_cutoff() -> None:
    action = dividend(
        ex_date=date(2026, 11, 26), record_date=date(2026, 11, 26), payable_date=date(2026, 12, 1)
    )
    assert dividend_cutoff(action, "NYSE", NOW, evidence(NOW)) is None
    assert dividend_cutoff(dividend(), "NYSE", NOW, None) is None


@pytest.mark.parametrize("new,old,quantity,expected", [(2, 1, 3, 6), (3, 2, 4, 6), (4, 1, 0, 0)])
def test_exact_forward_split_preserves_total_basis(new, old, quantity, expected) -> None:
    owner = SplitOwner(1, Decimal(quantity), Decimal("123.45") if quantity else Decimal(0))
    result = plan_forward_split(split(new_rate=Decimal(new), old_rate=Decimal(old)), [owner])
    assert result.allowed and result.ratio == Fraction(new, old)
    assert result.owners == (replace(owner, quantity=Decimal(expected)),)


@pytest.mark.parametrize(
    "quantity",
    [
        Decimal(1),
        Decimal("999999999999"),
        Decimal("1.5"),
        Decimal("1e999999"),
        Decimal("1e-999999"),
        Decimal("NaN"),
        True,
        1.2,
    ],
)
def test_any_bad_owner_holds_everyone(quantity) -> None:
    result = plan_forward_split(
        split(new_rate=Decimal(3), old_rate=Decimal(2)),
        [SplitOwner(1, Decimal(2), Decimal(10)), SplitOwner(2, quantity, Decimal(3))],
    )
    assert not result.allowed and result.owners == ()


@pytest.mark.parametrize(
    "changes",
    [
        {"new_rate": Decimal(1), "old_rate": Decimal(2)},
        {"new_rate": Decimal(1)},
        {"old_rate": Decimal(0)},
        {"new_rate": 1.5},
        {"economic_at": None},
        {"units": None},
    ],
)
def test_nonforward_or_ambiguous_split_refuses(changes) -> None:
    assert not plan_forward_split(split(**changes), []).allowed


def current(**changes):
    return evaluate_action_state(
        **{
            "now": NOW,
            "health": "current",
            "rights_current": True,
            "coverage_complete": True,
            "valid_until": NOW + timedelta(minutes=5),
            "unit_epoch": 0,
            "quote_unit_epoch": 0,
            **changes,
        }
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"declaration_date": date(2026, 11, 11)},
        {"declaration_date": "2026-11-01"},
        {"provider_event_id": " "},
        {"provider_event_id": "x" * 257},
        {"coin_id": True},
        {"symbol": []},
        {"source_event_at": NOW.replace(tzinfo=None)},
        {"economic_at": NOW.replace(tzinfo=None)},
        {"record_date": None},
        {"payable_date": None},
        {"same_boundary_split": 1},
        {"rate": Decimal("0.12345678912345678912345678912")},
    ],
)
def test_malformed_identity_dates_and_terms_remain_uncertain(changes) -> None:
    assert classify_action(dividend(**changes)).kind == "uncertain"


def test_unknown_event_and_outside_calendar_coverage_have_no_guessed_economics() -> None:
    assert classify_action(dividend(event_type="merger")).kind == "unsupported"
    assert classify_action(split(new_rate=Decimal("99999999999"))).kind == "uncertain"
    assert dividend_cutoff(split(), "NYSE", NOW, evidence(NOW)) is None
    assert dividend_cutoff(dividend(), "other", NOW, evidence(NOW)) is None


def test_split_overflow_and_invalid_basis_or_duplicate_owner_abort_entire_plan() -> None:
    owner = SplitOwner(1, Decimal("600000000000"), Decimal("1.00"))
    assert not plan_forward_split(split(), [owner]).allowed
    assert not plan_forward_split(split(), [replace(owner, total_basis=Decimal("0.001"))]).allowed
    assert not plan_forward_split(split(), [replace(owner, user_id=True)]).allowed
    assert not plan_forward_split(split(), [replace(owner, total_basis=Decimal("1e12"))]).allowed
    assert not plan_forward_split(split(), [replace(owner, quantity=Decimal(0))]).allowed
    owner = replace(owner, quantity=Decimal(2))
    assert not plan_forward_split(split(), [owner, owner]).allowed
    assert plan_forward_split(split(), []).allowed


def test_due_bills_need_verified_mapping_and_do_not_invert_split() -> None:
    assert classify_action(split(due_bills=True)).kind == "uncertain"
    assert classify_action(split(due_bills=0)).kind == "uncertain"
    assert (
        classify_action(split(due_bills=True, due_bill_mapping_verified=True)).kind
        == "supported_forward_split"
    )
    assert classify_action(split(economic_at=NOW + timedelta(days=1))).kind == "uncertain"
    assert classify_action(split(payable_date=date(2026, 11, 9))).kind == "uncertain"


def test_unknown_monitor_and_malformed_boundary_cannot_promote_current() -> None:
    assert current(health="unknown").state == "unknown"
    assert current(known_boundary=NOW.replace(tzinfo=None)).state == "unknown"
    assert current(unit_epoch=True).state == "unknown"
    assert current(quote_unit_epoch=True).state == "suspended"
    assert current(persistent_holds=("source_gap",)).reason == "conflicting"


def test_current_monitor_never_clears_persistent_hold() -> None:
    assert current().state == "current"
    assert current().valuation_allowed and not current().execution_enabled
    assert current(persistent_holds=("unsupported",)).state == "suspended"
    assert current(persistent_holds=("unsupported",), rights_current=False).state == "suspended"
    assert current(unresolved_revision=True).state == "suspended"


def test_monitor_coverage_expiry_and_known_boundary_fail_closed() -> None:
    assert current(rights_current=False).state == "unknown"
    assert current(coverage_complete=False).reason == "source_gap"
    assert current(valid_until=NOW).state == "unknown"
    assert current(health="reconciling").state == "reconciling"
    assert current(known_boundary=NOW + timedelta(seconds=10)).valid_until == NOW + timedelta(
        seconds=10
    )
    assert current(known_boundary=NOW).state == "reconciling"


def test_post_split_quote_requires_exact_epoch_and_strict_source_boundary() -> None:
    assert current(unit_epoch=1).reason == "post_split_quote_missing"
    assert (
        current(unit_epoch=1, quote_unit_epoch=1, split_boundary=NOW, quote_event_at=NOW).reason
        == "post_split_quote_missing"
    )
    assert (
        current(
            unit_epoch=1,
            quote_unit_epoch=1,
            split_boundary=NOW - timedelta(seconds=2),
            quote_event_at=NOW - timedelta(seconds=1),
        ).state
        == "current"
    )
