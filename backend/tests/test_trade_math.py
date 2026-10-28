"""Money math tests: D-06 worked examples (recomputed with Decimal) and seeded invariants."""

import random
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import ROUND_DOWN, Decimal

import pytest
from app.services.trade_math import (
    MAX_VALUE,
    Plan,
    TradeCosts,
    TradeRefused,
    cost_basis_after,
    floor8,
    plan_trade,
    q2,
    q8,
)

D = Decimal
COSTS = TradeCosts(spread=D("0.0025"), fee_rate=D("0.0025"), min_fee=D("0.01"), min_order=D("1.00"))
BIG_CASH = D("10000.00")


def buy_usd(
    mid: str, amount: str, cash: str = "10000.00", symbol: str = "BTC", costs: TradeCosts = COSTS
) -> Plan:
    return plan_trade(
        symbol=symbol,
        side="buy",
        kind="usd",
        value=D(amount),
        mid=D(mid),
        cash=D(cash),
        held=D("0"),
        costs=costs,
    )


def buy_qty(mid: str, qty: str, cash: str = "10000.00", symbol: str = "BTC") -> Plan:
    return plan_trade(
        symbol=symbol,
        side="buy",
        kind="quantity",
        value=D(qty),
        mid=D(mid),
        cash=D(cash),
        held=D("0"),
        costs=COSTS,
    )


def sell(mid: str, qty: str, held: str, symbol: str = "BTC", cash: str = "10000.00") -> Plan:
    return plan_trade(
        symbol=symbol,
        side="sell",
        kind="quantity",
        value=D(qty),
        mid=D(mid),
        cash=D(cash),
        held=D(held),
        costs=COSTS,
    )


@contextmanager
def refused(code: str, message: str | None = None) -> Iterator[None]:
    with pytest.raises(TradeRefused) as info:
        yield
    assert info.value.code == code
    if message is not None:
        assert info.value.message == message


# --- rounding helpers -------------------------------------------------------------


def test_rounding_helpers() -> None:
    assert q2(D("0.125")) == D("0.12")  # half-even
    assert q2(D("0.135")) == D("0.14")
    assert q8(D("0.000000025")) == D("0.00000002")
    assert q8(D("0.000000035")) == D("0.00000004")
    assert floor8(D("0.999999999")) == D("0.99999999")
    assert D("999999999999.99999999") == MAX_VALUE


def test_trade_refused_attributes() -> None:
    e = TradeRefused("below_minimum", "msg")
    assert (e.code, e.message) == ("below_minimum", "msg")
    assert str(e) == "msg"


# --- B1: buy by dollar amount -----------------------------------------------------


def test_b1_btc() -> None:
    p = buy_usd("100000.00", "100.00")
    assert p.side == "buy" and p.kind == "usd"
    assert p.input_value == D("100.00") and p.mid == D("100000.00")
    assert p.exec_price == D("100250.00000000")
    assert p.fee == D("0.25")
    assert p.notional == D("99.75")
    assert p.quantity == D("0.00099501")
    assert p.cash_delta == D("-100.00")
    assert p.cash_before == D("10000.00") and p.cash_after == D("9900.00")
    assert p.held_before == D("0") and p.held_after == D("0.00099501")
    assert p.whole_position is False
    assert p.quantity * p.exec_price == D("99.7497525")


def test_b1_doge() -> None:
    p = buy_usd("0.08", "10.00", symbol="DOGE")
    assert p.exec_price == D("0.08020000")
    assert p.fee == D("0.02")
    assert p.notional == D("9.98")
    assert p.quantity == D("124.43890274")
    assert p.cash_delta == D("-10.00")


def test_b1_minimum_fee_applies_btc() -> None:
    p = buy_usd("100000", "1.00")
    assert p.fee == D("0.01")
    assert p.notional == D("0.99")
    assert p.quantity == D("0.00000987")
    assert p.cash_delta == D("-1.00")


def test_b1_minimum_fee_applies_doge() -> None:
    p = buy_usd("0.08", "1.00", symbol="DOGE")
    assert p.fee == D("0.01")
    assert p.quantity == D("12.34413965")
    assert p.cash_delta == D("-1.00")


def test_b1_below_minimum() -> None:
    with refused("below_minimum", "The minimum order is $1.00."):
        buy_usd("100000", "0.99")


def test_b1_quantity_rounds_to_zero() -> None:
    with refused("below_minimum"):
        buy_usd("100000000000", "1.00")


def test_b1_rates_come_from_costs() -> None:
    costs = TradeCosts(spread=D("0.01"), fee_rate=D("0"), min_fee=D("0"), min_order=D("1.00"))
    p = buy_usd("100000", "100.00", costs=costs)
    assert p.exec_price == D("101000.00000000")
    assert p.fee == D("0.00")
    assert p.quantity == D("0.00099009")


def test_min_order_message_uses_configured_value() -> None:
    costs = TradeCosts(spread=D("0"), fee_rate=D("0"), min_fee=D("0"), min_order=D("1234.50"))
    with refused("below_minimum", "The minimum order is $1,234.50."):
        buy_usd("100", "10.00", costs=costs)


# --- B2: buy by quantity ----------------------------------------------------------


def test_b2_btc() -> None:
    p = buy_qty("100000", "0.00015")
    assert p.kind == "quantity" and p.input_value == D("0.00015")
    assert p.exec_price == D("100250.00000000")
    assert p.quantity == D("0.00015")
    assert p.notional == D("15.04")
    assert p.fee == D("0.04")
    assert p.cash_delta == D("-15.08")
    assert p.cash_after == D("9984.92")
    assert p.held_after == D("0.00015")


def test_b2_doge() -> None:
    p = buy_qty("0.08", "125", symbol="DOGE")
    assert p.notional == D("10.02")
    assert p.fee == D("0.03")
    assert p.cash_delta == D("-10.05")


def test_b2_minimum_fee() -> None:
    p = buy_qty("100000", "0.00001")
    assert p.notional == D("1.00")
    assert p.fee == D("0.01")
    assert p.cash_delta == D("-1.01")


def test_b2_below_minimum() -> None:
    with refused("below_minimum"):
        buy_qty("100000", "0.0000099")


def test_b2_zero_quantity_refused() -> None:
    with refused("below_minimum"):
        buy_qty("100000", "0")


# --- S1: sell ---------------------------------------------------------------------


def test_s1_btc_whole_position() -> None:
    p = sell("100000", "0.00099501", "0.00099501")
    assert p.side == "sell"
    assert p.exec_price == D("99750.00000000")
    assert p.notional == D("99.25")
    assert p.fee == D("0.25")
    assert p.cash_delta == D("99.00")
    assert p.cash_after == D("10099.00")
    assert p.held_before == D("0.00099501") and p.held_after == D("0")
    assert p.whole_position is True


def test_s1_doge_partial() -> None:
    p = sell("0.08", "124.43890274", "200", symbol="DOGE")
    assert p.exec_price == D("0.07980000")
    assert p.notional == D("9.93")
    assert p.fee == D("0.02")
    assert p.cash_delta == D("9.91")
    assert p.held_after == D("75.56109726")
    assert p.whole_position is False


def test_s1_sub_cent_whole_position_allowed() -> None:
    p = sell("0.08", "0.05", "0.05", symbol="DOGE")
    assert p.notional == D("0.00")
    assert p.fee == D("0.00")
    assert p.cash_delta == D("0.00")
    assert p.whole_position is True


def test_s1_one_cent_whole_position_fee_capped() -> None:
    p = sell("0.08", "0.1", "0.1", symbol="DOGE")
    assert p.notional == D("0.01")
    assert p.fee == D("0.01")
    assert p.cash_delta == D("0.00")


def test_s1_dust() -> None:
    with refused("below_minimum"):
        sell("100000", "0.00000990", "0.00000997")
    p = sell("100000", "0.00000997", "0.00000997")
    assert p.notional == D("0.99")
    assert p.fee == D("0.01")
    assert p.cash_delta == D("0.98")
    assert p.whole_position is True


def test_s1_oversell_message_uses_db_scale() -> None:
    with refused("insufficient_quantity", "You hold 0.00100000 BTC."):
        sell("100000", "0.0010001", "0.00100000")


def test_s1_nothing_held() -> None:
    with refused("insufficient_quantity", "You hold 0 BTC."):
        sell("100000", "0.001", "0")


def test_s1_zero_or_negative_quantity_refused() -> None:
    with refused("below_minimum"):
        sell("100000", "0", "0")
    with refused("below_minimum"):
        sell("100000", "-0.001", "0.5")


def test_sell_with_usd_is_invalid() -> None:
    with refused("invalid_order"):
        plan_trade(
            symbol="BTC",
            side="sell",
            kind="usd",
            value=D("10.00"),
            mid=D("100000"),
            cash=BIG_CASH,
            held=D("1"),
            costs=COSTS,
        )


# --- refusals: cash, bound, order -------------------------------------------------


def test_insufficient_cash_b1() -> None:
    with refused("insufficient_cash", "You have $99.99; this order needs $100.00."):
        buy_usd("100000", "100.00", cash="99.99")


def test_insufficient_cash_b2_fee_included() -> None:
    with refused("insufficient_cash"):
        buy_qty("100000", "0.00015", cash="15.07")


def test_exact_cash_is_accepted() -> None:
    p = buy_usd("100000", "100.00", cash="100.00")
    assert p.cash_after == D("0.00")
    p = buy_qty("100000", "0.00015", cash="15.08")
    assert p.cash_after == D("0.00")


def test_cash_message_thousands_separator() -> None:
    with refused("insufficient_cash", "You have $1,000.00; this order needs $2,000.00."):
        buy_usd("100000", "2000.00", cash="1000.00")


def test_order_buy_below_minimum_beats_cash() -> None:
    with refused("below_minimum"):
        buy_usd("100000", "0.50", cash="0.10")


def test_order_oversell_beats_minimum() -> None:
    with refused("insufficient_quantity"):
        sell("100000", "0.0000001", "0.00000001")


def test_order_too_large_notional() -> None:
    with refused("order_too_large", "This order is too large."):
        buy_qty("100000", "999999999999", cash="999999999999.99999999")


def test_order_too_large_quantity_alone() -> None:
    with refused("order_too_large"):
        buy_qty("0.00000001", "1000000000000", cash="1")


def test_order_too_large_checked_before_cash() -> None:
    with refused("order_too_large"):
        buy_usd("0.00000001", "999999999999.99", cash="1.00")


def test_order_too_large_buy_usd_quantity() -> None:
    # quantity from a tiny price overflows NUMERIC(20,8) even though the amount is small
    with refused("order_too_large"):
        buy_usd("0.00000001", "100000.00", cash="100000.00")


# --- cost basis -------------------------------------------------------------------


def test_cost_basis_buy_from_zero() -> None:
    assert cost_basis_after(
        side="buy",
        cost_basis=D("0"),
        held_before=D("0"),
        quantity=D("0.00099501"),
        cash_delta=D("-100.00"),
    ) == D("100.00")


def test_cost_basis_buy_adds_cash_spent() -> None:
    assert cost_basis_after(
        side="buy",
        cost_basis=D("100.00"),
        held_before=D("0.00099501"),
        quantity=D("0.00015"),
        cash_delta=D("-15.08"),
    ) == D("115.08")


def test_cost_basis_partial_sell() -> None:
    assert cost_basis_after(
        side="sell",
        cost_basis=D("100.00"),
        held_before=D("0.00099501"),
        quantity=D("0.0005"),
        cash_delta=D("49.00"),
    ) == D("49.75")


def test_cost_basis_full_sell_is_zero() -> None:
    assert cost_basis_after(
        side="sell",
        cost_basis=D("100.00"),
        held_before=D("0.00099501"),
        quantity=D("0.00099501"),
        cash_delta=D("99.00"),
    ) == D("0")


def test_cost_basis_sell_from_zero_basis() -> None:
    assert cost_basis_after(
        side="sell",
        cost_basis=D("0.00"),
        held_before=D("2"),
        quantity=D("1"),
        cash_delta=D("5.00"),
    ) == D("0.00")


# --- seeded invariants ------------------------------------------------------------


def _grid8(rng: random.Random, lo: str, hi: str) -> Decimal:
    lo_i, hi_i = int(D(lo).scaleb(8)), int(D(hi).scaleb(8))
    return D(rng.randint(lo_i, hi_i)).scaleb(-8)


@pytest.mark.parametrize("seed", [4, 2026])
def test_invariants_buy_by_usd(seed: int) -> None:
    rng = random.Random(seed)  # noqa: S311 - deterministic test data
    for _ in range(5000):
        mid = _grid8(rng, "0.0001", "200000")
        amount = D(rng.randint(100, 1_000_000)).scaleb(-2)
        p = plan_trade(
            symbol="X",
            side="buy",
            kind="usd",
            value=amount,
            mid=mid,
            cash=D("1000000.00"),
            held=D("0"),
            costs=COSTS,
        )
        assert p.cash_delta == -amount
        assert p.fee >= D("0.01")
        assert p.quantity == floor8(p.quantity)
        assert p.quantity * p.exec_price <= amount - p.fee
        gap = (amount - p.fee) - p.quantity * p.exec_price
        assert gap < p.exec_price * D("1e-8") + D("1e-16")
        assert p.notional == amount - p.fee
        assert p.cash_after == D("1000000.00") - amount
        assert all(x == q2(x) for x in (p.fee, p.notional, p.cash_delta, p.cash_after))
        assert p.quantity == q8(p.quantity)
        assert not p.quantity.is_nan()


@pytest.mark.parametrize("seed", [4, 2026])
def test_invariants_buy_by_quantity_and_sell(seed: int) -> None:
    rng = random.Random(seed)  # noqa: S311 - deterministic test data
    for _ in range(3000):
        mid = _grid8(rng, "0.0001", "200000")
        qty = _grid8(rng, "0.001", "5000")
        buy = plan_trade(
            symbol="X",
            side="buy",
            kind="quantity",
            value=qty,
            mid=mid,
            cash=D("999999999.00"),
            held=D("0"),
            costs=COSTS,
        )
        assert buy.cash_delta == -(buy.notional + buy.fee)
        assert buy.fee >= D("0.01")
        assert all(x == q2(x) for x in (buy.fee, buy.notional, buy.cash_delta))
        assert buy.held_after == qty

        # selling the whole position always succeeds
        whole = plan_trade(
            symbol="X",
            side="sell",
            kind="quantity",
            value=qty,
            mid=mid,
            cash=D("0"),
            held=qty,
            costs=COSTS,
        )
        assert whole.whole_position is True and whole.held_after == D("0")
        assert whole.cash_delta == whole.notional - whole.fee >= D("0")
        assert whole.fee <= whole.notional
        assert whole.cash_after == whole.cash_delta
        assert not whole.exec_price.is_nan()

        part = (qty / 2).quantize(D("0.00000001"), rounding=ROUND_DOWN)
        try:
            ps = plan_trade(
                symbol="X",
                side="sell",
                kind="quantity",
                value=part,
                mid=mid,
                cash=D("0"),
                held=qty,
                costs=COSTS,
            )
        except TradeRefused as e:
            assert e.code == "below_minimum"
        else:
            assert ps.cash_delta == ps.notional - ps.fee >= D("0")
            assert ps.fee <= ps.notional
            assert ps.held_after == qty - part
