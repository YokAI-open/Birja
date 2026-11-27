"""Exact private daily observation wire types."""

from datetime import date

from pydantic import AwareDatetime, BaseModel

from app.schemas.portfolios import PortfolioId
from app.schemas.trades import Money


class PortfolioDailyPoint(BaseModel):
    utc_day: date
    captured_at: AwareDatetime
    total_value: Money | None
    valuation_complete: bool


class PortfolioDailySeries(BaseModel):
    portfolio_id: PortfolioId
    points: list[PortfolioDailyPoint]


class PortfolioDailyHistory(BaseModel):
    start_day: date
    end_day: date
    portfolios: list[PortfolioDailySeries]
