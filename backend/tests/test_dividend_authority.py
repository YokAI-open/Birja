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


async def test_acl_bootstrap_accepts_exact_current_authority(engine, migrated):
    import asyncio
    import subprocess
    from pathlib import Path

    root = await asyncio.to_thread(lambda: Path(__file__).resolve().parents[2])
    script = await asyncio.to_thread((root / "deploy/db/bootstrap-roles.sql").read_text)
    matrix = """SELECT CASE WHEN
      has_function_privilege('birja_scheduler',
        'public.apply_stock_dividend(bigint,bigint,text,text)','EXECUTE') AND
      has_function_privilege('birja_scheduler',
        'public.record_stock_dividend_hold(bigint,text)','EXECUTE') AND NOT
      has_function_privilege('birja_app',
        'public.apply_stock_dividend(bigint,bigint,text,text)','EXECUTE') AND NOT
      has_function_privilege('birja_scheduler',
        'public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)','EXECUTE') AND NOT
      has_column_privilege('birja_scheduler','accounts','cash','UPDATE') AND
      has_table_privilege('birja_app','stock_dividend_payments','SELECT') AND
      has_table_privilege('birja_scheduler','stock_dividend_payments','SELECT') AND NOT
      has_table_privilege('birja_scheduler','stock_dividend_payments','INSERT') AND NOT
      has_sequence_privilege('birja_scheduler','stock_dividend_payments_id_seq','USAGE')
      THEN 'dividend_bootstrap_ok' ELSE 'unsafe_bootstrap' END;
      ROLLBACK;
    """
    script = script.rsplit("COMMIT;", 1)[0] + matrix
    result = await asyncio.to_thread(
        subprocess.run,
        [
            "docker",
            "compose",
            "-f",
            str(root / "docker-compose.test.yml"),
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "birja_test",
            "-d",
            "birja_test",
            "-XqAt",
            "-v",
            "ON_ERROR_STOP=1",
            "-v",
            "bootstrap=birja_test",
            "-v",
            "apply=true",
            "-v",
            "db_name=birja_test",
            "-v",
            "app_password=test-only-app",
            "-v",
            "scheduler_password=test-only-scheduler",
            "-v",
            "migrator_password=test-only-migrator",
        ],
        input=script,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "dividend_bootstrap_ok"


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


async def test_scheduler_boundary_reconciled_successor_preserves_held_original(authority_case):
    conn, ids = authority_case
    original = await apply(conn, ids)
    uncertain = await successor(conn, ids, classification="uncertain", eligible=False)
    held = await hold(conn, original["payment_id"], uncertain["revision_fingerprint"])
    corrected = await successor(conn, uncertain, rate="0.75")
    # Retained reviewed reconciliation has its independent operator-only proof.
    # This is synthetic external/review evidence, never a financial bypass.
    await conn.execute(
        text("""INSERT INTO stock_action_resolutions(event_id,coin_id,
      expected_revision,admission_generation,epoch,decision,decision_key,evidence,
      evidence_hash,before_digest,after_digest,actor_ref,created_at)
      SELECT :event_id,:coin_id,:revision_id,4,3,'accept_corrected_supported_revision',
      'synthetic-dividend-reconciliation',jsonb_build_object('format',1,'held_revision_ids',
      (SELECT jsonb_agg(r.id ORDER BY r.id) FROM stock_action_revisions r
       WHERE r.event_id=:event_id)),repeat('a',64),repeat('b',64),repeat('c',64),
      'synthetic-reviewed-operator',clock_timestamp()"""),
        corrected,
    )
    result = await apply(conn, corrected)
    assert result["outcome"] == "applied" and await apply(conn, corrected) == result
    row = (
        await conn.execute(
            text("""SELECT previous_decision_id,applied_delta FROM
      stock_dividend_decisions WHERE id=:d"""),
            {"d": result["decision_id"]},
        )
    ).one()
    assert tuple(row) == (held["decision_id"], Decimal(".5"))
    assert (
        await conn.execute(text("SELECT original_amount FROM stock_dividend_payments"))
    ).scalar_one() == Decimal(1)
    assert (
        await conn.execute(
            text("SELECT outcome,applied_delta FROM stock_dividend_decisions WHERE id=:d"),
            {"d": held["decision_id"]},
        )
    ).one() == ("held_uncertain", Decimal(0))


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
        "UPDATE stock_data_admissions SET calendar=jsonb_set(calendar,'{sources}',"
        "'[\"https://evil.test/\",\"https://www.nyse.com/\"]'::jsonb) WHERE product='calendar'",
        "UPDATE stock_data_admissions SET calendar=jsonb_set(calendar,'{overrides}',"
        '\'[{"exchange":"XNYS","date":"2026-11-12","state":"unknown",'
        '"source":"https://www.nyse.com/"}]\'::jsonb) WHERE product=\'calendar\'',
        "UPDATE stock_data_admissions SET scope=jsonb_set(scope,'{capabilities}',"
        "'[\"rest\",\"arbitrary\"]'::jsonb) WHERE product='actions'",
        "UPDATE stock_data_admissions SET scope=scope-'all_us_replay_ingress' "
        "WHERE product='actions'",
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


@pytest.mark.parametrize("role", ["birja_app", "birja_scheduler"])
async def test_acl_direct_write_and_private_helper_denials(authority_case, role):
    conn, ids = authority_case
    await apply(conn, ids)
    async with conn.begin_nested():
        await conn.execute(text(f"SET LOCAL ROLE {role}"))
        for statement in (
            "UPDATE public.accounts SET cash=999999",
            "INSERT INTO public.stock_dividend_payments(event_id) VALUES (1)",
            "INSERT INTO public.stock_dividend_decisions(payment_id) VALUES (1)",
            "UPDATE public.stock_dividend_payments SET original_amount=0",
            "DELETE FROM public.stock_dividend_decisions",
            "SELECT public.stock_dividend_authority(1,1,'a','b',false,NULL)",
            "DROP FUNCTION public.record_stock_dividend_hold(bigint,text)",
            "ALTER FUNCTION public.apply_stock_dividend(bigint,bigint,text,text) "
            "OWNER TO birja_scheduler",
            "ALTER TABLE public.stock_dividend_payments DISABLE TRIGGER stock_dividend_immutable",
            "CREATE FUNCTION public.apply_stock_dividend(bigint,bigint,text,text) "
            "RETURNS void LANGUAGE SQL AS 'SELECT 1'",
            "CREATE TABLE public.accounts_shadow(user_id bigint,cash numeric)",
        ):
            with pytest.raises(DBAPIError) as error:
                async with conn.begin_nested():
                    await conn.execute(text(statement))
            assert error.value.orig.sqlstate == "42501", statement
        if role == "birja_app":
            for statement in (
                "SELECT public.apply_stock_dividend(1,1,'a','b')",
                "SELECT public.record_stock_dividend_hold(1,'a')",
            ):
                with pytest.raises(DBAPIError) as error:
                    async with conn.begin_nested():
                        await conn.execute(text(statement))
                assert error.value.orig.sqlstate == "42501"
        await conn.execute(text("RESET ROLE"))


async def test_acl_function_identity_exact_and_public_cannot_execute(authority_case):
    import hashlib
    import re

    conn, _ = authority_case
    module = migration()
    for signature, body, definer in (
        (module.APPLY_SIGNATURE, module.APPLY, True),
        (module.HOLD_SIGNATURE, module.HOLD, True),
        (module.AUTHORITY_SIGNATURE, module.AUTHORITY, False),
        ("public.reject_stock_dividend_mutation()", module.IMMUTABILITY, False),
    ):
        row = (
            await conn.execute(
                text("""SELECT pg_get_userbyid(proowner) AS owner,
              prosrc,provolatile::text,prosecdef,proconfig FROM pg_proc
              WHERE oid=to_regprocedure(:s)"""),
                {"s": signature},
            )
        ).one()
        assert row.owner == "birja_migrator" and row.provolatile == "v" and row.prosecdef == definer
        assert row.proconfig == ["search_path=pg_catalog, public, pg_temp"]
        expected = re.search(r"AS \$[a-z]+\$(.*?)\$[a-z]+\$", body, re.S)[1]
        assert (
            hashlib.sha256(row.prosrc.encode()).digest()
            == hashlib.sha256(expected.encode()).digest()
        )
    await conn.execute(text("CREATE ROLE birja_dividend_public_test NOLOGIN NOINHERIT"))
    await conn.execute(text("GRANT USAGE ON SCHEMA public TO birja_dividend_public_test"))
    async with conn.begin_nested():
        await conn.execute(text("SET LOCAL ROLE birja_dividend_public_test"))
        for statement in (
            "SELECT public.apply_stock_dividend(1,1,'a','b')",
            "SELECT public.record_stock_dividend_hold(1,'a')",
            "SELECT public.stock_dividend_authority(1,1,'a','b',false,NULL)",
        ):
            with pytest.raises(DBAPIError) as error:
                async with conn.begin_nested():
                    await conn.execute(text(statement))
            assert error.value.orig.sqlstate == "42501"
        await conn.execute(text("RESET ROLE"))


async def test_identity_bootstrap_refuses_tampered_body_and_public_acl(authority_case):
    import asyncio
    from pathlib import Path

    conn, _ = authority_case
    source = await asyncio.to_thread(
        lambda: (Path(__file__).resolve().parents[2] / "deploy/db/bootstrap-roles.sql").read_text()
    )
    guard = source[source.index("DO $dividend_identity$") : source.index("\\if :apply")]
    await conn.execute(text(guard))
    for statement in (
        "ALTER FUNCTION public.apply_stock_dividend(bigint,bigint,text,text) SECURITY INVOKER",
        "GRANT EXECUTE ON FUNCTION public.record_stock_dividend_hold(bigint,text) TO PUBLIC",
        "ALTER FUNCTION public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb) "
        "SET search_path=public,pg_temp",
        "ALTER FUNCTION public.record_stock_dividend_hold(bigint,text) OWNER TO birja_test",
        "ALTER FUNCTION public.record_stock_dividend_hold(bigint,text) STABLE",
        migration()
        .HOLD.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION")
        .replace("status:='epoch:'", "status:='forged:'"),
    ):
        async with conn.begin_nested() as outer:
            await conn.execute(text(statement))
            with pytest.raises(DBAPIError, match="authority mismatch"):
                async with conn.begin_nested():
                    await conn.execute(text(guard))
            await outer.rollback()


@pytest.mark.parametrize("change", ["closed", "shortened", "coverage"])
async def test_current_admitted_calendar_semantics_refuse_stale_eligibility(authority_case, change):
    from dataclasses import fields
    from datetime import datetime, time
    from zoneinfo import ZoneInfo

    from app.services.stock_admission import ProductAdmission, evaluate_admission
    from app.services.stock_sessions import build_sessions

    conn, ids = authority_case
    row = dict(
        (await conn.execute(text("SELECT * FROM stock_data_admissions WHERE product='calendar'")))
        .mappings()
        .one()
    )
    rv = (
        await conn.execute(
            text("SELECT normalized_terms FROM stock_action_revisions WHERE id=:revision_id"), ids
        )
    ).scalar_one()
    cal = dict(row["calendar"])
    ex_date = rv["ex_date"]
    if change == "coverage":
        now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
        cal["coverage_start"] = str(now.date())
    else:
        override = {
            "exchange": "XNAS",
            "date": ex_date,
            "state": change,
            "source": "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
        }
        if change == "shortened":
            day = datetime.fromisoformat(ex_date).date()
            override.update(
                opens_at=datetime.combine(
                    day, time(9, 30), ZoneInfo("America/New_York")
                ).isoformat(),
                closes_at=datetime.combine(day, time(13), ZoneInfo("America/New_York")).isoformat(),
            )
        cal["overrides"] = [override]
    row["calendar"] = cal
    admission = ProductAdmission(**{f.name: row[f.name] for f in fields(ProductAdmission)})
    now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
    assert evaluate_admission(admission, "calendar", "derived", now).allowed
    sessions = build_sessions(now, admission)
    expected = [s for s in sessions if s.exchange == "NASDAQ" and str(s.session_date) == ex_date]
    if change == "coverage":
        assert not expected
    elif change == "closed":
        assert len(expected) == 1 and expected[0].opens_at is None
    else:
        assert len(expected) == 1 and expected[0].opens_at is not None
        cached = (await conn.execute(text("SELECT opens_at FROM stock_sessions"))).scalar_one()
        assert expected[0].opens_at != cached
    await conn.execute(
        text(
            "UPDATE stock_data_admissions SET calendar=CAST(:c AS jsonb) WHERE product='calendar'"
        ),
        {"c": json.dumps(cal)},
    )
    with pytest.raises(DBAPIError):
        await apply(conn, ids)
    assert (
        await conn.execute(text("SELECT cash FROM accounts WHERE user_id=:user_id"), ids)
    ).scalar_one() == Decimal(100)
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_decisions"))
    ).scalar_one() == 0


@pytest.mark.parametrize("declaration", ["type", "name", "mode"])
async def test_identity_preflight_refuses_altered_out_declaration(authority_case, declaration):
    import asyncio
    from pathlib import Path

    conn, _ = authority_case
    definition = migration().APPLY
    if declaration == "type":
        definition = definition.replace(
            "RETURNS TABLE(payment_id bigint,", "RETURNS TABLE(payment_id text,"
        )
    elif declaration == "name":
        definition = definition.replace(
            "RETURNS TABLE(payment_id bigint,", "RETURNS TABLE(payment_reference bigint,"
        )
    else:
        definition = definition.replace(
            "p_event bigint,p_entitlement bigint,p_revision text,p_fingerprint text)",
            "p_event bigint,p_entitlement bigint,p_revision text,p_fingerprint text,"
            "OUT payment_id bigint,OUT decision_id bigint,OUT outcome text)",
        )
        definition = definition.replace(
            "RETURNS TABLE(payment_id bigint,decision_id bigint,outcome text)",
            "RETURNS SETOF record",
        )
    assert definition != migration().APPLY
    await conn.execute(text("DROP FUNCTION public.apply_stock_dividend(bigint,bigint,text,text)"))
    await conn.execute(text(definition))
    await conn.execute(
        text(
            "ALTER FUNCTION public.apply_stock_dividend(bigint,bigint,text,text) OWNER TO birja_migrator"
        )
    )
    await conn.execute(
        text(
            "REVOKE ALL ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text) FROM PUBLIC"
        )
    )
    await conn.execute(
        text(
            "GRANT EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text) TO birja_scheduler"
        )
    )
    source = await asyncio.to_thread(
        lambda: (Path(__file__).resolve().parents[2] / "deploy/db/bootstrap-roles.sql").read_text()
    )
    guard = source[source.index("DO $dividend_identity$") : source.index("\\if :apply")]
    with pytest.raises(DBAPIError, match="authority mismatch"):
        async with conn.begin_nested():
            await conn.execute(text(guard))
