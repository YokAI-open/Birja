"""Dated stock marks keep their original financial snapshot and source rights.

Curated marks use the original fill's immutable admission evidence. Catalog
marks use the durable quote's separate, listing-specific mark permission.
Both paths recheck the applicable authority before a position is valued.
"""

from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import Table, Text, and_, case, cast, exists, func, select
from sqlalchemy.dialects.postgresql import JSONB

from app.core.config import MarketValuationSettings
from app.models.corporate_action import (
    StockActionEvent,
    StockActionRevision,
    StockActionState,
    StockSplitApplication,
)
from app.models.stock import StockInstrument
from app.models.stock_catalog import (
    StockCatalogAdmission,
    StockCatalogAlias,
    StockCatalogGeneration,
    StockCatalogListing,
)
from app.models.stock_catalog_finance import (
    StockCatalogActionCoverage,
    StockCatalogFinancialQuote,
    StockCatalogInstrument,
    StockCatalogStatus,
)
from app.schemas.stock_trades import AuthorityIdentity
from app.services.corporate_actions import action_hold_queries
from app.services.stock_catalog_financial_quotes import (
    catalog_mark_sessions,
    catalog_mark_units_safe,
    evaluate_catalog_financial_mark,
)
from app.services.stock_catalog_promotion import _MARK_FIELDS, CATALOG_ACTION_FIELDS
from app.services.stock_catalog_quotes import validate_catalog_asset_mapping
from app.services.stock_catalog_search import _permitted_listing
from app.services.stock_eligibility import LoadedExecution, admission_rows, session_rows
from app.services.stock_halts import SOURCE as REPORTED_HALT_SOURCE
from app.services.stock_sessions import RegularSession, SessionDecision
from app.services.stock_trading import _authority
from app.services.stock_trading_rules import (
    ExecutionEvidence,
    RefusalReason,
    ValuationEvidence,
    evaluate_valuation,
)


@dataclass(frozen=True)
class StockMark:
    mark_mode: Literal["fresh", "closed", "halted", "unavailable"] = "unavailable"
    valuation_reason: RefusalReason = "permission_unavailable"
    source: Literal["alpaca"] | None = None
    feed: Literal["iex"] | None = None
    event_at: datetime | None = None
    collected_at: datetime | None = None
    historical_admission_until: datetime | None = None
    retained_until: datetime | None = None
    valid_until: datetime | None = None
    authority: AuthorityIdentity | None = None
    units_safe: bool = False


@dataclass(frozen=True)
class StockValuation:
    mid: Decimal | None
    mark: StockMark
    daily_aggregate_allowed: bool = False


def _daily_aggregate_allowed(scope: dict[str, Any]) -> bool:
    """Honor specific limits within an already-admitted durable mark grant.

    Curated marks require derived use, durable accounting and backup/restore.
    Catalog marks require derivation, storage and backup for each mark field.
    A narrower restriction on the derived aggregate can override those uses.
    Raw quote retention controls whether the mark can be used now. The
    observation includes only the private rounded total, never the raw mark.
    """
    return (
        scope.get("durable_derived_use", True) is True
        and scope.get("durable_derived_backup", True) is True
    )


def catalog_valuation_query(coin_ids: Any, settings: MarketValuationSettings, at: datetime) -> Any:
    """Set-based authority projection for the caller's already-owned positive holdings."""
    binding: Table = StockCatalogInstrument.__table__  # type: ignore[assignment]
    listing: Table = StockCatalogListing.__table__  # type: ignore[assignment]
    quote: Table = StockCatalogFinancialQuote.__table__  # type: ignore[assignment]
    action: Table = StockActionState.__table__  # type: ignore[assignment]
    status: Table = StockCatalogStatus.__table__  # type: ignore[assignment]
    coverage = StockCatalogActionCoverage
    generation, instrument = StockCatalogGeneration, StockInstrument
    grant = StockCatalogAdmission.__table__
    mark = grant.alias("mark_permission")
    mapping = grant.alias("provider_mapping")
    actions = grant.alias("action_permission")
    halt = grant.alias("halt_permission")
    directory = grant.alias("directory_permission")
    name = grant.alias("name_permission")
    classification = grant.alias("classification_permission")
    scopes = {"account": settings.stock_data_account, "server": settings.stock_data_server}
    visible = and_(
        generation.is_active,
        generation.published_at <= at,
        generation.valid_until > at,
        generation.mode.in_(("live", "fixture") if settings.env == "test" else ("live",)),
        listing.c.state == "active",
        listing.c.valid_until > at,
        listing.c.classification.in_(("common_stock", "ordinary_shares")),
        _permitted_listing(at, generation.mode == "fixture"),
    )
    display_until = func.least(
        generation.valid_until,
        listing.c.valid_until,
        case((generation.mode == "live", directory.c.valid_until)),
        case((generation.mode == "live", name.c.valid_until)),
        case((generation.mode == "live", classification.c.valid_until)),
    )
    alias = StockCatalogAlias
    alias_until = (
        select(func.max(alias.valid_until))
        .where(
            alias.listing_id == listing.c.id,
            alias.security_id == binding.c.catalog_id,
            alias.namespace != "former",
            alias.symbol == listing.c.provider_symbol,
            alias.verified_at <= at,
            alias.valid_until > at,
        )
        .correlate(binding, listing)
        .scalar_subquery()
    )
    held, missing = action_hold_queries(binding.c.coin_id)
    event, revision, split = StockActionEvent, StockActionRevision, StockSplitApplication
    due = exists(
        select(event.id)
        .join(revision, revision.id == event.current_revision_id)
        .where(
            event.coin_id == binding.c.coin_id,
            revision.classification == "supported_forward_split",
            revision.verified_cutoff <= at,
            ~exists(select(split.id).where(split.economic_event_id == event.id).correlate(event)),
        )
        .correlate(binding)
    )
    changed = exists(
        select(split.id)
        .join(event, event.id == split.economic_event_id)
        .where(
            split.coin_id == binding.c.coin_id,
            split.revision_id != event.current_revision_id,
        )
        .correlate(binding)
    )
    units_attested = and_(
        coverage.catalog_id == binding.c.catalog_id,
        coverage.listing_id == binding.c.listing_id,
        coverage.journal_origin == action.c.journal_start_at,
        coverage.journal_origin >= binding.c.promoted_at,
        coverage.coverage_start == action.c.coverage_start,
        coverage.covered_until == action.c.covered_until,
        coverage.observed_at == action.c.checked_at,
        coverage.valid_until == action.c.valid_until,
        coverage.admission_id == action.c.admission_generation,
        coverage.cursor.is_not_distinct_from(action.c.cursor),
        coverage.coverage_start <= coverage.journal_origin,
        coverage.journal_origin <= coverage.covered_until,
        coverage.covered_until <= at,
        action.c.complete_from <= coverage.covered_until,
        actions.c.scope.contains(scopes),
        func.public.stock_catalog_scope_current(
            actions.c.id,
            "catalog_actions",
            binding.table_valued(),
            listing.table_valued(),
            at,
            cast(CATALOG_ACTION_FIELDS, JSONB),
        ),
        ~exists(held.correlate(binding)),
        ~exists(missing.correlate(binding)),
        ~due,
        ~changed,
    )
    quote_attested = and_(
        quote.c.catalog_id == binding.c.catalog_id,
        quote.c.listing_id == binding.c.listing_id,
        quote.c.provider_asset_id == listing.c.provider_asset_id,
        quote.c.provider_admission_id == listing.c.provider_admission_id,
        instrument.provider_asset_id == listing.c.provider_asset_id,
        instrument.provider_verified_at == listing.c.provider_verified_at,
        instrument.listing_exchange == listing.c.listing_exchange,
        mark.c.scope.contains(scopes),
        mark.c.reviewed_at <= quote.c.collected_at,
        func.public.stock_catalog_scope_current(
            mark.c.id,
            "catalog_mark",
            binding.table_valued(),
            listing.table_valued(),
            at,
            cast(_MARK_FIELDS, JSONB),
        ),
    )
    halt_attested = and_(
        status.c.catalog_id == binding.c.catalog_id,
        status.c.listing_id == binding.c.listing_id,
        status.c.state == "halted",
        status.c.event_at <= at,
        status.c.observed_at <= at,
        status.c.valid_until > at,
        halt.c.scope.contains(scopes),
        func.public.stock_catalog_scope_current(
            halt.c.id,
            "catalog_halt",
            binding.table_valued(),
            listing.table_valued(),
            at,
            cast(
                {
                    key: ["collection", "execution", "storage", "backup"]
                    for key in ("report_digest", "event_at", "valid_until", "state")
                },
                JSONB,
            ),
        ),
    )
    rows = (
        select(
            binding.c.coin_id,
            binding.c.catalog_id,
            binding.c.listing_id,
            visible.label("visible"),
            display_until.label("display_until"),
            func.to_jsonb(listing.table_valued()).label("listing"),
            func.to_jsonb(quote.table_valued())
            .op("||")(
                func.jsonb_build_object(
                    "bid", cast(quote.c.bid, Text), "ask", cast(quote.c.ask, Text)
                )
            )
            .label("quote"),
            func.jsonb_build_object(
                "epoch",
                action.c.epoch,
                "unit_epoch",
                action.c.unit_epoch,
                "admission_generation",
                action.c.admission_generation,
                "health",
                action.c.health,
                "checked_at",
                action.c.checked_at,
                "valid_until",
                action.c.valid_until,
                "next_blocking_at",
                action.c.next_blocking_at,
                "quote_not_before",
                action.c.quote_not_before,
            ).label("action"),
            units_attested.label("units_attested"),
            quote_attested.label("quote_attested"),
            case(
                (
                    halt_attested,
                    func.jsonb_build_object(
                        "session_date",
                        status.c.session_date,
                        "valid_until",
                        func.least(status.c.valid_until, halt.c.valid_until),
                    ),
                )
            ).label("halt"),
            actions.c.valid_until.label("action_review_until"),
            mark.c.id.label("mark_id"),
            mark.c.reviewed_at.label("mark_reviewed"),
            mark.c.valid_until.label("mark_until"),
            mark.c.fields.label("mark_fields"),
            mark.c.scope.label("mark_scope"),
            mapping.c.reviewed_at.label("mapping_reviewed"),
            mapping.c.valid_until.label("mapping_until"),
            mapping.c.scope.label("mapping_scope"),
            alias_until.label("alias_until"),
        )
        .select_from(binding)
        .join(
            listing,
            and_(
                listing.c.id == binding.c.listing_id, listing.c.security_id == binding.c.catalog_id
            ),
        )
        .join(generation, generation.id == listing.c.generation_id)
        .join(instrument, instrument.coin_id == binding.c.coin_id)
        .outerjoin(quote, quote.c.coin_id == binding.c.coin_id)
        .outerjoin(action, action.c.coin_id == binding.c.coin_id)
        .outerjoin(coverage, coverage.coin_id == binding.c.coin_id)
        .outerjoin(status, status.c.coin_id == binding.c.coin_id)
        .outerjoin(halt, halt.c.id == status.c.admission_id)
        .outerjoin(mark, mark.c.id == quote.c.mark_admission_id)
        .outerjoin(mapping, mapping.c.id == listing.c.provider_admission_id)
        .outerjoin(actions, actions.c.id == coverage.admission_id)
        .outerjoin(directory, directory.c.id == listing.c.directory_admission_id)
        .outerjoin(name, name.c.id == listing.c.name_admission_id)
        .outerjoin(classification, classification.c.id == listing.c.classification_admission_id)
        .where(binding.c.coin_id.in_(coin_ids))
        .subquery()
    )
    return select(func.jsonb_agg(func.to_jsonb(rows.table_valued()))).scalar_subquery()


@dataclass(frozen=True)
class CatalogHoldingValuation:
    catalog_id: str
    symbol: str
    name: str
    exchange: Literal["NYSE", "NASDAQ"] | None
    value: StockValuation


def _catalog_stamp(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _visible_catalog_label(row: dict[str, Any], now: datetime) -> bool:
    until = _catalog_stamp(row["display_until"])
    return row["visible"] is True and until is not None and now < until


CatalogSessions = dict[str, tuple[SessionDecision, RegularSession | None]]


def catalog_valuation_sessions(
    raw: Any, settings: MarketValuationSettings, now: datetime
) -> CatalogSessions:
    """Resolve both reviewed venues once per authoritative snapshot."""
    calendar = admission_rows(raw.admissions or []).get("calendar")
    sessions = session_rows(raw.sessions or [])
    return {
        exchange: catalog_mark_sessions(
            calendar,
            sessions,
            exchange,
            now,
            account=settings.stock_data_account,
            server=settings.stock_data_server,
        )
        for exchange in ("NYSE", "NASDAQ")
    }


def _catalog_mark_snapshot(
    row: dict[str, Any],
    action: StockActionState,
    sessions: CatalogSessions,
    settings: MarketValuationSettings,
    now: datetime,
    *,
    halt: dict[str, str] | None,
) -> StockValuation:
    def unavailable(reason: RefusalReason) -> StockValuation:
        return StockValuation(None, StockMark(valuation_reason=reason, units_safe=True))

    if not _visible_catalog_label(row, now) or row["quote_attested"] is not True:
        return unavailable("permission_unavailable" if row["quote"] else "quote_unavailable")
    quote_dates = (
        "event_at",
        "collected_at",
        "observed_at",
        "opens_at",
        "closes_at",
        "valid_until",
    )
    quote_data = row["quote"]
    quote = StockCatalogFinancialQuote(
        **{
            **quote_data,
            **{key: _catalog_stamp(quote_data[key]) for key in quote_dates},
            "session_date": date.fromisoformat(quote_data["session_date"]),
            "bid": Decimal(quote_data["bid"]),
            "ask": Decimal(quote_data["ask"]),
        }
    )
    if action.unit_epoch != quote.unit_epoch or (
        action.quote_not_before is not None and quote.event_at < action.quote_not_before
    ):
        return StockValuation(None, StockMark(valuation_reason="units_changed"))

    listing_dates = (
        "provider_verified_at",
        "provider_valid_until",
        "valid_until",
        "unit_evidence_at",
    )
    listing_data = row["listing"]
    listing = StockCatalogListing(
        **{
            **listing_data,
            **{key: _catalog_stamp(listing_data[key]) for key in listing_dates},
        }
    )
    reviewed = _catalog_stamp(row["mapping_reviewed"])
    mapping_until = _catalog_stamp(row["mapping_until"])
    mark_until = _catalog_stamp(row["mark_until"])
    display_until = _catalog_stamp(row["display_until"])
    action_until = _catalog_stamp(row["action_review_until"])
    if any(v is None or now >= v for v in (mapping_until, mark_until, display_until, action_until)):
        return unavailable("permission_unavailable")
    if reviewed is None or mapping_until is None or row["mapping_scope"] is None:
        return unavailable("permission_unavailable")
    scope = {"account": settings.stock_data_account, "server": settings.stock_data_server}
    mapping = validate_catalog_asset_mapping(
        listing,
        now,
        reviewed_at=reviewed,
        valid_until=mapping_until,
        scope=row["mapping_scope"],
        alias_until=_catalog_stamp(row["alias_until"]),
        **scope,
    )
    if mapping is None or mark_until is None or display_until is None or action_until is None:
        return unavailable("permission_unavailable")
    decision, previous = sessions[listing.listing_exchange]
    if decision.state == "unknown":
        return unavailable("session_unavailable")
    halted_until = (
        _catalog_stamp(halt["valid_until"])
        if halt is not None
        and decision.current is not None
        and decision.current.session_date.isoformat() == halt["session_date"]
        else None
    )
    mark = evaluate_catalog_financial_mark(
        quote,
        action,
        listing.listing_exchange,
        now,
        permission_until=min(mapping[1], mark_until, display_until, action_until),
        decision=decision,
        previous=previous,
        halted_until=halted_until,
    )
    if mark is None:
        return unavailable("quote_stale" if now >= quote.valid_until else "quote_unavailable")
    return StockValuation(
        mark.mid,
        StockMark(
            mark_mode=mark.mode,
            valuation_reason="available",
            source="alpaca",
            feed="iex",
            event_at=mark.event_at,
            collected_at=mark.collected_at,
            historical_admission_until=quote.valid_until,
            retained_until=quote.valid_until,
            valid_until=mark.valid_until,
            units_safe=True,
        ),
        daily_aggregate_allowed=_daily_aggregate_allowed(row["mark_scope"]),
    )


def _scoped_action_state(row: dict[str, Any], now: datetime) -> StockActionState | None:
    until = _catalog_stamp(row["action_review_until"])
    if row["units_attested"] is not True or until is None or now >= until:
        return None
    state = row["action"]
    dates = ("checked_at", "valid_until", "next_blocking_at", "quote_not_before")
    action = StockActionState(**{**state, **{key: _catalog_stamp(state[key]) for key in dates}})
    return action if catalog_mark_units_safe(action, now) else None


def value_catalog_holding(
    original: dict[str, Any],
    current: dict[str, Any] | None,
    *,
    original_sessions: CatalogSessions,
    current_sessions: CatalogSessions,
    settings: MarketValuationSettings,
    now: datetime,
    allow_mark: bool = True,
) -> CatalogHoldingValuation:
    """Value the original owned quote with current scope and unchanged unit evidence."""
    catalog_id = str(original["catalog_id"])
    listing = (
        current["listing"]
        if current
        and current["catalog_id"] == original["catalog_id"]
        and _visible_catalog_label(current, now)
        else None
    )
    label: tuple[str, str, Literal["NYSE", "NASDAQ"] | None] = (
        (listing["ticker"], listing["company_name"], listing["listing_exchange"])
        if listing
        else ("STOCK", "Restricted stock", None)
    )

    def holding(value: StockValuation) -> CatalogHoldingValuation:
        return CatalogHoldingValuation(catalog_id, *label, value)

    if (
        not allow_mark
        or current is None
        or current["catalog_id"] != original["catalog_id"]
        or current["listing_id"] != original["listing_id"]
    ):
        return holding(StockValuation(None, StockMark()))
    before, after = _scoped_action_state(original, now), _scoped_action_state(current, now)
    if (
        before is None
        or after is None
        or before.epoch != after.epoch
        or (before.admission_generation != after.admission_generation)
    ):
        return holding(StockValuation(None, StockMark(valuation_reason="action_unavailable")))
    if before.unit_epoch != after.unit_epoch:
        return holding(StockValuation(None, StockMark(valuation_reason="units_changed")))
    # Renewal can narrow the original rights, but cannot authorize a price
    # from a different review or provider mapping.
    keys = (
        "mark_id",
        "mark_reviewed",
        "mark_fields",
        "mark_scope",
        "mapping_reviewed",
        "mapping_scope",
    )
    if any(original[key] != current[key] for key in keys):
        return holding(StockValuation(None, StockMark(units_safe=True)))
    first_quote, latest_quote = original["quote"], current["quote"]
    session_keys = ("session_date", "opens_at", "closes_at", "calendar_generation")
    if (
        first_quote
        and latest_quote
        and any(first_quote[key] != latest_quote[key] for key in session_keys)
    ):
        return holding(
            StockValuation(
                None,
                StockMark(
                    valuation_reason="session_unavailable",
                    units_safe=True,
                ),
            )
        )
    # The second snapshot can report a halt after the financial read. Keep
    # the source price and recheck its deadline with the latest halt.
    halt = current["halt"]
    value = _catalog_mark_snapshot(original, before, original_sessions, settings, now, halt=halt)
    if value.mid is None:
        return holding(value)
    latest = _catalog_mark_snapshot(current, after, current_sessions, settings, now, halt=halt)
    if latest.mid is None:
        return holding(latest)
    if value.mark.valid_until is None or latest.mark.valid_until is None:
        return holding(StockValuation(None, StockMark(units_safe=True)))
    return holding(
        replace(
            value,
            mark=replace(
                value.mark,
                valid_until=min(value.mark.valid_until, latest.mark.valid_until),
            ),
        )
    )


def _action(loaded: LoadedExecution, raw: Any) -> ExecutionEvidence:
    """Consumed exact applied split markers cannot invalidate compatible display."""
    e = loaded.evidence
    row: dict[str, Any] = next((a for a in raw.actions or [] if a["coin_id"] == e.coin_id), {})
    cached, split, applied = (
        row.get(k) for k in ("next_blocking_at", "split_boundary", "quote_not_before")
    )
    if cached is not None and split is not None and split == applied and cached <= split:
        pending = row.get("pending_boundary")
        return replace(e, next_blocking_at=datetime.fromisoformat(pending) if pending else None)
    return e


def _units_safe(e: ExecutionEvidence, now: datetime) -> bool:
    admissions = [a for a in e.admissions if a.product in ("actions", "reference", "calendar")]
    return bool(
        len(admissions) == 3
        and e.action_current
        and e.action_valid_until is not None
        and now < e.action_valid_until
        and (e.next_blocking_at is None or now < e.next_blocking_at)
        and all(a.approved and now < a.valid_until for a in admissions)
    )


def value_stock(
    snapshot: LoadedExecution | None,
    current: LoadedExecution | None,
    *,
    raw: Any,
    current_raw: Any,
    proof: dict[str, Any] | None,
    now: datetime,
) -> StockValuation:
    def denied(reason: RefusalReason, *, units: bool = False) -> StockValuation:
        return StockValuation(None, StockMark(valuation_reason=reason, units_safe=units))

    if snapshot is None or current is None:
        return denied("permission_unavailable")
    e, latest = _action(snapshot, raw), _action(current, current_raw)
    if e.provider_asset_id != latest.provider_asset_id:
        return denied("permission_unavailable")
    if e.unit_epoch != latest.unit_epoch:
        return denied("units_changed")
    if e.safety_epoch != latest.safety_epoch:
        return denied("action_unavailable")
    if e.admissions != latest.admissions:
        return denied("permission_unavailable")
    # Renewed observations may suppress old prices or turn them into dated halt
    # marks, never renew the old snapshot's authority deadline or source price.
    units = _units_safe(e, now) and _units_safe(latest, now)
    status = latest.status
    closed_reported = (
        latest.session_state == "closed"
        and e.status.source == status.source == REPORTED_HALT_SOURCE
    )
    if not closed_reported:
        if (
            e.status.continuity_generation != status.continuity_generation
            or e.status.valid_until is None
            or status.valid_until is None
        ):
            return denied("status_unavailable", units=units)
        status = replace(status, valid_until=min(e.status.valid_until, status.valid_until))
    if e.action_valid_until is None or latest.action_valid_until is None:
        return denied("action_unavailable")
    if e.session_valid_until is None or latest.session_valid_until is None:
        return denied("session_unavailable")
    e = replace(
        e,
        status=status,
        action_current=e.action_current and latest.action_current,
        action_valid_until=min(e.action_valid_until, latest.action_valid_until),
        session_state=latest.session_state,
        session_date=latest.session_date,
        opens_at=latest.opens_at,
        closes_at=latest.closes_at,
        session_valid_until=min(e.session_valid_until, latest.session_valid_until),
        next_blocking_at=min(
            (v for v in (e.next_blocking_at, latest.next_blocking_at) if v is not None),
            default=None,
        ),
    )
    units = _units_safe(e, now)
    if proof is None:
        return denied("permission_unavailable", units=units)
    try:
        quote_admission = next(a for a in e.admissions if a.product == "quotes")
        original = next(a for a in proof["admissions"] if a["product"] == "quotes")
        original_until = datetime.fromisoformat(original["valid_until"])
        original_from = datetime.fromisoformat(original["valid_from"])
        if (
            proof["provider_asset_id"] != e.provider_asset_id
            or original["generation"] != e.quote.admission_generation
            or original["row_hash"] != quote_admission.row_hash
            or e.quote.collected_at is None
            or not original_from <= e.quote.collected_at < original_until
        ):
            return denied("permission_unavailable", units=units)
        source_session = next(
            s
            for s in session_rows(raw.sessions or [])
            if s.exchange == snapshot.listing_exchange and s.session_date == e.quote.session_date
        )
        if (
            source_session.opens_at is None
            or source_session.closes_at is None
            or e.quote.event_at is None
            or not source_session.opens_at <= e.quote.event_at < source_session.closes_at
        ):
            return denied("quote_unavailable", units=units)
    except KeyError, TypeError, ValueError, StopIteration:
        return denied("permission_unavailable", units=units)
    decision = evaluate_valuation(
        ValuationEvidence(e, snapshot.quote_retained_until, original_until), now
    )
    if decision.mode == "unavailable":
        return denied(decision.reason, units=units)
    quote_scope = admission_rows(raw.admissions or [])["quotes"].scope
    return StockValuation(
        decision.mid,
        StockMark(
            mark_mode=decision.mode,
            valuation_reason=decision.reason,
            source="alpaca",
            feed="iex",
            event_at=e.quote.event_at,
            collected_at=e.quote.collected_at,
            historical_admission_until=original_until,
            retained_until=snapshot.quote_retained_until,
            valid_until=decision.valid_until,
            authority=_authority(replace(snapshot, evidence=e)),
            units_safe=units,
        ),
        daily_aggregate_allowed=_daily_aggregate_allowed(quote_scope),
    )
