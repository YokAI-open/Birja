from dataclasses import asdict
from typing import Self

from pydantic import AwareDatetime, BaseModel, Field

from app.schemas.trades import Money
from app.services.portfolio import PortfolioPriceStatus, PortfolioSnapshot


class HoldingOut(BaseModel):
    symbol: str
    name: str
    is_active: bool
    quantity: Money
    cost_basis: Money
    average_cost: Money
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
    valued_at: AwareDatetime
    prices_as_of: AwareDatetime | None
    fresh_seconds: int = Field(ge=0)
    stale_seconds: int = Field(ge=0)
    holdings: list[HoldingOut]

    @classmethod
    def from_value(cls, value: PortfolioSnapshot) -> Self:
        return cls.model_validate(asdict(value))
