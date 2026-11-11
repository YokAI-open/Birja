"""Real isolated PostgreSQL accounting invariants and privilege boundaries."""

import asyncio
import os
import shutil
import subprocess
from collections.abc import AsyncIterator
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from tests.test_migrations import _versions
from tests.test_stock_migrations import _financial_snapshot, migrate

ACTION_TABLES = {
    "stock_action_events",
    "stock_action_sources",
    "stock_action_revisions",
    "stock_action_observations",
    "stock_action_state",
    "stock_ownership_movements",
    "stock_split_applications",
    "stock_dividend_entitlements",
    "stock_action_resolutions",
}


async def test_durable_action_schema_exists(engine: AsyncEngine, migrated: None) -> None:
    async with engine.connect() as conn:
        tables = set(
            (
                await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                )
            ).scalars()
        )
        assert tables >= ACTION_TABLES, "Accounting needs nine durable constrained relations"


async def test_quote_has_local_unit_provenance(engine: AsyncEngine, migrated: None) -> None:
    async with engine.connect() as conn:
        columns = set(
            (
                await conn.execute(
                    text(
                        (
                            "SELECT column_name FROM information_schema.columns WHERE "
                            "table_name='stock_quotes'"
                        )
                    )
                )
            ).scalars()
        )
        assert "unit_epoch" in columns, "Quote units must survive restart and split boundaries"


@pytest_asyncio.fixture
async def ledger(
    engine: AsyncEngine, migrated: None
) -> AsyncIterator[tuple[AsyncConnection, int, int]]:
    async with engine.connect() as conn:
        tx = await conn.begin()
        uid = (
            await conn.execute(
                text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                {"e": f"action-{uuid4()}@example.test"},
            )
        ).scalar_one()
        cid = (
            await conn.execute(
                text("SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 1")
            )
        ).scalar_one()
        yield conn, cid, uid
        await tx.rollback()


async def event(conn: AsyncConnection, cid: int) -> tuple[int, int, int]:
    eid = (
        await conn.execute(
            text(
                "INSERT INTO "
                "stock_action_events(coin_id,economic_key,first_observed_at) VALUES "
                "(:c,:k,now()) RETURNING id"
            ),
            {"c": cid, "k": str(uuid4())},
        )
    ).scalar_one()
    sid = (
        await conn.execute(
            text(
                "INSERT INTO "
                "stock_action_sources(event_id,provider,product,provider_event_id) "
                "VALUES (:e,'alpaca','actions',:k) RETURNING id"
            ),
            {"e": eid, "k": str(uuid4())},
        )
    ).scalar_one()
    rid = (
        await conn.execute(
            text(
                "INSERT INTO "
                "stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason)"
                " VALUES (:e,:s,1,:f,'snapshot',now(),1,'{}','uncertain','fixture') "
                "RETURNING id"
            ),
            {"e": eid, "s": sid, "f": "a" * 64},
        )
    ).scalar_one()
    await conn.execute(
        text("UPDATE stock_action_events SET current_revision_id=:r WHERE id=:e"),
        {"r": rid, "e": eid},
    )
    return eid, sid, rid


async def movement(conn: AsyncConnection, cid: int, uid: int, **changes: object) -> None:
    params: dict[str, object] = {
        "c": cid,
        "u": uid,
        "seq": 1,
        "q": Decimal("2"),
        "before": Decimal(0),
        "after": Decimal(2),
        "bb": Decimal(0),
        "ab": Decimal(20),
        "epoch": 0,
        "kind": "opening",
        "trade": None,
        "app": None,
        "key": "opening",
    }
    params.update(changes)
    await conn.execute(
        text("""INSERT INTO stock_ownership_movements
    (coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,trade_id,application_id,causal_key)
    VALUES (:c,:u,:seq,now(),now(),:q,:before,:after,:bb,:ab,:epoch,:kind,:trade,:app,:key)"""),
        params,
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"q": Decimal("NaN")},
        {"q": Decimal("Infinity")},
        {"q": Decimal("-Infinity")},
        {"q": Decimal("1.5")},
        {"q": Decimal("1000000000000")},
        {"q": Decimal(0)},
        {"after": Decimal(3)},
        {"ab": Decimal("NaN")},
        {"ab": Decimal("1.001")},
        {"epoch": -1},
        {"epoch": 9007199254740992},
        {"seq": 0},
        {"kind": "fill"},
        {"kind": "split"},
        {"trade": 999999},
        {"before": Decimal(1)},
        {"key": ""},
    ],
)
async def test_movement_constraints(ledger, changes) -> None:
    conn, cid, uid = ledger
    with pytest.raises(DBAPIError) as error:
        await movement(conn, cid, uid, **changes)
    assert error.value.orig.sqlstate in {"23514", "23503", "22003"}


@pytest.mark.parametrize("changes", [{"key": "other"}, {"seq": 2}])
async def test_movement_economic_uniqueness(ledger, changes) -> None:
    conn, cid, uid = ledger
    await movement(conn, cid, uid)
    with pytest.raises(DBAPIError) as error:
        await movement(conn, cid, uid, **changes)
    assert error.value.orig.sqlstate == "23505"


async def test_event_revision_source_and_current_pointer_match(ledger) -> None:
    conn, cid, _ = ledger
    eid, origin, rid = await event(conn, cid)
    other, _, _ = await event(conn, cid)
    await conn.execute(
        text("UPDATE stock_action_events SET current_revision_id=:r WHERE id=:e"),
        {"r": rid, "e": other},
    )
    with pytest.raises(DBAPIError) as error:
        await conn.execute(
            text("SET CONSTRAINTS fk_stock_action_events_current_revision IMMEDIATE")
        )
    assert error.value.orig.sqlstate == "23503"
    assert eid != other


@pytest.mark.parametrize(
    "target",
    ["revision_ordinal", "revision_fingerprint", "source", "observation", "split", "entitlement"],
)
async def test_durable_event_duplicate_refused(ledger, target) -> None:
    conn, cid, uid = ledger
    eid, sid, rid = await event(conn, cid)
    params = {"e": eid, "s": sid, "r": rid, "u": uid, "f": "a" * 64, "c": cid}
    if target.startswith("revision"):
        params["ordinal"] = 1 if target == "revision_ordinal" else 2
        params["f"] = "b" * 64 if target == "revision_ordinal" else "a" * 64
        sql = """INSERT INTO stock_action_revisions
        (event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,
         admission_generation,normalized_terms,classification,reason)
        VALUES (:e,:s,:ordinal,:f,'update',now(),1,'{}','uncertain','fixture')"""
    elif target == "source":
        sql = (
            "INSERT INTO "
            "stock_action_sources(event_id,provider,product,provider_event_id) "
            "SELECT event_id,provider,product,provider_event_id FROM "
            "stock_action_sources WHERE id=:s"
        )
    elif target == "observation":
        sql = (
            "INSERT INTO "
            "stock_action_observations(event_id,source_id,revision_id,mutation_id,observed_at,admission_generation,source_kind,cycle_id)"
            " VALUES (:e,:s,:r,'m',now(),1,'replay','cycle')"
        )
    elif target == "split":
        sql = (
            "INSERT INTO "
            "stock_split_applications(coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at)"
            " VALUES (:c,:e,:r,'2','1',now(),0,1,0,:f,:f,now())"
        )
    else:
        sql = (
            "INSERT INTO "
            "stock_dividend_entitlements(event_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,last_movement_sequence,eligible_quantity,state,fingerprint)"
            " VALUES (:e,:u,:r,now(),'exclusive',1,'epoch0',0,0,2,'eligible',:f)"
        )
    if target in {"observation", "split", "entitlement"}:
        await conn.execute(text(sql), params)
    with pytest.raises(DBAPIError) as error:
        await conn.execute(text(sql), params)
    assert error.value.orig.sqlstate == "23505"


@pytest.mark.parametrize(
    "table,column,value",
    [
        ("stock_action_state", "epoch", "0"),
        ("stock_action_state", "unit_epoch", "-1"),
        ("stock_action_state", "health", "'healthy'"),
        ("stock_action_state", "staged_continuation", "'[]'::jsonb"),
        ("stock_action_state", "cursor", "repeat('a',4097)"),
        ("stock_action_revisions", "normalized_terms", "'[]'::jsonb"),
        ("stock_action_revisions", "normalized_terms", "jsonb_build_object('x',repeat('a',16385))"),
        ("stock_action_revisions", "classification", "'whatever'"),
    ],
)
async def test_bounded_authority_state(ledger, table, column, value) -> None:
    conn, cid, _ = ledger
    eid, sid, rid = await event(conn, cid)
    await conn.execute(
        text("INSERT INTO stock_action_state(coin_id,admission_generation) VALUES (:c,1)"),
        {"c": cid},
    )
    # Identifiers/expressions come solely from this fixed test matrix.
    with pytest.raises(DBAPIError) as error:
        await conn.execute(text(f"UPDATE {table} SET {column}={value}"))  # noqa: S608 - fixed matrix
    assert error.value.orig.sqlstate == "23514"


async def test_populated_0010_upgrade_preserves_legacy(engine: AsyncEngine, migrated: None) -> None:
    await migrate("0010", down=True)
    async with engine.begin() as conn:
        uid = (
            await conn.execute(
                text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                {"e": f"legacy-{uuid4()}@example.test"},
            )
        ).scalar_one()
        cid = (await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
        await conn.execute(
            text("INSERT INTO accounts(user_id,cash,starting_cash) VALUES (:u,9876.54,10000)"),
            {"u": uid},
        )
        await conn.execute(
            text(
                "INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) VALUES "
                "(:u,:c,0.00123456,123.46)"
            ),
            {"u": uid, "c": cid},
        )
        await conn.execute(
            text("""INSERT INTO trades
            (user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
             exec_price,fee,cash_delta,cash_after,idempotency_key)
            VALUES (:u,:c,'buy','quantity',0.00123456,0.00123456,99900,now(),
                    100000,0,-123.46,9876.54,gen_random_uuid())"""),
            {"u": uid, "c": cid},
        )
    try:
        before = await _financial_snapshot(engine)
        await migrate("head")
        assert await _versions(engine) == ["0013"]
        assert await _financial_snapshot(engine) == before
        await migrate("0010", down=True)
        assert await _financial_snapshot(engine) == before
    finally:
        await migrate("head")
        async with engine.begin() as conn:
            for table in ("trades", "holdings", "accounts"):
                await conn.execute(text(f"DELETE FROM {table} WHERE user_id=:u"), {"u": uid})  # noqa: S608 - fixed allowlist
            await conn.execute(text("DELETE FROM users WHERE id=:u"), {"u": uid})


async def test_populated_accounting_downgrade_refuses_before_alter(
    engine: AsyncEngine, migrated: None
) -> None:
    async with engine.begin() as conn:
        cid = (
            await conn.execute(
                text("SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 1")
            )
        ).scalar_one()
        eid = (
            await conn.execute(
                text(
                    "INSERT INTO "
                    "stock_action_events(coin_id,economic_key,first_observed_at) VALUES "
                    "(:c,:k,now()) RETURNING id"
                ),
                {"c": cid, "k": str(uuid4())},
            )
        ).scalar_one()
    try:
        with pytest.raises(DBAPIError, match="durable stock accounting prevents downgrade"):
            await migrate("0010", down=True)
        assert await _versions(engine) == ["0011"]
        async with engine.connect() as conn:
            assert (
                await conn.execute(
                    text("SELECT count(*) FROM stock_action_events WHERE id=:e"), {"e": eid}
                )
            ).scalar_one() == 1
            assert (
                await conn.execute(
                    text(
                        "SELECT count(*) FROM information_schema.columns WHERE "
                        "table_name='stock_quotes' AND column_name='unit_epoch'"
                    )
                )
            ).scalar_one() == 1
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("DELETE FROM stock_action_events WHERE id=:e"), {"e": eid})


@pytest_asyncio.fixture
async def runtime_roles(engine: AsyncEngine, migrated: None) -> AsyncIterator[None]:
    await migrate("0010", down=True)
    async with engine.begin() as conn:
        for role in ("birja_app", "birja_scheduler", "birja_migrator"):
            await conn.execute(text(f"CREATE ROLE {role} NOLOGIN NOINHERIT"))  # noqa: S608 - fixed isolated roles
            await conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {role}"))  # noqa: S608
    try:
        await migrate("head")
        yield
    finally:
        async with engine.begin() as conn:
            for role in ("birja_app", "birja_scheduler", "birja_action_operator", "birja_migrator"):
                exists = (
                    await conn.execute(
                        text("SELECT count(*) FROM pg_roles WHERE rolname=:r"), {"r": role}
                    )
                ).scalar_one()
                if exists:
                    await conn.execute(text(f"DROP OWNED BY {role}"))  # noqa: S608 - fixed isolated roles
                    await conn.execute(text(f"DROP ROLE {role}"))  # noqa: S608


async def test_upgrade_grants_support_quantity_but_deny_cash_and_authority(
    engine: AsyncEngine,
    runtime_roles: None,
) -> None:
    async with engine.connect() as conn:
        for column in ("id", "coin_id", "user_id", "side", "quantity", "cash_delta"):
            assert (
                await conn.execute(
                    text("SELECT has_column_privilege('birja_scheduler','trades',:c,'SELECT')"),
                    {"c": column},
                )
            ).scalar_one()
        assert not (
            await conn.execute(
                text("SELECT has_table_privilege('birja_scheduler','trades','SELECT')")
            )
        ).scalar_one()
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        await conn.execute(
            text("SELECT id,coin_id,user_id,side,quantity,cash_delta FROM trades LIMIT 0")
        )
        for statement in (
            "SELECT * FROM trades",
            "SELECT cash_after FROM trades",
            "UPDATE trades SET quantity=quantity",
            "DELETE FROM trades",
            "INSERT INTO trades DEFAULT VALUES",
        ):
            with pytest.raises(DBAPIError) as error:
                async with conn.begin_nested():
                    await conn.execute(text(statement))
            assert error.value.orig.sqlstate == "42501"
        await conn.execute(text("RESET ROLE"))
        assert (
            await conn.execute(
                text(
                    "SELECT has_column_privilege('birja_scheduler','holdings','quantity','UPDATE')"
                )
            )
        ).scalar_one(), "Splits require precisely quantity-only UPDATE"
        assert not (
            await conn.execute(
                text(
                    "SELECT has_column_privilege('birja_scheduler',"
                    "'holdings','cost_basis','UPDATE')"
                )
            )
        ).scalar_one()
        assert (
            await conn.execute(
                text("SELECT has_table_privilege('birja_app','stock_ownership_movements','INSERT')")
            )
        ).scalar_one()


async def denied(conn: AsyncConnection, statement: str) -> None:
    savepoint = await conn.begin_nested()
    try:
        with pytest.raises(DBAPIError) as error:
            await conn.execute(text(statement))
        assert error.value.orig.sqlstate == "42501", statement
    finally:
        await savepoint.rollback()


async def test_actual_runtime_grants_deny_immutable_and_authority_writes(
    engine: AsyncEngine,
    runtime_roles: None,
) -> None:
    async with engine.connect() as conn, conn.begin():
        for role in ("birja_app", "birja_scheduler", "birja_action_operator"):
            await conn.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608 - fixed test roles
            for table, field in (
                ("stock_action_revisions", "reason"),
                ("stock_action_observations", "cycle_id"),
                ("stock_ownership_movements", "causal_key"),
                ("stock_split_applications", "new_rate"),
                ("stock_dividend_entitlements", "state"),
                ("stock_action_resolutions", "decision"),
            ):
                await conn.execute(text(f"SELECT id FROM {table} LIMIT 1"))  # noqa: S608 - fixed tables
                await denied(conn, f"UPDATE {table} SET {field}={field} WHERE false")  # noqa: S608 - fixed matrix
                await denied(conn, f"DELETE FROM {table} WHERE false")  # noqa: S608 - fixed matrix
            await denied(conn, "INSERT INTO stock_action_resolutions DEFAULT VALUES")
            await denied(
                conn, "UPDATE stock_data_admissions SET generation=generation+1 WHERE false"
            )
            await denied(conn, "SELECT setval('stock_action_resolutions_id_seq',999)")
            if role != "birja_app":
                await denied(conn, "UPDATE accounts SET cash=cash+1 WHERE false")
                await denied(conn, "UPDATE holdings SET cost_basis=cost_basis WHERE false")
                await denied(conn, "INSERT INTO trades DEFAULT VALUES")
            if role == "birja_scheduler":
                await conn.execute(text("UPDATE holdings SET quantity=quantity WHERE false"))
                await conn.execute(
                    text(
                        "UPDATE stock_action_events SET current_revision_id=current_revision_id "
                        "WHERE false"
                    )
                )
                await denied(
                    conn, "UPDATE stock_action_events SET economic_key=economic_key WHERE false"
                )
                await conn.execute(text("SELECT nextval('stock_action_revisions_id_seq')"))
            if role == "birja_app":
                await conn.execute(text("SELECT nextval('stock_ownership_movements_id_seq')"))
                await denied(conn, "INSERT INTO stock_action_revisions DEFAULT VALUES")
            await conn.execute(text("RESET ROLE"))
        attrs = (
            await conn.execute(
                text(
                    "SELECT rolcanlogin,rolinherit,rolsuper,rolcreaterole,rolcreatedb,"
                    "rolreplication,rolbypassrls FROM pg_roles "
                    "WHERE rolname='birja_action_operator'"
                )
            )
        ).one()
        assert tuple(attrs) == (False,) * 7
        assert not (
            await conn.execute(
                text(
                    "SELECT 1 FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles "
                    "WHERE rolname='birja_action_operator') OR roleid=(SELECT oid FROM pg_roles "
                    "WHERE rolname='birja_action_operator')"
                )
            )
        ).all()


async def test_scheduler_grants_allow_append_with_identity_sequences(
    engine: AsyncEngine,
    runtime_roles: None,
) -> None:
    async with engine.connect() as conn, conn.begin():
        cid = (
            await conn.execute(
                text("SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 1")
            )
        ).scalar_one()
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        eid, sid, rid = await event(conn, cid)
        await conn.execute(
            text("INSERT INTO stock_action_state(coin_id,admission_generation) VALUES (:c,1)"),
            {"c": cid},
        )
        await conn.execute(
            text(
                "INSERT INTO stock_action_observations(event_id,source_id,revision_id,observed_at,"
                "admission_generation,source_kind,cycle_id) "
                "VALUES (:e,:s,:r,now(),1,'snapshot','fixture')"
            ),
            {"e": eid, "s": sid, "r": rid},
        )
        assert eid > 0 and sid > 0 and rid > 0
        await conn.rollback()


async def test_fresh_bootstrap_grants_match_upgrade_without_repair(
    engine: AsyncEngine,
    runtime_roles: None,
) -> None:
    matrix = """SELECT string_agg(r||':'||t||':'||p||':'||
      has_table_privilege(r,t,p)::text,'|' ORDER BY r,t,p)
      FROM unnest(ARRAY['birja_app','birja_scheduler','birja_action_operator']) r,
      unnest(ARRAY['stock_action_events','stock_action_sources','stock_action_revisions',
        'stock_action_observations','stock_action_state','stock_ownership_movements',
        'stock_split_applications','stock_dividend_entitlements','stock_action_resolutions']) t,
      unnest(ARRAY['SELECT','INSERT','UPDATE','DELETE','TRUNCATE','REFERENCES','TRIGGER']) p"""
    async with engine.connect() as conn:
        before = (await conn.execute(text(matrix))).scalar_one()
    root = await asyncio.to_thread(lambda: Path(__file__).resolve().parents[2])
    script = await asyncio.to_thread((root / "deploy/db/bootstrap-roles.sql").read_text)
    script = script.rsplit("COMMIT;", 1)[0] + matrix + ";\nROLLBACK;\n"
    docker = shutil.which("docker")
    assert docker is not None
    result = await asyncio.to_thread(
        subprocess.run,
        [
            docker,
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
            "-X",
            "-qAt",
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
    assert result.stdout.strip() == before


async def test_verified_alias_can_observe_same_economic_revision(ledger) -> None:
    conn, cid, _ = ledger
    eid, origin, rid = await event(conn, cid)
    sid = (
        await conn.execute(
            text("""INSERT INTO stock_action_sources
      (event_id,provider,product,provider_event_id)
      VALUES (:e,'alpaca','actions',:k) RETURNING id"""),
            {"e": eid, "k": str(uuid4())},
        )
    ).scalar_one()
    await conn.execute(
        text("""INSERT INTO stock_action_observations
          (event_id,source_id,revision_id,observed_at,admission_generation,source_kind,cycle_id)
          VALUES (:e,:s,:r,now(),1,'snapshot','alias')"""),
        {"e": eid, "s": sid, "r": rid},
    )
    assert (
        await conn.execute(
            text("SELECT source_id FROM stock_action_revisions WHERE id=:r"), {"r": rid}
        )
    ).scalar_one() == origin
    assert (
        await conn.execute(
            text("SELECT count(*) FROM stock_action_revisions WHERE event_id=:e"), {"e": eid}
        )
    ).scalar_one() == 1


async def fill_cause(conn: AsyncConnection, cid: int, uid: int) -> int:
    return (
        await conn.execute(
            text("""INSERT INTO trades
      (user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
       exec_price,fee,cash_delta,cash_after,idempotency_key)
      VALUES (:u,:c,'buy','quantity',2,2,10,now(),10,0,-20,9980,gen_random_uuid())
      RETURNING id"""),
            {"c": cid, "u": uid},
        )
    ).scalar_one()


@pytest.mark.parametrize("mismatch", ["user", "coin"])
async def test_movement_rejects_foreign_fill_cause(ledger, mismatch: str) -> None:
    conn, cid, uid = ledger
    foreign_cid = cid
    foreign_uid = uid
    if mismatch == "coin":
        foreign_cid = (
            await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))
        ).scalar_one()
    else:
        foreign_uid = (
            await conn.execute(
                text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                {"e": f"foreign-{uuid4()}@example.test"},
            )
        ).scalar_one()
    tid = await fill_cause(conn, foreign_cid, foreign_uid)
    with pytest.raises(DBAPIError) as error:
        await movement(conn, cid, uid, kind="fill", trade=tid)
    assert error.value.orig.sqlstate == "23503"


@pytest.mark.parametrize("mismatch", ["source", "revision"])
async def test_observation_rejects_cross_event_alias(ledger, mismatch: str) -> None:
    conn, cid, _ = ledger
    eid, sid, rid = await event(conn, cid)
    _, other_source, other_revision = await event(conn, cid)
    if mismatch == "source":
        sid = other_source
    else:
        rid = other_revision
    with pytest.raises(DBAPIError) as error:
        await conn.execute(
            text("""INSERT INTO stock_action_observations
          (event_id,source_id,revision_id,observed_at,admission_generation,source_kind,cycle_id)
          VALUES (:e,:s,:r,now(),1,'snapshot','foreign')"""),
            {"e": eid, "s": sid, "r": rid},
        )
    assert error.value.orig.sqlstate == "23503"


async def split_cause(conn: AsyncConnection, cid: int) -> int:
    eid, _, rid = await event(conn, cid)
    return (
        await conn.execute(
            text("""INSERT INTO stock_split_applications
      (coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,
       prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at)
      VALUES (:c,:e,:r,'2','1',now(),0,1,0,:f,:f,now()) RETURNING id"""),
            {"c": cid, "e": eid, "r": rid, "f": "a" * 64},
        )
    ).scalar_one()


@pytest.mark.parametrize("mismatch", ["coin", "epoch"])
async def test_movement_rejects_foreign_split_cause(ledger, mismatch: str) -> None:
    conn, cid, uid = ledger
    source_coin = cid
    if mismatch == "coin":
        source_coin = (
            await conn.execute(
                text(
                    "SELECT coin_id FROM stock_instruments WHERE coin_id<>:c "
                    "ORDER BY coin_id LIMIT 1"
                ),
                {"c": cid},
            )
        ).scalar_one()
    app = await split_cause(conn, source_coin)
    with pytest.raises(DBAPIError) as error:
        await movement(
            conn,
            cid,
            uid,
            kind="split",
            app=app,
            before=Decimal(2),
            after=Decimal(4),
            bb=Decimal(20),
            epoch=0 if mismatch == "epoch" else 1,
        )
    assert error.value.orig.sqlstate == "23503"


async def test_split_application_cannot_claim_another_event_coin(ledger) -> None:
    conn, cid, _ = ledger
    app = await split_cause(conn, cid)
    other = (
        await conn.execute(
            text(
                "SELECT coin_id FROM stock_instruments WHERE coin_id<>:c ORDER BY coin_id LIMIT 1"
            ),
            {"c": cid},
        )
    ).scalar_one()
    with pytest.raises(DBAPIError) as error:
        await conn.execute(
            text("UPDATE stock_split_applications SET coin_id=:c WHERE id=:a"),
            {"c": other, "a": app},
        )
    assert error.value.orig.sqlstate == "23503"


async def test_valid_causes_work_under_runtime_grants_with_narrow_trade_read(
    engine: AsyncEngine,
    runtime_roles: None,
) -> None:
    async with engine.connect() as conn:
        tx = await conn.begin()
        try:
            uid = (
                await conn.execute(
                    text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                    {"e": f"causes-{uuid4()}@example.test"},
                )
            ).scalar_one()
            cid = (
                await conn.execute(
                    text("SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 1")
                )
            ).scalar_one()
            tid = await fill_cause(conn, cid, uid)
            app = await split_cause(conn, cid)
            await conn.execute(text("SET LOCAL ROLE birja_app"))
            await movement(conn, cid, uid, kind="fill", trade=tid)
            await conn.execute(text("RESET ROLE"))
            await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
            await conn.execute(text("SELECT id FROM trades LIMIT 1"))
            await denied(conn, "SELECT cash_after FROM trades LIMIT 1")
            await movement(
                conn,
                cid,
                uid,
                kind="split",
                app=app,
                before=Decimal(2),
                after=Decimal(4),
                bb=Decimal(20),
                epoch=1,
                seq=2,
                key="split",
            )
            await conn.execute(text("RESET ROLE"))
            assert (
                await conn.execute(
                    text("SELECT count(*) FROM stock_ownership_movements WHERE user_id=:u"),
                    {"u": uid},
                )
            ).scalar_one() == 2
        finally:
            await tx.rollback()


async def test_failed_restricted_upgrade_can_retry_exact_concurrent_index(
    engine: AsyncEngine,
    migrated: None,
) -> None:
    """The committed concurrent index must survive and support a safe retry."""
    await migrate("0010", down=True)
    async with engine.begin() as conn:
        exists = (
            await conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname='birja_action_operator'"))
        ).scalar_one_or_none()
        if exists:
            await conn.execute(text("DROP OWNED BY birja_action_operator"))
            await conn.execute(text("DROP ROLE birja_action_operator"))
        await conn.execute(
            text(
                "CREATE ROLE birja_action_retry_migrator LOGIN NOINHERIT PASSWORD 'test-only-retry'"
            )
        )
        await conn.execute(
            text("GRANT USAGE ON SCHEMA public TO birja_action_retry_migrator WITH GRANT OPTION")
        )
        await conn.execute(text("GRANT CREATE ON SCHEMA public TO birja_action_retry_migrator"))
        await conn.execute(
            text("GRANT REFERENCES ON ALL TABLES IN SCHEMA public TO birja_action_retry_migrator")
        )
        await conn.execute(
            text(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON alembic_version "
                "TO birja_action_retry_migrator"
            )
        )
        await conn.execute(
            text(
                "GRANT SELECT ON stock_instruments,stock_data_admissions,stock_sessions "
                "TO birja_action_retry_migrator WITH GRANT OPTION"
            )
        )
        await conn.execute(text("ALTER TABLE trades OWNER TO birja_action_retry_migrator"))
        await conn.execute(text("ALTER TABLE stock_quotes OWNER TO birja_action_retry_migrator"))
    root = await asyncio.to_thread(lambda: Path(__file__).resolve().parents[1])

    async def restricted_upgrade() -> tuple[int, str]:
        proc = await asyncio.create_subprocess_exec(
            str(root / ".venv/bin/alembic"),
            "upgrade",
            "head",
            cwd=root,
            env={
                "PATH": os.defpath,
                "ENV": "test",
                "DATABASE_URL": "postgresql+asyncpg://birja_action_retry_migrator:test-only-retry@127.0.0.1:55432/birja_test",
                "REDIS_URL": "redis://:test@127.0.0.1:56379/0",
                "OTP_HMAC_SECRET": "test-only-otp-secret-not-for-prod-000000",
                "JWT_SECRET": "test-only-jwt-secret-not-for-prod-000000",
                "ALPACA_API_KEY": "",
                "ALPACA_SECRET_KEY": "",
                "STOCK_DATA_ENABLED": "false",
            },
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        output, _ = await asyncio.wait_for(proc.communicate(), 30)
        assert proc.returncode is not None
        return proc.returncode, output.decode()

    try:
        code, output = await restricted_upgrade()
        assert code != 0 and "preprovision birja_action_operator" in output
        assert await _versions(engine) == ["0010"]
        async with engine.begin() as conn:
            assert (
                await conn.execute(
                    text(
                        "SELECT indisvalid FROM pg_index "
                        "WHERE indexrelid='uq_trades_id_coin_user'::regclass"
                    )
                )
            ).scalar_one()
            await conn.execute(text("CREATE ROLE birja_action_operator NOLOGIN NOINHERIT"))
        code, output = await restricted_upgrade()
        assert code == 0, output
        assert await _versions(engine) == ["0013"]
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("REASSIGN OWNED BY birja_action_retry_migrator TO birja_test"))
            await conn.execute(text("DROP OWNED BY birja_action_retry_migrator"))
            await conn.execute(text("DROP ROLE birja_action_retry_migrator"))
            if (
                await conn.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one() == "0010":
                await conn.execute(text("DROP INDEX IF EXISTS uq_trades_id_coin_user"))
        await migrate("head")


async def test_same_name_wrong_cause_index_is_rejected_without_repair(
    engine: AsyncEngine,
    migrated: None,
) -> None:
    await migrate("0010", down=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("CREATE UNIQUE INDEX uq_trades_id_coin_user ON trades(id,user_id,coin_id)")
            )
        with pytest.raises(RuntimeError, match="incompatible preexisting trade cause index"):
            await migrate("head")
        assert await _versions(engine) == ["0010"]
        async with engine.connect() as conn:
            assert (
                (
                    await conn.execute(
                        text("SELECT pg_get_indexdef('uq_trades_id_coin_user'::regclass)")
                    )
                )
                .scalar_one()
                .endswith("(id, user_id, coin_id)")
            )
            assert (
                await conn.execute(text("SELECT to_regclass('public.stock_action_events')"))
            ).scalar_one() is None
    finally:
        async with engine.begin() as conn:
            await conn.execute(text("DROP INDEX uq_trades_id_coin_user"))
        await migrate("head")


async def test_cancelled_exact_concurrent_index_is_rebuilt_safely(
    engine: AsyncEngine,
    migrated: None,
) -> None:
    """Create a genuine invalid build by cancelling its old-snapshot wait."""
    await migrate("0010", down=True)
    try:
        async with engine.connect() as snapshot, engine.connect() as builder:
            snapshot = await snapshot.execution_options(isolation_level="REPEATABLE READ")
            snapshot_tx = await snapshot.begin()
            await snapshot.execute(text("SELECT id FROM trades LIMIT 1"))
            builder = await builder.execution_options(isolation_level="AUTOCOMMIT")
            pid = (await builder.execute(text("SELECT pg_backend_pid()"))).scalar_one()
            task = asyncio.create_task(
                builder.execute(
                    text(
                        "CREATE UNIQUE INDEX CONCURRENTLY uq_trades_id_coin_user "
                        "ON trades(id,coin_id,user_id)"
                    )
                )
            )
            try:
                async with engine.connect() as observer:
                    for _ in range(100):
                        phase = (
                            await observer.execute(
                                text(
                                    "SELECT phase FROM pg_stat_progress_create_index WHERE pid=:p"
                                ),
                                {"p": pid},
                            )
                        ).scalar_one_or_none()
                        if phase == "waiting for old snapshots":
                            break
                        await observer.rollback()
                        await asyncio.sleep(0.02)
                    else:
                        raise AssertionError(
                            "Concurrent index did not reach observable snapshot barrier"
                        )
                    assert (
                        await observer.execute(text("SELECT pg_cancel_backend(:p)"), {"p": pid})
                    ).scalar_one()
                with pytest.raises(DBAPIError) as error:
                    await asyncio.wait_for(task, 5)
                assert error.value.orig.sqlstate == "57014"
            finally:
                await snapshot_tx.rollback()
                if not task.done():
                    task.cancel()
                    await asyncio.gather(task, return_exceptions=True)
        async with engine.connect() as conn:
            assert not (
                await conn.execute(
                    text(
                        "SELECT indisvalid FROM pg_index "
                        "WHERE indexrelid='uq_trades_id_coin_user'::regclass"
                    )
                )
            ).scalar_one()
        await migrate("head")
        assert await _versions(engine) == ["0013"]
        async with engine.connect() as conn:
            assert (
                await conn.execute(
                    text(
                        "SELECT indisvalid AND indisready FROM pg_index "
                        "WHERE indexrelid='uq_trades_id_coin_user'::regclass"
                    )
                )
            ).scalar_one()
    finally:
        await migrate("head")
