"""Fail closed before connecting; exercise every role refusal without repair."""

import runpy
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
        main()
    monkeypatch.delenv("ENV")
    monkeypatch.delenv("DATABASE_URL")
    with (
        patch(
            "app.db.dev_bootstrap.asyncio.run", side_effect=lambda coroutine: coroutine.close()
        ) as run,
        patch.dict(sys.modules),
    ):
        del sys.modules["app.db.dev_bootstrap"]
        runpy.run_module("app.db.dev_bootstrap", run_name="__main__")
    run.assert_called_once()
