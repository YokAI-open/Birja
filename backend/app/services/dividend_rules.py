"""Pure dividend targets; retained SQL authority owns eligibility and cash writes.

The caller supplies cumulative *applied* cash, including the original payment.
Target identity and replay/deduplication belong to retained revision/entitlement
records, not economic amounts: A→B→A is a valid series of different targets.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Literal

ZERO = Decimal("0.00")
CENT = Decimal("0.01")
RATE_STEP = Decimal("0.00000001")
MAX_QUANTITY = Decimal("999999999999")
MAX_RATE = Decimal("999999999999.99999999")
MAX_MONEY = Decimal("999999999999.99")

DividendOutcome = Literal["applied", "held_uncertain", "held_unaffordable", "verified_no_change"]
DividendReason = Literal[
    "target_applied", "terms_unverified", "insufficient_cash", "target_unchanged"
]


class DividendRuleError(ValueError):
    """Invalid/unrepresentable input; never a guessed zero target."""

    code = "numeric_range"

    def __init__(self) -> None:
        super().__init__("This dividend target cannot be represented safely.")


@dataclass(frozen=True)
class DividendTarget:
    desired_total: Decimal | None
    cumulative_applied_before: Decimal
    proposed_delta: Decimal | None
    applied_delta: Decimal
    cash_after: Decimal
    outcome: DividendOutcome
    reason: DividendReason


def _validate(value: Decimal, maximum: Decimal, step: Decimal) -> None:
    if not (
        isinstance(value, Decimal)
        and value.is_finite()
        and ZERO <= value <= maximum
        and value == value.quantize(step, rounding=ROUND_HALF_EVEN)
    ):
        raise DividendRuleError


def evaluate_dividend_target(
    quantity: Decimal | None, rate: Decimal | None, cumulative_applied: Decimal, cash: Decimal
) -> DividendTarget:
    """Round one exact total, then subtract applied cash; uncertainty has no target.

    None is an explicit unknown verified term, never cancellation-as-zero. Even
    an uncertain result validates the known locked cash/applied snapshot. A
    supported verified zero term can instead authorize a genuine reversal.
    The isolated context covers all NUMERIC(20,8) products and differences,
    independently of a caller's precision, rounding mode and decimal traps.
    """
    with localcontext(Context(prec=64, rounding=ROUND_HALF_EVEN)):
        _validate(cumulative_applied, MAX_MONEY, CENT)
        _validate(cash, MAX_MONEY, CENT)
        if quantity is not None:
            _validate(quantity, MAX_QUANTITY, Decimal("1"))
        if rate is not None:
            _validate(rate, MAX_RATE, RATE_STEP)
        if quantity is None or rate is None:
            return DividendTarget(
                None, cumulative_applied, None, ZERO, cash, "held_uncertain", "terms_unverified"
            )
        raw_target = quantity * rate
        if raw_target > MAX_RATE:
            raise DividendRuleError
        desired_total = raw_target.quantize(CENT, rounding=ROUND_HALF_EVEN)
        if desired_total > MAX_MONEY:
            raise DividendRuleError
        delta = desired_total - cumulative_applied
        cash_after = cash + delta
        if cash_after < ZERO:
            return DividendTarget(
                desired_total,
                cumulative_applied,
                delta,
                ZERO,
                cash,
                "held_unaffordable",
                "insufficient_cash",
            )
        if cash_after > MAX_MONEY:
            raise DividendRuleError
        return DividendTarget(
            desired_total,
            cumulative_applied,
            delta,
            delta,
            cash_after,
            "applied" if delta else "verified_no_change",
            "target_applied" if delta else "target_unchanged",
        )
