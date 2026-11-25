"""Catalog orders against the disposable 0026 ledger as the restricted app."""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import StockDataAdmission, StockSession
from app.schemas.stock_catalog_quotes import CatalogConfirmIn, CatalogOrderIn
from app.schemas.stock_trades import TradeIn
from app.services import stock_catalog_trading, stock_sessions, stock_trading, trading
from app.services.portfolios import OwnedActivePortfolio
from app.services.trade_math import TradeRefused
from tests.test_migrations import install_current_test_grants
from tests.test_stock_catalog_promotion import FIRST_ASSET, _listing, _promote, _reviewed_grant
from tests.test_stock_catalog_promotion import finance_0025 as finance_0025
from tests.test_stock_catalog_promotion import finance_0026 as finance_0026
from tests.test_stock_catalog_publish import _manifest, _publish
from tests.test_stock_catalog_sql_authority import execution_market as execution_market
from tests.test_stock_sessions import evidence


@pytest_asyncio.fixture
async def catalog_market(execution_market, finance_0026, settings, monkeypatch):
    market = execution_market
    today = market["session"]
    day = timedelta(days=1)
    bounds = (
        (today, market["opens"], market["end"]),
        (today + day, market["opens"] + day, market["end"] + day),
    )
    # The fixture calendar surrounds real database time. The normal session
    # decision, wall-clock expiry, role grants and ledger checks still run.
    monkeypatch.setattr(stock_sessions, "_calendar_bounds", lambda *_: bounds)
    reviewed = evidence(market["now"])
    reviewed = replace(
        reviewed,
        generation=1,
        valid_until=market["end"],
        calendar={**reviewed.calendar, "review_valid_until": market["end"].isoformat()},
    )
    async with finance_0026.begin() as db:
        await db.execute(delete(StockDataAdmission).where(StockDataAdmission.product == "calendar"))
        db.add(StockDataAdmission(**asdict(reviewed)))
        await db.execute(delete(StockSession))
        for session in stock_sessions.build_sessions(market["now"], reviewed):
            db.add(StockSession(**asdict(session)))
        await db.execute(
            text("""
            INSERT INTO stock_catalog_financial_quotes
              (coin_id,catalog_id,listing_id,provider_asset_id,
              provider_admission_id,execution_admission_id,bid,ask,unit_epoch,event_at,collected_at,
              observed_at,session_date,calendar_generation,opens_at,closes_at,valid_until)
            VALUES (:c,:catalog,:listing,:asset,:provider,:execution,9.995,10.005,0,
              CAST(:now AS timestamptz)-interval '1 second',:now,:now,:session,1,:opens,:end,:end)
        """),
            market,
        )
        market["sibling"] = await db.scalar(
            text("SELECT id FROM accounts WHERE user_id=:u AND name='Strategy B'"), market
        )
    await install_current_test_grants()
    return {**market, "settings": settings.model_copy(update={"stock_data_enabled": True})}


@asynccontextmanager
async def _app(engine):
    async with engine.connect() as conn:
        await conn.execute(text("SET ROLE birja_app"))
        await conn.commit()
        try:
            async with AsyncSession(bind=conn, expire_on_commit=False) as db:
                yield db
        finally:
            await conn.rollback()
            await conn.execute(text("RESET ROLE"))
            await conn.commit()


def _preview_input(market):
    return CatalogOrderIn.model_validate(
        {"listing_version": str(market["listing"]), "side": "buy", "quantity": "1"}
    )


def _confirmation(market, **changes):
    return CatalogConfirmIn.model_validate(
        {
            "listing_version": str(market["listing"]),
            "side": "buy",
            "quantity": "1",
            "expected_exec_price": "10.005",
            "idempotency_key": uuid4(),
        }
        | changes
    )


def _portfolio(market):
    return OwnedActivePortfolio(market["p"], market["u"])


async def _confirm(engine, market, order, **overrides):
    context = {
        "portfolio": _portfolio(market),
        "catalog_id": market["catalog"],
        "order": order,
        "settings": market["settings"],
    } | overrides
    async with _app(engine) as db:
        return await stock_catalog_trading.execute(db, **context)


async def test_catalog_buy_sell_and_exact_original_replay(engine, catalog_market, finance_0026):
    market = catalog_market
    buy = _confirmation(market)
    async with _app(engine) as db:
        preview = await stock_catalog_trading.quote(
            db,
            portfolio=_portfolio(market),
            catalog_id=market["catalog"],
            order=_preview_input(market),
            settings=market["settings"],
        )
    assert (preview.exec_price, preview.cash_after, preview.held_after, preview.fee) == (
        Decimal("10.005"),
        Decimal("1224.56"),
        Decimal(1),
        Decimal(0),
    )
    first, second = await asyncio.gather(
        _confirm(engine, market, buy), _confirm(engine, market, buy)
    )
    assert (first[1], second[1]) in ((True, False), (False, True))
    original = first[0]
    assert original == second[0] and original.cash_after == preview.cash_after
    async with finance_0026() as db:
        basis = await db.scalar(
            text("SELECT cost_basis FROM holdings WHERE coin_id=:c AND portfolio_id=:p"), market
        )
        assert basis == Decimal("10")
    sell, created = await _confirm(
        engine, market, _confirmation(market, side="sell", expected_exec_price="9.995")
    )
    assert created and (sell.held_after, sell.cash_after, sell.fee) == (
        Decimal(0),
        Decimal("1234.56"),
        Decimal(0),
    )
    async with finance_0026() as db:
        assert await db.scalar(text("SELECT count(*) FROM stock_catalog_fill_evidence")) == 2
        prior_generation = await db.scalar(
            text("SELECT id FROM stock_catalog_generations WHERE is_active")
        )
    now = market["now"] + timedelta(seconds=1)
    generation = await _publish(
        finance_0026, _manifest(now, nasdaq=(("FQR", "fixture-nasdaq"),)), prior_generation, now=now
    )
    renamed = await _listing(finance_0026, generation.generation_id, "FQR")
    grant = await _reviewed_grant(finance_0026, renamed, FIRST_ASSET, now)
    bound = await _promote(finance_0026, renamed, grant, now)
    assert bound.coin_id == market["c"] and bound.catalog_id == market["catalog"]
    assert await _confirm(engine, market, buy) == (original, False)
    with pytest.raises(TradeRefused) as changed_version:
        await _confirm(engine, market, buy.model_copy(update={"listing_version": renamed.id}))
    assert changed_version.value.code == "idempotency_conflict"
    with pytest.raises(TradeRefused) as invalid_price:
        await _confirm(engine, market, buy.model_copy(update={"expected_exec_price": Decimal(10)}))
    assert invalid_price.value.code == "idempotency_conflict"
    with pytest.raises(TradeRefused) as invalid_root:
        await _confirm(
            engine, market, buy, portfolio=OwnedActivePortfolio(market["sibling"], market["u"])
        )
    assert invalid_root.value.code == "idempotency_conflict"
    async with _app(engine) as db:
        with pytest.raises(TradeRefused) as legacy:
            await stock_trading.execute(
                db,
                portfolio=_portfolio(market),
                settings=market["settings"],
                order=TradeIn.model_validate(
                    {
                        "symbol": original.symbol,
                        "side": "buy",
                        "quantity": "1",
                        "expected_exec_price": "10.005",
                        "idempotency_key": buy.idempotency_key,
                    }
                ),
            )
    assert legacy.value.code == "idempotency_conflict"


async def test_catalog_reprice_then_reconfirm_and_refuse_expired_quote(
    engine, catalog_market, finance_0026
):
    market = catalog_market
    order = _confirmation(market, expected_exec_price="10")
    with pytest.raises(stock_catalog_trading.CatalogPriceChanged) as moved:
        await _confirm(engine, market, order)
    assert moved.value.detail.quote.exec_price == Decimal("10.005")
    assert moved.value.detail.cash_delta_change == Decimal(0)
    async with finance_0026() as db:
        assert await db.scalar(text("SELECT count(*) FROM stock_catalog_fill_evidence")) == 0
    replacement = order.model_copy(update={"expected_exec_price": Decimal("10.005")})
    assert (await _confirm(engine, market, replacement))[1]
    async with finance_0026.begin() as db:
        await db.execute(
            text("""
            UPDATE stock_catalog_financial_quotes
            SET event_at=CAST(:now AS timestamptz)-interval '120 seconds' WHERE coin_id=:c
        """),
            market,
        )
    with pytest.raises(TradeRefused) as stale:
        await _confirm(engine, market, _confirmation(market))
    assert stale.value.code == "quote_stale"


async def test_catalog_and_crypto_compete_for_one_portfolio_cash(
    engine, catalog_market, finance_0026
):
    market = catalog_market
    async with finance_0026.begin() as db:
        await db.execute(text("UPDATE accounts SET cash=15 WHERE id=:p"), market)
        await db.execute(
            text("""
            INSERT INTO prices (coin_id,mid,as_of,source)
            SELECT id,50000,clock_timestamp(),'fake' FROM coins
            WHERE symbol='BTC' AND asset_class='crypto'
        """)
        )

    async def buy_crypto():
        async with _app(engine) as db:
            return await trading.execute(
                db,
                portfolio=_portfolio(market),
                order=trading.Order("BTC", "buy", "usd", Decimal(10)),
                expected_mid=Decimal(50000),
                idempotency_key=uuid4(),
                settings=market["settings"],
            )

    results = await asyncio.gather(
        _confirm(engine, market, _confirmation(market)), buy_crypto(), return_exceptions=True
    )
    assert sum(isinstance(result, tuple) for result in results) == 1
    faults = [result for result in results if isinstance(result, BaseException)]
    assert len(faults) == 1 and isinstance(faults[0], TradeRefused)
    assert faults[0].code == "insufficient_cash"
    async with finance_0026() as db:
        assert await db.scalar(text("SELECT cash FROM accounts WHERE id=:p"), market) == Decimal(5)
        assert (
            await db.scalar(text("SELECT count(*) FROM trades WHERE portfolio_id=:p"), market) == 1
        )


async def test_catalog_quote_expiry_during_account_lock_refuses(
    engine, catalog_market, finance_0026, monkeypatch
):
    market = catalog_market
    async with finance_0026.begin() as db:
        await db.execute(
            text("""
            UPDATE stock_catalog_financial_quotes
            SET valid_until=clock_timestamp()+interval '1 second' WHERE coin_id=:c
        """),
            market,
        )
    original_account = stock_catalog_trading._account
    requested = asyncio.Event()

    async def at_lock(db, portfolio, *, lock=False):
        if lock:
            requested.set()
        return await original_account(db, portfolio, lock=lock)

    monkeypatch.setattr(stock_catalog_trading, "_account", at_lock)
    async with finance_0026.begin() as blocker:
        await blocker.execute(text("SELECT id FROM accounts WHERE id=:p FOR UPDATE"), market)
        attempt = asyncio.create_task(_confirm(engine, market, _confirmation(market)))
        await asyncio.wait_for(requested.wait(), timeout=3)
        await blocker.execute(text("SELECT pg_sleep(1.1)"))
        assert not attempt.done()
    with pytest.raises(TradeRefused) as expired:
        await attempt
    assert expired.value.code == "quote_stale"
    async with finance_0026() as db:
        assert await db.scalar(text("SELECT count(*) FROM stock_catalog_fill_evidence")) == 0
