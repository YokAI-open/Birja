"""Pure trade money math (Phase 4, D-01..D-07). No I/O, no settings, no logging.

Rounding happens at five defined points and nowhere else; intermediates are never rounded:

- R1 execution price: ``q8(mid * (1 +/- spread))`` (buy up, sell down).
- R2 buy by $: ``floor8(budget / exec_price)``. The one deliberate ROUND_DOWN, because
  rounding up could spend more than the user typed.
- R3 fees in cents (HALF_EVEN) with the D-06 floor (min fee) and, on sells, the cap at notional.
- R4 notional ``q2(quantity * exec_price)`` on the quantity paths.
- R5 (``cost_basis_after``) partial-sell removal ``q2(cost_basis * quantity / held_before)``.

D-02: a buy by $ amount A moves cash by exactly ``-A``; A includes the fee, so
``fee = max(min_fee, q2(A * f / (1 + f)))`` and the coins are bought with ``A - fee``.

D-04 interpretation: for a buy by $ amount the minimum order applies to the typed amount A (the
order size the user chose, which D-02 defines as fee-inclusive). D-06 requires a $1.00 buy to
succeed with a $0.01 fee, although its coin notional is then $0.99. Quantity orders (buy and sell)
compare the $ notional at execution price against the minimum, as D-04 states; selling exactly the
whole position is allowed below the minimum (TRADE-06).

Refusal order (callers and tests depend on it): invalid combination, oversell, minimum,
NUMERIC(20,8) bound, then cash.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_DOWN, ROUND_HALF_EVEN, Decimal, localcontext
from typing import Literal

Q8 = Decimal("0.00000001")
Q2 = Decimal("0.01")
MAX_VALUE = Decimal("999999999999.99999999")  # NUMERIC(20,8) max

Side = Literal["buy", "sell"]
InputKind = Literal["usd", "quantity"]

_ZERO = Decimal("0")
_ONE = Decimal("1")


def q8(x: Decimal) -> Decimal:
    return x.quantize(Q8, rounding=ROUND_HALF_EVEN)


def q2(x: Decimal) -> Decimal:
    return x.quantize(Q2, rounding=ROUND_HALF_EVEN)


def floor8(x: Decimal) -> Decimal:
    return x.quantize(Q8, rounding=ROUND_DOWN)


class TradeRefused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class TradeCosts:
    spread: Decimal
    fee_rate: Decimal
    min_fee: Decimal
    min_order: Decimal


@dataclass(frozen=True)
class Plan:
    side: Side
    kind: InputKind
    input_value: Decimal
    mid: Decimal
    exec_price: Decimal
    quantity: Decimal
    notional: Decimal
    fee: Decimal
    cash_delta: Decimal
    cash_before: Decimal
    cash_after: Decimal
    held_before: Decimal
    held_after: Decimal
    whole_position: bool


def _below_minimum(costs: TradeCosts) -> TradeRefused:
    return TradeRefused("below_minimum", f"The minimum order is ${costs.min_order:,.2f}.")


def plan_trade(
    *,
    symbol: str,
    side: Side,
    kind: InputKind,
    value: Decimal,
    mid: Decimal,
    cash: Decimal,
    held: Decimal,
    costs: TradeCosts,
) -> Plan:
    """Price one market order and decide whether it is allowed. Raises TradeRefused."""
    with localcontext() as ctx:
        ctx.prec = 50

        if side == "sell" and kind == "usd":
            raise TradeRefused("invalid_order", "Sells must be placed by quantity.")
        if side == "sell" and value > held:
            raise TradeRefused("insufficient_quantity", f"You hold {format(held, 'f')} {symbol}.")
        if value > MAX_VALUE:
            # guards the quantize calls below against InvalidOperation on absurd input
            raise TradeRefused("order_too_large", "This order is too large.")

        sign = _ONE + costs.spread if side == "buy" else _ONE - costs.spread
        exec_price = q8(mid * sign)  # R1
        if exec_price <= _ZERO:
            raise TradeRefused("invalid_order", "No usable price for this order.")

        whole_position = False
        if kind == "usd":  # buy by $ amount, fee-inclusive (D-02)
            fee = max(costs.min_fee, q2(value * costs.fee_rate / (_ONE + costs.fee_rate)))  # R3
            notional = value - fee
            quantity = floor8(notional / exec_price)  # R2
            cash_delta = -value
            if value < costs.min_order or quantity <= _ZERO:
                raise _below_minimum(costs)
        else:
            quantity = value
            raw = quantity * exec_price
            notional = q2(raw)  # R4
            fee = max(costs.min_fee, q2(raw * costs.fee_rate))  # R3
            if side == "buy":
                cash_delta = -(notional + fee)
                if notional < costs.min_order:
                    raise _below_minimum(costs)
            else:
                fee = min(fee, notional)  # D-06: proceeds are never negative
                cash_delta = notional - fee
                whole_position = quantity == held
                if quantity <= _ZERO or (notional < costs.min_order and not whole_position):
                    raise _below_minimum(costs)

        if any(x > MAX_VALUE for x in (quantity, notional, fee, abs(cash_delta))):
            raise TradeRefused("order_too_large", "This order is too large.")

        if side == "buy" and -cash_delta > cash:
            raise TradeRefused(
                "insufficient_cash",
                f"You have ${cash:,.2f}; this order needs ${-cash_delta:,.2f}.",
            )

        held_after = held + quantity if side == "buy" else held - quantity
        return Plan(
            side=side,
            kind=kind,
            input_value=value,
            mid=mid,
            exec_price=exec_price,
            quantity=quantity,
            notional=notional,
            fee=fee,
            cash_delta=cash_delta,
            cash_before=cash,
            cash_after=cash + cash_delta,
            held_before=held,
            held_after=held_after,
            whole_position=whole_position,
        )


def cost_basis_after(
    *,
    side: Side,
    cost_basis: Decimal,
    held_before: Decimal,
    quantity: Decimal,
    cash_delta: Decimal,
) -> Decimal:
    """D-07: a buy adds the cash spent (fee included); a sell removes its pro-rata share."""
    if side == "buy":
        return cost_basis + (-cash_delta)
    if quantity == held_before:
        return _ZERO
    with localcontext() as ctx:
        ctx.prec = 50
        return cost_basis - q2(cost_basis * quantity / held_before)  # R5
