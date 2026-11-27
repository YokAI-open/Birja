"""Private metadata discovery and explicitly owned portfolio statements."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, HTTPException, Path, Request, Response

from app.api.v2.portfolio_management import (
    ManagementRoute,
    creation_key,
    enforce_closure_attempt,
    enforce_creation_attempt,
    read_closure_body,
    read_management_body,
)
from app.core.deps import (
    ClientIpDep,
    CsrfDep,
    CurrentUserDep,
    DbDep,
    OwnedActivePortfolioDep,
    RedisDep,
    SettingsDep,
)
from app.schemas.portfolio import HoldingOut, PortfolioOut
from app.schemas.portfolio_closure import PortfolioClosureReceipt
from app.schemas.portfolio_daily_values import PortfolioDailyHistory
from app.schemas.portfolios import (
    PortfolioCreate,
    PortfolioMetadata,
    PortfolioOverview,
    PortfolioOverviewList,
    PortfolioPatch,
    PortfolioSummary,
)
from app.schemas.trades import Money
from app.services.portfolio import get_portfolio, load_portfolio_snapshots
from app.services.portfolio_closure import ClosureIntent, close_owned_portfolio
from app.services.portfolio_daily_values import read_portfolio_daily_history
from app.services.portfolios import (
    create_portfolio,
    get_portfolio_metadata,
    list_active_portfolios,
    update_portfolio_metadata,
)

router = APIRouter(prefix="/portfolios", tags=["portfolios"], route_class=ManagementRoute)

PortfolioOverview.model_rebuild(_types_namespace={"HoldingOut": HoldingOut, "Money": Money})


@router.get(
    "",
    response_model=list[PortfolioSummary],
    summary="Discover your active portfolio identities",
    description="Returns owned active IDs and names in stable order, without funding or totals.",
)
async def portfolios(user: CurrentUserDep, db: DbDep) -> list[PortfolioSummary]:
    return await list_active_portfolios(db, user)


@router.get(
    "/overview",
    response_model=PortfolioOverviewList,
    summary="Compare your active portfolio statements",
    description="Returns up to ten owned books in ID order with separate values and returns.",
)
async def overview(
    user: CurrentUserDep, db: DbDep, settings: SettingsDep
) -> list[PortfolioOverview]:
    snapshots = await load_portfolio_snapshots(db, owner_id=user.id, settings=settings)
    return [PortfolioOverview.from_value(value) for value in snapshots]


@router.get(
    "/value-history",
    response_model=PortfolioDailyHistory,
    summary="Read daily values for your active portfolios",
    description="Returns up to thirty UTC days of observations for the signed-in owner's books.",
)
async def value_history(user: CurrentUserDep, db: DbDep) -> PortfolioDailyHistory:
    return await read_portfolio_daily_history(db, owner_id=user.id)


@router.get(
    "/{portfolio_id}",
    response_model=PortfolioOut,
    summary="Read one owned portfolio statement",
    description="Values the selected active portfolio against its original stored starting cash.",
)
async def portfolio(
    portfolio: OwnedActivePortfolioDep, db: DbDep, settings: SettingsDep
) -> PortfolioOut:
    return PortfolioOut.from_value(await get_portfolio(db, portfolio=portfolio, settings=settings))


PortfolioPath = Annotated[str, Path(pattern=r"^[1-9][0-9]{0,18}$", max_length=19)]


def _portfolio_id(value: str) -> int:
    result = int(value)
    if result > 9223372036854775807:
        raise HTTPException(422, detail={"code": "invalid_input"})
    return result


@router.post(
    "",
    response_model=PortfolioMetadata,
    status_code=201,
    summary="Create one independently funded portfolio",
    description="Uses the original UUIDv4 key for permanent safe retries; returns200 on replay.",
)
async def create(
    request: Request,
    response: Response,
    user: CurrentUserDep,
    csrf: CsrfDep,
    db: DbDep,
    redis: RedisDep,
    ip: ClientIpDep,
    settings: SettingsDep,
) -> PortfolioMetadata:
    await enforce_creation_attempt(redis, user.id, ip, settings)
    keys = request.headers.getlist("idempotency-key")
    key = creation_key(keys[0] if len(keys) == 1 else None)
    payload = cast(PortfolioCreate, await read_management_body(request, patch=False))
    result, replayed = await create_portfolio(db, user, key, payload)
    response.status_code = 200 if replayed else 201
    return result


@router.patch(
    "/{portfolio_id}",
    response_model=PortfolioMetadata,
    summary="Edit an owned active portfolio's metadata",
    description="Changes name or description without changing funding, trades or original intent.",
)
async def edit_metadata(
    portfolio_id: PortfolioPath,
    request: Request,
    user: CurrentUserDep,
    csrf: CsrfDep,
    db: DbDep,
) -> PortfolioMetadata:
    target = _portfolio_id(portfolio_id)
    payload = cast(PortfolioPatch, await read_management_body(request, patch=True))
    return await update_portfolio_metadata(db, user, target, payload)


@router.get(
    "/{portfolio_id}/metadata",
    response_model=PortfolioMetadata,
    summary="Read an owned active portfolio's metadata",
    description="Returns only ID, name and description; no pooled or financial values.",
)
async def metadata(
    portfolio_id: PortfolioPath, user: CurrentUserDep, db: DbDep
) -> PortfolioMetadata:
    return await get_portfolio_metadata(db, user, _portfolio_id(portfolio_id))


@router.delete(
    "/{portfolio_id}",
    response_model=PortfolioClosureReceipt,
    summary="End one explicitly reviewed owned portfolio",
    description="Permanently freezes the original strategy; "
    "retries acknowledge only its original identity.",
)
async def delete_portfolio(
    portfolio_id: PortfolioPath,
    request: Request,
    user: CurrentUserDep,
    csrf: CsrfDep,
    db: DbDep,
    redis: RedisDep,
    ip: ClientIpDep,
    settings: SettingsDep,
) -> PortfolioClosureReceipt:
    target = _portfolio_id(portfolio_id)
    await enforce_closure_attempt(redis, user.id, ip, settings)
    payload = await read_closure_body(request)
    original = ClosureIntent(
        user.id, target, UUID(payload.intent_key), payload.confirmation_name, payload.policy_version
    )
    result = await close_owned_portfolio(db, original)
    return PortfolioClosureReceipt(portfolio_id=result.portfolio_id)
