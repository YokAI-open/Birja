"""Independent final SQL ownership/lifecycle/role expectations, not live-derived sets."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.portfolio_fixtures import OWNED_TABLES, portfolio_world, seed_owned_crypto_trade

__all__ = ["portfolio_world"]

EXPECTED_ROLES = {"birja_app", "birja_scheduler", "birja_migrator"}
EXPECTED_PRIVATE_AUTHORITIES = {
    "check_stock_fill_integrity()",
    "assert_stock_execution_current(bigint,bigint,jsonb)",
    "stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)",
    "apply_stock_dividend(bigint,bigint,text,text)",
    "record_stock_dividend_hold(bigint,text)",
    "check_stock_split_digest_version()",
}


async def test_final_sql_owned_tables_have_pairwise_root_authority(engine, migrated):
    async with engine.connect() as conn:
        roles = (
            await conn.execute(
                text("""SELECT rolname,rolinherit,rolsuper,rolcreatedb,
            rolcreaterole,rolreplication,rolbypassrls FROM pg_roles
            WHERE rolname IN ('birja_app','birja_scheduler','birja_migrator')""")
            )
        ).all()
        assert {row[0] for row in roles} == EXPECTED_ROLES
        assert all(not any(row[1:]) for row in roles)
        functions = (
            (
                await conn.execute(
                    text("""SELECT p.oid::regprocedure::text
            FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
            WHERE n.nspname='public'""")
                )
            )
            .scalars()
            .all()
        )
        functions = {signature.replace(" ", "") for signature in functions}
        assert functions >= EXPECTED_PRIVATE_AUTHORITIES
        expected_names = {signature.split("(", 1)[0] for signature in EXPECTED_PRIVATE_AUTHORITIES}
        assert {
            signature for signature in functions if signature.split("(", 1)[0] in expected_names
        } == EXPECTED_PRIVATE_AUTHORITIES
        for table in OWNED_TABLES:
            keys = (
                (
                    await conn.execute(
                        text("""SELECT pg_get_constraintdef(oid)
                FROM pg_constraint WHERE conrelid=to_regclass(:t) AND contype='f'"""),
                        {"t": table},
                    )
                )
                .scalars()
                .all()
            )
            assert any(
                "FOREIGN KEY (portfolio_id, user_id)" in key
                and "REFERENCES accounts(id, user_id)" in key
                for key in keys
            ), table
        assert (
            await conn.execute(text("SELECT to_regclass('public.portfolio_stock_closures')"))
        ).scalar_one() is not None
        assert (
            await conn.execute(
                text("SELECT to_regprocedure('public.associate_legacy_portfolio_only()')")
            )
        ).scalar_one() is None


async def test_final_sql_closed_root_refuses_new_fill_even_for_migration_owner(portfolio_world):
    conn, world = portfolio_world
    with pytest.raises(DBAPIError):
        async with conn.begin_nested():
            await seed_owned_crypto_trade(conn, world, world.closed)
    assert not (
        await conn.execute(text("SELECT id FROM trades WHERE portfolio_id=:p"), {"p": world.closed})
    ).all()


@pytest.mark.parametrize("role", ["birja_app", "birja_scheduler"])
async def test_final_sql_runtime_roles_cannot_rewrite_original_financial_root(
    portfolio_world, role, engine
):
    conn, world = portfolio_world
    tid, _ = await seed_owned_crypto_trade(conn, world, world.first)
    # The exact restricted roles/ACL installation is owned by12-07/16; no
    # synthetic permissions are created here to simulate a passing boundary.
    # The isolated administrator may SET ROLE; the authenticated NOINHERIT
    # migrator intentionally cannot. An independent connection proves the
    # actual permission denial even though seeded rows are uncommitted.
    async with engine.connect() as runtime, runtime.begin():
        await runtime.execute(text(f"SET LOCAL ROLE {role}"))  # noqa: S608 - fixed matrix
        with pytest.raises(DBAPIError) as denied:
            async with runtime.begin_nested():
                await runtime.execute(
                    text("UPDATE trades SET portfolio_id=:p WHERE id=:t"),
                    {"p": world.sibling, "t": tid},
                )
        assert denied.value.orig.sqlstate == "42501"
    assert (
        await conn.execute(text("SELECT portfolio_id FROM trades WHERE id=:t"), {"t": tid})
    ).scalar_one() == world.first


async def test_final_sql_runtime_cannot_bypass_closed_portfolio_cash_authority(
    portfolio_world, engine
):
    conn, world = portfolio_world
    before = (
        await conn.execute(
            text("SELECT cash,closed_at FROM accounts WHERE id=:p"), {"p": world.closed}
        )
    ).one()
    # Direct cash bypass is denied. Domain worker suites separately exercise
    # the retained earned-but-unpaid entitlement seeded by seed_legacy_books.
    async with engine.connect() as runtime, runtime.begin():
        await runtime.execute(text("SET LOCAL ROLE birja_scheduler"))
        with pytest.raises(DBAPIError) as denied:
            async with runtime.begin_nested():
                await runtime.execute(
                    text("UPDATE accounts SET cash=cash+1 WHERE id=:p"), {"p": world.closed}
                )
        assert denied.value.orig.sqlstate == "42501"
    assert (
        await conn.execute(
            text("SELECT cash,closed_at FROM accounts WHERE id=:p"), {"p": world.closed}
        )
    ).one() == before
