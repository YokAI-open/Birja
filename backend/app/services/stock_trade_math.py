"""Stock planning seam; replaced by the exact stock rules in the GREEN gate."""

from decimal import Decimal

from app.services.trade_math import Plan, Side, TradeCosts, plan_trade


def plan_stock_trade(
    *,
    side: Side,
    quantity: Decimal,
    bid: Decimal,
    ask: Decimal,
    cash: Decimal,
    held: Decimal,
    cost_basis: Decimal,
) -> Plan:
    return plan_trade(
        symbol="STOCK",
        side=side,
        kind="quantity",
        value=quantity,
        mid=ask if side == "buy" else bid,
        cash=cash,
        held=held,
        costs=TradeCosts(*(Decimal("0") for _ in range(4))),
    )
