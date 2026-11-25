#!/usr/bin/env python3
"""Independent0023 before-backup oracle on explicitly owned synthetic data.

Opening positions and historical sale/event inputs are declared fixture data.
Creation, crypto execution, dividend payment/hold and terminal closure use their
real authorities. Public DELETE acceptance belongs to07/09/17, not this fixture.
No restored data is used to manufacture the before-backup expectation.
"""

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE_NAMES = frozenset(
    {
        "users",
        "accounts",
        "auth_sessions",
        "refresh_tokens",
        "coins",
        "prices",
        "holdings",
        "trades",
        "alembic_version",
        "stock_instruments",
        "stock_quotes",
        "stock_sessions",
        "stock_data_admissions",
        "stock_action_events",
        "stock_action_state",
        "stock_action_sources",
        "stock_action_revisions",
        "stock_action_observations",
        "stock_action_resolutions",
        "stock_dividend_entitlements",
        "stock_split_applications",
        "stock_ownership_movements",
        "stock_fill_facts",
        "stock_status_evidence",
        "stock_dividend_payments",
        "stock_dividend_decisions",
        "portfolio_stock_closures",
        "portfolio_creations",
        "portfolio_initializations",
        "portfolio_lifecycle_closures",
        "portfolio_closure_intents",
    }
)
IDENTITY_NAMES = TABLE_NAMES - {
    "alembic_version",
    "prices",
    "stock_instruments",
    "stock_quotes",
    "stock_action_state",
    "stock_fill_facts",
    "stock_status_evidence",
}


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def producer():
    spec = importlib.util.spec_from_file_location(
        "closure_fixture_producer", ROOT / "deploy/backup-snapshot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.require_closure_source(ROOT)
    return module


def historical_helpers(*, load_backend=True):
    spec = importlib.util.spec_from_file_location(
        "closure_event_helpers", ROOT / "deploy/tests/portfolio-execution-fixture.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    namespace = {}
    if load_backend:
        exec(
            compile(module.COMMON, "<source-owned-synthetic-event-helpers>", "exec"),
            namespace,
        )
    return namespace, module.COMMON


def require_projection(value):
    if (
        not isinstance(value, dict)
        or set(value) != {"revision", "tables", "sequences"}
        or value["revision"] != "0023"
    ):
        raise ValueError("0023 projection shape")
    tables = value["tables"]
    if set(tables) != TABLE_NAMES or set(value["sequences"]) != IDENTITY_NAMES:
        raise ValueError("complete31-table24-identity oracle required")
    for last, called in value["sequences"].values():
        if (
            type(last) is not int
            or not 1 <= last <= 9223372036854775807
            or type(called) is not bool
        ):
            raise ValueError("identity state invalid")
    roots = {r["name"]: r for r in tables["accounts"]}
    if set(roots) != {"Mixed", "Active", "Crypto", "Blank", "Zero"}:
        raise ValueError("independent strategy inventory")
    # Independent expected economics, not recomputed by the seed or restore.
    expected = {
        "Mixed": ("9880.50000000", True),
        "Active": ("9860.25000000", False),
        "Crypto": ("9900.00000000", True),
        "Blank": ("10000.00000000", True),
        "Zero": ("10000.00000000", True),
    }
    for name, (cash, closed) in expected.items():
        row = roots[name]
        if (
            row["cash"] != cash
            or row["starting_cash"] != "10000.00000000"
            or (row["closed_at"] is not None) != closed
        ):
            raise ValueError("independent cash/baseline/closure oracle")
    if (
        len(tables["portfolio_creations"]) != 5
        or len(tables["portfolio_initializations"]) != 2
    ):
        raise ValueError("once-only grant/latch lineage")
    closed = {r["portfolio_id"]: r for r in tables["portfolio_lifecycle_closures"]}
    if len(closed) != 4 or set(closed) != {
        r["id"] for r in roots.values() if r["closed_at"]
    }:
        raise ValueError("terminal lifecycle inventory")
    by_intent = {r["id"]: r for r in tables["portfolio_closure_intents"]}
    if (
        len(by_intent) != 5
        or sum(r["outcome"] == "confirmation_changed" for r in by_intent.values()) != 1
    ):
        raise ValueError("closed/refused immutable outcome oracle")
    for name, root in roots.items():
        if root["id"] not in closed:
            continue
        record = closed[root["id"]]
        intent = by_intent[record["intent_id"]]
        if (
            record["provenance"],
            record["confirmation_name"],
            record["user_id"],
            record["closed_at"],
        ) != ("owner_confirmation", name, root["user_id"], root["closed_at"]):
            raise ValueError("closure confirmation/time/owner oracle")
        if (
            intent["portfolio_id"],
            intent["user_id"],
            intent["outcome"],
            intent["confirmation_name"],
        ) != (root["id"], root["user_id"], "closed", name):
            raise ValueError("closure intent lineage oracle")
    stocks = {
        r["symbol"]: r["id"] for r in tables["coins"] if r["asset_class"] == "stock"
    }
    a, b = sorted(stocks.values())[:2]
    held = {
        (r["portfolio_id"], r["coin_id"]): (r["quantity"], r["cost_basis"])
        for r in tables["holdings"]
    }
    if held[roots["Mixed"]["id"], a] != ("0.00000000", "0.00000000") or held[
        roots["Mixed"]["id"], b
    ] != ("2.00000000", "20.00000000"):
        raise ValueError("sold-out and held stock oracle")
    boundaries = tables["portfolio_stock_closures"]
    if len(boundaries) != 2 or {
        (r["coin_id"], r["closing_sequence"], r["unit_epoch"]) for r in boundaries
    } != {(a, 3, 0), (b, 2, 0)}:
        raise ValueError("global sold-out stock boundary oracle")
    if not all(r["portfolio_id"] == roots["Mixed"]["id"] for r in boundaries):
        raise ValueError("stock closure moved into sibling")
    if len(tables["trades"]) != 4 or len(tables["stock_fill_facts"]) != 1:
        raise ValueError("immutable stock sale and crypto fill oracle")
    btc = next(r["id"] for r in tables["coins"] if r["symbol"] == "BTC")
    if held[roots["Active"]["id"], btc] != ("0.00995012", "100.00000000"):
        raise ValueError("independent active crypto quantity/basis oracle")
    active_fills = [r for r in tables["trades"] if r["portfolio_id"] == roots["Active"]["id"]]
    if len(active_fills) != 1 or active_fills[0]["idempotency_key"] != "00000000-0000-4000-8000-000000000067":
        raise ValueError("original active crypto fill identity required")
    if len(tables["stock_dividend_payments"]) != 2 or not any(
        r["outcome"] == "held_uncertain" for r in tables["stock_dividend_decisions"]
    ):
        raise ValueError("retained paid/held dividend evidence required")
    paid = {r["event_id"] for r in tables["stock_dividend_payments"]}
    if not any(
        r["event_id"] not in paid and r["state"] == "eligible"
        for r in tables["stock_dividend_entitlements"]
    ):
        raise ValueError("earned unpaid dividend causal evidence required")
    return value


async def seed(factory, settings, app_engine, scheduler_engine, helpers):
    """Current source-owned authority on synthetic initialized strategy roots."""
    from uuid import UUID
    from datetime import timedelta
    from decimal import Decimal
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.services.portfolio_closure import ClosureIntent, close_portfolio
    from app.services.trading import Order, execute
    from app.services.portfolios import OwnedActivePortfolio
    from app.services.stock_ownership import assert_ownership_consistent

    ids = {}
    async with factory.begin() as db:
        if (await db.execute(text("SELECT count(*) FROM users"))).scalar_one():
            raise ValueError("empty synthetic identity space required")
        coins = list(
            (
                await db.execute(
                    text(
                        "SELECT coin_id FROM stock_instruments ORDER BY coin_id LIMIT 2"
                    )
                )
            ).scalars()
        )
        # Declared fixture opening rows still obey the successor trigger's
        # instrument-first lock contract; no financial guard is bypassed.
        for coin in coins:
            await db.execute(
                text(
                    "SELECT pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:' || CAST(:c AS text),0))"
                ),
                {"c": str(coin)},
            )
        owner = (
            await db.execute(
                text(
                    "INSERT INTO users(email) VALUES ('strategy@closure-fixture.invalid') RETURNING id"
                )
            )
        ).scalar_one()
        zero = (
            await db.execute(
                text(
                    "INSERT INTO users(email) VALUES ('zero@closure-fixture.invalid') RETURNING id"
                )
            )
        ).scalar_one()
        for uid, name in ((owner, "Mixed"), (zero, "Zero")):
            pid = (
                await db.execute(text("SELECT initialize_portfolio(:u)"), {"u": uid})
            ).scalar_one()
            await db.execute(
                text("SELECT * FROM update_portfolio_metadata(:u,:p,:n,'',true,true)"),
                {"u": uid, "p": pid, "n": name},
            )
            ids[name] = (uid, pid)
        for n, name in enumerate(("Active", "Crypto", "Blank"), 1):
            pid = (
                await db.execute(
                    text(
                        "SELECT portfolio_id FROM create_portfolio(:u,:k,:n,'fixture strategy')"
                    ),
                    {"u": owner, "k": UUID(int=n, version=4), "n": name},
                )
            ).scalar_one()
            ids[name] = (owner, pid)
        now = (await db.execute(text("SELECT clock_timestamp()"))).scalar_one()
        at = now - timedelta(days=10)
        for coin in coins:
            await db.execute(
                text(
                    "INSERT INTO stock_action_state(coin_id,health,admission_generation,journal_start_at,complete_from) VALUES (:c,'current',1,:at,:at)"
                ),
                {"c": coin, "at": at - timedelta(days=1)},
            )
        # Declared historical opening quantities/basis. The sold-out stock also
        # carries the immutable fill/facts/movement for its later actual sale.
        for coin, rows in (
            (coins[0], [("Mixed", 1, 2), ("Active", 3, 3)]),
            (coins[1], [("Mixed", 1, 2), ("Active", 2, 1)]),
        ):
            for name, seq, qty in rows:
                uid, pid = ids[name]
                when = at if name == "Mixed" else at + timedelta(days=2)
                await db.execute(
                    text(
                        "INSERT INTO holdings(user_id,portfolio_id,coin_id,quantity,cost_basis) VALUES (:u,:p,:c,:q,:b)"
                    ),
                    {"u": uid, "p": pid, "c": coin, "q": qty, "b": qty * 10},
                )
                await db.execute(
                    text(
                        "INSERT INTO stock_ownership_movements(user_id,portfolio_id,coin_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key) VALUES (:u,:p,:c,:s,:at,:at,:q,0,:q,0,:b,0,'opening',:k)"
                    ),
                    {
                        "u": uid,
                        "p": pid,
                        "c": coin,
                        "s": seq,
                        "at": when,
                        "q": qty,
                        "b": qty * 10,
                        "k": f"opening:{pid}:{coin}",
                    },
                )
        uid, pid = ids["Mixed"]
        sale_at = at + timedelta(days=1)
        trade = (
            await db.execute(
                text(
                    "INSERT INTO trades(user_id,portfolio_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key,created_at) VALUES (:u,:p,:c,'sell','quantity',2,2,10,:at,10,0,20,9980,:k,:at) RETURNING id"
                ),
                {
                    "u": uid,
                    "p": pid,
                    "c": coins[0],
                    "at": sale_at,
                    "k": UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
                },
            )
        ).scalar_one()
        await db.execute(
            text(
                "INSERT INTO stock_fill_facts(trade_id,portfolio_id,coin_id,user_id,provider_asset_id,symbol,company_name,listing_exchange,source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,observed_at,session_date,opens_at,closes_at,authority) SELECT t.id,t.portfolio_id,t.coin_id,t.user_id,'fixture-asset',c.symbol,c.name,i.listing_exchange,'alpaca','iex',10,10,10,0,:at,:at,:at,CAST(:at AS timestamptz)::date,CAST(:at AS timestamptz)-interval '1 hour',CAST(:at AS timestamptz)+interval '1 hour','{}'::jsonb FROM trades t JOIN coins c ON c.id=t.coin_id JOIN stock_instruments i ON i.coin_id=t.coin_id WHERE t.id=:t"
            ),
            {"t": trade, "at": sale_at},
        )
        await db.execute(
            text(
                "INSERT INTO stock_ownership_movements(user_id,portfolio_id,coin_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key,trade_id) VALUES (:u,:p,:c,2,:at,:at,-2,2,0,20,0,0,'fill',:k,:t)"
            ),
            {
                "u": uid,
                "p": pid,
                "c": coins[0],
                "at": sale_at,
                "k": f"fill:{trade}",
                "t": trade,
            },
        )
        await db.execute(
            text(
                "UPDATE holdings SET quantity=0,cost_basis=0 WHERE portfolio_id=:p AND coin_id=:c"
            ),
            {"p": pid, "c": coins[0]},
        )
        for name, cash in (("Mixed", Decimal("9980")), ("Active", Decimal("9960"))):
            await db.execute(
                text("UPDATE accounts SET cash=:cash WHERE id=:p"),
                {"cash": cash, "p": ids[name][1]},
            )
        btc = (
            await db.execute(
                text("SELECT id FROM coins WHERE symbol='BTC' AND asset_class='crypto'")
            )
        ).scalar_one()
        await db.execute(
            text(
                "INSERT INTO prices(coin_id,mid,as_of,source) VALUES (:c,10000,clock_timestamp(),'fake')"
            ),
            {"c": btc},
        )
    app_factory = async_sessionmaker(app_engine, expire_on_commit=False)
    for index, name in enumerate(("Mixed", "Crypto", "Active"), 1):
        async with app_factory() as db:
            result, new = await execute(
                db,
                portfolio=OwnedActivePortfolio(ids[name][1], ids[name][0]),
                order=Order("BTC", "buy", "usd", Decimal("100")),
                expected_mid=Decimal("10000"),
                idempotency_key=UUID(int=100 + index, version=4),
                settings=settings,
            )
            if not new or result.cash_after != (
                {"Mixed": Decimal("9880"), "Crypto": Decimal("9900"), "Active": Decimal("9860")}[name]
            ):
                raise ValueError("actual crypto execution oracle")
            await db.commit()
    await dividend_seed(factory, scheduler_engine, ids, coins[1], now, helpers)
    async with app_factory() as db:
        refused = await close_portfolio(
            db,
            ClosureIntent(
                owner, ids["Active"][1], UUID(int=200, version=4), "Old reviewed name"
            ),
        )
        if refused.outcome != "confirmation_changed":
            raise ValueError("terminal refused intent required")
    for index, name in enumerate(("Mixed", "Crypto", "Blank", "Zero"), 201):
        async with app_factory() as db:
            outcome = await close_portfolio(
                db,
                ClosureIntent(
                    ids[name][0], ids[name][1], UUID(int=index, version=4), name
                ),
            )
            if outcome.outcome != "closed":
                raise ValueError("real same-transaction closure proof required")
    for coin in coins:
        async with factory() as db:
            await assert_ownership_consistent(db, coin)
            await db.rollback()


async def dividend_seed(factory, scheduler_engine, ids, coin, now, helpers):
    """Declared historical announcements/entitlements; actual payment/hold."""
    from dataclasses import asdict, replace
    from datetime import timedelta
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.models.stock import StockDataAdmission
    from app.services.stock_sessions import build_sessions
    from app.services.dividends import process_dividend, record_dividend_hold

    async with factory.begin() as db:
        base = helpers["admission"](now)
        calendar = replace(
            base,
            product="calendar",
            scope={**base.scope, "feed": "iex"},
            quota={**base.quota, "retention_seconds": 86400},
            allowed_fields=["exchange", "session_date", "opens_at", "closes_at"],
            calendar={
                "exchanges": ["XNYS", "XNAS"],
                "version": "exchange-calendars-4.13.2/synthetic-fixture",
                "sources": [
                    "https://www.nyse.com/trade/hours-calendars",
                    "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
                ],
                "review_valid_until": (now + timedelta(hours=2)).isoformat(),
                "coverage_start": (now.date() - timedelta(days=45)).isoformat(),
                "coverage_end": (now.date() + timedelta(days=90)).isoformat(),
                "overrides": [],
            },
        )
        reference = replace(
            base,
            product="reference",
            scope={**base.scope, "feed": "iex"},
            quota={**base.quota, "retention_seconds": 86400},
            allowed_fields=["symbol", "name", "exchange", "provider_asset_id"],
        )
        db.add_all(
            [StockDataAdmission(**asdict(item)) for item in (base, calendar, reference)]
        )
        await db.execute(
            text(
                "UPDATE stock_instruments SET provider_asset_id='closure-synthetic-asset',provider_verified_at=:n WHERE coin_id=:c"
            ),
            {"n": now, "c": coin},
        )
        await db.execute(
            text(
                "UPDATE stock_action_state SET checked_at=:n,coverage_start=:start,covered_until=:n,valid_until=:end WHERE coin_id=:c"
            ),
            {
                "n": now,
                "start": now - timedelta(days=15),
                "end": now + timedelta(hours=1),
                "c": coin,
            },
        )
        exchange = (
            await db.execute(
                text("SELECT listing_exchange FROM stock_instruments WHERE coin_id=:c"),
                {"c": coin},
            )
        ).scalar_one()
        session = max(
            (
                s
                for s in build_sessions(now, calendar)
                if s.exchange == exchange and s.opens_at and s.opens_at < now
            ),
            key=lambda s: s.opens_at,
        )
        cutoff = session.opens_at
        await db.execute(
            text(
                "INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation) VALUES (:e,:d,:o,:cl,:d,:d,1)"
            ),
            {
                "e": exchange,
                "d": session.session_date,
                "o": cutoff,
                "cl": session.closes_at,
            },
        )
        targets = []
        for key, paid in (
            ("closure-paid-dividend", True),
            ("closure-earned-unpaid", False),
        ):
            eid, rid = await helpers["event"](db, coin, key, now)
            terms = {
                "event_type": "cash_dividend",
                "currency": "USD",
                "subtype": "ordinary",
                "foreign": False,
                "special": False,
                "due_bills": False,
                "identity_verified": True,
                "dates_verified": True,
                "cancelled": False,
                "identity_changed": False,
                "rate": "0.25",
                "ex_date": str(cutoff.date()),
                "record_date": str(cutoff.date()),
                "payable_date": str(
                    cutoff.date() if paid else (now + timedelta(days=1)).date()
                ),
            }
            fp = helpers["digest"]([key])
            await db.execute(
                text(
                    "UPDATE stock_action_revisions SET classification='supported_dividend',normalized_terms=CAST(:t AS jsonb),verified_cutoff=:cut WHERE id=:r"
                ),
                {"t": json.dumps(terms), "cut": cutoff, "r": rid},
            )
            for name, quantity in (("Mixed", 2), ("Active", 1)):
                uid, pid = ids[name]
                efp = helpers["digest"]([key, pid])
                ent = (
                    await db.execute(
                        text(
                            "INSERT INTO stock_dividend_entitlements(event_id,portfolio_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,last_movement_sequence,eligible_quantity,state,fingerprint) VALUES (:e,:p,:u,:r,:cut,'exclusive-regular-session-open',1,'unit_epoch:0',0,2,:q,'eligible',:fp) RETURNING id"
                        ),
                        {
                            "e": eid,
                            "p": pid,
                            "u": uid,
                            "r": rid,
                            "cut": cutoff,
                            "q": quantity,
                            "fp": efp,
                        },
                    )
                ).scalar_one()
                if paid:
                    targets.append(
                        {
                            "portfolio_id": pid,
                            "event_id": eid,
                            "entitlement_id": ent,
                            "expected_revision_fingerprint": fp,
                            "expected_entitlement_fingerprint": efp,
                        }
                    )
    scheduled = async_sessionmaker(scheduler_engine, expire_on_commit=False)
    payments = []
    for target in targets:
        async with scheduled() as db:
            payments.append(await process_dividend(db, **target))
    async with factory.begin() as db:
        eid = targets[0]["event_id"]
        sid = (
            await db.execute(
                text("SELECT source_id FROM stock_action_revisions WHERE event_id=:e"),
                {"e": eid},
            )
        ).scalar_one()
        fp = helpers["digest"](["closure-uncertain-correction"])
        rid = (
            await db.execute(
                text(
                    "INSERT INTO stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason) VALUES (:e,:s,2,:fp,'update',clock_timestamp(),1,'{}','uncertain','source_gap') RETURNING id"
                ),
                {"e": eid, "s": sid, "fp": fp},
            )
        ).scalar_one()
        await db.execute(
            text("UPDATE stock_action_events SET current_revision_id=:r WHERE id=:e"),
            {"r": rid, "e": eid},
        )
    async with scheduled() as db:
        held = await record_dividend_hold(
            db,
            portfolio_id=ids["Mixed"][1],
            payment_id=payments[0].payment_id,
            expected_revision_fingerprint=fp,
        )
        if held.outcome != "held_uncertain":
            raise ValueError("actual held correction required")


async def project(db, *, columns=None, identities=None):
    from sqlalchemy import text
    from app.services.stock_ownership import assert_ownership_consistent

    if columns is None:
        contract = producer()
        columns = contract.contract_columns("0023")
        identities = contract.identity_tables("0023")
    if (
        await db.execute(text("SELECT version_num FROM alembic_version"))
    ).scalar_one() != "0023":
        raise ValueError("0023 schema before projection")
    coins = list(
        (
            await db.execute(
                text(
                    "SELECT DISTINCT coin_id FROM stock_ownership_movements ORDER BY coin_id"
                )
            )
        ).scalars()
    )
    # The caller provides a business session. Each single-instrument proof keeps
    # its guard; separate completed read transactions never clear db.info.
    for coin in coins:
        await assert_ownership_consistent(db, coin)
        await db.rollback()
    tables = {}
    for table in sorted(columns):
        fields = columns[table]
        key = (
            "id"
            if "id" in fields
            else "trade_id"
            if "trade_id" in fields
            else "coin_id"
            if "coin_id" in fields
            else "version_num"
        )
        raw = (
            await db.execute(
                text(
                    "SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY "
                    + key
                    + "),'[]'::jsonb)::text FROM public."
                    + table
                    + " t"
                )
            )
        ).scalar_one()
        tables[table] = json.loads(raw, parse_float=str)
    tails = {}
    for table in identities:
        tails[table] = list(
            (
                await db.execute(
                    text("SELECT last_value,is_called FROM public." + table + "_id_seq")
                )
            ).one()
        )
    return {"revision": "0023", "tables": tables, "sequences": tails}


async def replay_restored(factory, settings, app_engine, scheduler_engine, before,
                          *, columns, identities):
    """Retry actual original services after the complete restored comparison."""
    from contextlib import asynccontextmanager
    from dataclasses import asdict
    from datetime import datetime
    from decimal import Decimal
    from uuid import UUID
    from fastapi import HTTPException
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.user import User
    from app.schemas.portfolios import PortfolioCreate
    from app.services.portfolios import create_portfolio, list_active_portfolios, OwnedActivePortfolio
    from app.services.trading import execute, Order
    from app.services.dividends import process_dividend, DividendRefused

    tables = before['tables']
    roots = {row['name']: row for row in tables['accounts']}
    active, closed = roots['Active'], roots['Mixed']
    @asynccontextmanager
    async def restricted(engine, role):
        assert role in {'birja_app', 'birja_scheduler'}
        async with engine.connect() as conn:
            assert (await conn.execute(text(
                'SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'
            ))).scalar_one()
            await conn.commit()
            await conn.execute(text('SET ROLE ' + role))
            await conn.commit()
            try:
                identity = (await conn.execute(text(
                    'SELECT session_user,current_user,NOT (rolsuper OR rolinherit OR '
                    'rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls) '
                    'FROM pg_roles WHERE rolname=current_user'
                ))).one()
                assert identity == ('birja_ops_bootstrap', role, True)
                await conn.commit()
                async with AsyncSession(bind=conn, expire_on_commit=False) as db:
                    yield db
            finally:
                await conn.rollback()
                await conn.execute(text('RESET ROLE'))
                await conn.commit()

    def app():
        return restricted(app_engine, 'birja_app')

    def scheduler():
        return restricted(scheduler_engine, 'birja_scheduler')

    for role, sessions in (('app', app), ('scheduler', scheduler)):
        async with sessions() as db:
            assert (await db.execute(text('SELECT current_user'))).scalar_one() == 'birja_'+role
            assert (await db.execute(text('SELECT session_user'))).scalar_one() == 'birja_ops_bootstrap'
            await db.rollback()

    async def active_lists():
        result = {}
        for user in tables['users']:
            async with app() as db:
                values = await list_active_portfolios(db, User(id=user['id']))
                result[user['id']] = [(value.id, value.name) for value in values]
                await db.rollback()
        return result

    lists_before = await active_lists()
    assert lists_before[roots['Zero']['user_id']] == []
    assert lists_before[active['user_id']] == [(active['id'], 'Active')]
    creation = next(row for row in tables['portfolio_creations'] if row['portfolio_id'] == active['id'])
    async with app() as db:
        metadata, replayed = await create_portfolio(db, User(id=creation['user_id']),
            UUID(creation['creation_key']), PortfolioCreate(**creation['canonical_payload']))
        assert replayed and metadata.id == active['id']
        assert (metadata.name, metadata.description) == (active['name'], active['description'])

    original = next(row for row in tables['trades']
                    if row['portfolio_id'] == active['id']
                    and row['idempotency_key'] == str(UUID(int=103, version=4)))
    async with app() as db:
        fill, new = await execute(db, portfolio=OwnedActivePortfolio(active['id'], active['user_id']),
            order=Order('BTC', 'buy', 'usd', Decimal('100')), expected_mid=Decimal('10000'),
            idempotency_key=UUID(original['idempotency_key']), settings=settings)
        assert not new
        expected_fill = {
            'portfolio_id': active['id'], 'trade_id': original['id'],
            'created_at': datetime.fromisoformat(original['created_at']), 'symbol': 'BTC',
            'side': original['side'], 'input_kind': original['input_kind'],
            'input_value': Decimal(original['input_value']), 'mid': Decimal(original['mid_price']),
            'as_of': datetime.fromisoformat(original['price_as_of']),
            **{key: Decimal(original[key]) for key in
               ('exec_price', 'quantity', 'fee', 'cash_delta', 'cash_after')},
            'notional': -Decimal(original['cash_delta'])-Decimal(original['fee']),
        }
        assert asdict(fill) == expected_fill

    payment = next(row for row in tables['stock_dividend_payments'] if row['portfolio_id'] == active['id'])
    async with scheduler() as db:
        paid = await process_dividend(db, portfolio_id=active['id'], event_id=payment['event_id'],
            entitlement_id=payment['entitlement_id'],
            expected_revision_fingerprint=payment['revision_fingerprint'],
            expected_entitlement_fingerprint=payment['entitlement_fingerprint'])
        assert paid.payment_id == payment['id'] and paid.outcome == 'original'

    closed_creation = next(row for row in tables['portfolio_creations'] if row['portfolio_id'] == closed['id'])
    async with app() as db:
        try:
            await create_portfolio(db, User(id=closed['user_id']), UUID(closed_creation['creation_key']),
                PortfolioCreate(**closed_creation['canonical_payload']))
        except HTTPException as error:
            assert error.status_code == 404 and error.detail == {'code': 'portfolio_unavailable'}
        else:
            raise AssertionError('closed original creation admitted')
    closed_fill = next(row for row in tables['trades'] if row['portfolio_id'] == closed['id']
                       and row['idempotency_key'] == str(UUID(int=101, version=4)))
    async with app() as db:
        try:
            await execute(db, portfolio=OwnedActivePortfolio(closed['id'], closed['user_id']),
                order=Order('BTC', 'buy', 'usd', Decimal('100')), expected_mid=Decimal('10000'),
                idempotency_key=UUID(closed_fill['idempotency_key']), settings=settings)
        except HTTPException as error:
            assert error.status_code == 404 and error.detail == {'code': 'portfolio_unavailable'}
        else:
            raise AssertionError('closed original fill admitted')
    closed_payment = next(row for row in tables['stock_dividend_payments'] if row['portfolio_id'] == closed['id'])
    async with scheduler() as db:
        try:
            await process_dividend(db, portfolio_id=closed['id'], event_id=closed_payment['event_id'],
                entitlement_id=closed_payment['entitlement_id'],
                expected_revision_fingerprint=closed_payment['revision_fingerprint'],
                expected_entitlement_fingerprint=closed_payment['entitlement_fingerprint'])
        except DividendRefused as error:
            assert error.code == 'portfolio_unavailable'
        else:
            raise AssertionError('closed original dividend admitted')

    assert await active_lists() == lists_before
    async with factory() as db:
        after = await project(db, columns=columns, identities=identities)
    assert after['tables'] == tables
    changes = {}
    for name, (last, called) in before['sequences'].items():
        actual_last, actual_called = after['sequences'][name]
        assert actual_last >= last and (not called or actual_called)
        if [actual_last, actual_called] != [last, called]:
            changes[name] = {'before': [last, called], 'after': [actual_last, actual_called]}
    return after, {'restored_original_retries': True, 'active_creation_id': metadata.id,
        'active_fill_id': fill.trade_id, 'active_payment_id': paid.payment_id,
        'closed_refusals': 3, 'sequence_changes': changes,
        'restricted_identity_mode': 'owned-login-set-role'}


def private_snapshot(path, existing):
    path = Path(path)
    if (
        not path.is_absolute()
        or path.is_symlink()
        or path.resolve() != path
        or not str(path).startswith("/tmp/birja-")
        or path.exists() != existing
    ):
        raise ValueError("owned private snapshot required")
    if existing and (
        not path.is_file()
        or path.stat().st_mode & 0o077
        or path.stat().st_uid != os.getuid()
    ):
        raise ValueError("private immutable snapshot required")
    return path


def save_snapshot(path, value):
    require_projection(value)
    path = private_snapshot(path, False)
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(canonical(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_snapshot(path, digest, value):
    path = private_snapshot(path, True)
    if (
        not isinstance(digest, str)
        or not re.fullmatch("[0-9a-f]{64}", digest)
        or hashlib.sha256(path.read_bytes()).hexdigest() != digest
    ):
        raise ValueError("before-backup snapshot hash required")
    require_projection(value)
    expected = require_projection(json.loads(path.read_bytes()))
    if canonical(value) != canonical(expected):
        raise ValueError("restored lifecycle/finance/sequence evidence changed")
    return digest


def program(*, mode, database=None, expected=None, before=None):
    if (
        mode not in {"create", "projection", "verify", "compare", "replay-restored"}
        or database not in {None, "birja_restore_test"}
        or (mode == "create" and database)
    ):
        raise ValueError("unsafe closure fixture mode/database")
    if mode in {"compare", "replay-restored"} and (
        not isinstance(expected, str) or not re.fullmatch("[0-9a-f]{64}", expected)
    ):
        raise ValueError("before-backup snapshot hash required")
    if mode == 'replay-restored':
        if database != 'birja_restore_test':
            raise ValueError('restored database required for original retries')
        require_projection(before)
        if hashlib.sha256(canonical(before)).hexdigest() != expected:
            raise ValueError('before-backup snapshot hash required')
    contract = producer()
    _, common = historical_helpers(load_backend=False)
    # The explicit 0023 database lane also runs in the 0024 campaign. Bind
    # its executable to the source profile that was authenticated above.
    source_pins = contract.CLOSURE_SOURCE_SHA256
    if (ROOT / "backend/alembic/versions/0024_stock_halt_snapshot.py").is_file():
        contract.require_closure_source(ROOT, revision="0024")
        source_pins = contract.REPORTED_HALT_SOURCE_SHA256
    pins = {
        name.removeprefix("backend/"): sha
        for name, sha in source_pins.items()
        if name.startswith("backend/")
    }
    code = (
        "DATABASE="
        + repr(database)
        + "\nMODE="
        + repr(mode)
        + "\nBEFORE_SNAPSHOT=" + repr(before)
        + "\nSOURCE_SHA256="
        + repr(pins)
        + "\n"
    )
    code += (
        "TABLE_COLUMNS="
        + repr({k: sorted(v) for k, v in contract.contract_columns("0023").items()})
        + "\nIDENTITY_TABLES="
        + repr(contract.identity_tables("0023"))
        + "\n"
    )
    code += r"""
import asyncio,hashlib,json,os,ssl
from pathlib import Path
for name,expected in SOURCE_SHA256.items():
 p=Path('/app')/name
 if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
  raise ValueError('0023 source mismatch before import')
import asyncpg
from urllib.parse import urlsplit,urlunsplit
async def declared():
 parts=urlsplit(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://'))
 if parts.hostname!='postgres' or parts.port!=5432 or parts.username!='birja_migrator' or parts.path!='/birja_source_test' or parts.query:
  raise ValueError('owned synthetic source identity required')
 if DATABASE:parts=parts._replace(path='/'+DATABASE)
 ca=os.environ.get('DATABASE_SSL_CA_FILE')
 if not ca:raise ValueError('verified TLS required')
 c=await asyncpg.connect(urlunsplit(parts),ssl=ssl.create_default_context(cafile=ca))
 try:
  if MODE=='create':
   if await c.fetchval("SELECT count(*) FROM pg_tables WHERE schemaname='public'"):
    raise ValueError('owned empty schema required')
  elif await c.fetchval('SELECT version_num FROM alembic_version')!='0023':
   raise ValueError('0023 only before import')
 finally:await c.close()
asyncio.run(declared())
"""
    code += (
        common
        + "\n"
        + "\n".join(inspect.getsource(fn) for fn in (seed, dividend_seed, project, replay_restored))
    )
    code += r"""
async def run():
 settings,engine,factory,args=setup()
 if MODE=='replay-restored':
  # Owned login enters existing NOLOGIN SQL authority for each service session.
  # The migrator factory remains the independent read-only oracle.
  replay_url=engine.url.set(username='birja_ops_bootstrap',password=os.environ['FIXTURE_BOOT_PASSWORD'])
  app=create_async_engine(replay_url,connect_args=args)
  scheduler=create_async_engine(replay_url,connect_args=args)
 else:
  app=create_async_engine(engine.url.set(username='birja_app',password=os.environ['FIXTURE_APP_PASSWORD']),connect_args=args)
  scheduler=create_async_engine(engine.url.set(username='birja_scheduler',password=os.environ['FIXTURE_SCHEDULER_PASSWORD']),connect_args=args)
 try:
  if MODE=='create':
   from alembic import command
   from alembic.config import Config
   await asyncio.to_thread(command.upgrade,Config('/app/alembic.ini'),'0023')
   from app.db.portfolio_bootstrap import PREFLIGHT_0023_SQL,GRANTS_0023_SQL
   async with engine.begin() as conn:
    raw=await conn.get_raw_connection()
    await raw.driver_connection.execute(PREFLIGHT_0023_SQL)
    await raw.driver_connection.execute(GRANTS_0023_SQL)
   await seed(factory,settings,app,scheduler,globals())
  async with factory() as db:
   value=await project(db,columns=TABLE_COLUMNS,identities=IDENTITY_TABLES)
   if MODE=='replay-restored':
    assert json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)==json.dumps(BEFORE_SNAPSHOT,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    value,replay=await replay_restored(factory,settings,app,scheduler,value,columns=TABLE_COLUMNS,identities=IDENTITY_TABLES)
    print('portfolio_restored_replay='+json.dumps(replay,sort_keys=True,separators=(',',':')))
   print('portfolio_projection='+json.dumps(value,sort_keys=True,separators=(',',':')))
   print('portfolio_verified_tls=true')
 finally:await app.dispose();await scheduler.dispose();await engine.dispose()
asyncio.run(run())
"""
    return code


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("mode", choices=["create", "projection", "verify", "compare", "replay-restored"])
    parser.add_argument("--database", choices=["birja_restore_test"])
    parser.add_argument("--snapshot")
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    before = None
    if args.mode == 'replay-restored':
        if args.database != 'birja_restore_test' or not args.snapshot:
            raise ValueError('restored database and before-backup snapshot required')
        path = private_snapshot(args.snapshot, True)
        before = json.loads(path.read_bytes())
        compare_snapshot(path, args.expected_sha256, before)
    code = program(mode=args.mode, database=args.database,
        expected=args.expected_sha256, before=before)
    if transport:
        value = transport(code)
    else:
        command = json.loads(os.environ["BIRJA_PORTFOLIO_FIXTURE_TRANSPORT"])
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(v, str) and v for v in command)
        ):
            raise ValueError("explicit owned argv required")
        result = subprocess.run(
            command, input=code.encode(), capture_output=True, timeout=300, check=True
        )
        rows = [
            r.split(b"=", 1)[1]
            for r in result.stdout.splitlines()
            if r.startswith(b"portfolio_projection=")
        ]
        if (
            len(rows) != 1
            or b"portfolio_verified_tls=true" not in result.stdout.splitlines()
        ):
            raise ValueError("exact TLS projection required")
        value = json.loads(rows[0])
        if args.mode == 'replay-restored':
            reports = [r.split(b'=', 1)[1] for r in result.stdout.splitlines()
                       if r.startswith(b'portfolio_restored_replay=')]
            if len(reports) != 1:
                raise ValueError('actual restored retry report required')
            value = {'projection': value, 'replay': json.loads(reports[0])}
    if args.mode == 'replay-restored':
        if not isinstance(value, dict) or set(value) != {'projection', 'replay'}:
            raise ValueError('actual restored retry report required')
        report = value['replay']
        if report.get('restored_original_retries') is not True or report.get('closed_refusals') != 3:
            raise ValueError('actual restored retry report required')
        value = value['projection']
        require_projection(value)
        if value['tables'] != before['tables']:
            raise ValueError('restored retry changed immutable tables')
        print('restored_original_retries=true')
        print('restored_retry_result='+json.dumps(report,sort_keys=True))
    require_projection(value)
    digest = (
        save_snapshot(args.snapshot, value)
        if args.mode == "projection"
        else compare_snapshot(args.snapshot, args.expected_sha256, value)
        if args.mode == "compare"
        else hashlib.sha256(canonical(value)).hexdigest()
    )
    print("portfolio_fixture_sha256=" + digest)
    return digest


if __name__ == "__main__":
    main()
