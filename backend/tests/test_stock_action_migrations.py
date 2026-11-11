"""Real isolated PostgreSQL accounting invariants and privilege boundaries."""

from collections.abc import AsyncIterator
from decimal import Decimal
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
    eid, _, rid = await event(conn, cid)
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
    params = {"e": eid, "s": sid, "r": rid, "u": uid, "f": "a" * 64}
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
            "stock_action_observations(source_id,revision_id,mutation_id,observed_at,admission_generation,source_kind,cycle_id)"
            " VALUES (:s,:r,'m',now(),1,'replay','cycle')"
        )
    elif target == "split":
        sql = (
            "INSERT INTO "
            "stock_split_applications(economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at)"
            " VALUES (:e,:r,'2','1',now(),0,1,0,:f,:f,now())"
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
        assert await _versions(engine) == ["0011"]
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
