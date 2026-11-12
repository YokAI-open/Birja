"""Actual PostgreSQL dividend authority and hostile restricted callers."""

import json
from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.test_dividend_rules import TARGET_VECTORS
from tests.test_dividend_schema import dividend_case, migration
from tests.test_stock_action_migrations import ledger
from tests.test_stock_admission import action_admitted, admitted
from tests.test_stock_sessions import evidence

__all__ = ["ledger", "dividend_case"]


async def test_scheduler_boundary_requires_narrow_authority(engine, migrated):
    async with engine.connect() as conn:
        assert (
            await conn.execute(
                text(
                    "SELECT to_regprocedure("
                    "'public.apply_stock_dividend(bigint,bigint,text,text)') "
                    "IS NOT NULL AND to_regprocedure("
                    "'public.record_stock_dividend_hold(bigint,text)') "
                    "IS NOT NULL"
                )
            )
        ).scalar_one(), "Scheduler needs both narrow retained-row financial authorities"


@pytest_asyncio.fixture
async def authority_case(dividend_case, request):
    conn, ids = dividend_case
    await conn.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
    for role in ("birja_app", "birja_scheduler"):
        await conn.execute(text(f"CREATE ROLE {role} NOLOGIN NOINHERIT"))
    await conn.execute(
        text("GRANT USAGE ON SCHEMA public TO birja_migrator,birja_scheduler,birja_app")
    )
    await conn.execute(
        text("""GRANT SELECT ON stock_action_events,stock_action_revisions,
      stock_action_observations,stock_action_resolutions,stock_action_state,stock_instruments,
      coins,stock_data_admissions,stock_sessions,stock_ownership_movements,stock_split_applications,
      stock_dividend_entitlements,stock_dividend_payments,
      stock_dividend_decisions,accounts TO birja_migrator""")
    )
    await conn.execute(
        text("GRANT INSERT ON stock_dividend_payments,stock_dividend_decisions TO birja_migrator")
    )
    await conn.execute(
        text(
            "GRANT USAGE ON SEQUENCE stock_dividend_payments_id_seq,"
            "stock_dividend_decisions_id_seq TO birja_migrator"
        )
    )
    await conn.execute(text("GRANT UPDATE(cash) ON accounts TO birja_migrator"))
    await conn.execute(
        text(
            "GRANT EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text),"
            "public.record_stock_dividend_hold(bigint,text) TO birja_scheduler"
        )
    )
    await conn.execute(text(migration().GRANTS))
    now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
    params = getattr(getattr(request.node, "callspec", None), "params", {})
    quantity = Decimal(params.get("quantity", 2))
    for authority in (admitted("reference"), action_admitted(), evidence(now)):
        authority = replace(
            authority,
            reviewed_at=now - timedelta(hours=1),
            valid_from=now - timedelta(hours=1),
            valid_until=now + timedelta(hours=1),
            scope={
                **authority.scope,
                "durable_accounting": True,
                "backup_restore": True,
                "retention_mode": "durable-accounting",
            },
        )
        values = asdict(authority)
        for field in ("scope", "quota", "allowed_fields", "calendar"):
            values[field] = json.dumps(values[field])
        cols = list(values)
        expressions = [
            f"CAST(:{k} AS jsonb)"
            if k in ("scope", "quota", "allowed_fields", "calendar")
            else f":{k}"
            for k in cols
        ]
        await conn.execute(
            text(
                f"INSERT INTO stock_data_admissions ({','.join(cols)}) "  # noqa: S608 - fixed dataclass fields
                f"VALUES ({','.join(expressions)})"
            ),
            values,
        )
    await conn.execute(
        text("INSERT INTO accounts(user_id,cash,starting_cash) VALUES (:user_id,100,10000)"), ids
    )
    await conn.execute(
        text("""INSERT INTO stock_action_state(coin_id,admission_generation,
      health,checked_at,valid_until,journal_start_at,complete_from,coverage_start,covered_until)
      VALUES (:coin_id,4,'current',clock_timestamp()-interval '1 hour',
      clock_timestamp()+interval '1 hour',
      clock_timestamp()-interval '10 days',clock_timestamp()-interval '10 days',
      clock_timestamp()-interval '10 days',clock_timestamp())"""),
        ids,
    )
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
        "ex_date": str(now.date() - timedelta(days=3)),
        "record_date": str(now.date() - timedelta(days=2)),
        "payable_date": str(now.date() - timedelta(days=1)),
    }
    await conn.execute(
        text("""UPDATE stock_action_revisions SET classification='supported_dividend',
      normalized_terms=CAST(:terms AS jsonb),admission_generation=4,
      verified_cutoff=clock_timestamp()-interval '3 days' WHERE id=:revision_id"""),
        {**ids, "terms": json.dumps(terms)},
    )
    await conn.execute(
        text("""UPDATE stock_dividend_entitlements SET
      cutoff=(SELECT verified_cutoff FROM stock_action_revisions WHERE id=:revision_id),
      cutoff_rule='exclusive-regular-session-open',units_basis='unit_epoch:0',
      eligible_quantity=:quantity,last_movement_sequence=:sequence WHERE id=:entitlement_id"""),
        {**ids, "quantity": quantity, "sequence": 1 if quantity else 0},
    )
    if quantity:
        await conn.execute(
            text("""INSERT INTO stock_ownership_movements(coin_id,user_id,sequence,
          economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,
          unit_epoch,cause_kind,causal_key)
          SELECT :coin_id,:user_id,1,cutoff-interval '1 day',clock_timestamp(),
          :quantity,0,:quantity,0,0,0,'opening','synthetic-dividend-opening'
          FROM stock_dividend_entitlements WHERE id=:entitlement_id"""),
            {**ids, "quantity": quantity},
        )
    await conn.execute(
        text("""INSERT INTO stock_sessions(exchange,session_date,opens_at,
      closes_at,calendar_admission_generation,coverage_start,coverage_end)
      SELECT i.listing_exchange,(r.normalized_terms->>'ex_date')::date,en.cutoff,
        en.cutoff+interval '6 hours',4,(r.normalized_terms->>'ex_date')::date,
        (r.normalized_terms->>'ex_date')::date
      FROM stock_instruments i JOIN stock_action_revisions r ON r.id=:revision_id
      JOIN stock_dividend_entitlements en ON en.id=:entitlement_id WHERE i.coin_id=:coin_id"""),
        ids,
    )
    yield conn, ids


async def apply(conn, ids):
    async with conn.begin_nested():
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        row = (
            (
                await conn.execute(
                    text(
                        "SELECT * FROM public.apply_stock_dividend(:event_id,:entitlement_id,"
                        ":revision_fingerprint,:entitlement_fingerprint)"
                    ),
                    ids,
                )
            )
            .mappings()
            .one()
        )
        await conn.execute(text("RESET ROLE"))
        return dict(row)


async def test_scheduler_boundary_real_credit_and_original_replay(authority_case):
    conn, ids = authority_case
    result = await apply(conn, ids)
    assert result["outcome"] == "original" and result["decision_id"] is None
    assert (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal(101)
    await conn.execute(text("UPDATE stock_data_admissions SET state='denied'"))
    assert await apply(conn, ids) == result
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 1


@pytest.mark.parametrize("quantity,rate,expected", TARGET_VECTORS)
async def test_half_even_sql_matches_literal_python_vectors(
    authority_case, quantity, rate, expected
):
    conn, ids = authority_case
    await conn.execute(text("UPDATE accounts SET cash=0 WHERE user_id=:user_id"), ids)
    await conn.execute(
        text(
            "UPDATE stock_dividend_entitlements SET eligible_quantity=:q WHERE id=:entitlement_id"
        ),
        {**ids, "q": quantity},
    )
    await conn.execute(
        text(
            "UPDATE stock_action_revisions SET normalized_terms=jsonb_set("
            "normalized_terms,'{rate}',to_jsonb(CAST(:r AS text))) WHERE id=:revision_id"
        ),
        {**ids, "r": str(rate)},
    )
    await apply(conn, ids)
    assert (
        await conn.execute(text("SELECT original_amount FROM stock_dividend_payments"))
    ).scalar_one() == Decimal(expected)


@pytest.mark.parametrize(
    "field", ["event_id", "entitlement_id", "revision_fingerprint", "entitlement_fingerprint"]
)
async def test_scheduler_boundary_forged_identity_refused(authority_case, field):
    conn, ids = authority_case
    bad = {**ids, field: "f" * 64 if field.endswith("fingerprint") else 9223372036854775807}
    with pytest.raises(DBAPIError):
        await apply(conn, bad)
    assert (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal(100)
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0


async def test_shadow_temporary_objects_cannot_mint_cash(authority_case):
    conn, ids = authority_case
    await conn.execute(text("CREATE TEMP TABLE accounts(user_id bigint,cash numeric)"))
    await conn.execute(text("INSERT INTO pg_temp.accounts VALUES (:user_id,999999)"), ids)
    await conn.execute(text("CREATE TEMP TABLE stock_data_admissions(product text,state text)"))
    await conn.execute(text("SET LOCAL search_path=pg_temp,public,pg_catalog"))
    await apply(conn, ids)
    assert (
        await conn.execute(text("SELECT cash FROM public.accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal(101)
    assert (await conn.execute(text("SELECT cash FROM pg_temp.accounts"))).scalar_one() == Decimal(
        999999
    )


async def successor(conn, ids, *, rate="0.75", classification="supported_dividend", eligible=True):
    """Append synthetic external evidence; actual accounting is never mocked."""
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
                text("""INSERT INTO stock_dividend_entitlements(event_id,user_id,
          revision_id,cutoff,cutoff_rule,units_basis,unit_epoch,last_movement_sequence,
          eligible_quantity,state,version,supersedes_id,fingerprint)
          SELECT event_id,user_id,:r,cutoff,cutoff_rule,units_basis,unit_epoch,
          last_movement_sequence,
          eligible_quantity,'eligible',version+1,id,:f FROM stock_dividend_entitlements
          WHERE id=:entitlement_id RETURNING id"""),
                {**ids, "r": rid, "f": efp},
            )
        ).scalar_one()
        new.update(entitlement_id=eid, entitlement_fingerprint=efp)
    return new


async def hold(conn, payment, revision):
    async with conn.begin_nested():
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        result = dict(
            (
                await conn.execute(
                    text("SELECT * FROM public.record_stock_dividend_hold(:p,:r)"),
                    {"p": payment, "r": revision},
                )
            )
            .mappings()
            .one()
        )
        await conn.execute(text("RESET ROLE"))
        return result


async def test_scheduler_boundary_a_b_a_and_nochange_append_immutable_lineage(authority_case):
    conn, ids = authority_case
    original = await apply(conn, ids)
    b = await successor(conn, ids)
    changed = await apply(conn, b)
    assert changed["outcome"] == "applied"
    assert await apply(conn, b) == changed
    a = await successor(conn, b, rate="0.5")
    again = await apply(conn, a)
    unchanged = await successor(conn, a, rate="0.5")
    nothing = await apply(conn, unchanged)
    assert again["outcome"] == "applied" and nothing["outcome"] == "verified_no_change"
    rows = (
        await conn.execute(
            text(
                "SELECT applied_delta,cumulative_applied_before,previous_decision_id "
                "FROM stock_dividend_decisions ORDER BY id"
            )
        )
    ).all()
    assert [r.applied_delta for r in rows] == [Decimal(".5"), Decimal("-.5"), Decimal(0)]
    assert [r.cumulative_applied_before for r in rows] == [Decimal(1), Decimal("1.5"), Decimal(1)]
    assert rows[1].previous_decision_id == changed["decision_id"]
    assert (
        await conn.execute(
            text("SELECT original_amount FROM stock_dividend_payments WHERE id=:p"),
            {"p": original["payment_id"]},
        )
    ).scalar_one() == Decimal(1)
    assert (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal(101)


async def test_scheduler_boundary_unaffordable_hold_then_successor(authority_case):
    conn, ids = authority_case
    await apply(conn, ids)
    revised = await successor(conn, ids, rate=".1")
    await conn.execute(text("UPDATE accounts SET cash=.79 WHERE user_id=:user_id"), ids)
    held = await apply(conn, revised)
    assert held["outcome"] == "held_unaffordable" and await apply(conn, revised) == held
    await conn.execute(text("UPDATE accounts SET cash=.80 WHERE user_id=:user_id"), ids)
    paid = await apply(conn, revised)
    assert paid["outcome"] == "applied"
    assert (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal(0)
    assert (
        await conn.execute(
            text("SELECT previous_decision_id FROM stock_dividend_decisions WHERE id=:d"),
            {"d": paid["decision_id"]},
        )
    ).scalar_one() == held["decision_id"]


@pytest.mark.parametrize("classification", ["cancelled", "uncertain"])
async def test_scheduler_boundary_paid_then_uncertain_without_eligible_snapshot(
    authority_case, classification
):
    conn, ids = authority_case
    original = await apply(conn, ids)
    revised = await successor(conn, ids, classification=classification, eligible=False)
    result = await hold(conn, original["payment_id"], revised["revision_fingerprint"])
    assert result["outcome"] == "held_uncertain"
    assert await hold(conn, original["payment_id"], revised["revision_fingerprint"]) == result
    row = (
        await conn.execute(
            text(
                "SELECT entitlement_id,desired_total,proposed_delta,applied_delta "
                "FROM stock_dividend_decisions"
            )
        )
    ).one()
    assert tuple(row) == (None, None, None, Decimal(0))
    assert (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal(101)


async def test_scheduler_boundary_no_anchor_or_healthy_target_cannot_hold(authority_case):
    conn, ids = authority_case
    with pytest.raises(DBAPIError):
        await hold(conn, 9223372036854775807, ids["revision_fingerprint"])
    result = await apply(conn, ids)
    with pytest.raises(DBAPIError, match="needs uncertainty"):
        await hold(conn, result["payment_id"], ids["revision_fingerprint"])


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE stock_dividend_entitlements SET eligible_quantity=3",
        "UPDATE stock_dividend_entitlements SET cutoff=cutoff+interval '1 second'",
        "UPDATE stock_dividend_entitlements SET units_basis='shares'",
        "UPDATE stock_dividend_entitlements SET last_movement_sequence=99",
        "UPDATE stock_action_state SET health='unknown'",
        "UPDATE stock_data_admissions SET scope=scope-'backup_restore' WHERE product='actions'",
        "UPDATE stock_data_admissions SET valid_until=clock_timestamp()-interval '1 second'",
        "UPDATE stock_sessions SET calendar_admission_generation=5",
    ],
)
async def test_scheduler_boundary_unverified_retained_work_refuses_no_cash(authority_case, sql):
    conn, ids = authority_case
    await conn.execute(text(sql))
    with pytest.raises(DBAPIError):
        await apply(conn, ids)
    assert (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal(100)
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0


async def test_scheduler_boundary_actual_producer_snapshot_without_split_cutoff(authority_case):
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.corporate_action import StockActionRevision, StockDividendEntitlement
    from app.models.stock import StockDataAdmission
    from app.services.corporate_actions import derive_dividend_entitlements
    from app.services.stock_admission import ProductAdmission
    from app.services.stock_sessions import build_sessions

    conn, ids = authority_case
    await conn.execute(
        text(
            "UPDATE stock_instruments SET provider_asset_id='synthetic-dividend-asset',"
            "provider_verified_at=clock_timestamp() WHERE coin_id=:coin_id"
        ),
        ids,
    )
    await conn.execute(
        text(
            "INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) "
            "VALUES (:user_id,:coin_id,2,0)"
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
        rows = build_sessions(now, cal)
        selected = next(
            r
            for r in rows
            if r.exchange == "NASDAQ" and str(r.session_date) == rv.normalized_terms["ex_date"]
        )
        await conn.execute(
            text("UPDATE stock_sessions SET opens_at=:o,closes_at=:c"),
            {"o": selected.opens_at, "c": selected.closes_at},
        )
        # Recompute from existing immutable opening movement, using real calendar.
        result = (await derive_dividend_entitlements(db, ids["event_id"]))[0]
        assert result.state == "eligible"
        assert result.eligible_quantity == Decimal(2)
        assert rv.verified_cutoff is None
        retained = await db.get(StockDividendEntitlement, result.id)
        actual = {
            **ids,
            "entitlement_id": result.id,
            "entitlement_fingerprint": retained.fingerprint,
        }
        await db.flush()
        assert (await apply(conn, actual))["outcome"] == "original"
