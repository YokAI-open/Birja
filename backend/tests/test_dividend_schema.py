"""Real PostgreSQL dividend identities, saved terms and append-only lineage."""

import importlib.util
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import insert, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from app.models.dividend import StockDividendDecision
from tests.test_stock_action_migrations import event, ledger
from tests.test_stock_migrations import migrate

__all__ = ["ledger"]


def migration():
    path = Path(__file__).resolve().parents[1] / "alembic/versions/0014_dividend_accounting.py"
    spec = importlib.util.spec_from_file_location("dividend_migration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_anchor_schema_exists(engine: AsyncEngine, migrated: None) -> None:
    async with engine.connect() as conn:
        tables = set(
            (
                await conn.execute(
                    text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                )
            ).scalars()
        )
        assert tables >= {"stock_dividend_payments", "stock_dividend_decisions"}, (
            "Dividend originals and decisions need durable constrained relations"
        )


@pytest_asyncio.fixture
async def dividend_case(ledger) -> AsyncIterator[tuple[AsyncConnection, dict[str, object]]]:
    conn, cid, uid = ledger
    eid, _, rid = await event(conn, cid)
    entitlement = (
        await conn.execute(
            text("""INSERT INTO stock_dividend_entitlements
        (event_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,
         last_movement_sequence,eligible_quantity,state,fingerprint)
        VALUES (:e,:u,:r,now(),'exclusive',1,'shares',0,0,2,'eligible',:f) RETURNING id"""),
            {"e": eid, "u": uid, "r": rid, "f": "b" * 64},
        )
    ).scalar_one()
    yield (
        conn,
        {
            "event_id": eid,
            "coin_id": cid,
            "user_id": uid,
            "revision_id": rid,
            "revision_fingerprint": "a" * 64,
            "entitlement_id": entitlement,
            "entitlement_fingerprint": "b" * 64,
        },
    )


async def payment(conn: AsyncConnection, terms: dict[str, object], **changes: object) -> int:
    values = {**terms, "original_amount": Decimal("1.00"), "rate": Decimal("0.5"), **changes}
    return (
        await conn.execute(
            text("""INSERT INTO stock_dividend_payments
      (event_id,coin_id,user_id,revision_id,revision_fingerprint,entitlement_id,
       entitlement_fingerprint,symbol,company_name,cutoff,cutoff_rule,units_basis,
       unit_epoch,eligible_quantity,rate,ex_date,record_date,payable_date,
       original_amount,recorded_at,cash_after)
      VALUES (:event_id,:coin_id,:user_id,:revision_id,:revision_fingerprint,:entitlement_id,
       :entitlement_fingerprint,'AAPL','Saved Apple',now(),'exclusive','shares',0,2,:rate,
       DATE '2026-11-01',DATE '2026-11-02',DATE '2026-11-10',:original_amount,now(),10001)
      RETURNING id"""),
            values,
        )
    ).scalar_one()


async def test_zero_target_anchor(dividend_case) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms, original_amount=Decimal("0.00"), rate=Decimal(0))
    assert (
        await conn.execute(
            text("SELECT original_amount FROM stock_dividend_payments WHERE id=:p"), {"p": pid}
        )
    ).scalar_one() == Decimal(0)
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await payment(conn, terms)
    assert error.value.orig.sqlstate == "23505"


@pytest.mark.parametrize(
    "field",
    [
        "user_id",
        "event_id",
        "revision_id",
        "entitlement_id",
        "revision_fingerprint",
        "entitlement_fingerprint",
    ],
)
async def test_anchor_cross_links_rejected(dividend_case, field: str) -> None:
    conn, terms = dividend_case
    changes = {field: "c" * 64 if field.endswith("fingerprint") else 9223372036854775807}
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await payment(conn, terms, **changes)
    assert error.value.orig.sqlstate == "23503"


async def test_individually_valid_foreign_keys_cannot_cross_link(dividend_case) -> None:
    from uuid import uuid4

    conn, terms = dividend_case
    other_uid = (
        await conn.execute(
            text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
            {"e": f"other-dividend-{uuid4()}@example.test"},
        )
    ).scalar_one()
    other_event, _, other_revision = await event(conn, terms["coin_id"])
    for changes in (
        {"user_id": other_uid},
        {"event_id": other_event},
        {"revision_id": other_revision},
    ):
        with pytest.raises(DBAPIError) as error:
            async with conn.begin_nested():
                await payment(conn, terms, **changes)
        assert error.value.orig.sqlstate == "23503"


@pytest.mark.parametrize("amount", ["-0.01", "NaN", "Infinity", "1000000000000", "0.001"])
async def test_anchor_amount_finite_nonnegative_cents(dividend_case, amount: str) -> None:
    conn, terms = dividend_case
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await payment(conn, terms, original_amount=Decimal(amount))
    assert error.value.orig.sqlstate in {"23514", "22003"}


@pytest.mark.parametrize(
    "operation",
    ["UPDATE stock_dividend_payments SET symbol='CHANGED'", "DELETE FROM stock_dividend_payments"],
)
async def test_anchor_immutable_even_owner(dividend_case, operation: str) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms)
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await conn.execute(text(f"{operation} WHERE id=:p"), {"p": pid})
    assert error.value.orig.sqlstate == "23514"


async def test_populated_downgrade_refuses_before_ddl(dividend_case) -> None:
    conn, terms = dividend_case
    await payment(conn, terms)
    module = migration()

    def downgrade(sync_conn):
        with Operations.context(MigrationContext.configure(sync_conn)):
            module.downgrade()

    with pytest.raises(DBAPIError, match="populated dividend accounting"):
        async with conn.begin_nested():
            await conn.run_sync(downgrade)


async def decision(
    conn: AsyncConnection, terms: dict[str, object], pid: int, **changes: object
) -> int:
    values = {
        **terms,
        "payment_id": pid,
        "previous_decision_id": None,
        "previous_application_id": None,
        "desired_total": Decimal("0.50"),
        "cumulative_applied_before": Decimal("1.00"),
        "proposed_delta": Decimal("-0.50"),
        "applied_delta": Decimal(0),
        "outcome": "held_unaffordable",
        "reason": "insufficient_cash",
        "status_identity": "epoch:1:insufficient_cash",
        "recorded_at": datetime.now(UTC),
        "cash_after": Decimal("0.20"),
        "symbol": "AAPL",
        "company_name": "Saved Apple",
        "cutoff": datetime.now(UTC),
        "cutoff_rule": "exclusive",
        "units_basis": "shares",
        "unit_epoch": 0,
        "eligible_quantity": Decimal(2),
        "rate": Decimal("0.25"),
        "ex_date": date(2026, 11, 1),
        "record_date": date(2026, 11, 2),
        "payable_date": date(2026, 11, 10),
        **changes,
    }
    return (
        await conn.execute(
            insert(StockDividendDecision).values(**values).returning(StockDividendDecision.id)
        )
    ).scalar_one()


def uncertain_terms() -> dict[str, object]:
    return dict.fromkeys(
        (
            "entitlement_id",
            "entitlement_fingerprint",
            "desired_total",
            "proposed_delta",
            "eligible_quantity",
            "rate",
            "cutoff",
            "cutoff_rule",
            "units_basis",
            "unit_epoch",
            "ex_date",
            "record_date",
            "payable_date",
        )
    ) | {
        "outcome": "held_uncertain",
        "reason": "terms_unverified",
        "status_identity": "epoch:2:terms_unverified",
    }


async def test_nullable_uncertain_existing_anchor_deduplicates(dividend_case) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms)
    held = await decision(conn, terms, pid, **uncertain_terms())
    assert held > 0
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await decision(
                conn,
                terms,
                pid,
                **uncertain_terms(),
                recorded_at=datetime.now(UTC),
                cash_after=Decimal(123),
            )
    assert error.value.orig.sqlstate == "23505"
    assert (
        await conn.execute(
            text(
                "SELECT desired_total IS NULL AND proposed_delta IS NULL AND applied_delta=0 "
                "FROM stock_dividend_decisions WHERE id=:d"
            ),
            {"d": held},
        )
    ).scalar_one()


async def test_uncertainty_without_anchor_does_not_publish(dividend_case) -> None:
    conn, terms = dividend_case
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await decision(conn, terms, 9223372036854775807, **uncertain_terms())
    assert error.value.orig.sqlstate == "23503"
    assert (
        await conn.execute(
            text("SELECT count(*) FROM stock_dividend_payments WHERE event_id=:event_id"), terms
        )
    ).scalar_one() == 0


async def test_held_then_applied_successor_and_target_dedup(dividend_case) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms)
    held = await decision(conn, terms, pid)
    applied = await decision(
        conn,
        terms,
        pid,
        previous_decision_id=held,
        outcome="applied",
        reason="target_applied",
        applied_delta=Decimal("-0.50"),
        cash_after=Decimal("0.50"),
    )
    assert applied > held
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await decision(
                conn,
                terms,
                pid,
                previous_decision_id=applied,
                previous_application_id=applied,
                outcome="applied",
                reason="target_applied",
                applied_delta=Decimal("-0.50"),
                cash_after=Decimal("0.50"),
            )
    assert error.value.orig.sqlstate == "23505"
    assert (
        await conn.execute(
            text("SELECT original_amount FROM stock_dividend_payments WHERE id=:p"), {"p": pid}
        )
    ).scalar_one() == Decimal(1)


@pytest.mark.parametrize(
    "operation",
    ["UPDATE stock_dividend_decisions SET cash_after=99", "DELETE FROM stock_dividend_decisions"],
)
async def test_decision_immutable(dividend_case, operation: str) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms)
    did = await decision(conn, terms, pid)
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await conn.execute(text(f"{operation} WHERE id=:d"), {"d": did})
    assert error.value.orig.sqlstate == "23514"


async def test_runtime_direct_writes_denied_and_app_read_only(dividend_case) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms)
    for role in ("birja_app", "birja_scheduler"):
        # Roles exist only in this rollback-owned test transaction.
        await conn.execute(text(f"CREATE ROLE {role} NOLOGIN"))
        await conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {role}"))
    # Execute the exact migration grant block after provisioning local NOLOGIN
    # roles; full fresh/upgraded restricted bootstrap parity belongs to plan02.
    await conn.execute(text(migration().GRANTS))
    for role in ("birja_app", "birja_scheduler"):
        async with conn.begin_nested():
            await conn.execute(text(f"SET LOCAL ROLE {role}"))
            if role == "birja_app":
                assert (
                    await conn.execute(
                        text("SELECT id FROM stock_dividend_payments WHERE id=:p"), {"p": pid}
                    )
                ).scalar_one() == pid
            for table in ("stock_dividend_payments", "stock_dividend_decisions"):
                for operation in (
                    f"INSERT INTO {table}(event_id) VALUES (1)",  # noqa: S608 - fixed table list
                    f"UPDATE {table} SET event_id=1",  # noqa: S608 - fixed table list
                    f"DELETE FROM {table}",  # noqa: S608 - fixed table list
                ):
                    with pytest.raises(DBAPIError) as error:
                        async with conn.begin_nested():
                            await conn.execute(text(operation))
                    assert error.value.orig.sqlstate == "42501"
            await conn.execute(text("RESET ROLE"))


async def test_original_owner_and_event_lineage_cannot_cross(dividend_case) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms)
    held = await decision(conn, terms, pid)
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await decision(
                conn,
                terms,
                pid,
                outcome="applied",
                reason="target_applied",
                applied_delta=Decimal("-0.50"),
                cash_after=Decimal("0.50"),
                previous_decision_id=held,
                previous_application_id=held,
            )
    assert error.value.orig.sqlstate == "23514"
    for field in ("payment_id", "user_id", "event_id", "revision_id", "entitlement_id"):
        with pytest.raises(DBAPIError) as error:
            async with conn.begin_nested():
                await decision(
                    conn,
                    terms,
                    pid,
                    status_identity=f"different:{field}",
                    **{field: 9223372036854775807},
                )
        assert error.value.orig.sqlstate == "23503"


@pytest.mark.parametrize("field", ["desired_total", "proposed_delta", "eligible_quantity", "rate"])
async def test_uncertain_never_invents_verified_terms(dividend_case, field: str) -> None:
    conn, terms = dividend_case
    pid = await payment(conn, terms)
    values = {**uncertain_terms(), field: Decimal(0)}
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await decision(conn, terms, pid, **values)
    assert error.value.orig.sqlstate == "23514"


async def test_model_metadata_matches_reviewed_migration(engine, migrated) -> None:
    from alembic.autogenerate import compare_metadata

    from app.db.base import Base

    def compare(conn):
        return compare_metadata(
            MigrationContext.configure(conn, opts={"compare_type": True}), Base.metadata
        )

    async with engine.connect() as conn:
        assert await conn.run_sync(compare) == []


async def test_populated_0013_entitlement_survives_upgrade_and_empty_downgrade(engine, migrated):
    from uuid import uuid4

    await migrate("0013", down=True)
    try:
        async with engine.begin() as conn:
            uid = (
                await conn.execute(
                    text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                    {"e": f"dividend-schema-{uuid4()}@example.test"},
                )
            ).scalar_one()
            cid = (
                await conn.execute(
                    text("SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 1")
                )
            ).scalar_one()
            eid, sid, rid = await event(conn, cid)
            enid = (
                await conn.execute(
                    text("""INSERT INTO stock_dividend_entitlements
              (event_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,
               last_movement_sequence,eligible_quantity,state,fingerprint)
              VALUES (:e,:u,:r,now(),'exclusive',1,'shares',0,0,2,'eligible',:f) RETURNING id"""),
                    {"e": eid, "u": uid, "r": rid, "f": "b" * 64},
                )
            ).scalar_one()
            before = (
                await conn.execute(
                    text("SELECT to_jsonb(e) FROM stock_dividend_entitlements e WHERE id=:e"),
                    {"e": enid},
                )
            ).scalar_one()
        for target, down in (("0014", False), ("0013", True), ("0014", False)):
            await migrate(target, down=down)
            async with engine.connect() as conn:
                after = (
                    await conn.execute(
                        text("SELECT to_jsonb(e) FROM stock_dividend_entitlements e WHERE id=:e"),
                        {"e": enid},
                    )
                ).scalar_one()
                assert before == after
        async with engine.begin() as conn:
            await conn.execute(
                text("DELETE FROM stock_dividend_entitlements WHERE id=:e"), {"e": enid}
            )
            await conn.execute(
                text("UPDATE stock_action_events SET current_revision_id=NULL WHERE id=:e"),
                {"e": eid},
            )
            await conn.execute(text("DELETE FROM stock_action_revisions WHERE id=:r"), {"r": rid})
            await conn.execute(text("DELETE FROM stock_action_sources WHERE id=:s"), {"s": sid})
            await conn.execute(text("DELETE FROM stock_action_events WHERE id=:e"), {"e": eid})
            await conn.execute(text("DELETE FROM users WHERE id=:u"), {"u": uid})
    finally:
        await migrate("head")
