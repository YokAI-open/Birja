"""Committed, explicitly synthetic evidence for independent financial clients.

Only the owned disposable database is allowed. Financial behavior uses the
unchanged restricted SQL functions; cleanup runs after all clients finish.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from datetime import timedelta
from decimal import Decimal

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import dividends
from tests.stock_action_fixtures import (
    install_current_runtime_roles,
    synthetic_corruption,
    synthetic_opening,
    synthetic_portfolio_id,
)
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case  # noqa: F401
from tests.test_stock_action_migrations import event

__all__ = ["ownership", "status_case", "stock_trade_case", "dividend_case"]


async def require_owned(db):
    assert await db.scalar(
        text(
            "SELECT current_database()='birja_test' AND current_user='birja_test' "
            "AND rolsuper FROM pg_roles WHERE rolname=current_user"
        )
    ), "Committed financial fixture requires the guarded disposable test owner"


@pytest_asyncio.fixture
async def dividend_case(stock_trade_case, engine, request):
    factory, cid, uid, now = stock_trade_case
    async with engine.begin() as conn:
        await install_current_runtime_roles(conn)
    ids = None
    try:
        async with factory.begin() as db:
            root = await synthetic_portfolio_id(db, uid)
            eid, _, rid = await event(db, cid)
            terms = {
                "event_type": "cash_dividend",
                "currency": "USD",
                "subtype": "ordinary",
                "foreign": False,
                "special": False,
                "due_bills": False,
                "identity_verified": True,
                "dates_verified": True,
                "cancelled": False,
                "identity_changed": False,
                "rate": "0.5",
                "symbol": "AAPL",
                "ex_date": str(now.date() - timedelta(days=3)),
                "record_date": str(now.date() - timedelta(days=2)),
                "payable_date": str(now.date() - timedelta(days=1)),
            }
            cutoff = await db.scalar(
                text(
                    "SELECT opens_at FROM stock_sessions WHERE exchange='NASDAQ' "
                    "AND session_date=:d"
                ),
                {"d": now.date() - timedelta(days=3)},
            )
            assert cutoff is not None
            quantity = getattr(request.node, "callspec", None)
            quantity = Decimal(quantity.params.get("quantity", 2)) if quantity else Decimal(2)
            if quantity:
                await synthetic_opening(
                    db, cid, uid, cutoff - timedelta(days=1), quantity=quantity, basis=Decimal(20)
                )
            await db.execute(
                text(
                    "UPDATE stock_action_revisions SET classification='supported_dividend',"
                    "admission_generation=4,normalized_terms=CAST(:t AS jsonb),"
                    "verified_cutoff=NULL WHERE id=:r"
                ),
                {"t": json.dumps(terms), "r": rid},
            )
            ent = await db.scalar(
                text(
                    "INSERT INTO stock_dividend_entitlements"
                    "(event_id,portfolio_id,user_id,revision_id,cutoff,"
                    "cutoff_rule,units_basis,unit_epoch,last_movement_sequence,eligible_quantity,"
                    "state,version,fingerprint) VALUES (:e,:p,:u,:r,:cutoff,"
                    "'exclusive-regular-session-open','unit_epoch:0',0,:seq,:q,'eligible',1,"
                    "repeat('b',64)) RETURNING id"
                ),
                {
                    "e": eid,
                    "p": root,
                    "u": uid,
                    "r": rid,
                    "cutoff": cutoff,
                    "seq": 1 if quantity else 0,
                    "q": quantity,
                },
            )
            await db.execute(
                text(
                    "UPDATE stock_action_state SET journal_start_at=:j,complete_from=:j,"
                    "coverage_start=:j,covered_until=clock_timestamp() WHERE coin_id=:c"
                ),
                {"j": cutoff - timedelta(days=1), "c": cid},
            )
            await db.execute(text("UPDATE accounts SET cash=100 WHERE user_id=:u"), {"u": uid})
            ids = {
                "event_id": eid,
                "coin_id": cid,
                "user_id": uid,
                "portfolio_id": root,
                "revision_id": rid,
                "revision_fingerprint": "a" * 64,
                "entitlement_id": ent,
                "entitlement_fingerprint": "b" * 64,
            }
        yield factory, ids
    finally:
        async with factory.begin() as db:
            await require_owned(db)
            await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
            for table in ("stock_dividend_decisions", "stock_dividend_payments"):
                async with synthetic_corruption(db, table, trigger="stock_dividend_immutable"):
                    await db.execute(
                        text(f"DELETE FROM public.{table} WHERE user_id=:u"),  # noqa: S608 - fixed tuple
                        {"u": uid},
                    )
            if ids is not None:
                await db.execute(
                    text("DELETE FROM stock_action_resolutions WHERE event_id=:event_id"), ids
                )
                async with synthetic_corruption(
                    db, "stock_dividend_entitlements", trigger="portfolio_association_only"
                ):
                    await db.execute(
                        text("DELETE FROM stock_dividend_entitlements WHERE event_id=:event_id"),
                        ids,
                    )


@asynccontextmanager
async def scheduler(factory):
    async with factory.kw["bind"].connect() as conn:
        pid = await conn.scalar(text("SELECT pg_backend_pid()"))
        await conn.execute(text("SET ROLE birja_scheduler"))
        await conn.commit()
        try:
            async with AsyncSession(bind=conn, expire_on_commit=False) as db:
                db.info["pid"] = pid
                yield db
        finally:
            await conn.rollback()
            await conn.execute(text("RESET ROLE"))
            await conn.commit()


async def process(factory, ids):
    async with scheduler(factory) as db:
        return await dividends.process_dividend(db, **work(ids))


def work(ids):
    return {
        "event_id": ids["event_id"],
        "portfolio_id": ids["portfolio_id"],
        "entitlement_id": ids["entitlement_id"],
        "expected_revision_fingerprint": ids["revision_fingerprint"],
        "expected_entitlement_fingerprint": ids["entitlement_fingerprint"],
    }


async def hold(factory, payment, fingerprint):
    async with factory() as db:
        root = (
            await db.execute(
                text("SELECT portfolio_id FROM stock_dividend_payments WHERE id=:p"), {"p": payment}
            )
        ).scalar_one()
    async with scheduler(factory) as db:
        return await dividends.record_dividend_hold(
            db, portfolio_id=root, payment_id=payment, expected_revision_fingerprint=fingerprint
        )


async def successor(conn, ids, *, rate="0.75", classification="supported_dividend", eligible=True):
    """Append current-root synthetic evidence; accounting remains actual restricted SQL."""
    fp = (
        await conn.execute(text("SELECT encode(sha256(gen_random_uuid()::text::bytea),'hex')"))
    ).scalar_one()
    rid = (
        await conn.execute(
            text("""INSERT INTO stock_action_revisions(event_id,source_id,
      ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,
      classification,reason,verified_cutoff)
      SELECT event_id,source_id,ordinal+1,:fp,'snapshot',clock_timestamp(),admission_generation,
      jsonb_set(normalized_terms,'{rate}',to_jsonb(CAST(:rate AS text))),:classification,'fixture',
      NULL FROM stock_action_revisions WHERE id=:revision_id RETURNING id"""),
            {**ids, "fp": fp, "rate": rate, "classification": classification},
        )
    ).scalar_one()
    await conn.execute(
        text("UPDATE stock_action_events SET current_revision_id=:r WHERE id=:event_id"),
        {**ids, "r": rid},
    )
    await conn.execute(
        text("UPDATE stock_action_state SET epoch=epoch+1 WHERE coin_id=:coin_id"), ids
    )
    new = {**ids, "revision_id": rid, "revision_fingerprint": fp}
    if eligible:
        efp = (
            await conn.execute(text("SELECT encode(sha256(gen_random_uuid()::text::bytea),'hex')"))
        ).scalar_one()
        eid = (
            await conn.execute(
                text("""INSERT INTO stock_dividend_entitlements(event_id,portfolio_id,user_id,
          revision_id,cutoff,cutoff_rule,units_basis,unit_epoch,last_movement_sequence,
          eligible_quantity,state,version,supersedes_id,fingerprint)
          SELECT event_id,portfolio_id,user_id,:r,cutoff,cutoff_rule,units_basis,unit_epoch,
          last_movement_sequence,
          eligible_quantity,'eligible',version+1,id,:f FROM stock_dividend_entitlements
          WHERE id=:entitlement_id RETURNING id"""),
                {**ids, "r": rid, "f": efp},
            )
        ).scalar_one()
        new.update(entitlement_id=eid, entitlement_fingerprint=efp)
    return new


async def revise(factory, ids, **changes):
    async with factory.begin() as db:
        return await successor(db, ids, **changes)


async def books(factory, uid):
    async with factory() as db:
        cash = await db.scalar(text("SELECT cash FROM accounts WHERE user_id=:u"), {"u": uid})
        rows = []
        for table in ("stock_dividend_payments", "stock_dividend_decisions", "trades"):
            rows.append(
                (
                    await db.execute(
                        text(
                            f"SELECT to_jsonb(t) FROM public.{table} t "  # noqa: S608 - fixed tuple
                            "WHERE user_id=:u ORDER BY id"
                        ),
                        {"u": uid},
                    )
                )
                .scalars()
                .all()
            )
        return cash, rows


async def waiting(factory, pid, task):
    async with asyncio.timeout(5):
        while True:
            if task.done():
                await task
                raise AssertionError("Client completed before its actual PostgreSQL wait")
            async with factory() as db:
                if await db.scalar(text("SELECT cardinality(pg_blocking_pids(:p))"), {"p": pid}):
                    return
            await asyncio.sleep(0.01)
