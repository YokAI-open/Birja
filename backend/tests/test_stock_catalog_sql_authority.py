"""Catalog fill authority on the staged disposable PostgreSQL revision."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.db.schema_contract import require_schema
from app.models.stock_catalog import StockCatalogAdmission
from tests.portfolio_fixtures import economic_snapshot, seed_portfolio_world
from tests.test_migrations import install_current_test_grants, run_test_migration
from tests.test_stock_catalog_promotion import (
    ACCOUNT,
    FIRST_ASSET,
    SERVER,
    _listing,
    _promote,
    _reviewed_grant,
)
from tests.test_stock_catalog_promotion import (
    finance_0025 as finance_0025,
)
from tests.test_stock_catalog_promotion import (
    finance_0026 as finance_0026,
)
from tests.test_stock_catalog_publish import Factory, _manifest, _publish


@pytest_asyncio.fixture
async def execution_market(finance_0026: Factory):
    now = datetime.now(UTC)
    origin = now - timedelta(minutes=15)
    opens = now - timedelta(minutes=10)
    end = now + timedelta(minutes=10)
    session_date = now.date()
    generation = await _publish(finance_0026, _manifest(origin), None, now=origin)
    listing = await _listing(finance_0026, generation.generation_id, "FQA")
    grant = await _reviewed_grant(finance_0026, listing, FIRST_ASSET, origin)
    instrument = await _promote(finance_0026, listing, grant, origin)
    common = {
        "c": instrument.coin_id,
        "catalog": instrument.catalog_id,
        "listing": instrument.listing_id,
        "provider": instrument.provider_admission_id,
        "execution": grant,
        "asset": FIRST_ASSET,
        "account": ACCOUNT,
        "server": SERVER,
        "session": session_date,
        "opens": opens,
        "end": end,
        "origin": origin,
        "now": now,
        "report": "a" * 64,
        "report_until": now + timedelta(seconds=120),
    }
    async with finance_0026.begin() as db:
        for artifact, feed, fields, purposes in (
            (
                "halt",
                "nasdaq-rss",
                ("report_digest", "event_at", "valid_until", "state"),
                ("collection", "execution", "storage", "backup"),
            ),
            (
                "actions",
                "alpaca-corporate-actions",
                ("provider_event_id", "symbol", "event_type", "process_date", "terms"),
                ("collection", "derivation", "storage", "backup"),
            ),
        ):
            permission = StockCatalogAdmission(
                artifact=f"catalog_{artifact}",
                reference="Disposable scope review",
                reviewed_at=origin,
                valid_until=end,
                is_fixture=True,
                fields={field: list(purposes) for field in fields},
                scope={
                    "account": ACCOUNT,
                    "server": SERVER,
                    "catalog_id": str(instrument.catalog_id),
                    "listing_id": str(instrument.listing_id),
                    "provider_asset_id": FIRST_ASSET,
                    "feed": feed,
                },
            )
            db.add(permission)
            await db.flush()
            common[artifact] = permission.id
        world = await seed_portfolio_world(await db.connection())
        common |= {"p": world.first, "u": world.owner}
        await db.execute(
            text("""
            INSERT INTO stock_data_admissions
              (product,state,generation,reviewed_at,valid_from,valid_until,evidence_ref,
               terms_version,collection_allowed,derived_allowed,scope,calendar)
            VALUES ('calendar','approved',1,:origin,:origin,:end,'synthetic','synthetic',true,true,
              jsonb_build_object('application','birja','audience','authenticated-users',
                'feed','iex','account',CAST(:account AS text),'server',CAST(:server AS text)),
              jsonb_build_object('review_valid_until',CAST(:end AS timestamptz)))
        """),
            common,
        )
        await db.execute(
            text("""
            INSERT INTO stock_sessions
              (exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation)
            VALUES ('NASDAQ',:session,:opens,:end,:session,:session,1)
        """),
            common,
        )
        await db.execute(
            text("""
            INSERT INTO stock_catalog_status
              (coin_id,catalog_id,listing_id,admission_id,report_digest,state,event_at,
               observed_at,valid_until,session_date)
            VALUES (:c,:catalog,:listing,:halt,:report,'normal',:now,:now,:report_until,:session)
        """),
            common,
        )
        await db.execute(
            text("""
            INSERT INTO stock_catalog_action_coverage
              (coin_id,catalog_id,listing_id,admission_id,journal_origin,coverage_start,
               covered_until,observed_at,valid_until)
            VALUES (:c,:catalog,:listing,:actions,:origin,:origin,:now,:now,:end)
        """),
            common,
        )
        await db.execute(
            text("""
            UPDATE stock_action_state SET health='current', checked_at=:now, valid_until=:end,
              coverage_start=:origin, covered_until=:now, journal_start_at=:origin,
              complete_from=:origin, admission_generation=:actions
            WHERE coin_id=:c
        """),
            common,
        )
    return common


async def _book_catalog_fill(conn: AsyncConnection, market: dict, case: str) -> dict:
    expected = {"provider_asset_id": market["asset"]} | {
        field: str(market[key])
        for field, key in (
            ("portfolio_id", "p"),
            ("coin_id", "c"),
            ("catalog_id", "catalog"),
            ("listing_id", "listing"),
        )
    }
    event = market["now"] - timedelta(seconds=120 if case == "quote_age" else 1)
    values = market | {"event": event, "key": uuid4(), "authority": json.dumps(expected)}
    for statement in (
        "SELECT pg_advisory_xact_lock_shared(1026019025)",
        "SELECT pg_advisory_xact_lock(hashtextextended("
        "'birja.stock.instrument:' || CAST(CAST(:c AS bigint) AS text),0))",
        "SELECT id FROM accounts WHERE id=:p FOR UPDATE",
        """
        INSERT INTO stock_catalog_financial_quotes (coin_id,catalog_id,listing_id,provider_asset_id,
          provider_admission_id,execution_admission_id,bid,ask,unit_epoch,event_at,collected_at,observed_at,
          session_date,calendar_generation,opens_at,closes_at,valid_until)
        VALUES (:c,:catalog,:listing,:asset,:provider,:execution,9.995,10.005,0,:event,:now,:now,
          :session,1,:opens,:end,:end)
        """,
        "UPDATE accounts SET cash=cash-10 WHERE id=:p",
        "INSERT INTO holdings (portfolio_id,user_id,coin_id,quantity,cost_basis) "
        "VALUES (:p,:u,:c,1,10)",
    ):
        await conn.execute(text(statement), values)

    values["t"] = await conn.scalar(
        text("""
        INSERT INTO trades (portfolio_id,user_id,coin_id,side,input_kind,input_value,quantity,
          mid_price,price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key)
        SELECT :p,:u,:c,'buy','quantity',1,1,10,:event,10.005,0,-10,cash,:key
        FROM accounts WHERE id=:p RETURNING id
    """),
        values,
    )
    await conn.execute(
        text("""
        INSERT INTO stock_fill_facts (trade_id,portfolio_id,coin_id,user_id,provider_asset_id,
          symbol,company_name,listing_exchange,source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,
          observed_at,session_date,opens_at,closes_at,authority)
        SELECT :t,:p,:c,:u,:asset,ticker,company_name,listing_exchange,'alpaca','iex',9.995,10.005,
          10,1,:event,:now,:now,:session,:opens,:end,CAST(:authority AS jsonb)
        FROM stock_catalog_listings WHERE id=:listing
    """),
        values,
    )
    await conn.execute(
        text("""
        INSERT INTO stock_ownership_movements (coin_id,portfolio_id,user_id,sequence,economic_at,
          recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,
          cause_kind,trade_id,causal_key)
        VALUES (:c,:p,:u,1,:now,:now,1,0,1,0,10,0,'fill',:t,CAST(CAST(:key AS uuid) AS text))
    """),
        values,
    )
    if case != "missing_adjunct":
        await conn.execute(
            text("""
            INSERT INTO stock_catalog_fill_evidence (trade_id,coin_id,catalog_id,listing_id,
              provider_admission_id,execution_admission_id,halt_admission_id,action_admission_id,
              unit_epoch,action_epoch,report_digest,report_event_at,report_valid_until,quote_valid_until)
            SELECT :t,:c,:catalog,:listing,:provider,:execution,:halt,:actions,0,a.epoch,:report,
              :now,:report_until,:end FROM stock_action_state a WHERE coin_id=:c
        """),
            values,
        )
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    await conn.execute(text("SELECT pg_advisory_xact_lock_shared(1326459824,1)"))
    return values


_FINAL = text(
    "SELECT public.assert_catalog_stock_execution_current(:t,:u,CAST(:authority AS jsonb))"
)


async def test_catalog_finalizer_executes_under_app_grants(
    engine: AsyncEngine,
    execution_market: dict,
) -> None:
    await install_current_test_grants()
    async with engine.begin() as conn:
        fill = await _book_catalog_fill(conn, execution_market, "valid")
        await conn.execute(text("SET LOCAL ROLE birja_app"))
        assert await require_schema(conn) == "0026"
        await conn.execute(_FINAL, fill)
        assert (
            await conn.scalar(
                text("SELECT report_digest FROM stock_catalog_fill_evidence WHERE trade_id=:t"),
                fill,
            )
            == fill["report"]
        )


async def test_execution_exact_fill_is_retained_and_adjunct_is_immutable(
    finance_0026: Factory,
    execution_market: dict,
) -> None:
    async with finance_0026.begin() as db:
        conn = await db.connection()
        fill = await _book_catalog_fill(conn, execution_market, "valid")
        await conn.execute(_FINAL, fill)
    async with finance_0026.begin() as db:
        assert await db.scalar(text("SELECT cash_delta FROM trades WHERE id=:t"), fill) == Decimal(
            "-10.00"
        )
        assert (
            await db.scalar(
                text("SELECT report_digest FROM stock_catalog_fill_evidence WHERE trade_id=:t"),
                fill,
            )
            == fill["report"]
        )
        with pytest.raises(DBAPIError, match="catalog stock fill facts are immutable"):
            async with db.begin_nested():
                await db.execute(
                    text("DELETE FROM stock_catalog_fill_evidence WHERE trade_id=:t"), fill
                )


@pytest.mark.parametrize(
    ("case", "expected"),
    [
        ("quote_age", "quote unavailable"),
        ("new_report", "status unavailable"),
        ("revoked_grant", "execution permission changed"),
        ("new_unit", "action unavailable"),
        ("wrong_listing", "execution permission changed"),
        ("wrong_calendar_scope", "market closed"),
        ("wrong_action_generation", "action unavailable"),
        ("other_cash", "authority identity changed"),
        ("missing_adjunct", "fill facts required"),
    ],
)
async def test_execution_refusal_rolls_back_ledger(
    finance_0026: Factory,
    execution_market: dict,
    case: str,
    expected: str,
) -> None:
    async with finance_0026.begin() as db:
        before = await economic_snapshot(await db.connection())
    with pytest.raises(DBAPIError, match=expected):
        async with finance_0026.begin() as db:
            conn = await db.connection()
            order = await _book_catalog_fill(conn, execution_market, case)
            if case == "new_report":
                await conn.execute(
                    text(
                        "UPDATE stock_catalog_status SET report_digest=repeat('b',64) "
                        "WHERE coin_id=:c"
                    ),
                    order,
                )
            elif case == "revoked_grant":
                await conn.execute(
                    text(
                        "UPDATE stock_catalog_admissions SET revoked_at=clock_timestamp() "
                        "WHERE id=:execution"
                    ),
                    order,
                )
            elif case == "new_unit":
                await conn.execute(
                    text("UPDATE stock_action_state SET unit_epoch=1 WHERE coin_id=:c"), order
                )
            elif case == "wrong_listing":
                await conn.execute(
                    text("""
                    UPDATE stock_catalog_admissions
                    SET scope=jsonb_set(scope,'{listing_id}',to_jsonb('unrelated listing'::text))
                    WHERE id=:execution
                """),
                    order,
                )
            elif case == "wrong_calendar_scope":
                await conn.execute(
                    text("""
                    UPDATE stock_data_admissions
                    SET scope=jsonb_set(scope,'{server}',to_jsonb('unrelated server'::text))
                    WHERE product='calendar'
                """)
                )
            elif case == "other_cash":
                await conn.execute(text("UPDATE accounts SET cash=cash-1 WHERE id=:p"), order)
            elif case == "wrong_action_generation":
                await conn.execute(
                    text(
                        "UPDATE stock_action_state SET admission_generation=:execution "
                        "WHERE coin_id=:c"
                    ),
                    order,
                )
            await conn.execute(_FINAL, order)
    async with finance_0026.begin() as db:
        assert await economic_snapshot(await db.connection()) == before
        assert await db.scalar(text("SELECT count(*) FROM stock_catalog_fill_evidence")) == 0


_LEGACY_ROUTINES = text("""
    SELECT oid, proname, pg_get_functiondef(oid), proacl::text
    FROM pg_proc WHERE pronamespace='public'::regnamespace AND proname IN (
      'assert_stock_execution_current','stock_dividend_authority','apply_stock_dividend',
      'record_stock_dividend_hold','check_stock_split_digest_version','apply_stock_action_resolution'
    ) ORDER BY proname
""")


async def test_downgrade_restores_legacy_routine_definitions_and_grants(
    finance_0025: AsyncEngine,
) -> None:
    async with finance_0025.connect() as conn:
        before = (await conn.execute(_LEGACY_ROUTINES)).all()
        assert len(before) == 6
    await asyncio.to_thread(run_test_migration, "0026")
    async with finance_0025.connect() as conn:
        installed = (await conn.execute(_LEGACY_ROUTINES)).all()
        assert [row[:2] for row in installed] == [row[:2] for row in before]
        assert next(
            row for row in installed if row.proname == "assert_stock_execution_current"
        ) == (next(row for row in before if row.proname == "assert_stock_execution_current"))
        assert any(
            current[2] != legacy[2] for current, legacy in zip(installed, before, strict=True)
        )
    await asyncio.to_thread(run_test_migration, "0025", down=True)
    async with finance_0025.connect() as conn:
        assert (await conn.execute(_LEGACY_ROUTINES)).all() == before
