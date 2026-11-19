"""Successor temporal fences use actual instrument gates and closure boundaries."""

from datetime import timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_portfolio_closure_authority import authority, stock_authority
from tests.test_portfolio_closure_stocks import proof_grants

__all__ = ["authority", "stock_authority"]


@pytest_asyncio.fixture
async def closed_case(stock_authority):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio

    app, migrator, admin, books = stock_authority
    await proof_grants(admin)
    user, portfolio = books["roots"][0]
    async with AsyncSession(app) as db:
        await close_portfolio(db, ClosureIntent(user, portfolio, uuid4(), "Strategy"))
    async with admin.connect() as conn:
        boundary = (
            await conn.execute(text("SELECT closed_at FROM accounts WHERE id=:p"), {"p": portfolio})
        ).scalar_one()
    return app, migrator, admin, books, boundary


async def gate(conn, coin):
    await conn.execute(
        text(
            "SELECT pg_advisory_xact_lock(hashtextextended("
            "'birja.stock.instrument:' || CAST(:c AS text),0))"
        ),
        {"c": str(coin)},
    )


async def opening(conn, owner, portfolio, coin, stamp):
    await conn.execute(
        text("""INSERT INTO stock_ownership_movements
        (user_id,portfolio_id,coin_id,sequence,economic_at,recorded_at,quantity,
        before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key)
        SELECT :u,:p,:c,coalesce(max(sequence),0)+1,:at,:at,1,0,1,0,10,0,'opening',:key
        FROM stock_ownership_movements WHERE coin_id=:c"""),
        {"u": owner, "p": portfolio, "c": coin, "at": stamp, "key": "opening:" + str(portfolio)},
    )


@pytest.mark.parametrize("micros", [0, -1])
async def test_equal_or_backward_movement_clock_refuses_even_with_gate(closed_case, micros):
    from tests.test_portfolio_closure_migrations import root

    _, migrator, _, books, boundary = closed_case
    coin = books["stocks"][0]
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        await gate(conn, coin)
        with pytest.raises(DBAPIError, match="stock_terminal_clock"):
            async with conn.begin_nested():
                await opening(
                    conn, owner, portfolio, coin, boundary + timedelta(microseconds=micros)
                )


@pytest.mark.parametrize("micros", [0, -1])
async def test_equal_or_backward_application_clock_refuses(closed_case, micros):
    from tests.test_stock_action_migrations import event

    _, migrator, _, books, boundary = closed_case
    coin = books["stocks"][0]
    async with migrator.begin() as conn:
        await gate(conn, coin)
        eid, _, rid = await event(conn, coin)
        with pytest.raises(DBAPIError, match="stock_terminal_clock"):
            async with conn.begin_nested():
                await conn.execute(
                    text("""INSERT INTO stock_split_applications
                    (coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,
                    processed_at,prior_unit_epoch,new_unit_epoch,sequence_boundary,
                    before_digest,after_digest,owner_digest_version)
                    VALUES (:c,:e,:r,'2','1',:cutoff,:at,0,1,4,:digest,:digest,2)"""),
                    {
                        "c": coin,
                        "e": eid,
                        "r": rid,
                        "cutoff": boundary - timedelta(days=1),
                        "at": boundary + timedelta(microseconds=micros),
                        "digest": "0" * 64,
                    },
                )
