"""Resolve one explicit owned active financial root, without fallback."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Account, User
from app.schemas.portfolios import (
    PortfolioCreate,
    PortfolioMetadata,
    PortfolioPatch,
    PortfolioSummary,
)


@dataclass(frozen=True)
class OwnedActivePortfolio:
    portfolio_id: int
    user_id: int


async def resolve_owned_active_portfolio(
    db: AsyncSession, user: User, portfolio_id: int
) -> OwnedActivePortfolio:
    row = (
        await db.execute(
            select(Account.id, Account.user_id).where(
                Account.id == portfolio_id,
                Account.user_id == user.id,
                Account.closed_at.is_(None),
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "portfolio_unavailable"})
    return OwnedActivePortfolio(portfolio_id=row.id, user_id=row.user_id)


async def list_active_portfolios(db: AsyncSession, user: User) -> list[PortfolioSummary]:
    rows = await db.execute(
        select(Account.id, Account.name)
        .where(Account.user_id == user.id, Account.closed_at.is_(None))
        .order_by(Account.id)
    )
    result = [PortfolioSummary(id=row.id, name=row.name) for row in rows]
    await fence_owned_active_portfolios(db, user.id, [row.id for row in result])
    return result


async def fence_owned_active_portfolios(
    db: AsyncSession, user_id: int, portfolio_ids: list[int]
) -> None:
    """Final read authority, held until the response transaction closes.

    This is deliberately separate from initial target resolution. In particular,
    stock execution must acquire its instrument gate before any account lock.
    Call only after financial hydration/operations, with no later instrument work.
    """
    if not portfolio_ids:
        return
    found = set(
        (
            await db.scalars(
                select(Account.id)
                .where(
                    Account.id.in_(portfolio_ids),
                    Account.user_id == user_id,
                    Account.closed_at.is_(None),
                )
                .order_by(Account.id)
                .with_for_update(read=True, of=Account)
            )
        ).all()
    )
    if found != set(portfolio_ids):
        raise HTTPException(404, detail={"code": "portfolio_unavailable"})


def _management_error(exc: DBAPIError) -> HTTPException | None:
    state = getattr(exc.orig, "sqlstate", None)
    cause = getattr(exc.orig, "__cause__", None)
    message = getattr(cause, "message", None)
    if state == "23505" and message in {"name_taken", "creation_key_conflict"}:
        return HTTPException(409, detail={"code": message})
    if state == "23514" and message == "portfolio_limit":
        return HTTPException(409, detail={"code": message})
    if state == "P0002" and message == "portfolio_unavailable":
        return HTTPException(404, detail={"code": message})
    if state == "22023":
        return HTTPException(422, detail={"code": "invalid_input"})
    if state == "P0001" and message == "creation_quota":
        now = datetime.now(UTC)
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return HTTPException(
            429,
            detail={"code": message},
            headers={"Retry-After": str(max(1, int((midnight - now).total_seconds()) + 1))},
        )
    if state in {"55P03", "57014", "40001", "40P01"}:
        return HTTPException(
            503, detail={"code": "service_unavailable"}, headers={"Retry-After": "5"}
        )
    return None


async def create_portfolio(
    db: AsyncSession, user: User, key: UUID, payload: PortfolioCreate
) -> tuple[PortfolioMetadata, bool]:
    """SQL owns canonical intent, owner lock, grant and replay ordering; service commits."""
    try:
        row = (
            await db.execute(
                text("SELECT * FROM public.create_portfolio(:u,:k,:n,:d)"),
                {"u": user.id, "k": key, "n": payload.name, "d": payload.description},
            )
        ).one()
        result = PortfolioMetadata(id=row.portfolio_id, name=row.name, description=row.description)
        replayed = bool(row.replayed)
        await db.commit()
        return result, replayed
    except DBAPIError as exc:
        await db.rollback()
        refusal = _management_error(exc)
        if refusal is not None:
            raise refusal from None
        raise


async def update_portfolio_metadata(
    db: AsyncSession, user: User, portfolio_id: int, payload: PortfolioPatch
) -> PortfolioMetadata:
    try:
        row = (
            await db.execute(
                text("SELECT * FROM public.update_portfolio_metadata(:u,:p,:n,:d,:hn,:hd)"),
                {
                    "u": user.id,
                    "p": portfolio_id,
                    "n": payload.name,
                    "d": payload.description,
                    "hn": "name" in payload.model_fields_set,
                    "hd": "description" in payload.model_fields_set,
                },
            )
        ).one()
        result = PortfolioMetadata(id=row.portfolio_id, name=row.name, description=row.description)
        await db.commit()
        return result
    except DBAPIError as exc:
        await db.rollback()
        refusal = _management_error(exc)
        if refusal is not None:
            raise refusal from None
        raise


async def get_portfolio_metadata(
    db: AsyncSession, user: User, portfolio_id: int
) -> PortfolioMetadata:
    row = (
        await db.execute(
            select(Account.id, Account.name, Account.description).where(
                Account.id == portfolio_id, Account.user_id == user.id, Account.closed_at.is_(None)
            )
        )
    ).one_or_none()
    if row is None:
        raise HTTPException(404, detail={"code": "portfolio_unavailable"})
    await fence_owned_active_portfolios(db, user.id, [portfolio_id])
    return PortfolioMetadata(id=row.id, name=row.name, description=row.description)
