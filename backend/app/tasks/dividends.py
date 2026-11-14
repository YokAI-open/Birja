"""Bounded retained-row work; SQL alone owns financial authority and dedup.

Progress cursors are disposable scheduling hints, never accounting state. A
restart scans retained work again and the SQL boundary returns saved results.
"""

import asyncio
import logging
from dataclasses import dataclass
from itertools import zip_longest

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.services.dividends import DividendRefused, process_dividend, record_dividend_hold
from app.tasks.scheduler import CycleResult

logger = logging.getLogger(__name__)
MAX_CANDIDATES = 100
CYCLE_SECONDS = 40


@dataclass
class DividendCursor:
    verified: int = 0
    anchors: int = 0


# Both sources are durable rows. Never join the anchor path to an eligible
# snapshot: a cancelled replacement may deliberately have no such snapshot.
VERIFIED = """SELECT en.id AS key,en.event_id,en.id AS entitlement_id,
 r.fingerprint AS revision_fingerprint,en.fingerprint AS entitlement_fingerprint
 FROM public.stock_dividend_entitlements en
 JOIN public.stock_action_events e ON e.id=en.event_id
 JOIN public.stock_action_revisions r ON r.id=e.current_revision_id
 WHERE en.id>:after AND en.revision_id=r.id AND en.state='eligible'
 AND r.classification='supported_dividend'
 AND r.normalized_terms->>'payable_date' <=
 to_char(clock_timestamp() AT TIME ZONE 'America/New_York','YYYY-MM-DD')
 AND NOT EXISTS(SELECT FROM public.stock_dividend_entitlements newer
 WHERE newer.event_id=en.event_id AND newer.user_id=en.user_id
 AND (newer.version,newer.id)>(en.version,en.id))
 ORDER BY en.id LIMIT :cap"""

ANCHORS = """SELECT p.id AS key,p.id AS payment_id,r.fingerprint AS revision_fingerprint
 FROM public.stock_dividend_payments p
 JOIN public.stock_action_events e ON e.id=p.event_id
 JOIN public.stock_action_revisions r ON r.id=e.current_revision_id
 JOIN public.stock_action_state st ON st.coin_id=p.coin_id
 WHERE p.id>:after AND (
 r.classification<>'supported_dividend' OR st.health<>'current'
 OR st.valid_until IS NULL OR st.valid_until<=clock_timestamp()
 OR NOT EXISTS(SELECT FROM public.stock_dividend_entitlements en
   WHERE en.event_id=p.event_id AND en.user_id=p.user_id
   AND en.revision_id=r.id AND en.state='eligible'
   AND NOT EXISTS(SELECT FROM public.stock_dividend_entitlements newer
     WHERE newer.event_id=en.event_id AND newer.user_id=en.user_id
     AND (newer.version,newer.id)>(en.version,en.id)))
 OR EXISTS(SELECT FROM public.stock_action_events held
   WHERE held.coin_id=p.coin_id AND (
     EXISTS(SELECT FROM public.stock_action_revisions hr WHERE hr.event_id=held.id
       AND hr.classification NOT IN ('supported_dividend','supported_forward_split'))
     OR EXISTS(SELECT FROM public.stock_action_observations ob
       WHERE ob.event_id=held.id AND ob.source_kind='missing_or_uncertain'))))
 ORDER BY p.id LIMIT :cap"""


async def _page(
    sessionmaker: async_sessionmaker[AsyncSession], statement: str, after: int
) -> list[dict[str, int | str]]:
    async with sessionmaker() as db:
        rows = (
            (await db.execute(text(statement), {"after": after, "cap": MAX_CANDIDATES // 2}))
            .mappings()
            .all()
        )
        if not rows and after:
            rows = (
                (await db.execute(text(statement), {"after": 0, "cap": MAX_CANDIDATES // 2}))
                .mappings()
                .all()
            )
        return [dict(row) for row in rows]


async def run_dividend_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    settings: SchedulerSettings,
    cursor: DividendCursor | None = None,
) -> CycleResult:
    if not settings.stock_actions_enabled:
        return CycleResult("ok")
    cursor = cursor if cursor is not None else DividendCursor()
    accepted = rejected = 0
    try:
        async with asyncio.timeout(CYCLE_SECONDS):
            verified = await _page(sessionmaker, VERIFIED, cursor.verified)
            anchors = await _page(sessionmaker, ANCHORS, cursor.anchors)
            for target, anchor in zip_longest(verified, anchors):
                for candidate, held in ((target, False), (anchor, True)):
                    if candidate is None:
                        continue
                    key = int(candidate["key"])
                    # Advance before attempting, including a refused/timeout item;
                    # a held first owner cannot starve later retained owners.
                    if held:
                        cursor.anchors = key
                    else:
                        cursor.verified = key
                    try:
                        async with sessionmaker() as db:
                            if held:
                                await record_dividend_hold(
                                    db,
                                    payment_id=int(candidate["payment_id"]),
                                    expected_revision_fingerprint=str(
                                        candidate["revision_fingerprint"]
                                    ),
                                )
                            else:
                                await process_dividend(
                                    db,
                                    event_id=int(candidate["event_id"]),
                                    entitlement_id=int(candidate["entitlement_id"]),
                                    expected_revision_fingerprint=str(
                                        candidate["revision_fingerprint"]
                                    ),
                                    expected_entitlement_fingerprint=str(
                                        candidate["entitlement_fingerprint"]
                                    ),
                                )
                        accepted += 1
                    except DividendRefused:
                        rejected += 1
        return CycleResult("ok", accepted, rejected)
    except Exception:
        logger.warning("dividend cycle failed: cycle_unavailable")
        return CycleResult("source_error", accepted, rejected)
