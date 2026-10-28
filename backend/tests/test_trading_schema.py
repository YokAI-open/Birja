"""Postgres itself must refuse impossible money states (backstops behind the row lock)."""

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.price import Coin
from app.models.trade import Holding, Trade
from app.models.user import Account, User
from tests.helpers import unique_email


@pytest_asyncio.fixture
async def ids(engine: AsyncEngine, migrated: None) -> AsyncIterator[dict[str, int]]:
    async with engine.begin() as conn:
        user_id = (
            await conn.execute(insert(User).values(email=unique_email("schema")).returning(User.id))
        ).scalar_one()
        other_id = (
            await conn.execute(insert(User).values(email=unique_email("schema")).returning(User.id))
        ).scalar_one()
        await conn.execute(
            insert(Account).values(user_id=user_id, cash=Decimal("10000.00"), starting_cash=10000)
        )
        coin_id = (await conn.execute(select(Coin.id).where(Coin.symbol == "BTC"))).scalar_one()
    yield {"user": user_id, "other": other_id, "coin": coin_id}
    async with engine.begin() as conn:
        for uid in (user_id, other_id):
            await conn.execute(delete(Trade).where(Trade.user_id == uid))
            await conn.execute(delete(Holding).where(Holding.user_id == uid))
            await conn.execute(delete(Account).where(Account.user_id == uid))
            await conn.execute(delete(User).where(User.id == uid))


def _trade(ids: dict[str, int], **over: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "user_id": ids["user"],
        "coin_id": ids["coin"],
        "side": "buy",
        "input_kind": "usd",
        "input_value": Decimal("100.00"),
        "quantity": Decimal("0.00100000"),
        "mid_price": Decimal("100000.00000000"),
        "price_as_of": datetime(2026, 10, 28, 12, 0, tzinfo=UTC),
        "exec_price": Decimal("100100.00000000"),
        "fee": Decimal("0.10"),
        "cash_delta": Decimal("-100.00"),
        "cash_after": Decimal("9900.00"),
        "idempotency_key": uuid.uuid4(),
    }
    row.update(over)
    return row


def _holding(ids: dict[str, int], **over: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "user_id": ids["user"],
        "coin_id": ids["coin"],
        "quantity": Decimal("1.00000000"),
        "cost_basis": Decimal("100.00"),
    }
    row.update(over)
    return row


async def _refuses(engine: AsyncEngine, stmt: Any, constraint: str) -> None:
    with pytest.raises(IntegrityError) as exc:
        async with engine.begin() as conn:
            await conn.execute(stmt)
    assert constraint in str(exc.value)


async def test_valid_buy_and_sell_rows_insert(engine: AsyncEngine, ids: dict[str, int]) -> None:
    sell = _trade(
        ids,
        side="sell",
        input_kind="quantity",
        input_value=Decimal("0.00000001"),
        quantity=Decimal("0.00000001"),
        fee=Decimal("0.00"),
        cash_delta=Decimal("0.00"),
        cash_after=Decimal("10000.00"),
    )
    async with engine.begin() as conn:
        await conn.execute(insert(Trade).values(_trade(ids)))
        await conn.execute(insert(Trade).values(sell))
        await conn.execute(insert(Holding).values(_holding(ids)))
        count = (await conn.execute(select(Trade.id).where(Trade.user_id == ids["user"]))).all()
    assert len(count) == 2


async def test_holding_default_cost_basis_is_zero(engine: AsyncEngine, ids: dict[str, int]) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            insert(Holding).values(user_id=ids["user"], coin_id=ids["coin"], quantity=Decimal("0"))
        )
        cost = (
            await conn.execute(select(Holding.cost_basis).where(Holding.user_id == ids["user"]))
        ).scalar_one()
    assert cost == Decimal("0")


async def test_negative_cash_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = update(Account).where(Account.user_id == ids["user"]).values(cash=Decimal("-1"))
    await _refuses(engine, stmt, "ck_accounts_cash_non_negative")


async def test_sub_cent_cash_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = update(Account).where(Account.user_id == ids["user"]).values(cash=Decimal("1.005"))
    await _refuses(engine, stmt, "ck_accounts_cash_cents")


async def test_negative_holding_quantity_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Holding).values(
        _holding(ids, quantity=Decimal("-0.00000001"), cost_basis=Decimal("0"))
    )
    await _refuses(engine, stmt, "ck_holdings_quantity_non_negative")


async def test_duplicate_holding_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    async with engine.begin() as conn:
        await conn.execute(insert(Holding).values(_holding(ids)))
    await _refuses(engine, insert(Holding).values(_holding(ids)), "uq_holdings_user_coin")


async def test_empty_holding_with_cost_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Holding).values(_holding(ids, quantity=Decimal("0"), cost_basis=Decimal("1.00")))
    await _refuses(engine, stmt, "ck_holdings_empty_has_no_cost")


async def test_sub_cent_cost_basis_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Holding).values(_holding(ids, cost_basis=Decimal("1.001")))
    await _refuses(engine, stmt, "ck_holdings_cost_basis_cents")


async def test_negative_cost_basis_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Holding).values(_holding(ids, cost_basis=Decimal("-1.00")))
    await _refuses(engine, stmt, "ck_holdings_cost_basis_non_negative")


async def test_duplicate_idempotency_key_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    key = uuid.uuid4()
    async with engine.begin() as conn:
        await conn.execute(insert(Trade).values(_trade(ids, idempotency_key=key)))
    stmt = insert(Trade).values(_trade(ids, idempotency_key=key))
    await _refuses(engine, stmt, "uq_trades_user_idempotency_key")


async def test_same_key_for_other_user_allowed(engine: AsyncEngine, ids: dict[str, int]) -> None:
    key = uuid.uuid4()
    async with engine.begin() as conn:
        await conn.execute(insert(Trade).values(_trade(ids, idempotency_key=key)))
        await conn.execute(
            insert(Trade).values(_trade(ids, idempotency_key=key, user_id=ids["other"]))
        )


async def test_unknown_side_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    # ck_trades_side_known and ck_trades_cash_delta_sign both reject 'hold'
    # (no cash_delta fits an unknown side); Postgres reports the first it checks.
    await _refuses(engine, insert(Trade).values(_trade(ids, side="hold")), "ck_trades_")


async def test_sell_by_usd_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Trade).values(
        _trade(ids, side="sell", input_kind="usd", cash_delta=Decimal("5.00"))
    )
    await _refuses(engine, stmt, "ck_trades_sell_by_quantity")


async def test_buy_with_zero_cash_delta_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Trade).values(_trade(ids, cash_delta=Decimal("0.00")))
    await _refuses(engine, stmt, "ck_trades_cash_delta_sign")


async def test_sell_with_negative_cash_delta_refused(
    engine: AsyncEngine, ids: dict[str, int]
) -> None:
    stmt = insert(Trade).values(
        _trade(ids, side="sell", input_kind="quantity", cash_delta=Decimal("-0.01"))
    )
    await _refuses(engine, stmt, "ck_trades_cash_delta_sign")


async def test_sub_cent_fee_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Trade).values(_trade(ids, fee=Decimal("0.001")))
    await _refuses(engine, stmt, "ck_trades_cents")


async def test_negative_cash_after_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Trade).values(_trade(ids, cash_after=Decimal("-0.01")))
    await _refuses(engine, stmt, "ck_trades_cash_after_non_negative")


async def test_zero_trade_quantity_refused(engine: AsyncEngine, ids: dict[str, int]) -> None:
    stmt = insert(Trade).values(_trade(ids, quantity=Decimal("0")))
    await _refuses(engine, stmt, "ck_trades_quantity_positive")
