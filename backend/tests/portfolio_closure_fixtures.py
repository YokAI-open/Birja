"""Synthetic retained0020 books and independent byte/value preservation oracle."""

from datetime import timedelta
from uuid import uuid4

from sqlalchemy import text


async def seed_public_stock_positions(api, coin_id, at, positions):
    """Declared prehistory on public-created roots, never a closure shortcut.

    Each tuple is(owner, root, quantity, basis); the existing global tail is
    preserved and exact synthetic opening movements follow the same stock gate.
    Trading/deletion acceptance still uses the production HTTP endpoints.
    """
    from decimal import Decimal

    from sqlalchemy.ext.asyncio import AsyncSession

    from tests.stock_action_fixtures import synthetic_opening

    async with api.migrator.begin() as conn:
        await conn.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended("
                "'birja.stock.instrument:' || CAST(:c AS text),0))"
            ),
            {"c": str(coin_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO stock_action_state(coin_id,admission_generation,"
                "journal_start_at,complete_from) VALUES (:c,1,:at,:at) "
                "ON CONFLICT(coin_id) DO NOTHING"
            ),
            {"c": coin_id, "at": at - timedelta(days=1)},
        )
        sequence = (
            await conn.execute(
                text(
                    "SELECT coalesce(max(sequence),0) FROM stock_ownership_movements "
                    "WHERE coin_id=:c"
                ),
                {"c": coin_id},
            )
        ).scalar_one()
        async with AsyncSession(bind=conn, join_transaction_mode="create_savepoint") as db:
            for index, (owner, root, quantity, basis) in enumerate(positions, 1):
                await synthetic_opening(
                    db,
                    coin_id,
                    owner,
                    at,
                    quantity=Decimal(quantity),
                    basis=Decimal(basis),
                    sequence=sequence + index,
                    portfolio_id=int(root),
                )
            await db.commit()


async def frozen_financial_snapshot(conn, portfolio_id):
    """Independent root-only oracle; shared market evidence/tails may advance."""
    result = {}
    tables = (
        "accounts",
        "holdings",
        "trades",
        "portfolio_creations",
        "stock_ownership_movements",
        "stock_dividend_entitlements",
        "stock_dividend_payments",
        "stock_dividend_decisions",
        "portfolio_stock_closures",
        "portfolio_lifecycle_closures",
        "portfolio_closure_intents",
    )
    for table in tables:
        key = "id" if table == "accounts" else "portfolio_id"
        result[table] = tuple(
            (
                await conn.execute(
                    text(
                        f'SELECT to_jsonb(t)::text FROM public."{table}" t '  # noqa: S608 - fixed inventory
                        f"WHERE {key}=:p ORDER BY to_jsonb(t)::text"
                    ),
                    {"p": portfolio_id},
                )
            ).scalars()
        )
    result["stock_fill_facts"] = tuple(
        (
            await conn.execute(
                text(
                    "SELECT to_jsonb(f)::text FROM stock_fill_facts f "
                    "JOIN trades t ON t.id=f.trade_id "
                    "WHERE t.portfolio_id=:p ORDER BY f.trade_id"
                ),
                {"p": portfolio_id},
            )
        ).scalars()
    )
    return result


async def retained_snapshot(conn):
    """All original rows and sequence states, including lifecycle cutoff metadata."""
    from tests.test_migrations import MIGRATION_TABLES

    result = {}
    for table in sorted(MIGRATION_TABLES - {"alembic_version"}):
        result[table] = tuple(
            (
                await conn.execute(
                    text(
                        f'SELECT to_jsonb(t)::text FROM public."{table}" t '  # noqa: S608
                        "ORDER BY to_jsonb(t)::text"
                    )
                )
            ).scalars()
        )
    sequences = (
        await conn.execute(
            text("""SELECT c.relname FROM pg_class c
        JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' AND c.relkind='S'
        AND c.relname NOT IN
          ('portfolio_closure_intents_id_seq','portfolio_lifecycle_closures_id_seq')
        ORDER BY c.relname""")
        )
    ).scalars()
    for sequence in sequences:
        assert sequence in {f"{table}_id_seq" for table in MIGRATION_TABLES}
        result[sequence] = tuple(
            (
                await conn.execute(
                    text(
                        f'SELECT last_value,is_called FROM public."{sequence}"'  # noqa: S608
                    )
                )
            ).one()
        )
    return result


async def seed_retained_books(conn, new_root):
    """One sold-out+held multi-stock root; active siblings and crypto/empty roots.

    These are declared privileged HISTORICAL fixtures at0020, not public deletion
    acceptance. Every stock sale has real immutable trade/facts/movement lineage.
    """
    assert (
        await conn.execute(text("SELECT version_num FROM alembic_version"))
    ).scalar_one() == "0020"
    roots = [await new_root(conn) for _ in range(5)]
    stocks = list(
        (
            await conn.execute(
                text("SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 2")
            )
        ).scalars()
    )
    now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
    at = now - timedelta(days=10)
    for coin in stocks:
        await conn.execute(
            text("""INSERT INTO stock_action_state
            (coin_id,admission_generation,journal_start_at,complete_from)
            VALUES (:c,1,:at,:at)"""),
            {"c": coin, "at": at - timedelta(days=1)},
        )
    for coin, entries in ((stocks[0], [(0, 1, 2), (1, 2, 3)]), (stocks[1], [(0, 1, 1)])):
        for index, sequence, quantity in entries:
            owner, portfolio = roots[index]
            await conn.execute(
                text("""INSERT INTO holdings
                (user_id,portfolio_id,coin_id,quantity,cost_basis) VALUES (:u,:p,:c,:q,:basis)"""),
                {"u": owner, "p": portfolio, "c": coin, "q": quantity, "basis": quantity * 10},
            )
            await conn.execute(
                text("""INSERT INTO stock_ownership_movements
                (user_id,portfolio_id,coin_id,sequence,economic_at,recorded_at,
                quantity,before_quantity,after_quantity,before_basis,after_basis,
                unit_epoch,cause_kind,causal_key)
                VALUES (:u,:p,:c,:seq,:at,:at,:q,0,:q,0,:basis,0,'opening',:key)"""),
                {
                    "u": owner,
                    "p": portfolio,
                    "c": coin,
                    "seq": sequence,
                    "at": at,
                    "q": quantity,
                    "basis": quantity * 10,
                    "key": f"opening:{portfolio}:{coin}",
                },
            )
    owner, portfolio = roots[0]
    sale_at = at + timedelta(days=1)
    trade = (
        await conn.execute(
            text("""INSERT INTO trades
        (user_id,portfolio_id,coin_id,side,input_kind,input_value,quantity,mid_price,
        price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key)
        VALUES (:u,:p,:c,'sell','quantity',2,2,10,:at,10,0,20,8785.43,:key) RETURNING id"""),
            {"u": owner, "p": portfolio, "c": stocks[0], "at": sale_at, "key": uuid4()},
        )
    ).scalar_one()
    await conn.execute(
        text("""INSERT INTO stock_fill_facts
        (trade_id,portfolio_id,coin_id,user_id,provider_asset_id,symbol,company_name,
        listing_exchange,source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,
        observed_at,session_date,opens_at,closes_at,authority)
        SELECT t.id,t.portfolio_id,t.coin_id,t.user_id,'fixture-asset',c.symbol,
        c.name,i.listing_exchange,'alpaca','iex',10,10,10,0,:at,:at,:at,
        CAST(:at AS timestamptz)::date,CAST(:at AS timestamptz)-interval '1 hour',
        CAST(:at AS timestamptz)+interval '1 hour','{}'::jsonb
        FROM trades t JOIN stock_instruments i ON i.coin_id=t.coin_id
        JOIN coins c ON c.id=t.coin_id WHERE t.id=:t"""),
        {"at": sale_at, "t": trade},
    )
    await conn.execute(
        text("""INSERT INTO stock_ownership_movements
        (user_id,portfolio_id,coin_id,sequence,economic_at,recorded_at,quantity,
        before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,
        causal_key,trade_id) VALUES (:u,:p,:c,3,:at,:at,-2,2,0,20,0,0,'fill',:key,:t)"""),
        {
            "u": owner,
            "p": portfolio,
            "c": stocks[0],
            "at": sale_at,
            "key": f"fill:{trade}",
            "t": trade,
        },
    )
    await conn.execute(
        text("UPDATE holdings SET quantity=0,cost_basis=0 WHERE portfolio_id=:p AND coin_id=:c"),
        {"p": portfolio, "c": stocks[0]},
    )
    await conn.execute(text("UPDATE accounts SET cash=8785.43 WHERE id=:p"), {"p": portfolio})
    # Add a later instrument-global tail belonging to a different active root.
    observer, observer_root = roots[2]
    await conn.execute(
        text("""INSERT INTO holdings(user_id,portfolio_id,coin_id,quantity,cost_basis)
        VALUES (:u,:p,:c,1,10)"""),
        {"u": observer, "p": observer_root, "c": stocks[0]},
    )
    await conn.execute(
        text("""INSERT INTO stock_ownership_movements
        (user_id,portfolio_id,coin_id,sequence,economic_at,recorded_at,quantity,
        before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key)
        VALUES (:u,:p,:c,4,:at,:at,1,0,1,0,10,0,'opening',:key)"""),
        {
            "u": observer,
            "p": observer_root,
            "c": stocks[0],
            "at": sale_at + timedelta(days=1),
            "key": f"opening:{observer_root}:{stocks[0]}",
        },
    )
    crypto_owner, crypto_root = roots[3]
    await conn.execute(
        text("""INSERT INTO holdings(user_id,portfolio_id,coin_id,quantity,cost_basis)
        SELECT :u,:p,id,0.00123456,123.46 FROM coins WHERE symbol='BTC'"""),
        {"u": crypto_owner, "p": crypto_root},
    )
    # Check deferred fill facts BEFORE closing its owning root.
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    await conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    for index in (0, 3, 4):
        uid, pid = roots[index]
        await conn.execute(
            text("UPDATE accounts SET closed_at=:at WHERE id=:p"), {"at": now, "p": pid}
        )
        if index == 0:
            for coin in stocks:
                await conn.execute(
                    text("""INSERT INTO portfolio_stock_closures
                    (user_id,portfolio_id,coin_id,closed_at,closing_sequence,unit_epoch)
                    SELECT :u,:p,:c,:at,max(sequence),0 FROM stock_ownership_movements
                    WHERE coin_id=:c"""),
                    {"u": uid, "p": pid, "c": coin, "at": now},
                )
    return {"roots": roots, "stocks": stocks, "closed": [roots[i][1] for i in (0, 3, 4)]}
