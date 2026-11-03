"""Synthetic trust and execution-path contracts; no real service credentials."""

import asyncio
import runpy
import ssl
import subprocess
from pathlib import Path

import pytest
from alembic import context
from alembic.config import Config
from pydantic import ValidationError

from app.core.config import SchedulerSettings, Settings
from app.db.connection import database_connect_args


def create_test_ca(path: Path) -> str:
    ca = path / "synthetic-ca.pem"
    subprocess.run(  # noqa: S603 - fixed openssl command and pytest-owned temporary paths
        [
            "/usr/bin/openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(path / "synthetic-key.pem"),
            "-out",
            str(ca),
            "-days",
            "1",
            "-subj",
            "/CN=Birja synthetic test CA",
            "-addext",
            "basicConstraints=critical,CA:TRUE",
        ],
        check=True,
        capture_output=True,
    )
    return str(ca)


@pytest.fixture
def ca(tmp_path: Path) -> str:
    return create_test_ca(tmp_path)


def make_settings(kind: type[Settings] | type[SchedulerSettings], **kw: object):
    args = {
        "env": "prod",
        "database_url": "postgresql+asyncpg://synthetic:UrlSecret@postgres/synthetic",
        "redis_url": "redis://localhost/0",
        **kw,
    }
    if kind is Settings:
        args.update(
            otp_hmac_secret="o" * 40,
            jwt_secret="j" * 40,
            email_backend="resend",
            resend_api_key="synthetic",
            email_from="a@b.co",
        )
    return kind(**args)


@pytest.mark.parametrize("kind", [Settings, SchedulerSettings])
def test_production_requires_ca(kind) -> None:
    with pytest.raises(ValidationError, match="database_ssl_ca_file") as exc:
        make_settings(kind)
    assert "UrlSecret" not in str(exc.value)


@pytest.mark.parametrize("kind", [Settings, SchedulerSettings])
@pytest.mark.parametrize("bad", ["missing", "directory", "malformed", "unreadable"])
def test_invalid_trust_fails_closed(kind, bad: str, tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "private-trust-path"
    if bad == "directory":
        path.mkdir()
    elif bad == "malformed":
        path.write_text("not a certificate")
    elif bad == "unreadable":
        path.write_text("not readable")
        # Deterministic even when pytest runs as root.
        monkeypatch.setattr(
            ssl,
            "create_default_context",
            lambda **kw: (_ for _ in ()).throw(PermissionError("private-trust-path")),
        )
    with pytest.raises(ValidationError, match="database_ssl_ca_file") as exc:
        make_settings(kind, database_ssl_ca_file=str(path))
    assert "UrlSecret" not in str(exc.value)
    assert "private-trust-path" not in str(exc.value)


@pytest.mark.parametrize("kind", [Settings, SchedulerSettings])
@pytest.mark.parametrize(
    "query",
    [
        "sslmode=disable",
        "sslmode=verify-full",
        "ssl=prefer",
        "ssl=require",
        "sslrootcert=private",
        "s%73l=disable",
    ],
)
def test_url_cannot_override_tls(kind, query: str, ca: str) -> None:
    with pytest.raises(ValidationError, match="TLS.*query") as exc:
        make_settings(
            kind,
            database_ssl_ca_file=ca,
            database_url=f"postgresql+asyncpg://u:UrlSecret@postgres/db?{query}",
        )
    assert "UrlSecret" not in str(exc.value)


@pytest.mark.parametrize("kind", [Settings, SchedulerSettings])
@pytest.mark.parametrize("migration", [False, True])
def test_verified_context_and_bounded_timeouts(kind, migration: bool, ca: str) -> None:
    settings = make_settings(kind, database_ssl_ca_file=ca)
    args = database_connect_args(settings, migration=migration)
    ctx = args.get("ssl")
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True
    assert ctx.minimum_version >= ssl.TLSVersion.TLSv1_2
    assert ctx.cert_store_stats()["x509_ca"] == 1
    assert args["timeout"] == 5
    assert args["server_settings"]["idle_in_transaction_session_timeout"] == "30000"
    assert args["server_settings"]["statement_timeout"] == ("120000" if migration else "30000")
    if migration:
        assert args["server_settings"]["lock_timeout"] == "5000"
    assert "UrlSecret" not in repr(settings)


@pytest.mark.parametrize("env", ["dev", "test"])
@pytest.mark.parametrize("kind", [Settings, SchedulerSettings])
def test_nonproduction_keeps_prior_policy(kind, env: str) -> None:
    assert database_connect_args(make_settings(kind, env=env)) == {
        "timeout": 5,
        "server_settings": {
            "statement_timeout": "30000",
            "idle_in_transaction_session_timeout": "30000",
        },
    }


def test_explicit_nonproduction_ca_is_verified(ca: str) -> None:
    args = database_connect_args(
        make_settings(SchedulerSettings, env="test", database_ssl_ca_file=ca)
    )
    assert isinstance(args.get("ssl"), ssl.SSLContext)
    assert args["ssl"].check_hostname


def test_helper_rechecks_trust_at_engine_creation(ca: str) -> None:
    settings = make_settings(SchedulerSettings, database_ssl_ca_file=ca)
    Path(ca).unlink()
    with pytest.raises(ValueError, match="database_ssl_ca_file"):
        database_connect_args(settings)


@pytest.mark.parametrize("consumer", ["backend", "scheduler", "migration"])
async def test_actual_engine_paths_use_shared_policy(consumer: str, ca: str, monkeypatch) -> None:
    from app import main
    from app.tasks import scheduler

    settings = make_settings(Settings, database_ssl_ca_file=ca)
    calls = []
    real_policy = database_connect_args

    def policy(settings, *, migration=False):
        args = real_policy(settings, migration=migration)
        calls.append((migration, args))
        return args

    class EngineReached(Exception):
        pass

    def engine(*args, **kwargs):
        assert len(calls) == 1
        assert kwargs["connect_args"] is calls[0][1]
        assert isinstance(kwargs["connect_args"].get("ssl"), ssl.SSLContext)
        raise EngineReached

    # Stop at the engine factory: exercise real startup code without any network I/O.
    if consumer == "backend":
        monkeypatch.setattr(main, "database_connect_args", policy, raising=False)
        monkeypatch.setattr(main, "create_async_engine", engine)
        with pytest.raises(EngineReached):
            async with main.lifespan(main.create_app(settings)):
                pass
    elif consumer == "scheduler":
        monkeypatch.setattr(scheduler, "database_connect_args", policy, raising=False)
        monkeypatch.setattr(scheduler, "get_scheduler_settings", lambda: settings)
        monkeypatch.setattr(scheduler, "create_async_engine", engine)
        with pytest.raises(EngineReached):
            await scheduler.amain(asyncio.Event())
    else:
        import sqlalchemy.ext.asyncio as sqlalchemy_async

        import app.core.config as config_module
        import app.db.connection as connection

        cfg = Config()
        monkeypatch.setattr(context, "config", cfg, raising=False)
        monkeypatch.setattr(context, "is_offline_mode", lambda: False)
        monkeypatch.setattr(config_module, "get_settings", lambda: settings)
        monkeypatch.setattr(connection, "database_connect_args", policy)
        monkeypatch.setattr(sqlalchemy_async, "async_engine_from_config", engine)
        # env.py is synchronous Alembic entrypoint, so run it off this event loop.
        with pytest.raises(EngineReached):
            await asyncio.to_thread(
                runpy.run_path, str(Path(__file__).parents[1] / "alembic/env.py")
            )
    assert calls[0][0] is (consumer == "migration")
