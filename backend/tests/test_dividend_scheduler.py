# ruff: noqa: F811
"""Real retained work discovery and restricted cash publication."""

from types import SimpleNamespace

from app.tasks.dividends import run_dividend_cycle
from tests.dividend_fixtures import (  # noqa: F401
    books,
    dividend_case,
    ownership,
    status_case,
    stock_trade_case,
)

__all__ = ["dividend_case"]


async def test_retained_due_target_credits_once(dividend_case):
    factory, ids = dividend_case
    settings = SimpleNamespace(stock_actions_enabled=True)
    await run_dividend_cycle(sessionmaker=factory, settings=settings)
    cash, rows = await books(factory, ids["user_id"])
    assert cash == 101 and len(rows[0]) == 1
