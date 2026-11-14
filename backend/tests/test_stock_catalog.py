"""Catalogue seed identity, default denial and protected rollback behavior."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.test_stock_migrations import migrate

EXPECTED = [
    ("AAPL", "Apple", "NASDAQ"),
    ("MSFT", "Microsoft", "NASDAQ"),
    ("NVDA", "NVIDIA", "NASDAQ"),
    ("AMZN", "Amazon", "NASDAQ"),
    ("GOOGL", "Alphabet Class A", "NASDAQ"),
    ("META", "Meta Platforms", "NASDAQ"),
    ("TSLA", "Tesla", "NASDAQ"),
    ("AVGO", "Broadcom", "NASDAQ"),
    ("AMD", "Advanced Micro Devices", "NASDAQ"),
    ("COST", "Costco", "NASDAQ"),
    ("JPM", "JPMorgan Chase", "NYSE"),
    ("V", "Visa", "NYSE"),
    ("JNJ", "Johnson & Johnson", "NYSE"),
    ("PG", "Procter & Gamble", "NYSE"),
    ("KO", "Coca-Cola", "NYSE"),
    ("XOM", "ExxonMobil", "NYSE"),
    ("CVX", "Chevron", "NYSE"),
    ("HD", "Home Depot", "NYSE"),
    ("MCD", "McDonald's", "NYSE"),
    ("DIS", "Walt Disney", "NYSE"),
]


async def _catalogue(engine: AsyncEngine) -> list[tuple]:
    async with engine.connect() as conn:
        return [
            tuple(row)
            for row in (
                await conn.execute(
                    text("""SELECT
            c.symbol,c.name,s.listing_exchange,c.id,c.sort_order,c.kraken_pair,
            s.provider_asset_id,s.provider_verified_at,s.currency,s.security_type,
            s.source,s.source_ref FROM coins c JOIN stock_instruments s ON s.coin_id=c.id
            WHERE c.asset_class='stock' ORDER BY c.sort_order,c.id""")
                )
            ).all()
        ]


async def _crypto(engine: AsyncEngine) -> list[tuple]:
    async with engine.connect() as conn:
        return [
            tuple(row)
            for row in (
                await conn.execute(
                    text("""SELECT id,symbol,name,
            kraken_pair,sort_order,is_active FROM coins WHERE asset_class='crypto' ORDER BY id""")
                )
            ).all()
        ]


async def test_exact_twenty_stock_identities_default_unverified(
    engine: AsyncEngine, clean_stock_discovery: None
) -> None:
    stocks = await _catalogue(engine)
    assert [row[:3] for row in stocks] == EXPECTED
    assert [row[4] for row in stocks] == list(range(1, 21))
    assert len({row[3] for row in stocks}) == 20
    assert all(row[5:8] == (None, None, None) for row in stocks)
    assert all(row[8:11] == ("USD", "common_stock", "sec") for row in stocks)
    assert all(
        row[11] == "https://www.sec.gov/files/company_tickers_exchange.json" for row in stocks
    )
    assert len(await _crypto(engine)) == 15
    async with engine.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT count(*) FROM stock_data_admissions WHERE state='approved'")
            )
        ).scalar_one() == 0
        assert (await conn.execute(text("SELECT count(*) FROM stock_quotes"))).scalar_one() == 0


async def test_seed_repeat_and_rollback_preserve_crypto(
    engine: AsyncEngine, migrated: None
) -> None:
    before_crypto = await _crypto(engine)
    before_stocks = await _catalogue(engine)
    await migrate("head")
    assert await _catalogue(engine) == before_stocks
    await migrate("0009", down=True)
    try:
        assert await _catalogue(engine) == []
        assert await _crypto(engine) == before_crypto
    finally:
        await migrate("head")
    assert [row[:3] for row in await _catalogue(engine)] == EXPECTED
    assert await _crypto(engine) == before_crypto


@pytest.mark.parametrize("financial_table", ["holdings", "trades"])
async def test_seed_downgrade_refuses_financial_loss(
    engine: AsyncEngine, migrated: None, financial_table: str
) -> None:
    # Exercise0010's seed guard specifically. Successor accounting revisions
    # have their own earlier, stricter financial downgrade guard.
    await migrate("0010", down=True)
    async with engine.begin() as conn:
        cid = (
            await conn.execute(
                text("SELECT id FROM coins WHERE asset_class='stock' AND symbol='AAPL'")
            )
        ).scalar_one()
        uid = (
            await conn.execute(
                text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                {"e": f"seed-guard-{financial_table}@example.test"},
            )
        ).scalar_one()
        if financial_table == "holdings":
            await conn.execute(
                text(
                    "INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) VALUES (:u,:c,1,10)"
                ),
                {"u": uid, "c": cid},
            )
        else:
            await conn.execute(
                text("""INSERT INTO trades
                (user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
                 exec_price,fee,cash_delta,cash_after,idempotency_key)
                VALUES (:u,:c,'buy','quantity',1,1,10,now(),10,0,-10,9990,gen_random_uuid())"""),
                {"u": uid, "c": cid},
            )
    before = await _catalogue(engine)
    try:
        with pytest.raises(DBAPIError, match="stock financial references prevent seed downgrade"):
            await migrate("0009", down=True)
        assert await _catalogue(engine) == before
    finally:
        async with engine.begin() as conn:
            for table in ("holdings", "trades"):
                await conn.execute(text(f"DELETE FROM {table} WHERE user_id=:u"), {"u": uid})  # noqa: S608 - fixed allowlist
            await conn.execute(text("DELETE FROM users WHERE id=:u"), {"u": uid})
        await migrate("head")
