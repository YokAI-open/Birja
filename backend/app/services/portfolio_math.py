"""Pure mid-price valuation. Only response boundaries are rounded."""

from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Literal


@dataclass(frozen=True)
class PositionInput:
    symbol: str
    name: str
    is_active: bool
    quantity: Decimal
    cost_basis: Decimal
    mid: Decimal | None
    as_of: datetime | None
    asset_class: Literal["crypto", "stock"] = field(default="crypto", kw_only=True)
    coin_id: str = field(default="0", kw_only=True)
    provider_asset_id: str | None = field(default=None, kw_only=True)
    units_safe: bool = field(default=True, kw_only=True)


@dataclass(frozen=True)
class PositionValue(PositionInput):
    average_cost: Decimal | None
    current_value: Decimal | None
    unrealized_pl: Decimal | None
    unrealized_pl_percent: Decimal | None
    allocation_percent: Decimal | None


@dataclass(frozen=True)
class ClassValues:
    cash: Decimal
    stocks: Decimal | None
    crypto: Decimal | None


@dataclass(frozen=True)
class ClassAllocation:
    cash: Decimal | None
    stocks: Decimal | None
    crypto: Decimal | None


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
    known_value: Decimal
    unvalued_holding_count: int
    class_values: ClassValues
    class_allocation_percent: ClassAllocation


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
        ctx.prec = 64
        held = sorted(
            (
                p if p.units_safe else replace(p, mid=None, as_of=None)
                for p in positions
                if p.quantity > 0
            ),
            key=lambda p: (p.symbol, int(p.coin_id)),
        )
        raw_values = [p.quantity * p.mid if p.mid is not None else None for p in held]
        complete = all(value is not None for value in raw_values)
        known = cash + sum((v for v in raw_values if v is not None), Decimal(0))
        total = known if complete else None
        pl = total - starting_cash if total is not None else None

        def allocation(value: Decimal | None) -> Decimal | None:
            return _round(value / total * 100) if value is not None and total else None

        holdings = []
        for p, raw in zip(held, raw_values, strict=True):
            unrealized = raw - p.cost_basis if raw is not None else None
            holdings.append(
                PositionValue(
                    **{**asdict(p), "cost_basis": _round(p.cost_basis)},
                    average_cost=_round(p.cost_basis / p.quantity, "0.00000001")
                    if p.units_safe
                    else None,
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

        def class_value(asset: str) -> Decimal | None:
            values = [v for p, v in zip(held, raw_values, strict=True) if p.asset_class == asset]
            return (
                sum((v for v in values if v is not None), Decimal(0))
                if all(v is not None for v in values)
                else None
            )

        stocks, crypto = class_value("stock"), class_value("crypto")
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
            known_value=_round(known),
            unvalued_holding_count=sum(v is None for v in raw_values),
            class_values=ClassValues(
                _round(cash),
                _round(stocks) if stocks is not None else None,
                _round(crypto) if crypto is not None else None,
            ),
            class_allocation_percent=ClassAllocation(
                allocation(cash), allocation(stocks), allocation(crypto)
            ),
        )
