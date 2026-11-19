"""Historical dividend authority must not permanently exclude never-owners."""

from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import event, func, select, text, update

from app.models.corporate_action import StockActionRevision, StockDividendEntitlement
from app.models.user import Account, User
from app.services import corporate_actions as actions
from app.services import stock_trading
from app.services.portfolios import OwnedActivePortfolio
from app.services.trade_math import TradeRefused
from tests.dividend_fixtures import (
    dividend_case,
    ownership,
    process,
    scheduler,
    status_case,
    stock_trade_case,
)
from tests.helpers import sign_in
from tests.portfolio_fixtures import delete_owned_test_root
from tests.stock_action_fixtures import synthetic_opening
from tests.test_portfolio_stock_trading import order, snapshot

__all__ = ["dividend_case", "ownership", "status_case", "stock_trade_case"]


@pytest_asyncio.fixture
async def paid_historical_dividend(dividend_case):
    factory, original = dividend_case
    async with factory.begin() as db:
        cutoff = await db.scalar(
            select(StockDividendEntitlement.cutoff).where(
                StockDividendEntitlement.id == original["entitlement_id"]
            )
        )
        await db.execute(
            update(StockActionRevision)
            .where(StockActionRevision.id == original["revision_id"])
            .values(
                verified_cutoff=cutoff,
                normalized_terms=StockActionRevision.normalized_terms.op("||")(
                    {"coin_id": original["coin_id"], "process_date": str(cutoff.date())}
                ),
            )
        )
    # The actual scheduler producer/payment service establishes an independent
    # historical owner's eligible snapshot and once-only cash credit first.
    async with scheduler(factory) as db:
        derived = await actions.derive_dividend_entitlements(db, original["event_id"])
        await db.commit()
    assert len(derived) == 1 and derived[0].eligible_quantity == 2
    current = {
        **original,
        "entitlement_id": derived[0].id,
        "entitlement_fingerprint": derived[0].fingerprint,
    }
    result = await process(factory, current)
    async with factory() as db:
        assert (
            await db.scalar(select(Account.cash).where(Account.id == original["portfolio_id"]))
            == 101
        )
        assert await db.scalar(select(func.count()).select_from(StockDividendEntitlement)) >= 1
    yield factory, current, cutoff, result


async def restricted_buy(factory, root, settings, body):
    async with factory() as db:
        await db.execute(text("SET LOCAL ROLE birja_app"))
        return await stock_trading.execute(db, portfolio=root, order=body, settings=settings)


@contextmanager
def final_authority_calls(factory):
    calls = []

    def observe(_connection, _cursor, statement, _parameters, _context, _many):
        if "SELECT public.assert_stock_execution_current(" in statement:
            calls.append("final_authority")

    engine = factory.kw["bind"].sync_engine
    event.listen(engine, "before_cursor_execute", observe)
    try:
        yield calls
    finally:
        event.remove(engine, "before_cursor_execute", observe)


@pytest.mark.parametrize(
    "kind", ["existing-other-owner", "existing-sibling", "created-after-cutoff"]
)
async def test_never_owner_first_buy_after_paid_dividend_is_available_and_replayable(
    paid_historical_dividend, new_user, settings, kind
):
    factory, ids, cutoff, _ = paid_historical_dividend
    uid = ids["user_id"] if kind == "existing-sibling" else await new_user()
    async with factory.begin() as db:
        if kind == "existing-sibling":
            target = Account(
                user_id=uid,
                name="Never owned the dividend stock",
                name_key="never owned the dividend stock",
                cash=Decimal(1000),
                starting_cash=Decimal(1000),
                created_at=cutoff - timedelta(days=1),
            )
            db.add(target)
            await db.flush()
        else:
            target = (await db.scalars(select(Account).where(Account.user_id == uid))).one()
            target.cash = Decimal(1000)
            if kind == "existing-other-owner":
                target.created_at = cutoff - timedelta(days=1)
            else:
                assert target.created_at > cutoff
        root = OwnedActivePortfolio(target.id, uid)
    # Repeating the genuine worker producer cannot discover a root that never
    # owned this instrument. The first fill must not depend on a fabricated
    # zero entitlement/payment being inserted merely to unlock trading.
    async with scheduler(factory) as db:
        assert len(await actions.derive_dividend_entitlements(db, ids["event_id"])) == 1
        await db.commit()
    async with factory() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(StockDividendEntitlement)
                .where(StockDividendEntitlement.portfolio_id == root.portfolio_id)
            )
            == 0
        )
    original_owner = OwnedActivePortfolio(ids["portfolio_id"], ids["user_id"])
    owner_before = await snapshot(factory, original_owner)
    body = order(quantity="1")
    receipt, created = await restricted_buy(factory, root, settings, body)
    assert created and receipt.cash_after == 898 and receipt.held_after == 1
    after = await snapshot(factory, root)
    replay, created = await restricted_buy(factory, root, settings, body)
    assert not created and replay == receipt
    assert await snapshot(factory, root) == after
    later, created = await restricted_buy(factory, root, settings, order(quantity="1"))
    assert created and later.cash_after == 796 and later.held_after == 2
    after_later = await snapshot(factory, root)
    replay, created = await restricted_buy(factory, root, settings, body)
    assert not created and replay == receipt
    assert await snapshot(factory, root) == after_later
    assert await snapshot(factory, original_owner) == owner_before
    async with factory() as db:
        assert (
            await db.scalar(
                text("SELECT count(*) FROM stock_dividend_payments WHERE portfolio_id=:p"),
                {"p": root.portfolio_id},
            )
            == 0
        )


async def test_historical_owner_with_unresolved_entitlement_remains_refused(
    paid_historical_dividend, new_user, settings
):
    factory, ids, cutoff, _ = paid_historical_dividend
    uid = await new_user()
    async with factory.begin() as db:
        target = (await db.scalars(select(Account).where(Account.user_id == uid))).one()
        target.cash = Decimal(1000)
        target.created_at = cutoff - timedelta(days=2)
        root = OwnedActivePortfolio(target.id, uid)
        await synthetic_opening(
            db,
            ids["coin_id"],
            uid,
            cutoff - timedelta(hours=1),
            quantity=Decimal(1),
            basis=Decimal(10),
            sequence=2,
            portfolio_id=root.portfolio_id,
        )
    before = await snapshot(factory, root)
    with final_authority_calls(factory) as calls, pytest.raises(TradeRefused) as refused:
        await restricted_buy(factory, root, settings, order(quantity="1"))
    assert calls == ["final_authority"]
    assert refused.value.code == "quote_unavailable"
    assert await snapshot(factory, root) == before


async def test_incomplete_historical_coverage_does_not_exempt_never_owner(
    paid_historical_dividend, new_user, settings
):
    from app.models.corporate_action import StockActionState

    factory, ids, cutoff, _ = paid_historical_dividend
    uid = await new_user()
    async with factory.begin() as db:
        target = (await db.scalars(select(Account).where(Account.user_id == uid))).one()
        root = OwnedActivePortfolio(target.id, uid)
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == ids["coin_id"])
            .values(complete_from=cutoff + timedelta(seconds=1))
        )
    before = await snapshot(factory, root)
    with final_authority_calls(factory) as calls, pytest.raises(TradeRefused) as refused:
        await restricted_buy(factory, root, settings, order(quantity="1"))
    assert calls == ["final_authority"]
    assert refused.value.code == "quote_unavailable"
    assert await snapshot(factory, root) == before


async def test_closed_never_owner_remains_unavailable(
    paid_historical_dividend, new_user, settings, auth_client, outbox
):
    factory, _, _, _ = paid_historical_dividend
    uid = await new_user()
    async with factory.begin() as db:
        target = (await db.scalars(select(Account).where(Account.user_id == uid))).one()
        root = OwnedActivePortfolio(target.id, uid)
        email = await db.scalar(select(User.email).where(User.id == uid))
    await sign_in(auth_client, outbox, email)
    await delete_owned_test_root(auth_client, factory, root.portfolio_id)
    before = await snapshot(factory, root)
    with pytest.raises(HTTPException) as unavailable:
        await restricted_buy(factory, root, settings, order(quantity="1"))
    assert unavailable.value.status_code == 404
    assert unavailable.value.detail == {"code": "portfolio_unavailable"}
    assert await snapshot(factory, root) == before
