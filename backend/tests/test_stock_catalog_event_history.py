"""Owned catalog History retains the label and stable identity of each event."""

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import text

from app.schemas.event_history import EventDividendCorrection, EventTrade
from app.services.corporate_actions import apply_due_actions
from app.services.event_history import list_event_history
from app.services.portfolios import OwnedActivePortfolio
from tests.portfolio_fixtures import portfolio_session
from tests.test_stock_catalog_financial_actions import (
    _derive,
    _dividend,
    _ingest,
    _post,
    _rename_with_current_mapping,
    _scheduler,
)
from tests.test_stock_catalog_financial_actions import action_case as action_case
from tests.test_stock_catalog_financial_actions import scoped_actions as scoped_actions
from tests.test_stock_catalog_promotion import FIRST_ASSET, _listing, _promote, _reviewed_grant
from tests.test_stock_catalog_promotion import finance_0025 as finance_0025
from tests.test_stock_catalog_promotion import finance_0026 as finance_0026
from tests.test_stock_catalog_publish import _manifest, _publish
from tests.test_stock_catalog_trading import _app, _confirm, _confirmation, _portfolio
from tests.test_stock_catalog_trading import catalog_market as catalog_market
from tests.test_stock_catalog_trading import execution_market as execution_market


async def test_owned_catalog_fills_keep_original_ticker_after_reuse(
    engine, finance_0026, catalog_market
):
    market = catalog_market
    buy, created = await _confirm(engine, market, _confirmation(market))
    assert created
    sell, created = await _confirm(
        engine, market, _confirmation(market, side="sell", expected_exec_price="9.995")
    )
    assert created
    async with finance_0026() as db:
        previous = await db.scalar(text("SELECT id FROM stock_catalog_generations WHERE is_active"))
    now = market["now"] + timedelta(seconds=1)
    renamed = await _publish(
        finance_0026, _manifest(now, nasdaq=(("FQR", "fixture-nasdaq"),)), previous, now=now
    )
    listing = await _listing(finance_0026, renamed.generation_id, "FQR")
    grant = await _reviewed_grant(finance_0026, listing, FIRST_ASSET, now)
    binding = await _promote(finance_0026, listing, grant, now)
    assert binding.catalog_id == market["catalog"]
    later = now + timedelta(seconds=1)
    reused = await _publish(
        finance_0026,
        _manifest(later, nasdaq=(("FQR", "fixture-nasdaq"), ("FQA", "fixture-replacement"))),
        renamed.generation_id,
        now=later,
    )
    replacement = await _listing(finance_0026, reused.generation_id, "FQA")
    assert replacement.security_id != binding.catalog_id
    async with _app(engine) as db:
        root = _portfolio(market)
        first = await list_event_history(db, portfolio=root, limit=1)
        assert first.next_cursor is not None
        second = await list_event_history(db, portfolio=root, limit=1, cursor=first.next_cursor)
        assert second.next_cursor is None
        for event, receipt in zip(first.items + second.items, (sell, buy), strict=True):
            assert isinstance(event, EventTrade)
            assert (event.id, event.symbol, event.catalog_id) == (
                f"trade:{receipt.trade_id}",
                "FQA",
                str(binding.catalog_id),
            )
            assert Decimal(event.cash_delta) == receipt.cash_delta
        sibling = OwnedActivePortfolio(market["sibling"], market["u"])
        assert (await list_event_history(db, portfolio=sibling)).items == []
        with pytest.raises(HTTPException) as refused:
            await list_event_history(
                db, portfolio=OwnedActivePortfolio(market["p"], 9223372036854775807)
            )
        assert refused.value.status_code == 404


async def test_catalog_dividend_correction_keeps_original_owned_lineage(scoped_actions):
    conn, case = scoped_actions
    action = _dividend(case)
    payment = await _post(conn, await _derive(conn, case, action))
    renamed = await _rename_with_current_mapping(conn, case)
    corrected = replace(action, symbol=renamed.ticker, rate=Decimal("0.90"))
    await _post(conn, await _derive(conn, case, corrected))
    async with portfolio_session(conn) as db:
        root = OwnedActivePortfolio(case.world.first, case.world.owner)
        page = await list_event_history(db, portfolio=root, limit=1)
        sibling = OwnedActivePortfolio(case.world.sibling, case.world.owner)
        assert (await list_event_history(db, portfolio=sibling)).items == []
    (event,) = page.items
    assert isinstance(event, EventDividendCorrection)
    assert event.catalog_id == event.original.catalog_id == str(case.binding.catalog_id)
    assert event.symbol == event.original.symbol == case.listing.ticker
    assert event.payment_reference == f"dividend:{payment.payment_id}"
    assert Decimal(event.cash_delta) == Decimal("0.80")
    serialized = event.model_dump(mode="json")
    serialized["original"]["catalog_id"] = str(case.binding.catalog_id + 1)
    with pytest.raises(ValidationError, match="Invalid catalog lineage"):
        EventDividendCorrection.model_validate(serialized)


async def test_catalog_split_history_holds_original_units_and_basis(scoped_actions):
    conn, case = scoped_actions
    split = _dividend(
        case,
        event_type="forward_split",
        rate=None,
        units="pre_split",
        economic_at=case.cutoff,
        new_rate=Decimal("2"),
        old_rate=Decimal("1"),
    )
    async with _scheduler(conn) as db, db.begin():
        authority, _ = await _ingest(db, case, split)
        assert await apply_due_actions(db, case.binding.coin_id, catalog=authority)
    await conn.execute(text("SET CONSTRAINTS stock_catalog_split_movements IMMEDIATE"))
    async with portfolio_session(conn) as db:
        root = OwnedActivePortfolio(case.world.first, case.world.owner)
        history = await list_event_history(db, portfolio=root)
    (event,) = history.model_dump(mode="json")["items"]
    assert (event["kind"], event["symbol"], event["name"], event["catalog_id"]) == (
        "split",
        case.listing.ticker,
        case.listing.company_name,
        str(case.binding.catalog_id),
    )
    assert (Decimal(event["quantity_before"]), Decimal(event["quantity_after"])) == (2, 4)
    assert (
        Decimal(event["cost_basis_before"])
        == Decimal(event["cost_basis_after"])
        == Decimal("87.65")
    )


def test_catalog_history_wire_uses_strict_issue_id_and_symbol_without_legacy_key():
    stamp = "2026-11-24T15:00:00.000000Z"
    trade = {
        "kind": "trade",
        "id": "trade:1",
        "recorded_at": stamp,
        "symbol": "4Q.A+/=C",
        "name": "Fixture shares",
        "cash_delta": "-2.50",
        "asset_type": "stock",
        "side": "buy",
        "quantity": "1",
        "exec_price": "2.50",
        "fee": "0",
        "filled_at": stamp,
        "source": "alpaca",
        "feed": "iex",
        "quote_at": stamp,
        "catalog_id": "9223372036854775807",
    }
    assert EventTrade.model_validate(trade).model_dump(mode="json") == trade
    for changes in (
        {"asset_type": "crypto"},
        {"catalog_id": None},
        {"catalog_id": "01"},
        {"catalog_id": "9223372036854775808"},
        {"symbol": "@1"},
    ):
        with pytest.raises(ValidationError):
            EventTrade.model_validate(trade | changes)
    legacy = {name: value for name, value in trade.items() if name != "catalog_id"}
    with pytest.raises(ValidationError, match="Invalid event symbol"):
        EventTrade.model_validate(legacy)
    legacy["symbol"] = "AAPL"
    assert EventTrade.model_validate(legacy).model_dump(mode="json") == legacy
