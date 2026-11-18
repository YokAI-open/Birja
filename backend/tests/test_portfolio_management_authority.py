"""Explicit0020 restricted-role proof; no partial current-app admission."""

import asyncio
import hashlib
import secrets
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine

from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import run_test_migration, test_migration_url

BACKEND = Path(__file__).resolve().parents[1]
CREATE = "SELECT * FROM public.create_portfolio(:u,:k,:n,:d)"
EDIT = "SELECT * FROM public.update_portfolio_metadata(:u,:p,:n,:d,:hn,:hd)"


@pytest_asyncio.fixture
async def authority(engine):
    await reset_disposable_schema(engine)
    await asyncio.to_thread(run_test_migration, "0019")
    if (BACKEND / "alembic/versions/0020_portfolio_management_authority.py").exists():
        await asyncio.to_thread(run_test_migration, "0020")
    password = secrets.token_hex(32)
    async with engine.begin() as conn:
        # Disposable authenticated login, rather than SET ROLE or caller GUCs.
        await conn.execute(text(f"ALTER ROLE birja_app LOGIN PASSWORD '{password}'"))  # noqa: S608
        await conn.execute(text("GRANT SELECT,INSERT ON users TO birja_app"))
        await conn.execute(text("GRANT USAGE ON SEQUENCE users_id_seq TO birja_app"))
        await conn.execute(text("GRANT SELECT ON accounts TO birja_app"))
        await conn.execute(text("GRANT UPDATE(cash) ON accounts TO birja_app"))
        await conn.execute(
            text("GRANT SELECT,INSERT,UPDATE ON auth_sessions,refresh_tokens TO birja_app")
        )
        await conn.execute(
            text("GRANT USAGE ON SEQUENCE auth_sessions_id_seq,refresh_tokens_id_seq TO birja_app")
        )
    app = create_async_engine(make_url(engine.url).set(username="birja_app", password=password))
    migrator = create_async_engine(test_migration_url())
    try:
        yield app, migrator
    finally:
        await app.dispose()
        await migrator.dispose()
        await reset_disposable_schema(engine)


async def owner(migrator):
    async with migrator.begin() as conn:
        return (
            await conn.execute(
                text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                {"e": f"authority-{uuid4()}@example.test"},
            )
        ).scalar_one()


async def create(app, uid, name="Strategy", description="", key=None):
    async with app.begin() as conn:
        return (
            await conn.execute(
                text(CREATE), {"u": uid, "k": key or uuid4(), "n": name, "d": description}
            )
        ).one()


async def reject(app, sql, params=None, *, state, message=None):
    with pytest.raises(DBAPIError) as error:
        async with app.begin() as conn:
            await conn.execute(text(sql), params or {})
    assert error.value.orig.sqlstate == state, str(error.value.orig)
    if message:
        assert message in str(error.value.orig)


async def close(migrator, root):
    async with migrator.begin() as conn:
        await conn.execute(
            text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"), {"p": root}
        )


async def test_fixed_grant_canonical_payload_and_replay_after_rename(authority):
    app, migrator = authority
    uid = await owner(migrator)
    key = uuid4()
    first = await create(app, uid, "  Straße  ", "line\r\nnext", key)
    assert (first.name, first.description, first.replayed) == ("Straße", "line\nnext", False)
    async with app.begin() as conn:
        assert (await conn.execute(text("SELECT session_user,current_user"))).one() == (
            "birja_app",
            "birja_app",
        )
        changed = (
            await conn.execute(
                text(EDIT),
                {
                    "u": uid,
                    "p": first.portfolio_id,
                    "n": "Renamed",
                    "d": "changed",
                    "hn": True,
                    "hd": True,
                },
            )
        ).one()
        assert (changed.name, changed.description) == ("Renamed", "changed")
    replay = await create(app, uid, "Straße", "line\nnext", key)
    assert (
        replay.portfolio_id,
        replay.creation_id,
        replay.name,
        replay.description,
        replay.replayed,
    ) == (first.portfolio_id, first.creation_id, "Renamed", "changed", True)
    async with migrator.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT cash,starting_cash,name_key FROM accounts WHERE id=:p"),
                {"p": first.portfolio_id},
            )
        ).one() == (10000, 10000, "renamed")
        assert (
            await conn.execute(
                text("SELECT canonical_payload,amount,origin FROM portfolio_creations")
            )
        ).one() == ({"name": "Straße", "description": "line\nnext"}, 10000, "explicit")
    await reject(
        app,
        CREATE,
        {"u": uid, "k": key, "n": "Renamed", "d": "changed"},
        state="23505",
        message="creation_key_conflict",
    )


async def test_closed_original_never_regrants_or_binds_to_reused_name(authority):
    app, migrator = authority
    uid = await owner(migrator)
    key = uuid4()
    first = await create(app, uid, key=key)
    await close(migrator, first.portfolio_id)
    replacement = await create(app, uid)
    assert replacement.portfolio_id != first.portfolio_id
    await reject(
        app,
        CREATE,
        {"u": uid, "k": key, "n": "Strategy", "d": ""},
        state="P0002",
        message="portfolio_unavailable",
    )
    async with migrator.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT count(*),sum(amount) FROM portfolio_creations WHERE user_id=:u"),
                {"u": uid},
            )
        ).one() == (2, 20000)


async def test_same_key_race_has_one_grant_and_distinct_key_race_respects_tenth_slot(authority):
    app, migrator = authority
    uid = await owner(migrator)
    key = uuid4()
    rows = await asyncio.gather(*(create(app, uid, key=key) for _ in range(8)))
    assert len({row.portfolio_id for row in rows}) == 1
    assert sum(not row.replayed for row in rows) == 1
    for n in range(8):
        await create(app, uid, f"Existing {n}")
    results = await asyncio.gather(
        *(create(app, uid, f"Race {n}") for n in range(6)), return_exceptions=True
    )
    assert sum(not isinstance(row, Exception) for row in results) == 1
    errors = [row for row in results if isinstance(row, Exception)]
    assert all(
        isinstance(error, DBAPIError) and "portfolio_limit" in str(error.orig) for error in errors
    )
    replay = await create(app, uid, key=key)
    assert replay.replayed
    async with migrator.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT count(*),sum(cash),sum(starting_cash) FROM accounts WHERE user_id=:u"),
                {"u": uid},
            )
        ).one() == (10, 100000, 100000)


async def test_active_name_race_and_same_name_other_owner(authority):
    app, migrator = authority
    uid, other = await owner(migrator), await owner(migrator)
    results = await asyncio.gather(
        create(app, uid, "Straße"), create(app, uid, "STRASSE"), return_exceptions=True
    )
    assert sum(not isinstance(row, Exception) for row in results) == 1
    error = next(row for row in results if isinstance(row, Exception))
    assert isinstance(error, DBAPIError) and "name_taken" in str(error.orig)
    assert (await create(app, other, "STRASSE")).name == "STRASSE"


@pytest.mark.parametrize(
    "name,description,key",
    [
        ("\tBad", "", uuid4()),
        ("", "", uuid4()),
        ("a" * 61, "", uuid4()),
        ("Good", "\x7f", uuid4()),
        ("Good", "d" * 1001, uuid4()),
        (None, "", uuid4()),
        ("Good", None, uuid4()),
        ("Good", "", UUID(int=0)),
        ("Good", "", None),
    ],
)
async def test_invalid_intent_leaves_no_root_or_journal(authority, name, description, key):
    app, migrator = authority
    uid = await owner(migrator)
    await reject(app, CREATE, {"u": uid, "k": key, "n": name, "d": description}, state="22023")
    async with migrator.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM accounts"))).scalar_one() == 0
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_creations"))
        ).scalar_one() == 0


async def test_owner_boundary_and_metadata_flags_preserve_finances(authority):
    app, migrator = authority
    uid, other = await owner(migrator), await owner(migrator)
    root = (await create(app, uid)).portfolio_id
    params = {"u": other, "p": root, "n": "Stolen", "d": "", "hn": True, "hd": False}
    await reject(app, EDIT, params, state="P0002", message="portfolio_unavailable")
    for changes in ({"hn": False, "hd": False}, {"hn": None}, {"p": -1}, {"u": None}):
        await reject(app, EDIT, {**params, "u": uid, **changes}, state="22023")
    async with app.begin() as conn:
        changed = (
            await conn.execute(
                text(EDIT),
                {**params, "u": uid, "n": None, "hn": False, "d": "\t\rtest", "hd": True},
            )
        ).one()
        assert (changed.name, changed.description) == ("Strategy", "\t\ntest")
        changed = (
            await conn.execute(
                text(EDIT), {**params, "u": uid, "n": None, "hn": False, "d": "", "hd": True}
            )
        ).one()
        assert changed.description == ""
    await close(migrator, root)
    await reject(app, EDIT, {**params, "u": uid}, state="P0002")
    async with migrator.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": root}
            )
        ).one() == (10000, 10000)
    await reject(app, CREATE, {"u": -1, "k": uuid4(), "n": "X", "d": ""}, state="22023")
    await reject(
        app, CREATE, {"u": 9223372036854775807, "k": uuid4(), "n": "X", "d": ""}, state="P0002"
    )


async def test_direct_money_provenance_and_private_execution_are_denied(authority):
    app, migrator = authority
    uid = await owner(migrator)
    root = (await create(app, uid)).portfolio_id
    attempts = [
        "INSERT INTO accounts(user_id,name,name_key,cash,starting_cash) "
        "VALUES (:u,'Forged','forged',10000,10000)",
        "UPDATE accounts SET starting_cash=20000 WHERE id=:p",
        "UPDATE accounts SET name='Forged',name_key='forged' WHERE id=:p",
        "UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p",
        "UPDATE users SET email='forged@example.test' WHERE id=:u",
        "INSERT INTO portfolio_initializations(user_id,origin) VALUES (:u,'legacy')",
        "INSERT INTO portfolio_creations(user_id,creation_key,portfolio_id,origin,"
        "payload_version,canonical_payload,amount) "
        "VALUES (:u,gen_random_uuid(),:p,'explicit',1,'{}',20000)",
        "UPDATE portfolio_creations SET amount=20000",
        "DELETE FROM portfolio_creations",
        "UPDATE portfolio_initializations SET origin='legacy'",
        "DELETE FROM portfolio_initializations",
        "SELECT portfolio_display_name('private')",
        "SELECT portfolio_name_key('private')",
        "SELECT portfolio_description('private')",
        "SELECT create_portfolio(:u,gen_random_uuid(),'X','',20000)",
    ]
    for sql in attempts:
        await reject(
            app,
            sql,
            {"u": uid, "p": root},
            state="42883" if sql.startswith("SELECT create_portfolio") else "42501",
        )
    async with app.begin() as conn:
        # Existing restricted cash writers still work with private normalizers.
        await conn.execute(text("UPDATE accounts SET cash=9999 WHERE id=:p"), {"p": root})
    async with migrator.begin() as conn:
        for sql in (
            "UPDATE portfolio_creations SET amount=10000",
            "DELETE FROM portfolio_creations",
        ):
            with pytest.raises(DBAPIError) as error:
                async with conn.begin_nested():
                    await conn.execute(text(sql))
            assert error.value.orig.sqlstate == "23514"


async def test_daily_new_grant_quota_is_durable_and_replay_precedes_it(authority):
    app, migrator = authority
    uid = await owner(migrator)
    key = uuid4()
    original = await create(app, uid, "Original", key=key)
    for n in range(99):
        row = await create(app, uid, f"Retained {n}")
        await close(migrator, row.portfolio_id)
    await reject(
        app,
        CREATE,
        {"u": uid, "k": uuid4(), "n": "Over quota", "d": ""},
        state="P0001",
        message="creation_quota",
    )
    assert (await create(app, uid, "Original", key=key)).portfolio_id == original.portfolio_id
    async with migrator.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT count(*),sum(amount) FROM portfolio_creations WHERE user_id=:u"),
                {"u": uid},
            )
        ).one() == (100, 1000000)


async def test_definer_catalogue_scheduler_denial_and_bounded_owner_lock(authority, engine):
    app, migrator = authority
    uid = await owner(migrator)
    async with migrator.connect() as conn:
        rows = (
            await conn.execute(
                text(
                    "SELECT p.proname,pg_get_userbyid(p.proowner),p.prosecdef,p.proconfig "
                    "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                    "WHERE n.nspname='public' AND p.proname IN "
                    "('create_portfolio','initialize_portfolio','update_portfolio_metadata') "
                    "ORDER BY p.proname"
                )
            )
        ).all()
        assert len(rows) == 3
        for _, owner_name, definer, config in rows:
            assert owner_name == "birja_migrator" and definer
            assert "search_path=pg_catalog, public, pg_temp" in config
            assert "lock_timeout=2s" in config
    async with engine.begin() as conn:
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        for query in (
            CREATE,
            "SELECT initialize_portfolio(:u)",
            "SELECT * FROM update_portfolio_metadata(:u,1,'X','',true,true)",
        ):
            with pytest.raises(DBAPIError) as error:
                async with conn.begin_nested():
                    await conn.execute(text(query), {"u": uid, "k": uuid4(), "n": "X", "d": ""})
            assert error.value.orig.sqlstate == "42501"
    async with migrator.begin() as locked:
        await locked.execute(text("SELECT id FROM users WHERE id=:u FOR UPDATE"), {"u": uid})
        await asyncio.wait_for(
            reject(app, CREATE, {"u": uid, "k": uuid4(), "n": "X", "d": ""}, state="55P03"),
            timeout=6,
        )
    assert (await create(app, uid)).name == "Strategy"


async def test_authority_source_hash_and_downgrade_refuse_before_writes(authority):
    from tests.test_portfolio_management_migrations import run_upgrade

    _, migrator = authority
    path = BACKEND / "alembic/versions/0020_portfolio_management_authority.py"
    spec = spec_from_file_location("management_authority", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    assert (
        hashlib.sha256(
            (BACKEND / "alembic/sql/0020_portfolio_management.sql").read_bytes()
        ).hexdigest()
        == module.SQL_SHA256
    )
    module.SQL_SHA256 = "0" * 64
    query = "SELECT pg_get_functiondef('create_portfolio(bigint,uuid,text,text)'::regprocedure)"
    async with migrator.begin() as conn:
        before = (await conn.execute(text(query))).scalar_one()
        with pytest.raises(RuntimeError, match="checksum mismatch"):
            await run_upgrade(conn, module)
        assert (await conn.execute(text(query))).scalar_one() == before
    uid = await owner(migrator)
    async with migrator.begin() as conn:
        await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": uid})
    with pytest.raises(RuntimeError, match="downgrade refused"):
        await asyncio.to_thread(run_test_migration, "0019", down=True)
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_creations"))
        ).scalar_one() == 1
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == "0020"
