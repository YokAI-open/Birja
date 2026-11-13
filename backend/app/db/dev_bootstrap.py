"""Explicit local Compose prerequisite; never production role provisioning."""

import argparse
import asyncio
import os

import asyncpg  # type: ignore[import-untyped]  # Driver has no published typing marker.
from sqlalchemy.engine import make_url


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


async def bootstrap(env: str, database_url: str, *, after_migrations: bool = False) -> None:
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
                await _authorize_dividends(conn)
    finally:
        await conn.close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--after-migrations", action="store_true")
    args = parser.parse_args(argv)
    asyncio.run(
        bootstrap(
            os.environ.get("ENV", ""),
            os.environ.get("DATABASE_URL", ""),
            after_migrations=args.after_migrations,
        )
    )


if __name__ == "__main__":
    main()
