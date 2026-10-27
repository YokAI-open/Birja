import asyncio
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.models.user import Account, User
from app.services.accounts import STARTING_CASH, get_or_create_user
from tests.helpers import unique_email


@pytest.fixture
def sessions(engine: AsyncEngine, migrated: None) -> async_sessionmaker:  # type: ignore[type-arg]
    return async_sessionmaker(engine, expire_on_commit=False)


async def test_first_call_creates_user_and_account(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    email = unique_email()
    async with sessions() as db:
        uid, created = await get_or_create_user(db, email)
        await db.commit()
    assert created is True
    async with sessions() as db:
        acct = (await db.execute(select(Account).where(Account.user_id == uid))).scalar_one()
    assert acct.cash == acct.starting_cash == Decimal("10000.00") == STARTING_CASH


async def test_second_call_is_idempotent(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    email = unique_email()
    async with sessions() as db:
        uid, _ = await get_or_create_user(db, email)
        await db.commit()
    async with sessions() as db:
        uid2, created = await get_or_create_user(db, email)
        await db.commit()
    assert (uid2, created) == (uid, False)
    async with sessions() as db:
        n = (
            await db.execute(
                select(func.count()).select_from(Account).where(Account.user_id == uid)
            )
        ).scalar_one()
    assert n == 1


async def test_concurrent_first_sign_ins_create_one_account(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    email = unique_email()

    async def one() -> tuple[int, bool]:
        async with sessions() as db:
            result = await get_or_create_user(db, email)
            await db.commit()
            return result

    results = await asyncio.gather(*(one() for _ in range(10)))
    assert sum(1 for _, created in results if created) == 1
    assert len({uid for uid, _ in results}) == 1
    async with sessions() as db:
        users = (
            await db.execute(select(func.count()).select_from(User).where(User.email == email))
        ).scalar_one()
        accts = (
            await db.execute(
                select(func.count()).select_from(Account).where(Account.user_id == results[0][0])
            )
        ).scalar_one()
    assert (users, accts) == (1, 1)


async def test_negative_cash_rejected(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    async with sessions() as db:
        uid, _ = await get_or_create_user(db, unique_email())
        await db.commit()
    async with sessions() as db:
        acct = (await db.execute(select(Account).where(Account.user_id == uid))).scalar_one()
        acct.cash = Decimal("-0.01")
        with pytest.raises(IntegrityError):
            await db.flush()


async def test_second_account_rejected(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    async with sessions() as db:
        uid, _ = await get_or_create_user(db, unique_email())
        await db.commit()
    async with sessions() as db:
        db.add(Account(user_id=uid, cash=Decimal("1"), starting_cash=Decimal("1")))
        with pytest.raises(IntegrityError):
            await db.flush()


async def test_uppercase_email_rejected(sessions: async_sessionmaker) -> None:  # type: ignore[type-arg]
    async with sessions() as db:
        db.add(User(email="Upper-" + unique_email()))
        with pytest.raises(IntegrityError):
            await db.flush()
