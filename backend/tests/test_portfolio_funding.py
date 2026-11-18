"""Once-only initialization and explicit funding in real restricted transactions."""

import asyncio
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services.accounts import get_or_create_user
from tests import test_portfolio_management_authority as authority_harness
from tests.test_portfolio_management_authority import (
    close,
    create,
    owner,
    reject,
)

authority = authority_harness.authority


async def evidence(migrator, uid):
    async with migrator.connect() as conn:
        roots = (
            await conn.execute(
                text(
                    "SELECT id,name,description,cash,starting_cash,closed_at FROM accounts "
                    "WHERE user_id=:u ORDER BY id"
                ),
                {"u": uid},
            )
        ).all()
        grants = (
            await conn.execute(
                text(
                    "SELECT portfolio_id,origin,amount FROM portfolio_creations "
                    "WHERE user_id=:u ORDER BY id"
                ),
                {"u": uid},
            )
        ).all()
        latch = (
            await conn.execute(
                text(
                    "SELECT origin,portfolio_id,creation_id FROM portfolio_initializations "
                    "WHERE user_id=:u"
                ),
                {"u": uid},
            )
        ).all()
        return roots, grants, latch


async def test_signup_records_initial_provenance_and_explicit_create_is_separate(authority):
    app, migrator = authority
    sessions = async_sessionmaker(app, expire_on_commit=False)
    email = f"funding-{uuid4()}@example.test"
    async with sessions() as db:
        uid, created = await get_or_create_user(db, email)
        assert created
        await db.commit()
    roots, grants, latch = await evidence(migrator, uid)
    assert len(roots) == len(grants) == len(latch) == 1
    initial = roots[0].id
    assert tuple(roots[0])[1:] == ("My portfolio", "", 10000, 10000, None)
    assert tuple(grants[0]) == (initial, "initial", 10000)
    assert latch[0].origin == "initial" and latch[0].portfolio_id == initial
    async with app.begin() as conn:
        assert (
            await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": uid})
        ).scalar_one() == initial
    extra = await create(app, uid, "Independent")
    assert extra.portfolio_id != initial
    await close(migrator, initial)
    await close(migrator, extra.portfolio_id)
    before = await evidence(migrator, uid)
    for _ in range(2):
        async with sessions() as db:
            assert await get_or_create_user(db, email) == (uid, False)
            await db.commit()
        async with app.begin() as conn:
            assert (
                await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": uid})
            ).scalar_one() == initial
    assert await evidence(migrator, uid) == before
    replacement = await create(app, uid, "Replacement")
    assert replacement.portfolio_id not in {initial, extra.portfolio_id}
    roots, grants, latch = await evidence(migrator, uid)
    assert len(roots) == len(grants) == 3 and len(latch) == 1
    assert sum(row.amount for row in grants) == 30000


async def test_concurrent_signup_commits_one_initial_journal_and_latch(authority):
    app, migrator = authority
    sessions = async_sessionmaker(app, expire_on_commit=False)
    email = f"funding-race-{uuid4()}@example.test"

    async def signup():
        async with sessions() as db:
            result = await get_or_create_user(db, email)
            await db.commit()
            return result

    results = await asyncio.gather(*(signup() for _ in range(8)))
    assert sum(created for _, created in results) == 1
    assert len({uid for uid, _ in results}) == 1
    roots, grants, latch = await evidence(migrator, results[0][0])
    assert len(roots) == len(grants) == len(latch) == 1
    assert grants[0].amount == roots[0].cash == roots[0].starting_cash == 10000


async def test_signup_rollback_removes_user_root_grant_and_latch_together(authority):
    app, migrator = authority
    sessions = async_sessionmaker(app, expire_on_commit=False)
    email = f"funding-rollback-{uuid4()}@example.test"
    async with sessions() as db:
        uid, created = await get_or_create_user(db, email)
        assert created
        # Own transaction has all evidence, independently invisible until commit.
        assert (await evidence(migrator, uid)) == ([], [], [])
        await db.rollback()
    assert (await evidence(migrator, uid)) == ([], [], [])
    async with migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT id FROM users WHERE email=:e"), {"e": email})
        ).first() is None
    async with sessions() as db:
        replacement, created = await get_or_create_user(db, email)
        assert created and replacement != uid
        await db.commit()
    roots, grants, latch = await evidence(migrator, replacement)
    assert len(roots) == len(grants) == len(latch) == 1


async def test_legacy_empty_latch_cannot_be_initialized_but_can_explicitly_create(authority):
    app, migrator = authority
    uid = await owner(migrator)
    async with migrator.begin() as conn:
        await conn.execute(
            text("INSERT INTO portfolio_initializations(user_id,origin) VALUES (:u,'legacy')"),
            {"u": uid},
        )
    for _ in range(2):
        async with app.begin() as conn:
            assert (
                await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": uid})
            ).scalar_one() is None
    roots, grants, latch = await evidence(migrator, uid)
    assert roots == grants == [] and tuple(latch[0]) == ("legacy", None, None)
    await create(app, uid)
    roots, grants, latch = await evidence(migrator, uid)
    assert len(roots) == len(grants) == 1 and len(latch) == 1
    assert grants[0].origin == "explicit"


async def test_concurrent_initializer_is_once_only_and_unlatched_existing_books_refuse(authority):
    app, migrator = authority
    uid = await owner(migrator)

    async def initialize():
        async with app.begin() as conn:
            return (
                await conn.execute(text("SELECT initialize_portfolio(:u)"), {"u": uid})
            ).scalar_one()

    roots = await asyncio.gather(*(initialize() for _ in range(8)))
    assert len(set(roots)) == 1
    books, grants, latch = await evidence(migrator, uid)
    assert len(books) == len(grants) == len(latch) == 1
    other = await owner(migrator)
    await create(app, other)
    await reject(
        app,
        "SELECT initialize_portfolio(:u)",
        {"u": other},
        state="P0002",
        message="initialization_unavailable",
    )
    for malformed in (None, 0, -1):
        await reject(app, "SELECT initialize_portfolio(:u)", {"u": malformed}, state="22023")
