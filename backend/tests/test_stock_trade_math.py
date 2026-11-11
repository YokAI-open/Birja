"""Stock-only money boundaries, without changing crypto policy."""

from decimal import Decimal as D

import pytest

from app.services.stock_trade_math import plan_stock_trade
from app.services.trade_math import TradeRefused


def test_fractional_quantity_cannot_mint_fractional_stock() -> None:
    with pytest.raises(TradeRefused) as error:
        plan_stock_trade(
            side="buy", quantity=D("1.5"), bid=D("10"), ask=D("11"),
            cash=D("100"), held=D("0"), cost_basis=D("0"),
        )
    assert error.value.code == "invalid_quantity"
