"""Exact public financial vectors; later SQL authority must match these values."""

from dataclasses import FrozenInstanceError
from decimal import ROUND_UP, Decimal, Inexact, Rounded, localcontext
from typing import Any

import pytest

from app.services.dividend_rules import DividendRuleError, evaluate_dividend_target

# Literal independent expected amounts, also consumed by actual SQL parity tests.
TARGET_VECTORS = (
    ("1", ".005", "0.00"),
    ("1", ".015", "0.02"),
    ("1", ".025", "0.02"),
    ("3", ".005", "0.02"),
    ("1", "1.005", "1.00"),
    ("1", "1.015", "1.02"),
    ("999999999999", ".00000001", "10000.00"),
    ("1", "999999999999.99499999", "999999999999.99"),
    ("0", "999999999999.99999999", "0.00"),
    ("100", "0", "0.00"),
)


@pytest.mark.parametrize("quantity,rate,expected", TARGET_VECTORS)
def test_target_vectors(quantity: str, rate: str, expected: str) -> None:
    result = evaluate_dividend_target(Decimal(quantity), Decimal(rate), Decimal(0), Decimal(0))
    assert result.desired_total == Decimal(expected)


# Distinct target revisions may repeat an earlier economic amount. Persistence
# supplies target identities; this oracle intentionally accepts A again after B.
def test_a_b_a_and_repeated_target() -> None:
    a = evaluate_dividend_target(Decimal(10), Decimal(".25"), Decimal(0), Decimal(10))
    assert (a.applied_delta, a.cash_after) == (Decimal("2.50"), Decimal("12.50"))
    b = evaluate_dividend_target(Decimal(10), Decimal(".35"), Decimal("2.50"), a.cash_after)
    assert (b.desired_total, b.proposed_delta, b.cash_after) == (
        Decimal("3.50"),
        Decimal("1.00"),
        Decimal("13.50"),
    )
    a_again = evaluate_dividend_target(Decimal(10), Decimal(".25"), Decimal("3.50"), b.cash_after)
    assert (a_again.applied_delta, a_again.cash_after, a_again.outcome, a_again.reason) == (
        Decimal("-1.00"),
        Decimal("12.50"),
        "applied",
        "target_applied",
    )
    repeat = evaluate_dividend_target(
        Decimal(10), Decimal(".25"), Decimal("2.50"), a_again.cash_after
    )
    assert (repeat.applied_delta, repeat.cash_after, repeat.outcome, repeat.reason) == (
        Decimal("0.00"),
        Decimal("12.50"),
        "verified_no_change",
        "target_unchanged",
    )


def test_correction_uses_rounded_totals_not_rounded_rate_difference() -> None:
    # Prior 1×.005 paid .00, next 1×.015 owes .02; rate difference is .01.
    corrected = evaluate_dividend_target(Decimal(1), Decimal(".015"), Decimal("0.00"), Decimal(0))
    assert corrected.applied_delta == Decimal(".02")
    # Reverse has a negative half-cent rate change but a whole two-cent debit.
    reversed_target = evaluate_dividend_target(
        Decimal(1), Decimal(".005"), Decimal(".02"), Decimal(".02")
    )
    assert (reversed_target.applied_delta, reversed_target.cash_after) == (
        Decimal("-.02"),
        Decimal(0),
    )


def test_held_proposals_never_enter_cumulative_applied_then_apply_when_affordable() -> None:
    for _ in range(2):
        held = evaluate_dividend_target(Decimal(10), Decimal(".10"), Decimal(3), Decimal("1.99"))
        assert (held.desired_total, held.cumulative_applied_before, held.proposed_delta) == (
            Decimal("1.00"),
            Decimal("3.00"),
            Decimal("-2.00"),
        )
        assert (held.applied_delta, held.cash_after, held.outcome, held.reason) == (
            Decimal("0.00"),
            Decimal("1.99"),
            "held_unaffordable",
            "insufficient_cash",
        )
    applied = evaluate_dividend_target(Decimal(10), Decimal(".10"), Decimal(3), Decimal(2))
    assert (applied.applied_delta, applied.cash_after, applied.outcome) == (
        Decimal("-2.00"),
        Decimal("0.00"),
        "applied",
    )


@pytest.mark.parametrize("quantity,rate", [(None, None), (None, Decimal(0)), (Decimal(0), None)])
def test_uncertainty_has_no_target_or_proposal_and_never_reverses(
    quantity: Decimal | None, rate: Decimal | None
) -> None:
    result = evaluate_dividend_target(quantity, rate, Decimal(10), Decimal(20))
    assert result.desired_total is None
    assert result.proposed_delta is None
    assert (result.cumulative_applied_before, result.applied_delta, result.cash_after) == (
        Decimal(10),
        Decimal(0),
        Decimal(20),
    )
    assert (result.outcome, result.reason) == ("held_uncertain", "terms_unverified")


@pytest.mark.parametrize("quantity,rate", [("0", "1"), ("5", "0")])
def test_verified_zero_can_reverse_original(quantity: str, rate: str) -> None:
    result = evaluate_dividend_target(Decimal(quantity), Decimal(rate), Decimal(10), Decimal(10))
    assert (result.desired_total, result.applied_delta, result.cash_after) == (
        Decimal("0.00"),
        Decimal("-10.00"),
        Decimal("0.00"),
    )


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize("bad", ["NaN", "sNaN", "Infinity", "-Infinity", "-0.01", "1000000000000"])
def test_rejects_nonfinite_negative_and_out_of_range(index: int, bad: str) -> None:
    values = [Decimal(1), Decimal(1), Decimal(0), Decimal(0)]
    values[index] = Decimal(bad)
    with pytest.raises(DividendRuleError, match="represented safely") as exc:
        evaluate_dividend_target(*values)
    assert exc.value.code == "numeric_range"


@pytest.mark.parametrize("index,bad", [(0, ".5"), (1, ".000000001"), (2, ".001"), (3, ".001")])
def test_rejects_unrepresentable_scale(index: int, bad: str) -> None:
    values = [Decimal(1), Decimal(1), Decimal(0), Decimal(0)]
    values[index] = Decimal(bad)
    with pytest.raises(DividendRuleError):
        evaluate_dividend_target(*values)


@pytest.mark.parametrize("index", range(4))
@pytest.mark.parametrize("bad", [1, 0.5, "1", True])
def test_never_coerces_non_decimal(index: int, bad: Any) -> None:
    values: list[Any] = [Decimal(1), Decimal(1), Decimal(0), Decimal(0)]
    values[index] = bad
    with pytest.raises(DividendRuleError):
        evaluate_dividend_target(*values)


@pytest.mark.parametrize(
    "quantity,rate,cumulative,cash",
    [
        ("999999999999", "999999999999.99999999", "0", "0"),
        ("1", "999999999999.995", "0", "0"),
        ("1", ".01", "0", "999999999999.99"),
    ],
)
def test_rejects_exact_product_rounded_target_and_result_cash_overflow(
    quantity: str, rate: str, cumulative: str, cash: str
) -> None:
    with pytest.raises(DividendRuleError):
        evaluate_dividend_target(
            Decimal(quantity), Decimal(rate), Decimal(cumulative), Decimal(cash)
        )


def test_maximum_money_and_exotic_ambient_context_do_not_round_intermediates() -> None:
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.rounding = ROUND_UP
        ctx.Emax = 2
        ctx.traps[Inexact] = True
        ctx.traps[Rounded] = True
        result = evaluate_dividend_target(
            Decimal("999999999999"),
            Decimal(".00000001"),
            Decimal("9999.99"),
            Decimal("999999999999.98"),
        )
        assert result.desired_total == Decimal("10000.00")
        assert result.proposed_delta == Decimal(".01")
        assert result.cash_after == Decimal("999999999999.99")
        assert ctx.prec == 2
        assert ctx.rounding == ROUND_UP


def test_uncertain_still_validates_known_inputs_and_locked_snapshot() -> None:
    with pytest.raises(DividendRuleError):
        evaluate_dividend_target(None, Decimal("NaN"), Decimal(0), Decimal(0))
    with pytest.raises(DividendRuleError):
        evaluate_dividend_target(None, None, Decimal("-.01"), Decimal(0))
    with pytest.raises(DividendRuleError):
        evaluate_dividend_target(None, None, Decimal(0), Decimal("-.01"))


def test_immutable_result_and_zero_original_are_truthful() -> None:
    result = evaluate_dividend_target(Decimal(1), Decimal(".005"), Decimal(0), Decimal(10))
    assert (result.desired_total, result.proposed_delta, result.applied_delta) == (
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
    )
    assert (result.outcome, result.reason, result.cash_after) == (
        "verified_no_change",
        "target_unchanged",
        Decimal(10),
    )
    with pytest.raises(FrozenInstanceError):
        result.cash_after = Decimal(100)  # type: ignore[misc]
