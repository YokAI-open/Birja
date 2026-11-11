"""Authenticated discovery projection; no provider requests or execution."""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

from sqlalchemy import case, exists, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.corporate_action import (
    StockActionEvent,
    StockActionRevision,
    StockActionState,
    StockSplitApplication,
)
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument, StockQuote, StockSession
from app.schemas.stocks import (
    StockActionOut,
    StockAdmission,
    StockAttribution,
    StockItem,
    StockQuoteOut,
    StockSessionOut,
    StocksResponse,
)
from app.services.corporate_actions import action_hold_queries
from app.services.stock_action_rules import evaluate_action_state
from app.services.stock_admission import ProductAdmission, evaluate_admission
from app.services.stock_quote_rules import CURATED_SYMBOLS, ValidatedStockQuote, quote_eligibility
from app.services.stock_sessions import RegularSession, load_sessions, session_at


def _now() -> datetime:
    return datetime.now(UTC)


def _json_rows(model: Any, maximum: int, anchor: datetime | None = None) -> Any:
    query = select(model.__table__).order_by(*model.__table__.primary_key.columns)
    if model is StockSession and anchor is not None:
        query = query.where(
            StockSession.session_date >= anchor.date() - timedelta(days=45),
            StockSession.session_date <= anchor.date() + timedelta(days=90),
        )
    bounded = query.limit(maximum).subquery()
    return select(func.jsonb_agg(func.to_jsonb(bounded.table_valued()))).scalar_subquery()


def _admissions(rows: list[dict[str, Any]]) -> dict[str, ProductAdmission]:
    result = {}
    for row in rows:
        row = {key: value for key, value in row.items() if key != "id"}
        for key in ("reviewed_at", "valid_from", "valid_until"):
            if row[key] is not None:
                row[key] = datetime.fromisoformat(row[key])
        item = ProductAdmission(**row)
        result[item.product] = item
    return result


def _sessions(rows: list[dict[str, Any]]) -> list[RegularSession]:
    result = []
    for row in rows:
        row = {key: value for key, value in row.items() if key != "id"}
        for key in ("session_date", "coverage_start", "coverage_end"):
            row[key] = date.fromisoformat(row[key])
        for key in ("opens_at", "closes_at"):
            if row[key] is not None:
                row[key] = datetime.fromisoformat(row[key])
        result.append(RegularSession(**row))
    return result


def _action_rows() -> Any:
    """Twenty fixed-size authority facts; no event/audit payload crosses to Python."""
    state = StockActionState.__table__
    held, missing = action_hold_queries(Coin.id)
    held = held.correlate(Coin)
    missing = missing.correlate(Coin)
    safe_reason = case(
        *(
            (exists(held.where(StockActionRevision.reason == reason)), reason)
            for reason in ("unsupported", "fractional", "conflicting", "identity_change")
        ),
        (exists(held), "conflicting"),
        (exists(missing), "source_gap"),
        else_=None,
    )
    applied = StockSplitApplication
    event = StockActionEvent
    revision = StockActionRevision
    boundary = (
        select(applied.cutoff)
        .where(applied.coin_id == Coin.id, applied.new_unit_epoch == state.c.unit_epoch)
        .order_by(applied.id.desc())
        .limit(1)
        .correlate(Coin, state)
        .scalar_subquery()
    )
    changed_split = exists(
        select(applied.id)
        .join(event, event.id == applied.economic_event_id)
        .where(applied.coin_id == Coin.id, applied.revision_id != event.current_revision_id)
        .correlate(Coin)
    )
    pending_boundary = (
        select(func.min(revision.verified_cutoff))
        .join(event, event.current_revision_id == revision.id)
        .where(
            event.coin_id == Coin.id,
            revision.classification == "supported_forward_split",
            ~exists(
                select(applied.id).where(applied.economic_event_id == event.id).correlate(event)
            ),
        )
        .correlate(Coin)
        .scalar_subquery()
    )
    query = (
        select(
            Coin.id.label("coin_id"),
            *(
                state.c[name]
                for name in (
                    "epoch",
                    "unit_epoch",
                    "health",
                    "checked_at",
                    "valid_until",
                    "admission_generation",
                    "coverage_start",
                    "covered_until",
                    "quote_not_before",
                    "next_blocking_at",
                )
            ),
            safe_reason.label("hold"),
            boundary.label("split_boundary"),
            changed_split.label("changed_split"),
            pending_boundary.label("pending_boundary"),
        )
        .outerjoin(state, state.c.coin_id == Coin.id)
        .where(Coin.asset_class == "stock", Coin.is_active, Coin.symbol.in_(CURATED_SYMBOLS))
        .order_by(Coin.sort_order, Coin.id)
        .limit(20)
        .subquery()
    )
    return select(func.jsonb_agg(func.to_jsonb(query.table_valued()))).scalar_subquery()


def _action_projection(
    raw: dict[str, Any] | None,
    admission: ProductAdmission | None,
    calendar_deadline: datetime | None,
    checked_at: datetime,
    scope: dict[str, Any],
    quote_epoch: int | None,
    quote_event_at: datetime | None,
) -> tuple[StockActionOut, bool]:
    rights = all(
        evaluate_admission(
            admission, "actions", purpose, checked_at, feed="alpaca-corporate-actions", **scope
        ).allowed
        for purpose in ("collection", "display", "derived", "retention")
    )
    if not rights or raw is None:
        return StockActionOut(), False
    try:
        row = dict(raw)
        for key in (
            "checked_at",
            "valid_until",
            "coverage_start",
            "covered_until",
            "quote_not_before",
            "next_blocking_at",
            "split_boundary",
            "pending_boundary",
        ):
            row[key] = datetime.fromisoformat(row[key]) if row[key] is not None else None
        epoch, units = row["epoch"], row["unit_epoch"]
        if type(epoch) is not int or not 1 <= epoch <= 9007199254740991:
            return StockActionOut(), False
        rights = (
            rights and row["admission_generation"] == cast(ProductAdmission, admission).generation
        )
        deadlines = [
            row["valid_until"],
            calendar_deadline,
            cast(ProductAdmission, admission).valid_until,
        ]
        validity = min(deadlines) if all(value is not None for value in deadlines) else None
        boundaries = [
            value
            for value in (row["next_blocking_at"], row["pending_boundary"])
            if value is not None
        ]
        decision = evaluate_action_state(
            now=checked_at,
            health=row["health"],
            rights_current=rights,
            coverage_complete=(
                row["coverage_start"] is not None
                and row["covered_until"] is not None
                and row["coverage_start"] <= row["covered_until"] <= checked_at
                and row["checked_at"] is not None
                and row["checked_at"] <= checked_at
            ),
            valid_until=validity,
            persistent_holds=(row["hold"],) if row["hold"] else (),
            unresolved_revision=row["changed_split"],
            known_boundary=min(boundaries) if boundaries else None,
            unit_epoch=units,
            quote_unit_epoch=quote_epoch if quote_epoch is not None else units,
            split_boundary=(
                row["split_boundary"] if row["split_boundary"] == row["quote_not_before"] else None
            ),
            quote_event_at=quote_event_at,
        )
        # A past authority snapshot is not renewed by serving a response.
        return StockActionOut(
            state=decision.state,
            reason=cast(Any, decision.reason),
            epoch=epoch,
            checked_at=row["checked_at"],
            valid_until=decision.valid_until,
        ), decision.valuation_allowed
    except TypeError, ValueError, KeyError:
        return StockActionOut(), False


async def list_stocks(
    db: AsyncSession, settings: Settings, *, now: Callable[[], datetime] | None = None
) -> StocksResponse:
    """Three bounded reads; only the final committed evidence snapshot authorizes.

    Core column projections bypass identity-map snapshots. READ COMMITTED is
    checked in the final statement, so an accidental repeatable-read caller
    cannot expose a quote using stale permission. Nothing awaits after that
    statement: UTC evaluation, projection and the router return are synchronous.
    The boundary cannot predict changes committed after its statement snapshot.
    """
    now = now or _now
    quote_columns = [
        column.label("quote_" + column.name) for column in StockQuote.__table__.columns
    ]
    catalogue = (
        (
            await db.execute(
                select(
                    Coin.id,
                    Coin.symbol,
                    Coin.name,
                    StockInstrument.listing_exchange,
                    *quote_columns,
                )
                .join(StockInstrument, StockInstrument.coin_id == Coin.id)
                .outerjoin(StockQuote, StockQuote.coin_id == Coin.id)
                .where(
                    Coin.asset_class == "stock",
                    Coin.is_active,
                    Coin.symbol.in_(CURATED_SYMBOLS),
                    StockInstrument.source == "sec",
                    StockInstrument.source_ref
                    == "https://www.sec.gov/files/company_tickers_exchange.json",
                )
                .order_by(Coin.sort_order, Coin.id)
                .limit(20)
            )
        )
        .mappings()
        .all()
    )
    # All potentially blocking preparatory reads precede the authority boundary.
    staged_at = now()
    await load_sessions(db, staged_at)
    authority: dict[str, ProductAdmission] = {}
    sessions: list[RegularSession] = []
    actions: dict[int, dict[str, Any]] = {}
    try:
        final = (
            await db.execute(
                select(
                    _json_rows(StockDataAdmission, 6).label("admissions"),
                    _json_rows(StockSession, 273, staged_at).label("sessions"),
                    _action_rows().label("actions"),
                    func.current_setting("transaction_isolation").label("isolation"),
                ).execution_options(stock_final_evidence=True)
            )
        ).one()
        if final.isolation == "read committed" and len(final.admissions or []) <= 5:
            authority = _admissions(final.admissions or [])
            sessions = _sessions(final.sessions or [])
            if len(final.actions or []) <= 20:
                actions = {row["coin_id"]: row for row in final.actions or []}
    except SQLAlchemyError, ValueError, TypeError, KeyError:
        # Safe SEC metadata survives; never return/log driver/provider evidence.
        authority = {}
        sessions = []
    checked_at = now()
    quote_authority = authority.get("quotes")
    scope: dict[str, Any] = {
        "account": settings.stock_data_account,
        "server": settings.stock_data_server,
    }
    permission = evaluate_admission(quote_authority, "quotes", "display", checked_at, **scope)
    permitted = (
        permission.allowed
        and evaluate_admission(quote_authority, "quotes", "derived", checked_at, **scope).allowed
        and evaluate_admission(quote_authority, "quotes", "retention", checked_at, **scope).allowed
    )
    # Trusted configured scope reaches every nested evaluation.
    calendar = authority.get("calendar")
    if not evaluate_admission(calendar, "calendar", "derived", checked_at, **scope).allowed:
        calendar = None
    decisions = {
        exchange: session_at(exchange, checked_at, sessions, calendar, **scope)
        for exchange in ("NYSE", "NASDAQ")
    }
    items = []
    disclosure_deadline = permission.valid_until
    for row in catalogue:
        session = decisions[row.listing_exchange]
        current = session.current
        action, action_safe = _action_projection(
            actions.get(row.id),
            authority.get("actions"),
            session.valid_until,
            checked_at,
            scope,
            row.quote_unit_epoch,
            row.quote_event_at,
        )
        quote = None
        reason = "permission_unavailable"
        if permitted and action_safe:
            reason = "missing"
            # Local accounting provenance is not a provider validation field.
            # Nonzero units need Plan09's authentic current-unit gate before
            # either a recent or historical amount can be disclosed.
            if row.quote_coin_id is not None:
                fields = {
                    name: row["quote_" + name]
                    for name in (
                        "coin_id",
                        "bid",
                        "ask",
                        "mid",
                        "source",
                        "feed",
                        "event_at",
                        "collected_at",
                        "session_date",
                        "admission_generation",
                    )
                }
                candidate = ValidatedStockQuote(symbol=row.symbol, **fields)
                matched = evaluate_admission(
                    quote_authority,
                    "quotes",
                    "display",
                    checked_at,
                    expected_generation=candidate.admission_generation,
                    **scope,
                ).allowed
                retained_until = candidate.collected_at + timedelta(
                    seconds=cast(ProductAdmission, quote_authority).quota["retention_seconds"]
                )
                matched = matched and checked_at < retained_until
                if not matched:
                    reason = "permission_unavailable"
                elif not 0 <= (checked_at - candidate.event_at).total_seconds() < 120:
                    reason = "stale"
                elif session.state != "open" or not quote_eligibility(
                    candidate, current, checked_at
                ):
                    reason = "session_unavailable"
                else:
                    reason = "recent"
                # Permission and session authority govern disclosure; freshness
                # governs the independent recent claim. The UI may show a dated
                # last quote while closed/stale, never imply a tradable price.
                if (
                    matched
                    and session.state != "unknown"
                    and candidate.event_at <= candidate.collected_at <= checked_at
                ):
                    disclosure_deadline = min(cast(datetime, disclosure_deadline), retained_until)
                    quote = StockQuoteOut(
                        bid=candidate.bid,
                        ask=candidate.ask,
                        mid=candidate.mid,
                        event_at=candidate.event_at,
                        collected_at=candidate.collected_at,
                        age_seconds=int((checked_at - candidate.event_at).total_seconds()),
                    )
        items.append(
            StockItem(
                id=row.id,
                symbol=row.symbol,
                company_name=row.name,
                listing_exchange=row.listing_exchange,
                quote=quote,
                action=action,
                valuation_reason=(
                    "available"
                    if quote is not None
                    else "post_split_quote_missing"
                    if action.reason == "post_split_quote_missing"
                    else "action_unavailable"
                    if not action_safe
                    else "quote_unavailable"
                ),
                session=StockSessionOut(
                    state=cast(Any, session.state),
                    opens_at=current.opens_at if current else None,
                    closes_at=current.closes_at if current else None,
                    next_open_at=session.next_session.opens_at if session.next_session else None,
                    valid_until=session.valid_until,
                ),
                quote_reason=cast(Any, reason),
                session_reason=cast(Any, session.state),
            )
        )
    return StocksResponse(
        server_now=checked_at,
        admission=StockAdmission(
            state="approved" if permitted else "unavailable",
            generation=permission.generation if permitted else None,
            valid_until=disclosure_deadline if permitted else None,
        ),
        attribution=StockAttribution(required_text=permission.attribution if permitted else ""),
        items=tuple(items),
    )
