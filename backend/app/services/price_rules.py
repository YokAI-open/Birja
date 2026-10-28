"""Pure price acceptance rules (PRICE-04, D-04). No I/O.

A poll is accepted when the new mid is within ``max_move`` of the last good
price. A bigger jump is held back as a candidate; if ``confirm_n`` consecutive
polls stay within ``confirm_tol`` of the first rejected value (the anchor) the
move is treated as genuine and accepted.

The candidate state lives in memory in the single scheduler process and is
rebuildable: after a restart a real jump is simply confirmed again.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Literal

Decision = Literal["accept", "accept_confirmed", "reject_invalid", "reject_spike"]

_MID_QUANTUM = Decimal("1e-8")


@dataclass(frozen=True)
class Candidate:
    anchor: Decimal
    count: int


def parse_price(raw: object) -> Decimal | None:
    """Parse a Kraken price string; None unless it is a finite positive number."""
    if not isinstance(raw, str):
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        return None
    if not value.is_finite() or value <= 0:
        return None
    return value


def _first(entry: dict[str, object], key: str) -> Decimal | None:
    side = entry.get(key)
    if not isinstance(side, list) or not side:
        return None
    return parse_price(side[0])


def mid_from_ticker(entry: object) -> Decimal | None:
    """Mid of best bid and ask, rounded half-even to 8 dp; None if unusable."""
    if not isinstance(entry, dict):
        return None
    bid = _first(entry, "b")
    ask = _first(entry, "a")
    if bid is None or ask is None or bid > ask:
        return None
    mid = ((bid + ask) / 2).quantize(_MID_QUANTUM, rounding=ROUND_HALF_EVEN)
    if mid <= 0:
        return None
    return mid


def evaluate_price(
    last_good: Decimal | None,
    new: Decimal,
    candidate: Candidate | None,
    *,
    max_move: Decimal = Decimal("0.25"),
    confirm_tol: Decimal = Decimal("0.05"),
    confirm_n: int = 3,
) -> tuple[Decision, Candidate | None]:
    """Decide what to do with ``new``; returns the decision and the next candidate."""
    if not new.is_finite() or new <= 0:
        return "reject_invalid", candidate
    if last_good is None:
        return "accept", None
    if abs(new - last_good) / last_good <= max_move:
        return "accept", None
    if candidate is not None and abs(new - candidate.anchor) / candidate.anchor <= confirm_tol:
        count = candidate.count + 1
        if count >= confirm_n:
            return "accept_confirmed", None
        return "reject_spike", Candidate(candidate.anchor, count)
    return "reject_spike", Candidate(new, 1)
