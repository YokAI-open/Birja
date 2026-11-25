"""Exercise the selected quote and owned catalog context through the real app."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from pydantic import ValidationError
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v2 import stock_catalog as routes
from app.models.corporate_action import StockActionState
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogGeneration
from app.models.stock_catalog_finance import StockCatalogFinancialQuote
from app.services.stock_catalog_quote_demand import catalog_quote_key, pending_catalog_quotes
from app.services.stock_catalog_quotes import (
    CatalogDisplayQuote,
    load_catalog_quote_context,
    publish_catalog_quote,
)
from app.services.stock_quote_rules import ValidIexQuote
from tests.helpers import OutboxSender, csrf_headers, sign_in, unique_email
from tests.test_migrations import install_current_test_grants
from tests.test_portfolio_closure_api import intent
from tests.test_portfolio_stock_api import body, headers, private
from tests.test_stock_catalog_api import _financial_counts
from tests.test_stock_catalog_publish import NOW, Factory, _manifest, _publish
from tests.test_stock_catalog_publish import catalog_factory as catalog_factory
from tests.test_stock_catalog_quote_scheduler import _financial_request_and_tick
from tests.test_stock_catalog_quote_scheduler import finance_0025 as finance_0025
from tests.test_stock_catalog_quote_scheduler import finance_0026 as finance_0026
from tests.test_stock_catalog_quote_scheduler import financial_market as financial_market
from tests.test_stock_catalog_quotes import seed_catalog_quote_fixture

PORTFOLIOS = "/api/v2/portfolios"


@dataclass
class Target:
    client: httpx.AsyncClient
    catalog_id: int
    listing_version: int
    portfolio_id: str
    clock: datetime = NOW

    @property
    def price_url(self) -> str:
        return f"/api/v2/stock-catalog/{self.catalog_id}/quote"

    def context_url(self, portfolio_id: str | None = None) -> str:
        return (
            f"{PORTFOLIOS}/{portfolio_id or self.portfolio_id}"
            f"/stock-catalog/{self.catalog_id}/trade-context"
        )

    async def quote(self, listing_version: str | None = None) -> httpx.Response:
        return await self.client.post(
            self.price_url,
            json={"listing_version": listing_version or str(self.listing_version)},
            headers=headers(self.client),
        )


@pytest_asyncio.fixture
async def target(
    catalog_factory: Factory,
    clean_stock_discovery: None,
    running_app: FastAPI,
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> Target:
    await sign_in(auth_client, outbox, unique_email("catalog-owner"))
    [portfolio] = (await auth_client.get(PORTFOLIOS)).json()
    clock = getattr(request, "param", NOW)
    async with catalog_factory.begin() as db:
        catalog_id, listing_version = await seed_catalog_quote_fixture(db, clock)
    settings = running_app.state.settings.model_copy(update={"stock_data_enabled": True})
    monkeypatch.setattr(running_app.state, "settings", settings)
    result = Target(auth_client, catalog_id, listing_version, portfolio["id"], clock)
    monkeypatch.setattr(
        routes, "datetime", SimpleNamespace(now=lambda tz: result.clock.astimezone(tz))
    )
    return result


async def test_authentication_csrf_and_canonical_listing_selection(
    running_app: FastAPI,
    target: Target,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unexpected_demand(*args: object, **kwargs: object) -> str:
        raise AssertionError("refused selection unexpectedly requested a quote")

    monkeypatch.setattr(routes, "request_catalog_quote", unexpected_demand)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=running_app), base_url="https://test"
    ) as signed_out:
        csrf = await csrf_headers(signed_out)
        for denied in (
            await signed_out.get(target.context_url()),
            await signed_out.post(
                target.price_url,
                json={"listing_version": str(target.listing_version)},
                headers=csrf,
            ),
        ):
            assert denied.status_code == 401
            private(denied)
    denied = await target.client.post(
        target.price_url, json={"listing_version": str(target.listing_version)}
    )
    assert denied.status_code == 403
    private(denied)
    for invalid_body in (
        {"listing_version": target.listing_version},
        {"listing_version": "0"},
        {"listing_version": "9223372036854775808"},
        {"listing_version": str(target.listing_version), "symbol": "AAPL"},
    ):
        invalid = await target.client.post(
            target.price_url, json=invalid_body, headers=headers(target.client)
        )
        assert invalid.status_code == 422
        private(invalid)
    stale = await target.quote(str(target.listing_version + 1))
    assert stale.status_code == 409 and stale.json() == {"detail": {"code": "listing_changed"}}
    private(stale)


@pytest.mark.parametrize("outage", [True, False])
async def test_catalog_does_not_fall_back_to_state_redis(
    target: Target,
    catalog_factory: Factory,
    running_app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    outage: bool,
) -> None:
    class UnavailableCache:
        async def get(self, key: str) -> None:
            raise RedisConnectionError("Synthetic volatile cache unavailable")

        async def eval(self, *args: object) -> None:
            raise RedisConnectionError("Synthetic volatile cache unavailable")

    settings = running_app.state.settings
    async with catalog_factory() as db:
        context = await load_catalog_quote_context(
            db, settings, target.catalog_id, now=target.clock
        )
    assert context.binding is not None
    scope = {"account": settings.stock_data_account, "server": settings.stock_data_server}
    key = catalog_quote_key(
        **scope,
        catalog_id=target.catalog_id,
        listing_version=target.listing_version,
        fingerprint=context.binding.fingerprint,
    )
    state = running_app.state.redis
    await state.set(
        key,
        CatalogDisplayQuote(
            bid=Decimal("17.24"),
            ask=Decimal("17.26"),
            mid=Decimal("17.25"),
            event_at=target.clock - timedelta(seconds=4),
            collected_at=target.clock,
        ).model_dump_json(),
        ex=10,
    )
    try:
        monkeypatch.setattr(
            running_app.state, "catalog_quote_redis", UnavailableCache() if outage else None
        )
        price = await target.quote()
        assert price.status_code == 200
        assert price.json()["quote"] is None
        assert price.json()["reason"] == "quote_unavailable"
        assert not await pending_catalog_quotes(state, **scope)
        existing = await target.client.get(PORTFOLIOS)
        assert existing.status_code == 200 and existing.json()[0]["id"] == target.portfolio_id
    finally:
        await state.delete(key)


def test_production_catalog_cache_requires_a_separate_instance(settings) -> None:
    assert settings.catalog_cache_url == settings.redis_url
    assert settings.model_copy(update={"env": "prod"}).catalog_cache_url is None
    endpoint = settings.redis_url.rsplit("/", 1)[0] + "/1"
    with pytest.raises(ValidationError, match="separate Redis instance"):
        type(settings)(catalog_quote_redis_url=endpoint)


async def test_read_only_target_and_financial_authority_remain_portfolio_specific(
    target: Target,
    catalog_factory: Factory,
    running_app: FastAPI,
    outbox: OutboxSender,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unexpected_demand(*args: object, **kwargs: object) -> str:
        raise AssertionError("read-only context unexpectedly requested a quote")

    monkeypatch.setattr(routes, "request_catalog_quote", unexpected_demand)

    async def create(name: str) -> str:
        created = await target.client.post(
            PORTFOLIOS,
            json={"name": name},
            headers={**headers(target.client), "Idempotency-Key": str(uuid4())},
        )
        assert created.status_code == 201, created.text
        return str(created.json()["id"])

    sibling = await create("Another strategy")
    closed = await create("Close this strategy")
    closed_response = await target.client.request(
        "DELETE",
        f"{PORTFOLIOS}/{closed}",
        json=intent("Close this strategy"),
        headers=headers(target.client),
    )
    assert closed_response.status_code == 200, closed_response.text
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=running_app), base_url="https://test"
    ) as other_owner:
        await sign_in(other_owner, outbox, unique_email("catalog-other-owner"))
        [foreign] = (await other_owner.get(PORTFOLIOS)).json()

    async with catalog_factory() as db:
        before = await _financial_counts(db)
    for pid in (closed, foreign["id"], "9223372036854775807"):
        unavailable = await target.client.get(target.context_url(pid))
        assert unavailable.status_code == 404
        assert unavailable.json() == {"detail": {"code": "portfolio_unavailable"}}
        private(unavailable)
    for pid in (target.portfolio_id, sibling):
        context = await target.client.get(target.context_url(pid))
        assert context.status_code == 200, context.text
        private(context)
        assert context.json()["portfolio_id"] == pid
        assert context.json()["read_only"] is True
        assert Decimal(context.json()["cash"]) == Decimal("10000")
        assert Decimal(context.json()["held_quantity"]) == 0
        assert Decimal(context.json()["buy_max_quantity"]) == 0
        assert context.json()["listing"]["catalog_id"] == str(target.catalog_id)
        assert context.json()["listing"]["listing_version"] == str(target.listing_version)
        assert context.json()["quote"] is None
    # Ordinary order entry is reserved for admitted curated instruments. A
    # newly discovered ticker can be viewed here but is not an order symbol.
    disabled = await target.client.post(
        f"{PORTFOLIOS}/{target.portfolio_id}/stock-trades/quote",
        json={"symbol": "FQA", "side": "buy", "quantity": "1"},
        headers=headers(target.client),
    )
    confirm = await target.client.post(
        f"{PORTFOLIOS}/{target.portfolio_id}/stock-trades",
        json=body(symbol="FQA"),
        headers=headers(target.client),
    )
    for refused in (disabled, confirm):
        assert refused.status_code == 409 and refused.json() == {
            "detail": {"code": "quote_unavailable"}
        }
        private(refused)
    order = {"listing_version": str(target.listing_version), "side": "buy", "quantity": "1"}
    # The confirm endpoint validates the request shape before it can refuse
    # financial execution on an unpromoted catalog issue.
    confirmation = {
        **order,
        "expected_exec_price": "17.26",
        "idempotency_key": str(uuid4()),
        "preview_token": f"1.0.{'0' * 64}",
    }
    base = target.context_url().removesuffix("trade-context")
    for action, payload in (
        ("preview", order),
        ("confirm", confirmation),
    ):
        denied = await target.client.post(
            base + action, json=payload, headers=headers(target.client)
        )
        assert denied.status_code == 409
        private(denied)
        assert denied.json() == {"detail": {"code": "read_only"}}
    async with catalog_factory() as db:
        assert await _financial_counts(db) == before


@pytest.mark.parametrize(
    "state", ["throttled", "source_error", "failed_check", "queue_full", "ready"]
)
async def test_selected_wait_releases_sql_and_preserves_source_reason(
    target: Target, monkeypatch: pytest.MonkeyPatch, state: str
) -> None:
    seen: list[AsyncSession] = []

    async def track(db, settings, catalog_id, *, now):
        seen.append(db)
        return await load_catalog_quote_context(db, settings, catalog_id, now=now)

    async def wait(redis, *, account, server, catalog_id, listing_version, fingerprint, purpose):
        assert not seen[-1].in_transaction()
        assert (catalog_id, listing_version) == (target.catalog_id, target.listing_version)
        assert account == server == "birja" and len(fingerprint) == 64
        assert purpose == "display"
        return state

    monkeypatch.setattr(routes, "load_catalog_quote_context", track)
    monkeypatch.setattr(routes, "request_catalog_quote", wait)
    response = await target.quote()
    private(response)
    if state == "queue_full":
        assert response.status_code == 503 and response.headers["retry-after"] == "5"
        assert response.json() == {"detail": {"code": "queue_full"}}
    else:
        assert response.status_code == 200, response.text
        assert response.json()["quote"] is None
        assert response.json()["reason"] == ("quote_unavailable" if state == "ready" else state)
    assert len(seen) == 4


async def test_wait_rechecks_revoked_permissions_and_changed_listing(
    target: Target, catalog_factory: Factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def revoke(*args: object, **kwargs: object) -> str:
        async with catalog_factory.begin() as db:
            await db.execute(
                update(StockCatalogAdmission)
                .where(StockCatalogAdmission.artifact == "alpaca_iex_quotes")
                .values(revoked_at=target.clock)
            )
        return "ready"

    monkeypatch.setattr(routes, "request_catalog_quote", revoke)
    revoked = await target.quote()
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["reason"] == "missing_permission" and revoked.json()["quote"] is None
    async with catalog_factory.begin() as db:
        active = await db.scalar(
            select(StockCatalogGeneration).where(StockCatalogGeneration.is_active)
        )
        assert active is not None
        generation = active.id
        active.sources = {
            source.artifact: source.model_dump(mode="json")
            for source in _manifest(target.clock).sources
        }
        await db.execute(
            update(StockCatalogAdmission)
            .where(StockCatalogAdmission.artifact == "alpaca_iex_quotes")
            .values(revoked_at=None)
        )

    async def replace(*args: object, **kwargs: object) -> str:
        target.clock += timedelta(hours=1)
        await _publish(
            catalog_factory,
            _manifest(target.clock, nasdaq=(("FQA", "new-issue"),)),
            generation,
            now=target.clock,
        )
        return "ready"

    monkeypatch.setattr(routes, "request_catalog_quote", replace)
    changed = await target.quote()
    assert changed.status_code == 409 and changed.json() == {"detail": {"code": "listing_changed"}}
    old_context = await target.client.get(target.context_url())
    assert old_context.status_code == 200, old_context.text
    assert old_context.json()["listing"]["catalog_id"] == str(target.catalog_id)
    assert old_context.json()["listing"]["state"] == "retired"
    assert old_context.json()["reason"] == "identity_review"
    assert old_context.json()["quote"] is None
    retired = await target.quote(old_context.json()["listing"]["listing_version"])
    assert retired.status_code == 200 and retired.json()["reason"] == "identity_review"
    assert retired.json()["quote"] is None


@pytest.mark.parametrize("target", [NOW.replace(hour=20, minute=59)], indirect=True)
async def test_selected_display_price_and_permitted_closed_mark(
    target: Target, catalog_factory: Factory, running_app: FastAPI
) -> None:
    settings = running_app.state.settings
    redis = running_app.state.redis
    account = settings.stock_data_account
    server = settings.stock_data_server
    checked_at = target.clock
    event_at = checked_at - timedelta(seconds=4)
    price = ValidIexQuote(
        Decimal("17.24"), Decimal("17.26"), Decimal("17.25"), event_at, checked_at
    )
    async with asyncio.TaskGroup() as tasks:
        choice = tasks.create_task(target.quote())
        async with asyncio.timeout(5):
            # The API and worker synchronize through Redis.
            while not (  # noqa: ASYNC110
                pending := await pending_catalog_quotes(redis, account=account, server=server)
            ):
                await asyncio.sleep(0.025)
        [request] = pending
        assert (request.catalog_id, request.listing_version) == (
            target.catalog_id,
            target.listing_version,
        )
        async with catalog_factory() as db:
            context = await load_catalog_quote_context(
                db, settings, target.catalog_id, now=checked_at
            )
        assert context.binding is not None
        assert await publish_catalog_quote(
            redis,
            request,
            context.binding,
            context.session,
            price,
            account=account,
            server=server,
            now=checked_at,
        )

    response = choice.result()
    assert response.status_code == 200, response.text
    private(response)
    expected_price = {
        "bid": "17.24",
        "ask": "17.26",
        "mid": "17.25",
        "source": "alpaca",
        "feed": "iex",
        "currency": "USD",
        "event_at": event_at.isoformat().replace("+00:00", "Z"),
        "collected_at": checked_at.isoformat().replace("+00:00", "Z"),
        "valid_until": min(context.binding.valid_until, checked_at + timedelta(minutes=10))
        .isoformat()
        .replace("+00:00", "Z"),
    }
    assert response.json()["reason"] == "ready" and response.json()["quote"] == expected_price
    assert response.json()["session"]["state"] == "open"
    assert response.json()["listing"]["ticker"] == "FQA"
    repeated = await target.quote()
    assert repeated.status_code == 200 and repeated.json() == response.json()
    assert not await pending_catalog_quotes(redis, account=account, server=server)

    target.clock += timedelta(minutes=2)
    expected_reopening = (checked_at + timedelta(days=1)).replace(hour=14, minute=30)
    for closed in (await target.quote(), await target.client.get(target.context_url())):
        assert closed.status_code == 200, closed.text
        private(closed)
        assert (
            closed.json()["reason"] == "market_closed" and closed.json()["quote"] == expected_price
        )
        assert closed.json()["session"]["state"] == "closed"
        assert (
            datetime.fromisoformat(closed.json()["session"]["next_open_at"]) == expected_reopening
        )
    assert not await pending_catalog_quotes(redis, account=account, server=server)

    await redis.delete(
        catalog_quote_key(
            account=account,
            server=server,
            catalog_id=target.catalog_id,
            listing_version=target.listing_version,
            fingerprint=context.binding.fingerprint,
        )
    )
    cold = await target.client.get(target.context_url())
    assert cold.status_code == 200, cold.text
    assert cold.json()["reason"] == "market_closed" and cold.json()["quote"] is None
    assert cold.json()["session"]["next_open_at"] is not None


@pytest.mark.parametrize("invalid", ["scope", "units", "session"])
async def test_both_closed_routes_read_the_durable_mark_with_cold_redis(
    financial_market,
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    running_app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
    invalid: str,
) -> None:
    market = financial_market
    instrument = market.instruments[0]
    _, outcome, requests = await _financial_request_and_tick(market, instrument, market.reply)
    assert (outcome, requests) == ("ready", 1)
    await install_current_test_grants()
    await sign_in(auth_client, outbox, unique_email("closed-mark-owner"))
    [portfolio] = (await auth_client.get(PORTFOLIOS)).json()
    marked = Target(
        auth_client,
        instrument.catalog_id,
        instrument.listing_id,
        portfolio["id"],
        market.now + timedelta(minutes=4),
    )
    monkeypatch.setattr(
        running_app.state,
        "settings",
        running_app.state.settings.model_copy(update={"stock_data_enabled": True}),
    )
    monkeypatch.setattr(routes, "datetime", SimpleNamespace(now=lambda _: marked.clock))

    async def no_closed_demand(*args, **kwargs):
        raise AssertionError("closed market must not enqueue quote work")

    monkeypatch.setattr(routes, "request_catalog_quote", no_closed_demand)

    async def presentation(expected: Decimal | None) -> None:
        for response in (await marked.quote(), await marked.client.get(marked.context_url())):
            assert response.status_code == 200, response.text
            private(response)
            value = response.json()
            assert value["reason"] == value["execution_reason"] == "market_closed"
            assert value["read_only"] is True and value["session"]["state"] == "closed"
            assert datetime.fromisoformat(value["session"]["next_open_at"]) == (
                market.now + timedelta(days=1)
            ).replace(hour=14, minute=30)
            if expected is None:
                assert value["quote"] is None
            else:
                assert Decimal(value["quote"]["mid"]) == expected
                assert datetime.fromisoformat(value["quote"]["event_at"]) == market.now
                assert datetime.fromisoformat(value["quote"]["valid_until"]) == (
                    market.now + timedelta(minutes=20)
                )

    await presentation(Decimal("102"))
    async with market.factory.begin() as db:
        quote = await db.get(StockCatalogFinancialQuote, instrument.coin_id)
        assert quote is not None and quote.mark_admission_id is not None
        if invalid == "scope":
            scope = await db.get(StockCatalogAdmission, quote.mark_admission_id)
            assert scope is not None
            scope.revoked_at = marked.clock
        elif invalid == "units":
            await db.execute(
                update(StockActionState)
                .where(StockActionState.coin_id == instrument.coin_id)
                .values(unit_epoch=quote.unit_epoch + 1)
            )
        else:
            quote.calendar_generation += 1
    await presentation(None)
