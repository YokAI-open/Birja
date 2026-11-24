"""Selected display quote tests on the disposable PostgreSQL and Redis stack."""

import asyncio
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from uuid import uuid4

import httpx
import pytest
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.stock import StockDataAdmission, StockSession
from app.models.stock_catalog import (
    StockCatalogAdmission,
    StockCatalogGeneration,
    StockCatalogListing,
    StockCatalogSecurity,
)
from app.services import stock_catalog_quote_demand as demand
from app.services.stock_catalog_provider import (
    CatalogAssetAdmission,
    CatalogAssetTarget,
    CatalogUnitEvidence,
    stage_catalog_assets,
)
from app.services.stock_catalog_publish import promote_catalog_mappings
from app.services.stock_catalog_quotes import (
    load_catalog_quote_context,
    publish_catalog_quote,
    read_catalog_quote,
)
from app.services.stock_catalog_sources import ListingExchange
from app.services.stock_quote_rules import RawIexQuote, validate_iex_quote
from app.services.stock_sessions import build_sessions
from tests.test_stock_catalog_publish import Factory
from tests.test_stock_catalog_publish import catalog_factory as catalog_factory
from tests.test_stock_sessions import evidence as calendar_evidence

NOW = datetime(2026, 11, 24, 20, 59, tzinfo=UTC)


def _digest(value: str) -> str:
    return sha256(value.encode()).hexdigest()


async def seed_catalog_quote_fixture(
    db: AsyncSession,
    now: datetime,
    *,
    account: str = "birja",
    server: str = "birja",
    ticker: str = "FQA",
    exchange: ListingExchange = "NASDAQ",
    symbols_per_request: int = 8,
) -> tuple[int, int]:
    """Seed one synthetic issue and its reviewed mappings using mocked provider IO."""
    old = await db.scalar(select(StockCatalogGeneration).where(StockCatalogGeneration.is_active))
    if old is None:
        old = StockCatalogGeneration(
            mode="fixture",
            sources={},
            coverage={},
            published_at=now - timedelta(hours=2),
            valid_until=now + timedelta(days=2),
            is_active=True,
            manifest_sha256=_digest(str(uuid4())),
        )
        db.add(old)
        db.add(
            StockCatalogAdmission(
                artifact="alpaca_iex_quotes",
                reference="Synthetic selected quote scope only",
                reviewed_at=now - timedelta(hours=1),
                valid_until=now + timedelta(hours=3),
                fields={
                    field: ["collection", "display", "cache"]
                    for field in ("symbol", "bid", "ask", "event_at")
                },
                scope={
                    "account": account,
                    "server": server,
                    "feed": "iex",
                    "currency": "USD",
                    "listing_exchanges": ["NASDAQ", "NYSE"],
                    "requests_per_minute": 10,
                    "max_response_bytes": 32768,
                    "symbols_per_request": symbols_per_request,
                },
                is_fixture=True,
            )
        )
        utc_calendar = calendar_evidence(now)
        authority = replace(
            utc_calendar, scope={**utc_calendar.scope, "account": account, "server": server}
        )
        calendar = await db.scalar(
            select(StockDataAdmission).where(StockDataAdmission.product == "calendar")
        )
        if calendar is None:
            db.add(StockDataAdmission(**asdict(authority)))
        else:
            for name, value in asdict(authority).items():
                setattr(calendar, name, value)
        await db.flush()
        # Fixed reviewed sessions keep these fixtures independent from the host clock.
        sessions = build_sessions(now, authority, account=account, server=server)
        assert sessions
        await db.execute(delete(StockSession))
        db.add_all(StockSession(**asdict(row)) for row in sessions)
    assert old.mode == "fixture"
    issue = StockCatalogSecurity(identity_key="review:" + _digest(str(uuid4())), created_at=now)
    db.add(issue)
    await db.flush()
    name = f"Synthetic {ticker} Holdings"
    listing = StockCatalogListing(
        generation_id=old.id,
        security_id=issue.id,
        ticker=ticker,
        normalized_ticker=ticker,
        company_name=name,
        normalized_name=name.casefold(),
        listing_exchange=exchange,
        classification="common_stock",
        state="active",
        reason="corroborated_share_class",
        source="nasdaqlisted" if exchange == "NASDAQ" else "otherlisted",
        row_key=ticker,
        row_digest=_digest(ticker),
        evidence_digest=_digest("classification:" + ticker),
        evidence_at=now - timedelta(hours=2),
        valid_until=old.valid_until,
    )
    db.add(listing)
    await db.flush()
    target = CatalogAssetTarget(
        catalog_id=issue.id,
        listing_version=listing.id,
        listing_exchange=exchange,
        provider_symbol=ticker,
    )
    unit = CatalogUnitEvidence(
        target=target,
        currency="USD",
        units_per_share=1,
        classification="common_stock",
        reviewed_at=now - timedelta(hours=2),
        valid_until=now + timedelta(hours=4),
        evidence_digest=_digest("units:" + ticker),
    )
    provider = CatalogAssetAdmission(
        account=account,
        server=server,
        environment="paper",
        reviewed_at=now - timedelta(hours=1),
        valid_until=now + timedelta(hours=4),
        evidence_digest=_digest("alpaca-reference:" + ticker),
        targets=(target,),
        purposes=frozenset(
            {"collection", "internal_use", "derived_use", "display", "storage", "backup"}
        ),
        request_limit=1,
    )
    grant = StockCatalogAdmission(
        artifact="alpaca_assets",
        reference="Fixture provider mapping review",
        reviewed_at=provider.reviewed_at,
        valid_until=provider.valid_until,
        fields={
            field: sorted(provider.purposes)
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
            "provider": provider.model_dump(mode="json"),
            "units": [unit.model_dump(mode="json")],
        },
    )
    db.add(grant)
    await db.flush()
    asset_id = str(uuid4())
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={
                "id": asset_id,
                "symbol": ticker,
                "class": "us_equity",
                "status": "active",
                "exchange": exchange,
            },
        )
    )
    async with httpx.AsyncClient(transport=transport) as client:
        proofs = await stage_catalog_assets(
            client,
            (unit,),
            provider,
            account=account,
            server=server,
            expected_listings={issue.id: target},
            clock=lambda: now,
        )
    assert await promote_catalog_mappings(db, grant.id, proofs, now=now, allow_fixture=True) == 1
    return issue.id, listing.id


async def _one_pending(redis: Redis, account: str, server: str) -> demand.CatalogQuoteRequest:
    async with asyncio.timeout(3):
        for _ in range(300):
            jobs = await demand.pending_catalog_quotes(redis, account=account, server=server)
            if jobs:
                break
            await asyncio.sleep(0.01)
    assert len(jobs) == 1
    return jobs[0]


async def test_coalesces_by_exact_binding_and_completes_only_matching_token(redis_client):
    account, server = str(uuid4()), "fixture"
    details = {
        "account": account,
        "server": server,
        "catalog_id": 5,
        "listing_version": 9,
        "fingerprint": _digest("chosen"),
    }
    first = asyncio.create_task(demand.request_catalog_quote(redis_client, **details))
    same = asyncio.create_task(demand.request_catalog_quote(redis_client, **details))
    job = await _one_pending(redis_client, account, server)
    assert await demand.current_catalog_quote_request(
        redis_client, job, account=account, server=server
    )
    assert not await demand.current_catalog_quote_request(
        redis_client, job, account=account, server="other"
    )
    wrong = replace(job, token="older-request")
    assert not await demand.complete_catalog_quote(
        redis_client, wrong, account=account, server=server, reason="ready"
    )
    assert await demand.complete_catalog_quote(
        redis_client, job, account=account, server=server, reason="throttled"
    )
    assert await asyncio.gather(first, same) == ["throttled", "throttled"]
    assert not await demand.complete_catalog_quote(
        redis_client, job, account=account, server=server, reason="ready"
    )
    assert await demand.pending_catalog_quotes(redis_client, account=account, server=server) == ()


async def test_capacity_is_shared_per_account_and_worker_selection_is_bounded(redis_client):
    account = str(uuid4())
    servers = ("fixture-1", "fixture-2")
    tasks = []
    try:
        for i in range(64):
            tasks.append(
                asyncio.create_task(
                    demand.request_catalog_quote(
                        redis_client,
                        account=account,
                        server=servers[i % 2],
                        catalog_id=i + 1,
                        listing_version=i + 1,
                        fingerprint=_digest(str(i)),
                    )
                )
            )
        async with asyncio.timeout(3):
            for _ in range(300):
                if await redis_client.zcard(demand._queue(account)) == 64:
                    break
                await asyncio.sleep(0.01)
        assert (
            await demand.request_catalog_quote(
                redis_client,
                account=account,
                server="other",
                catalog_id=100,
                listing_version=100,
                fingerprint=_digest("one too many"),
            )
            == "queue_full"
        )
        for i, server in enumerate(servers):
            pending = await demand.pending_catalog_quotes(
                redis_client, account=account, server=server
            )
            assert len(pending) == 8
            assert all((job.catalog_id - 1) % 2 == i for job in pending)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        async for key in redis_client.scan_iter(match=demand._queue(account) + "*"):
            await redis_client.delete(key)


async def test_timed_out_request_cannot_complete_or_refresh_selection(redis_client, monkeypatch):
    monkeypatch.setattr(demand, "_REQUEST_TTL_MS", 100)
    monkeypatch.setattr(demand, "_WAIT_SECONDS", 0.05)
    account, server = str(uuid4()), "fixture"
    first = asyncio.create_task(
        demand.request_catalog_quote(
            redis_client,
            account=account,
            server=server,
            catalog_id=1,
            listing_version=2,
            fingerprint=_digest("version"),
        )
    )
    job = await _one_pending(redis_client, account, server)
    assert await first == "quote_unavailable"
    await asyncio.sleep(0.1)
    assert await demand.pending_catalog_quotes(redis_client, account=account, server=server) == ()
    assert not await demand.complete_catalog_quote(
        redis_client, job, account=account, server=server, reason="ready"
    )


async def test_cache_is_exact_and_recovers_closed_mark_only_inside_current_scope(
    catalog_factory: Factory,
    settings: Settings,
    redis_client: Redis,
    clean_stock_discovery: None,
):
    config = settings.model_copy(update={"stock_data_enabled": True})
    account, server = config.stock_data_account, config.stock_data_server
    async with catalog_factory.begin() as db:
        catalog_id, version = await seed_catalog_quote_fixture(db, NOW)
        other_id, _ = await seed_catalog_quote_fixture(db, NOW, ticker="FQB", exchange="NYSE")
    async with catalog_factory() as db:
        choice = await load_catalog_quote_context(db, config, catalog_id, now=NOW)
        other = await load_catalog_quote_context(db, config, other_id, now=NOW)
    assert choice.reason == "ready" and choice.binding is not None
    assert other.reason == "ready" and other.binding is not None
    assert (
        await read_catalog_quote(redis_client, choice, account=account, server=server, now=NOW)
        is None
    )
    job = asyncio.create_task(
        demand.request_catalog_quote(
            redis_client,
            account=account,
            server=server,
            catalog_id=catalog_id,
            listing_version=version,
            fingerprint=choice.binding.fingerprint,
        )
    )
    request = await _one_pending(redis_client, account, server)
    price = validate_iex_quote(
        RawIexQuote(Decimal("101.005"), Decimal("101.006"), NOW - timedelta(seconds=2), ["R", "R"]),
        listing_exchange="NASDAQ",
        collected_at=NOW,
    )
    assert price is not None
    assert not await publish_catalog_quote(
        redis_client,
        request,
        other.binding,
        other.session,
        price,
        account=account,
        server=server,
        now=NOW,
    )
    assert await publish_catalog_quote(
        redis_client,
        request,
        choice.binding,
        choice.session,
        price,
        account=account,
        server=server,
        now=NOW,
    )
    assert await job == "ready"
    key = demand.catalog_quote_key(
        account=account,
        server=server,
        catalog_id=catalog_id,
        listing_version=version,
        fingerprint=choice.binding.fingerprint,
    )
    assert 0 < await redis_client.pttl(key) <= 600_000
    selected = await read_catalog_quote(
        redis_client, choice, account=account, server=server, now=NOW
    )
    assert selected is not None and selected.mid == Decimal("101.00550000")
    assert selected.event_at == NOW - timedelta(seconds=2)
    assert (
        await read_catalog_quote(redis_client, other, account=account, server=server, now=NOW)
        is None
    )
    after_close = NOW + timedelta(minutes=2)
    async with catalog_factory() as db:
        closed = await load_catalog_quote_context(db, config, catalog_id, now=after_close)
    assert closed.reason == "market_closed" and closed.session.next_session is not None
    assert (
        await read_catalog_quote(
            redis_client, closed, account=account, server=server, now=after_close
        )
        == selected
    )
    assert (
        await read_catalog_quote(
            redis_client, closed, account=account, server=server, now=NOW + timedelta(minutes=10)
        )
        is None
    )
    async with catalog_factory.begin() as db:
        grant = await db.scalar(
            select(StockCatalogAdmission).where(
                StockCatalogAdmission.artifact == "alpaca_iex_quotes"
            )
        )
        assert grant is not None
        grant.revoked_at = NOW + timedelta(minutes=1)
    async with catalog_factory() as db:
        revoked = await load_catalog_quote_context(db, config, catalog_id, now=after_close)
    assert revoked.binding is None
    assert revoked.reason == "market_closed"
    assert (
        await read_catalog_quote(
            redis_client, revoked, account=account, server=server, now=after_close
        )
        is None
    )
    await redis_client.delete(key)
    assert (
        await read_catalog_quote(
            redis_client, closed, account=account, server=server, now=after_close
        )
        is None
    )


@pytest.mark.parametrize("role", ["birja_app", "birja_scheduler"])
async def test_current_display_scope_and_units_are_checked_under_restricted_roles(
    catalog_factory: Factory,
    settings: Settings,
    clean_stock_discovery: None,
    role: str,
):
    config = settings.model_copy(update={"stock_data_enabled": True})
    async with catalog_factory.begin() as db:
        catalog_id, _ = await seed_catalog_quote_fixture(db, NOW, symbols_per_request=1)
    async with catalog_factory() as db:
        await db.execute(text("SET LOCAL ROLE " + role))  # noqa: S608 - fixed test role
        original = await load_catalog_quote_context(db, config, catalog_id, now=NOW)
        assert original.binding is not None and original.binding.symbols_per_request == 1
    async with catalog_factory() as db:
        disabled = await load_catalog_quote_context(db, settings, catalog_id, now=NOW)
        assert disabled.binding is None and disabled.reason == "price_disabled"
        fixture_forbidden = await load_catalog_quote_context(
            db,
            config.model_copy(update={"env": "dev"}),
            catalog_id,
            now=NOW,
        )
        assert fixture_forbidden.binding is None
    async with catalog_factory.begin() as db:
        asset = await db.scalar(
            select(StockCatalogAdmission).where(StockCatalogAdmission.artifact == "alpaca_assets")
        )
        assert asset is not None
        changed = {**asset.scope["units"][0], "evidence_digest": _digest("different issue")}
        asset.scope = {**asset.scope, "units": [changed]}
    async with catalog_factory() as db:
        altered = await load_catalog_quote_context(db, config, catalog_id, now=NOW)
        assert altered.binding is None and altered.reason == "mapping_review"


async def test_total_redis_loss_yields_no_display_or_demand(monkeypatch, redis_client):
    async def refused(*args, **kwargs):
        raise RedisError("synthetic cache loss")

    monkeypatch.setattr(redis_client, "eval", refused)
    assert (
        await demand.request_catalog_quote(
            redis_client,
            account="fixture",
            server="fixture",
            catalog_id=1,
            listing_version=1,
            fingerprint=_digest("fixture"),
        )
        == "quote_unavailable"
    )


async def test_cache_cutoff_uses_current_source_rights_instead_of_publication_expiry(
    catalog_factory: Factory,
    settings: Settings,
    clean_stock_discovery: None,
):
    config = settings.model_copy(update={"stock_data_enabled": True})
    shortened_until = NOW + timedelta(seconds=30)
    async with catalog_factory.begin() as db:
        catalog_id, version = await seed_catalog_quote_fixture(db, NOW)
        listing = await db.get(StockCatalogListing, version)
        assert listing is not None
        generation = await db.get(StockCatalogGeneration, listing.generation_id)
        assert generation is not None
        directory = StockCatalogAdmission(
            artifact="nasdaqlisted",
            reference="Synthetic directory permission",
            reviewed_at=NOW - timedelta(hours=1),
            valid_until=shortened_until,
            fields={
                "ticker": ["display"],
                "company_name": ["display"],
                "listing_exchange": ["display"],
                "share_class": ["display"],
                "eligibility": ["derived_use"],
            },
            scope={},
        )
        classification = StockCatalogAdmission(
            artifact="openfigi",
            reference="Synthetic classification permission",
            reviewed_at=directory.reviewed_at,
            valid_until=NOW + timedelta(hours=1),
            fields={"classification": ["derived_use"], "identity_key": ["derived_use"]},
            scope={},
        )
        db.add_all((directory, classification))
        await db.flush()
        listing.directory_admission_id = listing.name_admission_id = directory.id
        listing.classification_admission_id = classification.id
        generation.mode = "live"
        quote = await db.scalar(
            select(StockCatalogAdmission).where(
                StockCatalogAdmission.artifact == "alpaca_iex_quotes",
            )
        )
        assert quote is not None
        quote.is_fixture = False
    async with catalog_factory() as db:
        scoped = await load_catalog_quote_context(db, config, catalog_id, now=NOW)
        expired = await load_catalog_quote_context(db, config, catalog_id, now=shortened_until)
    assert scoped.binding is not None and scoped.binding.valid_until == shortened_until
    assert expired.binding is None
