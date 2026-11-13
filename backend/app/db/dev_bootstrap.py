"""Explicit local Compose prerequisite; never production role provisioning."""

import asyncio
import os

import asyncpg  # type: ignore[import-untyped]  # Driver has no published typing marker.
from sqlalchemy.engine import make_url


async def bootstrap(env: str, database_url: str) -> None:
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
    finally:
        await conn.close()


def main() -> None:
    asyncio.run(bootstrap(os.environ.get("ENV", ""), os.environ.get("DATABASE_URL", "")))


if __name__ == "__main__":
    main()
