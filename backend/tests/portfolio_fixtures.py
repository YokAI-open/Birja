"""Independent synthetic money oracles on the guarded disposable test database.

Staged tests intentionally do not request migrated/running_app: a runnable app
must never be admitted against expansion/association-only revisions.
"""

import asyncio
import hashlib
import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, create_async_engine

from tests.test_migrations import ensure_dividend_test_owner, run_test_migration, test_migration_url

OWNED_TABLES = (
    "holdings",
    "trades",
    "stock_fill_facts",
    "stock_ownership_movements",
    "stock_dividend_entitlements",
    "stock_dividend_payments",
    "stock_dividend_decisions",
)
ECONOMIC_TABLES = ("users", "accounts", *OWNED_TABLES, "stock_split_applications")


async def migrate_to(revision: str, *, down: bool = False) -> None:
    assert revision in {"base", "head", *(f"{n:04}" for n in range(7, 18))}
    await asyncio.to_thread(run_test_migration, revision, down=down)


async def reset_disposable_schema(engine: AsyncEngine) -> None:
    """Destructive teardown ONLY in the exact throwaway database, never an app path."""
    test_migration_url(os.environ["DATABASE_URL"], os.environ["REDIS_URL"])
    async with engine.begin() as conn:
        assert (
            await conn.execute(
                text(
                    "SELECT current_database(),session_user,rolsuper FROM pg_roles "
                    "WHERE rolname=session_user"
                )
            )
        ).one() == ("birja_test", "birja_test", True)
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public AUTHORIZATION birja_test"))
    await ensure_dividend_test_owner()


@pytest_asyncio.fixture
async def portfolio_migration_db(engine: AsyncEngine) -> AsyncIterator[AsyncEngine]:
    await reset_disposable_schema(engine)
    try:
        yield engine
    finally:
        # Immutable seeded ledgers cannot be SQL-deleted or downgraded. Throw
        # away this isolated schema, then restore the genuine migration head.
        await reset_disposable_schema(engine)
        await migrate_to("head")


async def economic_snapshot(conn: AsyncConnection) -> dict[str, tuple[tuple, ...]]:
    """Freeze every legacy column including retained jsonb bytes and timestamps."""
    result = {}
    for table in ECONOMIC_TABLES:
        present = (await conn.execute(text("SELECT to_regclass(:t)"), {"t": table})).scalar()
        if present is None:
            continue
        # Compare all legacy values, explicitly removing only new metadata.
        key = "trade_id" if table == "stock_fill_facts" else "id"
        rows = await conn.execute(
            text(  # noqa: S608 - fixed inventory above
                f"SELECT {key},(to_jsonb(t)-'portfolio_id'-'name'-'closed_at'-'description'"  # noqa: S608
                f"-'owner_digest_version')::text FROM public.{table} t ORDER BY {key}"
            )
        )
        result[table] = tuple(tuple(row) for row in rows)
    return result


@dataclass(frozen=True)
class LegacyBooks:
    owners: tuple[int, int]
    roots: tuple[int, int]
    crypto: int
    stock: int
    trade_ids: tuple[int, int]
    split_id: int
    cash: tuple[Decimal, Decimal] = (Decimal("8765.43"), Decimal("123.45"))
    baselines: tuple[Decimal, Decimal] = (Decimal("12500.00"), Decimal("7777.00"))


def legacy_digest(rows: list[list[object]]) -> str:
    # Independent canonical oracle, not imported from the implementation under test.
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def seed_legacy_books(conn: AsyncConnection) -> LegacyBooks:
    """Two actual users, unequal original books and ONE global two-owner split."""
    from tests.test_dividend_schema import decision, payment
    from tests.test_stock_action_migrations import event, movement
    from tests.test_stock_execution_migrations import insert_trade

    owners, roots, trade_ids = [], [], []
    crypto = (await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
    stock = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
    for cash, baseline in (("8765.43", "12500"), ("123.45", "7777")):
        uid = (
            await conn.execute(
                text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                {"e": f"portfolio-legacy-{uuid4()}@example.test"},
            )
        ).scalar_one()
        root = (
            await conn.execute(
                text(
                    "INSERT INTO accounts(user_id,cash,starting_cash) "
                    "VALUES (:u,:cash,:baseline) RETURNING id"
                ),
                {"u": uid, "cash": Decimal(cash), "baseline": Decimal(baseline)},
            )
        ).scalar_one()
        owners.append(uid)
        roots.append(root)
        await conn.execute(
            text(
                "INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) "
                "VALUES (:u,:c,0.00123456,123.46),(:u,:s,4,20)"
            ),
            {"u": uid, "c": crypto, "s": stock},
        )
        await conn.execute(
            text("""INSERT INTO trades
            (user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
             exec_price,fee,cash_delta,cash_after,idempotency_key)
            VALUES (:u,:c,'buy','quantity',0.00123456,0.00123456,99900,
             TIMESTAMPTZ '2026-10-01 12:00:00+00',100000,0,-123.46,:cash,:key)"""),
            {"u": uid, "c": crypto, "cash": Decimal(cash), "key": uuid4()},
        )
        tid = await insert_trade(conn, stock, uid)
        trade_ids.append(tid)
        await conn.execute(
            text("""INSERT INTO stock_fill_facts
            (trade_id,coin_id,user_id,provider_asset_id,symbol,company_name,listing_exchange,
             source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,observed_at,
             session_date,opens_at,closes_at,authority)
            SELECT id,coin_id,user_id,'fixture-asset','AAPL','Saved company','NASDAQ',
             'alpaca','iex',10,10,10,2,price_as_of,price_as_of,price_as_of,
             (price_as_of AT TIME ZONE 'UTC')::date,price_as_of-interval '1 hour',
             price_as_of+interval '1 hour','{}'::jsonb FROM trades WHERE id=:t"""),
            {"t": tid},
        )
        await movement(conn, stock, uid, seq=len(owners), kind="fill", trade=tid, key=f"fill:{tid}")
    eid, _, rid = await event(conn, stock)
    sid = (
        await conn.execute(
            text("""INSERT INTO stock_split_applications
        (coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,
         new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at)
        VALUES (:c,:e,:r,'2','1',now(),0,1,2,:before,:after,now()) RETURNING id"""),
            {
                "c": stock,
                "e": eid,
                "r": rid,
                "before": legacy_digest([[u, "2.00000000", "20.00000000"] for u in owners]),
                "after": legacy_digest([[u, "4.00000000", "20.00000000"] for u in owners]),
            },
        )
    ).scalar_one()
    for i, uid in enumerate(owners):
        await movement(
            conn,
            stock,
            uid,
            seq=3 + i,
            q=Decimal(2),
            before=Decimal(2),
            after=Decimal(4),
            bb=Decimal(20),
            ab=Decimal(20),
            epoch=1,
            kind="split",
            app=sid,
            key=f"split:{sid}:{uid}",
        )
    # One paid/corrected dividend and a separate earned-but-unpaid entitlement.
    for i, uid in enumerate(owners):
        de, _, dr = await event(conn, stock)
        en = (
            await conn.execute(
                text("""INSERT INTO stock_dividend_entitlements
            (event_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,
             last_movement_sequence,eligible_quantity,state,fingerprint)
            VALUES (:e,:u,:r,now(),'exclusive',1,'shares',1,900000002,4,'eligible',:f)
            RETURNING id"""),
                {"e": de, "u": uid, "r": dr, "f": "b" * 64},
            )
        ).scalar_one()
        if i == 0:
            terms = {
                "event_id": de,
                "coin_id": stock,
                "user_id": uid,
                "revision_id": dr,
                "revision_fingerprint": "a" * 64,
                "entitlement_id": en,
                "entitlement_fingerprint": "b" * 64,
            }
            pid = await payment(conn, terms)
            await decision(conn, terms, pid)
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    return LegacyBooks(tuple(owners), tuple(roots), crypto, stock, tuple(trade_ids), sid)


@dataclass(frozen=True)
class PortfolioWorld:
    empty_owner: int
    single_owner: int
    owner: int
    foreign_owner: int
    single: int
    first: int
    sibling: int
    closed: int
    foreign: int
    crypto: int


async def seed_portfolio_world(conn: AsyncConnection) -> PortfolioWorld:
    """Final-schema test seeding authenticated as migrator, not public creation."""
    assert (await conn.execute(text("SELECT session_user"))).scalar_one() == "birja_migrator"
    owners = []
    for label in ("empty", "single", "strategies", "foreign"):
        owners.append(
            (
                await conn.execute(
                    text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                    {"e": f"{label}-{uuid4()}@example.test"},
                )
            ).scalar_one()
        )
    roots = []
    for owner, name, cash, closed in (
        (owners[1], "Only strategy", "9876.54", False),
        (owners[2], "Strategy A", "1234.56", False),
        (owners[2], "Strategy B", "4321.09", False),
        (owners[2], "Ended strategy", "55.55", True),
        (owners[3], "Foreign strategy", "777.77", False),
    ):
        roots.append(
            (
                await conn.execute(
                    text("""INSERT INTO accounts
            (user_id,name,cash,starting_cash,closed_at)
            VALUES (:u,:n,:cash,10000,CASE WHEN :closed THEN clock_timestamp() ELSE NULL END)
            RETURNING id"""),
                    {"u": owner, "n": name, "cash": Decimal(cash), "closed": closed},
                )
            ).scalar_one()
        )
    crypto = (await conn.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
    for root, quantity, basis in ((roots[1], "0.1", "123.00"), (roots[2], "0.2", "456.00")):
        await conn.execute(
            text("""INSERT INTO holdings
            (portfolio_id,user_id,coin_id,quantity,cost_basis) VALUES (:p,:u,:c,:q,:b)"""),
            {"p": root, "u": owners[2], "c": crypto, "q": Decimal(quantity), "b": Decimal(basis)},
        )
    return PortfolioWorld(*owners, *roots, crypto)


@pytest_asyncio.fixture
async def portfolio_world(engine: AsyncEngine, migrated: None):
    """Private final-schema matrix; all financial changes roll back after a case."""
    migrator = create_async_engine(test_migration_url())
    try:
        async with migrator.connect() as conn:
            tx = await conn.begin()
            try:
                world = await seed_portfolio_world(conn)
                yield conn, world
            finally:
                await tx.rollback()
    finally:
        await migrator.dispose()


async def seed_owned_crypto_trade(
    conn: AsyncConnection, world: PortfolioWorld, root: int, key=None
) -> tuple[int, object]:
    key = key or uuid4()
    tid = (
        await conn.execute(
            text("""INSERT INTO trades
        (portfolio_id,user_id,coin_id,side,input_kind,input_value,quantity,mid_price,
         price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key)
        VALUES (:p,:u,:c,'buy','quantity',0.001,0.001,50000,clock_timestamp(),
         50000,0.25,-50.25,1184.31,:key) RETURNING id"""),
            {"p": root, "u": world.owner, "c": world.crypto, "key": key},
        )
    ).scalar_one()
    return tid, key


def portfolio_session(conn: AsyncConnection) -> AsyncSession:
    return AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
