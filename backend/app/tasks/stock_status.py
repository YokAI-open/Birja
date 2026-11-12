"""Finite offline status cycle in the single scheduler lane; no live transport."""

import asyncio
import logging
from dataclasses import replace

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.stock_execution import StockStatusEvidence
from app.services.stock_status import StatusUnavailable, invalidate_status, persist_status_batch
from app.services.stock_status_rules import StatusBatch, StatusEvent, status_batch_within_bounds
from app.tasks.scheduler import CycleResult

logger = logging.getLogger(__name__)


async def _invalidate_all(factory: async_sessionmaker[AsyncSession]) -> int:
    async with factory() as db:
        ids = list(
            (
                await db.scalars(
                    select(StockStatusEvidence.coin_id)
                    .order_by(StockStatusEvidence.coin_id)
                    .limit(21)
                )
            ).all()
        )
    if len(ids) > 20:
        raise ValueError("Unbounded status catalogue")
    changed = 0
    for cid in ids:
        async with factory.begin() as db:
            changed += await invalidate_status(db, cid)
    return changed


async def run_stock_status_cycle(
    session_factory: async_sessionmaker[AsyncSession],
    source: StatusBatch | None = None,
    *,
    settings: SchedulerSettings | None = None,
) -> CycleResult:
    """None invalidates startup continuity; finite injection is test-only.

    No socket, REST request, credential or configuration-selectable fake source
    exists. Therefore this path makes zero account-quota-consuming attempts.
    Any future real transport must use the existing shared attempt quota and
    separately verified bootstrap/continuity/rights; this is not an adapter.
    """
    if source is not None and (settings is None or settings.env != "test"):
        raise ValueError("Finite status injection requires explicit test settings")
    try:
        async with asyncio.timeout(10):
            if source is None:
                return CycleResult("ok", rejected=await _invalidate_all(session_factory))
            if (
                not status_batch_within_bounds(source)
                or any(
                    not isinstance(event, StatusEvent) or type(event.coin_id) is not int
                    for event in source.events
                )
                or source.lost is not False
                or source.reconnected is not False
                or source.complete is not True
                or source.contiguous is not True
                or source.end_marker is not True
            ):
                return CycleResult("source_error", rejected=await _invalidate_all(session_factory))
            groups: dict[int, list[StatusEvent]] = {}
            for event in source.events:
                groups.setdefault(event.coin_id, []).append(event)
            if len(groups) > 20:
                return CycleResult("source_error", rejected=await _invalidate_all(session_factory))
            assert settings is not None  # noqa: S101 - explicit injection guard above
            accepted = rejected = 0
            for cid, events in sorted(groups.items()):
                try:
                    async with session_factory.begin() as db:
                        value = await persist_status_batch(
                            db,
                            replace(source, events=tuple(events)),
                            coin_id=cid,
                            account=settings.stock_data_account,
                            server=settings.stock_data_server,
                        )
                    if value.continuity_current:
                        accepted += 1
                    else:
                        rejected += 1
                except StatusUnavailable:
                    async with session_factory.begin() as db:
                        await invalidate_status(db, cid)
                    rejected += 1
            return CycleResult("ok", accepted=accepted, rejected=rejected)
    except Exception as exc:
        logger.warning("stock status cycle failed: %s", type(exc).__name__)
        try:
            async with asyncio.timeout(2):
                await _invalidate_all(session_factory)
        except Exception as invalidation:
            logger.warning("stock status invalidation failed: %s", type(invalidation).__name__)
        return CycleResult("source_error")
