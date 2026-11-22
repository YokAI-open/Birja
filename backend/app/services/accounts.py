from decimal import Decimal

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import IdentityOut

STARTING_CASH = Decimal("10000.00")


async def get_or_create_user(db: AsyncSession, email: str) -> tuple[int, bool]:
    """Return (user_id, created). Grants the starting cash exactly once: the
    UNIQUE(email) conflict decides who creates. Does not commit; the caller
    owns the transaction."""
    stmt = (
        pg_insert(User)
        .values(email=email)
        .on_conflict_do_nothing(index_elements=["email"])
        .returning(User.id)
    )
    new_id = (await db.execute(stmt)).scalar_one_or_none()
    if new_id is not None:
        await db.execute(text("SELECT public.initialize_portfolio(:user_id)"), {"user_id": new_id})
        return new_id, True
    existing = (await db.execute(select(User.id).where(User.email == email))).scalar_one()
    return existing, False


async def get_me(db: AsyncSession, user_id: int) -> IdentityOut:
    """Identity is independent of portfolio count and never creates financial roots."""
    email = (await db.execute(select(User.email).where(User.id == user_id))).scalar_one()
    return IdentityOut(email=email)
