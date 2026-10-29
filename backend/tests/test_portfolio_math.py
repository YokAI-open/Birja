from datetime import UTC, datetime
from decimal import Decimal as D
from decimal import localcontext

from app.services.portfolio_math import PositionInput, calculate_portfolio


def position(quantity="0.00099501", basis="100", mid="100000", symbol="BTC"):
    return PositionInput(
        symbol,
        symbol,
        True,
        D(quantity),
        D(basis),
        None if mid is None else D(mid),
        None if mid is None else datetime(2026, 10, 29, tzinfo=UTC),
    )


def test_fee_inclusive_buy_uses_raw_value_and_normalizes_zero():
    p = calculate_portfolio(D("9900"), D("10000"), [position()])
    assert (p.total_value, p.total_pl, p.total_pl_percent) == (D("9999.50"), D("-0.50"), D("0.00"))
    assert str(p.total_pl_percent) == "0.00"
    h = p.holdings[0]
    assert h.current_value == D("99.50")
    assert h.average_cost == D("100501.50249746")
    assert h.unrealized_pl == D("-0.50")
    assert h.unrealized_pl_percent == D("-0.50")
    assert (p.cash_allocation_percent, h.allocation_percent) == (D("99.00"), D("1.00"))


def test_cash_only_and_liquidated_keep_actual_cash():
    for cash, pl in [("10000", "0"), ("9999", "-1")]:
        p = calculate_portfolio(D(cash), D("10000"), [])
        assert p.total_value == D(cash)
        assert p.total_pl == D(pl)
        assert p.holdings == ()
        assert p.cash_allocation_percent == D("100.00")


def test_missing_price_never_publishes_partial_totals_or_allocations():
    p = calculate_portfolio(D("5"), D("10"), [position(), position(mid=None, symbol="ETH")])
    assert p.valuation_complete is False
    assert p.total_value is p.total_pl is p.total_pl_percent is p.cash_allocation_percent is None
    assert p.holdings[0].current_value == D("99.50")
    assert p.holdings[1].current_value is p.holdings[1].unrealized_pl is None
    assert all(h.allocation_percent is None for h in p.holdings)


def test_zero_basis_start_and_total_have_explicit_null_percentages():
    p = calculate_portfolio(D("0"), D("0"), [position(quantity="1", basis="0", mid="2")])
    assert p.total_pl_percent is None
    assert p.holdings[0].average_cost == D("0")
    assert p.holdings[0].unrealized_pl_percent is None
    assert p.holdings[0].unrealized_pl == D("2")
    empty = calculate_portfolio(D("0"), D("0"), [])
    assert empty.cash_allocation_percent is None


def test_raw_intermediates_half_even_dust_and_large_derived_values():
    with localcontext() as ctx:
        ctx.prec = 6  # Calculator owns its precision independent of callers.
        p = calculate_portfolio(
            D("0"), D("1"), [position("999999999999.99999999", "1", "999999999999.99999999")]
        )
    assert p.total_value == D("999999999999999999980000.00")
    dust = calculate_portfolio(D("0"), D("1"), [position("0.00000001", "0.01", "0.00000001")])
    assert dust.holdings[0].average_cost == D("1000000.00000000")
    ties = calculate_portfolio(
        D("0"), D("1"), [position("1", "0", "0.125"), position("1", "0", "0.135", "ETH")]
    )
    assert [h.current_value for h in ties.holdings] == [D("0.12"), D("0.14")]
    assert ties.total_value == D("0.26")
