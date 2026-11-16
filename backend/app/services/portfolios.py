"""Resolve one explicit owned active financial root, without fallback."""

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Account, User
from app.schemas.portfolios import PortfolioSummary


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
    return [PortfolioSummary(id=row.id, name=row.name) for row in rows]
