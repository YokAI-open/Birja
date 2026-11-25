"""Explicit local Compose prerequisite; never production role provisioning."""

import argparse
import asyncio
import os
import secrets
import sys
from pathlib import Path

import asyncpg  # type: ignore[import-untyped]  # Driver has no published typing marker.
from sqlalchemy.engine import make_url

from app.db.portfolio_bootstrap import (
    ACL_0023_SHA256,
    ACL_0025_SHA256,
    ACL_0025_SQL,
    ACL_0026_SHA256,
    ACL_0026_SQL,
    ACL_SQL,
    CATALOGUE_FINANCE_TABLES,
    CATALOGUE_TABLES,
    CURRENT_PORTFOLIO_REVISION,
    DEFAULT_ACL_0023_SHA256,
    DEFAULT_ACL_0023_SQL,
    GRANTS_0023_SQL,
    GRANTS_0025_SQL,
    GRANTS_0026_SQL,
    PORTFOLIO_PREFLIGHT_SQL,
)

BACKEND_DIR = Path(__file__).resolve().parents[2]

# Existing local application objects only. Never REASSIGN OWNED or transfer an
# unknown extension/table/function, even in the disposable development database.
TABLES = frozenset(
    [
        "alembic_version",
        "users",
        "accounts",
        "auth_sessions",
        "refresh_tokens",
        "coins",
        "prices",
        "holdings",
        "trades",
        "stock_instruments",
        "stock_quotes",
        "stock_sessions",
        "stock_data_admissions",
        "stock_action_events",
        "stock_action_sources",
        "stock_action_revisions",
        "stock_action_observations",
        "stock_action_state",
        "stock_ownership_movements",
        "stock_split_applications",
        "stock_dividend_entitlements",
        "stock_action_resolutions",
        "stock_fill_facts",
        "stock_status_evidence",
        "stock_dividend_payments",
        "stock_dividend_decisions",
        "portfolio_stock_closures",
        "portfolio_creations",
        "portfolio_initializations",
    ]
)
FUNCTIONS = frozenset(
    [
        "reject_stock_action_mutation",
        "reject_stock_record_mutation",
        "reject_stock_dividend_mutation",
        "check_stock_fill_integrity",
        "assert_stock_execution_current",
        "apply_stock_action_resolution",
        "stock_dividend_authority",
        "apply_stock_dividend",
        "record_stock_dividend_hold",
        "associate_legacy_portfolio_only",
        "check_stock_split_digest_version",
        "check_portfolio_financial_write",
        "lock_stock_portfolio_roots",
        "portfolio_display_name",
        "portfolio_name_key",
        "portfolio_description",
        "check_portfolio_management_metadata",
        "associate_portfolio_metadata_only",
        "create_portfolio",
        "initialize_portfolio",
        "update_portfolio_metadata",
    ]
)
FUNCTION_SIGNATURES = frozenset(
    {
        "reject_stock_action_mutation()",
        "reject_stock_record_mutation()",
        "reject_stock_dividend_mutation()",
        "check_stock_fill_integrity()",
        "assert_stock_execution_current(bigint,bigint,jsonb)",
        "apply_stock_action_resolution(bigint,bigint,bigint,bigint,bigint,text,text,text,jsonb,text)",
        "stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)",
        "apply_stock_dividend(bigint,bigint,text,text)",
        "record_stock_dividend_hold(bigint,text)",
        "associate_legacy_portfolio_only()",
        "check_stock_split_digest_version()",
        "check_portfolio_financial_write()",
        "lock_stock_portfolio_roots(bigint)",
        "portfolio_display_name(text)",
        "portfolio_name_key(text)",
        "portfolio_description(text)",
        "check_portfolio_management_metadata()",
        "associate_portfolio_metadata_only()",
        "create_portfolio(bigint,uuid,text,text)",
        "initialize_portfolio(bigint)",
        "update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean)",
    }
)


def migration_objects(revision: str | None) -> tuple[frozenset[str], frozenset[str]]:
    """Finite migration-only inventories, distinct from runtime admission."""
    if revision is not None and revision not in {f"{n:04}" for n in range(7, 28)}:
        raise ValueError("Unsupported migration revision inventory")
    if revision not in {"0021", "0022", *PORTFOLIO_PREFLIGHT_SQL}:
        return TABLES, FUNCTION_SIGNATURES
    tables = TABLES | {"portfolio_lifecycle_closures", "portfolio_closure_intents"}
    signatures = FUNCTION_SIGNATURES - {
        "reject_stock_action_mutation()",
        "reject_stock_record_mutation()",
        "associate_legacy_portfolio_only()",
        "associate_portfolio_metadata_only()",
    }
    signatures |= {"check_portfolio_lifecycle_integrity()"}
    if revision != "0021":
        signatures |= {"check_portfolio_terminal_root()"}
    if revision in PORTFOLIO_PREFLIGHT_SQL:
        signatures |= {
            "close_portfolio(bigint,bigint,uuid,text,text)",
            "check_stock_terminal_clock()",
        }
    if revision in {"0025", "0026", "0027"}:
        tables |= CATALOGUE_TABLES
    if revision in {"0026", "0027"}:
        tables |= CATALOGUE_FINANCE_TABLES
        signatures |= {
            "stock_catalog_scope_current(bigint,text,stock_catalog_instruments,"
            "stock_catalog_listings,timestampwithtimezone,jsonb)",
            "check_catalog_stock_fill()",
            "assert_catalog_stock_execution_current(bigint,bigint,jsonb)",
            "stock_catalog_action_context(bigint,bigint,bigint,"
            "timestampwithtimezone,timestampwithtimezone,boolean)",
            "check_stock_catalog_split_movements()",
        }
    return frozenset(tables), frozenset(signatures)


def require_complete_migration_inventory(
    revision: str | None,
    relations: list[tuple[str, str, str]],
    signatures: set[str],
) -> None:
    if revision not in {"0021", "0022", *PORTFOLIO_PREFLIGHT_SQL}:
        return
    tables, functions = migration_objects(revision)
    nonidentity = {
        "alembic_version",
        "prices",
        "stock_instruments",
        "stock_quotes",
        "stock_action_state",
        "stock_fill_facts",
        "stock_status_evidence",
    } | CATALOGUE_FINANCE_TABLES
    if (
        {name for name, kind, _ in relations if kind == "r"} != tables
        or {name for name, kind, _ in relations if kind == "S"}
        != {f"{t}_id_seq" for t in tables - nonidentity}
        or signatures != functions
    ):
        raise ValueError("Incomplete successor migration inventory")


async def _authorize_portfolios(conn: asyncpg.Connection, revision: str) -> None:
    grants_sql, acl_sql, acl_sha256 = {
        "0025": (GRANTS_0025_SQL, ACL_0025_SQL, ACL_0025_SHA256),
        "0026": (GRANTS_0026_SQL, ACL_0026_SQL, ACL_0026_SHA256),
        "0027": (GRANTS_0026_SQL, ACL_0026_SQL, ACL_0026_SHA256),
    }.get(revision, (GRANTS_0023_SQL, ACL_SQL, ACL_0023_SHA256))
    await conn.execute(PORTFOLIO_PREFLIGHT_SQL[revision])
    await conn.execute(grants_sql)
    if await conn.fetchval(acl_sql) != acl_sha256:
        raise ValueError("Unexpected final management grants")
    if await conn.fetchval(DEFAULT_ACL_0023_SQL) != DEFAULT_ACL_0023_SHA256:
        raise ValueError("Unexpected final closure default privileges")


async def _migrate_dev(conn: asyncpg.Connection, database_url: str) -> None:
    """Authenticate the finite migration child; keep the parent admin unchanged."""
    revision = None
    if await conn.fetchval("SELECT to_regclass('public.alembic_version') IS NOT NULL"):
        rows = await conn.fetch("SELECT version_num FROM public.alembic_version")
        if len(rows) != 1 or rows[0][0] not in {f"{n:04}" for n in range(7, 28)}:
            raise ValueError("Unsupported dev migration revision; refusing")
        revision = rows[0][0]
    await conn.execute("SELECT pg_advisory_lock(1026016001)")
    try:
        async with conn.transaction():
            for role in ("birja_migrator", "birja_app", "birja_scheduler", "birja_action_operator"):
                row = await conn.fetchrow(
                    "SELECT oid,rolinherit,rolsuper,rolcreatedb,rolcreaterole,"
                    "rolreplication,rolbypassrls FROM pg_roles WHERE rolname=$1",
                    role,
                )
                if row is None:
                    # The role list is a closed source-owned set, not user input.
                    await conn.execute(
                        f"CREATE ROLE {role} NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB "
                        "NOCREATEROLE NOREPLICATION NOBYPASSRLS"
                    )
                elif any(v for k, v in row.items() if k != "oid") or await conn.fetchval(
                    "SELECT EXISTS(SELECT FROM pg_auth_members WHERE roleid=$1 OR member=$1)",
                    row["oid"],
                ):
                    raise ValueError("Unsafe dev role; refusing repair")
            relations = await conn.fetch(
                "SELECT c.relname,c.relkind::text,pg_get_userbyid(c.relowner) FROM pg_class c "
                "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' "
                "AND c.relkind IN ('r','S')"
            )
            allowed_tables, allowed_functions = migration_objects(revision)
            for name, kind, owner in relations:
                allowed = allowed_tables if kind == "r" else {t + "_id_seq" for t in allowed_tables}
                if name not in allowed or owner not in {"birja", "birja_migrator"}:
                    raise ValueError("Unexpected dev relation; refusing transfer")
            functions = await conn.fetch(
                "SELECT p.oid::regprocedure::text,p.proname,pg_get_userbyid(p.proowner) "
                "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='public'"
            )
            for signature, _name, owner in functions:
                if signature.replace("public.", "").replace(
                    " ", ""
                ) not in allowed_functions or owner not in {"birja", "birja_migrator"}:
                    raise ValueError("Unexpected dev routine; refusing transfer")
            require_complete_migration_inventory(
                revision,
                [tuple(row) for row in relations],
                {row[0].replace("public.", "").replace(" ", "") for row in functions},
            )
            for name, kind, _ in relations:
                if kind == "r":
                    await conn.execute(f'ALTER TABLE public."{name}" OWNER TO birja_migrator')
            for signature, _, _ in functions:
                await conn.execute(f"ALTER FUNCTION {signature} OWNER TO birja_migrator")
            await conn.execute(
                "GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator;"
                "REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler;"
                "GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler"
            )
            password = secrets.token_hex(32)
            statement = await conn.fetchval(
                "SELECT format('ALTER ROLE birja_migrator LOGIN PASSWORD %L',$1::text)", password
            )
            await conn.execute(statement)
        try:
            child = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "app.db.portfolio_migrate",
                cwd=BACKEND_DIR,
                env={
                    **os.environ,
                    "DATABASE_URL": make_url(database_url)
                    .set(username="birja_migrator", password=password)
                    .render_as_string(hide_password=False),
                },
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                await asyncio.wait_for(child.communicate(), timeout=180)
            except TimeoutError:
                child.kill()
                await child.wait()
                raise ValueError("Dev final migration timed out; resume explicitly") from None
            if child.returncode:
                raise ValueError("Dev final migration failed; diagnostics withheld")
        finally:
            await conn.execute("ALTER ROLE birja_migrator NOLOGIN PASSWORD NULL")
        async with conn.transaction():
            await _authorize_portfolios(conn, CURRENT_PORTFOLIO_REVISION)
        print(
            f"dev_final_migration=true source_revision={revision} "
            f"final={CURRENT_PORTFOLIO_REVISION}"
        )
    finally:
        await conn.execute("SELECT pg_advisory_unlock(1026016001)")


async def _authorize_dividends(conn: asyncpg.Connection) -> None:
    """Grant only the frozen authority's object access on an ordinary dev schema."""
    if not await conn.fetchval(
        "SELECT d.datdba='birja'::regrole AND n.nspowner IN "
        "('birja'::regrole,'pg_database_owner'::regrole) "
        "AND (SELECT count(*)=1 AND bool_and(version_num='0014') FROM public.alembic_version) "
        "FROM pg_catalog.pg_database d CROSS JOIN pg_catalog.pg_namespace n "
        "WHERE d.datname=current_database() AND n.nspname='public'"
    ):
        raise ValueError("Unexpected dev database/schema/revision; refusing grants")
    if not await conn.fetchval(
        "WITH expected(name,kind) AS (VALUES "
        "('stock_action_events','r'),('stock_action_revisions','r'),"
        "('stock_action_observations','r'),('stock_action_resolutions','r'),"
        "('stock_action_state','r'),('stock_instruments','r'),('coins','r'),"
        "('stock_data_admissions','r'),('stock_sessions','r'),"
        "('stock_ownership_movements','r'),('stock_split_applications','r'),"
        "('stock_dividend_entitlements','r'),('stock_dividend_payments','r'),"
        "('stock_dividend_decisions','r'),('accounts','r'),"
        "('stock_dividend_payments_id_seq','S'),('stock_dividend_decisions_id_seq','S')) "
        "SELECT count(c.oid)=17 AND bool_and(c.relowner='birja'::regrole "
        "AND c.relkind::text=e.kind) FROM expected e LEFT JOIN pg_catalog.pg_class c "
        "ON c.relname=e.name AND c.relnamespace='public'::regnamespace"
    ) or not await conn.fetchval(
        "SELECT count(*)=2 FROM pg_catalog.pg_depend dep "
        "JOIN pg_catalog.pg_class seq ON seq.oid=dep.objid "
        "JOIN pg_catalog.pg_class tab ON tab.oid=dep.refobjid "
        "JOIN pg_catalog.pg_attribute a ON a.attrelid=tab.oid AND a.attnum=dep.refobjsubid "
        "WHERE dep.classid='pg_class'::regclass AND dep.refclassid='pg_class'::regclass "
        "AND dep.deptype='i' AND a.attname='id' AND a.attidentity='a' "
        "AND tab.relnamespace='public'::regnamespace AND seq.relnamespace=tab.relnamespace "
        "AND tab.relname IN ('stock_dividend_payments','stock_dividend_decisions') "
        "AND seq.relname=tab.relname||'_id_seq'"
    ):
        raise ValueError("Unexpected dev relation ownership/identity; refusing grants")
    if not await conn.fetchval(
        "SELECT count(*)=4 AND bool_and(p.proowner='birja_migrator'::regrole "
        "AND p.prosecdef=(p.proname IN ('apply_stock_dividend','record_stock_dividend_hold'))) "
        "FROM pg_catalog.pg_proc p WHERE p.oid IN ("
        "to_regprocedure('public.apply_stock_dividend(bigint,bigint,text,text)'),"
        "to_regprocedure('public.record_stock_dividend_hold(bigint,text)'),"
        "to_regprocedure('public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)'),"
        "to_regprocedure('public.reject_stock_dividend_mutation()'))"
    ):
        raise ValueError("Unexpected dev dividend function owner; refusing grants")
    await conn.execute("GRANT USAGE ON SCHEMA public TO birja_migrator")
    await conn.execute(
        "GRANT SELECT ON public.stock_action_events,public.stock_action_revisions,"
        "public.stock_action_observations,public.stock_action_resolutions,"
        "public.stock_action_state,public.stock_instruments,public.coins,"
        "public.stock_data_admissions,public.stock_sessions,public.stock_ownership_movements,"
        "public.stock_split_applications,public.stock_dividend_entitlements,"
        "public.stock_dividend_payments,public.stock_dividend_decisions,public.accounts "
        "TO birja_migrator"
    )
    await conn.execute(
        "GRANT INSERT ON public.stock_dividend_payments,public.stock_dividend_decisions "
        "TO birja_migrator"
    )
    await conn.execute(
        "GRANT USAGE ON SEQUENCE public.stock_dividend_payments_id_seq,"
        "public.stock_dividend_decisions_id_seq TO birja_migrator"
    )
    await conn.execute("GRANT UPDATE(cash) ON public.accounts TO birja_migrator")


async def bootstrap(
    env: str, database_url: str, *, after_migrations: bool = False, migrate: bool = False
) -> None:
    url = make_url(database_url)
    if (
        env != "dev"
        or url.drivername != "postgresql+asyncpg"
        or url.host != "postgres"
        or url.port != 5432
        or url.username != "birja"
        or url.database != "birja"
        or not url.password
        or url.query
    ):
        raise ValueError("Dev bootstrap requires the local Compose dev database")
    conn = await asyncpg.connect(
        url.set(drivername="postgresql").render_as_string(hide_password=False),
        timeout=10,
        command_timeout=15,
        server_settings={"statement_timeout": "15000", "lock_timeout": "10000"},
    )
    try:
        async with conn.transaction():
            if not await conn.fetchval(
                "SELECT current_database()='birja' AND current_user='birja' AND rolsuper "
                "FROM pg_catalog.pg_roles WHERE rolname=current_user"
            ):
                raise ValueError("Dev bootstrap requires the local database administrator")
            await conn.execute("SELECT pg_catalog.pg_advisory_xact_lock(1026016001)")
            role = await conn.fetchrow(
                "SELECT oid,rolcanlogin,rolinherit,rolsuper,rolcreatedb,rolcreaterole,"
                "rolreplication,rolbypassrls FROM pg_catalog.pg_roles "
                "WHERE rolname='birja_migrator'"
            )
            if role is None:
                if after_migrations:
                    raise ValueError("Missing dev migration owner; refusing grants")
                await conn.execute(
                    "CREATE ROLE birja_migrator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB "
                    "NOCREATEROLE NOREPLICATION NOBYPASSRLS"
                )
            elif any(value for key, value in role.items() if key != "oid") or await conn.fetchval(
                "SELECT EXISTS(SELECT FROM pg_catalog.pg_auth_members "
                "WHERE roleid=$1 OR member=$1)",
                role["oid"],
            ):
                raise ValueError("Unsafe existing dev migration owner; refusing repair")
            if after_migrations:
                revision = await conn.fetchval("SELECT version_num FROM public.alembic_version")
                if revision in {"0015", "0016", "0018", "0019", "0021", "0022"}:
                    raise ValueError("migration_only; refusing normal dev bootstrap")
                if revision in PORTFOLIO_PREFLIGHT_SQL:
                    await _authorize_portfolios(conn, revision)
                elif revision in {"0017", "0020"}:
                    raise ValueError("Retained schema requires explicit forward migration")
                else:
                    await _authorize_dividends(conn)
        if migrate:
            await _migrate_dev(conn, database_url)
    finally:
        await conn.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--after-migrations", action="store_true")
    parser.add_argument("--migrate", action="store_true")
    args = parser.parse_args(argv)
    asyncio.run(
        bootstrap(
            os.environ.get("ENV", ""),
            os.environ.get("DATABASE_URL", ""),
            after_migrations=args.after_migrations,
            migrate=args.migrate,
        )
    )


if __name__ == "__main__":
    main()
