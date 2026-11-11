"""Pure whole-share stock math, independent from crypto spread/minimum policy.

Only final notional and proportional basis removal round to cents. The exact
midpoint is retained separately from Trade's eight-place metadata.
"""

from dataclasses import dataclass
from decimal import ROUND_FLOOR, ROUND_HALF_EVEN, Decimal, localcontext

from app.services.trade_math import Q2, Q8, Side, TradeRefused, cost_basis_after

MAX_QUANTITY = Decimal("999999999999")
MAX_PRICE = Decimal("999999999999.99999999")
MAX_MONEY = Decimal("999999999999.99")
ZERO = Decimal("0")


@dataclass(frozen=True)
class StockTradePlan:
    side: Side
    quantity: Decimal
    bid: Decimal
    ask: Decimal
    exact_mid: Decimal
    mid: Decimal
    exec_price: Decimal
    notional: Decimal
    fee: Decimal
    cash_delta: Decimal
    cash_before: Decimal
    cash_after: Decimal
    held_before: Decimal
    held_after: Decimal
    cost_basis_before: Decimal
    cost_basis_after: Decimal
    whole_position: bool


def _refuse(code: str) -> TradeRefused:
    return TradeRefused(code, "This stock order cannot be represented safely.")


def _decimal(value: Decimal, *, maximum: Decimal, step: Decimal, positive: bool = False) -> bool:
    return (
        isinstance(value, Decimal)
        and value.is_finite()
        and (value > ZERO if positive else value >= ZERO)
        and value <= maximum
        and value == value.quantize(step, rounding=ROUND_HALF_EVEN)
    )


def _snapshot(*, bid: Decimal, ask: Decimal, cash: Decimal, held: Decimal, basis: Decimal) -> None:
    if not (
        _decimal(bid, maximum=MAX_PRICE, step=Q8, positive=True)
        and _decimal(ask, maximum=MAX_PRICE, step=Q8, positive=True)
        and bid <= ask
        and _decimal(cash, maximum=MAX_MONEY, step=Q2)
        and _decimal(held, maximum=MAX_QUANTITY, step=Decimal("1"))
        and _decimal(basis, maximum=MAX_MONEY, step=Q2)
        and (held != ZERO or basis == ZERO)
    ):
        raise _refuse("numeric_range")


def plan_stock_trade(
    *,
    side: Side,
    quantity: Decimal,
    bid: Decimal,
    ask: Decimal,
    cash: Decimal,
    held: Decimal,
    cost_basis: Decimal,
) -> StockTradePlan:
    """Return immutable fee-free accounting facts or a fixed domain refusal."""
    with localcontext() as ctx:
        ctx.prec = 64
        if not _decimal(quantity, maximum=MAX_QUANTITY, step=Decimal("1"), positive=True):
            raise _refuse("invalid_quantity")
        if side not in ("buy", "sell"):
            raise _refuse("numeric_range")
        _snapshot(bid=bid, ask=ask, cash=cash, held=held, basis=cost_basis)
        if side == "sell" and quantity > held:
            raise _refuse("insufficient_holding")
        exact_mid = (bid + ask) / Decimal("2")
        exec_price = ask if side == "buy" else bid
        raw_notional = quantity * exec_price
        if raw_notional > MAX_PRICE:
            raise _refuse("numeric_range")
        notional = raw_notional.quantize(Q2, rounding=ROUND_HALF_EVEN)
        if notional > MAX_MONEY or (side == "buy" and notional == ZERO):
            raise _refuse("numeric_range")
        if side == "buy" and notional > cash:
            raise _refuse("insufficient_cash")
        delta = -notional if side == "buy" else notional
        held_after = held + quantity if side == "buy" else held - quantity
        cash_after = cash + delta
        basis_after = cost_basis_after(
            side=side,
            cost_basis=cost_basis,
            held_before=held,
            quantity=quantity,
            cash_delta=delta,
        )
        if not (
            ZERO <= held_after <= MAX_QUANTITY
            and ZERO <= cash_after <= MAX_MONEY
            and ZERO <= basis_after <= MAX_MONEY
        ):
            raise _refuse("numeric_range")
        return StockTradePlan(
            side=side,
            quantity=quantity,
            bid=bid,
            ask=ask,
            exact_mid=exact_mid,
            mid=exact_mid.quantize(Q8, rounding=ROUND_HALF_EVEN),
            exec_price=exec_price,
            notional=notional,
            fee=ZERO,
            cash_delta=delta,
            cash_before=cash,
            cash_after=cash_after,
            held_before=held,
            held_after=held_after,
            cost_basis_before=cost_basis,
            cost_basis_after=basis_after,
            whole_position=side == "sell" and quantity == held,
        )


def buy_max_quantity(*, bid: Decimal, ask: Decimal, cash: Decimal,
                     held: Decimal, cost_basis: Decimal) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = 64
        return (cash / ask).to_integral_value(rounding=ROUND_FLOOR)


def sell_all_quantity(*, bid: Decimal, ask: Decimal, cash: Decimal,
                      held: Decimal, cost_basis: Decimal) -> Decimal:
    return held
