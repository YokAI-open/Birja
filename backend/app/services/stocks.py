"""Authenticated discovery projection; no provider requests or execution."""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument, StockQuote, StockSession
from app.schemas.stocks import (
    StockAdmission,
    StockAttribution,
    StockItem,
    StockQuoteOut,
    StockSessionOut,
    StocksResponse,
)
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
    try:
        final = (
            await db.execute(
                select(
                    _json_rows(StockDataAdmission, 6).label("admissions"),
                    _json_rows(StockSession, 273, staged_at).label("sessions"),
                    func.current_setting("transaction_isolation").label("isolation"),
                ).execution_options(stock_final_evidence=True)
            )
        ).one()
        if final.isolation == "read committed" and len(final.admissions or []) <= 5:
            authority = _admissions(final.admissions or [])
            sessions = _sessions(final.sessions or [])
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
        quote = None
        reason = "permission_unavailable"
        if permitted:
            reason = "missing"
            if row.quote_coin_id is not None:
                fields = {
                    column.name: row["quote_" + column.name]
                    for column in StockQuote.__table__.columns
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
