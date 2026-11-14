from dataclasses import asdict
from typing import Literal, Self

from pydantic import AwareDatetime, BaseModel, Field

from app.schemas.trades import Money
from app.services.portfolio import PortfolioPriceStatus, PortfolioSnapshot
from app.services.portfolio_math import ClassAllocation, ClassValues
from app.services.stock_valuation import StockMark


class HoldingOut(BaseModel):
    symbol: str
    name: str
    is_active: bool
    quantity: Money
    cost_basis: Money
    average_cost: Money | None
    asset_class: Literal["crypto", "stock"]
    coin_id: str = Field(pattern=r"^[1-9][0-9]{0,18}$")
    provider_asset_id: str | None
    stock_mark: StockMark | None
    mid: Money | None
    current_value: Money | None
    unrealized_pl: Money | None
    unrealized_pl_percent: Money | None
    allocation_percent: Money | None
    as_of: AwareDatetime | None
    age_seconds: int | None = Field(ge=0)
    status: PortfolioPriceStatus


class PortfolioOut(BaseModel):
    cash: Money
    starting_cash: Money
    total_value: Money | None
    total_pl: Money | None
    total_pl_percent: Money | None
    cash_allocation_percent: Money | None
    valuation_complete: bool
    known_value: Money
    unvalued_holding_count: int = Field(ge=0)
    class_values: ClassValues
    class_allocation_percent: ClassAllocation
    valued_at: AwareDatetime
    prices_as_of: AwareDatetime | None
    fresh_seconds: int = Field(ge=0)
    stale_seconds: int = Field(ge=0)
    holdings: list[HoldingOut]

    @classmethod
    def from_value(cls, value: PortfolioSnapshot) -> Self:
        return cls.model_validate(asdict(value))
