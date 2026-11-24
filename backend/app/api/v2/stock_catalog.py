"""Private display and owned orders for an exact catalog issue and listing."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Response
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.stock_trades import PrivateRoute, _refusal
from app.core.config import Settings
from app.core.deps import (
    CsrfDep,
    CurrentUserDep,
    DbDep,
    OwnedActivePortfolioDep,
    RedisDep,
    SettingsDep,
)
from app.models.corporate_action import StockActionState
from app.models.stock_catalog_finance import StockCatalogInstrument
from app.schemas.stock_catalog import CatalogIdInput, StockCatalogItem
from app.schemas.stock_catalog_quotes import (
    CatalogConfirmRequest,
    CatalogFillOut,
    CatalogOrderIn,
    CatalogPreviewOut,
    CatalogPriceOut,
    CatalogQuoteIn,
    CatalogQuoteOut,
    CatalogQuoteReason,
    CatalogSessionOut,
    CatalogTradeContextOut,
)
from app.services import stock_catalog_trading
from app.services.portfolios import OwnedActivePortfolio, fence_owned_active_portfolios
from app.services.stock_catalog_financial_quotes import read_catalog_financial_mark
from app.services.stock_catalog_quote_demand import CatalogQuotePurpose, request_catalog_quote
from app.services.stock_catalog_quotes import (
    CatalogDisplayQuote,
    CatalogQuoteContext,
    catalog_quote_is_current,
    catalog_quote_valid_until,
    load_catalog_quote_context,
    read_catalog_quote,
)
from app.services.stock_catalog_search import catalog_item
from app.services.trade_math import TradeRefused

router = APIRouter(tags=["stock catalog quotes"], route_class=PrivateRoute)
CatalogPath = Annotated[CatalogIdInput, Path()]


def _listing_changed() -> HTTPException:
    return HTTPException(409, detail={"code": "listing_changed"})


async def _read_context(
    db: AsyncSession,
    settings: Settings,
    catalog_id: int,
    expected_version: int | None = None,
) -> tuple[CatalogQuoteContext, StockCatalogItem]:
    context = await load_catalog_quote_context(db, settings, catalog_id, now=datetime.now(UTC))
    if context.listing is None:
        raise HTTPException(404, detail={"code": "stock_catalog_not_found"})
    listing = catalog_item(context.listing)
    if expected_version is not None and listing.listing_version != expected_version:
        raise _listing_changed()
    return context, listing


async def _cache_action_deadline(
    db: AsyncSession,
    listing: StockCatalogItem,
    quote: CatalogDisplayQuote,
    quote_deadline: datetime,
    now: datetime,
) -> datetime | None:
    row = (
        (
            await db.execute(
                select(
                    StockCatalogInstrument.listing_id,
                    StockActionState.health,
                    StockActionState.unit_epoch,
                    StockActionState.checked_at,
                    StockActionState.valid_until,
                    StockActionState.quote_not_before,
                    StockActionState.next_blocking_at,
                )
                .outerjoin(
                    StockActionState, StockActionState.coin_id == StockCatalogInstrument.coin_id
                )
                .where(StockCatalogInstrument.catalog_id == listing.catalog_id)
            )
        )
        .tuples()
        .one_or_none()
    )
    if row is None:
        return quote_deadline
    version, health, units, observed_at, valid_until, cutoff, next_block = row
    if not (
        version == listing.listing_version
        and health == "current"
        and observed_at is not None
        and valid_until is not None
        and observed_at <= now < valid_until
        and (quote.event_at > cutoff if cutoff is not None else units == 0)
    ):
        return None
    return min(quote_deadline, valid_until, next_block or quote_deadline)


async def _present(
    db: AsyncSession,
    redis: Redis,
    settings: Settings,
    context: CatalogQuoteContext,
    listing: StockCatalogItem,
    *,
    fallback: CatalogQuoteReason = CatalogQuoteReason.QUOTE_UNAVAILABLE,
    portfolio: OwnedActivePortfolio | None = None,
) -> tuple[CatalogQuoteContext, stock_catalog_trading.CatalogExecution, CatalogQuoteOut]:
    binding = context.binding
    quote = None
    if binding is not None:
        await db.rollback()
        quote = await read_catalog_quote(
            redis,
            context,
            account=settings.stock_data_account,
            server=settings.stock_data_server,
            now=datetime.now(UTC),
        )
    if portfolio is not None:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    if portfolio is not None or binding is not None:
        # Recheck the listing even with cold Redis or after waiting for the
        # final ownership read. The ticker alone cannot authorize a refresh.
        context, listing = await _read_context(
            db, settings, listing.catalog_id, listing.listing_version
        )

    now = datetime.now(UTC)
    execution = await stock_catalog_trading.load_catalog_execution(
        db, settings, listing.catalog_id, listing.listing_version, now, portfolio=portfolio
    )
    if execution.version_changed:
        raise _listing_changed()
    state: Literal["open", "closed", "unknown"] = "unknown"
    if context.session.state == "open":
        state = "open"
    elif context.session.state == "closed":
        state = "closed"
    durable = None
    if settings.stock_data_enabled and state != "unknown":
        durable = await read_catalog_financial_mark(
            db,
            listing.catalog_id,
            listing.listing_version,
            now,
            allow_fixture=settings.env == "test",
            account=settings.stock_data_account,
            server=settings.stock_data_server,
        )
    price = None
    if (
        quote is not None
        and binding is not None
        and context.binding is not None
        and context.binding.fingerprint == binding.fingerprint
        and catalog_quote_is_current(quote, context, now=now)
    ):
        deadline = await _cache_action_deadline(
            db, listing, quote, catalog_quote_valid_until(quote, context.binding), now
        )
        if deadline is not None and now < deadline:
            price = CatalogPriceOut(
                bid=quote.bid,
                ask=quote.ask,
                mid=quote.mid,
                event_at=quote.event_at,
                collected_at=quote.collected_at,
                valid_until=deadline,
            )
    if (
        durable is not None
        and durable.mode == ("fresh" if state == "open" else "closed")
        and (
            price is None
            or (durable.event_at, durable.collected_at) >= (price.event_at, price.collected_at)
        )
    ):
        price = CatalogPriceOut(
            bid=durable.bid,
            ask=durable.ask,
            mid=durable.mid,
            event_at=durable.event_at,
            collected_at=durable.collected_at,
            valid_until=durable.valid_until,
        )

    session = context.session
    reason = CatalogQuoteReason(context.reason)
    if price is not None and datetime.now(UTC) >= price.valid_until:
        price = None
    if price is not None:
        reason = CatalogQuoteReason.MARKET_CLOSED if state == "closed" else CatalogQuoteReason.READY
    elif reason == CatalogQuoteReason.READY:
        reason = fallback
    execution_reason = "market_closed" if state == "closed" else execution.reason
    return (
        context,
        execution,
        CatalogQuoteOut(
            listing=listing,
            session=CatalogSessionOut(
                state=state,
                opens_at=session.current.opens_at if session.current else None,
                closes_at=session.current.closes_at if session.current else None,
                next_open_at=session.next_session.opens_at if session.next_session else None,
            ),
            quote=price,
            reason=reason,
            read_only=execution_reason != "available",
            execution_reason=execution_reason,
        ),
    )


@router.post(
    "/stock-catalog/{catalog_id}/quote",
    response_model=CatalogQuoteOut,
    summary="Request a selected listing's display price",
    description="Requests one admitted listing version and returns a display price or reason.",
)
async def post_catalog_quote(
    catalog_id: CatalogPath,
    body: CatalogQuoteIn,
    user: CurrentUserDep,
    csrf: CsrfDep,
    db: DbDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> CatalogQuoteOut:
    context, listing = await _read_context(db, settings, catalog_id, body.listing_version)
    context, execution, view = await _present(db, redis, settings, context, listing)
    financial = execution.financial
    purpose: CatalogQuotePurpose
    if (
        view.session.state == "open"
        # The halt worker starts tracking a selected issue when it sees a
        # financial request or its stored quote. Missing status still blocks orders.
        and execution.reason
        in {"quote_unavailable", "quote_stale", "status_unavailable", "units_changed"}
        and financial is not None
    ):
        purpose, fingerprint = "financial", financial.fingerprint
    elif view.quote is None and context.reason == "ready" and context.binding is not None:
        purpose, fingerprint = "display", context.binding.fingerprint
    else:
        return view

    # Return the DB connection before waiting. A display result never
    # authorizes an order on the financial lane.
    await db.rollback()
    result = await request_catalog_quote(
        redis,
        account=settings.stock_data_account,
        server=settings.stock_data_server,
        catalog_id=catalog_id,
        listing_version=body.listing_version,
        fingerprint=fingerprint,
        purpose=purpose,
    )
    context, listing = await _read_context(db, settings, catalog_id, body.listing_version)
    fallback = (
        CatalogQuoteReason.QUOTE_UNAVAILABLE if result == "ready" else CatalogQuoteReason(result)
    )
    context, execution, view = await _present(
        db, redis, settings, context, listing, fallback=fallback
    )
    current = execution.financial if purpose == "financial" else context.binding
    if current is not None and current.fingerprint != fingerprint:
        raise _listing_changed()
    if view.reason == CatalogQuoteReason.QUEUE_FULL:
        raise HTTPException(503, detail={"code": "queue_full"}, headers={"Retry-After": "5"})
    return view


@router.get(
    "/portfolios/{portfolio_id}/stock-catalog/{catalog_id}/trade-context",
    response_model=CatalogTradeContextOut,
    summary="Read an owned portfolio's catalog trade context",
    description="Current listing, price and exact amounts for the active owned portfolio.",
)
async def get_catalog_trade_context(
    catalog_id: CatalogPath,
    portfolio: OwnedActivePortfolioDep,
    db: DbDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> CatalogTradeContextOut:
    context, listing = await _read_context(db, settings, catalog_id)
    _, execution, view = await _present(db, redis, settings, context, listing, portfolio=portfolio)
    draft = await stock_catalog_trading.draft(db, portfolio=portfolio, loaded=execution)
    return CatalogTradeContextOut(
        **view.model_dump(),
        portfolio_id=portfolio.portfolio_id,
        cash=draft.cash,
        held_quantity=draft.held_quantity,
        buy_max_quantity=draft.buy_max_quantity,
    )


async def _refresh_execution(
    db: AsyncSession,
    redis: Redis,
    settings: Settings,
    portfolio: OwnedActivePortfolio,
    catalog_id: int,
    listing_version: int,
    reason: str,
) -> bool:
    refreshable = {"quote_unavailable", "quote_stale", "units_changed"}
    if reason not in refreshable:
        return False
    execution = await stock_catalog_trading.load_catalog_execution(
        db, settings, catalog_id, listing_version, datetime.now(UTC), portfolio=portfolio
    )
    if execution.financial is None or execution.reason not in refreshable:
        return execution.available
    await db.rollback()
    await request_catalog_quote(
        redis,
        account=settings.stock_data_account,
        server=settings.stock_data_server,
        catalog_id=catalog_id,
        listing_version=listing_version,
        fingerprint=execution.financial.fingerprint,
        purpose="financial",
    )
    # Retry the full transaction and its original-key receipt lookup. A
    # coalesced refresh result is only a hint.
    return True


def _order_refusal(exc: TradeRefused) -> HTTPException:
    if isinstance(exc, stock_catalog_trading.CatalogPriceChanged):
        return HTTPException(409, detail=exc.detail.model_dump(mode="json"))
    if exc.code == "listing_changed":
        return _listing_changed()
    if exc.code == "preview_expired":
        return _refusal(TradeRefused("quote_stale", exc.message))
    if exc.code in {"read_only", "receipt_missing"}:
        return HTTPException(409, detail={"code": exc.code})
    return _refusal(exc)


@router.post(
    "/portfolios/{portfolio_id}/stock-catalog/{catalog_id}/preview",
    response_model=CatalogPreviewOut,
    summary="Preview an exact catalog stock order",
)
async def post_catalog_preview(
    catalog_id: CatalogPath,
    body: CatalogOrderIn,
    portfolio: OwnedActivePortfolioDep,
    csrf: CsrfDep,
    db: DbDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> CatalogPreviewOut:
    try:
        try:
            preview = await stock_catalog_trading.quote(
                db, portfolio=portfolio, catalog_id=catalog_id, order=body, settings=settings
            )
        except TradeRefused as exc:
            if not await _refresh_execution(
                db, redis, settings, portfolio, catalog_id, body.listing_version, exc.code
            ):
                raise
            preview = await stock_catalog_trading.quote(
                db, portfolio=portfolio, catalog_id=catalog_id, order=body, settings=settings
            )
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _order_refusal(exc) from None
    return preview


@router.post(
    "/portfolios/{portfolio_id}/stock-catalog/{catalog_id}/confirm",
    response_model=CatalogFillOut,
    status_code=201,
    summary="Confirm or replay an exact catalog stock order",
)
async def post_catalog_confirm(
    catalog_id: CatalogPath,
    body: CatalogConfirmRequest,
    portfolio: OwnedActivePortfolioDep,
    csrf: CsrfDep,
    db: DbDep,
    redis: RedisDep,
    settings: SettingsDep,
    response: Response,
) -> CatalogFillOut:
    try:
        try:
            fill, created = await stock_catalog_trading.execute(
                db, portfolio=portfolio, catalog_id=catalog_id, order=body, settings=settings
            )
        except TradeRefused as exc:
            if not await _refresh_execution(
                db, redis, settings, portfolio, catalog_id, body.listing_version, exc.code
            ):
                raise
            fill, created = await stock_catalog_trading.execute(
                db, portfolio=portfolio, catalog_id=catalog_id, order=body, settings=settings
            )
    except TradeRefused as exc:
        await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
        raise _order_refusal(exc) from None
    await fence_owned_active_portfolios(db, portfolio.user_id, [portfolio.portfolio_id])
    if not created:
        response.status_code = 200
    return fill


@router.post(
    "/portfolios/{portfolio_id}/stock-catalog/{catalog_id}/receipt",
    response_model=CatalogFillOut,
    summary="Look up an original catalog order receipt",
)
async def post_catalog_receipt(
    catalog_id: CatalogPath,
    body: CatalogConfirmRequest,
    portfolio: OwnedActivePortfolioDep,
    csrf: CsrfDep,
    db: DbDep,
    settings: SettingsDep,
) -> CatalogFillOut:
    try:
        return await stock_catalog_trading.lookup_receipt(
            db, portfolio=portfolio, catalog_id=catalog_id, order=body, settings=settings
        )
    except TradeRefused as exc:
        raise _order_refusal(exc) from None
