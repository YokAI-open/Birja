"""Durable valuations against the isolated PostgreSQL runtime roles."""

import asyncio
import hashlib
import json
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import SchedulerSettings
from app.services.portfolio import load_portfolio_snapshots
from app.services.portfolio_daily_values import capture_portfolio_daily_value
from app.tasks import portfolio_daily_values as daily_task
from app.tasks import stock_catalog_import
from app.tasks.scheduler import CycleResult
from app.tasks.stock_catalog_enroll import _execute_batch, _inputs
from tests.helpers import coin_id, put_price
from tests.portfolio_fixtures import close_empty_test_root, seed_portfolio_world
from tests.stock_action_fixtures import synthetic_owned_portfolio
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case
from tests.test_migrations import install_current_test_grants, run_test_migration
from tests.test_portfolio_daily_schema import authorize_dev, run_migration, scratch_database
from tests.test_stock_catalog_enroll import ACCOUNT, SERVER, _files, _private
from tests.test_stock_catalog_finance_migration import finance_0025
from tests.test_stock_catalog_promotion import finance_0026
from tests.test_stock_catalog_publish import NOW, _manifest, _publish, _rights
from tests.test_stock_sessions import evidence
from tests.test_stock_trading_service import trade_order

__all__ = [
    "scratch_database",
    "finance_0025",
    "finance_0026",
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
    finance_0026, engine, settings, scope, tmp_path, monkeypatch
):
    from app.models.corporate_action import StockActionState
    from app.models.stock import StockDataAdmission, StockSession
    from app.models.stock_catalog import StockCatalogAdmission, StockCatalogListing
    from app.models.stock_catalog_finance import (
        StockCatalogActionCoverage,
        StockCatalogFinancialQuote,
        StockCatalogInstrument,
    )
    from app.models.trade import Holding
    from app.services.stock_sessions import build_sessions

    monkeypatch.setenv("STOCK_DATA_ACCOUNT", ACCOUNT)
    monkeypatch.setenv("STOCK_DATA_SERVER", SERVER)
    monkeypatch.setenv("ALPACA_ASSET_ENVIRONMENT", "paper")
    await asyncio.to_thread(run_test_migration, "0028")
    await install_current_test_grants()
    at = NOW.replace(hour=22, minute=0)
    deadline = at + timedelta(hours=1)
    rights = _rights()
    async with finance_0026.begin() as db:
        db.add_all(
            StockCatalogAdmission(**right.model_dump(), scope={}, is_fixture=False)
            for right in rights
        )
    publication = await _publish(finance_0026, _manifest(rights=rights), None)
    packet, files = _files(tmp_path, publication.generation_id, publication.digest)
    for product in ("assets", "units", "execution", "mark", "halt", "actions"):
        packet[product]["valid_until"] = deadline.isoformat()
    if scope == "derived_restricted":
        packet["mark_limits"] = {**packet["mark_limits"], "durable_derived_use": False}
    _private(files[0], json.dumps(packet).encode())
    inputs = _inputs(*files)
    async with finance_0026.begin() as db:
        reviewed = await _execute_batch(db, inputs, now=NOW, after=0, limit=100)
        applied = await _execute_batch(
            db, inputs, now=NOW, after=0, limit=100, expected_sha=reviewed["batch_sha256"]
        )
        assert applied["outcomes"] == {"enroll": 2}
        listing = await db.scalar(
            select(StockCatalogListing).where(StockCatalogListing.ticker == "FQA")
        )
        bound = await db.get(StockCatalogInstrument, listing.security_id)
        grants = {
            grant.artifact: grant
            for grant in await db.scalars(
                select(StockCatalogAdmission).where(
                    StockCatalogAdmission.scope.contains({"listing_id": str(listing.id)})
                )
            )
        }
        mark, actions = grants["catalog_mark"], grants["catalog_actions"]
    assert mark.scope == {
        **packet["mark_limits"],
        "account": ACCOUNT,
        "server": SERVER,
        "catalog_id": str(bound.catalog_id),
        "listing_id": str(listing.id),
        "provider_asset_id": listing.provider_asset_id,
        "feed": "iex",
    }

    if scope in {"backup_restricted", "revoked"}:

        class ReviewClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return NOW + timedelta(minutes=1)

        monkeypatch.setattr(stock_catalog_import, "datetime", ReviewClock)
        async with engine.begin() as conn:
            await conn.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
        exact_scope = {**mark.scope, "durable_derived_backup": False}
        exact_packet = tmp_path / "exact-mark.json"
        row = {
            "artifact": "catalog_mark",
            "reference": "Synthetic reviewed closed market mark",
            "reviewed_at": mark.reviewed_at.isoformat(),
            "valid_until": deadline.isoformat(),
            "fields": mark.fields,
            "scope": exact_scope,
        }
        args = ["admit", str(exact_packet), "--expect-generation", str(publication.generation_id)]
        migrator = finance_0026.kw["bind"]
        if scope == "backup_restricted":
            for invalid in ("false", None, 0):
                raw = json.dumps(
                    {
                        "version": 1,
                        "admissions": [
                            {**row, "scope": {**exact_scope, "durable_derived_backup": invalid}}
                        ],
                        "revoke_ids": [mark.id],
                    }
                )
                _private(exact_packet, raw.encode())
                with pytest.raises(ValidationError, match="durable_derived_backup"):
                    await stock_catalog_import._admit(migrator, stock_catalog_import._args(args))
            forbidden = {
                **row,
                "artifact": "catalog_execution",
                "fields": stock_catalog_import._FINANCIAL_FIELDS["catalog_execution"],
            }
            _private(exact_packet, json.dumps({"version": 1, "admissions": [forbidden]}).encode())
            with pytest.raises(ValidationError, match="durable_derived_backup"):
                await stock_catalog_import._admit(migrator, stock_catalog_import._args(args))
        raw = json.dumps({"version": 1, "admissions": [row], "revoke_ids": [mark.id]})
        _private(exact_packet, raw.encode())
        review = await stock_catalog_import._admit(migrator, stock_catalog_import._args(args))
        digest = hashlib.sha256(raw.encode()).hexdigest()
        assert review["packet_sha256"] == digest
        replacement = await stock_catalog_import._admit(
            migrator,
            stock_catalog_import._args(
                [
                    *args,
                    "--apply",
                    "--expected-packet-sha",
                    digest,
                ]
            ),
        )
        async with finance_0026() as db:
            new_mark = await db.get(StockCatalogAdmission, int(replacement["admission_ids"][0]))
            assert new_mark.scope == exact_scope
        if scope == "backup_restricted":
            mark = new_mark

    # Synthetic prices and action completeness let the actual reviewed mark apply
    # after the exchange closes. Quote evidence references the grant writer's ID.
    observed = at - timedelta(hours=1, minutes=1)
    calendar = evidence(observed)
    calendar = replace(calendar, scope={**calendar.scope, "account": ACCOUNT, "server": SERVER})
    sessions = build_sessions(observed, calendar, account=ACCOUNT, server=SERVER)
    session = next(
        row for row in sessions if row.exchange == "NASDAQ" and row.session_date == at.date()
    )
    async with finance_0026.begin() as db:
        world = await seed_portfolio_world(await db.connection())
        first, owner = world.first, world.owner
        db.add(StockDataAdmission(**asdict(calendar)))
        db.add_all(StockSession(**asdict(row)) for row in sessions)
        db.add(
            Holding(
                coin_id=bound.coin_id,
                portfolio_id=first,
                user_id=owner,
                quantity=Decimal(2),
                cost_basis=Decimal("198.50"),
            )
        )
        db.add(
            StockCatalogFinancialQuote(
                coin_id=bound.coin_id,
                catalog_id=bound.catalog_id,
                listing_id=listing.id,
                provider_asset_id=listing.provider_asset_id,
                provider_admission_id=listing.provider_admission_id,
                mark_admission_id=mark.id,
                bid=Decimal(101),
                ask=Decimal(103),
                unit_epoch=0,
                event_at=observed,
                collected_at=observed,
                observed_at=observed,
                session_date=session.session_date,
                opens_at=session.opens_at,
                closes_at=session.closes_at,
                calendar_generation=session.calendar_admission_generation,
                valid_until=deadline,
            )
        )
        state = await db.get(StockActionState, bound.coin_id)
        state.health, state.checked_at, state.valid_until = "current", observed, deadline
        state.journal_start_at = state.complete_from = state.coverage_start = bound.promoted_at
        state.covered_until, state.admission_generation = observed, actions.id
        db.add(
            StockCatalogActionCoverage(
                coin_id=bound.coin_id,
                catalog_id=bound.catalog_id,
                listing_id=listing.id,
                admission_id=actions.id,
                journal_origin=bound.promoted_at,
                coverage_start=bound.promoted_at,
                covered_until=observed,
                observed_at=observed,
                valid_until=deadline,
            )
        )
        await db.execute(
            text("INSERT INTO prices(coin_id,mid,as_of,source) VALUES (:coin,100,:at,'fake')"),
            {"coin": world.crypto, "at": observed},
        )
    scope_settings = {"stock_data_account": ACCOUNT, "stock_data_server": SERVER}
    settings = settings.model_copy(update=scope_settings)
    factory = async_sessionmaker(engine)
    async with factory.begin() as db:
        await db.execute(text("SET LOCAL ROLE birja_app"))
        (current,) = await load_portfolio_snapshots(
            db, owner_id=owner, portfolio_ids=[first], settings=settings, now=at
        )
    assert current.total_value == (None if scope == "revoked" else Decimal("1448.56")), [
        (holding.symbol, holding.stock_mark) for holding in current.holdings
    ]
    async with factory.begin() as db:
        await db.execute(text("SET LOCAL ROLE birja_scheduler"))
        assert await capture_portfolio_daily_value(
            db,
            owner_id=owner,
            portfolio_id=first,
            expected_day=at.date(),
            settings=SchedulerSettings(**scope_settings),
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
