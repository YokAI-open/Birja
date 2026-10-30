"""Pure mid-price valuation. Only response boundaries are rounded."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext


@dataclass(frozen=True)
class PositionInput:
    symbol: str
    name: str
    is_active: bool
    quantity: Decimal
    cost_basis: Decimal
    mid: Decimal | None
    as_of: datetime | None


@dataclass(frozen=True)
class PositionValue(PositionInput):
    average_cost: Decimal
    current_value: Decimal | None
    unrealized_pl: Decimal | None
    unrealized_pl_percent: Decimal | None
    allocation_percent: Decimal | None


@dataclass(frozen=True)
class PortfolioValue:
    cash: Decimal
    starting_cash: Decimal
    total_value: Decimal | None
    total_pl: Decimal | None
    total_pl_percent: Decimal | None
    cash_allocation_percent: Decimal | None
    valuation_complete: bool
    holdings: tuple[PositionValue, ...]


def _round(value: Decimal, places: str = "0.01") -> Decimal:
    result = value.quantize(Decimal(places), rounding=ROUND_HALF_EVEN)
    return result.copy_abs() if result.is_zero() else result


def calculate_portfolio(
    cash: Decimal, starting_cash: Decimal, positions: Sequence[PositionInput]
) -> PortfolioValue:
    """Value positive positions without rounding inputs or intermediate results.

    Missing prices invalidate totals and every allocation, while known positions
    retain their independent value. Zero denominators have no defined percentage.
    """
    with localcontext() as ctx:
        ctx.prec = 50
        held = [p for p in positions if p.quantity > 0]
        raw_values = [p.quantity * p.mid if p.mid is not None else None for p in held]
        complete = all(value is not None for value in raw_values)
        total = (
            cash + sum((v for v in raw_values if v is not None), Decimal(0)) if complete else None
        )
        pl = total - starting_cash if total is not None else None

        def allocation(value: Decimal | None) -> Decimal | None:
            return _round(value / total * 100) if value is not None and total else None

        holdings = []
        for p, raw in zip(held, raw_values, strict=True):
            unrealized = raw - p.cost_basis if raw is not None else None
            holdings.append(
                PositionValue(
                    symbol=p.symbol,
                    name=p.name,
                    is_active=p.is_active,
                    quantity=p.quantity,
                    cost_basis=_round(p.cost_basis),
                    mid=p.mid,
                    as_of=p.as_of,
                    average_cost=_round(p.cost_basis / p.quantity, "0.00000001"),
                    current_value=_round(raw) if raw is not None else None,
                    unrealized_pl=_round(unrealized) if unrealized is not None else None,
                    unrealized_pl_percent=(
                        _round(unrealized / p.cost_basis * 100)
                        if unrealized is not None and p.cost_basis
                        else None
                    ),
                    allocation_percent=allocation(raw),
                )
            )
        return PortfolioValue(
            cash=_round(cash),
            starting_cash=_round(starting_cash),
            total_value=_round(total) if total is not None else None,
            total_pl=_round(pl) if pl is not None else None,
            total_pl_percent=(
                _round(pl / starting_cash * 100) if pl is not None and starting_cash else None
            ),
            cash_allocation_percent=allocation(cash),
            valuation_complete=complete,
            holdings=tuple(holdings),
        )
