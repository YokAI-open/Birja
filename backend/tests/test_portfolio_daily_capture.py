"""Durable valuations against the isolated PostgreSQL runtime roles."""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import SchedulerSettings
from app.services.portfolio import load_portfolio_snapshots
from app.services.portfolio_daily_values import capture_portfolio_daily_value
from app.tasks import portfolio_daily_values as daily_task
from app.tasks.scheduler import CycleResult
from tests.helpers import coin_id, put_price
from tests.portfolio_fixtures import close_empty_test_root, seed_portfolio_world
from tests.stock_action_fixtures import synthetic_owned_portfolio
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case
from tests.test_migrations import install_current_test_grants, run_test_migration
from tests.test_portfolio_daily_schema import authorize_dev, run_migration, scratch_database
from tests.test_stock_catalog_valuation import (
    catalog_book,
    finance_0025,
    finance_0026,
    financial_market,
)
from tests.test_stock_trading_service import trade_order

__all__ = [
    "scratch_database",
    "catalog_book",
    "finance_0025",
    "finance_0026",
    "financial_market",
    "ownership",
    "status_case",
    "stock_trade_case",
]

AT = datetime(2026, 11, 26, 22, 30, tzinfo=UTC)


@pytest_asyncio.fixture
async def capture_world(scratch_database):
    admin, migrator = scratch_database
    await run_migration(migrator, "0028")
    await authorize_dev(admin, "0028")
    async with migrator.begin() as conn:
        world = await seed_portfolio_world(conn)
    return async_sessionmaker(admin), migrator, world


async def record(factory, owner, root, settings, *, clock=lambda: AT):
    async with factory.begin() as db:
        await db.execute(text("SET LOCAL ROLE birja_scheduler"))
        return await capture_portfolio_daily_value(
            db,
            owner_id=owner,
            portfolio_id=root,
            expected_day=AT.date(),
            settings=settings,
            clock=clock,
        )


async def readings(factory):
    async with factory.begin() as db:
        await db.execute(text("SET LOCAL ROLE birja_app"))
        return (
            await db.execute(
                text("""
                SELECT portfolio_id, captured_at, starting_cash, total_value, valuation_complete
                FROM portfolio_daily_values ORDER BY portfolio_id, utc_day
                """)
            )
        ).all()


async def test_exact_scheduler_parity_baseline_and_incomplete(capture_world, settings):
    factory, migrator, world = capture_world
    async with migrator.begin() as conn:
        new_root = await conn.scalar(
            text("""
                INSERT INTO accounts(user_id,name,name_key,cash,starting_cash)
                VALUES (:owner,'Legacy value','legacy value',12.35, 7654.32109876)
                RETURNING id
            """),
            {"owner": world.owner},
        )
        await conn.execute(
            text("""
                INSERT INTO prices(coin_id,mid,as_of,source)
                VALUES (:coin,23567.89123456,:at,'fake')
            """),
            {"coin": world.crypto, "at": AT - timedelta(minutes=6)},
        )
    async with factory.begin() as db:
        await db.execute(text("SET LOCAL ROLE birja_app"))
        expected = await load_portfolio_snapshots(
            db, owner_id=world.owner, settings=settings, now=AT
        )
    for snapshot in expected:
        assert await record(factory, world.owner, int(snapshot.portfolio_id), settings)
    assert [row.total_value for row in await readings(factory)] == [p.total_value for p in expected]
    assert (await readings(factory))[-1] == (
        new_root,
        AT,
        Decimal("7654.32109876"),
        Decimal("12.35"),
        True,
    )
    assert not await record(factory, world.foreign_owner, new_root, settings)
    assert not await record(factory, world.owner, world.closed, settings)
    async with migrator.begin() as conn:
        await conn.execute(text("DELETE FROM prices WHERE coin_id=:coin"), {"coin": world.crypto})
    assert not await record(factory, world.owner, world.first, settings)
    assert (await readings(factory))[0].total_value == Decimal("3591.35")


async def test_missing_quote_observation_cannot_be_replaced(capture_world, settings):
    factory, migrator, world = capture_world
    assert await record(factory, world.owner, world.first, settings)
    async with migrator.begin() as conn:
        await conn.execute(
            text("INSERT INTO prices(coin_id,mid,as_of,source) VALUES (:coin,200,:at,'fake')"),
            {"coin": world.crypto, "at": AT},
        )
    assert not await record(factory, world.owner, world.first, settings)
    assert await readings(factory) == [(world.first, AT, Decimal("10000"), None, False)]


async def test_featured_and_crypto_daily_value_matches_current_statement(
    stock_trade_case, engine, clean_prices, settings, monkeypatch
):
    from app.services import stock_sessions
    from app.services.stock_trading import execute

    factory, coin, uid, now = stock_trade_case
    deadline = now + timedelta(hours=22, minutes=30)
    async with factory.begin() as db:
        await db.execute(
            text("""
                UPDATE stock_data_admissions SET valid_until=:until,
                 calendar=CASE WHEN product='calendar' THEN calendar ||
                  jsonb_build_object('review_valid_until', CAST(:until_text AS text))
                  ELSE calendar END,
                 quota=CASE WHEN product='quotes' THEN quota ||
                  jsonb_build_object('retention_seconds', 86400)
                  ELSE quota END
            """),
            {"until": deadline, "until_text": deadline.isoformat()},
        )
        await db.execute(
            text("UPDATE stock_action_state SET valid_until=:until WHERE coin_id=:coin"),
            {"until": deadline, "coin": coin},
        )
    async with factory() as db:
        portfolio = await synthetic_owned_portfolio(db, uid)
        fill, _ = await execute(db, portfolio=portfolio, order=trade_order(), settings=settings)
    at = max(now.replace(hour=22, minute=0, second=0, microsecond=0), fill.executed_at)
    close = fill.executed_at
    create_calendar = stock_sessions.calendars.get_calendar

    def closed_calendar(*args, **kwargs):
        calendar = create_calendar(*args, **kwargs)
        close_session = calendar.session_close

        def session_close(day):
            stamp = close_session(day)
            return type(stamp)(close) if str(day) == str(now.date()) else stamp

        calendar.session_close = session_close
        return calendar

    stock_sessions._calendar_bounds.cache_clear()
    monkeypatch.setattr(stock_sessions.calendars, "get_calendar", closed_calendar)
    crypto = await coin_id(engine, "BTC")
    await put_price(engine, "BTC", "12345.67890123", at)
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE stock_sessions SET closes_at=:close WHERE session_date=:date"),
            {"close": close, "date": now.date()},
        )
        await db.execute(
            text("""
                UPDATE stock_data_admissions SET scope=scope || '{"feed":"nasdaq-rss"}'
                WHERE product='status'
            """)
        )
        await db.execute(
            text("""
                INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis)
                VALUES (:root,:uid,:coin,0.1,100)
            """),
            {"root": portfolio.portfolio_id, "uid": uid, "coin": crypto},
        )
    try:
        async with factory.begin() as db:
            await db.execute(text("SET LOCAL ROLE birja_app"))
            (current,) = await load_portfolio_snapshots(
                db, owner_id=uid, portfolio_ids=[portfolio.portfolio_id], settings=settings, now=at
            )
        assert current.total_value == Decimal("11232.57")
        assert (
            next(h.stock_mark for h in current.holdings if h.asset_class == "stock").mark_mode
            == "closed"
        )
        async with factory.begin() as db:
            await db.execute(text("SET LOCAL ROLE birja_scheduler"))
            assert await capture_portfolio_daily_value(
                db,
                owner_id=uid,
                portfolio_id=portfolio.portfolio_id,
                expected_day=at.date(),
                settings=SchedulerSettings(),
                clock=lambda: at,
            )
        result = next(
            row for row in await readings(factory) if row.portfolio_id == portfolio.portfolio_id
        )
        assert result.total_value == current.total_value and result.valuation_complete
    finally:
        async with factory.begin() as db:
            await db.execute(
                text("DELETE FROM portfolio_daily_values WHERE portfolio_id=:root"),
                {"root": portfolio.portfolio_id},
            )


@pytest.mark.parametrize(
    "scope", ["permitted", "derived_restricted", "backup_restricted", "revoked"]
)
async def test_catalog_daily_aggregate_respects_current_mark_and_durable_rights(
    catalog_book, engine, scope
):
    from app.models.corporate_action import StockActionState
    from app.models.stock_catalog import StockCatalogAdmission
    from app.models.stock_catalog_finance import (
        StockCatalogActionCoverage,
        StockCatalogFinancialQuote,
    )

    market, settings = catalog_book
    await asyncio.to_thread(run_test_migration, "0028")
    await install_current_test_grants()
    bound = market.instruments[0]
    at = market.now.replace(hour=22, minute=0)
    deadline = at + timedelta(hours=1)
    first, owner = market.world.first, market.world.owner
    # Leases are synthetic and span the daily observation after the real session
    # closes. The current mark still comes through the recorded authority checks.
    async with market.factory.begin() as db:
        quote = await db.get(StockCatalogFinancialQuote, bound.coin_id)
        mark = await db.get(StockCatalogAdmission, quote.mark_admission_id)
        quote.valid_until = mark.valid_until = deadline
        if scope == "derived_restricted":
            mark.scope = {**mark.scope, "durable_derived_use": False}
        elif scope == "backup_restricted":
            mark.scope = {**mark.scope, "durable_derived_backup": False}
        elif scope == "revoked":
            mark.revoked_at = at
        state = await db.get(StockActionState, bound.coin_id)
        actions = await db.get(StockCatalogAdmission, state.admission_generation)
        state.valid_until = actions.valid_until = deadline
        await db.execute(
            update(StockCatalogActionCoverage)
            .where(StockCatalogActionCoverage.coin_id == bound.coin_id)
            .values(valid_until=deadline)
        )
    factory = async_sessionmaker(engine)
    async with factory.begin() as db:
        await db.execute(text("SET LOCAL ROLE birja_app"))
        (current,) = await load_portfolio_snapshots(
            db, owner_id=owner, portfolio_ids=[first], settings=settings, now=at
        )
    assert current.total_value == (None if scope == "revoked" else Decimal("1448.56"))
    async with factory.begin() as db:
        await db.execute(text("SET LOCAL ROLE birja_scheduler"))
        assert await capture_portfolio_daily_value(
            db,
            owner_id=owner,
            portfolio_id=first,
            expected_day=at.date(),
            settings=market.settings,
            clock=lambda: at,
        )
    rows = await readings(factory)
    result = next(row for row in rows if row.portfolio_id == first)
    assert result.total_value == (current.total_value if scope == "permitted" else None)
    assert result.valuation_complete is (scope == "permitted")


@pytest.mark.parametrize("late_read", [0, 3, 4])
async def test_capture_window_rechecks_after_authority_and_before_append(
    capture_world, settings, late_read
):
    factory, _, world = capture_world
    next_day = (AT + timedelta(days=1)).replace(hour=0, minute=0)
    inputs = iter([AT] * late_read + [next_day])
    assert not await record(factory, world.owner, world.first, settings, clock=lambda: next(inputs))
    assert await readings(factory) == []


@pytest.mark.parametrize("close_first", [True, False])
async def test_capture_and_terminal_close_serialize(capture_world, settings, close_first):
    factory, migrator, world = capture_world
    owner, root = world.foreign_owner, world.foreign
    waiter_pid = asyncio.Future()

    async def capture(db):
        await db.execute(text("SET LOCAL ROLE birja_scheduler"))
        return await capture_portfolio_daily_value(
            db,
            owner_id=owner,
            portfolio_id=root,
            expected_day=AT.date(),
            settings=settings,
            clock=lambda: AT,
        )

    async def wait_for_gate():
        if close_first:
            async with factory.begin() as db:
                waiter_pid.set_result(await db.scalar(text("SELECT pg_backend_pid()")))
                return await capture(db)
        async with migrator.begin() as conn:
            waiter_pid.set_result(await conn.scalar(text("SELECT pg_backend_pid()")))
            await close_empty_test_root(conn, root)
        return False

    blocking_factory = async_sessionmaker(migrator) if close_first else factory
    async with blocking_factory() as db:
        pid = await db.scalar(text("SELECT pg_backend_pid()"))
        if close_first:
            await close_empty_test_root(db, root)
        else:
            assert await capture(db)
        task = asyncio.create_task(wait_for_gate())
        try:
            async with asyncio.timeout(5):
                waiter = await waiter_pid
                async with migrator.connect() as monitor:
                    while pid not in await monitor.scalar(  # noqa: ASYNC110
                        text("SELECT pg_blocking_pids(:waiter)"), {"waiter": waiter}
                    ):
                        await asyncio.sleep(0.01)
            await db.commit()
            assert not await asyncio.wait_for(task, timeout=5)
        finally:
            if not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
    assert not await record(factory, owner, root, settings)
    expected = [] if close_first else [(root, AT, Decimal("10000"), Decimal("777.77"), True)]
    assert await readings(factory) == expected


@pytest_asyncio.fixture
async def scheduler_books(capture_world):
    factory, migrator, world = capture_world
    engine = create_async_engine(
        factory.kw["bind"].url, connect_args={"server_settings": {"role": "birja_scheduler"}}
    )
    try:
        async with engine.connect() as conn:
            assert await conn.scalar(text("SELECT current_user")) == "birja_scheduler"
            assert await daily_task.daily_capture_schema_available(engine)
        yield async_sessionmaker(engine), factory, migrator, world
    finally:
        await engine.dispose()


async def test_scheduler_cycle_batch_fairness_and_rollback(scheduler_books, monkeypatch):
    scheduler, admin, migrator, world = scheduler_books
    extra = []
    async with migrator.begin() as conn:
        for i in range(6):
            extra.append(
                await conn.scalar(
                    text("SELECT portfolio_id FROM create_portfolio(:o,:key,:name,'')"),
                    {"o": world.owner, "key": uuid4(), "name": f"Capture {i}"},
                )
            )
    doomed = world.single
    attempted = []
    real_capture = daily_task.capture_portfolio_daily_value

    async def intermittently_fail(db, **kwargs):
        root = kwargs["portfolio_id"]
        attempted.append(root)
        appended = await real_capture(db, **kwargs)
        if root == doomed and attempted.count(root) == 1:
            raise RuntimeError("Synthetic capture rollback")
        return appended

    monkeypatch.setattr(daily_task, "capture_portfolio_daily_value", intermittently_fail)
    settings, cursor = SchedulerSettings(), daily_task.DailyValueCursor()

    async def run():
        return await daily_task.run_portfolio_daily_capture(
            sessionmaker=scheduler, settings=settings, cursor=cursor, clock=lambda: AT
        )

    expected = [world.single, world.first, world.sibling, world.foreign, *extra]
    assert await run() == CycleResult("ok", accepted=7, rejected=1)
    assert attempted == expected[:8]
    assert [row.portfolio_id for row in await readings(admin)] == expected[1:8]
    assert await run() == CycleResult("ok", accepted=2)
    assert attempted == expected
    assert await run() == CycleResult("ok")
    assert cursor.after_id == 0
    assert await run() == CycleResult("ok", accepted=1)
    assert attempted == [*expected, doomed]
    assert [row.portfolio_id for row in await readings(admin)] == expected


async def test_scheduler_cycle_timeout_advances_to_later_roots(scheduler_books):
    scheduler, admin, migrator, world = scheduler_books
    cursor = daily_task.DailyValueCursor()
    async with migrator.begin() as conn:
        await conn.execute(
            text("SELECT id FROM accounts WHERE id=:root FOR UPDATE"), {"root": world.single}
        )
        result = await daily_task.run_portfolio_daily_capture(
            sessionmaker=scheduler, settings=SchedulerSettings(), cursor=cursor, clock=lambda: AT
        )
    assert result == CycleResult("ok", accepted=3, rejected=1)
    assert [row.portfolio_id for row in await readings(admin)] == [
        world.first,
        world.sibling,
        world.foreign,
    ]


async def test_scheduler_cycle_window_rollover_restart_and_duplicate(scheduler_books):
    scheduler, admin, _, _ = scheduler_books
    settings = SchedulerSettings()
    cursor = daily_task.DailyValueCursor()

    async def run(at, state=cursor):
        return await daily_task.run_portfolio_daily_capture(
            sessionmaker=scheduler, settings=settings, cursor=state, clock=lambda: at
        )

    opens = AT.replace(hour=22, minute=0)
    assert await run(opens - timedelta(microseconds=1)) == CycleResult("ok")
    outcomes = await asyncio.gather(run(opens), run(opens, daily_task.DailyValueCursor()))
    assert all(outcome.status == "ok" and not outcome.rejected for outcome in outcomes)
    assert sum(outcome.accepted for outcome in outcomes) == 4
    assert await run(opens + timedelta(minutes=15), daily_task.DailyValueCursor()) == CycleResult(
        "ok"
    )
    assert await run(opens + timedelta(hours=2)) == CycleResult("ok")
    assert cursor.day is None and cursor.after_id == 0
    assert await run(opens + timedelta(days=2)) == CycleResult("ok", accepted=4)
    assert [row.captured_at for row in await readings(admin)] == [
        opens,
        opens + timedelta(days=2),
    ] * 4


async def test_scheduler_cycle_clock_failures_are_local(scheduler_books):
    scheduler, admin, _, _ = scheduler_books
    settings = SchedulerSettings()
    cursor = daily_task.DailyValueCursor()

    def unavailable():
        raise RuntimeError("Synthetic clock unavailable")

    assert await daily_task.run_portfolio_daily_capture(
        sessionmaker=scheduler, settings=settings, cursor=cursor, clock=unavailable
    ) == CycleResult("source_error")
    clock = iter([AT, AT.replace(hour=21)])
    assert await daily_task.run_portfolio_daily_capture(
        sessionmaker=scheduler, settings=settings, cursor=cursor, clock=lambda: next(clock)
    ) == CycleResult("ok")
    assert await readings(admin) == []
