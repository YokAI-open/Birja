"""Actual restricted PostgreSQL roles and final execution authority."""

import json

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.test_stock_action_migrations import runtime_roles as _runtime_roles

runtime_roles = _runtime_roles


@pytest_asyncio.fixture
async def guard_case(engine, migrated, new_user, request):
    from tests.test_stock_execution_migrations import complete_receipt

    uid = await new_user()
    async with engine.connect() as conn:
        tx = await conn.begin()
        cid = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
        await conn.execute(
            text("""UPDATE stock_instruments SET provider_asset_id='fixture-asset',
        provider_verified_at=CAST(:n AS timestamptz) WHERE coin_id=:c"""),
            {"n": now, "c": cid},
        )
        for product in ("reference", "quotes", "actions", "status", "calendar"):
            await conn.execute(
                text("""INSERT INTO stock_data_admissions
            (product,state,generation,reviewed_at,valid_from,valid_until,evidence_ref,terms_version,
             collection_allowed,display_allowed,derived_allowed,retention_allowed,calendar)
            VALUES (:p,'approved',1,CAST(:n AS timestamptz),
            CAST(:n AS timestamptz)-interval '1 hour',CAST(:n AS timestamptz)+interval '1 hour',
            'synthetic-only','fixture',true,true,true,true,
            CASE WHEN :p='calendar' THEN jsonb_build_object(
            'review_valid_until',CAST(:n AS timestamptz)+interval '1 hour')
            ELSE '{}'::jsonb END)"""),
                {"p": product, "n": now},
            )
        await conn.execute(
            text("""INSERT INTO stock_quotes
        (coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation,unit_epoch)
        VALUES (:c,10,10,10,'alpaca','iex',CAST(:n AS timestamptz),
        CAST(:n AS timestamptz),CAST(CAST(:n AS timestamptz) AS date),1,0)"""),
            {"c": cid, "n": now},
        )
        await conn.execute(
            text("""INSERT INTO stock_sessions
        (exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation)
        SELECT listing_exchange,CAST(CAST(:n AS timestamptz) AS date),
        CAST(:n AS timestamptz)-interval '1 hour',CAST(:n AS timestamptz)+interval '1 hour',
        CAST(CAST(:n AS timestamptz) AS date),CAST(CAST(:n AS timestamptz) AS date),1
        FROM stock_instruments WHERE coin_id=:c"""),
            {"c": cid, "n": now},
        )
        lease = getattr(request, "param", 60)
        await conn.execute(
            text("""INSERT INTO stock_status_evidence
        (coin_id,provider_asset_id,state,event_at,observed_at,session_date,admission_generation,
         continuity_generation,sequence,valid_until,bootstrap_verified,continuity_current,source_ref)
        VALUES (:c,'fixture-asset','normal',CAST(:n AS timestamptz),CAST(:n AS timestamptz),
        CAST(CAST(:n AS timestamptz) AS date),1,1,1,
        CAST(:n AS timestamptz)+:lease*interval '1 second',
        true,true,'synthetic-only')"""),
            {"c": cid, "n": now, "lease": lease},
        )
        await conn.execute(
            text("""INSERT INTO stock_action_state
        (coin_id,health,admission_generation,checked_at,valid_until,coverage_start,covered_until)
        VALUES (:c,'current',1,CAST(:n AS timestamptz),CAST(:n AS timestamptz)+interval '1 hour',
        CAST(:n AS timestamptz)-interval '1 day',CAST(:n AS timestamptz))"""),
            {"c": cid, "n": now},
        )
        snapshot = (
            await conn.execute(
                text("""SELECT jsonb_build_object(
        'coin_id',i.coin_id,'provider_asset_id',i.provider_asset_id,
        'admissions',(SELECT jsonb_agg(jsonb_build_object('product',product,'generation',generation,
          'row_hash',encode(sha256(convert_to(to_jsonb(a)::text,'UTF8')),'hex'),
          'valid_from',valid_from,'valid_until',valid_until,'approved',true) ORDER BY product)
          FROM stock_data_admissions a),
        'action_current',true,'action_valid_until',ac.valid_until,'next_blocking_at',null,
        'safety_epoch',ac.epoch,'unit_epoch',ac.unit_epoch,'status',to_jsonb(st),
        'session_state','open','session_date',se.session_date,'opens_at',se.opens_at,
        'closes_at',se.closes_at,'session_valid_until',ac.valid_until,
        'calendar_generation',se.calendar_admission_generation,
        'quote',(to_jsonb(q)-'mid')||jsonb_build_object('provider_asset_id',i.provider_asset_id))
        FROM stock_instruments i JOIN stock_quotes q USING(coin_id)
        JOIN stock_status_evidence st USING(coin_id) JOIN stock_action_state ac USING(coin_id)
        JOIN stock_sessions se ON se.exchange=i.listing_exchange AND se.session_date=q.session_date
        WHERE i.coin_id=:c"""),
                {"c": cid},
            )
        ).scalar_one()
        tid = await complete_receipt(conn, cid, uid, authority=snapshot, at=now)
        await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        yield conn, cid, uid, tid, snapshot
        await tx.rollback()


async def call_guard(conn, tid, uid, snapshot):
    await conn.execute(
        text("SELECT public.assert_stock_execution_current(:t,:u,CAST(:s AS jsonb))"),
        {"t": tid, "u": uid, "s": json.dumps(snapshot)},
    )


async def test_final_guard_accepts_exact_current_bound_snapshot(guard_case):
    conn, _, uid, tid, snapshot = guard_case
    await call_guard(conn, tid, uid, snapshot)


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE stock_data_admissions SET attribution='changed' WHERE product='quotes'",
        "UPDATE stock_data_admissions SET valid_until=clock_timestamp() WHERE product='quotes'",
        "UPDATE stock_data_admissions SET state='revoked' WHERE product='actions'",
        "UPDATE stock_action_state SET epoch=epoch+1",
        "UPDATE stock_action_state SET health='unknown'",
        "UPDATE stock_action_state SET next_blocking_at=clock_timestamp()",
        "UPDATE stock_quotes SET event_at=event_at-interval '120 seconds'",
        "UPDATE stock_quotes SET unit_epoch=unit_epoch+1",
        "UPDATE stock_status_evidence SET state='halted'",
        "UPDATE stock_status_evidence SET continuity_current=false,bootstrap_verified=false",
        "UPDATE stock_status_evidence SET sequence=sequence+1",
        "UPDATE stock_sessions SET closes_at=clock_timestamp()",
        "UPDATE stock_instruments SET provider_asset_id='changed' "
        "WHERE provider_asset_id='fixture-asset'",
    ],
)
async def test_final_guard_reads_current_rows_not_caller_flags(guard_case, sql):
    conn, _, uid, tid, snapshot = guard_case
    await conn.execute(text(sql))
    with pytest.raises(DBAPIError) as exc:
        await call_guard(conn, tid, uid, snapshot)
    assert exc.value.orig.sqlstate == "22023"


async def test_forged_snapshot_and_wrong_owner_refused(guard_case):
    conn, _, uid, tid, snapshot = guard_case
    for owner, body in ((uid + 100000, snapshot), (uid, {**snapshot, "safety_epoch": 999})):
        with pytest.raises(DBAPIError) as exc:
            async with conn.begin_nested():
                await call_guard(conn, tid, owner, body)
        assert exc.value.orig.sqlstate == "22023"


@pytest.mark.parametrize("guard_case", [1], indirect=True)
async def test_advancing_database_clock_expires_status_inside_same_transaction(guard_case):
    conn, _, uid, tid, snapshot = guard_case
    await call_guard(conn, tid, uid, snapshot)
    await conn.execute(text("SELECT pg_sleep(1.05)"))
    with pytest.raises(DBAPIError, match="status unavailable") as exc:
        await call_guard(conn, tid, uid, snapshot)
    assert exc.value.orig.sqlstate == "22023"


async def test_runtime_function_authority_is_invoker_fixed_and_not_public(engine, runtime_roles):
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("""SELECT p.prosecdef,p.proconfig,
          pg_get_userbyid(p.proowner)=(SELECT pg_get_userbyid(relowner) FROM pg_class
           WHERE oid='public.stock_fill_facts'::regclass) AS same_owner,
          has_function_privilege('birja_app',p.oid,'EXECUTE') AS app,
          has_function_privilege('birja_scheduler',p.oid,'EXECUTE') AS scheduler,
          EXISTS(SELECT FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner)))
           WHERE grantee=0 AND privilege_type='EXECUTE') AS public
          FROM pg_proc p WHERE p.oid=
          'public.assert_stock_execution_current(bigint,bigint,jsonb)'::regprocedure""")
            )
        ).one()
        assert row.prosecdef is False
        assert row.proconfig == ["search_path=pg_catalog, public"]
        assert row.same_owner and row.app and not row.scheduler and not row.public
        await conn.execute(text("CREATE ROLE birja_stock_public_probe NOLOGIN NOINHERIT"))
        await conn.execute(text("GRANT USAGE ON SCHEMA public TO birja_stock_public_probe"))
        for role in ("birja_scheduler", "birja_stock_public_probe"):
            async with conn.begin_nested():
                await conn.execute(text(f"SET LOCAL ROLE {role}"))
                with pytest.raises(DBAPIError) as exc:
                    async with conn.begin_nested():
                        await conn.execute(
                            text("SELECT public.assert_stock_execution_current(1,1,'{}')")
                        )
                assert exc.value.orig.sqlstate == "42501"


async def test_scheduler_can_write_status_but_not_receipts(engine, runtime_roles):
    async with engine.connect() as conn:
        tx = await conn.begin()
        cid = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        await conn.execute(
            text("""INSERT INTO public.stock_status_evidence
        (coin_id,provider_asset_id,source_ref) VALUES (:c,'synthetic','fixture')"""),
            {"c": cid},
        )
        with pytest.raises(DBAPIError) as exc:
            async with conn.begin_nested():
                await conn.execute(text("SELECT * FROM public.stock_fill_facts"))
        assert exc.value.orig.sqlstate == "42501"
        await tx.rollback()


async def test_bootstrap_and_upgrade_grants_have_exact_runtime_parity(engine, runtime_roles):
    from pathlib import Path

    source = (Path(__file__).parents[2] / "deploy/db/bootstrap-roles.sql").read_text()
    block = (
        "DO $execution_grants$"
        + source.split("DO $execution_grants$", 1)[1].split("$execution_grants$;", 1)[0]
        + "$execution_grants$;"
    )
    query = text("""SELECT r,t,p,has_table_privilege(r,t,p) FROM
      unnest(ARRAY['birja_app','birja_scheduler']) r CROSS JOIN
      unnest(ARRAY['public.stock_fill_facts','public.stock_status_evidence']) t CROSS JOIN
      unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) p
      ORDER BY r,t,p""")
    async with engine.connect() as conn:
        before = (await conn.execute(query)).all()
        await conn.execute(
            text("""REVOKE ALL ON public.stock_fill_facts,
          public.stock_status_evidence FROM birja_app,birja_scheduler""")
        )
        await conn.execute(block and text(block))
        assert (await conn.execute(query)).all() == before
        assert (
            await conn.execute(
                text("""SELECT
          has_function_privilege('birja_app',
            'public.assert_stock_execution_current(bigint,bigint,jsonb)','EXECUTE')
          AND NOT has_function_privilege('birja_scheduler',
            'public.assert_stock_execution_current(bigint,bigint,jsonb)','EXECUTE')""")
            )
        ).scalar_one()
        await conn.rollback()
