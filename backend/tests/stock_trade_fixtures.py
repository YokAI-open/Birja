"""Explicit isolated status authority; never imported by application code.

Financial/action/quote/session cases extend this shared real-DB foundation.
No enabled boolean or live credential supplies product rights.
"""

from dataclasses import asdict, replace
from datetime import timedelta
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
async def stock_trade_case(status_case, ownership):
    """Real independent rows and a deliberately synthetic open session.

    Official schedules have separate tests. This fixture exercises finances at
    any wall-clock hour without faking the DB clock. The ownership fixture owns
    immutable fill/history cleanup.
    """
    from app.models.corporate_action import StockActionState
    from app.models.stock import StockQuote, StockSession
    from app.services.stock_status import persist_status_batch
    from app.services.stock_status_rules import StatusBatch, StatusEvent
    from tests.test_stock_sessions import evidence

    factory, cid, now = status_case
    _, owner_cid, uid = ownership
    assert cid == owner_cid
    async with factory.begin() as db:
        for authority in (admitted("quotes"), action_admitted(), evidence(now)):
            authority = replace(
                authority,
                reviewed_at=now - timedelta(hours=1),
                valid_from=now - timedelta(hours=1),
                valid_until=now + timedelta(hours=1),
            )
            await db.execute(insert(StockDataAdmission).values(**asdict(authority)))
        exchange = (
            await db.execute(
                select(StockInstrument.listing_exchange).where(StockInstrument.coin_id == cid)
            )
        ).scalar_one()
        await db.execute(
            insert(StockSession).values(
                exchange=exchange,
                session_date=now.date(),
                opens_at=now - timedelta(hours=1),
                closes_at=now + timedelta(hours=1),
                coverage_start=now.date() - timedelta(days=45),
                coverage_end=now.date() + timedelta(days=90),
                calendar_admission_generation=4,
            )
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
    yield factory, cid, uid, now
