# ruff: noqa: F811
"""Real financial effects through the stock service, never a fabricated fill."""

from decimal import Decimal

import pytest

from app.schemas.stock_trades import QuoteIn
from app.services import stock_trading
from tests.stock_trade_fixtures import ownership, status_case, stock_trade_case  # noqa: F401
from tests.test_stock_status import financial_snapshot


async def test_stock_preview_is_read_only(stock_trade_case, settings):
    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    async with factory() as db:
        result = await stock_trading.quote(
            db,
            user_id=uid,
            order=QuoteIn(symbol="AAPL", side="buy", quantity="2"),
            settings=settings,
        )
    assert result.coin_id == str(cid)
    assert result.exec_price == Decimal(102)
    assert result.notional == Decimal(204)
    assert result.cash_after == Decimal(9796)
    assert result.held_after == Decimal(2)
    assert result.fee == 0
    assert await financial_snapshot(factory) == before


async def test_buy_partial_sell_and_sold_out_keep_exact_basis(stock_trade_case, settings):
    from uuid import uuid4

    from sqlalchemy import select

    from app.models.corporate_action import StockOwnershipMovement
    from app.models.stock_execution import StockFillFacts
    from app.models.trade import Holding, Trade
    from app.models.user import Account
    from app.schemas.stock_trades import TradeIn

    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        buy, created = await stock_trading.execute(
            db,
            user_id=uid,
            order=TradeIn(
                symbol="AAPL",
                side="buy",
                quantity="3",
                expected_exec_price="102",
                idempotency_key=uuid4(),
            ),
            settings=settings,
        )
        assert created and buy.cash_after == Decimal(9694) and buy.held_after == 3
        assert buy.executed_at >= now and buy.fee == 0
        for qty, expected_cash, expected_held, expected_basis in (
            ("1", Decimal(9794), Decimal(2), Decimal(204)),
            ("2", Decimal(9994), Decimal(0), Decimal(0)),
        ):
            sale, created = await stock_trading.execute(
                db,
                user_id=uid,
                order=TradeIn(
                    symbol="AAPL",
                    side="sell",
                    quantity=qty,
                    expected_exec_price="100",
                    idempotency_key=uuid4(),
                ),
                settings=settings,
            )
            assert created and sale.cash_after == expected_cash and sale.held_after == expected_held
            row = (
                await db.execute(
                    select(Holding.quantity, Holding.cost_basis).where(
                        Holding.user_id == uid, Holding.coin_id == cid
                    )
                )
            ).one()
            assert tuple(row) == (expected_held, expected_basis)
        assert (await db.scalar(select(Account.cash).where(Account.user_id == uid))) == Decimal(
            9994
        )
        for model in (Trade, StockFillFacts, StockOwnershipMovement):
            assert len((await db.scalars(select(model).where(model.user_id == uid))).all()) == 3


def trade_order(**changes):
    from uuid import uuid4

    from app.schemas.stock_trades import TradeIn

    return TradeIn(
        **{
            "symbol": "AAPL",
            "side": "buy",
            "quantity": "2",
            "expected_exec_price": "102",
            "idempotency_key": uuid4(),
            **changes,
        }
    )


async def test_receipt_replays_after_sale_rename_and_permission_revocation(
    stock_trade_case, settings
):
    from sqlalchemy import update

    from app.models.price import Coin
    from app.models.stock import StockDataAdmission

    factory, cid, uid, now = stock_trade_case
    order = trade_order()
    async with factory() as db:
        original, created = await stock_trading.execute(
            db, user_id=uid, order=order, settings=settings
        )
        assert created
        await stock_trading.execute(
            db,
            user_id=uid,
            order=trade_order(side="sell", expected_exec_price="100"),
            settings=settings,
        )
    async with factory.begin() as db:
        await db.execute(
            update(Coin).where(Coin.id == cid).values(name="Renamed company", is_active=False)
        )
        await db.execute(update(StockDataAdmission).values(state="denied"))
    before = await financial_snapshot(factory)
    try:
        async with factory() as db:
            again, created = await stock_trading.execute(
                db,
                user_id=uid,
                order=order.model_copy(update={"expected_exec_price": Decimal(999)}),
                settings=settings,
            )
            assert not created and again == original
            assert again.held_after == 2 and again.cash_after == Decimal(9796)
        assert await financial_snapshot(factory) == before
    finally:
        async with factory.begin() as db:
            await db.execute(
                update(Coin).where(Coin.id == cid).values(name="Apple Inc.", is_active=True)
            )


@pytest.mark.parametrize(
    "change,code",
    [
        ({"quantity": "3"}, "idempotency_conflict"),
        ({"side": "sell"}, "idempotency_conflict"),
        ({"symbol": "MSFT"}, "idempotency_conflict"),
    ],
)
async def test_key_payload_change_conflicts_without_effect(
    stock_trade_case, settings, change, code
):
    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    order = trade_order()
    async with factory() as db:
        await stock_trading.execute(db, user_id=uid, order=order, settings=settings)
    before = await financial_snapshot(factory)
    async with factory() as db:
        changed = trade_order(**{**order.model_dump(mode="json"), **change})
        with pytest.raises(TradeRefused) as exc:
            await stock_trading.execute(db, user_id=uid, order=changed, settings=settings)
        assert exc.value.code == code
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize(
    "side,price,previous,delta",
    [
        ("buy", "101", Decimal(-202), Decimal(-2)),
        ("sell", "99", Decimal(198), Decimal(2)),
    ],
)
async def test_reprice_requires_reconfirmation_without_mutation(
    stock_trade_case, settings, side, price, previous, delta
):
    factory, cid, uid, now = stock_trade_case
    async with factory() as db:
        if side == "sell":
            await stock_trading.execute(db, user_id=uid, order=trade_order(), settings=settings)
    before = await financial_snapshot(factory)
    async with factory() as db:
        with pytest.raises(stock_trading.PriceChanged) as exc:
            await stock_trading.execute(
                db,
                user_id=uid,
                order=trade_order(side=side, expected_exec_price=price),
                settings=settings,
            )
        assert exc.value.detail.previous_cash_delta == previous
        assert exc.value.detail.cash_delta_change == delta
        assert exc.value.detail.exec_price_change == 1
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize(
    "change,code",
    [
        ({"side": "sell"}, "insufficient_holding"),
        ({"quantity": "100"}, "insufficient_cash"),
        ({"symbol": "BTC"}, "quote_unavailable"),
    ],
)
async def test_refusal_has_no_financial_effect(stock_trade_case, settings, change, code):
    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    async with factory() as db:
        with pytest.raises(TradeRefused) as exc:
            await stock_trading.execute(
                db, user_id=uid, order=trade_order(**change), settings=settings
            )
        assert exc.value.code == code
    assert await financial_snapshot(factory) == before


async def test_context_shortcuts_are_read_only(stock_trade_case, settings):
    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    async with factory() as db:
        result = await stock_trading.context(db, user_id=uid, symbol="AAPL", settings=settings)
        assert result.execution_enabled and result.buy_max_quantity == 98
        assert result.held_quantity == 0 and result.quote.bid == 100 and result.quote.ask == 102
        assert result.status.state == "normal" and result.action.state == "current"
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize(
    "mutation,code",
    [
        (
            "UPDATE stock_data_admissions SET state='denied' WHERE product='quotes'",
            "permission_unavailable",
        ),
        ("UPDATE stock_status_evidence SET state='halted'", "halted"),
        ("UPDATE stock_action_state SET health='unknown'", "action_unavailable"),
        ("DELETE FROM stock_quotes", "quote_unavailable"),
    ],
)
async def test_current_authority_refuses_new_fill(stock_trade_case, settings, mutation, code):
    from sqlalchemy import text

    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(text(mutation))
    before = await financial_snapshot(factory)
    async with factory() as db:
        with pytest.raises(TradeRefused) as exc:
            await stock_trading.execute(db, user_id=uid, order=trade_order(), settings=settings)
        assert exc.value.code == code
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize("failure", ["authority", "integrity", "cancel", "ownership", "db"])
async def test_late_failures_roll_back_all_staged_effects(
    stock_trade_case, settings, monkeypatch, failure
):
    import asyncio

    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError

    from app.services.stock_ownership import OwnershipHeld
    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    async with factory() as db:
        original = db.execute

        async def intercept(statement, *args, **kwargs):
            if "SET CONSTRAINTS ALL IMMEDIATE" in str(statement):
                if failure == "authority":
                    # Change actual persisted same-generation authority AFTER
                    # helper/fresh semantic evaluation. The real SQL guard denies.
                    await original(
                        text(
                            "UPDATE stock_data_admissions SET attribution='changed' "
                            "WHERE product='quotes'"
                        )
                    )
                elif failure == "integrity":
                    await original(
                        text("UPDATE accounts SET cash=-1 WHERE user_id=:uid"), {"uid": uid}
                    )
                elif failure == "cancel":
                    raise asyncio.CancelledError()
                elif failure == "ownership":
                    raise OwnershipHeld("history_gap")
                else:
                    await original(text("SELECT 1/0"))
            return await original(statement, *args, **kwargs)

        monkeypatch.setattr(db, "execute", intercept)
        expected = {
            "authority": TradeRefused,
            "integrity": IntegrityError,
            "cancel": asyncio.CancelledError,
            "ownership": TradeRefused,
            "db": DBAPIError,
        }[failure]
        with pytest.raises(expected):
            await stock_trading.execute(db, user_id=uid, order=trade_order(), settings=settings)
        assert not db.in_transaction()
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize(
    "hidden,change,expected",
    [(1, False, "replay"), (2, False, "replay"), (2, True, "conflict"), (99, False, "integrity")],
)
async def test_key_rechecked_under_lock_and_unique_backstop(
    stock_trade_case, settings, monkeypatch, hidden, change, expected
):
    from sqlalchemy.exc import IntegrityError

    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    order = trade_order()
    async with factory() as db:
        original, _ = await stock_trading.execute(db, user_id=uid, order=order, settings=settings)
    before = await financial_snapshot(factory)
    real = stock_trading.find_user_trade
    calls = 0

    async def miss_then_find(*args):
        nonlocal calls
        calls += 1
        return None if calls <= hidden else await real(*args)

    monkeypatch.setattr(stock_trading, "find_user_trade", miss_then_find)
    async with factory() as db:
        changed = order.model_copy(update={"quantity": Decimal(3)}) if change else order
        if expected == "replay":
            again, created = await stock_trading.execute(
                db, user_id=uid, order=changed, settings=settings
            )
            assert not created and again == original
        else:
            with pytest.raises(TradeRefused if expected == "conflict" else IntegrityError) as exc:
                await stock_trading.execute(db, user_id=uid, order=changed, settings=settings)
            if expected == "conflict":
                assert exc.value.code == "idempotency_conflict"
        assert not db.in_transaction()
    assert await financial_snapshot(factory) == before


async def test_crypto_key_conflicts_in_stock_lane_and_other_users_are_independent(
    stock_trade_case, settings, engine, clean_prices, new_user
):
    from uuid import uuid4

    from app.services import trading
    from app.services.trade_math import TradeRefused
    from tests.helpers import put_price

    factory, cid, uid, now = stock_trade_case
    key = uuid4()
    await put_price(engine, "BTC", "100", now)
    async with factory() as db:
        await trading.execute(
            db,
            user_id=uid,
            order=trading.Order("BTC", "buy", "usd", Decimal(100)),
            expected_mid=Decimal(100),
            idempotency_key=key,
            settings=settings,
        )
    before = await financial_snapshot(factory)
    async with factory() as db:
        with pytest.raises(TradeRefused) as exc:
            await stock_trading.execute(
                db, user_id=uid, order=trade_order(idempotency_key=key), settings=settings
            )
        assert exc.value.code == "idempotency_conflict"
    assert await financial_snapshot(factory) == before
    other = await new_user()
    async with factory() as db:
        fill, created = await stock_trading.execute(
            db, user_id=other, order=trade_order(idempotency_key=key), settings=settings
        )
        assert created and fill.cash_after == Decimal(9796)


@pytest.mark.parametrize(
    "change,code",
    [
        ("quotes", "permission_unavailable"),
        ("halted", "halted"),
        ("unknown", "action_unavailable"),
        ("missing", "quote_unavailable"),
    ],
)
async def test_context_denies_safely_without_financial_changes(
    stock_trade_case, settings, change, code
):
    from sqlalchemy import text

    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    mutations = {
        "quotes": "UPDATE stock_data_admissions SET state='denied' WHERE product='quotes'",
        "halted": "UPDATE stock_status_evidence SET state='halted'",
        "unknown": "UPDATE stock_action_state SET health='unknown'",
        "missing": "DELETE FROM stock_quotes",
    }
    async with factory.begin() as db:
        await db.execute(text(mutations[change]))
    before = await financial_snapshot(factory)
    async with factory() as db:
        if change == "quotes":
            with pytest.raises(TradeRefused) as exc:
                await stock_trading.context(db, user_id=uid, symbol="AAPL", settings=settings)
            assert exc.value.code == code
        else:
            result = await stock_trading.context(db, user_id=uid, symbol="AAPL", settings=settings)
            assert not result.execution_enabled and result.execution_reason == code
            assert result.buy_max_quantity == 0
            if change != "halted":
                assert result.quote is None
    assert await financial_snapshot(factory) == before


@pytest.mark.parametrize("price", ["103", "102"])
async def test_quote_update_after_helper_rolls_back_old_immutable_metadata(
    stock_trade_case, settings, monkeypatch, price
):
    from sqlalchemy import update

    from app.models.stock import StockQuote
    from app.services.trade_math import TradeRefused

    factory, cid, uid, now = stock_trade_case
    before = await financial_snapshot(factory)
    real = stock_trading.append_stock_movement

    async def append_then_update(db, movement):
        row = await real(db, movement)
        await db.execute(
            update(StockQuote)
            .where(StockQuote.coin_id == cid)
            .values(bid=Decimal(101), ask=Decimal(price), mid=(Decimal(101) + Decimal(price)) / 2)
        )
        return row

    monkeypatch.setattr(stock_trading, "append_stock_movement", append_then_update)
    async with factory() as db:
        with pytest.raises(TradeRefused) as exc:
            await stock_trading.execute(db, user_id=uid, order=trade_order(), settings=settings)
        assert exc.value.code == ("price_changed" if price == "103" else "quote_unavailable")
    assert await financial_snapshot(factory) == before


async def test_historical_rows_without_complete_receipt_never_reconstructed(ownership, settings):
    from app.services.trade_math import TradeRefused
    from tests.stock_action_fixtures import synthetic_fill

    factory, cid, uid = ownership
    async with factory() as db:
        saved = await synthetic_fill(db, cid, uid)
        key = saved.idempotency_key
        with pytest.raises(TradeRefused) as exc:
            await stock_trading.execute(
                db, user_id=uid, order=trade_order(idempotency_key=key), settings=settings
            )
        assert exc.value.code == "receipt_unavailable"


async def test_malformed_saved_receipt_is_unavailable(ownership, settings):
    from app.services.stock_ownership import StockMovementInput, append_stock_movement
    from app.services.trade_math import TradeRefused
    from tests.stock_action_fixtures import synthetic_fill

    factory, cid, uid = ownership
    async with factory.begin() as db:
        saved = await synthetic_fill(db, cid, uid)
        key = saved.idempotency_key
        await append_stock_movement(
            db,
            StockMovementInput(
                uid, cid, Decimal(2), Decimal(20), "fixture-fill", trade_id=saved.id
            ),
        )
    async with factory() as db:
        with pytest.raises(TradeRefused) as exc:
            await stock_trading.execute(
                db,
                user_id=uid,
                order=trade_order(symbol="SYNTH", idempotency_key=key),
                settings=settings,
            )
        assert exc.value.code == "receipt_unavailable"


def test_unsupported_authority_encoding_refuses():
    with pytest.raises(TypeError):
        stock_trading._encoded(object())


async def test_halt_context_does_not_disclose_unverified_future_quote(stock_trade_case, settings):
    from datetime import timedelta

    from sqlalchemy import update

    from app.models.stock import StockQuote
    from app.models.stock_execution import StockStatusEvidence

    factory, cid, uid, now = stock_trade_case
    async with factory.begin() as db:
        await db.execute(update(StockStatusEvidence).values(state="halted"))
        await db.execute(
            update(StockQuote).values(
                event_at=now + timedelta(minutes=1), collected_at=now + timedelta(minutes=1)
            )
        )
    async with factory() as db:
        result = await stock_trading.context(db, user_id=uid, symbol="AAPL", settings=settings)
        assert result.quote is None
        assert not result.execution_enabled and result.execution_reason == "halted"
