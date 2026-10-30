import asyncio
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from app.models.user import Account, User
from app.services.accounts import STARTING_CASH, get_or_create_user
from tests.helpers import OutboxSender, csrf_headers, request_and_get_code, unique_email


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


async def test_second_sign_in_keeps_cash(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    sessions: async_sessionmaker,  # type: ignore[type-arg]
) -> None:
    email = unique_email()
    for _ in range(2):
        code = await request_and_get_code(auth_client, outbox, email)
        headers = await csrf_headers(auth_client)
        resp = await auth_client.post(
            "/api/v1/auth/verify-code", json={"email": email, "code": code}, headers=headers
        )
        assert resp.status_code == 200
        assert Decimal(resp.json()["cash_usd"]) == Decimal("10000.00")
    async with sessions() as db:
        n = (
            await db.execute(
                select(func.count()).select_from(Account).join(User).where(User.email == email)
            )
        ).scalar_one()
    assert n == 1


def test_route_allow_list_has_no_cash_mutation(running_app) -> None:  # type: ignore[no-untyped-def]
    # FastAPI includes routers lazily, so read the generated OpenAPI paths.
    routes = {
        (method.upper(), path)
        for path, ops in running_app.openapi()["paths"].items()
        if path.startswith("/api/v1")
        for method in ops
    }
    assert routes == {
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/me"),
        ("GET", "/api/v1/prices"),
        ("GET", "/api/v1/portfolio"),
        ("GET", "/api/v1/auth/csrf"),
        ("POST", "/api/v1/auth/request-code"),
        ("POST", "/api/v1/auth/refresh"),
        ("POST", "/api/v1/auth/logout"),
        ("POST", "/api/v1/auth/verify-code"),
        ("POST", "/api/v1/trades"),
        ("GET", "/api/v1/trades"),
        ("POST", "/api/v1/trades/quote"),
        ("GET", "/api/v1/holdings/{symbol}"),
    }
    for _, path in routes:
        assert not any(w in path for w in ("reset", "deposit", "topup", "cash", "grant"))
