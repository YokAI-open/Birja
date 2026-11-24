"""Fail closed before connecting; exercise every role refusal without repair."""

import runpy
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db import dev_bootstrap
from app.db.dev_bootstrap import bootstrap, main

URL = "postgresql+asyncpg://birja:synthetic@postgres:5432/birja"
FLAGS = (
    "rolcanlogin",
    "rolinherit",
    "rolsuper",
    "rolcreatedb",
    "rolcreaterole",
    "rolreplication",
    "rolbypassrls",
)


@pytest.mark.parametrize(
    "env,url",
    [("prod", URL), ("test", URL), ("", URL)]
    + [
        ("dev", URL.replace(old, new))
        for old, new in [
            ("+asyncpg", ""),
            ("@postgres:", "@other:"),
            (":5432/", ":5433/"),
            ("//birja:", "//other:"),
            ("/birja", "/other"),
            (":synthetic@", ":@"),
            ("/birja", "/birja?sslmode=require"),
        ]
    ],
)
async def test_rejects_misrouted_input_before_connect(env, url):
    with patch("app.db.dev_bootstrap.asyncpg.connect", new_callable=AsyncMock) as connect:
        with pytest.raises(ValueError):
            await bootstrap(env, url)
        connect.assert_not_called()


def connection(role=None, *, administrator=True, membership=False):
    conn = MagicMock()
    conn.transaction.return_value.__aenter__ = AsyncMock()
    conn.transaction.return_value.__aexit__ = AsyncMock(return_value=False)
    conn.fetchval = AsyncMock(side_effect=[administrator, membership])
    conn.fetchrow = AsyncMock(return_value=role)
    conn.execute = AsyncMock()
    conn.close = AsyncMock()
    return conn


async def test_creates_only_absent_canonical_safe_owner():
    conn = connection()
    with patch("app.db.dev_bootstrap.asyncpg.connect", AsyncMock(return_value=conn)):
        await bootstrap("dev", URL)
    sql = [call.args[0] for call in conn.execute.call_args_list]
    assert sql == [
        "SELECT pg_catalog.pg_advisory_xact_lock(1026016001)",
        "CREATE ROLE birja_migrator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB "
        "NOCREATEROLE NOREPLICATION NOBYPASSRLS",
    ]
    conn.close.assert_awaited_once()


class DriverRecord(dict):
    """asyncpg records iterate values rather than column names."""

    def __iter__(self):
        return iter(self.values())


@pytest.mark.parametrize("flag", [None, "membership", *FLAGS])
async def test_existing_role_is_checked_without_repair(flag):
    role = DriverRecord({"oid": 123, **dict.fromkeys(FLAGS, False)})
    if flag in FLAGS:
        role[flag] = True
    conn = connection(role, membership=flag == "membership")
    with patch("app.db.dev_bootstrap.asyncpg.connect", AsyncMock(return_value=conn)):
        if flag is None:
            await bootstrap("dev", URL)
        else:
            with pytest.raises(ValueError, match="Unsafe existing"):
                await bootstrap("dev", URL)
    assert conn.execute.await_count == 1
    assert "pg_advisory_xact_lock" in conn.execute.call_args.args[0]
    conn.close.assert_awaited_once()


async def test_wrong_actual_admin_refuses_before_any_write():
    conn = connection(administrator=False)
    with (
        patch("app.db.dev_bootstrap.asyncpg.connect", AsyncMock(return_value=conn)),
        pytest.raises(ValueError, match="administrator"),
    ):
        await bootstrap("dev", URL)
    conn.execute.assert_not_awaited()
    conn.close.assert_awaited_once()


def test_main_uses_only_explicit_environment(monkeypatch):
    monkeypatch.setenv("ENV", "prod")
    monkeypatch.setenv("DATABASE_URL", URL)
    with pytest.raises(ValueError, match="local Compose"):
        main([])
    monkeypatch.delenv("ENV")
    monkeypatch.delenv("DATABASE_URL")
    with (
        patch(
            "app.db.dev_bootstrap.asyncio.run", side_effect=lambda coroutine: coroutine.close()
        ) as run,
        patch.dict(sys.modules),
        patch.object(sys, "argv", ["dev_bootstrap"]),
    ):
        del sys.modules["app.db.dev_bootstrap"]
        runpy.run_module("app.db.dev_bootstrap", run_name="__main__")
    run.assert_called_once()


@pytest.mark.parametrize(
    "failure", [None, "missing_owner", "schema", "relations", "identity", "functions"]
)
async def test_postmigration_grants_only_after_all_fixed_provenance_checks(failure):
    role = (
        None
        if failure == "missing_owner"
        else DriverRecord({"oid": 123, **dict.fromkeys(FLAGS, False)})
    )
    conn = connection(role)
    checks = [name != failure for name in ("schema", "relations", "identity", "functions")]
    conn.fetchval = AsyncMock(side_effect=[True, False, "0014", *checks] if role else [True])
    with patch("app.db.dev_bootstrap.asyncpg.connect", AsyncMock(return_value=conn)):
        if failure:
            with pytest.raises(ValueError, match="refusing"):
                await bootstrap("dev", URL, after_migrations=True)
        else:
            await bootstrap("dev", URL, after_migrations=True)
    sql = [call.args[0] for call in conn.execute.call_args_list]
    assert len(sql) == (6 if failure is None else 1)
    if failure is None:
        assert all("TO birja_migrator" in statement for statement in sql[1:])
        assert sql[-1] == "GRANT UPDATE(cash) ON public.accounts TO birja_migrator"
        assert not any("ALL" in statement or "GRANT OPTION" in statement for statement in sql)
    else:
        assert not any("GRANT" in statement for statement in sql)
    conn.close.assert_awaited_once()


def test_postmigration_cli_mode_is_explicit(monkeypatch):
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("DATABASE_URL", URL)
    with patch("app.db.dev_bootstrap.bootstrap", new_callable=AsyncMock) as start:
        main(["--after-migrations"])
    start.assert_awaited_once_with("dev", URL, after_migrations=True, migrate=False)


@pytest.mark.parametrize(
    "revision", ["0015", "0016", "0017", "0018", "0019", "0020", "0021", "0022", "0023", "0024"]
)
async def test_postmigration_portfolio_revision_dispatch_is_explicit(revision):
    role = DriverRecord({"oid": 123, **dict.fromkeys(FLAGS, False)})
    conn = connection(role)
    conn.fetchval = AsyncMock(side_effect=[True, False, revision])
    with (
        patch("app.db.dev_bootstrap.asyncpg.connect", AsyncMock(return_value=conn)),
        patch("app.db.dev_bootstrap._authorize_portfolios", new_callable=AsyncMock) as final,
        patch("app.db.dev_bootstrap._authorize_dividends", new_callable=AsyncMock) as legacy,
    ):
        if revision in {"0023", "0024"}:
            await bootstrap("dev", URL, after_migrations=True)
            final.assert_awaited_once_with(conn, revision)
        else:
            with pytest.raises(
                ValueError,
                match="forward migration" if revision in {"0017", "0020"} else "migration_only",
            ):
                await bootstrap("dev", URL, after_migrations=True)
            final.assert_not_awaited()
        legacy.assert_not_awaited()
    assert conn.execute.await_count == 1  # No grant before revision admission.
    conn.close.assert_awaited_once()


async def test_current_final_acl_mismatch_refuses_and_closes_transaction():
    """A current revision is not enough when the resulting privileges disagree."""
    role = DriverRecord({"oid": 123, **dict.fromkeys(FLAGS, False)})
    conn = connection(role)
    conn.fetchval = AsyncMock(side_effect=[True, False, "0024", "0" * 64])
    with (
        patch("app.db.dev_bootstrap.asyncpg.connect", AsyncMock(return_value=conn)),
        pytest.raises(ValueError, match="Unexpected final management grants"),
    ):
        # Keep the real final authorizer: it must check the resulting ACL after
        # executing the canonical preflight/grants, rather than report success.
        await bootstrap("dev", URL, after_migrations=True)
    assert [call.args[0] for call in conn.execute.call_args_list] == [
        "SELECT pg_catalog.pg_advisory_xact_lock(1026016001)",
        dev_bootstrap.PORTFOLIO_PREFLIGHT_SQL["0024"],
        dev_bootstrap.GRANTS_0023_SQL,
    ]
    assert conn.fetchval.await_count == 4
    assert conn.fetchval.call_args.args == (dev_bootstrap.ACL_SQL,)
    assert conn.transaction.return_value.__aexit__.await_args.args[0] is ValueError
    conn.close.assert_awaited_once()


@pytest.mark.parametrize(
    "outcome",
    [
        "success",
        "timeout",
        "child",
        "spawn",
        "revision",
        "role",
        "membership",
        "relation",
        "routine",
    ],
)
async def test_finite_dev_migration_never_leaves_login_enabled(outcome, capsys):
    """Child orchestration seams; real SQL provenance has independent PG tests."""
    conn = connection()
    conn.fetchval = AsyncMock(side_effect=[True, "PASSWORD-SQL"])
    if outcome == "membership":
        conn.fetchval = AsyncMock(side_effect=[True, True])
    elif outcome == "role":
        conn.fetchval = AsyncMock(return_value=True)
    elif outcome == "success":
        # Existing roles exercise the negative membership result as well as
        # creation of the absent canonical role on subsequent iterations.
        conn.fetchval = AsyncMock(side_effect=[True, False, "PASSWORD-SQL"])
    conn.fetch = AsyncMock(
        side_effect=[
            [("bad" if outcome == "revision" else "0014",)],
            [
                ("unexpected" if outcome == "relation" else "accounts", "r", "birja"),
                ("accounts_id_seq", "S", "birja_migrator"),
            ],
            [
                (
                    "bad()" if outcome == "routine" else "check_portfolio_financial_write()",
                    "check_portfolio_financial_write",
                    "birja_migrator",
                )
            ],
        ]
    )
    role = DriverRecord({"oid": 123, **dict.fromkeys(FLAGS[1:], False)})
    if outcome == "role":
        role["rolsuper"] = True
    conn.fetchrow = AsyncMock(
        side_effect=[role, None, None, None]
        if outcome in {"success", "role", "membership"}
        else [None] * 4
    )
    child = MagicMock()
    child.communicate = AsyncMock(side_effect=TimeoutError if outcome == "timeout" else None)
    child.wait = AsyncMock()
    child.returncode = int(outcome == "child")
    with (
        patch.object(
            dev_bootstrap.asyncio,
            "create_subprocess_exec",
            AsyncMock(
                side_effect=OSError("spawn") if outcome == "spawn" else None, return_value=child
            ),
        ) as spawn,
        patch.object(dev_bootstrap, "_authorize_portfolios", new_callable=AsyncMock) as authorize,
        patch.object(dev_bootstrap.secrets, "token_hex", return_value="ephemeral"),
    ):
        if outcome == "success":
            await dev_bootstrap._migrate_dev(conn, URL)
            authorize.assert_awaited_once_with(conn, "0024")
            assert (
                capsys.readouterr().out
                == "dev_final_migration=true source_revision=0014 final=0024\n"
            )
            assert "birja_migrator:ephemeral@" in spawn.call_args.kwargs["env"]["DATABASE_URL"]
        else:
            with pytest.raises((ValueError, OSError)):
                await dev_bootstrap._migrate_dev(conn, URL)
            authorize.assert_not_awaited()
            assert capsys.readouterr().out == ""
    sql = [str(c.args[0]) for c in conn.execute.call_args_list]
    if outcome == "revision":
        assert sql == []
    else:
        assert sql[0] == "SELECT pg_advisory_lock(1026016001)"
        assert sql[-1] == "SELECT pg_advisory_unlock(1026016001)"
    if outcome in {"success", "timeout", "child", "spawn"}:
        assert "ALTER ROLE birja_migrator NOLOGIN PASSWORD NULL" in sql
    else:
        spawn.assert_not_awaited()
    assert child.kill.call_count == int(outcome == "timeout")
    assert child.wait.await_count == int(outcome == "timeout")


async def test_bootstrap_explicit_migrate_dispatch_closes_parent():
    conn = connection()
    with (
        patch.object(dev_bootstrap.asyncpg, "connect", AsyncMock(return_value=conn)),
        patch.object(dev_bootstrap, "_migrate_dev", new_callable=AsyncMock) as migrate,
    ):
        await bootstrap("dev", URL, migrate=True)
    migrate.assert_awaited_once_with(conn, URL)
    conn.close.assert_awaited_once()


async def test_finite_dev_migration_fresh_database_reports_none(capsys):
    conn = connection()
    conn.fetchval = AsyncMock(side_effect=[False, "PASSWORD-SQL"])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetch = AsyncMock(side_effect=[[], []])
    child = MagicMock(returncode=0)
    child.communicate = AsyncMock()
    with (
        patch.object(
            dev_bootstrap.asyncio, "create_subprocess_exec", AsyncMock(return_value=child)
        ),
        patch.object(dev_bootstrap, "_authorize_portfolios", new_callable=AsyncMock),
    ):
        await dev_bootstrap._migrate_dev(conn, URL)
    assert "source_revision=None final=0024" in capsys.readouterr().out


async def test_portfolio_authorization_runs_actual_final_sql(engine, migrated):
    """Use asyncpg's real multi-statement protocol, not a mocked grant result."""
    from sqlalchemy import text

    async with engine.connect() as conn, conn.begin():
        raw = await conn.get_raw_connection()
        await dev_bootstrap._authorize_portfolios(raw.driver_connection, "0024")
        assert not (
            await conn.execute(
                text("SELECT has_table_privilege('birja_scheduler','accounts','UPDATE')")
            )
        ).scalar_one()
        assert (
            await conn.execute(
                text(
                    "SELECT has_function_privilege('birja_scheduler',"
                    "'lock_stock_portfolio_roots(bigint)','EXECUTE')"
                )
            )
        ).scalar_one()
