"""Collect and publish bounded reported-halt evidence for admitted stock simulations."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Literal

import httpx
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogAlias, StockCatalogListing
from app.models.stock_catalog_finance import StockCatalogFinancialQuote, StockCatalogStatus
from app.models.stock_execution import StockStatusEvidence
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_catalog_promotion import (
    CatalogFinancialBinding,
    load_catalog_financial_binding,
)
from app.services.stock_catalog_quote_demand import pending_catalog_quotes
from app.services.stock_halts import (
    MAX_REPORT_BYTES,
    REPORT_LOCK_KEYS,
    SOURCE,
    URL,
    HaltReport,
    catalog_report_state,
    parse_halt_report,
)
from app.services.stock_ownership import acquire_stock_gate
from app.services.stock_quote_rules import CURATED_SYMBOLS, verified_mapping
from app.services.stock_quotes import load_stock_catalog
from app.services.stock_sessions import load_sessions, session_at
from app.services.stock_trading_rules import StatusEvidence
from app.tasks.scheduler import CycleResult
from app.tasks.stock_scheduler import _admissions, _open_exchanges

if TYPE_CHECKING:
    from app.services.stock_catalog_financial_quotes import HeldQuotePosition

POLL_SECONDS = 60
DUE_CHECK_SECONDS = 2
_POLL_KEY = "sim:stock-halts:nasdaq-rss"
_CATALOG_PAGE = 8
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CatalogHaltWindow:
    """One scheduler's in-memory report and bounded held-issue cursor."""

    report: HaltReport | None = None
    held_after: HeldQuotePosition | None = None


_CATALOG_HALT_GRANT = text("""
 SELECT permission.id,permission.valid_until
 FROM public.stock_catalog_instruments AS binding
 JOIN public.stock_catalog_listings AS listing ON listing.id=binding.listing_id
 JOIN public.stock_catalog_admissions AS permission ON permission.artifact='catalog_halt'
   AND permission.scope @> jsonb_build_object(
     'catalog_id',CAST(binding.catalog_id AS text),'listing_id',CAST(listing.id AS text),
     'account',CAST(:account AS text),'server',CAST(:server AS text))
 WHERE binding.catalog_id=:catalog_id AND binding.listing_id=:listing_id
   AND public.stock_catalog_scope_current(permission.id,'catalog_halt',binding,listing,:at_time,
       (SELECT jsonb_object_agg(field,'["collection","execution","storage","backup"]'::jsonb)
        FROM unnest(ARRAY['report_digest','event_at','valid_until','state']) field))
 ORDER BY permission.id DESC LIMIT 1
 """)


async def _catalog_halt_grant(
    db: AsyncSession, binding: CatalogFinancialBinding, at: datetime
) -> tuple[int, datetime] | None:
    row = (
        await db.execute(
            _CATALOG_HALT_GRANT,
            {
                "account": binding.account,
                "server": binding.server,
                "catalog_id": binding.catalog_id,
                "listing_id": binding.listing_id,
                "at_time": at,
            },
        )
    ).one_or_none()
    return None if row is None else (row.id, row.valid_until)


async def _catalog_targets(
    db: AsyncSession,
    redis: Redis,
    window: CatalogHaltWindow,
    checked: datetime,
    *,
    account: str,
    server: str,
) -> tuple[tuple[int, int], ...]:
    from app.services.stock_catalog_financial_quotes import held_catalog_quote_page

    try:
        pending = await pending_catalog_quotes(redis, account=account, server=server)
    except RedisError:
        # Curated reports and durable catalog targets have their own authority.
        pending = ()
    held = await held_catalog_quote_page(
        db, now=checked, after=window.held_after, limit=_CATALOG_PAGE
    )
    window.held_after = held[-1].position if len(held) == _CATALOG_PAGE else None
    # A completed selection has no pending token by the time this loop runs.
    recent = await db.execute(
        select(StockCatalogFinancialQuote.catalog_id, StockCatalogFinancialQuote.listing_id)
        .where(StockCatalogFinancialQuote.observed_at > checked - timedelta(seconds=120))
        .order_by(StockCatalogFinancialQuote.observed_at.desc(), StockCatalogFinancialQuote.coin_id)
        .limit(_CATALOG_PAGE)
    )
    selected = [(r.catalog_id, r.listing_version) for r in pending if r.purpose == "financial"]
    return tuple(
        dict.fromkeys(
            [
                *selected,
                *((row.catalog_id, row.listing_id) for row in held),
                *((row.catalog_id, row.listing_id) for row in recent),
            ]
        )
    )


async def _catalog_binding(
    db: AsyncSession,
    target: tuple[int, int],
    at: datetime,
    *,
    account: str,
    server: str,
    allow_fixture: bool,
) -> CatalogFinancialBinding | None:
    binding = await load_catalog_financial_binding(db, *target, at, allow_fixture=allow_fixture)
    if binding is None or (binding.account, binding.server) != (account, server):
        return None
    return binding


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


async def _notice_names(
    db: AsyncSession, listing: StockCatalogListing, published_at: datetime, checked: datetime
) -> dict[str, datetime]:
    names = {} if listing.evidence_at is None else {listing.ticker: listing.evidence_at}
    aliases = await db.execute(
        select(StockCatalogAlias.symbol, StockCatalogAlias.verified_at).where(
            StockCatalogAlias.listing_id == listing.id,
            StockCatalogAlias.security_id == listing.security_id,
            StockCatalogAlias.namespace.in_(("act", "cqs", "nasdaq", "former")),
            StockCatalogAlias.verified_at <= published_at,
            StockCatalogAlias.valid_until > checked,
        )
    )
    for alias in aliases:
        names[alias.symbol] = min(names.get(alias.symbol, alias.verified_at), alias.verified_at)
    return names


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


async def _write_catalog_status(
    db: AsyncSession,
    binding: CatalogFinancialBinding,
    report: HaltReport,
    admission_id: int,
    state: Literal["normal", "halted"],
    valid_until: datetime,
    session_date: date,
) -> int:
    status = StockCatalogStatus
    values = {
        "coin_id": binding.coin_id,
        "catalog_id": binding.catalog_id,
        "listing_id": binding.listing_id,
        "admission_id": admission_id,
        "report_digest": report.digest,
        "state": state,
        "event_at": report.published_at,
        "observed_at": report.observed_at,
        "valid_until": valid_until,
        "session_date": session_date,
    }
    statement = insert(status).values(**values)
    result = await db.scalar(
        statement.on_conflict_do_update(
            index_elements=[status.coin_id],
            set_={name: getattr(statement.excluded, name) for name in values if name != "coin_id"},
            where=or_(
                status.event_at < report.published_at,
                (status.event_at == report.published_at)
                & (status.report_digest == report.digest)
                & (
                    (status.listing_id != binding.listing_id)
                    | (status.admission_id != admission_id)
                ),
            ),
        ).returning(status.coin_id)
    )
    return int(result is not None)


async def _project_catalog_halt(
    db: AsyncSession,
    target: tuple[int, int],
    report: HaltReport,
    *,
    account: str,
    server: str,
    allow_fixture: bool,
) -> int:
    await db.execute(text("SELECT pg_advisory_xact_lock_shared(1026019025::bigint)"))
    checked = await db.scalar(func.clock_timestamp())
    if not isinstance(checked, datetime):
        return 0
    scope = {"account": account, "server": server}
    binding = await _catalog_binding(db, target, checked, **scope, allow_fixture=allow_fixture)
    if binding is None:
        return 0
    await acquire_stock_gate(db, binding.coin_id)
    await db.execute(text(f"SELECT pg_advisory_xact_lock({REPORT_LOCK_KEYS})"))
    checked = await db.scalar(func.clock_timestamp())
    if not isinstance(checked, datetime) or not report.observed_at <= checked < report.valid_until:
        return 0
    if await _catalog_binding(db, target, checked, **scope, allow_fixture=allow_fixture) != binding:
        return 0
    grant = await _catalog_halt_grant(db, binding, checked)
    calendar = (await _admissions(db)).get("calendar")
    if grant is None or calendar is None:
        return 0
    sessions = await load_sessions(db, checked)
    session = session_at(binding.listing_exchange, checked, sessions, calendar, **scope)
    if session.state != "open" or session.current is None or session.valid_until is None:
        return 0
    listing = await db.get(StockCatalogListing, binding.listing_id)
    if listing is None or listing.evidence_at is None:
        return 0
    names = await _notice_names(db, listing, report.published_at, checked)
    state = catalog_report_state(report, binding.listing_exchange, names)
    if state is None:
        status = StockCatalogStatus
        await db.execute(
            update(status)
            .where(
                status.coin_id == binding.coin_id,
                status.event_at <= report.published_at,
                status.observed_at < checked,
            )
            .values(
                valid_until=func.least(
                    status.valid_until, status.observed_at + timedelta(microseconds=1)
                )
            )
        )
        return 0
    admission_id, scope_until = grant
    until = min(report.valid_until, scope_until, binding.valid_until, session.valid_until)
    if checked >= until:
        return 0
    return await _write_catalog_status(
        db, binding, report, admission_id, state, until, session.current.session_date
    )


async def _can_collect_catalog_report(
    db: AsyncSession,
    targets: tuple[tuple[int, int], ...],
    opened: set[str],
    checked: datetime,
    *,
    account: str,
    server: str,
    allow_fixture: bool,
) -> bool:
    for target in targets:
        binding = await _catalog_binding(
            db, target, checked, account=account, server=server, allow_fixture=allow_fixture
        )
        if (
            binding is not None
            and binding.listing_exchange in opened
            and await _catalog_halt_grant(db, binding, checked) is not None
        ):
            return True
    return False


async def _publish_catalog_report(
    sessionmaker: async_sessionmaker[AsyncSession],
    targets: tuple[tuple[int, int], ...],
    report: HaltReport,
    *,
    account: str,
    server: str,
    allow_fixture: bool,
) -> int:
    accepted = 0
    for target in targets:
        try:
            async with sessionmaker.begin() as db:
                written = await _project_catalog_halt(
                    db, target, report, account=account, server=server, allow_fixture=allow_fixture
                )
            accepted += written
        except Exception as exc:
            logger.warning("catalog halt projection failed: %s", type(exc).__name__)
    return accepted


async def _expire_prior_catalog_reports(
    db: AsyncSession, report: HaltReport, *, account: str, server: str
) -> None:
    await db.execute(text(f"SELECT pg_advisory_xact_lock({REPORT_LOCK_KEYS})"))
    admission = StockCatalogAdmission
    status = StockCatalogStatus
    await db.execute(
        update(status)
        .where(
            status.event_at < report.published_at,
            status.observed_at < report.observed_at,
            status.valid_until > report.observed_at,
            status.admission_id.in_(
                select(admission.id).where(
                    admission.artifact == "catalog_halt",
                    admission.scope.contains({"account": account, "server": server}),
                )
            ),
        )
        .values(valid_until=status.observed_at + timedelta(microseconds=1))
    )


async def run_stock_halt_cycle(
    *,
    sessionmaker: async_sessionmaker[AsyncSession],
    redis: Redis,
    http: httpx.AsyncClient,
    settings: SchedulerSettings,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    catalog_window: CatalogHaltWindow | None = None,
    catalog_redis: Redis | None = None,
) -> CycleResult:
    if not settings.stock_data_enabled:
        return CycleResult("ok")
    scope = {"account": settings.stock_data_account, "server": settings.stock_data_server}
    allow_fixture = settings.env == "test"
    try:
        async with asyncio.timeout(10):
            waiting = bool(await redis.exists(_POLL_KEY))
            checked = now()
            if catalog_window is not None and (
                catalog_window.report is not None and checked >= catalog_window.report.valid_until
            ):
                catalog_window.report = None
            cached = catalog_window.report if catalog_window is not None else None
            if waiting and cached is None:
                return CycleResult("locked")
            async with sessionmaker() as db:
                evidence = await _admissions(db)
                calendar = evidence.get("calendar")
                if calendar is None:
                    return CycleResult("ok")
                sessions = await load_sessions(db, checked)
                opened = _open_exchanges(checked, sessions, calendar, **scope)
                if not opened:
                    return CycleResult("ok")
                targets = (
                    await _catalog_targets(db, catalog_redis, catalog_window, checked, **scope)
                    if catalog_window is not None and catalog_redis is not None
                    else ()
                )
                curated = _admitted(evidence, checked, **scope)
                if (
                    not waiting
                    and not curated
                    and not await _can_collect_catalog_report(
                        db, targets, opened, checked, **scope, allow_fixture=allow_fixture
                    )
                ):
                    return CycleResult("ok")
            accepted = 0
            report = cached
            if not waiting:
                if not await redis.set(_POLL_KEY, "polled", nx=True, ex=POLL_SECONDS):
                    return CycleResult("locked")
                max_bytes = MAX_REPORT_BYTES
                if curated:
                    max_bytes = min(max_bytes, evidence["status"].quota["max_response_bytes"])
                report = await fetch_report(http, now, max_bytes=max_bytes)
                async with sessionmaker.begin() as db:
                    if catalog_window is not None:
                        await _expire_prior_catalog_reports(db, report, **scope)
                    if curated:
                        accepted = await _publish(db, report, evidence, **scope)
                if catalog_window is not None:
                    catalog_window.report = report
            if report is not None:
                accepted += await _publish_catalog_report(
                    sessionmaker, targets, report, **scope, allow_fixture=allow_fixture
                )
            return CycleResult("ok", accepted=accepted)
    except Exception as exc:
        logger.warning("reported stock halt cycle failed: %s", type(exc).__name__)
        return CycleResult("source_error")
