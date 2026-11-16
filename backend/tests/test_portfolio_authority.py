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


@pytest.mark.parametrize(
    "model_name", ["StockDividendEntitlement", "StockDividendPayment", "StockDividendDecision"]
)
def test_model_metadata_dividend_roots_and_causes_are_paired(model_name):
    from sqlalchemy import BigInteger, UniqueConstraint

    from app.models.corporate_action import StockDividendEntitlement
    from app.models.dividend import StockDividendDecision, StockDividendPayment

    table = {
        model.__name__: model
        for model in (StockDividendEntitlement, StockDividendPayment, StockDividendDecision)
    }[model_name].__table__
    root = table.c.portfolio_id
    assert isinstance(root.type, BigInteger) and not root.nullable
    assert root.default is None and root.server_default is None
    paired = next(
        fk
        for fk in table.foreign_key_constraints
        if tuple(fk.column_keys) == ("portfolio_id", "user_id")
    )
    assert tuple(e.target_fullname for e in paired.elements) == ("accounts.id", "accounts.user_id")
    assert all(fk.ondelete is None and fk.onupdate is None for fk in table.foreign_key_constraints)
    # Resolve every full causal tuple to a real unique key, not separate
    # individually valid references that can describe different portfolios.
    for fk in table.foreign_key_constraints:
        columns = tuple(element.column.name for element in fk.elements)
        target = fk.referred_table
        candidates = {tuple(target.primary_key.columns.keys())} | {
            tuple(c.columns.keys()) for c in target.constraints if isinstance(c, UniqueConstraint)
        }
        assert columns in candidates, (fk.name, columns, candidates)


def test_model_metadata_dividend_entitlement_supersession_and_payment_once_per_root():
    from sqlalchemy import UniqueConstraint

    from app.models.corporate_action import StockDividendEntitlement
    from app.models.dividend import StockDividendPayment

    entitlement = StockDividendEntitlement.__table__
    supersedes = next(
        fk
        for fk in entitlement.foreign_key_constraints
        if len(fk.column_keys) > 1 and "supersedes_id" in fk.column_keys
    )
    assert tuple(supersedes.column_keys) == ("supersedes_id", "event_id", "portfolio_id", "user_id")
    assert tuple(e.target_fullname for e in supersedes.elements) == (
        "stock_dividend_entitlements.id",
        "stock_dividend_entitlements.event_id",
        "stock_dividend_entitlements.portfolio_id",
        "stock_dividend_entitlements.user_id",
    )
    unique = {
        tuple(c.columns.keys()) for c in entitlement.constraints if isinstance(c, UniqueConstraint)
    }
    assert ("event_id", "portfolio_id", "revision_id", "fingerprint") in unique
    payment = StockDividendPayment.__table__
    unique = {
        tuple(c.columns.keys()) for c in payment.constraints if isinstance(c, UniqueConstraint)
    }
    assert ("event_id", "portfolio_id") in unique
    assert ("event_id", "user_id") not in unique
    identity = next(
        fk for fk in payment.foreign_key_constraints if "entitlement_id" in fk.column_keys
    )
    assert tuple(identity.column_keys) == (
        "entitlement_id",
        "event_id",
        "portfolio_id",
        "user_id",
        "revision_id",
        "entitlement_fingerprint",
    )


def test_model_metadata_dividend_decisions_cannot_cross_root_causal_chains():
    from app.models.dividend import StockDividendDecision

    table = StockDividendDecision.__table__
    expected = {
        "payment_id": ("payment_id", "event_id", "portfolio_id", "user_id", "coin_id"),
        "entitlement_id": (
            "entitlement_id",
            "event_id",
            "portfolio_id",
            "user_id",
            "revision_id",
            "entitlement_fingerprint",
        ),
        "previous_decision_id": (
            "previous_decision_id",
            "payment_id",
            "portfolio_id",
            "user_id",
            "event_id",
        ),
        "previous_application_id": (
            "previous_application_id",
            "payment_id",
            "portfolio_id",
            "user_id",
            "event_id",
        ),
    }
    for field, columns in expected.items():
        fk = next(fk for fk in table.foreign_key_constraints if field in fk.column_keys)
        assert tuple(fk.column_keys) == columns
        # Referred ownership fields must line up with the exact source tuple.
        assert [e.column.name for e in fk.elements][columns.index("portfolio_id")] == "portfolio_id"
        assert [e.column.name for e in fk.elements][columns.index("user_id")] == "user_id"
    assert ("portfolio_id", "recorded_at", "id") in {tuple(i.columns.keys()) for i in table.indexes}


async def test_final_sql_dividend_supersession_cannot_cross_sibling_portfolios(portfolio_world):
    from datetime import UTC, datetime
    from decimal import Decimal

    from sqlalchemy import insert
    from sqlalchemy.exc import IntegrityError

    from app.models.corporate_action import StockDividendEntitlement
    from tests.test_stock_action_migrations import event

    conn, world = portfolio_world
    coin = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
    eid, _, rid = await event(conn, coin)
    values = {
        "event_id": eid,
        "user_id": world.owner,
        "portfolio_id": world.first,
        "revision_id": rid,
        "cutoff": datetime(2026, 11, 10, tzinfo=UTC),
        "cutoff_rule": "regular_session_open",
        "version": 1,
        "units_basis": "post_split",
        "unit_epoch": 0,
        "last_movement_sequence": 0,
        "eligible_quantity": Decimal("2"),
        "state": "eligible",
        "fingerprint": "a" * 64,
    }
    entitlement = StockDividendEntitlement.__table__
    first = (
        await conn.execute(insert(entitlement).values(**values).returning(entitlement.c.id))
    ).scalar_one()
    with pytest.raises(IntegrityError) as err:
        async with conn.begin_nested():
            await conn.execute(
                insert(entitlement).values(
                    **{
                        **values,
                        "portfolio_id": world.sibling,
                        "supersedes_id": first,
                        "version": 2,
                        "fingerprint": "b" * 64,
                    }
                )
            )
    assert err.value.orig.sqlstate == "23503"


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
