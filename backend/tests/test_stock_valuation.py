# ruff: noqa: F811
"""Real mixed financial snapshot and independently permitted stock marks."""

from datetime import timedelta
from decimal import Decimal

import pytest

from app.services.portfolio import get_portfolio
from app.services.stock_trading import execute
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case  # noqa: F401
from tests.test_stock_trades_api import stock_http  # noqa: F401
from tests.test_stock_trading_service import trade_order


async def test_actual_stock_fill_is_valued_at_exact_midpoint(stock_trade_case, settings):
    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
        portfolio = await get_portfolio(db, user_id=uid, settings=settings)
    assert portfolio.total_value == Decimal(9998)
    assert portfolio.known_value == Decimal(9998) and portfolio.unvalued_holding_count == 0
    assert portfolio.holdings[0].asset_class == "stock" and portfolio.holdings[0].coin_id == str(
        cid
    )
    assert portfolio.holdings[0].mid == 101 and portfolio.holdings[0].current_value == 202


@pytest.mark.parametrize(
    "mutation,reason,units",
    [
        ("DELETE FROM stock_quotes", "permission_unavailable", True),
        ("UPDATE stock_status_evidence SET state='unknown'", "status_unavailable", True),
        ("UPDATE stock_status_evidence SET state='frozen'", "frozen", True),
        (
            "UPDATE stock_status_evidence SET valid_until=NULL,continuity_current=false",
            "status_unavailable",
            True,
        ),
        ("UPDATE stock_action_state SET health='unknown'", "action_unavailable", False),
        ("UPDATE stock_action_state SET valid_until=NULL", "action_unavailable", False),
        (
            "DELETE FROM stock_sessions WHERE session_date=current_date",
            "session_unavailable",
            False,
        ),
        (
            "UPDATE stock_quotes SET event_at=collected_at-interval '2 hours'",
            "quote_unavailable",
            True,
        ),
        (
            "UPDATE stock_data_admissions SET state='revoked' WHERE product='quotes'",
            "permission_unavailable",
            True,
        ),
        (
            "UPDATE stock_quotes SET event_at=clock_timestamp()-interval '120 seconds'",
            "quote_stale",
            True,
        ),
        (
            (
                "UPDATE stock_data_admissions SET valid_until=valid_until+interval '1 day' "
                "WHERE product='quotes'"
            ),
            "permission_unavailable",
            True,
        ),
    ],
)
async def test_unavailable_stock_never_publishes_partial_totals_or_unsafe_costs(
    stock_trade_case, settings, mutation, reason, units
):
    from sqlalchemy import text

    from tests.test_stock_status import financial_snapshot

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
    async with factory.begin() as db:
        await db.execute(text(mutation))
    before = await financial_snapshot(factory)
    async with factory() as db:
        p = await get_portfolio(db, user_id=uid, settings=settings)
    assert p.known_value == 9796 and p.unvalued_holding_count == 1
    assert p.total_value is p.total_pl is p.total_pl_percent is p.cash_allocation_percent is None
    assert p.class_values.stocks is None and p.class_values.crypto == 0
    assert (
        p.class_allocation_percent.cash
        is p.class_allocation_percent.stocks
        is p.class_allocation_percent.crypto
        is None
    )
    holding = p.holdings[0]
    assert holding.current_value is holding.mid is holding.as_of is holding.unrealized_pl is None
    assert holding.allocation_percent is None and holding.stock_mark.valuation_reason == reason
    assert holding.stock_mark.units_safe is units and holding.cost_basis == 204
    assert holding.average_cost == (Decimal(102) if units else None)
    assert await financial_snapshot(factory) == before


async def test_halted_old_mark_uses_original_source_and_current_independent_lease(
    stock_trade_case, settings
):
    from sqlalchemy import text

    from tests.test_stock_status import financial_snapshot

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
    async with factory.begin() as db:
        await db.execute(text("UPDATE stock_status_evidence SET state='halted'"))
        await db.execute(text("UPDATE stock_quotes SET event_at=collected_at-interval '5 minutes'"))
    before = await financial_snapshot(factory)
    async with factory() as db:
        p = await get_portfolio(db, user_id=uid, settings=settings)
    mark = p.holdings[0].stock_mark
    assert p.total_value == 9998 and mark.mark_mode == "halted" and mark.feed == "iex"
    assert p.holdings[0].age_seconds >= 300 and mark.event_at < mark.collected_at
    assert mark.valid_until <= mark.collected_at + timedelta(seconds=60)
    assert mark.historical_admission_until is not None and mark.retained_until is not None
    assert await financial_snapshot(factory) == before


async def test_quote_generation_renewal_requires_fresh_original_rights_proof(
    stock_trade_case, settings
):
    from sqlalchemy import text

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE stock_data_admissions SET generation=5 WHERE product='quotes'")
        )
        await db.execute(
            text(
                "UPDATE stock_quotes SET "
                "admission_generation=5,event_at=clock_timestamp(),collected_at=clock_timestamp()"
            )
        )
    async with factory() as db:
        missing = await get_portfolio(db, user_id=uid, settings=settings)
        assert (
            missing.total_value is None
            and missing.holdings[0].stock_mark.valuation_reason == "permission_unavailable"
        )
        await db.rollback()
        # Current rights can authorize a NEW fill. Its immutable original scope
        # then proves the new quote generation; it never blesses the old one.
        await execute(db, user_id=uid, order=trade_order(quantity="1"), settings=settings)
        permitted = await get_portfolio(db, user_id=uid, settings=settings)
        assert (
            permitted.total_value == 9997 and permitted.holdings[0].stock_mark.mark_mode == "fresh"
        )


async def test_exact_ninth_decimal_midpoint_is_not_storage_mid(stock_trade_case, settings):
    from sqlalchemy import text

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
    async with factory.begin() as db:
        await db.execute(text("UPDATE stock_quotes SET bid=1,ask=1.00000001,mid=1"))
    async with factory() as db:
        p = await get_portfolio(db, user_id=uid, settings=settings)
    assert p.holdings[0].mid == Decimal("1.000000005") and p.total_value == 9798


async def test_verified_closed_mark_is_dated_and_never_executes(
    stock_trade_case, settings, monkeypatch
):
    from sqlalchemy import text

    from app.services import stock_sessions
    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        fill, _ = await execute(db, user_id=uid, order=trade_order(), settings=settings)
    close = fill.executed_at + timedelta(microseconds=1)
    original = stock_sessions.calendars.get_calendar

    def closed_calendar(*args, **kwargs):
        calendar = original(*args, **kwargs)
        prior = calendar.session_close

        def session_close(day):
            stamp = prior(day)
            if str(day) == str(now.date()):
                return type(stamp)(close)
            return stamp

        calendar.session_close = session_close
        return calendar

    stock_sessions._calendar_bounds.cache_clear()
    monkeypatch.setattr(stock_sessions.calendars, "get_calendar", closed_calendar)
    async with factory.begin() as db:
        await db.execute(
            text("UPDATE stock_sessions SET closes_at=:close WHERE session_date=:date"),
            {"close": close, "date": now.date()},
        )
        await db.execute(text("UPDATE stock_quotes SET event_at=collected_at-interval '5 minutes'"))
    async with factory() as db:
        p = await get_portfolio(db, user_id=uid, settings=settings)
        assert p.total_value == 9998 and p.holdings[0].stock_mark.mark_mode == "closed"
        assert p.holdings[0].age_seconds >= 300
        await db.rollback()
        with pytest.raises(TradeRefused) as exc:
            await execute(db, user_id=uid, order=trade_order(), settings=settings)
        assert exc.value.code == "market_closed"


@pytest.mark.parametrize("deadline", ["quote", "status", "action"])
async def test_stock_mark_strict_expiry_never_extends_rights(stock_trade_case, settings, deadline):
    from sqlalchemy import select, text

    from app.models.stock import StockQuote
    from app.models.stock_execution import StockStatusEvidence

    factory, cid, uid, now = stock_trade_case
    if deadline == "quote":
        async with factory.begin() as db:
            await db.execute(
                text(
                    "UPDATE stock_data_admissions SET "
                    "quota=jsonb_set(quota,'{retention_seconds}','10') WHERE product='quotes'"
                )
            )
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
        if deadline == "quote":
            at = (
                await db.scalar(select(StockQuote.collected_at).where(StockQuote.coin_id == cid))
            ) + timedelta(seconds=10)
        elif deadline == "status":
            at = await db.scalar(
                select(StockStatusEvidence.valid_until).where(StockStatusEvidence.coin_id == cid)
            )
        else:
            at = now + timedelta(seconds=5)
            await db.execute(
                text("UPDATE stock_action_state SET valid_until=:at WHERE coin_id=:cid"),
                {"at": at, "cid": cid},
            )
            await db.commit()
        before = await get_portfolio(
            db, user_id=uid, settings=settings, now=at - timedelta(microseconds=1)
        )
        assert before.total_value == 9998 and before.holdings[0].stock_mark.valid_until <= at
        after = await get_portfolio(db, user_id=uid, settings=settings, now=at)
        assert after.total_value is None and after.known_value == 9796
        assert after.holdings[0].stock_mark.valid_until is None


async def test_consumed_split_marker_values_only_compatible_current_units(
    stock_trade_case, settings
):
    from sqlalchemy import func, select, text

    from app.services.stock_ownership import StockMovementInput, append_stock_movement
    from tests.stock_action_fixtures import synthetic_split

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
    async with factory.begin() as db:
        cutoff = await db.scalar(select(func.clock_timestamp()))
        split = await synthetic_split(db, cid, cutoff, boundary=1)
        await append_stock_movement(
            db,
            StockMovementInput(
                uid,
                cid,
                Decimal(2),
                Decimal(204),
                "split:" + str(split.id),
                application_id=split.id,
            ),
        )
        await db.execute(
            text(
                "UPDATE stock_action_state SET "
                "next_blocking_at=:cutoff,quote_not_before=:cutoff WHERE coin_id=:cid"
            ),
            {"cutoff": cutoff, "cid": cid},
        )
        await db.execute(
            text(
                "UPDATE stock_quotes SET "
                "bid=50,ask=51,mid=50.5,unit_epoch=1,event_at=clock_timestamp(),"
                "collected_at=clock_timestamp() WHERE coin_id=:cid"
            ),
            {"cid": cid},
        )
    async with factory() as db:
        p = await get_portfolio(db, user_id=uid, settings=settings)
    assert p.total_value == 9998 and p.holdings[0].quantity == 4
    assert p.holdings[0].average_cost == 51 and p.holdings[0].stock_mark.authority.unit_epoch == 1


@pytest.mark.parametrize(
    "change", ["fill", "units", "permission", "halt", "price", "epoch", "mapping", "continuity"]
)
async def test_fresh_authority_can_only_suppress_original_financial_snapshot(
    stock_trade_case, settings, monkeypatch, change
):
    from sqlalchemy import func, select, text

    from app.services.stock_ownership import StockMovementInput, append_stock_movement
    from tests.stock_action_fixtures import synthetic_split

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
    async with factory() as reader:
        real = reader.execute
        queries = []

        async def read_then_commit(statement, *args, **kwargs):
            result = await real(statement, *args, **kwargs)
            queries.append(str(statement))
            if len(queries) == 1:
                async with factory() as writer:
                    if change == "fill":
                        await execute(
                            writer, user_id=uid, order=trade_order(quantity="1"), settings=settings
                        )
                    else:
                        if change == "units":
                            cutoff = await writer.scalar(select(func.clock_timestamp()))
                            split = await synthetic_split(writer, cid, cutoff, boundary=1)
                            await append_stock_movement(
                                writer,
                                StockMovementInput(
                                    uid,
                                    cid,
                                    Decimal(2),
                                    Decimal(204),
                                    "split:" + str(split.id),
                                    application_id=split.id,
                                ),
                            )
                            await writer.execute(
                                text(
                                    "UPDATE stock_action_state SET quote_not_before=:cutoff "
                                    "WHERE coin_id=:cid"
                                ),
                                {"cutoff": cutoff, "cid": cid},
                            )
                            await writer.execute(
                                text(
                                    "UPDATE stock_quotes SET "
                                    "bid=50,ask=51,mid=50.5,unit_epoch=1,event_at=clock_timestamp(),collected_at=clock_timestamp()"
                                )
                            )
                        elif change == "permission":
                            await writer.execute(
                                text(
                                    "UPDATE stock_data_admissions SET state='revoked' WHERE "
                                    "product='quotes'"
                                )
                            )
                        elif change == "halt":
                            await writer.execute(
                                text("UPDATE stock_status_evidence SET state='halted'")
                            )
                        elif change == "mapping":
                            await writer.execute(
                                text(
                                    "UPDATE stock_instruments SET "
                                    "provider_asset_id='changed-asset' "
                                    "WHERE coin_id=:cid"
                                ),
                                {"cid": cid},
                            )
                        elif change == "continuity":
                            await writer.execute(
                                text(
                                    "UPDATE stock_status_evidence SET "
                                    "continuity_generation=continuity_generation+1"
                                )
                            )
                        elif change == "price":
                            await writer.execute(
                                text("UPDATE stock_quotes SET bid=200,ask=202,mid=201")
                            )
                        else:
                            await writer.execute(
                                text("UPDATE stock_action_state SET epoch=epoch+1")
                            )
                        await writer.commit()
            return result

        monkeypatch.setattr(reader, "execute", read_then_commit)
        p = await get_portfolio(reader, user_id=uid, settings=settings)
        assert p.cash == 9796 and p.holdings[0].quantity == 2 and p.holdings[0].cost_basis == 204
        assert sum("FROM accounts" in query for query in queries) == 1
        assert len(queries) == 2
        if change in ("units", "permission", "epoch", "mapping", "continuity"):
            assert p.total_value is None and p.known_value == 9796
            assert p.holdings[0].average_cost == (Decimal(102) if change == "continuity" else None)
        else:
            assert p.total_value == 9998 and p.holdings[0].mid == 101
            if change == "halt":
                assert p.holdings[0].stock_mark.mark_mode == "halted"


async def test_inactive_stock_keeps_owned_finances_but_no_unverified_mark(
    stock_trade_case, settings
):
    from sqlalchemy import text

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
    async with factory.begin() as db:
        await db.execute(text("UPDATE coins SET is_active=false WHERE id=:cid"), {"cid": cid})
    try:
        async with factory() as db:
            p = await get_portfolio(db, user_id=uid, settings=settings)
        assert p.total_value is None and p.known_value == 9796
        assert p.holdings[0].quantity == 2 and p.holdings[0].cost_basis == 204
        assert not p.holdings[0].is_active and p.holdings[0].average_cost is None
    finally:
        async with factory.begin() as db:
            await db.execute(text("UPDATE coins SET is_active=true WHERE id=:cid"), {"cid": cid})


async def test_missing_or_malformed_original_terms_never_mint_retention(stock_trade_case, settings):
    from sqlalchemy import select

    from app.models.stock_execution import StockFillFacts
    from app.services.stock_eligibility import execution_snapshot_query, executions_from_snapshot
    from app.services.stock_valuation import value_stock

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        await execute(db, user_id=uid, order=trade_order(), settings=settings)
        raw = (await db.execute(execution_snapshot_query(now))).one()
        loaded = executions_from_snapshot(raw, settings)[cid]
        original = await db.scalar(
            select(StockFillFacts.authority).where(StockFillFacts.coin_id == cid)
        )
    for proof in (
        {},
        {"admissions": []},
        {**original, "admissions": [{"product": "quotes", "valid_until": "not-a-date"}]},
    ):
        result = value_stock(
            loaded, loaded, raw=raw, current_raw=raw, proof=proof, now=raw.checked_at
        )
        assert result.mid is None and result.mark.valuation_reason == "permission_unavailable"
        assert result.mark.event_at is result.mark.valid_until is result.mark.authority is None


async def test_actual_stock_portfolio_wire_preserves_plain_strings_and_mark_identity(stock_http):
    import re

    from tests.test_stock_trades_api import BASE, body

    client, headers, factory, cid, uid, now = stock_http
    assert (await client.post(BASE, json=body(), headers=headers)).status_code == 201
    response = await client.get("/api/v1/portfolio")
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    value = response.json()
    assert value["valuation_complete"] and value["unvalued_holding_count"] == 0
    assert value["known_value"] == value["total_value"] == "9998.00"
    assert value["class_values"] == {"cash": "9796.00", "stocks": "202.00", "crypto": "0.00"}
    holding = value["holdings"][0]
    assert holding["asset_class"] == "stock" and holding["coin_id"] == str(cid)
    assert holding["stock_mark"]["mark_mode"] == "fresh" and holding["stock_mark"]["feed"] == "iex"
    assert holding["stock_mark"]["authority"]["unit_epoch"] == 0
    for field in (
        "quantity",
        "cost_basis",
        "average_cost",
        "mid",
        "current_value",
        "unrealized_pl",
        "allocation_percent",
    ):
        assert isinstance(holding[field], str) and re.fullmatch(
            r"-?[0-9]+(?:\.[0-9]+)?", holding[field]
        )
