"""Real transactional refusal proofs for the successor's defensive boundaries."""

from dataclasses import replace
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.services import portfolio_closure as service
from app.services import stock_ownership as ownership
from tests.portfolio_closure_fixtures import frozen_financial_snapshot
from tests.test_portfolio_closure_authority import authority, stock_authority
from tests.test_portfolio_closure_migrations import root
from tests.test_portfolio_closure_stocks import proof_grants

__all__ = ["authority", "stock_authority"]


@pytest.mark.parametrize("outcome", ["closed", "confirmation_changed"])
@pytest.mark.parametrize("replayed", [False, True])
def test_returned_closure_fields_accept_exact_original_and_finite_values(outcome, replayed):
    assert service._validate_closure_result(11, 11, outcome, replayed) is None


@pytest.mark.parametrize(
    "portfolio_id,outcome,replayed",
    [
        (12, "closed", False),
        (11, "other", False),
        (11, "closed", 0),
        (11, "closed", "false"),
        (11, "closed", None),
    ],
)
def test_returned_closure_fields_refuse_invalid_arguments(portfolio_id, outcome, replayed):
    with pytest.raises(ownership.OwnershipHeld, match="invalid_closure"):
        service._validate_closure_result(11, portfolio_id, outcome, replayed)


async def new_case(authority):
    app, migrator, admin = authority
    await proof_grants(admin)
    async with migrator.begin() as conn:
        user, portfolio = await root(conn)
    return app, admin, service.ClosureIntent(user, portfolio, uuid4(), "Strategy")


async def snapshot(engine, portfolio):
    async with engine.connect() as conn:
        return await frozen_financial_snapshot(conn, portfolio)


@pytest.mark.parametrize(
    "field,value",
    [
        ("user_id", 0),
        ("portfolio_id", True),
        ("portfolio_id", 9223372036854775808),
        ("intent_key", "invalid"),
        ("confirmation_name", ""),
        ("confirmation_name", "x" * 61),
        ("policy_version", "other"),
    ],
)
async def test_invalid_original_refuses_before_sql_and_preserves_book(authority, field, value):
    app, admin, original = await new_case(authority)
    before = await snapshot(admin, original.portfolio_id)
    async with AsyncSession(app) as db:
        with pytest.raises(ownership.OwnershipHeld, match="invalid_closure"):
            await service.close_portfolio(db, replace(original, **{field: value}))
        assert not db.in_transaction()
    assert await snapshot(admin, original.portfolio_id) == before


@pytest.mark.parametrize("pending", ["new", "dirty", "deleted", "nested"])
async def test_unrelated_business_session_is_refused_without_discarding_work(authority, pending):
    from app.models.user import Account, User

    app, admin, original = await new_case(authority)
    before = await snapshot(admin, original.portfolio_id)
    async with AsyncSession(app) as db:
        if pending == "new":
            db.add(User(email=f"unflushed-{uuid4()}@example.com"))
        elif pending == "nested":
            await db.begin_nested()
        else:
            account = await db.get(Account, original.portfolio_id)
            if pending == "dirty":
                account.cash -= 1
            else:
                await db.delete(account)
        with pytest.raises(HTTPException) as refusal:
            await service.close_owned_portfolio(db, original)
        assert refusal.value.status_code == 503
        assert refusal.value.detail == {"code": "service_unavailable"}
        assert refusal.value.headers == {"Retry-After": "5"}
        assert db.new or db.dirty or db.deleted or db.in_nested_transaction()
        await db.rollback()
    assert await snapshot(admin, original.portfolio_id) == before


@pytest.mark.parametrize("sqlstate,expected", [("40001", 3), ("40P01", 1)])
async def test_actual_server_fault_has_bounded_whole_transaction_retry(
    authority, monkeypatch, sqlstate, expected
):
    app, admin, original = await new_case(authority)
    before = await snapshot(admin, original.portfolio_id)
    attempts, rollbacks = [], []
    async with AsyncSession(app) as db:
        execute, rollback = db.execute, db.rollback

        async def fault(statement, *args, **kwargs):
            if str(statement).startswith("SELECT * FROM public.close_portfolio"):
                attempts.append(db.get_transaction())
                # An actual PostgreSQL exception aborts the real transaction.
                # No result, finance row or exception object is fabricated.
                command = {
                    "40001": "DO $$ BEGIN RAISE EXCEPTION 'retry' USING ERRCODE='40001'; END $$",
                    "40P01": "DO $$ BEGIN RAISE EXCEPTION 'refusal' USING ERRCODE='40P01'; END $$",
                }[sqlstate]
                return await execute(text(command))
            return await execute(statement, *args, **kwargs)

        async def observed_rollback():
            await rollback()
            rollbacks.append(not db.in_transaction())

        monkeypatch.setattr(db, "execute", fault)
        monkeypatch.setattr(db, "rollback", observed_rollback)
        with pytest.raises(DBAPIError) as failure:
            await service.close_portfolio(db, original)
        assert failure.value.orig.sqlstate == sqlstate
        assert len(attempts) == expected
        assert rollbacks == [True] * expected
        assert not db.in_transaction()
        assert "portfolio_closure_proof" not in db.info
    assert await snapshot(admin, original.portfolio_id) == before


async def test_terminal_clock_requires_actual_already_held_instrument_gate(authority):
    app, _, admin = authority
    async with admin.connect() as conn:
        coin = await conn.scalar(text("SELECT min(coin_id) FROM stock_instruments"))
    async with AsyncSession(app) as db:
        with pytest.raises(ownership.OwnershipHeld, match="invalid_closure"):
            await ownership.assert_stock_terminal_clock(db, coin, datetime.now(UTC))
        await db.rollback()


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
async def test_copied_closed_proof_cannot_replace_real_gate_or_isolation(
    stock_authority, monkeypatch, isolation
):
    app, _, admin, books = stock_authority
    await proof_grants(admin)
    user, portfolio = books["roots"][0]
    original = service.ClosureIntent(user, portfolio, uuid4(), "Strategy")
    captured = []
    actual = service.assert_closure_ownership_consistent

    async def capture(db):
        captured.append(db.info["portfolio_closure_proof"])
        await actual(db)

    monkeypatch.setattr(service, "assert_closure_ownership_consistent", capture)
    async with AsyncSession(app) as db:
        await service.close_portfolio(db, original)
    before = await snapshot(admin, portfolio)
    async with AsyncSession(app) as db:
        await db.connection(execution_options={"isolation_level": isolation})
        # Rebinding a copied private context is a hostile in-process test input,
        # never an API permission or a fabricated database row/result.
        db.info["portfolio_closure_proof"] = replace(captured[0], transaction=db.get_transaction())
        reason = "read_committed_required" if isolation == "REPEATABLE READ" else "invalid_closure"
        with pytest.raises(ownership.OwnershipHeld, match=reason):
            await ownership.assert_closure_ownership_consistent(db)
        await db.rollback()
    assert await snapshot(admin, portfolio) == before


@pytest.mark.parametrize("index", [3, 4])
async def test_real_retained_boundary_acknowledgement_preserves_exact_evidence(
    stock_authority, index
):
    app, _, admin, books = stock_authority
    await proof_grants(admin)
    user, portfolio = books["roots"][index]
    before = await snapshot(admin, portfolio)
    async with AsyncSession(app) as db:
        result = await service.close_portfolio(
            db, service.ClosureIntent(user, portfolio, uuid4(), "Different fresh review")
        )
        assert result == service.ClosureResult(portfolio, "closed", True)
        assert not db.in_transaction()
    assert await snapshot(admin, portfolio) == before


async def test_universal_proof_refuses_actual_active_book_without_lifecycle(authority):
    app, admin, original = await new_case(authority)
    before = await snapshot(admin, original.portfolio_id)
    async with AsyncSession(app) as db:
        await db.execute(text("SELECT 1"))
        db.info["portfolio_closure_proof"] = ownership._ClosureProofContext(
            db.get_transaction(),
            original.user_id,
            original.portfolio_id,
            original.intent_key,
            original.confirmation_name,
            original.policy_version,
            (),
        )
        with pytest.raises(ownership.OwnershipHeld, match="invalid_closure"):
            await ownership.assert_closure_ownership_consistent(db)
        await db.rollback()
    assert await snapshot(admin, original.portfolio_id) == before


@pytest.mark.parametrize("corruption", ["original_outcome", "missing_boundary"])
async def test_post_sql_corruption_rolls_back_the_entire_actual_closure(
    stock_authority, monkeypatch, corruption
):
    _, _, admin, books = stock_authority
    user, portfolio = books["roots"][0]
    original = service.ClosureIntent(user, portfolio, uuid4(), "Strategy")
    before = await snapshot(admin, portfolio)
    from app.db.portfolio_bootstrap import CATALOGUE_0023_SQL

    async with admin.connect() as conn:
        catalogue = await conn.scalar(text(CATALOGUE_0023_SQL))
    actual = service.assert_closure_ownership_consistent
    reached = []

    async def corrupt_then_prove(db):
        # Deliberate privileged corruption inside the SAME real transaction,
        # after actual SQL closure and before the complete Python proof.
        # No result object or persisted financial payload is fabricated.
        # Validate queued deferred links before this privileged negative fixture
        # changes trigger state; PostgreSQL otherwise refuses the ALTER itself.
        await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        if corruption == "original_outcome":
            await db.execute(text("ALTER TABLE portfolio_closure_intents DISABLE TRIGGER USER"))
            await db.execute(
                text(
                    "UPDATE portfolio_closure_intents SET outcome='confirmation_changed' "
                    "WHERE intent_key=:k"
                ),
                {"k": original.intent_key},
            )
        else:
            await db.execute(text("ALTER TABLE portfolio_stock_closures DISABLE TRIGGER USER"))
            await db.execute(
                text("DELETE FROM portfolio_stock_closures WHERE portfolio_id=:p AND coin_id=:c"),
                {"p": portfolio, "c": books["stocks"][1]},
            )
        reached.append(True)
        await actual(db)

    monkeypatch.setattr(service, "assert_closure_ownership_consistent", corrupt_then_prove)
    async with AsyncSession(admin) as db:
        with pytest.raises(ownership.OwnershipHeld, match="invalid_closure"):
            await service.close_portfolio(db, original)
        assert reached == [True]
        assert not db.in_transaction()
        assert "portfolio_closure_proof" not in db.info
    assert await snapshot(admin, portfolio) == before
    async with admin.connect() as conn:
        assert await conn.scalar(text(CATALOGUE_0023_SQL)) == catalogue


@pytest.mark.parametrize("corruption", ["retained_metadata", "conflicting_request"])
async def test_retained_ack_proof_refuses_real_transactional_evidence_corruption(
    stock_authority, monkeypatch, corruption
):
    _, _, admin, books = stock_authority
    user, portfolio = books["roots"][3]
    original = service.ClosureIntent(user, portfolio, uuid4(), "Fresh incoming review")
    before = await snapshot(admin, portfolio)
    from app.db.portfolio_bootstrap import CATALOGUE_0023_SQL

    async with admin.connect() as conn:
        catalogue = await conn.scalar(text(CATALOGUE_0023_SQL))
    actual = service.assert_closure_ownership_consistent
    reached = []

    async def corrupt_then_prove(db):
        if corruption == "retained_metadata":
            await db.execute(text("ALTER TABLE portfolio_lifecycle_closures DISABLE TRIGGER USER"))
            # Transient negative-test catalogue corruption is rolled back with
            # the refusal; no migration/authority source asset is changed.
            await db.execute(
                text(
                    "ALTER TABLE portfolio_lifecycle_closures DROP CONSTRAINT "
                    "ck_portfolio_lifecycle_closures_provenance_exact"
                )
            )
            await db.execute(
                text(
                    "UPDATE portfolio_lifecycle_closures SET confirmation_name='Unexpected' "
                    "WHERE portfolio_id=:p"
                ),
                {"p": portfolio},
            )
        else:
            await db.execute(text("ALTER TABLE portfolio_closure_intents DISABLE TRIGGER USER"))
            await db.execute(
                text(
                    "INSERT INTO portfolio_closure_intents"
                    "(user_id,portfolio_id,intent_key,confirmation_name,"
                    "policy_version,outcome,recorded_at) "
                    "VALUES (:u,:p,:k,'Another review','freeze_at_closure_v1',"
                    "'confirmation_changed',clock_timestamp())"
                ),
                {"u": user, "p": portfolio, "k": original.intent_key},
            )
        reached.append(True)
        await actual(db)

    monkeypatch.setattr(service, "assert_closure_ownership_consistent", corrupt_then_prove)
    async with AsyncSession(admin) as db:
        with pytest.raises(ownership.OwnershipHeld, match="invalid_closure"):
            await service.close_portfolio(db, original)
        assert reached == [True]
        assert not db.in_transaction()
    assert await snapshot(admin, portfolio) == before
    async with admin.connect() as conn:
        assert await conn.scalar(text(CATALOGUE_0023_SQL)) == catalogue


async def test_final_default_acl_check_refuses_actual_post_preflight_change(
    engine, migrated, monkeypatch
):
    from app.db.portfolio_bootstrap import CATALOGUE_0023_SQL, DEFAULT_ACL_0023_SQL
    from app.db.schema_contract import SchemaAdmissionError, require_schema

    async with engine.connect() as conn:
        baseline = await conn.scalar(text(DEFAULT_ACL_0023_SQL))
        catalogue = await conn.scalar(text(CATALOGUE_0023_SQL))
        actual_execute = AsyncConnection.execute
        changed = []

        async def race(self, statement, *args, **kwargs):
            if self is conn and str(statement) == DEFAULT_ACL_0023_SQL and not changed:
                await actual_execute(
                    self,
                    text(
                        "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
                        "GRANT EXECUTE ON FUNCTIONS TO birja_scheduler"
                    ),
                )
                changed.append(True)
            return await actual_execute(self, statement, *args, **kwargs)

        monkeypatch.setattr(AsyncConnection, "execute", race)
        with pytest.raises(SchemaAdmissionError, match="incompatible_authority"):
            await require_schema(conn)
        assert changed == [True]
        await conn.rollback()
    async with engine.connect() as conn:
        assert await conn.scalar(text(DEFAULT_ACL_0023_SQL)) == baseline
        assert await conn.scalar(text(CATALOGUE_0023_SQL)) == catalogue
        assert await require_schema(conn) == "0023"


@pytest.mark.parametrize("revision", ["0006", "0024", "", "unknown"])
def test_dev_migration_inventory_refuses_unsupported_revision(revision):
    from app.db.dev_bootstrap import migration_objects

    with pytest.raises(ValueError, match="Unsupported migration revision inventory"):
        migration_objects(revision)


async def test_dev_final_default_acl_recheck_reads_actual_current_authority(engine, migrated):
    from app.db import dev_bootstrap
    from app.db.portfolio_bootstrap import ACL_SQL, CATALOGUE_0023_SQL, DEFAULT_ACL_0023_SQL

    queries = (ACL_SQL, DEFAULT_ACL_0023_SQL, CATALOGUE_0023_SQL)
    async with engine.connect() as conn:
        before = tuple([await conn.scalar(text(query)) for query in queries])
        raw = await conn.get_raw_connection()
        driver = raw.driver_connection
        changed = []

        class ObservedConnection:
            async def execute(self, command):
                return await driver.execute(command)

            async def fetchval(self, query):
                if query == DEFAULT_ACL_0023_SQL and not changed:
                    # Coordinate the actual final read on this owned transaction;
                    # all SQL results still come from the real driver unchanged.
                    await driver.execute(
                        "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator "
                        "GRANT EXECUTE ON FUNCTIONS TO birja_scheduler"
                    )
                    changed.append(True)
                return await driver.fetchval(query)

        with pytest.raises(ValueError, match="Unexpected final closure default privileges"):
            await dev_bootstrap._authorize_portfolios(ObservedConnection())
        assert changed == [True]
        await conn.rollback()
    async with engine.connect() as conn:
        assert tuple([await conn.scalar(text(query)) for query in queries]) == before
