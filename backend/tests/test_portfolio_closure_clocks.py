"""Successor temporal fences use actual instrument gates and closure boundaries."""

import asyncio
from datetime import timedelta
from decimal import Decimal
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


async def test_temporal_guard_requires_already_held_gate(closed_case):
    from tests.test_portfolio_closure_migrations import root

    _, migrator, _, books, _ = closed_case
    async with migrator.begin() as conn:
        owner, portfolio = await root(conn)
        stamp = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
        with pytest.raises(DBAPIError, match="stock_gate_required"):
            async with conn.begin_nested():
                await opening(conn, owner, portfolio, books["stocks"][0], stamp)


@pytest.mark.parametrize("micros", [0, -1])
async def test_service_movement_clock_refuses_then_normal_sibling_fill_resumes(
    closed_case, monkeypatch, micros
):
    from app.services import stock_ownership as ownership
    from tests.stock_action_fixtures import synthetic_fill

    _, migrator, _, books, boundary = closed_case
    coin = books["stocks"][0]
    owner, portfolio = books["roots"][1]
    async with migrator.begin() as conn:
        await conn.execute(
            text("""UPDATE stock_action_state SET health='current',
            valid_until=clock_timestamp()+interval '1 hour' WHERE coin_id=:c"""),
            {"c": coin},
        )
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db:

            async def frozen(_db):
                return boundary + timedelta(microseconds=micros)

            with monkeypatch.context() as patch:
                patch.setattr(ownership, "_clock", frozen)
                with pytest.raises(ownership.OwnershipHeld, match="invalid_closure"):
                    async with db.begin_nested():
                        trade = await synthetic_fill(db, coin, owner, portfolio_id=portfolio)
                        await ownership.append_stock_movement(
                            db,
                            ownership.StockMovementInput(
                                owner,
                                coin,
                                Decimal(2),
                                Decimal(50),
                                "fill:" + str(trade.id),
                                trade_id=trade.id,
                                portfolio_id=portfolio,
                            ),
                        )
            trade = await synthetic_fill(db, coin, owner, portfolio_id=portfolio)
            movement = await ownership.append_stock_movement(
                db,
                ownership.StockMovementInput(
                    owner,
                    coin,
                    Decimal(2),
                    Decimal(50),
                    "fill:" + str(trade.id),
                    trade_id=trade.id,
                    portfolio_id=portfolio,
                ),
            )
            assert movement.recorded_at > boundary
            assert movement.after_quantity == 5 and movement.after_basis == 50
            await ownership.assert_ownership_consistent(db, coin)
            await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            await db.commit()


@pytest.mark.parametrize("micros", [0, -1])
async def test_service_split_clock_refuses_then_pending_sibling_assembly_resumes(
    closed_case, monkeypatch, micros
):
    from dataclasses import asdict, replace

    from sqlalchemy import select, update

    from app.models.corporate_action import StockActionState, StockSplitApplication
    from app.models.price import Coin
    from app.models.stock import StockDataAdmission, StockInstrument
    from app.models.trade import Holding
    from app.services import corporate_actions as actions
    from app.services.stock_ownership import OwnershipHeld, assert_ownership_consistent
    from tests.test_corporate_action_rules import dividend
    from tests.test_corporate_actions import batch, split_action
    from tests.test_stock_admission import action_admitted

    _, migrator, _, books, boundary = closed_case
    coin = books["stocks"][0]
    async with (
        migrator.begin() as conn,
        AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db,
    ):
        now = (await db.execute(text("SELECT clock_timestamp()"))).scalar_one()
        evidence = replace(
            action_admitted(),
            generation=1,
            reviewed_at=now - timedelta(hours=1),
            valid_from=now - timedelta(hours=2),
            valid_until=now + timedelta(hours=2),
        )
        db.add(StockDataAdmission(**asdict(evidence)))
        await db.execute(
            update(StockInstrument)
            .where(StockInstrument.coin_id == coin)
            .values(provider_asset_id="fixture-asset", provider_verified_at=now)
        )
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == coin)
            .values(health="current", valid_until=now + timedelta(hours=1))
        )
        symbol = (await db.execute(select(Coin.symbol).where(Coin.id == coin))).scalar_one()
        cutoff = boundary - timedelta(hours=1)
        action = split_action(
            dividend(
                coin_id=coin,
                symbol=symbol,
                provider_event_id=str(uuid4()),
                observed_at=now,
                process_date=cutoff.date(),
            ),
            cutoff,
            new_rate=Decimal(2),
            old_rate=Decimal(1),
        )
        await actions.persist_action_batch(db, batch(action), evidence)
        await db.flush()
        original_authority, original_clock = actions._authority, actions._clock
        armed = False

        async def arm(db, expected=None, **kwargs):
            nonlocal armed
            result = await original_authority(db, expected, **kwargs)
            if expected is not None:
                armed = True
            return result

        async def freeze_only_processed_at(db):
            nonlocal armed
            if armed:
                armed = False
                return boundary + timedelta(microseconds=micros)
            return await original_clock(db)

        with monkeypatch.context() as patch:
            patch.setattr(actions, "_authority", arm)
            patch.setattr(actions, "_clock", freeze_only_processed_at)
            with pytest.raises(OwnershipHeld, match="invalid_closure"):
                async with db.begin_nested():
                    await actions.apply_due_actions(db, coin)
        assert (await db.execute(select(StockSplitApplication.id))).all() == []
        result = await actions.apply_due_actions(db, coin)
        assert len(result) == 1
        state, _ = await assert_ownership_consistent(db, coin)
        assert state.unit_epoch == 1
        holdings = dict(
            (
                await db.execute(
                    select(Holding.portfolio_id, Holding.quantity).where(Holding.coin_id == coin)
                )
            ).all()
        )
        assert holdings[books["roots"][0][1]] == 0
        assert holdings[books["roots"][1][1]] == 6
        assert holdings[books["roots"][2][1]] == 2
        assert await actions.apply_due_actions(db, coin) == result
        await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        await db.commit()


async def test_queued_closer_samples_boundary_after_actual_instrument_wait(stock_authority):
    from app.services.portfolio_closure import ClosureIntent, close_portfolio
    from tests.test_portfolio_closure_migrations import root

    app, migrator, admin, books = stock_authority
    await proof_grants(admin)
    user, portfolio = books["roots"][0]
    coin = books["stocks"][0]
    async with migrator.connect() as writer, AsyncSession(app) as db:
        await gate(writer, coin)
        pid = (await db.execute(text("SELECT pg_backend_pid()"))).scalar_one()
        task = asyncio.create_task(
            close_portfolio(db, ClosureIntent(user, portfolio, uuid4(), "Strategy"))
        )
        try:
            async with asyncio.timeout(1.5):
                while True:
                    async with admin.connect() as observer:
                        waited = (
                            await observer.execute(
                                text(
                                    "SELECT wait_event_type='Lock' AND "
                                    "cardinality(pg_blocking_pids(pid))>0 "
                                    "FROM pg_stat_activity WHERE pid=:p"
                                ),
                                {"p": pid},
                            )
                        ).scalar_one()
                    if waited:
                        break
                    await asyncio.sleep(0)
            # A different active owner writes while closure waits on its gate.
            # This declared synthetic opening tests global ordering, not trading admission.
            sibling_owner, sibling = await root(writer)
            stamp = (await writer.execute(text("SELECT clock_timestamp()"))).scalar_one()
            await opening(writer, sibling_owner, sibling, coin, stamp)
            await writer.execute(
                text("""INSERT INTO holdings
                (user_id,portfolio_id,coin_id,quantity,cost_basis)
                VALUES (:u,:p,:c,1,10)"""),
                {"u": sibling_owner, "p": sibling, "c": coin},
            )
            await writer.commit()
            assert (await task).outcome == "closed"
            async with admin.connect() as conn:
                assert (
                    await conn.execute(
                        text("""SELECT closing_sequence,closed_at>:stamp
                    FROM portfolio_stock_closures WHERE portfolio_id=:p AND coin_id=:c"""),
                        {"p": portfolio, "c": coin, "stamp": stamp},
                    )
                ).one() == (5, True)
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            await writer.rollback()
            await db.rollback()
