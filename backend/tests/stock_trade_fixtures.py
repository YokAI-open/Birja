"""Explicit isolated status authority; never imported by application code.

Financial/action/quote/session cases extend this shared real-DB foundation.
No enabled boolean or live credential supplies product rights.
"""

from dataclasses import asdict, replace
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

import pytest_asyncio
from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.stock import StockDataAdmission, StockInstrument
from app.models.stock_execution import StockStatusEvidence
from tests.stock_action_fixtures import ownership as _ownership
from tests.test_stock_admission import action_admitted, admitted

ownership = _ownership


@pytest_asyncio.fixture
async def status_case(engine, migrated, clean_stock_discovery):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory.begin() as db:
        row = (
            await db.execute(
                select(
                    StockInstrument.coin_id,
                    StockInstrument.provider_asset_id,
                    StockInstrument.provider_verified_at,
                )
                .order_by(StockInstrument.coin_id)
                .limit(1)
            )
        ).one()
        cid, old_asset, old_verified = row
        now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
        await db.execute(delete(StockStatusEvidence).where(StockStatusEvidence.coin_id == cid))
        await db.execute(
            update(StockInstrument)
            .where(StockInstrument.coin_id == cid)
            .values(
                provider_asset_id="synthetic-status-asset",
                provider_verified_at=now,
            )
        )
        for product in ("reference", "status"):
            authority = replace(
                admitted(product),
                reviewed_at=now - timedelta(hours=1),
                valid_from=now - timedelta(hours=1),
                valid_until=now + timedelta(hours=1),
            )
            await db.execute(insert(StockDataAdmission).values(**asdict(authority)))
    try:
        yield factory, cid, now
    finally:
        async with factory.begin() as db:
            await db.execute(delete(StockStatusEvidence).where(StockStatusEvidence.coin_id == cid))
            await db.execute(
                update(StockInstrument)
                .where(StockInstrument.coin_id == cid)
                .values(
                    provider_asset_id=old_asset,
                    provider_verified_at=old_verified,
                )
            )


@pytest_asyncio.fixture
async def stock_trade_case(status_case, ownership, monkeypatch, request):
    """Real independent rows and a deliberately synthetic open session.

    Official schedules have separate tests. This fixture exercises finances at
    any wall-clock hour without faking the DB clock. The ownership fixture owns
    immutable fill/history cleanup.
    """
    from app.models.corporate_action import StockActionState
    from app.models.stock import StockQuote, StockSession
    from app.services import stock_sessions
    from app.services.stock_status import persist_status_batch
    from app.services.stock_status_rules import StatusBatch, StatusEvent
    from tests.test_stock_sessions import evidence

    factory, cid, now = status_case
    _, owner_cid, uid = ownership
    assert cid == owner_cid

    # Replace only the external calendar dataset. Real build_sessions/session_at
    # and their permission/generation/coverage validation still run, as does the
    # advancing DB clock/final SQL guard. Never cache this data outside fixture.
    class Stamp:
        def __init__(self, value):
            self.value = value

        def date(self):
            return self.value

        def to_pydatetime(self):
            return self.value

    class SyntheticCalendar:
        def __init__(self, start, end):
            first, last = date.fromisoformat(start), date.fromisoformat(end)
            self.sessions = [
                Stamp(first + timedelta(days=i)) for i in range((last - first).days + 1)
            ]

        def session_open(self, day):
            day = date.fromisoformat(day)
            if day == now.date():
                hours = 1 if getattr(request, "param", "open") == "closed" else -1
                return Stamp(now + timedelta(hours=hours))
            return Stamp(datetime.combine(day, time(14), UTC))

        def session_close(self, day):
            day = date.fromisoformat(day)
            if day == now.date():
                hours = 7 if getattr(request, "param", "open") == "closed" else 1
                return Stamp(now + timedelta(hours=hours))
            return Stamp(datetime.combine(day, time(21), UTC))

    stock_sessions._calendar_bounds.cache_clear()
    request.addfinalizer(stock_sessions._calendar_bounds.cache_clear)
    monkeypatch.setattr(
        stock_sessions.calendars,
        "get_calendar",
        lambda alias, *, start, end: SyntheticCalendar(start, end),
    )
    async with factory.begin() as db:
        # Display/collection alone cannot authorize permanent financial receipts
        # or their retained recovery copies. These remain synthetic permissions.
        await db.execute(
            update(StockDataAdmission).values(
                scope=StockDataAdmission.scope.op("||")(
                    {
                        "durable_accounting": True,
                        "backup_restore": True,
                        "retention_mode": "durable-accounting",
                    }
                )
            )
        )
        for authority in (admitted("quotes"), action_admitted(), evidence(now)):
            authority = replace(
                authority,
                reviewed_at=now - timedelta(hours=1),
                valid_from=now - timedelta(hours=1),
                valid_until=now + timedelta(hours=1),
                scope={
                    **authority.scope,
                    "durable_accounting": True,
                    "backup_restore": True,
                    "retention_mode": "durable-accounting",
                },
            )
            await db.execute(insert(StockDataAdmission).values(**asdict(authority)))
        await db.execute(
            insert(StockSession),
            [
                asdict(row)
                for row in stock_sessions.build_sessions(
                    now,
                    replace(
                        evidence(now),
                        valid_from=now - timedelta(hours=1),
                        valid_until=now + timedelta(hours=1),
                    ),
                )
            ],
        )
        await db.execute(
            insert(StockQuote).values(
                coin_id=cid,
                bid=Decimal(100),
                ask=Decimal(102),
                mid=Decimal(101),
                source="alpaca",
                feed="iex",
                event_at=now,
                collected_at=now,
                session_date=now.date(),
                admission_generation=4,
                unit_epoch=0,
            )
        )
        await db.execute(
            update(StockActionState)
            .where(StockActionState.coin_id == cid)
            .values(
                admission_generation=4,
                health="current",
                checked_at=now,
                valid_until=now + timedelta(hours=1),
                coverage_start=now - timedelta(days=1),
                covered_until=now,
            )
        )
        await persist_status_batch(
            db,
            StatusBatch(
                events=(
                    StatusEvent(
                        cid,
                        "synthetic-status-asset",
                        "normal",
                        now - timedelta(hours=1),
                        now.date(),
                        1,
                        "synthetic-independent-status",
                    ),
                ),
                observed_at=now,
                admission_generation=4,
                continuity_generation=1,
                baseline_verified=True,
                contiguous=True,
                complete=True,
                end_marker=True,
            ),
            coin_id=cid,
        )
    try:
        yield factory, cid, uid, now
    finally:
        from app.models.corporate_action import StockActionEvent, StockActionObservation

        async with factory.begin() as db:
            await db.execute(
                delete(StockActionObservation).where(
                    StockActionObservation.event_id.in_(
                        select(StockActionEvent.id).where(StockActionEvent.coin_id == cid)
                    )
                )
            )
        stock_sessions._calendar_bounds.cache_clear()


@pytest_asyncio.fixture
async def stock_pair_case(stock_trade_case):
    """Two explicitly verified instruments; cleanup owns only the second slot."""
    from sqlalchemy import literal, text

    from app.models.corporate_action import StockActionState, StockOwnershipMovement
    from app.models.stock import StockQuote
    from app.models.stock_execution import StockFillFacts
    from app.models.trade import Holding, Trade

    factory, first, uid, now = stock_trade_case
    async with factory.begin() as db:
        cid, old_asset, old_verified = (
            await db.execute(
                select(
                    StockInstrument.coin_id,
                    StockInstrument.provider_asset_id,
                    StockInstrument.provider_verified_at,
                )
                .where(StockInstrument.coin_id != first)
                .order_by(StockInstrument.coin_id)
                .limit(1)
            )
        ).one()
        await db.execute(
            update(StockInstrument)
            .where(StockInstrument.coin_id == cid)
            .values(provider_asset_id="synthetic-second-asset", provider_verified_at=now)
        )
        for model in (StockQuote, StockActionState, StockStatusEvidence):
            columns = list(model.__table__.columns)
            expressions = [
                literal(cid)
                if c.name == "coin_id"
                else literal("synthetic-second-asset")
                if c.name == "provider_asset_id"
                else c
                for c in columns
            ]
            await db.execute(
                insert(model).from_select(
                    [c.name for c in columns], select(*expressions).where(model.coin_id == first)
                )
            )
    try:
        yield factory, (first, cid), uid, now
    finally:
        async with factory.begin() as db:
            allowed = (
                await db.execute(
                    text(
                        "SELECT current_database()='birja_test' AND current_user='birja_test' "
                        "AND rolsuper FROM pg_roles WHERE rolname=current_user"
                    )
                )
            ).scalar_one()
            if not allowed:
                raise RuntimeError("Explicit isolated fixture cleanup only")
            for table in ("stock_fill_facts", "stock_ownership_movements", "trades"):
                await db.execute(
                    text(f"ALTER TABLE public.{table} DISABLE TRIGGER stock_record_immutable")
                )
            for model in (
                StockFillFacts,
                StockOwnershipMovement,
                Holding,
                Trade,
                StockActionState,
                StockQuote,
                StockStatusEvidence,
            ):
                await db.execute(delete(model).where(model.coin_id == cid))
            for table in ("stock_fill_facts", "stock_ownership_movements", "trades"):
                await db.execute(
                    text(f"ALTER TABLE public.{table} ENABLE TRIGGER stock_record_immutable")
                )
            await db.execute(
                update(StockInstrument)
                .where(StockInstrument.coin_id == cid)
                .values(provider_asset_id=old_asset, provider_verified_at=old_verified)
            )
