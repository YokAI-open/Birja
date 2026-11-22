"""Real OTP/session and once-only funding with zero, one or many roots."""

import asyncio
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import decode_access_token
from app.models.auth import AuthSession
from app.models.portfolio_creation import PortfolioInitialization
from app.models.user import Account, User
from app.schemas.auth import IdentityOut
from app.services import accounts, auth
from app.services.otp import OtpStore
from tests.portfolio_fixtures import close_empty_test_root
from tests.test_portfolio_creation import authority, management_api

__all__ = ["authority", "management_api"]


@pytest.fixture
def sessions(management_api):
    return async_sessionmaker(management_api.restricted, expire_on_commit=False)


@pytest.fixture
def legacy_sessions(management_api):
    return async_sessionmaker(management_api.migrator, expire_on_commit=False)


async def seed_identity(sessions, count, *, closed=False):
    email = f"identity-{uuid4()}@example.test"
    async with sessions() as db:
        user = User(email=email)
        db.add(user)
        await db.flush()
        uid = user.id
        db.add(PortfolioInitialization(user_id=uid, origin="legacy"))
        for n in range(count):
            db.add(
                Account(
                    user_id=uid,
                    name=f"Original {n}",
                    name_key=f"original {n}",
                    cash=Decimal("4321.09") + n,
                    starting_cash=Decimal("8765.43") + n,
                )
            )
        await db.flush()
        if closed:
            root = (await db.scalars(select(Account).where(Account.user_id == uid))).one()
            await close_empty_test_root(db, root.id)
        await db.commit()
    return uid, email


async def root_snapshot(sessions, uid):
    async with sessions() as db:
        return (
            await db.execute(
                select(
                    Account.id,
                    Account.name,
                    Account.cash,
                    Account.starting_cash,
                    Account.closed_at,
                    Account.created_at,
                )
                .where(Account.user_id == uid)
                .order_by(Account.id)
            )
        ).all()


@pytest.mark.parametrize("count,closed", [(0, False), (1, False), (2, False), (1, True)])
async def test_identity_read_and_returning_lookup_never_create_or_regrant(
    sessions, legacy_sessions, count, closed
):
    uid, email = await seed_identity(legacy_sessions, count, closed=closed)
    before = await root_snapshot(sessions, uid)
    for _ in range(2):
        async with sessions() as db:
            assert await accounts.get_me(db, uid) == IdentityOut(email=email)
            assert await accounts.get_or_create_user(db, email) == (uid, False)
            await db.commit()
    assert await root_snapshot(sessions, uid) == before


async def test_new_signup_alone_has_one_named_funded_root(sessions):
    email = f"first-{uuid4()}@example.test"
    async with sessions() as db:
        uid, created = await accounts.get_or_create_user(db, email)
        assert created
        assert await accounts.get_me(db, uid) == IdentityOut(email=email)
        await db.commit()
    roots = await root_snapshot(sessions, uid)
    assert len(roots) == 1
    assert roots[0].name == "My portfolio"
    assert roots[0].cash == roots[0].starting_cash == Decimal("10000.00")


async def test_concurrent_onboarding_commits_one_user_one_grant(sessions):
    email = f"concurrent-{uuid4()}@example.test"

    async def create():
        async with sessions() as db:
            result = await accounts.get_or_create_user(db, email)
            await db.commit()
            return result

    results = await asyncio.gather(*(create() for _ in range(8)))
    assert sum(created for _, created in results) == 1
    assert len({uid for uid, _ in results}) == 1
    roots = await root_snapshot(sessions, results[0][0])
    assert len(roots) == 1
    assert roots[0].cash == roots[0].starting_cash == Decimal("10000.00")


async def test_aborted_onboarding_rolls_back_user_and_funding_together(sessions):
    email = f"abort-{uuid4()}@example.test"
    async with sessions() as db:
        uid, _ = await accounts.get_or_create_user(db, email)
        await db.rollback()
    async with sessions() as db:
        assert (await db.execute(select(User.id).where(User.email == email))).first() is None
        assert (await db.execute(select(Account.id).where(Account.user_id == uid))).first() is None
        uid, created = await accounts.get_or_create_user(db, email)
        assert created
        await db.commit()
    assert len(await root_snapshot(sessions, uid)) == 1


@pytest.mark.parametrize("count,closed", [(0, False), (1, False), (2, False), (1, True)])
async def test_otp_identity_refresh_logout_independent_of_roots(
    sessions, legacy_sessions, redis_client, settings, count, closed
):
    uid, email = await seed_identity(legacy_sessions, count, closed=closed)
    before = await root_snapshot(sessions, uid)
    otp = OtpStore(redis_client, settings.otp_hmac_secret)
    code = await otp.issue(email)
    async with sessions() as db:
        identity, issued = await auth.verify_code(
            db, redis_client, otp, settings, email, code, "127.0.0.1"
        )
    assert identity.model_dump() == {"email": email}
    assert isinstance(identity, IdentityOut)
    claims = decode_access_token(issued.access, settings.jwt_secret)
    assert claims.user_id == uid
    async with sessions() as db:
        with pytest.raises(auth.InvalidCode):
            await auth.verify_code(db, redis_client, otp, settings, email, code, "127.0.0.1")
    async with sessions() as db:
        rotated = await auth.rotate_session(db, settings, issued.refresh)
    assert decode_access_token(rotated.access, settings.jwt_secret).user_id == uid
    async with sessions() as db:
        await auth.end_session(db, settings, rotated.access)
    async with sessions() as db:
        session = await db.get(AuthSession, claims.session_id)
        assert session.revoked_at is not None
    async with sessions() as db:
        with pytest.raises(auth.InvalidSession):
            await auth.rotate_session(db, settings, rotated.refresh)
    assert await root_snapshot(sessions, uid) == before


async def test_first_otp_signup_issues_identity_and_funds_once(sessions, redis_client, settings):
    email = f"otp-new-{uuid4()}@example.test"
    otp = OtpStore(redis_client, settings.otp_hmac_secret)
    for _ in range(2):
        code = await otp.issue(email)
        async with sessions() as db:
            identity, issued = await auth.verify_code(
                db, redis_client, otp, settings, email, code, "127.0.0.1"
            )
        assert identity.model_dump() == {"email": email}
    uid = decode_access_token(issued.access, settings.jwt_secret).user_id
    roots = await root_snapshot(sessions, uid)
    assert len(roots) == 1
    assert roots[0].name == "My portfolio"
    assert roots[0].cash == roots[0].starting_cash == Decimal("10000.00")
