"""Explicit ephemeral browser inputs. No application/debug route imports this file.

The calendar DATASET alone is synthetic, so money tests run at any wall-clock
hour. Real calendar validation, DB clock, final guard and all services still run.
Only the uniquely named disposable Docker database is permitted.
"""

import asyncio
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit


def guard():
    url = urlsplit(os.environ.get("DATABASE_URL", ""))
    if not (
        os.environ.get("BIRJA_E2E_GUARD") == "phase09-isolated"
        and os.environ.get("ENV") == "dev"
        and os.environ.get("EMAIL_BACKEND") == "console"
        and url.hostname == "postgres"
        and url.username == "birja_e2e"
        and url.path == "/birja_e2e"
        and not os.environ.get("ALPACA_API_KEY")
        and not os.environ.get("ALPACA_SECRET_KEY")
    ):
        raise RuntimeError("Requires explicit disposable phase09 browser database")


def anchor():
    return datetime.fromisoformat(os.environ["BIRJA_E2E_ANCHOR"])


CONTROL = Path("/tmp/birja-e2e-calendar.json")


def patch_calendar():
    guard()
    from app.services import stock_sessions

    original = stock_sessions._calendar_bounds

    def bounds(alias, start, end):
        base = anchor()
        opens, closes = base - timedelta(hours=1), base + timedelta(hours=1)
        if CONTROL.exists():
            data = json.loads(CONTROL.read_text())
            if data["state"] == "closed":
                closes = datetime.fromisoformat(data["at"])
        return tuple(
            (day, opens, closes) if day == base.date() else (day, op, cl)
            for day, op, cl in original(alias, start, end)
        )

    stock_sessions._calendar_bounds = bounds


def admission(product):
    from app.services.stock_admission import ProductAdmission
    from app.services.stock_quote_rules import CURATED_SYMBOLS

    base = anchor()
    fields = {
        "reference": ["symbol", "name", "exchange", "provider_asset_id"],
        "quotes": ["bid", "ask", "event_at", "symbol"],
        "actions": ["provider_event_id", "symbol", "event_type", "process_date"],
        "status": ["symbol", "status", "event_at"],
        "calendar": ["exchange", "session_date", "opens_at", "closes_at"],
    }
    scope = {
        "application": "birja",
        "audience": "authenticated-users",
        "account": "birja",
        "server": "birja",
        "feed": "iex",
        "durable_accounting": True,
        "backup_restore": True,
        "retention_mode": "durable-accounting",
    }
    if product == "actions":
        scope.update(
            feed="alpaca-corporate-actions",
            capabilities=["rest", "replay"],
            rest_symbols=sorted(CURATED_SYMBOLS),
            replay_region="us",
            all_us_replay_ingress=True,
        )
    calendar = (
        {}
        if product != "calendar"
        else {
            "exchanges": ["XNYS", "XNAS"],
            "version": "exchange-calendars-4.13.2/synthetic-browser-dataset",
            "sources": [
                "https://www.nyse.com/trade/hours-calendars",
                "https://www.nasdaq.com/market-activity/stock-market-holiday-schedule",
            ],
            "review_valid_until": (base + timedelta(hours=2)).isoformat(),
            "coverage_start": (base.date() - timedelta(days=45)).isoformat(),
            "coverage_end": (base.date() + timedelta(days=90)).isoformat(),
            "overrides": [],
        }
    )
    return ProductAdmission(
        product=product,
        state="approved",
        generation=4,
        reviewed_at=base - timedelta(hours=1),
        valid_from=base - timedelta(hours=1),
        valid_until=base + timedelta(hours=2),
        evidence_ref="synthetic-browser-only:no-provider-rights",
        terms_version="synthetic-v1",
        collection_allowed=True,
        display_allowed=True,
        derived_allowed=True,
        retention_allowed=True,
        scope=scope,
        quota={
            "requests_per_minute": 20,
            "symbols_per_request": 20,
            "max_response_bytes": 262144,
            "retention_seconds": 315360000 if product == "actions" else 86400,
        },
        allowed_fields=fields[product],
        attribution="IEX prices · synthetic test authority",
        calendar=calendar,
    )


async def prepare(operation, symbol="AAPL", argument=""):
    guard()
    if operation not in {
        "fresh",
        "open",
        "close",
        "status",
        "halt",
        "hold",
        "reprice",
        "stale",
        "long-name",
    }:
        raise ValueError("Unknown synthetic fixture operation")
    from app.models.corporate_action import StockActionState
    from app.models.price import Coin
    from app.models.stock import (
        StockDataAdmission,
        StockInstrument,
        StockQuote,
        StockSession,
    )
    from app.models.stock_execution import StockStatusEvidence
    from app.services.stock_sessions import build_sessions
    from app.services.stock_status import persist_status_batch
    from app.services.stock_status_rules import StatusBatch, StatusEvent
    from sqlalchemy import delete, func, select, update
    from sqlalchemy.dialects.postgresql import insert
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(os.environ["DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory.begin() as db:
            if (
                await db.execute(select(func.current_database()))
            ).scalar_one() != "birja_e2e":
                raise RuntimeError("Disposable database mismatch")
            now = (await db.execute(select(func.clock_timestamp()))).scalar_one()
            if operation in ("fresh", "open", "close"):
                CONTROL.write_text(
                    json.dumps(
                        {
                            "state": "closed" if operation == "close" else "open",
                            "at": now.isoformat(),
                        }
                    )
                )
                for product in ("reference", "quotes", "actions", "status", "calendar"):
                    await db.execute(
                        insert(StockDataAdmission)
                        .values(**asdict(admission(product)))
                        .on_conflict_do_nothing(index_elements=["product"])
                    )
                await db.execute(delete(StockSession))
                await db.execute(
                    insert(StockSession),
                    [asdict(row) for row in build_sessions(now, admission("calendar"))],
                )
            rows = (
                await db.execute(
                    select(StockInstrument, Coin.symbol)
                    .join(Coin)
                    .order_by(StockInstrument.coin_id)
                )
            ).all()
            if len(rows) != 20:
                raise RuntimeError("Expected exact twenty-stock fixture catalogue")
            await db.commit()
            for instrument, ticker in rows:
                async with factory.begin() as item_db:
                    cid = instrument.coin_id
                    db = item_db
                    instrument = await db.get(StockInstrument, cid)
                    if operation == "fresh":
                        instrument.provider_asset_id = "synthetic-browser-" + ticker
                        instrument.provider_verified_at = anchor()
                        await db.flush()
                        await db.execute(
                            insert(StockActionState)
                            .values(
                                coin_id=cid,
                                admission_generation=4,
                                health="current",
                                checked_at=now,
                                valid_until=now + timedelta(hours=1),
                                journal_start_at=anchor() - timedelta(days=5),
                                complete_from=anchor() - timedelta(days=5),
                                coverage_start=anchor() - timedelta(days=5),
                                covered_until=now,
                            )
                            .on_conflict_do_update(
                                index_elements=["coin_id"],
                                set_={
                                    "health": "current",
                                    "checked_at": now,
                                    "valid_until": now + timedelta(hours=1),
                                    "covered_until": now,
                                },
                            )
                        )
                        await db.execute(
                            insert(StockQuote)
                            .values(
                                coin_id=cid,
                                bid=Decimal(100),
                                ask=Decimal(102),
                                mid=Decimal(101),
                                source="alpaca",
                                feed="iex",
                                event_at=now,
                                collected_at=now,
                                session_date=now.date(),
                                admission_generation=4,
                                unit_epoch=0,
                            )
                            .on_conflict_do_update(
                                index_elements=["coin_id"],
                                set_={
                                    "bid": Decimal(100),
                                    "ask": Decimal(102),
                                    "mid": Decimal(101),
                                    "event_at": now,
                                    "collected_at": now,
                                },
                            )
                        )
                    if operation in ("fresh", "status", "halt", "open") and (
                        operation != "halt" or ticker == symbol
                    ):
                        old = await db.get(StockStatusEvidence, cid)
                        sequence = old.sequence + 1 if old else 1
                        batch = StatusBatch(
                            events=(
                                StatusEvent(
                                    cid,
                                    instrument.provider_asset_id,
                                    "halted" if operation == "halt" else "normal",
                                    now,
                                    now.date(),
                                    sequence,
                                    "synthetic-browser-status",
                                ),
                            ),
                            observed_at=now,
                            admission_generation=4,
                            continuity_generation=old.continuity_generation + 1
                            if old
                            else 1,
                            baseline_verified=True,
                            contiguous=True,
                            complete=True,
                            end_marker=True,
                        )
                        await persist_status_batch(db, batch, coin_id=cid)
                    if ticker != symbol:
                        continue
                    if operation == "reprice":
                        bid, ask = (Decimal(100), Decimal(argument or "103"))
                        await db.execute(
                            update(StockQuote)
                            .where(StockQuote.coin_id == cid)
                            .values(
                                bid=bid,
                                ask=ask,
                                mid=(bid + ask) / 2,
                                event_at=now,
                                collected_at=now,
                            )
                        )
                    elif operation == "hold":
                        await db.execute(
                            update(StockActionState)
                            .where(StockActionState.coin_id == cid)
                            .values(
                                health="unknown",
                                epoch=StockActionState.epoch + 1,
                                valid_until=None,
                            )
                        )
                    elif operation == "long-name":
                        await db.execute(
                            update(Coin)
                            .where(Coin.id == cid)
                            .values(
                                name=(
                                    "Apple Long Company Name "
                                    + "UnbrokenReferenceName" * 5
                                )[:64]
                            )
                        )
                    elif operation == "stale":
                        await db.execute(
                            update(StockQuote)
                            .where(StockQuote.coin_id == cid)
                            .values(
                                event_at=now - timedelta(seconds=120),
                                collected_at=now - timedelta(seconds=120),
                            )
                        )
    finally:
        await engine.dispose()
    print("synthetic_fixture_ready=" + operation)


if __name__ == "__main__":
    guard()
    sys.path.insert(0, "/app")
    patch_calendar()
    if sys.argv[1] == "serve":
        import uvicorn

        uvicorn.run("app.main:create_app", factory=True, host="0.0.0.0", port=8000)
    else:
        asyncio.run(prepare(*sys.argv[1:]))
