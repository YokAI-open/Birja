"""Finite migration orchestration: trusted bytes, child failure and lock cleanup.

Subprocess/engine construction are isolated here. Authentication and catalogue
checks are separately exercised against PostgreSQL, never a fabricated ledger.
"""

import runpy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db import portfolio_migrate as migration
from tests.portfolio_fixtures import migrate_to, portfolio_migration_db
from tests.test_migrations import test_migration_url

__all__ = ["portfolio_migration_db"]

URL = "postgresql+asyncpg://birja_migrator:synthetic@postgres:5432/birja"


def test_trusted_source_requires_exact_regular_files(tmp_path):
    migration.require_source()
    for name in migration.SOURCE:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((migration.BACKEND_DIR / name).read_bytes())
    migration.require_source(tmp_path)
    path = tmp_path / next(iter(migration.SOURCE))
    original = path.read_bytes()
    path.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="Untrusted"):
        migration.require_source(tmp_path)
    path.unlink()
    with pytest.raises(ValueError, match="Untrusted"):
        migration.require_source(tmp_path)
    path.symlink_to(migration.BACKEND_DIR / next(iter(migration.SOURCE)))
    with pytest.raises(ValueError, match="Untrusted"):
        migration.require_source(tmp_path)


@pytest.mark.parametrize(
    "env,url",
    [("test", URL)]
    + [
        ("prod", URL.replace(old, new))
        for old, new in (
            ("@postgres:", "@other:"),
            (":5432/", ":5433/"),
            ("//birja_migrator:", "//other:"),
            ("/birja", "/other"),
            (":synthetic@", ":@"),
            ("/birja", "/birja?options=x"),
        )
    ],
)
async def test_misrouted_identity_never_constructs_engine(env, url):
    with patch.object(migration, "create_async_engine") as create:
        with pytest.raises(ValueError, match="Explicit Compose"):
            await migration.migrate(SimpleNamespace(env=env, database_url=url))
        create.assert_not_called()


@pytest.mark.parametrize(
    "outcome", ["success", "timeout", "child", "revision", "preflight", "identity"]
)
async def test_child_finalization_and_failure_cleanup(outcome, capsys):
    conn = MagicMock()
    conn.execute = AsyncMock()
    conn.commit = AsyncMock()
    conn.rollback = AsyncMock()
    engine = MagicMock()
    engine.connect.return_value.__aenter__ = AsyncMock(return_value=conn)
    engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)
    engine.dispose = AsyncMock()
    child = SimpleNamespace(
        communicate=AsyncMock(side_effect=TimeoutError if outcome == "timeout" else None),
        kill=MagicMock(),
        wait=AsyncMock(),
        returncode=1 if outcome == "child" else 0,
    )
    identity = AsyncMock(
        side_effect=ValueError("identity")
        if outcome == "identity"
        else ["0014", "0016" if outcome == "revision" else "0017"]
    )
    if outcome == "preflight":

        async def execute(statement):
            if str(statement) == migration.PREFLIGHT_SQL:
                raise ValueError("preflight")

        conn.execute.side_effect = execute
    with (
        patch.object(migration, "create_async_engine", return_value=engine) as create,
        patch.object(migration, "database_connect_args", return_value={}) as args,
        patch.object(migration, "require_migrator", identity),
        patch.object(
            migration.asyncio, "create_subprocess_exec", AsyncMock(return_value=child)
        ) as spawn,
    ):
        settings = SimpleNamespace(env="prod", database_url=URL)
        if outcome == "success":
            await migration.migrate(settings)
            assert (
                capsys.readouterr().out
                == "portfolio_migration_to_final=true source_revision=0014 final=0017\n"
            )
            conn.rollback.assert_awaited_once()
        else:
            with pytest.raises(ValueError):
                await migration.migrate(settings)
            assert capsys.readouterr().out == ""
        args.assert_called_once_with(settings, migration=True)
        create.assert_called_once_with(URL, connect_args={})
    engine.dispose.assert_awaited_once()
    statements = [str(c.args[0]) for c in conn.execute.call_args_list]
    if outcome == "identity":
        assert statements == []
        spawn.assert_not_awaited()
    else:
        assert statements[0] == "SELECT pg_advisory_lock(1026016017)"
        assert statements[-1] == "SELECT pg_advisory_unlock(1026016017)"
        assert conn.commit.await_count == 2
        assert spawn.call_args.args[-2:] == ("upgrade", "0017")
        assert spawn.call_args.kwargs["cwd"] == migration.BACKEND_DIR
    assert child.kill.call_count == (outcome == "timeout")
    assert child.wait.await_count == (outcome == "timeout")


def test_cli_reports_only_redacted_failure_and_checks_source_first(capsys):
    async def fail(_settings):
        raise ValueError("sensitive child diagnostics")

    with (
        patch.object(migration, "require_source") as source,
        patch.object(migration, "get_settings", return_value=object()),
        patch.object(migration, "migrate", side_effect=fail),
        pytest.raises(SystemExit) as failure,
    ):
        migration.main()
    source.assert_called_once()
    assert failure.value.code == 1
    assert capsys.readouterr().err == "portfolio_migration_failed=true diagnostics=redacted\n"


def test_module_entrypoint_invokes_the_finite_main(monkeypatch):
    monkeypatch.setenv("ENV", "test")
    with patch("asyncio.run", side_effect=lambda coroutine: coroutine.close()) as run:
        runpy.run_module("app.db.portfolio_migrate", run_name="__main__")
    run.assert_called_once()


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "schema",
        "versions",
        "relation",
        "owner",
        "routine",
        "routine_owner",
        "identity",
        "fresh",
        "missing",
    ],
)
async def test_actual_authenticated_migrator_catalogue_refusals(portfolio_migration_db, damage):
    """Use a real credentialed restricted connection and real hostile catalogues."""
    if damage not in {"fresh", "missing"}:
        await migrate_to("0017")
    async with portfolio_migration_db.begin() as admin:
        assert (await admin.execute(text("SELECT current_database(),session_user"))).one() == (
            "birja_test",
            "birja_test",
        )
        await admin.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
        await admin.execute(
            text("REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler")
        )
        if damage == "schema":
            await admin.execute(text("GRANT CREATE ON SCHEMA public TO birja_app"))
        elif damage == "versions":
            await admin.execute(text("INSERT INTO alembic_version VALUES ('0013')"))
        elif damage == "relation":
            await admin.execute(text("CREATE TABLE public.unexpected_relation(id bigint)"))
        elif damage == "owner":
            await admin.execute(text("ALTER TABLE public.accounts OWNER TO birja_test"))
        elif damage == "routine":
            await admin.execute(
                text(
                    "CREATE FUNCTION public.unexpected_routine() RETURNS int "
                    "LANGUAGE sql AS 'SELECT 1'"
                )
            )
        elif damage == "routine_owner":
            await admin.execute(
                text("ALTER FUNCTION public.check_portfolio_financial_write() OWNER TO birja_test")
            )
    child = create_async_engine(test_migration_url())
    try:
        if damage == "identity":
            async with portfolio_migration_db.connect() as conn:
                with pytest.raises(ValueError, match="Authenticated restricted"):
                    await migration.require_migrator(conn)
        else:
            async with child.connect() as conn:
                assert (await conn.execute(text("SELECT session_user,current_user"))).one() == (
                    "birja_migrator",
                    "birja_migrator",
                )
                if damage in {None, "fresh"}:
                    assert await migration.require_migrator(conn, fresh=damage == "fresh") == (
                        None if damage == "fresh" else "0017"
                    )
                else:
                    with pytest.raises(ValueError):
                        await migration.require_migrator(conn)
    finally:
        await child.dispose()
