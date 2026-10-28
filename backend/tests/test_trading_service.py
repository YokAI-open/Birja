import dataclasses
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import Settings
from app.models.price import Coin
from app.models.trade import Trade
from app.services import trading
from app.services.trade_math import InputKind, Side, TradeRefused
from app.services.trading import (
    Order,
    PriceChanged,
    execute,
    holding_quantity,
    quote,
)
from tests.helpers import (
    cash_of,
    holding_of,
    put_holding,
    put_price,
    set_cash,
    trade_count,
)

NewUser = Callable[[], Awaitable[int]]
D = Decimal


def _order(
    value: str = "100", side: Side = "buy", kind: InputKind = "usd", symbol: str = "BTC"
) -> Order:
    return Order(symbol=symbol, side=side, kind=kind, value=D(value))


@pytest.fixture
def now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


async def _setup(
    engine: AsyncEngine, new_user: NewUser, now: datetime, mid: str = "100000.00"
) -> tuple[int, datetime]:
    user_id = await new_user()
    as_of = now - timedelta(seconds=10)
    await put_price(engine, "BTC", mid, as_of)
    return user_id, as_of


async def _buy(
    db: AsyncSession,
    user_id: int,
    settings: Settings,
    now: datetime,
    value: str = "100",
    key: uuid.UUID | None = None,
    mid: str = "100000.00",
) -> trading.Fill:
    fill, created = await execute(
        db,
        user_id=user_id,
        order=_order(value),
        expected_mid=D(mid),
        idempotency_key=key or uuid.uuid4(),
        settings=settings,
        now=now,
    )
    assert created
    return fill


# ---- quote -------------------------------------------------------------------------------


async def test_quote_buy_is_read_only(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, as_of = await _setup(engine, new_user, now)
    q = await quote(db, user_id=user_id, order=_order(), settings=settings, now=now)
    assert q.symbol == "BTC"
    assert q.as_of == as_of
    assert q.age_seconds == 10
    assert q.plan.quantity == D("0.00099501")
    assert q.plan.fee == D("0.25")
    assert q.plan.cash_after == D("9900.00")
    assert await trade_count(engine, user_id) == 0
    assert await holding_of(engine, user_id, "BTC") is None
    assert await cash_of(engine, user_id) == D("10000.00")


async def test_quote_uses_held_quantity_for_sells(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    await put_holding(engine, user_id, "BTC", "0.5", "100.00")
    q = await quote(
        db, user_id=user_id, order=_order("0.1", "sell", "quantity"), settings=settings, now=now
    )
    assert q.plan.held_before == D("0.5")
    assert q.plan.held_after == D("0.4")


async def test_quote_symbol_is_case_insensitive(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    q = await quote(db, user_id=user_id, order=_order(symbol="btc"), settings=settings, now=now)
    assert q.symbol == "BTC"


async def test_quote_unknown_coin(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    with pytest.raises(TradeRefused) as exc:
        await quote(db, user_id=user_id, order=_order(symbol="NOPE"), settings=settings, now=now)
    assert exc.value.code == "unknown_coin"


async def test_quote_inactive_coin_is_unknown(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    async with engine.begin() as conn:
        await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=False))
    try:
        with pytest.raises(TradeRefused) as exc:
            await quote(db, user_id=user_id, order=_order(), settings=settings, now=now)
        assert exc.value.code == "unknown_coin"
    finally:
        async with engine.begin() as conn:
            await conn.execute(update(Coin).where(Coin.symbol == "BTC").values(is_active=True))


async def test_quote_without_price_is_stale(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id = await new_user()
    with pytest.raises(TradeRefused) as exc:
        await quote(db, user_id=user_id, order=_order(), settings=settings, now=now)
    assert exc.value.code == "stale_price"
    assert "no price" in exc.value.message


async def test_quote_price_age_boundary(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id = await new_user()
    await put_price(engine, "BTC", "100000.00", now - timedelta(seconds=119))
    q = await quote(db, user_id=user_id, order=_order(), settings=settings, now=now)
    assert q.age_seconds == 119
    await put_price(engine, "BTC", "100000.00", now - timedelta(seconds=120))
    with pytest.raises(TradeRefused) as exc:
        await quote(db, user_id=user_id, order=_order(), settings=settings, now=now)
    assert exc.value.code == "stale_price"
    assert exc.value.message == (
        "The price for BTC is 120s old. Trading is paused until it refreshes."
    )


# ---- execute -----------------------------------------------------------------------------


async def test_execute_buy_writes_everything(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, as_of = await _setup(engine, new_user, now)
    fill = await _buy(db, user_id, settings, now)
    assert fill.cash_after == D("9900.00")
    assert fill.notional == D("99.75")
    assert fill.mid == D("100000.00")
    assert fill.as_of == as_of
    assert fill.symbol == "BTC"
    assert fill.side == "buy"
    assert fill.input_kind == "usd"
    assert fill.quantity == D("0.00099501")
    assert fill.created_at.tzinfo is not None
    assert await cash_of(engine, user_id) == D("9900.00")
    assert await holding_of(engine, user_id, "BTC") == (D("0.00099501"), D("100.00"))
    async with engine.connect() as conn:
        trade = (await conn.execute(select(Trade).where(Trade.user_id == user_id))).one()
    assert trade.id == fill.trade_id
    assert trade.mid_price == D("100000.00")
    assert trade.price_as_of == as_of
    assert trade.exec_price == D("100250.00000000")
    assert trade.fee == D("0.25")
    assert trade.cash_delta == D("-100.00")
    assert trade.cash_after == D("9900.00")
    assert trade.input_kind == "usd"
    assert trade.input_value == D("100.00")


async def test_execute_replay_returns_original_fill(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    key = uuid.uuid4()
    first = await _buy(db, user_id, settings, now, key=key)
    second, created = await execute(
        db,
        user_id=user_id,
        order=_order(),
        expected_mid=D("100000.00"),
        idempotency_key=key,
        settings=settings,
        now=now,
    )
    assert not created
    assert second == first
    assert await trade_count(engine, user_id) == 1
    assert await cash_of(engine, user_id) == D("9900.00")


async def test_replay_ignores_stale_and_changed_price(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    key = uuid.uuid4()
    first = await _buy(db, user_id, settings, now, key=key)
    await put_price(engine, "BTC", "90000.00", now - timedelta(seconds=600))
    again, created = await execute(
        db,
        user_id=user_id,
        order=_order(),
        expected_mid=D("100000.00"),
        idempotency_key=key,
        settings=settings,
        now=now,
    )
    assert (again, created) == (first, False)


async def test_same_key_different_order_conflicts(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    key = uuid.uuid4()
    await _buy(db, user_id, settings, now, key=key)
    with pytest.raises(TradeRefused) as exc:
        await _buy(db, user_id, settings, now, value="200", key=key)
    assert exc.value.code == "idempotency_conflict"
    assert await trade_count(engine, user_id) == 1
    assert await cash_of(engine, user_id) == D("9900.00")


async def test_price_changed_refuses_with_fresh_quote(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    with pytest.raises(PriceChanged) as exc:
        await _buy(db, user_id, settings, now, mid="99999.00")
    assert exc.value.code == "price_changed"
    assert exc.value.message == "The price moved. Review the new total and confirm again."
    assert exc.value.quote.plan.mid == D("100000.00")
    assert exc.value.quote.symbol == "BTC"
    assert await trade_count(engine, user_id) == 0
    assert await cash_of(engine, user_id) == D("10000.00")


async def test_expected_mid_scale_is_irrelevant(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    fill = await _buy(db, user_id, settings, now, mid="100000.0")
    assert fill.mid == D("100000")


async def test_newer_as_of_same_mid_executes_and_records_newer_as_of(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    newer = now - timedelta(seconds=2)
    await put_price(engine, "BTC", "100000.00", newer)
    fill = await _buy(db, user_id, settings, now)
    assert fill.as_of == newer
    async with engine.connect() as conn:
        recorded = (
            await conn.execute(select(Trade.price_as_of).where(Trade.user_id == user_id))
        ).scalar_one()
    assert recorded == newer


async def test_stale_at_execute_refused(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    await put_price(engine, "BTC", "100000.00", now - timedelta(seconds=130))
    with pytest.raises(TradeRefused) as exc:
        await _buy(db, user_id, settings, now)
    assert exc.value.code == "stale_price"
    assert await trade_count(engine, user_id) == 0
    assert await cash_of(engine, user_id) == D("10000.00")


async def test_unknown_coin_at_execute(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    with pytest.raises(TradeRefused) as exc:
        await execute(
            db,
            user_id=user_id,
            order=_order(symbol="NOPE"),
            expected_mid=D("1"),
            idempotency_key=uuid.uuid4(),
            settings=settings,
            now=now,
        )
    assert exc.value.code == "unknown_coin"


@pytest.mark.parametrize(
    ("order", "cash", "code"),
    [
        (_order("0.99"), "10000.00", "below_minimum"),
        (_order("100"), "50.00", "insufficient_cash"),
        (_order("1", "sell", "quantity"), "10000.00", "insufficient_quantity"),
    ],
)
async def test_plan_refusals_write_nothing(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
    order: Order,
    cash: str,
    code: str,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    await set_cash(engine, user_id, cash)
    with pytest.raises(TradeRefused) as exc:
        await execute(
            db,
            user_id=user_id,
            order=order,
            expected_mid=D("100000.00"),
            idempotency_key=uuid.uuid4(),
            settings=settings,
            now=now,
        )
    assert exc.value.code == code
    assert await trade_count(engine, user_id) == 0
    assert await cash_of(engine, user_id) == D(cash)
    assert await holding_of(engine, user_id, "BTC") is None


async def test_whole_position_sell_zeroes_holding_and_keeps_row(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    await _buy(db, user_id, settings, now)
    fill, created = await execute(
        db,
        user_id=user_id,
        order=_order("0.00099501", "sell", "quantity"),
        expected_mid=D("100000.00"),
        idempotency_key=uuid.uuid4(),
        settings=settings,
        now=now,
    )
    assert created
    assert fill.cash_delta == D("99.00")
    assert fill.cash_after == D("9999.00")
    assert fill.notional == D("99.25")
    assert await cash_of(engine, user_id) == D("9999.00")
    assert await holding_of(engine, user_id, "BTC") == (D("0E-8"), D("0"))


async def test_partial_sell_and_second_buy_adjust_cost_basis(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    await _buy(db, user_id, settings, now)
    await execute(
        db,
        user_id=user_id,
        order=_order("0.0005", "sell", "quantity"),
        expected_mid=D("100000.00"),
        idempotency_key=uuid.uuid4(),
        settings=settings,
        now=now,
    )
    assert await holding_of(engine, user_id, "BTC") == (D("0.00049501"), D("49.75"))
    await _buy(db, user_id, settings, now, value="50")
    held, basis = (await holding_of(engine, user_id, "BTC")) or (D(0), D(0))
    assert basis == D("99.75")
    assert held > D("0.00049501")


async def test_sub_cent_whole_position_sell(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id = await new_user()
    await put_price(engine, "DOGE", "0.08", now - timedelta(seconds=5))
    await put_holding(engine, user_id, "DOGE", "0.05", "0.01")
    fill, created = await execute(
        db,
        user_id=user_id,
        order=_order("0.05", "sell", "quantity", "DOGE"),
        expected_mid=D("0.08"),
        idempotency_key=uuid.uuid4(),
        settings=settings,
        now=now,
    )
    assert created
    assert fill.fee == D("0.00")
    assert fill.cash_delta == D("0.00")
    assert fill.quantity == D("0.05")
    assert await cash_of(engine, user_id) == D("10000.00")
    assert await holding_of(engine, user_id, "DOGE") == (D("0E-8"), D("0"))


# ---- idempotency backstop and error handling ---------------------------------------------


def _blind_first_lookup(monkeypatch: pytest.MonkeyPatch, always: bool = False) -> None:
    real = trading._find_trade
    calls = {"n": 0}

    async def fake(*args: Any, **kwargs: Any) -> Any:
        calls["n"] += 1
        if always or calls["n"] == 1:
            return None
        return await real(*args, **kwargs)

    monkeypatch.setattr(trading, "_find_trade", fake)


async def test_unique_race_backstop_returns_original_fill(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    key = uuid.uuid4()
    first = await _buy(db, user_id, settings, now, key=key)
    _blind_first_lookup(monkeypatch)
    again, created = await execute(
        db,
        user_id=user_id,
        order=_order(),
        expected_mid=D("100000.00"),
        idempotency_key=key,
        settings=settings,
        now=now,
    )
    assert (again, created) == (first, False)
    assert await trade_count(engine, user_id) == 1
    assert await cash_of(engine, user_id) == D("9900.00")


async def test_unique_race_backstop_conflicts_on_different_order(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    key = uuid.uuid4()
    await _buy(db, user_id, settings, now, key=key)
    _blind_first_lookup(monkeypatch)
    with pytest.raises(TradeRefused) as exc:
        await _buy(db, user_id, settings, now, value="150", key=key)
    assert exc.value.code == "idempotency_conflict"
    assert await trade_count(engine, user_id) == 1
    assert await cash_of(engine, user_id) == D("9900.00")


async def test_unique_violation_without_row_is_reraised(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    key = uuid.uuid4()
    await _buy(db, user_id, settings, now, key=key)
    _blind_first_lookup(monkeypatch, always=True)
    with pytest.raises(IntegrityError) as exc:
        await _buy(db, user_id, settings, now, key=key)
    assert "uq_trades_user_idempotency_key" in str(exc.value.orig)
    assert await trade_count(engine, user_id) == 1
    assert await cash_of(engine, user_id) == D("9900.00")


async def test_other_integrity_errors_propagate(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    real = trading.plan_trade

    def broken(**kwargs: Any) -> Any:
        return dataclasses.replace(real(**kwargs), cash_after=D("-1.00"))

    monkeypatch.setattr(trading, "plan_trade", broken)
    with pytest.raises(IntegrityError):
        await _buy(db, user_id, settings, now)
    assert await trade_count(engine, user_id) == 0
    assert await cash_of(engine, user_id) == D("10000.00")
    assert await holding_of(engine, user_id, "BTC") is None


# ---- holding_quantity --------------------------------------------------------------------


async def test_holding_quantity(
    db: AsyncSession,
    engine: AsyncEngine,
    settings: Settings,
    clean_prices: None,
    new_user: NewUser,
    now: datetime,
) -> None:
    user_id, _ = await _setup(engine, new_user, now)
    assert await holding_quantity(db, user_id=user_id, symbol="btc") == ("BTC", D("0"))
    await _buy(db, user_id, settings, now)
    assert await holding_quantity(db, user_id=user_id, symbol="BTC") == ("BTC", D("0.00099501"))
    with pytest.raises(TradeRefused) as exc:
        await holding_quantity(db, user_id=user_id, symbol="nope")
    assert exc.value.code == "unknown_coin"
