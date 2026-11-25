"""Owned catalog valuation against real schema and restricted test roles."""

from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import event, null, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2.portfolios import PortfolioOverview
from app.models.corporate_action import StockActionState
from app.models.stock import StockDataAdmission, StockSession
from app.models.stock_catalog import StockCatalogAdmission
from app.models.stock_catalog_finance import (
    StockCatalogActionCoverage,
    StockCatalogFinancialQuote,
    StockCatalogStatus,
)
from app.models.trade import Holding
from app.schemas.portfolio import PortfolioOut
from app.services import portfolio as portfolio_service
from app.services import stock_valuation
from app.services.portfolio import get_portfolio, load_portfolio_snapshots
from app.services.portfolios import OwnedActivePortfolio
from app.services.stock_catalog_promotion import CATALOG_ACTION_FIELDS
from app.services.stock_eligibility import execution_snapshot_query
from app.services.stock_sessions import SessionDecision
from tests.test_migrations import install_current_test_grants
from tests.test_stock_catalog_promotion import FIRST_ASSET, _listing, _promote, _reviewed_grant
from tests.test_stock_catalog_publish import _manifest, _publish
from tests.test_stock_catalog_quote_scheduler import _financial_request_and_tick
from tests.test_stock_catalog_quote_scheduler import finance_0025 as finance_0025
from tests.test_stock_catalog_quote_scheduler import finance_0026 as finance_0026
from tests.test_stock_catalog_quote_scheduler import financial_market as financial_market
from tests.test_stock_catalog_trading import _app


@pytest_asyncio.fixture
async def catalog_book(financial_market, settings):
    market = financial_market
    first, foreign = market.instruments
    origin = market.now - timedelta(minutes=10)
    deadline = market.now + timedelta(hours=1)
    async with market.factory.begin() as db:
        for binding, portfolio_id, owner_id in (
            (first, market.world.first, market.world.owner),
            (foreign, market.world.foreign, market.world.foreign_owner),
        ):
            actions = StockCatalogAdmission(
                artifact="catalog_actions",
                reference="Synthetic valuation scope",
                is_fixture=True,
                reviewed_at=origin,
                valid_until=deadline,
                fields=CATALOG_ACTION_FIELDS,
                scope={
                    "account": binding.account,
                    "server": binding.server,
                    "feed": "alpaca-corporate-actions",
                    "catalog_id": str(binding.catalog_id),
                    "listing_id": str(binding.listing_id),
                    "provider_asset_id": binding.provider_asset_id,
                },
            )
            db.add(actions)
            await db.flush()
            db.add(
                StockCatalogActionCoverage(
                    coin_id=binding.coin_id,
                    catalog_id=binding.catalog_id,
                    listing_id=binding.listing_id,
                    admission_id=actions.id,
                    journal_origin=origin,
                    coverage_start=origin,
                    covered_until=market.now,
                    observed_at=market.now,
                    valid_until=deadline,
                )
            )
            await db.execute(
                update(StockActionState)
                .where(StockActionState.coin_id == binding.coin_id)
                .values(
                    checked_at=market.now,
                    valid_until=deadline,
                    journal_start_at=origin,
                    complete_from=origin,
                    coverage_start=origin,
                    covered_until=market.now,
                    admission_generation=actions.id,
                )
            )
            db.add(
                Holding(
                    coin_id=binding.coin_id,
                    portfolio_id=portfolio_id,
                    user_id=owner_id,
                    quantity=Decimal(2),
                    cost_basis=Decimal("198.50"),
                )
            )
        await db.execute(
            text("INSERT INTO prices(coin_id,mid,as_of,source) VALUES (:c,100,:at,'fake')"),
            {"c": market.world.crypto, "at": market.now},
        )
        await db.execute(
            update(StockCatalogAdmission)
            .where(StockCatalogAdmission.id == first.admission_id)
            .values(valid_until=market.now + timedelta(minutes=2))
        )
    assert (await _financial_request_and_tick(market, first, market.reply))[1:] == ("ready", 1)
    await install_current_test_grants()
    return market, settings.model_copy(update={"stock_data_enabled": True})


async def test_catalog_closed_mark_and_incomplete_scope_use_same_two_owned_reads(
    engine, catalog_book
):
    market, settings = catalog_book
    now = market.now + timedelta(minutes=4)
    owner = market.world.owner
    bound = market.instruments[0]
    portfolio = OwnedActivePortfolio(market.world.first, owner)
    queries = []

    def capture(conn, cursor, statement, parameters, context, many):
        queries.append((statement, parameters))

    async with _app(engine) as db:
        event.listen(engine.sync_engine, "before_cursor_execute", capture)
        try:
            overview = await load_portfolio_snapshots(
                db, owner_id=owner, settings=settings, now=now
            )
        finally:
            event.remove(engine.sync_engine, "before_cursor_execute", capture)
        detail = await get_portfolio(db, portfolio=portfolio, settings=settings, now=now)
    assert len(queries) == 2
    assert market.instruments[1].coin_id not in queries[1][1]
    assert asdict(detail) == asdict(overview[0])
    assert Decimal("1448.56") == detail.known_value == detail.total_value
    assert detail.unvalued_holding_count == 0
    wire = PortfolioOut.from_value(detail).model_dump(mode="json")
    overview_wire = PortfolioOverview.from_value(overview[0]).model_dump(mode="json")
    assert wire["holdings"] == overview_wire["holdings"]
    crypto, stock = wire["holdings"]
    assert "catalog_id" not in crypto and "listing_exchange" not in crypto
    assert (stock["symbol"], stock["catalog_id"], stock["listing_exchange"]) == (
        "FQA",
        str(bound.catalog_id),
        "NASDAQ",
    )
    assert stock["provider_asset_id"] is None and stock["stock_mark"]["authority"] is None
    assert stock["stock_mark"]["mark_mode"] == "closed"
    assert stock["stock_mark"]["event_at"] == stock["as_of"]
    async with market.factory.begin() as db:
        quote = await db.get(StockCatalogFinancialQuote, bound.coin_id)
        assert quote is not None
        mark = await db.get(StockCatalogAdmission, quote.mark_admission_id)
        assert mark is not None
        mark.revoked_at = now
        assert await db.scalar(text("SELECT count(*) FROM stock_catalog_fill_evidence")) == 0
    async with _app(engine) as db:
        incomplete = await get_portfolio(db, portfolio=portfolio, settings=settings, now=now)
    assert (
        incomplete.total_value is incomplete.total_pl is incomplete.cash_allocation_percent is None
    )
    assert incomplete.known_value == Decimal("1244.56") and incomplete.unvalued_holding_count == 1
    holding = next(row for row in incomplete.holdings if row.catalog_id)
    assert holding.cost_basis == Decimal("198.50") and holding.quantity == Decimal(2)
    assert holding.stock_mark and holding.stock_mark.valuation_reason == "permission_unavailable"
    assert all(row.allocation_percent is None for row in incomplete.holdings)


async def test_catalog_halt_keeps_authorized_dated_price_until_report_lease(engine, catalog_book):
    market, settings = catalog_book
    binding = market.instruments[0]
    portfolio = OwnedActivePortfolio(market.world.first, market.world.owner)
    now = market.now + timedelta(seconds=45)
    event_at = market.now - timedelta(seconds=105)
    report_until = now + timedelta(seconds=10)
    permission_until = now + timedelta(seconds=5)
    async with market.factory.begin() as db:
        quote = await db.get(StockCatalogFinancialQuote, binding.coin_id)
        assert quote is not None
        quote.event_at = event_at
        quote.execution_admission_id = None
        grant = StockCatalogAdmission(
            artifact="catalog_halt",
            reference="Synthetic dated halt report",
            is_fixture=True,
            reviewed_at=market.now,
            valid_until=permission_until,
            fields={
                key: ["collection", "execution", "storage", "backup"]
                for key in ("report_digest", "event_at", "valid_until", "state")
            },
            scope={
                "account": binding.account,
                "server": binding.server,
                "catalog_id": str(binding.catalog_id),
                "listing_id": str(binding.listing_id),
                "provider_asset_id": binding.provider_asset_id,
                "feed": "nasdaq-rss",
            },
        )
        db.add(grant)
        await db.flush()
        db.add(
            StockCatalogStatus(
                coin_id=binding.coin_id,
                catalog_id=binding.catalog_id,
                listing_id=binding.listing_id,
                admission_id=grant.id,
                state="halted",
                report_digest="a" * 64,
                event_at=now,
                observed_at=now,
                valid_until=report_until,
                session_date=quote.session_date,
            )
        )

    async with _app(engine) as db:
        halted = await get_portfolio(db, portfolio=portfolio, settings=settings, now=now)
        expired = await get_portfolio(
            db, portfolio=portfolio, settings=settings, now=permission_until
        )
    priced = next(holding for holding in halted.holdings if holding.catalog_id)
    assert priced.current_value == Decimal("204.00")
    assert priced.stock_mark is not None
    assert priced.stock_mark.mark_mode == "halted"
    assert priced.stock_mark.event_at == priced.as_of == event_at
    assert priced.stock_mark.valid_until == permission_until
    unpriced = next(holding for holding in expired.holdings if holding.catalog_id)
    assert unpriced.current_value is None and expired.unvalued_holding_count == 1


async def test_catalog_mark_recheck_keeps_original_price_and_refuses_changed_units(
    engine,
    catalog_book,
    monkeypatch,
):
    market, settings = catalog_book
    portfolio = OwnedActivePortfolio(market.world.first, market.world.owner)
    coin_id = market.instruments[0].coin_id
    now = market.now + timedelta(minutes=4)
    original = AsyncSession.execute
    reads = 0
    writes = (
        (
            update(StockCatalogFinancialQuote)
            .where(StockCatalogFinancialQuote.coin_id == coin_id)
            .values(bid=201, ask=203)
        ),
    )

    async def intercept(db, stmt, *args, **kwargs):
        nonlocal reads
        result = await original(db, stmt, *args, **kwargs)
        reads += 1
        if reads == 1:
            async with market.factory.begin() as writer:
                for write in writes:
                    await original(writer, write)
        return result

    monkeypatch.setattr(AsyncSession, "execute", intercept)
    async with _app(engine) as db:
        first = await get_portfolio(db, portfolio=portfolio, settings=settings, now=now)
    assert reads == 2 and first.total_value == Decimal("1448.56")
    writes = (
        update(StockActionState).where(StockActionState.coin_id == coin_id).values(unit_epoch=1),
    )
    reads = 0
    async with _app(engine) as db:
        second = await get_portfolio(db, portfolio=portfolio, settings=settings, now=now)
    position = next(row for row in second.holdings if row.catalog_id)
    assert reads == 2 and second.total_value is None
    assert position.stock_mark and position.stock_mark.valuation_reason == "units_changed"
    assert position.average_cost is None and position.cost_basis == Decimal("198.50")
    async with market.factory.begin() as writer:
        await original(
            writer,
            update(StockActionState)
            .where(
                StockActionState.coin_id == coin_id,
            )
            .values(unit_epoch=0),
        )
    writes = (
        update(StockCatalogFinancialQuote)
        .where(StockCatalogFinancialQuote.coin_id == coin_id)
        .values(calendar_generation=2),
        update(StockDataAdmission)
        .where(StockDataAdmission.product == "calendar")
        .values(generation=2),
        update(StockSession).values(calendar_admission_generation=2),
    )
    reads = 0
    async with _app(engine) as db:
        third = await get_portfolio(db, portfolio=portfolio, settings=settings, now=now)
    position = next(row for row in third.holdings if row.catalog_id)
    assert reads == 2 and third.total_value is None
    assert position.stock_mark and position.stock_mark.valuation_reason == "session_unavailable"


async def test_catalog_valuation_refuses_incomplete_or_changed_read_evidence(
    engine, catalog_book, monkeypatch
):
    market, settings = catalog_book
    now = market.now + timedelta(minutes=4)
    coin_id = market.instruments[0].coin_id
    async with _app(engine) as db:
        query = execution_snapshot_query(now).add_columns(
            stock_valuation.catalog_valuation_query((coin_id,), settings, now).label("catalog")
        )
        source = (await db.execute(query)).one()
    (row,) = source.catalog
    sessions = stock_valuation.catalog_valuation_sessions(source, settings, now)

    def value(original, current, schedule=sessions):
        return stock_valuation.value_catalog_holding(
            original,
            current,
            original_sessions=schedule,
            current_sessions=sessions,
            settings=settings,
            now=now,
        ).value

    assert value(row, row).mid == Decimal("102")
    quote = row["quote"]
    for changed, expected in (
        ({"quote": quote | {"unit_epoch": quote["unit_epoch"] + 1}}, "units_changed"),
        ({"mapping_until": now.isoformat()}, "permission_unavailable"),
        ({"mapping_reviewed": None}, "permission_unavailable"),
        (
            {
                "mapping_scope": row["mapping_scope"]
                | {"provider": row["mapping_scope"]["provider"] | {"account": "other-fixture"}}
            },
            "permission_unavailable",
        ),
        ({"quote": quote | {"valid_until": now.isoformat()}}, "quote_stale"),
    ):
        snapshot = row | changed
        result = value(snapshot, snapshot)
        assert result.mid is None and result.mark.valuation_reason == expected, expected

    unknown = value(row, row, sessions | {"NASDAQ": (SessionDecision(), None)})
    assert unknown.mid is None and unknown.mark.valuation_reason == "session_unavailable"
    assert value(row, row | {"listing_id": row["listing_id"] + 1}).mid is None
    changed_review = value(row, row | {"mark_id": row["mark_id"] + 1})
    assert changed_review.mid is None and changed_review.mark.units_safe
    changed_attestation = value(row, row | {"quote_attested": False})
    assert changed_attestation.mid is None
    assert changed_attestation.mark.valuation_reason == "permission_unavailable"

    verified_mark = stock_valuation.evaluate_catalog_financial_mark

    def incomplete_mark(*args, **kwargs):
        verified = verified_mark(*args, **kwargs)
        assert verified is not None
        return replace(verified, valid_until=None)

    monkeypatch.setattr(stock_valuation, "evaluate_catalog_financial_mark", incomplete_mark)
    without_deadline = value(row, row)
    assert without_deadline.mid is None and without_deadline.mark.units_safe

    monkeypatch.setattr(portfolio_service, "catalog_valuation_query", lambda *_: null())
    async with _app(engine) as db:
        portfolio = await get_portfolio(
            db,
            portfolio=OwnedActivePortfolio(market.world.first, market.world.owner),
            settings=settings,
            now=now,
        )
    protected = next(holding for holding in portfolio.holdings if holding.coin_id == str(coin_id))
    assert (protected.symbol, protected.name, protected.current_value) == (
        "STOCK",
        "Restricted stock",
        None,
    )
    assert portfolio.total_value is None and portfolio.known_value == Decimal("1244.56")


async def test_catalog_rename_and_reused_ticker_keep_original_owned_issue(engine, catalog_book):
    market, settings = catalog_book
    bound = market.instruments[0]
    renamed_at = market.now + timedelta(minutes=3)
    async with market.factory() as db:
        previous = await db.scalar(text("SELECT id FROM stock_catalog_generations WHERE is_active"))
    updated = await _publish(
        market.factory,
        _manifest(
            renamed_at,
            nasdaq=(("FQR", "fixture-nasdaq"), ("FQA", "replacement-issue")),
        ),
        previous,
        now=renamed_at,
    )
    renamed = await _listing(market.factory, updated.generation_id, "FQR")
    replacement = await _listing(market.factory, updated.generation_id, "FQA")
    assert replacement.security_id != bound.catalog_id and renamed.security_id == bound.catalog_id
    grant = await _reviewed_grant(market.factory, renamed, FIRST_ASSET, renamed_at)
    result = await _promote(market.factory, renamed, grant, renamed_at)
    assert result.coin_id == bound.coin_id
    owner = market.world.owner
    async with _app(engine) as db:
        holding = await get_portfolio(
            db,
            portfolio=OwnedActivePortfolio(market.world.first, owner),
            settings=settings,
            now=renamed_at + timedelta(seconds=1),
        )
        with pytest.raises(HTTPException, match="404"):
            await get_portfolio(
                db,
                portfolio=OwnedActivePortfolio(market.world.foreign, owner),
                settings=settings,
                now=renamed_at + timedelta(seconds=1),
            )
    position = next(row for row in holding.holdings if row.catalog_id)
    assert (position.symbol, position.catalog_id, position.coin_id) == (
        "FQR",
        str(bound.catalog_id),
        str(bound.coin_id),
    )
    assert position.quantity == Decimal(2) and position.mid is None
    assert all(p.symbol != "FQA" for p in holding.holdings)
