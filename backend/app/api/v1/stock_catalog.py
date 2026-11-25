"""Authenticated SQL-only stock search and stable listing details."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, Response

from app.core.deps import CurrentUserDep, DbDep, SettingsDep
from app.schemas.stock_catalog import (
    CatalogIdInput,
    CatalogSearchText,
    StockCatalogItem,
    StockCatalogSearch,
)
from app.services.stock_catalog_search import catalog_item, get_catalog_listing, search_catalog

router = APIRouter(prefix="/stock-catalog", tags=["stock catalog"])
_PRIVATE_HEADERS = {"Cache-Control": "private, no-store", "Vary": "Cookie, Authorization"}


@router.get(
    "/search",
    response_model=StockCatalogSearch,
    summary="Search the locally admitted stock catalog",
    description="Returns at most twenty ticker, alias or company-name matches.",
)
async def search_stock_catalog(
    q: Annotated[CatalogSearchText, Query()],
    user: CurrentUserDep,
    db: DbDep,
    settings: SettingsDep,
    response: Response,
) -> StockCatalogSearch:
    result = await search_catalog(db, settings, q)
    response.headers.update(_PRIVATE_HEADERS)
    return result


@router.get(
    "/{catalog_id}",
    response_model=StockCatalogItem,
    summary="Read one durable stock listing identity",
    description="Resolves the original issue even when its ticker has been reassigned.",
)
async def stock_catalog_details(
    catalog_id: Annotated[CatalogIdInput, Path()],
    user: CurrentUserDep,
    db: DbDep,
    settings: SettingsDep,
    response: Response,
) -> StockCatalogItem:
    result = await get_catalog_listing(db, settings, catalog_id)
    if result is None:
        raise HTTPException(
            404,
            detail={"code": "stock_catalog_not_found"},
            headers=_PRIVATE_HEADERS,
        )
    response.headers.update(_PRIVATE_HEADERS)
    return catalog_item(result)
