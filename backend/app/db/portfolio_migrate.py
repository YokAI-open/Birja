"""Explicit authenticated migration-to-final; never a runtime admission bypass."""

import asyncio
import hashlib
import os
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import Settings, get_settings
from app.db.connection import database_connect_args
from app.db.dev_bootstrap import FUNCTION_SIGNATURES, TABLES
from app.db.portfolio_bootstrap import PREFLIGHT_SQL

BACKEND_DIR = Path(__file__).resolve().parents[2]
SOURCE = {
    "alembic/versions/0015_portfolio_expansion.py": (
        "9811795856a2fc96485cff103c0750622501535a480af39d916a3aaa1755ebb8"
    ),
    "alembic/versions/0016_portfolio_association.py": (
        "81fa8bcbc59a1a1875d79b53ba6ca7ade32449a16128837f3823e59087d1a327"
    ),
    "alembic/versions/0017_portfolio_ownership.py": (
        "df84ca54126423c9de52821906c93a79b3251983a2a9b032da939419b9ee7ee9"
    ),
    "alembic/sql/0017_stock_portfolio.sql": (
        "265262fa8377b801605867ebe692accd43acc29a8764f401633ffdabff25383e"
    ),
    "alembic/sql/0017_dividend_portfolio.sql": (
        "fc5cb6864bb553c5116f2580a79ece2ea86188aba6eb309af857b68b88918734"
    ),
}


def require_source(root: Path = BACKEND_DIR) -> None:
    for name, digest in SOURCE.items():
        path = root / name
        if path.is_symlink() or not path.is_file() or path.resolve().parent != path.parent:
            raise ValueError("Untrusted portfolio migration source")
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Untrusted portfolio migration source")


async def require_migrator(conn: AsyncConnection, *, fresh: bool = False) -> str | None:
    identity = (
        await conn.execute(
            text("""SELECT session_user,current_user,rolcanlogin,
      rolinherit,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,
      EXISTS(SELECT FROM pg_auth_members WHERE roleid=r.oid OR member=r.oid)
      FROM pg_roles r WHERE rolname=session_user""")
        )
    ).one()
    if identity[:3] != ("birja_migrator", "birja_migrator", True) or any(identity[3:]):
        raise ValueError("Authenticated restricted migrator required")
    if not (
        await conn.execute(
            text("""SELECT
      (SELECT count(*)=1 AND bool_and(pg_get_userbyid(nspowner)
       IN ('birja','pg_database_owner')) FROM pg_namespace WHERE nspname='public')
      AND NOT EXISTS(SELECT FROM pg_namespace n,
       LATERAL aclexplode(coalesce(n.nspacl,acldefault('n',n.nspowner))) x
       WHERE n.nspname='public' AND x.privilege_type='CREATE' AND x.grantee IN
        (0,'birja_app'::regrole,'birja_scheduler'::regrole))
      AND NOT EXISTS(SELECT FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler')
       AND (rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole
        OR rolreplication OR rolbypassrls))
      AND NOT EXISTS(SELECT FROM pg_auth_members WHERE roleid IN
       (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler'))
       OR member IN (SELECT oid FROM pg_roles WHERE rolname IN ('birja_app','birja_scheduler')))
      """)
        )
    ).scalar_one():
        raise ValueError("Unsafe migration schema or runtime roles")
    revision = None
    if (await conn.execute(text("SELECT to_regclass('public.alembic_version')"))).scalar():
        versions = (
            (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalars().all()
        )
        if len(versions) != 1 or versions[0] not in {f"{n:04}" for n in range(7, 18)}:
            raise ValueError("Unsupported portfolio migration revision")
        revision = versions[0]
    elif not fresh:
        raise ValueError("Populated migration revision required")
    rows = (
        await conn.execute(
            text("""SELECT c.relname,c.relkind::text,
      pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public' AND c.relkind IN ('r','S')""")
        )
    ).all()
    for name, kind, owner in rows:
        allowed = TABLES if kind == "r" else {t + "_id_seq" for t in TABLES}
        if name not in allowed or owner != "birja_migrator":
            raise ValueError("Unexpected migration relation ownership")
    rows = (
        await conn.execute(
            text("""SELECT p.oid::regprocedure::text,pg_get_userbyid(p.proowner)
      FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
      WHERE n.nspname='public'""")
        )
    ).all()
    if any(
        signature.replace("public.", "").replace(" ", "") not in FUNCTION_SIGNATURES
        or owner != "birja_migrator"
        for signature, owner in rows
    ):
        raise ValueError("Unexpected migration routine ownership")
    return revision


async def migrate(settings: Settings) -> None:
    url = make_url(settings.database_url)
    if (
        settings.env not in {"dev", "prod"}
        or url.host != "postgres"
        or url.port != 5432
        or url.username != "birja_migrator"
        or url.database != "birja"
        or not url.password
        or url.query
    ):
        raise ValueError("Explicit Compose migration identity required")
    engine = create_async_engine(
        settings.database_url, connect_args=database_connect_args(settings, migration=True)
    )
    try:
        async with engine.connect() as conn:
            revision = await require_migrator(conn, fresh=settings.env == "dev")
            await conn.execute(text("SELECT pg_advisory_lock(1026016017)"))
            await conn.commit()
            try:
                child = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "alembic",
                    "upgrade",
                    "0017",
                    cwd=BACKEND_DIR,
                    env=dict(os.environ),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                try:
                    await asyncio.wait_for(child.communicate(), timeout=180)
                except TimeoutError:
                    child.kill()
                    await child.wait()
                    raise ValueError(
                        "Portfolio finalization timed out; resume explicitly"
                    ) from None
                if child.returncode:
                    raise ValueError("Portfolio finalization failed; diagnostics withheld")
                if await require_migrator(conn) != "0017":
                    raise ValueError("Final portfolio revision absent")
                await conn.execute(text(PREFLIGHT_SQL))
                await conn.rollback()
            finally:
                await conn.execute(text("SELECT pg_advisory_unlock(1026016017)"))
                await conn.commit()
            print(
                "portfolio_migration_to_final=true source_revision=" + str(revision) + " final=0017"
            )
    finally:
        await engine.dispose()


def main() -> None:
    require_source()
    try:
        asyncio.run(migrate(get_settings()))
    except Exception:
        print("portfolio_migration_failed=true diagnostics=redacted", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
