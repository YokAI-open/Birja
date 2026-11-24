"""Reviewed financial quotes and held-stock demand for promoted catalog issues."""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Literal

from sqlalchemy import func, select, text, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.selectable import Exists

from app.core.config import SchedulerSettings, Settings
from app.models.corporate_action import StockActionState
from app.models.stock import StockDataAdmission
from app.models.stock_catalog_finance import StockCatalogFinancialQuote, StockCatalogInstrument
from app.models.trade import Holding
from app.models.user import Account
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_catalog_promotion import (
    _EXECUTION_FIELDS,
    _MARK_FIELDS,
    CatalogFinancialBinding,
    _catalog_id,
    load_catalog_financial_binding,
    load_catalog_mark_binding,
)
from app.services.stock_catalog_publish import _CATALOG_LOCK
from app.services.stock_ownership import acquire_stock_gate
from app.services.stock_quote_rules import RawIexQuote, ValidIexQuote, utc, validate_iex_quote
from app.services.stock_sessions import (
    RegularSession,
    SessionDecision,
    build_sessions,
    load_sessions,
    session_at,
)

_FRESH = timedelta(seconds=120)
_NEVER_QUOTED = datetime(1970, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, order=True)
class HeldQuotePosition:
    checked_at: datetime
    coin_id: int


@dataclass(frozen=True)
class HeldCatalogQuoteCandidate:
    catalog_id: int
    listing_id: int
    coin_id: int
    position: HeldQuotePosition


def _active_holding(coin_id: int | InstrumentedAttribute[int]) -> Exists:
    return (
        select(Holding.id)
        .join(Account, Account.id == Holding.portfolio_id)
        .where(Holding.coin_id == coin_id, Holding.quantity > 0, Account.closed_at.is_(None))
        .exists()
    )


async def is_catalog_quote_held(db: AsyncSession, coin_id: int) -> bool:
    return bool(await db.scalar(select(_active_holding(coin_id))))


async def held_catalog_quote_page(
    db: AsyncSession,
    *,
    now: datetime,
    after: HeldQuotePosition | None,
    limit: int,
    refresh_seconds: int = 60,
) -> tuple[HeldCatalogQuoteCandidate, ...]:
    """Walk only promoted issues with positive positions in active portfolios."""
    if not 1 <= limit <= 8 or not 0 <= refresh_seconds <= 120:
        raise ValueError("invalid held quote page bounds")
    instrument, quote = StockCatalogInstrument, StockCatalogFinancialQuote
    observed = func.coalesce(quote.observed_at, _NEVER_QUOTED)
    query = (
        select(instrument.catalog_id, instrument.listing_id, instrument.coin_id, observed)
        .outerjoin(
            quote,
            (quote.coin_id == instrument.coin_id) & (quote.listing_id == instrument.listing_id),
        )
        .where(
            _active_holding(instrument.coin_id),
            observed <= now - timedelta(seconds=refresh_seconds),
        )
        .order_by(observed, instrument.coin_id)
        .limit(limit)
    )
    if after is not None:
        query = query.where(
            tuple_(observed, instrument.coin_id) > (after.checked_at, after.coin_id)
        )
    return tuple(
        HeldCatalogQuoteCandidate(catalog, listing, coin, HeldQuotePosition(checked, coin))
        for catalog, listing, coin, checked in await db.execute(query)
    )


@dataclass(frozen=True)
class _QuoteGrant:
    id: int
    valid_until: datetime
    scope_cap: int
    requests_cap: int
    bytes_cap: int
    reviewed_at: datetime


def _cap(scope: dict[str, object], name: str, maximum: int, default: int) -> int | None:
    value = scope.get(name, default)
    return value if type(value) is int and 1 <= value <= maximum else None


async def _quote_grant(
    db: AsyncSession,
    binding: CatalogFinancialBinding,
    at: datetime,
    *,
    artifact: Literal["catalog_execution", "catalog_mark"],
    admission_id: int | None,
) -> _QuoteGrant | None:
    rows = (
        await db.execute(
            text("""
        SELECT a.id,a.reviewed_at,a.valid_until,a.scope
          FROM public.stock_catalog_instruments b
          JOIN public.stock_catalog_listings l ON (l.id,l.security_id)=(b.listing_id,b.catalog_id)
          JOIN public.stock_catalog_admissions a ON a.artifact=:artifact
          WHERE b.catalog_id=:catalog AND b.listing_id=:listing
            AND a.scope @> CAST(:scope AS jsonb)
            AND (CAST(:admission AS bigint) IS NULL OR a.id=:admission)
            AND public.stock_catalog_scope_current(a.id,:artifact,b,l,:at,CAST(:fields AS jsonb))
          ORDER BY a.id LIMIT 2
        """),
            {
                "artifact": artifact,
                "admission": admission_id,
                "catalog": binding.catalog_id,
                "listing": binding.listing_id,
                "at": at,
                "fields": json.dumps(
                    _EXECUTION_FIELDS if artifact == "catalog_execution" else _MARK_FIELDS
                ),
                "scope": json.dumps(
                    {
                        "account": binding.account,
                        "server": binding.server,
                        "catalog_id": str(binding.catalog_id),
                        "listing_id": str(binding.listing_id),
                        "provider_asset_id": binding.provider_asset_id,
                        "feed": "iex",
                    }
                ),
            },
        )
    ).all()
    if len(rows) != 1:
        return None
    grant_id, reviewed_at, expiry, scope = rows[0]
    symbols = _cap(scope, "symbols_per_request", 8, 1)
    requests = _cap(scope, "requests_per_minute", 200, 200)
    response_bytes = _cap(scope, "max_response_bytes", 1048576, 1048576)
    if symbols is None or requests is None or response_bytes is None:
        return None
    return _QuoteGrant(grant_id, expiry, symbols, requests, response_bytes, reviewed_at)


async def _sessions(
    db: AsyncSession, binding: CatalogFinancialBinding, now: datetime
) -> tuple[SessionDecision, RegularSession | None]:
    model = StockDataAdmission
    columns = [column for column in model.__table__.columns if column.name != "id"]
    row = (
        (await db.execute(select(*columns).where(model.product == "calendar")))
        .mappings()
        .one_or_none()
    )
    calendar = ProductAdmission(**row) if row else None
    return catalog_mark_sessions(
        calendar,
        await load_sessions(db, now),
        binding.listing_exchange,
        now,
        account=binding.account,
        server=binding.server,
    )


def catalog_mark_sessions(
    calendar: ProductAdmission | None,
    sessions: Sequence[RegularSession],
    exchange: str,
    now: datetime,
    *,
    account: str,
    server: str,
) -> tuple[SessionDecision, RegularSession | None]:
    """Return current and exact latest closed bounds from one admitted snapshot."""
    scope = {"account": account, "server": server}
    if not all(
        evaluate_admission(
            calendar, "calendar", purpose, now, account=account, server=server
        ).allowed
        for purpose in ("derived", "collection", "retention")
    ):
        return SessionDecision(), None
    decision = session_at(exchange, now, sessions, calendar, **scope)
    if decision.state != "closed":
        return decision, None
    previous = max(
        (
            row
            for row in build_sessions(now, calendar, **scope)
            if row.exchange == exchange and row.closes_at is not None and row.closes_at <= now
        ),
        key=lambda row: row.session_date,
        default=None,
    )
    return decision, previous if previous in sessions else None


@dataclass(frozen=True)
class CatalogFinancialQuoteContext:
    binding: CatalogFinancialBinding
    session: RegularSession
    unit_epoch: int
    quote_not_before: datetime | None
    execution: _QuoteGrant
    mark: _QuoteGrant | None
    valid_until: datetime

    @property
    def fingerprint(self) -> str:
        return sha256(repr(self).encode()).hexdigest()

    @property
    def symbols_per_request(self) -> int:
        return (
            min(self.execution.scope_cap, self.mark.scope_cap)
            if self.mark
            else self.execution.scope_cap
        )

    @property
    def requests_per_minute(self) -> int:
        return (
            min(self.execution.requests_cap, self.mark.requests_cap)
            if self.mark
            else self.execution.requests_cap
        )

    @property
    def max_response_bytes(self) -> int:
        return (
            min(self.execution.bytes_cap, self.mark.bytes_cap)
            if self.mark
            else self.execution.bytes_cap
        )


async def load_catalog_financial_quote_context(
    db: AsyncSession,
    settings: Settings | SchedulerSettings,
    catalog_id: int,
    listing_id: int,
    now: datetime,
) -> CatalogFinancialQuoteContext | None:
    if not settings.stock_data_enabled:
        return None
    binding = await load_catalog_financial_binding(
        db, catalog_id, listing_id, now, allow_fixture=settings.env == "test"
    )
    if binding is None or (binding.account, binding.server) != (
        settings.stock_data_account,
        settings.stock_data_server,
    ):
        return None
    decision, _ = await _sessions(db, binding, now)
    if decision.state != "open" or decision.current is None or decision.valid_until is None:
        return None
    execution = await _quote_grant(
        db, binding, now, artifact="catalog_execution", admission_id=binding.admission_id
    )
    if execution is None:
        return None
    mark = await _quote_grant(db, binding, now, artifact="catalog_mark", admission_id=None)
    if mark is not None:
        mark = replace(
            mark,
            valid_until=min(
                mark.valid_until,
                binding.identity_valid_until or binding.valid_until,
                decision.valid_until,
            ),
        )
    unit = (
        await db.execute(
            select(StockActionState.unit_epoch, StockActionState.quote_not_before).where(
                StockActionState.coin_id == binding.coin_id
            )
        )
    ).one_or_none()
    if unit is None:
        return None
    return CatalogFinancialQuoteContext(
        binding,
        decision.current,
        unit.unit_epoch,
        unit.quote_not_before,
        execution,
        mark,
        min(binding.valid_until, decision.valid_until, execution.valid_until),
    )


async def publish_catalog_financial_quote(
    db: AsyncSession,
    settings: SchedulerSettings,
    expected: CatalogFinancialQuoteContext,
    price: ValidIexQuote,
    now: Callable[[], datetime],
    *,
    held_only: bool,
) -> bool:
    """Recheck after locks and store just the normalized row in this transaction."""
    binding = expected.binding
    await db.execute(text("SELECT pg_advisory_xact_lock_shared(:key)"), {"key": _CATALOG_LOCK})
    await acquire_stock_gate(db, binding.coin_id)
    if held_only and not await is_catalog_quote_held(db, binding.coin_id):
        return False
    checked = now()
    current = await load_catalog_financial_quote_context(
        db, settings, binding.catalog_id, binding.listing_id, checked
    )
    observed = now()
    session = expected.session
    if (
        current != expected
        or session.opens_at is None
        or session.closes_at is None
        or not session.opens_at
        <= price.event_at
        <= price.collected_at
        <= observed
        < session.closes_at
        or observed >= expected.valid_until
        or observed - price.event_at >= _FRESH
        or (expected.quote_not_before is not None and price.event_at < expected.quote_not_before)
    ):
        return False
    mark = expected.mark if expected.mark and observed < expected.mark.valid_until else None
    valid_until = mark.valid_until if mark else expected.valid_until
    model = StockCatalogFinancialQuote
    record = insert(model).values(
        coin_id=binding.coin_id,
        catalog_id=binding.catalog_id,
        listing_id=binding.listing_id,
        provider_asset_id=binding.provider_asset_id,
        provider_admission_id=binding.provider_admission_id,
        execution_admission_id=expected.execution.id,
        mark_admission_id=mark.id if mark else None,
        bid=price.bid,
        ask=price.ask,
        unit_epoch=expected.unit_epoch,
        event_at=price.event_at,
        collected_at=price.collected_at,
        observed_at=observed,
        opens_at=session.opens_at,
        closes_at=session.closes_at,
        session_date=session.session_date,
        calendar_generation=session.calendar_admission_generation,
        valid_until=valid_until,
    )
    mutable = {
        col.name: record.excluded[col.name]
        for col in model.__table__.columns
        if col.name != "coin_id"
    }
    result = await db.scalar(
        record.on_conflict_do_update(
            index_elements=[model.coin_id],
            set_=mutable,
            where=(record.excluded.observed_at >= model.observed_at)
            & (
                (record.excluded.listing_id != model.listing_id)
                | (record.excluded.unit_epoch != model.unit_epoch)
                | (
                    tuple_(record.excluded.event_at, record.excluded.collected_at)
                    >= tuple_(model.event_at, model.collected_at)
                )
            ),
        ).returning(model.coin_id)
    )
    return result is not None


@dataclass(frozen=True)
class CatalogFinancialMark:
    bid: Decimal
    ask: Decimal
    mid: Decimal
    event_at: datetime
    collected_at: datetime
    valid_until: datetime
    mode: Literal["fresh", "closed"]


def catalog_mark_units_safe(action: StockActionState, now: datetime) -> bool:
    return (
        action.health == "current"
        and action.checked_at is not None
        and action.checked_at <= now
        and action.valid_until is not None
        and now < action.valid_until
        and (action.next_blocking_at is None or now < action.next_blocking_at)
    )


async def read_catalog_financial_mark(
    db: AsyncSession,
    catalog_id: int,
    listing_id: int,
    now: datetime,
    *,
    allow_fixture: bool = False,
    account: str | None = None,
    server: str | None = None,
) -> CatalogFinancialMark | None:
    """Read display-only evidence for one issue, including its prior closed session."""
    if not (_catalog_id(catalog_id) and _catalog_id(listing_id) and utc(now)):
        return None
    model = StockCatalogFinancialQuote
    row = (
        await db.execute(
            select(model, StockActionState)
            .join(StockActionState, StockActionState.coin_id == model.coin_id)
            .where(
                model.catalog_id == catalog_id,
                model.listing_id == listing_id,
                model.observed_at <= now,
                model.valid_until > now,
            )
            .execution_options(populate_existing=True)
        )
    ).one_or_none()
    if row is None:
        return None
    quote, action = row
    if quote.mark_admission_id is None or not catalog_mark_units_safe(action, now):
        return None
    binding = await load_catalog_mark_binding(
        db, catalog_id, listing_id, quote.mark_admission_id, now, allow_fixture=allow_fixture
    )
    if (
        binding is None
        or quote.coin_id != binding.coin_id
        or quote.provider_asset_id != binding.provider_asset_id
        or quote.provider_admission_id != binding.provider_admission_id
        or (account is not None and account != binding.account)
        or (server is not None and server != binding.server)
    ):
        return None
    grant = await _quote_grant(
        db, binding, now, artifact="catalog_mark", admission_id=quote.mark_admission_id
    )
    if grant is None or not grant.reviewed_at <= quote.collected_at < grant.valid_until:
        return None
    decision, previous = await _sessions(db, binding, now)
    return evaluate_catalog_financial_mark(
        quote,
        action,
        binding.listing_exchange,
        now,
        permission_until=min(grant.valid_until, binding.valid_until),
        decision=decision,
        previous=previous,
    )


def evaluate_catalog_financial_mark(
    quote: StockCatalogFinancialQuote,
    action: StockActionState,
    exchange: str,
    now: datetime,
    *,
    permission_until: datetime,
    decision: SessionDecision,
    previous: RegularSession | None,
) -> CatalogFinancialMark | None:
    """Check the exact observed quote, unit and session without touching Redis."""
    if (
        quote.mark_admission_id is None
        or not quote.observed_at <= now < quote.valid_until
        or action.unit_epoch != quote.unit_epoch
        or not catalog_mark_units_safe(action, now)
        or action.valid_until is None
        or (action.quote_not_before is not None and quote.event_at < action.quote_not_before)
    ):
        return None
    if decision.current is None or decision.valid_until is None or decision.state == "unknown":
        return None
    deadline = min(
        quote.valid_until,
        permission_until,
        action.valid_until,
        decision.valid_until,
    )
    if action.next_blocking_at is not None:
        deadline = min(deadline, action.next_blocking_at)
    if decision.state == "open":
        source = decision.current
        mode: Literal["fresh", "closed"] = "fresh"
        if source.closes_at is None:
            return None
        deadline = min(deadline, source.closes_at, quote.event_at + _FRESH)
    else:
        mode = "closed"
        if (
            previous is None
            or decision.next_session is None
            or decision.next_session.opens_at is None
        ):
            return None
        source = previous
        deadline = min(deadline, decision.next_session.opens_at)
    if (
        now >= deadline
        or (quote.session_date, quote.opens_at, quote.closes_at, quote.calendar_generation)
        != (
            source.session_date,
            source.opens_at,
            source.closes_at,
            source.calendar_admission_generation,
        )
        or source.calendar_admission_generation != decision.current.calendar_admission_generation
    ):
        return None
    price = validate_iex_quote(
        RawIexQuote(
            quote.bid,
            quote.ask,
            quote.event_at,
            ["R"],
            tape="C" if exchange == "NASDAQ" else "A",
        ),
        listing_exchange=exchange,
        collected_at=quote.collected_at,
    )
    return (
        CatalogFinancialMark(
            price.bid, price.ask, price.mid, price.event_at, price.collected_at, deadline, mode
        )
        if price
        else None
    )
