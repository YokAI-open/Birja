# ruff: noqa: F811
"""Observed PostgreSQL waits revalidate advancing retained dividend authority."""

import asyncio
from contextlib import asynccontextmanager
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.services import dividends
from app.services.stock_ownership import acquire_stock_gate
from tests.dividend_fixtures import (  # noqa: F401
    books,
    dividend_case,
    hold,
    ownership,
    process,
    require_owned,
    revise,
    scheduler,
    status_case,
    stock_trade_case,
    waiting,
    work,
)

__all__ = ["dividend_case"]


@asynccontextmanager
async def constraint_barrier(factory):
    """Inject synchronization, never a financial effect or weakened invariant.

    Dividend-only transactions currently have no naturally deferred trigger.
    This test adds an owned deferred callback to exercise the existing explicit
    SET CONSTRAINTS boundary, then authenticates and removes it in finally.
    """
    name = "test_dividend_wait_" + uuid4().hex
    body = "BEGIN PERFORM pg_advisory_xact_lock(101008,NEW.user_id::integer); RETURN NEW; END"
    async with factory.begin() as db:
        await require_owned(db)
        await db.execute(
            text(
                f"CREATE FUNCTION public.{name}() RETURNS trigger "
                "LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp "
                f"AS $barrier${body}$barrier$"
            )
        )
        for table in ("stock_dividend_payments", "stock_dividend_decisions"):
            await db.execute(
                text(
                    f"CREATE CONSTRAINT TRIGGER {name} AFTER INSERT ON "
                    f"public.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
                    f"EXECUTE FUNCTION public.{name}()"
                )
            )
    try:
        yield
    finally:
        async with factory.begin() as db:
            await require_owned(db)
            row = (
                await db.execute(
                    text(
                        "SELECT p.oid,p.prosrc,pg_get_userbyid(p.proowner),"
                        "p.proconfig FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                        "WHERE n.nspname='public' AND p.proname=:n"
                    ),
                    {"n": name},
                )
            ).one()
            assert tuple(row)[1:] == (
                body,
                "birja_test",
                ["search_path=pg_catalog, public, pg_temp"],
            )
            for table in ("stock_dividend_payments", "stock_dividend_decisions"):
                assert await db.scalar(
                    text(
                        "SELECT tgfoid=:oid AND tgdeferrable "
                        "AND tginitdeferred FROM pg_trigger WHERE tgrelid=to_regclass(:table) "
                        "AND tgname=:name"
                    ),
                    {"oid": row.oid, "table": table, "name": name},
                )
                await db.execute(text(f"DROP TRIGGER {name} ON public.{table}"))
            await db.execute(text(f"DROP FUNCTION public.{name}()"))


MUTATIONS = {
    "rights": "UPDATE stock_data_admissions SET state='denied' WHERE product='actions'",
    "same_generation_hash": "UPDATE stock_data_admissions SET attribution='changed' "
    "WHERE product='actions'",
    "retention": "UPDATE stock_data_admissions SET scope=scope-'backup_restore' "
    "WHERE product='reference'",
    "cutoff": "UPDATE stock_dividend_entitlements SET cutoff=cutoff+interval '1 second' "
    "WHERE event_id=:event_id",
    "units": "UPDATE stock_dividend_entitlements SET units_basis='shares' WHERE event_id=:event_id",
    "monitor": "UPDATE stock_action_state SET health='unknown' WHERE coin_id=:coin_id",
    "calendar": "UPDATE stock_data_admissions SET calendar=jsonb_set(calendar,'{version}',"
    "'\"changed-same-generation\"'::jsonb) WHERE product='calendar'",
}


async def mutate(factory, ids, mutation):
    if mutation == "revision":
        await revise(factory, ids)
        return
    async with factory.begin() as db:
        if mutation == "persistent_hold":
            await db.execute(
                text(
                    "INSERT INTO stock_action_observations(event_id,source_id,revision_id,"
                    "mutation_id,observed_at,admission_generation,source_kind,cycle_id) "
                    "SELECT event_id,source_id,id,:key,clock_timestamp(),4,"
                    "'missing_or_uncertain',:key FROM stock_action_revisions "
                    "WHERE id=:revision_id"
                ),
                {**ids, "key": str(uuid4())},
            )
        elif mutation == "newer_entitlement":
            await db.execute(
                text(
                    "INSERT INTO stock_dividend_entitlements(event_id,user_id,"
                    "revision_id,cutoff,cutoff_rule,units_basis,unit_epoch,last_movement_sequence,"
                    "eligible_quantity,state,version,supersedes_id,fingerprint) SELECT event_id,"
                    "user_id,revision_id,cutoff,cutoff_rule,units_basis,unit_epoch,"
                    "last_movement_sequence,eligible_quantity,'held',version+1,id,repeat('c',64) "
                    "FROM stock_dividend_entitlements WHERE id=:entitlement_id"
                ),
                ids,
            )
        else:
            await db.execute(text(MUTATIONS[mutation]), ids)


@pytest.mark.parametrize("boundary", ["gate", "account", "constraints"])
@pytest.mark.parametrize(
    "mutation", [*MUTATIONS, "revision", "newer_entitlement", "persistent_hold"]
)
async def test_actual_wait_reloads_current_and_refuses_invalid_authority(
    dividend_case, boundary, mutation
):
    factory, ids = dividend_case
    before = await books(factory, ids["user_id"])
    async with constraint_barrier(factory), scheduler(factory) as writer, factory() as blocker:
        if boundary == "gate":
            await acquire_stock_gate(blocker, ids["coin_id"])
        elif boundary == "account":
            await blocker.execute(
                text("SELECT user_id FROM accounts WHERE user_id=:user_id FOR UPDATE"), ids
            )
        else:
            await blocker.execute(
                text("SELECT pg_advisory_xact_lock(101008,:u)"), {"u": ids["user_id"]}
            )
        task = asyncio.create_task(dividends.process_dividend(writer, **work(ids)))
        try:
            await waiting(factory, writer.info["pid"], task)
            await mutate(factory, ids, mutation)
            await blocker.rollback()
            accepts_current = boundary != "constraints" and mutation in (
                "same_generation_hash",
                "calendar",
            )
            if accepts_current:
                assert (await asyncio.wait_for(task, 5)).outcome == "original"
            else:
                with pytest.raises(dividends.DividendRefused) as failure:
                    await asyncio.wait_for(task, 5)
                assert failure.value.code == "authority_unavailable"
            assert not writer.in_transaction()
        finally:
            await blocker.rollback()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    after = await books(factory, ids["user_id"])
    if accepts_current:
        assert after[0] == 101 and len(after[1][0]) == 1 and not after[1][1]
    else:
        assert after == before


@pytest.mark.parametrize("boundary", ["account", "constraints"])
@pytest.mark.parametrize("expires", ["rights", "monitor"])
async def test_actual_clock_expires_during_wait(dividend_case, boundary, expires):
    factory, ids = dividend_case
    before = await books(factory, ids["user_id"])
    async with factory.begin() as db:
        statement = (
            "UPDATE stock_data_admissions SET valid_until=clock_timestamp()+"
            "interval '1 second' WHERE product='actions'"
            if expires == "rights"
            else "UPDATE stock_action_state SET valid_until=clock_timestamp()+interval '1 second' "
            "WHERE coin_id=:coin_id"
        )
        await db.execute(text(statement), ids)
    async with constraint_barrier(factory), scheduler(factory) as writer, factory() as blocker:
        if boundary == "account":
            await blocker.execute(
                text("SELECT user_id FROM accounts WHERE user_id=:user_id FOR UPDATE"), ids
            )
        else:
            await blocker.execute(
                text("SELECT pg_advisory_xact_lock(101008,:u)"), {"u": ids["user_id"]}
            )
        task = asyncio.create_task(dividends.process_dividend(writer, **work(ids)))
        try:
            await waiting(factory, writer.info["pid"], task)
            await blocker.execute(text("SELECT pg_sleep(1.05)"))
            await blocker.rollback()
            with pytest.raises(dividends.DividendRefused):
                await asyncio.wait_for(task, 5)
        finally:
            await blocker.rollback()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert await books(factory, ids["user_id"]) == before


@pytest.mark.parametrize("boundary", ["gate", "account", "constraints"])
@pytest.mark.parametrize("mutation", ["rights", "revision"])
async def test_no_cash_hold_revalidates_after_real_wait(dividend_case, boundary, mutation):
    factory, ids = dividend_case
    original = await process(factory, ids)
    ids = await revise(factory, ids, classification="uncertain", eligible=False)
    before = await books(factory, ids["user_id"])
    async with constraint_barrier(factory), scheduler(factory) as writer, factory() as blocker:
        if boundary == "gate":
            await acquire_stock_gate(blocker, ids["coin_id"])
        elif boundary == "account":
            await blocker.execute(
                text("SELECT user_id FROM accounts WHERE user_id=:user_id FOR UPDATE"), ids
            )
        else:
            await blocker.execute(
                text("SELECT pg_advisory_xact_lock(101008,:u)"), {"u": ids["user_id"]}
            )
        task = asyncio.create_task(
            dividends.record_dividend_hold(
                writer,
                payment_id=original.payment_id,
                expected_revision_fingerprint=ids["revision_fingerprint"],
            )
        )
        try:
            await waiting(factory, writer.info["pid"], task)
            await mutate(factory, ids, mutation)
            await blocker.rollback()
            with pytest.raises(dividends.DividendRefused):
                await asyncio.wait_for(task, 5)
        finally:
            await blocker.rollback()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert await books(factory, ids["user_id"]) == before


async def test_cancellation_during_actual_account_wait_rolls_back(dividend_case):
    factory, ids = dividend_case
    before = await books(factory, ids["user_id"])
    async with scheduler(factory) as writer, factory() as blocker:
        await blocker.execute(
            text("SELECT user_id FROM accounts WHERE user_id=:user_id FOR UPDATE"), ids
        )
        task = asyncio.create_task(dividends.process_dividend(writer, **work(ids)))
        try:
            await waiting(factory, writer.info["pid"], task)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert not writer.in_transaction()
        finally:
            await blocker.rollback()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert await books(factory, ids["user_id"]) == before
    assert (await process(factory, ids)).outcome == "original"


@pytest.mark.parametrize("quantity", [0, 2])
async def test_due_does_not_require_open_market_or_fresh_quote(dividend_case, quantity):
    factory, ids = dividend_case
    async with factory.begin() as db:
        await db.execute(
            text(
                "UPDATE stock_quotes SET event_at=clock_timestamp()-interval "
                "'3 days' WHERE coin_id=:coin_id"
            ),
            ids,
        )
        await db.execute(
            text("UPDATE stock_status_evidence SET state='halted' WHERE coin_id=:coin_id"), ids
        )
        await db.execute(
            text(
                "UPDATE stock_sessions SET opens_at=clock_timestamp()-interval "
                "'2 hours',closes_at=clock_timestamp()-interval '1 hour' "
                "WHERE session_date=current_date"
            )
        )
    assert (await process(factory, ids)).outcome == "original"
    assert (await books(factory, ids["user_id"]))[0] == Decimal(100) + Decimal(quantity) * Decimal(
        ".5"
    )


async def test_numeric_overflow_refuses_without_history(dividend_case):
    factory, ids = dividend_case
    ids = await revise(factory, ids, rate="999999999999")
    before = await books(factory, ids["user_id"])
    with pytest.raises(dividends.DividendRefused) as failure:
        await process(factory, ids)
    assert failure.value.code == "numeric_range"
    assert await books(factory, ids["user_id"]) == before
