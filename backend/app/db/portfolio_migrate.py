"""Explicit authenticated migration-to-final; never a runtime admission bypass."""

import asyncio
import hashlib
import os
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.core.config import Settings, get_settings
from app.db.connection import database_connect_args
from app.db.dev_bootstrap import migration_objects, require_complete_migration_inventory
from app.db.portfolio_bootstrap import (
    CURRENT_PORTFOLIO_REVISION,
    MIGRATION_SUPPLEMENTAL_INVENTORY_SQL,
    PORTFOLIO_PREFLIGHT_SQL,
    PRE_CLOSURE_MIGRATION_SQL,
    PREFLIGHT_0014_MIGRATION_SQL,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
SOURCE = {
    "alembic/versions/0028_portfolio_daily_values.py": (
        "99ad0ef275fc877225ea13408b5c7c407465b5fb3cbae1b6ca1aefcaa80f0879"
    ),
    "alembic/sql/0028_portfolio_daily_values.sql": (
        "6982dea7fb2590633d622f53e856a079f15510766f3043bc4dda808458846954"
    ),
    "alembic/versions/0027_stock_catalog_nyse_source.py": (
        "9ebf379351b670ac376100bb6922d5fda8a27bcecb44d031cf9db080c105c427"
    ),
    "alembic/versions/0026_stock_catalog_finance.py": (
        "b003b09d70d6ea4df410874015cbe2b8230726fe9f9d5d0c587e65f91b6e1189"
    ),
    "alembic/sql/0026_stock_catalog_finance.sql": (
        "eb4a44fd9a2812aa693607db00d7d53240d8afb4d7e0bd1305035b1e15845a04"
    ),
    "alembic/sql/0026_stock_catalog_execution.sql": (
        "b8cc7ea9d8c9227bf420778912f86d7f2cbddca0494e608cd157f929917630fe"
    ),
    "alembic/sql/0026_stock_catalog_actions.sql": (
        "6aa0c43d7554fdb7ab85ee557bfcbee6a0fc8e286a5b118d999b3937139a28c3"
    ),
    "alembic/versions/0025_stock_catalog.py": (
        "cd1890bfec3b1dc4b638fd3e86c9217d6eb331be3e895f2443b74fd88d078826"
    ),
    "alembic/sql/0025_stock_catalog.sql": (
        "7665f5df6c828f681f6d7db7dda8b4cbf1a19d4f645fa4003fec94c1a5fa32fa"
    ),
    "alembic/versions/0024_stock_halt_snapshot.py": (
        "792f45724769b22df272a119633bc19a789e8b4153dedc96397b4ba0efcad7fd"
    ),
    "alembic/sql/0024_stock_halt_snapshot.sql": (
        "fa19099943dd885cfa3548cd45f25fb5d5150307524ea41d0cae0aa4b2c6e986"
    ),
    "alembic/versions/0021_portfolio_closure_schema.py": (
        "737446365d1304dc3721ced552102cde4d386b07031823eaf33967961732c81c"
    ),
    "alembic/versions/0022_portfolio_closure_provenance.py": (
        "0c3467650b7b308e7e4bb3f03f1e8f58d1f1ee8fe09c3361353a9036fea48cdb"
    ),
    "alembic/versions/0023_portfolio_closure_authority.py": (
        "d62c175438c9b1022771df1cac6e4b9333f77a2b8c3375aa365840daa78ce8b5"
    ),
    "alembic/sql/0023_portfolio_closure.sql": (
        "59577ba16c9e9ea9740c2cb0d171b7006931bb6b1b9e5d0408c9a6f673f7c920"
    ),
    "alembic/versions/0018_portfolio_management_expansion.py": (
        "8e63586555c85b6f6495d0da1bad4b8a455e5de71249a0f08e2c758e4b22b0b0"
    ),
    "alembic/versions/0019_portfolio_management_backfill.py": (
        "75f40d134e05ebdf06b15bff677d866474aa34ac64bdf66ec412bc8e0615f66d"
    ),
    "alembic/versions/0020_portfolio_management_authority.py": (
        "b6e304a0d3b610468caa93a893f300138269efcc5c80f014fa7c77a58eafcc9c"
    ),
    "alembic/sql/0019_portfolio_metadata.sql": (
        "a26d4230843f75af9202fce71a771818d0bd7f041777a8a01a0d53a8df7a7c65"
    ),
    "alembic/sql/0020_portfolio_management.sql": (
        "9fe1fd5706df5ac319f7a70dcfe73a437f0886ba7e4a827758fa8c414106963d"
    ),
    "alembic/versions/0015_portfolio_expansion.py": (
        "9811795856a2fc96485cff103c0750622501535a480af39d916a3aaa1755ebb8"
    ),
    "alembic/versions/0016_portfolio_association.py": (
        "81fa8bcbc59a1a1875d79b53ba6ca7ade32449a16128837f3823e59087d1a327"
    ),
    "alembic/versions/0017_portfolio_ownership.py": (
        "92cff0699a40b0b8f5f4d66bc56a39a2ef88e3184860d86d6957607a3413f32b"
    ),
    "alembic/sql/0017_stock_portfolio.sql": (
        "3dc967baccb425ba26f73bb2fab66b7947aff73f5454ea2f85e03a6e0aa5e08b"
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
      AND NOT EXISTS(SELECT FROM pg_roles WHERE rolname IN
       ('birja_app','birja_scheduler','birja_action_operator')
       AND (rolinherit OR rolsuper OR rolcreatedb OR rolcreaterole
        OR rolreplication OR rolbypassrls))
      AND NOT EXISTS(SELECT FROM pg_roles WHERE rolname='birja_action_operator'
       AND rolcanlogin)
      AND NOT EXISTS(SELECT FROM pg_auth_members WHERE roleid IN
       (SELECT oid FROM pg_roles WHERE rolname IN
        ('birja_app','birja_scheduler','birja_action_operator'))
       OR member IN (SELECT oid FROM pg_roles WHERE rolname IN
        ('birja_app','birja_scheduler','birja_action_operator')))
      """)
        )
    ).scalar_one():
        raise ValueError("Unsafe migration schema or runtime roles")
    revision = None
    if (await conn.execute(text("SELECT to_regclass('public.alembic_version')"))).scalar():
        versions = (
            (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalars().all()
        )
        if len(versions) != 1 or versions[0] not in {f"{n:04}" for n in range(7, 29)}:
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
    relations = [tuple(row) for row in rows]
    allowed_tables, allowed_functions = migration_objects(revision)
    for name, kind, owner in relations:
        allowed = allowed_tables if kind == "r" else {t + "_id_seq" for t in allowed_tables}
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
        signature.replace("public.", "").replace(" ", "") not in allowed_functions
        or owner != "birja_migrator"
        for signature, owner in rows
    ):
        raise ValueError("Unexpected migration routine ownership")
    require_complete_migration_inventory(
        revision,
        relations,
        {row[0].replace("public.", "").replace(" ", "") for row in rows},
    )
    # The frozen historical fingerprints omit some catalogue families. Current
    # entry must reject those objects even with disabled RLS, before any child
    # can apply DDL. Do not remove or normalize an unrecognized object.
    try:
        await conn.execute(text(MIGRATION_SUPPLEMENTAL_INVENTORY_SQL))
    except DBAPIError:
        raise ValueError("Unrecognized migration supplemental catalogue") from None
    if revision == "0014":
        try:
            await conn.execute(text(PREFLIGHT_0014_MIGRATION_SQL))
        except DBAPIError:
            raise ValueError("Unrecognized legacy migration authority") from None
    elif revision in PRE_CLOSURE_MIGRATION_SQL:
        # Authenticate prior authority before Alembic can mutate even one
        # object. Initial and runtime-granted20, and exact21/22 resumes, are
        # finite catalogue/ACL/default pairs, never a grant-repair fallback.
        try:
            await conn.execute(text(PRE_CLOSURE_MIGRATION_SQL[revision]))
        except DBAPIError:
            raise ValueError("Unrecognized pre-closure migration authority") from None
    elif revision in PORTFOLIO_PREFLIGHT_SQL:
        try:
            await conn.execute(text(PORTFOLIO_PREFLIGHT_SQL[revision]))
        except DBAPIError:
            raise ValueError("Unrecognized current or retained migration authority") from None
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
                    CURRENT_PORTFOLIO_REVISION,
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
                if await require_migrator(conn) != CURRENT_PORTFOLIO_REVISION:
                    raise ValueError("Final portfolio revision absent")
                await conn.execute(text(PORTFOLIO_PREFLIGHT_SQL[CURRENT_PORTFOLIO_REVISION]))
                await conn.rollback()
            finally:
                await conn.execute(text("SELECT pg_advisory_unlock(1026016017)"))
                await conn.commit()
            print(
                f"portfolio_migration_to_final=true source_revision={revision} "
                f"final={CURRENT_PORTFOLIO_REVISION}"
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
