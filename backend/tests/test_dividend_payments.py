"""Actual retained entitlement payments through the application transaction owner."""

import asyncio
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import dividends
from tests.test_dividend_authority import authority_case
from tests.test_dividend_schema import dividend_case
from tests.test_stock_action_migrations import ledger

__all__ = ["authority_case", "dividend_case", "ledger"]


async def process(conn, ids, **changes):
    work = {
        "event_id": ids["event_id"],
        "entitlement_id": ids["entitlement_id"],
        "expected_revision_fingerprint": ids["revision_fingerprint"],
        "expected_entitlement_fingerprint": ids["entitlement_fingerprint"],
        **changes,
    }
    await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
    try:
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db:
            return await dividends.process_dividend(db, **work)
    finally:
        await conn.execute(text("RESET ROLE"))


async def cash(conn, ids):
    return (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one()


async def test_due_original_retained_payment_once(authority_case):
    conn, ids = authority_case
    result = await process(conn, ids)
    assert await cash(conn, ids) == Decimal("101"), "A due retained dividend credits cash"
    assert result.outcome == "original" and result.decision_id is None
    assert await process(conn, ids) == result
    assert await cash(conn, ids) == Decimal("101")
    assert (
        await conn.execute(text("SELECT starting_cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal("10000")
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 1
    with pytest.raises(FrozenInstanceError):
        result.payment_id = 42


@pytest.mark.parametrize("day_offset", [0, 1])
async def test_due_uses_new_york_payable_day(authority_case, day_offset):
    conn, ids = authority_case
    await conn.execute(
        text(
            "UPDATE stock_action_revisions SET normalized_terms=jsonb_set("
            "normalized_terms,'{payable_date}',to_jsonb(((clock_timestamp() AT TIME ZONE "
            "'America/New_York')::date+CAST(:offset AS integer))::text)) WHERE id=:revision_id"
        ),
        {**ids, "offset": day_offset},
    )
    if day_offset:
        with pytest.raises(dividends.DividendRefused) as error:
            await process(conn, ids)
        assert error.value.code == "authority_unavailable"
        assert await cash(conn, ids) == Decimal(100)
        assert (
            await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
        ).scalar_one() == 0
    else:
        assert (await process(conn, ids)).outcome == "original"
        assert await cash(conn, ids) == Decimal(101)


@pytest.mark.parametrize("quantity", [0])
async def test_due_verified_zero_ownership_with_positive_rate_is_zero_original(
    authority_case, quantity
):
    conn, ids = authority_case
    result = await process(conn, ids)
    assert result.outcome == "original"
    assert await process(conn, ids) == result
    assert await cash(conn, ids) == Decimal(100)
    assert (
        await conn.execute(
            text("SELECT eligible_quantity,rate,original_amount FROM stock_dividend_payments")
        )
    ).one() == (Decimal(0), Decimal(".5"), Decimal(0))


async def test_due_declared_zero_rate_is_unverified_not_zero_original(authority_case):
    conn, ids = authority_case
    await conn.execute(
        text(
            "UPDATE stock_action_revisions SET normalized_terms=jsonb_set(normalized_terms,"
            "'{rate}','\"0\"'::jsonb)"
        )
    )
    retained = await derive_current(conn, ids)
    assert retained["state"] == "held"
    with pytest.raises(dividends.DividendRefused):
        await process(conn, retained)
    assert await cash(conn, ids) == Decimal(100)
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0


async def derive_current(conn, ids):
    """Use the real retained producer and reviewed calendar, never current Holdings as quantity."""
    from app.models.corporate_action import StockActionRevision, StockDividendEntitlement
    from app.models.stock import StockDataAdmission
    from app.services.corporate_actions import derive_dividend_entitlements
    from app.services.stock_admission import ProductAdmission
    from app.services.stock_sessions import build_sessions

    await conn.execute(
        text(
            "UPDATE stock_instruments SET provider_asset_id='synthetic-dividend-asset',"
            "provider_verified_at=clock_timestamp() WHERE coin_id=:coin_id"
        ),
        ids,
    )
    # Current balance reconciles with the journal; eligibility is reconstructed independently.
    await conn.execute(
        text(
            "INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) "
            "SELECT user_id,coin_id,after_quantity,after_basis FROM stock_ownership_movements "
            "WHERE user_id=:user_id AND coin_id=:coin_id ORDER BY sequence DESC LIMIT 1 "
            "ON CONFLICT (user_id,coin_id) DO NOTHING"
        ),
        ids,
    )
    async with AsyncSession(bind=conn, expire_on_commit=False) as db:
        rv = await db.get(StockActionRevision, ids["revision_id"])
        rv.verified_cutoff = None
        rv.normalized_terms = {
            **rv.normalized_terms,
            "coin_id": ids["coin_id"],
            "symbol": "AAPL",
            "process_date": rv.normalized_terms["ex_date"],
        }
        adm = (
            await db.execute(
                select(StockDataAdmission).where(StockDataAdmission.product == "calendar")
            )
        ).scalar_one()
        cal = ProductAdmission(
            **{f: getattr(adm, f) for f in ProductAdmission.__dataclass_fields__}
        )
        now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
        session = next(
            row
            for row in build_sessions(now, cal)
            if row.exchange == "NASDAQ" and str(row.session_date) == rv.normalized_terms["ex_date"]
        )
        await conn.execute(
            text(
                "INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,"
                "calendar_admission_generation,coverage_start,coverage_end) VALUES ('NASDAQ',"
                ":d,:o,:c,4,:d,:d) "
                "ON CONFLICT (exchange,session_date) DO UPDATE SET opens_at=EXCLUDED.opens_at,"
                "closes_at=EXCLUDED.closes_at"
            ),
            {"d": session.session_date, "o": session.opens_at, "c": session.closes_at},
        )
        result = (await derive_dividend_entitlements(db, ids["event_id"]))[0]
        retained = await db.get(StockDividendEntitlement, result.id)
        await db.flush()
        return {
            **ids,
            "entitlement_id": result.id,
            "entitlement_fingerprint": retained.fingerprint,
            "state": result.state,
            "quantity": result.eligible_quantity,
            "cutoff": result.cutoff,
        }


async def test_due_actual_producer_predecessor_entitlement_and_sold_after_cutoff(
    authority_case, settings
):
    """Producer-owned pre-payment entitlements remain discoverable without any current holding."""
    from app.services.portfolio import get_portfolio

    conn, ids = authority_case
    retained = await derive_current(conn, ids)
    assert retained["state"] == "eligible" and retained["quantity"] == Decimal(2)
    # The durable sale movement follows the actual reconstructed cutoff. No current Holding remains.
    trade = (
        await conn.execute(
            text(
                "INSERT INTO trades(user_id,coin_id,side,input_kind,input_value,quantity,"
                "mid_price,price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key) "
                "VALUES (:user_id,:coin_id,'sell','quantity',2,2,1,clock_timestamp(),1,0,2,100,"
                "gen_random_uuid()) RETURNING id"
            ),
            ids,
        )
    ).scalar_one()
    await conn.execute(
        text(
            "INSERT INTO stock_fill_facts(trade_id,coin_id,user_id,provider_asset_id,symbol,"
            "company_name,listing_exchange,source,feed,bid,ask,exact_mid,held_after,event_at,"
            "collected_at,observed_at,"
            "session_date,opens_at,closes_at,authority) SELECT id,coin_id,user_id,"
            "'synthetic-dividend-asset',"
            "'AAPL','Synthetic company','NASDAQ','alpaca','iex',1,1,1,0,price_as_of,"
            "price_as_of,price_as_of,"
            "price_as_of::date,price_as_of-interval '1 hour',price_as_of+interval '1 hour',"
            "'{}'::jsonb FROM trades WHERE id=:trade"
        ),
        {"trade": trade},
    )
    await conn.execute(
        text(
            "INSERT INTO stock_ownership_movements(coin_id,user_id,sequence,economic_at,"
            "recorded_at,"
            "quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,"
            "cause_kind,trade_id,causal_key) "
            "VALUES (:coin_id,:user_id,2,CAST(:cutoff AS timestamptz)+interval '1 hour',"
            "CAST(:cutoff AS timestamptz)+interval '1 hour',-2,2,0,0,0,0,'fill',:trade,"
            "'synthetic-sold-after')"
        ),
        {**retained, "trade": trade},
    )
    await conn.execute(
        text(
            "UPDATE holdings SET quantity=0,cost_basis=0 WHERE user_id=:user_id AND "
            "coin_id=:coin_id"
        ),
        ids,
    )
    result = await process(conn, retained)
    assert result.outcome == "original" and await cash(conn, ids) == Decimal(101)
    assert await process(conn, retained) == result
    async with AsyncSession(bind=conn) as db:
        portfolio = await get_portfolio(db, user_id=ids["user_id"], settings=settings)
        assert portfolio.cash == Decimal(101) and portfolio.total_value == Decimal(101)
        assert portfolio.starting_cash == Decimal(10000)
    from tests.test_dividend_authority import successor

    revised = await successor(conn, retained)
    await conn.execute(
        text(
            "UPDATE stock_action_revisions SET normalized_terms=jsonb_set("
            "normalized_terms,'{ex_date}',"
            "to_jsonb(((normalized_terms->>'ex_date')::date+1)::text)) WHERE id=:revision_id"
        ),
        revised,
    )
    later_cutoff = await derive_current(conn, revised)
    assert later_cutoff["state"] == "eligible" and later_cutoff["quantity"] == Decimal(0)
    corrected = await process(conn, later_cutoff)
    assert corrected.outcome == "applied" and await cash(conn, ids) == Decimal(100)
    assert (
        await conn.execute(
            text("SELECT original_amount FROM stock_dividend_payments WHERE id=:id"),
            {"id": result.payment_id},
        )
    ).scalar_one() == Decimal(1)


async def test_due_changed_cutoff_reconstructs_history_without_fixed_open_fallback(authority_case):
    from datetime import timedelta

    from tests.test_dividend_authority import successor

    conn, ids = authority_case
    original = await derive_current(conn, ids)
    revised = await successor(conn, original)
    await conn.execute(
        text(
            "UPDATE stock_action_revisions SET normalized_terms=jsonb_set("
            "normalized_terms,'{ex_date}',"
            "to_jsonb(((normalized_terms->>'ex_date')::date+1)::text)) WHERE id=:revision_id"
        ),
        revised,
    )
    newer = await derive_current(conn, revised)
    assert newer["state"] == "eligible" and newer["quantity"] == Decimal(2)
    assert newer["cutoff"] == original["cutoff"] + timedelta(days=1)
    assert newer["entitlement_id"] != original["entitlement_id"]
    assert (await process(conn, newer)).outcome == "original"


async def test_due_latest_held_snapshot_forbids_older_eligible_fallback(authority_case):
    conn, ids = authority_case
    await conn.execute(
        text(
            "INSERT INTO stock_dividend_entitlements(event_id,user_id,revision_id,"
            "cutoff,cutoff_rule,units_basis,unit_epoch,last_movement_sequence,"
            "eligible_quantity,state,"
            "version,supersedes_id,fingerprint) SELECT event_id,user_id,revision_id,cutoff,"
            "cutoff_rule,"
            "units_basis,unit_epoch,last_movement_sequence,0,'held',version+1,id,repeat('c',64) "
            "FROM stock_dividend_entitlements WHERE id=:entitlement_id"
        ),
        ids,
    )
    with pytest.raises(dividends.DividendRefused):
        await process(conn, ids)
    assert await cash(conn, ids) == Decimal(100)


@pytest.mark.parametrize("field", ["event_id", "entitlement_id"])
@pytest.mark.parametrize("value", [True, "1", 0, -1, 9223372036854775808])
async def test_due_strict_bounded_ids_before_sql(authority_case, field, value):
    conn, ids = authority_case
    with pytest.raises(dividends.DividendRefused) as error:
        await process(conn, ids, **{field: value})
    assert error.value.code == "invalid_identity"
    assert await cash(conn, ids) == Decimal(100)


@pytest.mark.parametrize(
    "field", ["expected_revision_fingerprint", "expected_entitlement_fingerprint"]
)
@pytest.mark.parametrize("value", [None, 7, "a" * 65, "A" * 64, "g" * 64])
async def test_due_strict_bounded_fingerprints(authority_case, field, value):
    conn, ids = authority_case
    with pytest.raises(dividends.DividendRefused) as error:
        await process(conn, ids, **{field: value})
    assert error.value.code == "invalid_identity"


@pytest.mark.parametrize(
    "failure,code",
    [
        ("identity", "authority_unavailable"),
        ("overflow", "numeric_range"),
        ("permission", "financial_unavailable"),
    ],
)
async def test_due_real_sql_errors_are_sanitized_and_rolled_back(authority_case, failure, code):
    conn, ids = authority_case
    changes = {}
    if failure == "identity":
        changes["event_id"] = 9223372036854775807
    elif failure == "overflow":
        await conn.execute(
            text("UPDATE accounts SET cash=999999999999.99 WHERE user_id=:user_id"), ids
        )
    else:
        await conn.execute(
            text(
                "REVOKE EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,"
                "text) FROM birja_scheduler"
            )
        )
    before = await cash(conn, ids)
    with pytest.raises(dividends.DividendRefused) as error:
        await process(conn, ids, **changes)
    assert error.value.code == code
    assert str(error.value) == "Dividend work is unavailable."
    assert error.value.__suppress_context__
    assert await cash(conn, ids) == before
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0


async def test_due_active_transaction_refused_without_discarding_caller_work(authority_case):
    conn, ids = authority_case
    async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db:
        await db.execute(text("SELECT 1"))
        with pytest.raises(dividends.DividendRefused) as error:
            await dividends.process_dividend(
                db,
                event_id=ids["event_id"],
                entitlement_id=ids["entitlement_id"],
                expected_revision_fingerprint=ids["revision_fingerprint"],
                expected_entitlement_fingerprint=ids["entitlement_fingerprint"],
            )
        assert error.value.code == "transaction_active" and db.in_transaction()


async def test_due_cancellation_after_actual_sql_rolls_back_cash_and_payment(authority_case):
    conn, ids = authority_case

    class CancelAfterActualSQL(AsyncSession):
        async def execute(self, statement, *args, **kwargs):
            await super().execute(statement, *args, **kwargs)
            raise asyncio.CancelledError

    await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
    try:
        async with CancelAfterActualSQL(bind=conn, join_transaction_mode="create_savepoint") as db:
            with pytest.raises(asyncio.CancelledError):
                await dividends.process_dividend(
                    db,
                    event_id=ids["event_id"],
                    entitlement_id=ids["entitlement_id"],
                    expected_revision_fingerprint=ids["revision_fingerprint"],
                    expected_entitlement_fingerprint=ids["entitlement_fingerprint"],
                )
            assert not db.in_transaction()
    finally:
        await conn.execute(text("RESET ROLE"))
    assert await cash(conn, ids) == Decimal(100)
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0


async def test_due_function_is_final_business_statement_before_commit(authority_case):
    conn, ids = authority_case
    statements = []

    def capture(connection, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(conn.sync_connection, "before_cursor_execute", capture)
    try:
        await process(conn, ids)
    finally:
        event.remove(conn.sync_connection, "before_cursor_execute", capture)
    boundary = next(
        i
        for i, statement in enumerate(statements)
        if "SELECT * FROM public.apply_stock_dividend" in statement
    )
    assert statements[boundary + 1].startswith("RELEASE SAVEPOINT")
    assert statements[boundary + 2 :] == ["RESET ROLE"]


async def test_original_replay_after_rights_loss_and_symbol_rename(authority_case):
    conn, ids = authority_case
    result = await process(conn, ids)
    original = (
        await conn.execute(text("SELECT row_to_json(p) FROM stock_dividend_payments p"))
    ).scalar_one()
    await conn.execute(text("UPDATE stock_data_admissions SET state='denied'"))
    await conn.execute(
        text("UPDATE coins SET symbol='RENAMED',name='Renamed' WHERE id=:coin_id"), ids
    )
    await conn.execute(text("UPDATE stock_action_state SET health='unknown',epoch=epoch+1"))
    assert await process(conn, ids) == result
    assert (
        await conn.execute(text("SELECT row_to_json(p) FROM stock_dividend_payments p"))
    ).scalar_one() == original
    assert await cash(conn, ids) == Decimal("101")
