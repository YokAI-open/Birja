"""Stock-only money boundaries, without changing crypto policy."""

from dataclasses import FrozenInstanceError
from decimal import Decimal as D
from decimal import localcontext
from typing import cast

import pytest

from app.services.stock_trade_math import (
    MAX_MONEY,
    MAX_PRICE,
    MAX_QUANTITY,
    StockTradePlan,
    buy_max_quantity,
    plan_stock_trade,
    sell_all_quantity,
)
from app.services.trade_math import Side, TradeRefused


def plan(*, side: Side = "buy", **overrides: D) -> StockTradePlan:
    values = dict(
        quantity=D("3"),
        bid=D("9.99"),
        ask=D("10.01"),
        cash=D("100"),
        held=D("4"),
        cost_basis=D("25"),
    )
    values.update(overrides)
    return plan_stock_trade(side=side, **values)


def test_fractional_quantity_cannot_mint_fractional_stock() -> None:
    with pytest.raises(TradeRefused) as error:
        plan_stock_trade(
            side="buy",
            quantity=D("1.5"),
            bid=D("10"),
            ask=D("11"),
            cash=D("100"),
            held=D("0"),
            cost_basis=D("0"),
        )
    assert error.value.code == "invalid_quantity"


@pytest.mark.parametrize(
    "side,price,delta,cash_after,held_after,basis",
    [
        ("buy", "10.01", "-30.03", "69.97", "7", "55.03"),
        ("sell", "9.99", "29.97", "129.97", "1", "6.25"),
    ],
)
def test_exact_execution_and_shared_cash(
    side: Side, price: str, delta: str, cash_after: str, held_after: str, basis: str
) -> None:
    p = plan(side=side)
    assert p.exec_price == D(price)
    assert p.bid == D("9.99") and p.ask == D("10.01")
    assert p.exact_mid == D("10") and p.mid == D("10.00000000")
    assert p.fee == 0 and p.cash_delta == D(delta)
    assert p.cash_before == D("100") and p.cash_after == D(cash_after)
    assert p.held_before == D("4") and p.held_after == D(held_after)
    assert p.cost_basis_before == D("25") and p.cost_basis_after == D(basis)
    with pytest.raises(FrozenInstanceError):
        p.fee = D("1")  # type: ignore[misc]


@pytest.mark.parametrize(
    "bid,ask,exact,metadata",
    [
        ("1", "1.00000001", "1.000000005", "1.00000000"),
        ("1.00000001", "1.00000002", "1.000000015", "1.00000002"),
    ],
)
def test_midpoint_retains_ninth_place(bid: str, ask: str, exact: str, metadata: str) -> None:
    p = plan(bid=D(bid), ask=D(ask))
    assert p.exact_mid == D(exact) and p.mid == D(metadata)


@pytest.mark.parametrize(
    "side,price,quantity,expected",
    [
        ("buy", "33.335", "3", "100.00"),
        ("buy", "0.015", "1", "0.02"),
        ("buy", "0.025", "1", "0.02"),
        ("buy", "0.005", "3", "0.02"),
        ("sell", "0.005", "1", "0.00"),
        ("sell", "0.015", "1", "0.02"),
    ],
)
def test_round_only_final_notional(side: Side, price: str, quantity: str, expected: str) -> None:
    p = plan(side=side, bid=D(price), ask=D(price), quantity=D(quantity))
    assert p.notional == D(expected)
    assert p.fee == 0


@pytest.mark.parametrize("basis,expected", [("0.01", "0.01"), ("0.03", "0.01"), ("0", "0")])
def test_proportional_basis_half_even(basis: str, expected: str) -> None:
    p = plan(side="sell", quantity=D("1"), held=D("2"), cost_basis=D(basis))
    assert p.cost_basis_after == D(expected)


def test_full_sell_resets_basis_and_proceeds_immediately() -> None:
    p = plan(side="sell", quantity=D("4"))
    assert p.whole_position and p.held_after == 0 and p.cost_basis_after == 0
    assert p.cash_after == D("139.96")
    next_buy = plan(cash=p.cash_after, quantity=D("13"))
    assert next_buy.cash_after == D("9.83")


@pytest.mark.parametrize(
    "quantity", ["0", "-1", "1.01", "NaN", "sNaN", "Infinity", "1000000000000"]
)
def test_invalid_quantities(quantity: str) -> None:
    with pytest.raises(TradeRefused) as error:
        plan(quantity=D(quantity))
    assert error.value.code == "invalid_quantity"


@pytest.mark.parametrize(
    "field,value",
    [
        ("bid", "0"),
        ("ask", "0"),
        ("bid", "-1"),
        ("ask", "NaN"),
        ("bid", "sNaN"),
        ("bid", "Infinity"),
        ("ask", "1000000000000"),
        ("bid", "0.000000001"),
        ("ask", "10.010000001"),
        ("bid", "12"),
        ("cash", "-0.01"),
        ("cash", "NaN"),
        ("cash", "1000000000000"),
        ("cash", "100.001"),
        ("held", "-1"),
        ("held", "1.5"),
        ("held", "1000000000000"),
        ("cost_basis", "-1"),
        ("cost_basis", "NaN"),
        ("cost_basis", "1000000000000"),
        ("cost_basis", "0.001"),
        ("held", "0"),
    ],
)
def test_invalid_snapshot_fails_closed(field: str, value: str) -> None:
    with pytest.raises(TradeRefused) as error:
        plan(**{field: D(value)})
    assert error.value.code == "numeric_range"


@pytest.mark.parametrize("quantity", [True, 1, 1.5, "1", None])
def test_non_decimal_input_is_not_coerced(quantity: object) -> None:
    with pytest.raises(TradeRefused) as error:
        plan(quantity=cast(D, quantity))
    assert error.value.code == "invalid_quantity"


@pytest.mark.parametrize(
    "kwargs,side,code",
    [
        ({"cash": D("30.02")}, "buy", "insufficient_cash"),
        ({"held": D("2")}, "sell", "insufficient_holding"),
        ({"quantity": D("1"), "bid": D("0.005"), "ask": D("0.005")}, "buy", "numeric_range"),
        ({"held": MAX_QUANTITY}, "buy", "numeric_range"),
        ({"cost_basis": MAX_MONEY}, "buy", "numeric_range"),
        ({"cash": MAX_MONEY}, "sell", "numeric_range"),
        ({"bid": MAX_PRICE, "ask": MAX_PRICE}, "buy", "numeric_range"),
        ({"quantity": D("1"), "bid": MAX_PRICE, "ask": MAX_PRICE}, "buy", "numeric_range"),
    ],
)
def test_refusals_do_not_mutate_inputs(kwargs: dict[str, D], side: Side, code: str) -> None:
    before = kwargs.copy()
    with pytest.raises(TradeRefused) as error:
        plan(side=side, **kwargs)
    assert error.value.code == code
    assert kwargs == before


def test_boundaries_and_low_ambient_precision() -> None:
    with localcontext() as ctx:
        ctx.prec = 6
        p = plan(
            quantity=MAX_QUANTITY,
            bid=D("1"),
            ask=D("1"),
            cash=MAX_MONEY,
            held=D("0"),
            cost_basis=D("0"),
        )
    assert p.quantity == MAX_QUANTITY and p.notional == MAX_QUANTITY
    assert p.cash_after == D("0.99") and p.cost_basis_after == MAX_QUANTITY
    p = plan(
        quantity=D("1"),
        bid=MAX_MONEY,
        ask=MAX_MONEY,
        cash=MAX_MONEY,
        held=D("0"),
        cost_basis=D("0"),
    )
    assert p.cash_after == 0 and p.cost_basis_after == MAX_MONEY


def test_invalid_side_fails_closed() -> None:
    with pytest.raises(TradeRefused) as error:
        plan(side=cast(Side, "hold"))
    assert error.value.code == "numeric_range"


def test_buy_max_caps_remaining_holding_capacity() -> None:
    quantity = buy_max_quantity(
        bid=D("1"), ask=D("1"), cash=D("100"), held=D("999999999997"), cost_basis=D("1")
    )
    assert quantity == D("2")


@pytest.mark.parametrize(
    "cash,ask,held,basis,expected",
    [
        ("100", "33.335", "0", "0", "2"),
        ("100", "101", "0", "0", "0"),
        ("0", "1", "0", "0", "0"),
        ("1", "0.00000001", "0", "0", "100000000"),
        ("999999999999.99", "0.00000001", "0", "0", "999999999999"),
        ("999999999999.99", "999999999999.99", "0", "0", "1"),
        ("100", "1", "999999999999", "1", "0"),
        ("100", "1", "1", "999999999998.99", "1"),
        ("100", "1", "1", "999999999999.99", "0"),
        ("100", "0.015", "1", "999999999999.97", "1"),
        ("100", "0.005", "1", "999999999999.97", "5"),
        ("100", "0.005", "999999999998", "1", "0"),
    ],
)
def test_buy_max_is_safe_bounded_draft(
    cash: str, ask: str, held: str, basis: str, expected: str
) -> None:
    snapshot = dict(bid=D(ask), ask=D(ask), cash=D(cash), held=D(held), cost_basis=D(basis))
    before = snapshot.copy()
    quantity = buy_max_quantity(**snapshot)
    assert quantity == D(expected)
    assert quantity <= MAX_QUANTITY - D(held)
    assert snapshot == before
    assert format(quantity, "f").isdigit()
    if quantity:
        p = plan_stock_trade(side="buy", quantity=quantity, **snapshot)
        assert p.cash_after >= 0 and p.cost_basis_after <= MAX_MONEY
        assert p.notional > 0


def test_conservative_shortcut_does_not_find_rounding_extra_share() -> None:
    assert (
        buy_max_quantity(
            bid=D("33.335"), ask=D("33.335"), cash=D("100"), held=D("0"), cost_basis=D("0")
        )
        == 2
    )
    assert plan(quantity=D("3"), bid=D("33.335"), ask=D("33.335")).cash_after == 0


@pytest.mark.parametrize(
    "cash,bid,held,basis,expected",
    [
        ("100", "9.99", "4", "25", "4"),
        ("0", "1", "0", "0", "0"),
        ("0", "0.00000001", "999999999999", "0", "999999999999"),
        ("999999999999.99", "1", "1", "1", "0"),
        ("999999999999.98", "0.005", "1", "1", "1"),
        ("0", "999999999999.99", "2", "1", "0"),
    ],
)
def test_sell_all_is_verified_draft(
    cash: str, bid: str, held: str, basis: str, expected: str
) -> None:
    snapshot = dict(bid=D(bid), ask=D(bid), cash=D(cash), held=D(held), cost_basis=D(basis))
    before = snapshot.copy()
    quantity = sell_all_quantity(**snapshot)
    assert quantity == D(expected)
    assert snapshot == before
    if quantity:
        p = plan_stock_trade(side="sell", quantity=quantity, **snapshot)
        assert p.held_after == 0 and p.cost_basis_after == 0
        assert p.cash_after >= p.cash_before


@pytest.mark.parametrize("shortcut", [buy_max_quantity, sell_all_quantity])
@pytest.mark.parametrize(
    "field,value", [("ask", "0"), ("held", "1.5"), ("cash", "NaN"), ("cost_basis", "-1")]
)
def test_shortcut_rejects_unverified_snapshot(shortcut: object, field: str, value: str) -> None:
    from collections.abc import Callable

    snapshot = dict(bid=D("1"), ask=D("1"), cash=D("100"), held=D("2"), cost_basis=D("1"))
    snapshot[field] = D(value)
    with pytest.raises(TradeRefused) as error:
        cast(Callable[..., D], shortcut)(**snapshot)
    assert error.value.code == "numeric_range"


def test_buy_max_uses_bounded_predicate_search(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.services.stock_trade_math as math

    calls = 0
    original = math.plan_stock_trade

    def counted(**kwargs: object) -> StockTradePlan:
        nonlocal calls
        calls += 1
        return original(**kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(math, "plan_stock_trade", counted)
    with localcontext() as ctx:
        ctx.prec = 6
        quantity = buy_max_quantity(
            bid=D("0.00000001"),
            ask=D("0.00000001"),
            cash=MAX_MONEY,
            held=D("1"),
            cost_basis=MAX_MONEY,
        )
    assert quantity == 0  # 0.005 rounds half-even to zero; cannot mint shares.
    assert calls == 0


def test_buy_max_large_search_respects_basis_half_cent_boundary() -> None:
    quantity = buy_max_quantity(
        bid=D("0.00000001"),
        ask=D("0.00000001"),
        cash=MAX_MONEY,
        held=D("1"),
        cost_basis=D("999999999999.98"),
    )
    assert quantity == D("1499999")
    p = plan(
        quantity=quantity,
        bid=D("0.00000001"),
        ask=D("0.00000001"),
        cash=MAX_MONEY,
        held=D("1"),
        cost_basis=D("999999999999.98"),
    )
    assert p.notional == D("0.01") and p.cost_basis_after == MAX_MONEY
