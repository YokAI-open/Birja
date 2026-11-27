"""Explicit ephemeral browser inputs. No application/debug route imports this file.

The calendar DATASET alone is synthetic, so money tests run at any wall-clock
hour. Real calendar validation, DB clock, final guard and all services still run.
Only the uniquely named disposable Docker database is permitted.
"""

import asyncio
import json
import os
import re
import secrets
import sys
from contextlib import asynccontextmanager, suppress
from dataclasses import asdict
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit
from uuid import NAMESPACE_URL, uuid5


def guard():
    url = urlsplit(os.environ.get("DATABASE_URL", ""))
    if not (
        os.environ.get("BIRJA_E2E_GUARD") == "phase09-isolated"
        and os.environ.get("ENV") == "dev"
        and os.environ.get("EMAIL_BACKEND") == "console"
        and url.hostname == "postgres"
        and url.username == "birja"
        and url.path == "/birja"
        and os.environ.get("COMPOSE_PROJECT_NAME") == "birja-phase09-e2e-test"
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
        window_start = base - timedelta(hours=1)
        window_end = base + timedelta(hours=1)
        data = {}
        if CONTROL.exists():
            data = json.loads(CONTROL.read_text())
        closed_at = datetime.fromisoformat(data["at"]) if data.get("state") == "closed" else None
        action_day = date.fromisoformat(data["session_date"]) if "session_date" in data else None
        rows = []
        for day, opens, closes in original(alias, start, end):
            if base.date() <= day <= window_end.date():
                midnight = datetime.combine(day, time.min, UTC)
                if midnight < window_end:
                    opens = max(midnight, window_start)
                    closes = min(midnight + timedelta(days=1), window_end)
            if closed_at is not None and day == closed_at.date():
                closes = closed_at
            if day == action_day:
                opens = datetime.fromisoformat(data["opens"])
                closes = datetime.fromisoformat(data["closes"])
            rows.append((day, opens, closes))
        return tuple(rows)

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
        reviewed_at=base if product == "calendar" else base - timedelta(hours=1),
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
            ).scalar_one() != "birja":
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
                    .where(Coin.is_active)
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
                                    "session_date": now.date(),
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


CATALOG_OUTAGE = Path("/tmp/birja-e2e-catalog-outage")
CATALOG_REQUESTS = Path("/tmp/birja-e2e-catalog-requests")
CATALOG_TRADED = "FQZT"
CATALOG_MIXED = "FQZM"
CATALOG_VENUES = {
    "FQXA": "NASDAQ", "FQXB": "NASDAQ", "FQX": "NYSE",
    CATALOG_TRADED: "NASDAQ", CATALOG_MIXED: "NASDAQ",
}
CATALOG_PRICES = {
    "FQXA": (17, 19), "FQXB": (24, 26), "FQX": (31, 33),
    CATALOG_TRADED: (101, 103), CATALOG_MIXED: (101, 103),
}


def catalog_guard():
    guard()
    if os.environ.get("BIRJA_E2E_CATALOG") != "1":
        raise RuntimeError("Requires the catalog browser fixture")


def digest(value):
    return sha256(value.encode()).hexdigest()


def catalog_manifest(now, reused, traded_reused=False):
    from app.services.stock_catalog_classification import InventoryRow
    from app.services.stock_catalog_sources import CatalogAlias
    from app.tasks.stock_catalog_inventory import (
        CatalogManifest,
        SourceEvidence,
        _coverage,
    )

    long_name = "Quartz Fixture International Research and Materials Holdings"
    issues = (
        ("nasdaqlisted", 1, "FQXA", "quartz-a", long_name, "A", "FQOLD"),
        ("nasdaqlisted", 2, "FQXB", "quartz-b", long_name, "B", None),
        (
            "nasdaqlisted",
            3,
            CATALOG_TRADED,
            "trade-replacement" if traded_reused else "trade-original",
            "Replacement Trade Fixture" if traded_reused else "Synthetic Trade Research",
            None,
            None,
        ),
        ("nasdaqlisted", 4, CATALOG_MIXED, "mixed", "Synthetic Mixed Research", None, None),
        (
            "otherlisted",
            1,
            "FQX",
            "replacement" if reused else "original",
            "Replacement Fixture" if reused else "Original Fixture",
            None,
            None,
        ),
    )
    rows = tuple(
        InventoryRow(
            source=source,
            row_key=f"{source}:{position}",
            row_digest=digest(f"{source}:{ticker}:{identity}"),
            ticker=ticker,
            listing_exchange=CATALOG_VENUES[ticker],
            company_name=name,
            name_source=source,
            classification="common_stock",
            share_class=share_class,
            identity_key=f"review:{digest(identity)}",
            aliases=(CatalogAlias(namespace="nasdaq", symbol=alias),) if alias else (),
            disposition="included",
            reason="reviewed_issue_evidence",
            evidence_at=now - timedelta(minutes=1),
            evidence_digest=digest(f"classification:{identity}"),
        )
        for source, position, ticker, identity, name, share_class, alias in issues
    )
    return CatalogManifest(
        mode="fixture",
        sources=(
            SourceEvidence(
                artifact="nasdaqlisted",
                sha256=digest(f"NASDAQ:{now}"),
                published_at=now - timedelta(minutes=2),
                row_count=4,
            ),
            SourceEvidence(
                artifact="otherlisted",
                sha256=digest(f"NYSE:{now}"),
                published_at=now - timedelta(minutes=2),
                row_count=1,
            ),
        ),
        rights=(),
        rows=rows,
        coverage=_coverage(rows),
        complete=True,
    )


async def admit_catalog_mapping(db, listing, now):
    import httpx
    from app.models.stock_catalog import StockCatalogAdmission
    from app.services.stock_catalog_provider import (
        CatalogAssetAdmission,
        CatalogAssetTarget,
        CatalogUnitEvidence,
        stage_catalog_assets,
    )
    from app.services.stock_catalog_publish import promote_catalog_mappings

    target = CatalogAssetTarget(
        catalog_id=listing.security_id,
        listing_version=listing.id,
        listing_exchange=listing.listing_exchange,
        provider_symbol=listing.ticker,
    )
    unit = CatalogUnitEvidence(
        target=target,
        currency="USD",
        units_per_share=1,
        classification="common_stock",
        reviewed_at=now - timedelta(minutes=1),
        valid_until=now + timedelta(hours=2),
        evidence_digest=digest(f"units:{listing.id}"),
    )
    purposes = frozenset(
        {"collection", "internal_use", "derived_use", "display", "storage", "backup"}
    )
    authority = CatalogAssetAdmission(
        account="birja",
        server="birja",
        environment="paper",
        reviewed_at=unit.reviewed_at,
        valid_until=unit.valid_until,
        evidence_digest=digest(f"mapping:{listing.id}"),
        targets=(target,),
        purposes=purposes,
        request_limit=1,
    )
    grant = StockCatalogAdmission(
        artifact="alpaca_assets",
        reference="Synthetic browser asset mapping",
        reviewed_at=authority.reviewed_at,
        valid_until=authority.valid_until,
        fields={
            field: sorted(purposes)
            for field in (
                "provider_asset_id",
                "provider_symbol",
                "asset_evidence",
                "currency",
                "units_per_share",
                "unit_evidence",
            )
        },
        scope={
            "provider": authority.model_dump(mode="json"),
            "units": [unit.model_dump(mode="json")],
        },
    )
    db.add(grant)
    await db.flush()

    def asset_reply(request):
        if request.url.path != f"/v2/assets/{listing.ticker}":
            raise ValueError("Unexpected synthetic asset lookup")
        return httpx.Response(
            200,
            json={
                "id": str(uuid5(NAMESPACE_URL, f"birja-e2e:{listing.security_id}")),
                "symbol": listing.ticker,
                "class": "us_equity",
                "status": "active",
                "exchange": listing.listing_exchange,
            },
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(asset_reply), trust_env=False
    ) as client:
        proofs = await stage_catalog_assets(
            client,
            (unit,),
            authority,
            account="birja",
            server="birja",
            expected_listings={listing.security_id: target},
            clock=lambda: now,
        )
    if (
        await promote_catalog_mappings(
            db, grant.id, proofs, now=now, allow_fixture=True
        )
        != 1
    ):
        raise RuntimeError("Synthetic catalog mapping was not promoted")


async def prepare_catalog(reused, traded_reused=False):
    catalog_guard()
    from app.models.stock_catalog import (
        StockCatalogAdmission,
        StockCatalogGeneration,
        StockCatalogListing,
    )
    from app.services.stock_catalog_publish import publish_catalog
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(os.environ["DATABASE_URL"])
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with factory.begin() as db:
            if await db.scalar(select(func.current_database())) != "birja":
                raise RuntimeError("Disposable database mismatch")
            now = await db.scalar(select(func.clock_timestamp()))
            generation = await db.scalar(
                select(StockCatalogGeneration.id).where(
                    StockCatalogGeneration.is_active
                )
            )
            grant = await db.scalar(
                select(StockCatalogAdmission.id).where(
                    StockCatalogAdmission.artifact == "alpaca_iex_quotes"
                )
            )
            if grant is None:
                db.add(
                    StockCatalogAdmission(
                        artifact="alpaca_iex_quotes",
                        reference="Synthetic browser display authority",
                        reviewed_at=now - timedelta(minutes=1),
                        valid_until=now + timedelta(hours=2),
                        fields={
                            field: ["collection", "display", "cache"]
                            for field in ("symbol", "bid", "ask", "event_at")
                        },
                        scope={
                            "account": "birja",
                            "server": "birja",
                            "feed": "iex",
                            "currency": "USD",
                            "listing_exchanges": ["NASDAQ", "NYSE"],
                            "requests_per_minute": 20,
                            "max_response_bytes": 32768,
                            "symbols_per_request": len(CATALOG_VENUES),
                        },
                        is_fixture=True,
                    )
                )
            receipt = await publish_catalog(
                db,
                catalog_manifest(now, reused, traded_reused),
                generation,
                now=now,
                allow_fixture=True,
            )
            listings = await db.scalars(
                select(StockCatalogListing).where(
                    StockCatalogListing.generation_id == receipt.generation_id,
                    StockCatalogListing.state == "active",
                )
            )
            for listing in listings.all():
                await admit_catalog_mapping(db, listing, now)
    finally:
        await engine.dispose()


@asynccontextmanager
async def enrolled_catalog_migrator(admin):
    """Enroll only the existing migrator in the disposable catalog database."""
    catalog_guard()
    from sqlalchemy import text
    from sqlalchemy.engine import make_url
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    password = secrets.token_hex(32)
    async with admin.begin() as conn:
        verified = await conn.scalar(
            text("""
            SELECT current_database()='birja' AND session_user='birja'
                AND NOT role.rolcanlogin AND NOT role.rolsuper
                AND (SELECT version_num FROM alembic_version)='0028'
            FROM pg_roles role WHERE role.rolname='birja_migrator'
            """)
        )
        if verified is not True:
            raise RuntimeError("Requires the migrated disposable catalog role")
        statement = await conn.scalar(
            text("SELECT format('ALTER ROLE birja_migrator LOGIN PASSWORD %L', CAST(:password AS text))"),
            {"password": password},
        )
        await conn.execute(text(statement))
    migrator = None
    try:
        url = make_url(os.environ["DATABASE_URL"]).set(username="birja_migrator", password=password)
        migrator = create_async_engine(url)
        yield async_sessionmaker(migrator, expire_on_commit=False)
    finally:
        if migrator is not None:
            await migrator.dispose()
        async with admin.begin() as conn:
            await conn.execute(text("ALTER ROLE birja_migrator NOLOGIN PASSWORD NULL"))


async def traded_listing(db, symbol=CATALOG_TRADED):
    from app.models.stock_catalog import StockCatalogGeneration, StockCatalogListing
    from sqlalchemy import select

    return (
        await db.scalars(
            select(StockCatalogListing)
            .join(StockCatalogGeneration, StockCatalogGeneration.id == StockCatalogListing.generation_id)
            .where(
                StockCatalogGeneration.is_active,
                StockCatalogListing.state == "active",
                StockCatalogListing.ticker == symbol,
            )
        )
    ).one()


async def catalog_status(db, listing, coin_id, grant_id, now, state):
    from app.models.stock_catalog_finance import StockCatalogStatus
    from sqlalchemy.dialects.postgresql import insert

    values = {
        "catalog_id": listing.security_id,
        "listing_id": listing.id,
        "admission_id": grant_id,
        "report_digest": digest(f"browser-report:{listing.id}:{state}:{now}"),
        "state": state,
        "event_at": now,
        "observed_at": now,
        "valid_until": now + timedelta(seconds=119),
        "session_date": now.date(),
    }
    await db.execute(
        insert(StockCatalogStatus)
        .values(coin_id=coin_id, **values)
        .on_conflict_do_update(index_elements=["coin_id"], set_=values)
    )


async def enroll_financial_fixture(admin, symbol, opening_owner=None):
    from app.models.corporate_action import StockActionState, StockOwnershipMovement
    from app.models.stock import StockSession
    from app.models.stock_catalog import StockCatalogAdmission
    from app.models.stock_catalog_finance import (
        StockCatalogActionCoverage,
        StockCatalogInstrument,
    )
    from app.models.trade import Holding
    from app.models.user import Account, User
    from app.services.stock_catalog_promotion import (
        _EXECUTION_FIELDS,
        _MARK_FIELDS,
        CATALOG_ACTION_FIELDS,
        promote_catalog_instrument,
    )
    from app.services.stock_ownership import acquire_stock_gate
    from sqlalchemy import func, select
    from sqlalchemy.dialects.postgresql import insert

    async with enrolled_catalog_migrator(admin) as sessions, sessions.begin() as db:
        now = await db.scalar(select(func.clock_timestamp()))
        listing = await traded_listing(db, symbol)
        historical_session = None
        if opening_owner is not None:
            if not re.fullmatch(r"e2e-[a-z0-9-]+@example\.com", opening_owner):
                raise ValueError("Requires the disposable browser account")
            historical_session = (
                await db.scalars(
                    select(StockSession)
                    .where(
                        StockSession.exchange == listing.listing_exchange,
                        StockSession.session_date < now.date(),
                        StockSession.opens_at.is_not(None),
                    )
                    .order_by(StockSession.session_date.desc())
                    .limit(1)
                )
            ).one()
        opening_at = (
            historical_session.opens_at - timedelta(seconds=1) if historical_session else None
        )
        ids = {
            "account": "birja",
            "server": "birja",
            "catalog_id": str(listing.security_id),
            "listing_id": str(listing.id),
            "provider_asset_id": listing.provider_asset_id,
        }
        grants = {}
        lease = now + timedelta(minutes=15)
        for artifact, feed, fields in (
            ("catalog_execution", "iex", _EXECUTION_FIELDS),
            ("catalog_mark", "iex", _MARK_FIELDS),
            ("catalog_actions", "alpaca-corporate-actions", CATALOG_ACTION_FIELDS),
            (
                "catalog_halt",
                "nasdaq-rss",
                {field: ["collection", "execution", "storage", "backup"]
                 for field in ("report_digest", "event_at", "valid_until", "state")},
            ),
        ):
            scope = {**ids, "feed": feed}
            if artifact == "catalog_actions":
                scope.update(
                    rest_symbols=[listing.ticker],
                    mutation_start=(now - timedelta(days=1)).isoformat(),
                    history_start=min(
                        now.date() - timedelta(days=1), opening_at.date() if opening_at else now.date()
                    ).isoformat(),
                    future_through=(now.date() + timedelta(days=2)).isoformat(),
                    all_us_replay_ingress=True,
                    replay_region="us",
                    known_id_recheck=True,
                    requests_per_minute=10,
                    symbols_per_request=1,
                    max_response_bytes=32768,
                )
            grant = StockCatalogAdmission(
                artifact=artifact,
                reference="Synthetic catalog browser fixture",
                reviewed_at=now - timedelta(minutes=1),
                valid_until=lease,
                fields=fields,
                scope=scope,
                is_fixture=True,
            )
            grants[artifact] = grant
            db.add(grant)
        await db.flush()
        binding = await promote_catalog_instrument(
            db, listing.security_id, listing.id, grants["catalog_execution"].id,
            now, allow_fixture=True, account="birja", server="birja",
        )
        instrument = await db.get(StockCatalogInstrument, binding.catalog_id)
        state = await db.get(StockActionState, binding.coin_id)
        if opening_at is not None:
            # Explicit fixture opening shares are distinct from the browser's
            # later real buy. A past dividend can only credit the opening shares.
            await acquire_stock_gate(db, binding.coin_id)
            root = (
                await db.scalars(
                    select(Account)
                    .join(User, User.id == Account.user_id)
                    .where(User.email == opening_owner, Account.closed_at.is_(None))
                    .with_for_update(of=Account)
                )
            ).one()
            assert state.sequence == 0 and root.cash == Decimal("10000")
            instrument.promoted_at = opening_at
            db.add_all(
                [
                    Holding(
                        portfolio_id=root.id, user_id=root.user_id, coin_id=binding.coin_id,
                        quantity=Decimal(2), cost_basis=Decimal(0),
                    ),
                    StockOwnershipMovement(
                        portfolio_id=root.id, user_id=root.user_id, coin_id=binding.coin_id,
                        sequence=1, economic_at=opening_at, recorded_at=opening_at,
                        quantity=Decimal(2), before_quantity=Decimal(0), after_quantity=Decimal(2),
                        before_basis=Decimal(0), after_basis=Decimal(0), unit_epoch=0,
                        cause_kind="opening", causal_key=f"catalog-browser-opening:{root.id}",
                    ),
                ]
            )
            state.sequence = 1
        origin = instrument.promoted_at
        coverage = {
            "catalog_id": binding.catalog_id,
            "listing_id": binding.listing_id,
            "admission_id": grants["catalog_actions"].id,
            "journal_origin": origin,
            "coverage_start": origin,
            "covered_until": now,
            "cursor": None,
            "observed_at": now,
            "valid_until": lease,
        }
        await db.execute(
            insert(StockCatalogActionCoverage)
            .values(coin_id=binding.coin_id, **coverage)
            .on_conflict_do_update(index_elements=["coin_id"], set_=coverage)
        )
        state.health = "current"
        state.epoch = max(state.epoch, 1)
        state.admission_generation = coverage["admission_id"]
        state.journal_start_at = origin
        state.complete_from = origin
        state.coverage_start = origin
        state.covered_until = now
        state.checked_at = now
        state.valid_until = lease
        state.cursor = None
        await catalog_status(db, listing, binding.coin_id, grants["catalog_halt"].id, now, "normal")


async def settle_catalog_fixture_action(engine, operation):
    """Exercise the ordinary action services with a synthetic session cutoff."""
    from app.models.corporate_action import StockActionRevision, StockActionState
    from app.models.stock import StockSession
    from app.models.stock_catalog_finance import (
        StockCatalogActionCoverage,
        StockCatalogInstrument,
    )
    from app.services.alpaca_actions import ActionBatch, ActionObservation
    from app.services.corporate_action_rules import NormalizedAction
    from app.services.corporate_actions import (
        apply_due_actions,
        derive_dividend_entitlements,
        persist_action_batch,
    )
    from app.services.dividends import process_dividend
    from app.services.stock_catalog_actions import load_catalog_action_authority
    from sqlalchemy import func, select, text, update
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions.begin() as db:
        listing = await traded_listing(db, CATALOG_MIXED)
        binding = await db.get(StockCatalogInstrument, listing.security_id)
        if binding is None or binding.listing_id != listing.id:
            raise RuntimeError("Requires the exact promoted fixture issue")
        cutoff = await db.scalar(select(func.clock_timestamp()))
        day = cutoff.date()
        if operation == "catalog-dividend":
            previous = (
                await db.scalars(
                    select(StockSession)
                    .where(
                        StockSession.exchange == listing.listing_exchange,
                        StockSession.session_date < day,
                        StockSession.opens_at.is_not(None),
                    )
                    .order_by(StockSession.session_date.desc())
                    .limit(1)
                )
            ).one()
            day, cutoff = previous.session_date, previous.opens_at
        else:
            closes = cutoff + timedelta(minutes=30)
            CONTROL.write_text(
                json.dumps(
                    {
                        "state": "open", "at": cutoff.isoformat(), "session_date": day.isoformat(),
                        "opens": cutoff.isoformat(), "closes": closes.isoformat(),
                    }
                )
            )
            await db.execute(
                update(StockSession)
                .where(StockSession.session_date == day)
                .values(opens_at=cutoff, closes_at=closes)
            )
        checked = await db.scalar(select(func.clock_timestamp()))
        coin_id = binding.coin_id
        coverage = await db.get(StockCatalogActionCoverage, coin_id)
        state = await db.get(StockActionState, coin_id)
        coverage.observed_at = coverage.covered_until = checked
        state.checked_at = state.covered_until = checked

    async with engine.connect() as conn:
        # Keep the runtime writes under its actual migration-installed grants.
        await conn.execute(text("SET ROLE birja_scheduler"))
        await conn.commit()
        try:
            async with AsyncSession(bind=conn, expire_on_commit=False) as db:
                split = operation == "catalog-split"
                async with db.begin():
                    now = await db.scalar(select(func.clock_timestamp()))
                    authority = await load_catalog_action_authority(
                        db, coin_id, now, account="birja", server="birja", allow_fixture=True
                    )
                    if authority is None:
                        raise RuntimeError("Fixture action scope unavailable")
                    action = NormalizedAction(
                        str(uuid5(NAMESPACE_URL, f"birja-browser:{coin_id}:{operation}")),
                        coin_id,
                        authority.ticker,
                        "forward_split" if split else "cash_dividend",
                        day,
                        now,
                        currency="USD",
                        rate=None if split else Decimal("0.50"),
                        ex_date=day,
                        record_date=day,
                        payable_date=day,
                        subtype="ordinary",
                        foreign=False,
                        special=False,
                        due_bills=False,
                        identity_verified=True,
                        dates_verified=True,
                        units="pre_split" if split else None,
                        economic_at=cutoff if split else None,
                        new_rate=Decimal(2) if split else None,
                        old_rate=Decimal(1) if split else None,
                    )
                    (revision,) = await persist_action_batch(
                        db,
                        ActionBatch(
                            records=(action,),
                            observations=(ActionObservation(action),),
                            complete=True,
                        ),
                        None,
                        catalog=authority,
                    )
                    if split:
                        applied = await apply_due_actions(db, coin_id, catalog=authority)
                        if len(applied) != 1:
                            raise RuntimeError("Expected one verified fixture split")
                        return
                    (entitlement,) = await derive_dividend_entitlements(
                        db, revision.event_id, catalog=authority
                    )
                    if entitlement.state != "eligible" or entitlement.eligible_quantity != 2:
                        raise RuntimeError("Expected the fixture's two-share entitlement")
                    terms = await db.get(StockActionRevision, revision.revision_id)
                payment = await process_dividend(
                    db,
                    portfolio_id=entitlement.portfolio_id,
                    event_id=entitlement.event_id,
                    entitlement_id=entitlement.id,
                    expected_revision_fingerprint=terms.fingerprint,
                    expected_entitlement_fingerprint=entitlement.fingerprint,
                )
                if payment.outcome != "original":
                    raise RuntimeError("Expected one ordinary fixture dividend")
        finally:
            await conn.rollback()
            await conn.execute(text("RESET ROLE"))
            await conn.commit()


async def prepare_catalog_finance(operation, opening_owner=None):
    catalog_guard()
    from app.models.corporate_action import StockActionState
    from app.models.stock import StockSession
    from app.models.stock_catalog import StockCatalogAdmission
    from app.models.stock_catalog_finance import (
        StockCatalogFinancialQuote,
        StockCatalogInstrument,
        StockCatalogStatus,
    )
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    engine = create_async_engine(os.environ["DATABASE_URL"])
    try:
        if operation in {"catalog-finance", "catalog-finance-mixed"}:
            if (operation == "catalog-finance-mixed") != (opening_owner is not None):
                raise ValueError("Only the mixed fixture requires an opening owner")
            symbol = CATALOG_MIXED if operation == "catalog-finance-mixed" else CATALOG_TRADED
            await enroll_financial_fixture(engine, symbol, opening_owner)
            return
        if operation in {"catalog-dividend", "catalog-split"}:
            await settle_catalog_fixture_action(engine, operation)
            return
        if operation == "catalog-cold-close":
            await prepare("close")
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions.begin() as db:
            listing = await traded_listing(db, CATALOG_MIXED if operation == "catalog-hold" else CATALOG_TRADED)
            binding = await db.get(StockCatalogInstrument, listing.security_id)
            if binding is None or binding.listing_id != listing.id:
                raise RuntimeError("Requires the exact promoted fixture issue")
            now = await db.scalar(select(func.clock_timestamp()))
            quote = await db.get(StockCatalogFinancialQuote, binding.coin_id)
            if quote is None or quote.listing_id != listing.id:
                raise RuntimeError("Requires the fixture's selected financial quote")
            status = await db.get(StockCatalogStatus, binding.coin_id)
            if operation == "catalog-cold-close":
                session = (
                    await db.scalars(
                        select(StockSession).where(
                            StockSession.exchange == listing.listing_exchange,
                            StockSession.session_date == quote.session_date,
                        )
                    )
                ).one()
                if not session.opens_at <= quote.event_at < session.closes_at <= now:
                    raise RuntimeError("Fixture close does not cover the stored quote")
                quote.opens_at, quote.closes_at = session.opens_at, session.closes_at
            elif operation == "catalog-expire-mark":
                scope = await db.get(StockCatalogAdmission, quote.mark_admission_id)
                scope.revoked_at = now
            elif operation == "catalog-halt":
                await catalog_status(db, listing, binding.coin_id, status.admission_id, now, "halted")
            elif operation == "catalog-resume":
                await catalog_status(db, listing, binding.coin_id, status.admission_id, now, "normal")
            elif operation == "catalog-reprice":
                quote.ask = Decimal("104.125")
            elif operation == "catalog-stale":
                quote.event_at = min(quote.event_at, now - timedelta(seconds=120))
            elif operation == "catalog-hold":
                state = await db.get(StockActionState, binding.coin_id)
                state.health = "reconciling"
                state.valid_until = None
            else:
                raise ValueError("Unknown catalog financial fixture action")
        if operation == "catalog-cold-close":
            from redis.asyncio import Redis

            redis = Redis.from_url(os.environ["REDIS_URL"])
            try:
                pattern = f"sim:stock-catalog-demand:{digest('birja')}:display:*"
                async for key in redis.scan_iter(match=pattern):
                    await redis.delete(key)
                if any([key async for key in redis.scan_iter(match=pattern)]):
                    raise RuntimeError("The synthetic display cache is not empty")
            finally:
                await redis.aclose()
    finally:
        await engine.dispose()


def catalog_reply(request):
    import httpx
    from app.services.alpaca import LATEST_QUOTES_URL

    symbols = request.url.params.get("symbols", "").split(",")
    if (
        str(request.url.copy_with(query=None)) != LATEST_QUOTES_URL
        or request.url.params.get("feed") != "iex"
        or request.url.params.get("currency") != "USD"
        or not set(symbols) <= CATALOG_VENUES.keys()
    ):
        raise ValueError("Unexpected synthetic quote request")
    with CATALOG_REQUESTS.open("a", encoding="utf-8") as records:
        records.write(json.dumps(symbols) + "\n")
    if CATALOG_OUTAGE.exists():
        return httpx.Response(503)
    now = datetime.now(UTC).isoformat()
    return httpx.Response(
        200,
        json={
            "quotes": {
                ticker: {
                    "bp": CATALOG_PRICES[ticker][0],
                    "ap": CATALOG_PRICES[ticker][1],
                    "t": now,
                    "c": ["R"],
                    "bx": "V",
                    "ax": "V",
                    "bs": 1,
                    "as": 1,
                    "z": "C" if CATALOG_VENUES[ticker] == "NASDAQ" else "A",
                }
                for ticker in symbols
            }
        },
    )


def catalog_app():
    catalog_guard()
    import httpx
    from app.core.config import SchedulerSettings, Settings
    from app.main import create_app
    from app.services.stock_catalog_quote_demand import pending_catalog_quotes
    from app.tasks.stock_catalog_quotes import run_catalog_quote_cycle

    # This in-process worker runs only in the disposable browser fixture and
    # receives a mock transport with no network fallback or provider secrets.
    app = create_app(
        Settings().model_copy(update={"env": "test", "stock_data_enabled": True})
    )
    worker = SchedulerSettings().model_copy(
        update={
            "env": "test",
            "stock_data_enabled": True,
            "stock_max_retries": 0,
        }
    )
    original_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(application):
        async with (
            original_lifespan(application),
            httpx.AsyncClient(
                transport=httpx.MockTransport(catalog_reply), trust_env=False
            ) as client,
        ):

            async def run():
                while True:
                    if await pending_catalog_quotes(
                        application.state.redis, account="birja", server="birja"
                    ):
                        await run_catalog_quote_cycle(
                            sessionmaker=application.state.sessionmaker,
                            redis=application.state.redis,
                            quota_redis=application.state.redis,
                            http=client,
                            settings=worker,
                        )
                    await asyncio.sleep(0.1)

            task = asyncio.create_task(run())
            try:
                yield
            finally:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

    app.router.lifespan_context = lifespan
    return app


def catalog_command(operation, opening_owner=None):
    catalog_guard()
    if operation in {"catalog-first", "catalog-reuse", "catalog-traded-reuse"}:
        if operation == "catalog-first":
            CATALOG_OUTAGE.unlink(missing_ok=True)
            CATALOG_REQUESTS.unlink(missing_ok=True)
        asyncio.run(prepare_catalog(
            reused=operation == "catalog-reuse",
            traded_reused=operation == "catalog-traded-reuse",
        ))
    elif operation == "catalog-outage":
        CATALOG_OUTAGE.touch()
    elif operation == "catalog-observed":
        rows = (
            CATALOG_REQUESTS.read_text().splitlines()
            if CATALOG_REQUESTS.exists()
            else []
        )
        print(json.dumps([json.loads(row) for row in rows]))
    elif operation in {
        "catalog-finance", "catalog-finance-mixed", "catalog-cold-close", "catalog-expire-mark", "catalog-reprice",
        "catalog-halt", "catalog-resume", "catalog-stale", "catalog-hold",
        "catalog-dividend", "catalog-split",
    }:
        asyncio.run(prepare_catalog_finance(operation, opening_owner))
    else:
        raise ValueError("Unknown synthetic catalog operation")


if __name__ == "__main__":
    guard()
    sys.path.insert(0, "/app")
    patch_calendar()
    if sys.argv[1] == "serve":
        import uvicorn

        if os.environ.get("BIRJA_E2E_CATALOG") == "1":
            uvicorn.run(catalog_app(), host="0.0.0.0", port=8000)
        else:
            uvicorn.run("app.main:create_app", factory=True, host="0.0.0.0", port=8000)
    elif sys.argv[1].startswith("catalog-"):
        catalog_command(*sys.argv[1:])
    else:
        asyncio.run(prepare(*sys.argv[1:]))
