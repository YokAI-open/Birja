"""Actual final-schema historical eligibility and active-root isolation."""

import json
from dataclasses import asdict, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corporate_action import StockDividendEntitlement
from app.models.price import Coin
from app.models.stock import StockDataAdmission, StockInstrument
from app.services import corporate_actions as actions
from app.services.stock_admission import ProductAdmission
from app.services.stock_sessions import RegularSession, build_sessions
from tests.test_corporate_action_rules import dividend
from tests.test_corporate_actions import batch
from tests.test_portfolio_creation import authority, management_api
from tests.test_portfolio_stock_ownership import close_root
from tests.test_portfolio_strategy_lifecycle import (
    current_stock_authority_case as stock_authority_case,
)
from tests.test_portfolio_strategy_lifecycle import strategy_books
from tests.test_stock_admission import action_admitted
from tests.test_stock_sessions import evidence

__all__ = ["authority", "management_api", "strategy_books", "stock_authority_case"]


def completed_entitlement_session(
    now: datetime, calendar: ProductAdmission, exchange: str
) -> RegularSession:
    sessions = [
        session
        for session in build_sessions(now, calendar)
        if session.exchange == exchange
        and session.opens_at is not None
        and session.closes_at is not None
        and session.closes_at < now
    ]
    return max(sessions, key=lambda session: session.session_date)


@pytest.mark.parametrize("exchange", ["NYSE", "NASDAQ"])
@pytest.mark.parametrize(
    "stamp,expected_day",
    [
        ("2026-11-17T14:29:59+00:00", "2026-11-16"),
        ("2026-11-17T14:30:00+00:00", "2026-11-16"),
        ("2026-11-17T15:29:59+00:00", "2026-11-16"),
        ("2026-11-17T20:59:59+00:00", "2026-11-16"),
        ("2026-11-17T21:00:01+00:00", "2026-11-17"),
        ("2026-11-27T17:59:59+00:00", "2026-11-25"),
        ("2026-11-27T18:00:01+00:00", "2026-11-27"),
        ("2026-11-29T16:00:00+00:00", "2026-11-27"),
        ("2026-03-09T13:45:00+00:00", "2026-03-06"),
    ],
)
def test_entitlement_fixture_keeps_later_split_after_cutoff(exchange, stamp, expected_day):
    now = datetime.fromisoformat(stamp).astimezone(UTC)
    session = completed_entitlement_session(now, evidence(now), exchange)
    assert session.session_date == date.fromisoformat(expected_day)
    assert session.closes_at is not None and session.closes_at < now
    assert session.opens_at is not None and session.opens_at < now - timedelta(hours=1)


@pytest_asyncio.fixture
async def entitlement_case(stock_authority_case):
    conn, case = stock_authority_case
    now = case["now"]
    db = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
    calendar = replace(evidence(now), generation=1)
    admission = replace(
        action_admitted(),
        generation=1,
        reviewed_at=now - timedelta(hours=1),
        valid_from=now - timedelta(hours=2),
        valid_until=now + timedelta(hours=2),
    )
    for item in (calendar, admission):
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == item.product)
            .values(**asdict(item))
        )
    exchange = (
        await db.execute(
            select(StockInstrument.listing_exchange).where(StockInstrument.coin_id == case["coin"])
        )
    ).scalar_one()
    session = completed_entitlement_session(now, calendar, exchange)
    await conn.execute(
        text("""UPDATE stock_action_state SET
      journal_start_at=CAST(:n AS timestamptz)-interval '20 days',
      complete_from=CAST(:n AS timestamptz)-interval '20 days',
      coverage_start=CAST(:n AS timestamptz)-interval '20 days',covered_until=:n
      WHERE coin_id=:c"""),
        {"n": now, "c": case["coin"]},
    )
    await conn.execute(
        text("""INSERT INTO stock_sessions(exchange,session_date,
      opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation)
      VALUES (:e,:d,:o,:cl,:d,:d,1) ON CONFLICT(exchange,session_date)
      DO UPDATE SET opens_at=EXCLUDED.opens_at,closes_at=EXCLUDED.closes_at"""),
        {"e": exchange, "d": session.session_date, "o": session.opens_at, "cl": session.closes_at},
    )
    for seq, (root, quantity) in enumerate(((case["first"], 2), (case["sibling"], 4)), 1):
        await conn.execute(
            text("""UPDATE holdings SET quantity=:q,cost_basis=:b
          WHERE portfolio_id=:p AND coin_id=:c"""),
            {"p": root, "c": case["coin"], "q": quantity, "b": quantity * 10},
        )
        await conn.execute(
            text("""INSERT INTO stock_ownership_movements
          (portfolio_id,user_id,coin_id,sequence,economic_at,recorded_at,quantity,
           before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key)
          VALUES (:p,:u,:c,:s,CAST(:n AS timestamptz)-interval '10 days',:n,:q,0,:q,0,:b,
                  0,'opening',:k)"""),
            {
                "p": root,
                "u": case["owner"],
                "c": case["coin"],
                "s": seq,
                "n": now,
                "q": quantity,
                "b": quantity * 10,
                "k": str(uuid4()),
            },
        )
    symbol = (await db.execute(select(Coin.symbol).where(Coin.id == case["coin"]))).scalar_one()
    action = dividend(
        coin_id=case["coin"],
        symbol=symbol,
        provider_event_id=str(uuid4()),
        observed_at=now,
        process_date=session.session_date,
        ex_date=session.session_date,
        record_date=session.session_date,
        payable_date=session.session_date,
    )
    result = (await actions.persist_action_batch(db, batch(action), admission))[0]
    try:
        yield db, conn, case, action, admission, result.event_id
    finally:
        await db.close()


async def test_active_same_owner_roots_have_distinct_historical_entitlements(entitlement_case):
    db, _, case, _, _, event = entitlement_case
    rows = await actions.derive_dividend_entitlements(db, event)
    assert [(r.portfolio_id, r.user_id, r.eligible_quantity, r.state) for r in rows] == [
        (case["first"], case["owner"], Decimal(2), "eligible"),
        (case["sibling"], case["owner"], Decimal(4), "eligible"),
    ]
    assert rows[0].fingerprint != rows[1].fingerprint
    assert await actions.derive_dividend_entitlements(db, event) == rows
    assert await actions.latest_verified_entitlements(db, event) == rows


async def test_scheduler_derives_without_cash_update_privilege(entitlement_case):
    db, conn, case, _, _, event = entitlement_case
    await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
    assert len(await actions.derive_dividend_entitlements(db, event)) == 2
    assert not (
        await conn.execute(
            text("SELECT has_column_privilege('birja_scheduler','accounts','cash','UPDATE')")
        )
    ).scalar_one()
    assert (
        await db.get(
            StockDividendEntitlement, (await actions.latest_verified_entitlements(db, event))[0].id
        )
    ).portfolio_id == case["first"]


@pytest.mark.parametrize("before_cutoff", [False, True])
async def test_historical_sale_uses_ex_date_not_current_holding(entitlement_case, before_cutoff):
    db, conn, case, _, _, event = entitlement_case
    # derive once to obtain the independently calendar-verified boundary.
    cutoff = (await actions.derive_dividend_entitlements(db, event))[0].cutoff
    at = cutoff + timedelta(hours=-1 if before_cutoff else 1)
    tid = (
        await conn.execute(
            text("""INSERT INTO trades
      (portfolio_id,user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
       exec_price,fee,cash_delta,cash_after,idempotency_key)
      VALUES (:p,:u,:c,'sell','quantity',2,2,10,:at,10,0,20,10000,:key) RETURNING id"""),
            {"p": case["first"], "u": case["owner"], "c": case["coin"], "at": at, "key": uuid4()},
        )
    ).scalar_one()
    await conn.execute(
        text("""INSERT INTO stock_fill_facts
      (trade_id,portfolio_id,coin_id,user_id,provider_asset_id,symbol,company_name,listing_exchange,
       source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,observed_at,session_date,
       opens_at,closes_at,authority)
      VALUES (:t,:p,:c,:u,'fixture-asset','AAPL','Synthetic company','NASDAQ','alpaca','iex',
       10,10,10,0,:at,:at,:at,CAST(:at AS timestamptz)::date,
       CAST(:at AS timestamptz)-interval '1 hour',CAST(:at AS timestamptz)+interval '1 hour',
       CAST(:s AS jsonb))"""),
        {
            "t": tid,
            "p": case["first"],
            "u": case["owner"],
            "c": case["coin"],
            "at": at,
            "s": json.dumps(case["snapshot"]),
        },
    )
    await conn.execute(
        text("""INSERT INTO stock_ownership_movements
      (portfolio_id,user_id,coin_id,sequence,economic_at,recorded_at,quantity,
       before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,trade_id,causal_key)
      VALUES (:p,:u,:c,3,:at,:at,-2,2,0,20,0,0,'fill',:t,:k)"""),
        {
            "t": tid,
            "p": case["first"],
            "u": case["owner"],
            "c": case["coin"],
            "at": at,
            "k": f"fill:{tid}",
        },
    )
    await conn.execute(
        text("DELETE FROM holdings WHERE portfolio_id=:p AND coin_id=:c"),
        {"p": case["first"], "c": case["coin"]},
    )
    db.expire_all()
    rows = await actions.derive_dividend_entitlements(db, event)
    assert [r.eligible_quantity for r in rows] == [Decimal(0 if before_cutoff else 2), Decimal(4)]
    assert {r.state for r in rows} == {"eligible"}


async def test_later_split_does_not_reprice_old_dividend_units(entitlement_case):
    from tests.test_portfolio_splits import record_split

    db, _, case, action, admission, event = entitlement_case
    original = await actions.derive_dividend_entitlements(db, event)
    assert original[0].cutoff < case["now"] - timedelta(hours=1)
    assert (
        len(
            await record_split(
                db, case, replace(action, payable_date=case["now"].date()), admission, hours=1
            )
        )
        == 1
    )
    rows = await actions.derive_dividend_entitlements(db, event)
    assert [(r.eligible_quantity, r.unit_epoch) for r in rows] == [(Decimal(2), 0), (Decimal(4), 0)]
    assert rows == original


async def test_closed_earned_eligibility_is_retained_but_not_rederived(entitlement_case):
    db, conn, case, action, admission, event = entitlement_case
    original = await actions.derive_dividend_entitlements(db, event)
    before = (
        await conn.execute(
            text("SELECT to_jsonb(e) FROM stock_dividend_entitlements e WHERE portfolio_id=:p"),
            {"p": case["first"]},
        )
    ).all()
    await close_root(db, conn, case, case["first"])
    assert [r.portfolio_id for r in await actions.latest_verified_entitlements(db, event)] == [
        case["sibling"]
    ]
    await actions.persist_action_batch(db, batch(replace(action, rate=Decimal(".75"))), admission)
    updated = await actions.derive_dividend_entitlements(db, event)
    assert len(updated) == 1 and updated[0].portfolio_id == case["sibling"]
    assert updated[0].supersedes_id == original[1].id and updated[0].version == 2
    assert (
        await conn.execute(
            text("SELECT to_jsonb(e) FROM stock_dividend_entitlements e WHERE portfolio_id=:p"),
            {"p": case["first"]},
        )
    ).all() == before


@pytest.mark.parametrize("cancelled", [False, True])
async def test_uncertain_or_cancelled_replacements_never_reveal_old_eligibility(
    entitlement_case, cancelled
):
    db, _, _, action, admission, event = entitlement_case
    original = await actions.derive_dividend_entitlements(db, event)
    changed = replace(action, cancelled=True) if cancelled else replace(action, rate=None)
    await actions.persist_action_batch(db, batch(changed), admission)
    rows = await actions.derive_dividend_entitlements(db, event)
    assert {r.state for r in rows} == {"cancelled" if cancelled else "held"}
    assert {r.eligible_quantity for r in rows} == {Decimal(0)}
    assert [r.supersedes_id for r in rows] == [r.id for r in original]
    assert not await actions.latest_verified_entitlements(db, event)
