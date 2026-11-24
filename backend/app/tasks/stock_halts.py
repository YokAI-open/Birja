"""Collect and publish bounded reported-halt evidence for admitted stock simulations."""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import httpx
from redis.asyncio import Redis
from sqlalchemy import func, or_, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.stock_execution import StockStatusEvidence
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_halts import (
    MAX_REPORT_BYTES,
    REPORT_LOCK_KEYS,
    SOURCE,
    URL,
    HaltReport,
    parse_halt_report,
)
from app.services.stock_quote_rules import CURATED_SYMBOLS, verified_mapping
from app.services.stock_quotes import load_stock_catalog
from app.services.stock_sessions import load_sessions
from app.services.stock_trading_rules import StatusEvidence
from app.tasks.scheduler import CycleResult
from app.tasks.stock_scheduler import _admissions, _open_exchanges

POLL_SECONDS = 60
DUE_CHECK_SECONDS = 2
_POLL_KEY = "sim:stock-halts:nasdaq-rss"
logger = logging.getLogger(__name__)


def _admitted(
    evidence: dict[str, ProductAdmission], at: datetime, *, account: str, server: str
) -> bool:
    return all(
        evaluate_admission(
            evidence.get(product),
            product,
            purpose,
            at,
            account=account,
            server=server,
            feed=SOURCE if product == "status" else "iex",
        ).allowed
        for product in ("reference", "status", "calendar")
        for purpose in ("collection", "display", "derived", "retention")
    )


async def fetch_report(
    http: httpx.AsyncClient, now: Callable[[], datetime], *, max_bytes: int = MAX_REPORT_BYTES
) -> HaltReport:
    async with http.stream("GET", URL, follow_redirects=False) as response:
        if response.status_code != 200:
            raise ValueError("Reported-halt source unavailable")
        body = bytearray()
        async for chunk in response.aiter_bytes(16384):
            if len(body) + len(chunk) > max_bytes:
                raise ValueError("Reported-halt response exceeds bound")
            body.extend(chunk)
        return parse_halt_report(
            bytes(body), last_modified=response.headers.get("Last-Modified", ""), observed_at=now()
        )


async def _publish(
    db: AsyncSession,
    report: HaltReport,
    evidence: dict[str, ProductAdmission],
    *,
    account: str,
    server: str,
) -> int:
    # Serialize report publication with each final stock-order check. One
    # exclusive report lock avoids taking multiple instrument gates at once.
    await db.execute(text(f"SELECT pg_advisory_xact_lock({REPORT_LOCK_KEYS})"))
    checked = await db.scalar(func.clock_timestamp())
    if not isinstance(checked, datetime) or not report.observed_at <= checked < report.valid_until:
        return 0
    scope = {"account": account, "server": server}
    if await _admissions(db) != evidence or not _admitted(evidence, checked, **scope):
        return 0
    session_date = checked.date()
    sessions = await load_sessions(db, checked)
    opened = _open_exchanges(checked, sessions, evidence["calendar"], **scope)
    if not opened:
        return 0
    mappings = await load_stock_catalog(db)
    if {mapping.symbol for mapping in mappings} != CURATED_SYMBOLS or not all(
        verified_mapping(mapping, checked) for mapping in mappings
    ):
        return 0
    deadlines = [evidence[product].valid_until for product in ("reference", "status", "calendar")]
    retention = report.observed_at + timedelta(
        seconds=evidence["status"].quota["retention_seconds"]
    )
    valid_until = min(
        report.valid_until, retention, *(until for until in deadlines if until is not None)
    )
    if checked >= valid_until:
        return 0
    observed_seconds = int(report.observed_at.timestamp())
    generation = observed_seconds * 1_000_000 + report.observed_at.microsecond
    records = [
        asdict(
            StatusEvidence(
                coin_id=mapping.coin_id,
                provider_asset_id=str(mapping.provider_asset_id),
                state="halted"
                if report.market_halted or mapping.symbol in report.halted_symbols
                else "normal",
                event_at=report.published_at,
                observed_at=report.observed_at,
                session_date=session_date,
                admission_generation=evidence["status"].generation,
                continuity_generation=generation,
                valid_until=valid_until,
                source=SOURCE,
                source_ref=report.digest,
            )
        )
        for mapping in sorted(mappings, key=lambda mapping: mapping.coin_id)
        if mapping.listing_exchange in opened
    ]
    if not records:
        return 0
    statement = insert(StockStatusEvidence).values(records)
    written = (
        (
            await db.execute(
                statement.on_conflict_do_update(
                    index_elements=[StockStatusEvidence.coin_id],
                    set_={
                        key: getattr(statement.excluded, key)
                        for key in records[0]
                        if key != "coin_id"
                    },
                    where=or_(
                        StockStatusEvidence.source != SOURCE,
                        StockStatusEvidence.event_at < statement.excluded.event_at,
                        StockStatusEvidence.admission_generation
                        < statement.excluded.admission_generation,
                    ),
                ).returning(StockStatusEvidence.coin_id)
            )
        )
        .scalars()
        .all()
    )
    if await _admissions(db) != evidence or await load_stock_catalog(db) != mappings:
        raise ValueError("Reported-halt authority changed before commit")
    final = await db.scalar(func.clock_timestamp())
    if (
        not isinstance(final, datetime)
        or not final < valid_until
        or not _admitted(evidence, final, **scope)
        or _open_exchanges(final, sessions, evidence["calendar"], **scope) != opened
    ):
        raise ValueError("Reported-halt authority changed before commit")
    return len(written)


async def run_stock_halt_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> CycleResult:
    if not settings.stock_data_enabled:
        return CycleResult("ok")
    scope = {"account": settings.stock_data_account, "server": settings.stock_data_server}
    try:
        async with asyncio.timeout(10):
            if await redis.exists(_POLL_KEY):
                return CycleResult("locked")
            checked = now()
            async with sessionmaker() as db:
                evidence = await _admissions(db)
                if not _admitted(evidence, checked, **scope):
                    return CycleResult("ok")
                sessions = await load_sessions(db, checked)
            if not _open_exchanges(checked, sessions, evidence["calendar"], **scope):
                return CycleResult("ok")
            if not await redis.set(_POLL_KEY, "polled", nx=True, ex=POLL_SECONDS):
                return CycleResult("locked")
            report = await fetch_report(
                http,
                now,
                max_bytes=min(MAX_REPORT_BYTES, evidence["status"].quota["max_response_bytes"]),
            )
            async with sessionmaker.begin() as db:
                return CycleResult("ok", accepted=await _publish(db, report, evidence, **scope))
    except Exception as exc:
        logger.warning("reported stock halt cycle failed: %s", type(exc).__name__)
        return CycleResult("source_error")
