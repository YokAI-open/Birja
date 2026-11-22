"""Explicit synthetic ownership seeds. Never imported by application code."""

import hashlib
import json
from contextlib import asynccontextmanager
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.corporate_action import (
    StockActionEvent,
    StockActionRevision,
    StockActionSource,
    StockActionState,
    StockOwnershipMovement,
    StockSplitApplication,
)
from app.models.stock import StockInstrument
from app.models.stock_execution import StockFillFacts
from app.models.trade import Holding, Trade
from app.models.user import Account


async def synthetic_portfolio_id(db, user_id, portfolio_id=None):
    """Resolve only the fixture's sole root, or validate its explicit sibling."""
    roots = (await db.execute(select(Account).where(Account.user_id == user_id))).scalars().all()
    if portfolio_id is None:
        assert len(roots) == 1, "Multi-root fixtures must name their intended portfolio"
        root = roots[0]
    else:
        root = next((root for root in roots if root.id == portfolio_id), None)
        assert root is not None, "Explicit fixture root must belong to the intended owner"
    assert root.closed_at is None, "Synthetic financial seeds require an active root"
    return root.id


async def synthetic_owned_portfolio(db, user_id):
    """Capture the fixture's verified sole root before invoking a service."""
    from app.services.portfolios import OwnedActivePortfolio

    return OwnedActivePortfolio(await synthetic_portfolio_id(db, user_id), user_id)


async def install_current_runtime_roles(conn):
    """Install the exact final production contract on this guarded test DB."""
    from app.db.portfolio_bootstrap import (
        GRANTS_0023_SQL as GRANTS_SQL,
    )
    from app.db.portfolio_bootstrap import (
        PREFLIGHT_0023_SQL as PREFLIGHT_SQL,
    )

    assert (
        await conn.execute(
            text(
                "SELECT current_database(),session_user FROM pg_roles "
                "WHERE rolname=session_user AND rolsuper"
            )
        )
    ).one() == ("birja_test", "birja_test")
    await conn.execute(text(PREFLIGHT_SQL))
    # The current authority includes a dollar-quoted DO block. Use asyncpg's
    # actual multi-statement protocol, as production bootstrap does; splitting
    # on semicolons would truncate the block before any grants can be applied.
    raw = await conn.get_raw_connection()
    await raw.driver_connection.execute(GRANTS_SQL)


@pytest_asyncio.fixture
async def current_runtime_roles(engine, migrated):
    async with engine.begin() as conn:
        await install_current_runtime_roles(conn)
    yield


@asynccontextmanager
async def synthetic_corruption(db, table, *, trigger="stock_record_immutable"):
    """Privileged isolated corruption SETUP only; restore before tested reads.

    Failed DDL/DML aborts its transaction, so rollback restores trigger state.
    Never call around production behavior or a restricted-role assertion.
    """
    allowed_targets = {
        ("trades", "stock_record_immutable"),
        ("trades", "stock_fill_integrity"),
        ("stock_fill_facts", "stock_record_immutable"),
        ("stock_fill_facts", "stock_fill_integrity"),
        ("stock_ownership_movements", "stock_record_immutable"),
        ("stock_dividend_entitlements", "portfolio_association_only"),
        ("stock_dividend_payments", "stock_dividend_immutable"),
        ("stock_dividend_decisions", "stock_dividend_immutable"),
        ("stock_split_applications", "portfolio_record_immutable"),
    }
    if (table, trigger) not in allowed_targets:
        raise RuntimeError("Fixed corruption target required")
    allowed = (
        await db.execute(
            text("""SELECT current_database()='birja_test'
      AND current_user='birja_test' AND rolsuper FROM pg_roles WHERE rolname=current_user""")
        )
    ).scalar_one()
    if not allowed:
        raise RuntimeError("Privileged isolated corruption setup only")
    trigger_state = text(
        "SELECT tgenabled::text FROM pg_trigger WHERE tgrelid=to_regclass(:table) "
        "AND tgname=:trigger AND NOT tgisinternal"
    )
    target = {"table": "public." + table, "trigger": trigger}
    assert (await db.execute(trigger_state, target)).scalar_one() == "O"
    await db.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    await db.execute(text(f"ALTER TABLE public.{table} DISABLE TRIGGER {trigger}"))
    try:
        yield
        await db.flush()
    finally:
        await db.execute(text(f"ALTER TABLE public.{table} ENABLE TRIGGER {trigger}"))
        assert (await db.execute(trigger_state, target)).scalar_one() == "O"


@pytest_asyncio.fixture
async def ownership(engine, migrated, new_user):
    user_id = await new_user()
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory.begin() as db:
        coin_id = (
            (await db.execute(select(StockInstrument.coin_id).order_by(StockInstrument.coin_id)))
            .scalars()
            .first()
        )
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        db.add(
            StockActionState(
                coin_id=coin_id,
                admission_generation=1,
                health="current",
                checked_at=now - timedelta(seconds=1),
                valid_until=now + timedelta(hours=1),
                journal_start_at=now - timedelta(days=5),
                complete_from=now - timedelta(days=5),
                coverage_start=now - timedelta(days=5),
                covered_until=now,
            )
        )
    try:
        yield factory, coin_id, user_id
    finally:
        async with factory.begin() as db:
            # Explicit test-only DDL maintenance, never a production escape or
            # behavior-under-test. Transaction rollback restores trigger state
            # if cleanup fails; never disable ALL/constraint/FK triggers.
            allowed = (
                await db.execute(
                    text("""SELECT current_database()='birja_test'
              AND current_user='birja_test' AND rolsuper FROM pg_roles
              WHERE rolname=current_user""")
                )
            ).scalar_one()
            if not allowed:
                raise RuntimeError("Test-only immutable cleanup identity required")
            for table in ("stock_fill_facts", "stock_ownership_movements", "trades"):
                await db.execute(
                    text(f"ALTER TABLE public.{table} DISABLE TRIGGER stock_record_immutable")
                )
            await db.execute(delete(StockFillFacts).where(StockFillFacts.coin_id == coin_id))
            await db.execute(
                delete(StockOwnershipMovement).where(StockOwnershipMovement.coin_id == coin_id)
            )
            async with synthetic_corruption(
                db, "stock_split_applications", trigger="portfolio_record_immutable"
            ):
                await db.execute(
                    delete(StockSplitApplication).where(StockSplitApplication.coin_id == coin_id)
                )
            events = select(StockActionEvent.id).where(StockActionEvent.coin_id == coin_id)
            await db.execute(
                update(StockActionEvent)
                .where(StockActionEvent.coin_id == coin_id)
                .values(current_revision_id=None)
            )
            await db.execute(
                delete(StockActionRevision).where(StockActionRevision.event_id.in_(events))
            )
            await db.execute(
                delete(StockActionSource).where(StockActionSource.event_id.in_(events))
            )
            await db.execute(delete(StockActionEvent).where(StockActionEvent.coin_id == coin_id))
            await db.execute(delete(Holding).where(Holding.coin_id == coin_id))
            await db.execute(delete(Trade).where(Trade.coin_id == coin_id))
            await db.execute(delete(StockActionState).where(StockActionState.coin_id == coin_id))
            for table in ("stock_fill_facts", "stock_ownership_movements", "trades"):
                await db.execute(
                    text(f"ALTER TABLE public.{table} ENABLE TRIGGER stock_record_immutable")
                )


async def synthetic_fill(
    db, coin_id, user_id, *, quantity=Decimal(2), side="buy", created_at=None, portfolio_id=None
):
    """Fill-like caller only; no production cash service or stock execution."""
    portfolio_id = await synthetic_portfolio_id(db, user_id, portfolio_id)
    now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
    trade = Trade(
        portfolio_id=portfolio_id,
        coin_id=coin_id,
        user_id=user_id,
        side=side,
        input_kind="quantity",
        input_value=quantity,
        quantity=quantity,
        mid_price=Decimal(10),
        price_as_of=now,
        exec_price=Decimal(10),
        fee=Decimal(0),
        cash_delta=quantity * Decimal(-10 if side == "buy" else 10),
        cash_after=Decimal(10000),
        idempotency_key=uuid4(),
        **({"created_at": created_at} if created_at is not None else {}),
    )
    db.add(trade)
    await db.flush()
    held = (
        await db.execute(
            select(Holding.quantity).where(
                Holding.coin_id == coin_id, Holding.portfolio_id == portfolio_id
            )
        )
    ).scalar_one_or_none() or Decimal(0)
    db.add(
        StockFillFacts(
            portfolio_id=portfolio_id,
            trade_id=trade.id,
            coin_id=coin_id,
            user_id=user_id,
            provider_asset_id="synthetic-asset",
            symbol="SYNTH",
            company_name="Synthetic fixture",
            listing_exchange="NASDAQ",
            source="alpaca",
            feed="iex",
            bid=Decimal(10),
            ask=Decimal(10),
            exact_mid=Decimal(10),
            # Invalid oversell fixtures are rolled back by refusal tests before
            # any movement; keep receipt locally valid to reach that behavior.
            held_after=max(Decimal(0), held + (quantity if side == "buy" else -quantity)),
            event_at=now,
            collected_at=now,
            observed_at=now,
            session_date=now.date(),
            opens_at=now - timedelta(hours=1),
            closes_at=now + timedelta(hours=1),
            authority={},
        )
    )
    await db.flush()
    return trade


async def synthetic_opening(
    db,
    coin_id,
    user_id,
    at,
    *,
    quantity=Decimal(2),
    basis=Decimal(20),
    sequence=1,
    portfolio_id=None,
):
    """Test-only prehistory; deliberately unavailable from production services."""
    await db.execute(
        text(
            "SELECT pg_advisory_xact_lock(hashtextextended("
            "'birja.stock.instrument:' || CAST(:c AS text),0))"
        ),
        {"c": str(coin_id)},
    )
    portfolio_id = await synthetic_portfolio_id(db, user_id, portfolio_id)
    row = StockOwnershipMovement(
        portfolio_id=portfolio_id,
        coin_id=coin_id,
        user_id=user_id,
        sequence=sequence,
        economic_at=at,
        recorded_at=at,
        quantity=quantity,
        before_quantity=Decimal(0),
        after_quantity=quantity,
        before_basis=Decimal(0),
        after_basis=basis,
        unit_epoch=0,
        cause_kind="opening",
        causal_key="synthetic-opening:" + str(portfolio_id),
    )
    db.add(row)
    db.add(
        Holding(
            portfolio_id=portfolio_id,
            coin_id=coin_id,
            user_id=user_id,
            quantity=quantity,
            cost_basis=basis,
        )
    )
    await db.flush()
    return row


async def synthetic_split(
    db,
    coin_id,
    cutoff,
    *,
    boundary=1,
    prior_epoch=0,
    before_digest=None,
    after_digest=None,
    applied=True,
):
    """Explicit matched event/revision/application; never false-causal shortcuts."""
    # Pending announcements are nonfinancial and may arrive while a financial
    # writer holds its gate. Only an applied fixture appends guarded economics.
    if applied:
        await db.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended("
                "'birja.stock.instrument:' || CAST(:c AS text),0))"
            ),
            {"c": str(coin_id)},
        )
    event = StockActionEvent(coin_id=coin_id, economic_key=str(uuid4()), first_observed_at=cutoff)
    db.add(event)
    await db.flush()
    source = StockActionSource(
        event_id=event.id, provider="synthetic", product="actions", provider_event_id=str(uuid4())
    )
    db.add(source)
    await db.flush()
    revision = StockActionRevision(
        event_id=event.id,
        source_id=source.id,
        ordinal=1,
        fingerprint="a" * 64,
        mutation_kind="snapshot",
        observed_at=cutoff,
        admission_generation=1,
        normalized_terms={"synthetic": True},
        classification="supported_forward_split",
        reason="verified synthetic fixture",
        verified_cutoff=cutoff,
        units="pre_split",
    )
    db.add(revision)
    await db.flush()
    event.current_revision_id = revision.id
    if not applied:
        return revision
    # Independent fixture encoding of the NEW root-aware digest; legacy stored
    # NULL-marker tuples are never rewritten or interpreted by this helper.
    rows = (
        (
            await db.execute(
                select(StockOwnershipMovement)
                .where(
                    StockOwnershipMovement.coin_id == coin_id,
                    StockOwnershipMovement.sequence <= boundary,
                )
                .order_by(StockOwnershipMovement.sequence)
            )
        )
        .scalars()
        .all()
    )
    latest = {row.portfolio_id: row for row in rows}
    before, after, sequence = [], [], boundary
    for pid, row in sorted(latest.items()):
        before.append(
            (
                pid,
                row.user_id,
                coin_id,
                format(row.after_quantity, ".8f"),
                format(row.after_basis, ".8f"),
                row.sequence,
                prior_epoch,
            )
        )
        if row.after_quantity > 0:
            sequence += 1
        after.append(
            (
                pid,
                row.user_id,
                coin_id,
                format(row.after_quantity * 2, ".8f"),
                format(row.after_basis, ".8f"),
                sequence if row.after_quantity > 0 else row.sequence,
                prior_epoch + 1,
            )
        )

    def digest(value):
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
    application = StockSplitApplication(
        coin_id=coin_id,
        economic_event_id=event.id,
        revision_id=revision.id,
        new_rate="2",
        old_rate="1",
        cutoff=cutoff,
        prior_unit_epoch=prior_epoch,
        new_unit_epoch=prior_epoch + 1,
        sequence_boundary=boundary,
        before_digest=before_digest if before_digest is not None else digest(before),
        after_digest=after_digest if after_digest is not None else digest(after),
        owner_digest_version=2,
        processed_at=now,
    )
    db.add(application)
    state = await db.get(StockActionState, coin_id)
    state.unit_epoch = prior_epoch + 1
    await db.flush()
    return application
