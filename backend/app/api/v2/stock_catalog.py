"""Request selected display quotes and read the owned catalog ticket."""

from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.stock_trades import PrivateRoute
from app.core.config import Settings
from app.core.deps import (
    CsrfDep,
    CurrentUserDep,
    DbDep,
    OwnedActivePortfolioDep,
    RedisDep,
    SettingsDep,
)
from app.schemas.stock_catalog import CatalogIdInput, StockCatalogItem
from app.schemas.stock_catalog_quotes import (
    CatalogPriceOut,
    CatalogQuoteIn,
    CatalogQuoteOut,
    CatalogQuoteReason,
    CatalogSessionOut,
    CatalogTradeContextOut,
)
from app.services.portfolios import OwnedActivePortfolio, fence_owned_active_portfolios
from app.services.stock_catalog_quote_demand import request_catalog_quote
from app.services.stock_catalog_quotes import (
    CatalogQuoteContext,
    catalog_quote_is_current,
    catalog_quote_valid_until,
    load_catalog_quote_context,
    read_catalog_quote,
)
from app.services.stock_catalog_search import catalog_item

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


async def _present(
    db: AsyncSession,
    redis: Redis,
    settings: Settings,
    context: CatalogQuoteContext,
    listing: StockCatalogItem,
    *,
    fallback: CatalogQuoteReason = CatalogQuoteReason.QUOTE_UNAVAILABLE,
    portfolio: OwnedActivePortfolio | None = None,
) -> tuple[CatalogQuoteContext, CatalogQuoteOut]:
    price = None
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
    if binding is not None and quote is not None:
        # Recheck the authority and clock after the cache read and portfolio
        # fence, which can wait for a concurrent portfolio change.
        context, listing = await _read_context(
            db, settings, listing.catalog_id, listing.listing_version
        )
        if (
            context.binding is not None
            and context.binding.fingerprint == binding.fingerprint
            and catalog_quote_is_current(quote, context, now=datetime.now(UTC))
        ):
            price = CatalogPriceOut(
                bid=quote.bid,
                ask=quote.ask,
                mid=quote.mid,
                event_at=quote.event_at,
                collected_at=quote.collected_at,
                valid_until=catalog_quote_valid_until(quote, context.binding),
            )

    session = context.session
    state: Literal["open", "closed", "unknown"] = "unknown"
    if session.state == "open":
        state = "open"
    elif session.state == "closed":
        state = "closed"
    reason = CatalogQuoteReason(context.reason)
    if reason == CatalogQuoteReason.READY and price is None:
        reason = fallback
    return context, CatalogQuoteOut(
        listing=listing,
        session=CatalogSessionOut(
            state=state,
            opens_at=session.current.opens_at if session.current else None,
            closes_at=session.current.closes_at if session.current else None,
            next_open_at=session.next_session.opens_at if session.next_session else None,
        ),
        quote=price,
        reason=reason,
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
    context, view = await _present(db, redis, settings, context, listing)
    binding = context.binding
    if view.quote is not None or context.reason != "ready" or binding is None:
        return view

    # Return the DB connection before the bounded scheduler wait. Only the
    # immutable scope of this selected listing crosses the wait boundary.
    await db.rollback()
    result = await request_catalog_quote(
        redis,
        account=settings.stock_data_account,
        server=settings.stock_data_server,
        catalog_id=catalog_id,
        listing_version=body.listing_version,
        fingerprint=binding.fingerprint,
    )
    context, listing = await _read_context(db, settings, catalog_id, body.listing_version)
    if context.binding is not None and context.binding.fingerprint != binding.fingerprint:
        raise _listing_changed()
    fallback = (
        CatalogQuoteReason.QUOTE_UNAVAILABLE if result == "ready" else CatalogQuoteReason(result)
    )
    context, view = await _present(db, redis, settings, context, listing, fallback=fallback)
    if context.binding is not None and context.binding.fingerprint != binding.fingerprint:
        raise _listing_changed()
    if view.reason == CatalogQuoteReason.QUEUE_FULL:
        raise HTTPException(503, detail={"code": "queue_full"}, headers={"Retry-After": "5"})
    return view


@router.get(
    "/portfolios/{portfolio_id}/stock-catalog/{catalog_id}/trade-context",
    response_model=CatalogTradeContextOut,
    summary="Read an owned portfolio's catalog trade context",
    description="Displays cached listing evidence and the active owned portfolio identity.",
)
async def get_catalog_trade_context(
    catalog_id: CatalogPath,
    portfolio: OwnedActivePortfolioDep,
    db: DbDep,
    redis: RedisDep,
    settings: SettingsDep,
) -> CatalogTradeContextOut:
    context, listing = await _read_context(db, settings, catalog_id)
    _, view = await _present(db, redis, settings, context, listing, portfolio=portfolio)
    return CatalogTradeContextOut(
        listing=view.listing,
        session=view.session,
        quote=view.quote,
        reason=view.reason,
        portfolio_id=portfolio.portfolio_id,
    )
