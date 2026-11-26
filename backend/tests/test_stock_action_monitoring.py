"""Real PostgreSQL continuity; private provider traffic is always mocked."""

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
import respx
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import SchedulerSettings
from app.db.portfolio_bootstrap import GRANTS_0026_SQL
from app.models.corporate_action import (
    StockActionEvent,
    StockActionObservation,
    StockActionRevision,
    StockActionSource,
    StockActionState,
    StockDividendEntitlement,
    StockOwnershipMovement,
)
from app.models.stock import StockDataAdmission, StockInstrument
from app.models.stock_catalog import StockCatalogAdmission, StockCatalogListing
from app.models.stock_catalog_finance import StockCatalogActionCoverage, StockCatalogInstrument
from app.models.trade import Holding
from app.services.alpaca_actions import (
    ActionBudget,
    fetch_action_snapshot,
    recheck_action_ids,
    replay_action_mutations,
)
from app.services.corporate_action_rules import classify_action
from app.services.stock_catalog_action_demand import _key, record_catalog_action_interest
from app.services.stock_catalog_actions import (
    catalog_action_candidates,
    load_catalog_action_authority,
)
from app.services.stock_catalog_promotion import CATALOG_ACTION_FIELDS
from app.services.stock_ownership import acquire_stock_gate
from app.services.stock_quote_rules import StockMapping
from app.services.stock_sessions import build_sessions
from app.tasks import stock_actions, stock_catalog_import, stock_scheduler
from tests.test_stock_admission import action_admitted, admitted
from tests.test_stock_catalog_promotion import (
    ACCOUNT,
    FIRST_ASSET,
    OTHER_ASSET,
    SERVER,
    _listing,
    _promote,
    _reviewed_grant,
)
from tests.test_stock_catalog_promotion import finance_0025 as finance_0025
from tests.test_stock_catalog_promotion import finance_0026 as finance_0026
from tests.test_stock_catalog_publish import _manifest, _publish, _rights, _sha
from tests.test_stock_sessions import evidence


@pytest_asyncio.fixture(autouse=True)
async def clean_account_attempts(redis_client):
    async for key in redis_client.scan_iter(match=stock_scheduler.ACCOUNT_WINDOW_PREFIX + "*"):
        await redis_client.delete(key)
    yield
    async for key in redis_client.scan_iter(match=stock_scheduler.ACCOUNT_WINDOW_PREFIX + "*"):
        await redis_client.delete(key)


@pytest_asyncio.fixture
async def monitor(engine, clean_stock_discovery, redis_client):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.now(UTC)
    baseline = now - timedelta(days=2)
    async with factory.begin() as db:
        rows = (await db.execute(select(StockInstrument))).scalars().all()
        saved = [(r.coin_id, r.provider_asset_id, r.provider_verified_at) for r in rows]
        for row in rows:
            row.provider_asset_id = f"synthetic-{row.coin_id}"
            row.provider_verified_at = baseline - timedelta(days=1)
        for auth in (action_admitted(), evidence(now), admitted("reference")):
            db.add(
                StockDataAdmission(
                    **asdict(
                        replace(
                            auth,
                            reviewed_at=now - timedelta(hours=1),
                            valid_from=now - timedelta(hours=2),
                            valid_until=now + timedelta(hours=2),
                            quota={**auth.quota, "requests_per_minute": 200},
                        )
                    )
                )
            )
    settings = SchedulerSettings(
        env="test",
        database_url=str(engine.url),
        redis_url="redis://:test@127.0.0.1:56379/0",
        alpaca_api_key="synthetic",
        alpaca_secret_key="synthetic",
    )
    settings = settings.model_copy(
        update={
            "stock_actions_enabled": True,
            "stock_actions_coverage_start": baseline,
            "stock_actions_segment_days": 100,
        }
    )
    try:
        yield factory, settings, baseline
    finally:
        async with factory.begin() as db:
            for model in (StockActionObservation, StockDividendEntitlement):
                await db.execute(delete(model))
            await db.execute(update(StockActionEvent).values(current_revision_id=None))
            await db.execute(delete(StockActionRevision))
            await db.execute(delete(StockActionSource))
            await db.execute(delete(StockActionEvent))
            await db.execute(delete(StockActionState))
            for cid, pid, checked in saved:
                await db.execute(
                    update(StockInstrument)
                    .where(StockInstrument.coin_id == cid)
                    .values(provider_asset_id=pid, provider_verified_at=checked)
                )
        async for key in redis_client.scan_iter(match="sim:stock:actions:*"):
            await redis_client.delete(key)


async def states(factory):
    async with factory() as db:
        return (
            (await db.execute(select(StockActionState).order_by(StockActionState.coin_id)))
            .scalars()
            .all()
        )


async def test_reviewed_operator_action_scope_is_usable_by_scheduler(
    engine, finance_0026, tmp_path, monkeypatch
):
    now = datetime.now(UTC)
    origin = now - timedelta(minutes=4)
    rights = tuple(
        right.model_copy(update={"reviewed_at": origin, "valid_until": now + timedelta(hours=2)})
        for right in _rights()
    )
    async with engine.begin() as admin:
        await admin.execute(text("ALTER SCHEMA public OWNER TO pg_database_owner"))
        raw = await admin.get_raw_connection()
        await raw.driver_connection.execute(GRANTS_0026_SQL)
    async with finance_0026.begin() as db:
        for right in rights:
            db.add(
                StockCatalogAdmission(
                    **right.model_dump(mode="json", exclude={"reviewed_at", "valid_until"}),
                    reviewed_at=right.reviewed_at,
                    valid_until=right.valid_until,
                    scope={},
                )
            )
        db.add(StockDataAdmission(**asdict(evidence(now))))
    generation = await _publish(finance_0026, _manifest(origin, rights=rights), None, now=origin)
    listing = await _listing(finance_0026, generation.generation_id, "FQA")
    execution = await _reviewed_grant(finance_0026, listing, FIRST_ASSET, origin)
    async with finance_0026.begin() as db:
        grant = await db.get(StockCatalogAdmission, execution)
        assert grant is not None
        grant.is_fixture = False
    binding = await _promote(finance_0026, listing, execution, origin, allow_fixture=False)
    monkeypatch.setenv("STOCK_DATA_ACCOUNT", ACCOUNT)
    monkeypatch.setenv("STOCK_DATA_SERVER", SERVER)
    packet = tmp_path / "synthetic-approval.json"
    command = ["admit", str(packet), "--expect-generation", str(generation.generation_id)]
    base_scope = {
        "account": ACCOUNT,
        "server": SERVER,
        "feed": "alpaca-corporate-actions",
        "catalog_id": str(binding.catalog_id),
        "listing_id": str(binding.listing_id),
        "provider_asset_id": binding.provider_asset_id,
    }
    scope = {
        **base_scope,
        "all_us_replay_ingress": True,
        "known_id_recheck": True,
        "replay_region": "us",
        "rest_symbols": [binding.provider_symbol],
        "history_start": origin.date().isoformat(),
        "future_through": (now.date() + timedelta(days=90)).isoformat(),
        "mutation_start": origin.isoformat(),
        "requests_per_minute": 12,
        "symbols_per_request": 1,
        "max_response_bytes": 65536,
    }

    def packet_with(scope):
        raw = json.dumps(
            {
                "version": 1,
                "admissions": [
                    {
                        "artifact": "catalog_actions",
                        "reference": "Synthetic reviewed exact action authority",
                        "reviewed_at": origin.isoformat(),
                        "valid_until": (now + timedelta(hours=1)).isoformat(),
                        "fields": CATALOG_ACTION_FIELDS,
                        "scope": scope,
                    }
                ],
            }
        )
        packet.write_text(raw)
        return _sha(raw)

    async with finance_0026() as db:
        migrator = db.bind
    for bad_scope in (base_scope, {**scope, "rest_symbols": ["OTHER"]}):
        packet_with(bad_scope)
        with pytest.raises(ValueError):
            await stock_catalog_import._admit(migrator, stock_catalog_import._args(command))
    digest = packet_with(scope)
    review = await stock_catalog_import._admit(migrator, stock_catalog_import._args(command))
    assert review == {"disposition": "reviewed", "packet_sha256": digest, "count": 1}
    async with finance_0026() as db:
        assert (
            await db.scalar(
                select(StockCatalogAdmission.id).where(
                    StockCatalogAdmission.artifact == "catalog_actions"
                )
            )
            is None
        )
    applied = await stock_catalog_import._admit(
        migrator,
        stock_catalog_import._args([*command, "--apply", "--expected-packet-sha", digest]),
    )
    async with engine.connect() as connection, AsyncSession(connection) as scheduler:
        await scheduler.execute(text("SET LOCAL ROLE birja_scheduler"))
        authority = await load_catalog_action_authority(
            scheduler, binding.coin_id, now, account=ACCOUNT, server=SERVER
        )
    assert authority is not None and authority.policy is not None
    assert applied["admission_ids"] == [str(authority.admission_id)]
    assert authority.policy.rest_symbols == (binding.provider_symbol,)
    assert authority.policy.requests_per_minute == 12
    assert authority.policy.mutation_start == origin


@pytest_asyncio.fixture
async def catalog_monitor(engine, finance_0026, redis_client, request):
    now = datetime.now(UTC)
    origin = now - timedelta(minutes=4)
    additional = tuple(
        (f"FDA{offset}", f"fixture-demand-{offset}")
        for offset in range(getattr(request, "param", 0))
    )
    generation = await _publish(
        finance_0026,
        _manifest(origin, nasdaq=(("FQA", "fixture-nasdaq"), *additional)),
        None,
        now=origin,
    )
    listing = await _listing(finance_0026, generation.generation_id, "FQA")
    execution = await _reviewed_grant(finance_0026, listing, FIRST_ASSET, origin)
    binding = await _promote(finance_0026, listing, execution, origin)
    async with finance_0026.begin() as db:
        db.add(StockDataAdmission(**asdict(evidence(now))))
        admission = StockCatalogAdmission(
            artifact="catalog_actions",
            reference="Fixture expanded monitoring rights",
            is_fixture=True,
            reviewed_at=origin,
            valid_until=now + timedelta(hours=2),
            fields=CATALOG_ACTION_FIELDS,
            scope={
                "account": ACCOUNT,
                "server": SERVER,
                "feed": "alpaca-corporate-actions",
                "catalog_id": str(binding.catalog_id),
                "listing_id": str(binding.listing_id),
                "provider_asset_id": binding.provider_asset_id,
                "history_start": origin.date().isoformat(),
                "future_through": (now.date() + timedelta(days=90)).isoformat(),
                "mutation_start": origin.isoformat(),
                "rest_symbols": ["FQA"],
                "symbols_per_request": 8,
                "requests_per_minute": 200,
                "max_response_bytes": 262144,
                "known_id_recheck": True,
                "all_us_replay_ingress": True,
                "replay_region": "us",
            },
        )
        db.add(admission)
        await db.flush()
        admission_id = admission.id
        grant = await db.get(StockCatalogAdmission, execution)
        assert grant is not None
        grant.revoked_at = now
    if additional:
        for offset, ticker in enumerate([*(ticker for ticker, _ in additional), "FQN"], start=3):
            extra_listing = await _listing(finance_0026, generation.generation_id, ticker)
            extra_asset = f"31000000-1234-4567-b89a-{offset:012}"
            extra_grant = await _reviewed_grant(finance_0026, extra_listing, extra_asset, origin)
            extra = await _promote(finance_0026, extra_listing, extra_grant, origin)
            async with finance_0026.begin() as db:
                db.add(
                    StockCatalogAdmission(
                        artifact=admission.artifact,
                        reference=f"Fixture actions for {ticker}",
                        is_fixture=True,
                        reviewed_at=admission.reviewed_at,
                        valid_until=admission.valid_until,
                        fields=admission.fields,
                        scope={
                            **admission.scope,
                            "catalog_id": str(extra.catalog_id),
                            "listing_id": str(extra.listing_id),
                            "provider_asset_id": extra.provider_asset_id,
                            "rest_symbols": [ticker],
                        },
                    )
                )
    settings = SchedulerSettings(
        env="test",
        database_url=str(engine.url),
        redis_url="redis://:test@127.0.0.1:56379/0",
        alpaca_api_key="synthetic",
        alpaca_secret_key="synthetic",
        stock_actions_enabled=True,
        stock_actions_coverage_start=origin,
    ).model_copy(update={"stock_actions_segment_days": 100})
    try:
        yield finance_0026, settings, origin, binding, admission_id
    finally:
        for key in (stock_actions.LOCK_KEY, stock_actions.WINDOW_KEY, _key(ACCOUNT, SERVER)):
            await redis_client.delete(key)


async def test_catalog_action_window_resumes_exact_page_and_proves_coverage(
    catalog_monitor, redis_client
):
    factory, settings, origin, binding, admission = catalog_monitor
    settings.stock_actions_max_attempts = 1
    page = "resume-catalog-page"

    async def monitor_selected(http):
        return await cycle(
            (factory, settings, origin), redis_client, http, catalog_redis=redis_client
        )

    async def select_listing(listing_id):
        await record_catalog_action_interest(
            redis_client,
            account=ACCOUNT,
            server=SERVER,
            catalog_id=binding.catalog_id,
            listing_id=listing_id,
        )

    def rest_reply(request):
        assert request.url.params["symbols"] == "FQA"
        assert request.url.params["data_quality"] == "all"
        continuation = None if request.url.params.get("page_token") == page else page
        return httpx.Response(200, json={"corporate_actions": {}, "next_page_token": continuation})

    with respx.mock(assert_all_called=False) as router:
        rest = router.get("https://data.alpaca.markets/v1/corporate-actions").mock(
            side_effect=rest_reply
        )
        replay = router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200,
            content=b"",
            headers={"content-type": "text/event-stream"},
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            await select_listing(binding.listing_id + 1)
            await monitor_selected(http)
            assert rest.call_count == 0 and replay.call_count == 0
            await redis_client.delete(stock_actions.WINDOW_KEY)
            await select_listing(binding.listing_id)
            assert (await monitor_selected(http)).status == "source_error"
            async with factory() as db:
                coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
                state = await db.get(StockActionState, binding.coin_id)
                assert (
                    coverage is not None
                    and coverage.cursor == page
                    and coverage.valid_until is None
                )
                assert (
                    state is not None
                    and state.health == "reconciling"
                    and state.valid_until is None
                )
            assert rest.call_count == 1 and replay.call_count == 0
            async with factory() as db:
                previous_listing = await db.get(StockCatalogListing, binding.listing_id)
                previous_grant = await db.get(StockCatalogAdmission, admission)
            assert previous_listing is not None and previous_grant is not None
            added_listing = await _listing(factory, previous_listing.generation_id, "FQN")
            added_execution = await _reviewed_grant(factory, added_listing, OTHER_ASSET, origin)
            added = await _promote(factory, added_listing, added_execution, origin)
            async with factory.begin() as db:
                db.add(
                    StockCatalogAdmission(
                        artifact=previous_grant.artifact,
                        reference="Fixture newly selected issue",
                        is_fixture=True,
                        reviewed_at=previous_grant.reviewed_at,
                        valid_until=previous_grant.valid_until,
                        fields=previous_grant.fields,
                        scope={
                            **previous_grant.scope,
                            "catalog_id": str(added.catalog_id),
                            "listing_id": str(added.listing_id),
                            "provider_asset_id": added.provider_asset_id,
                            "rest_symbols": ["FQN"],
                        },
                    )
                )
            settings.stock_actions_max_attempts = 4
            await redis_client.delete(stock_actions.WINDOW_KEY, _key(ACCOUNT, SERVER))
            assert (await monitor_selected(http)).status == "ok"
    assert rest.call_count == 2 and rest.calls.last.request.url.params["page_token"] == page
    assert replay.call_count == 1
    async with factory() as db:
        coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
        state = await db.get(StockActionState, binding.coin_id)
        assert coverage is not None and state is not None and state.health == "current"
        assert coverage.journal_origin == state.journal_start_at == origin
        assert coverage.admission_id == state.admission_generation == admission
        assert coverage.valid_until == state.valid_until and coverage.valid_until is not None
        assert coverage.covered_until == state.covered_until and coverage.covered_until > origin
        assert await db.get(StockCatalogActionCoverage, added.coin_id) is None


async def test_catalog_action_candidates_keep_only_active_positive_holdings_when_unselected(
    catalog_monitor,
):
    factory, _, _, binding, _ = catalog_monitor
    async with factory() as db:
        now = datetime.now(UTC)

        async def candidates():
            return await catalog_action_candidates(
                db, now, account=ACCOUNT, server=SERVER, allow_fixture=True, selected=()
            )

        owner = await db.scalar(
            text("INSERT INTO users(email) VALUES (:email) RETURNING id"),
            {"email": f"monitor-{uuid4()}@example.test"},
        )
        root = await db.scalar(text("SELECT initialize_portfolio(:owner)"), {"owner": owner})
        holding = Holding(user_id=owner, portfolio_id=root, coin_id=binding.coin_id, quantity=0)
        db.add(holding)
        await db.flush()
        assert await candidates() == ()
        holding.quantity = 1
        await db.flush()
        assert [item.binding.coin_id for item in await candidates()] == [binding.coin_id]
        holding.quantity = 0
        await acquire_stock_gate(db, binding.coin_id)
        db.add(
            StockOwnershipMovement(
                coin_id=binding.coin_id,
                user_id=owner,
                portfolio_id=root,
                sequence=1,
                economic_at=now - timedelta(days=1),
                recorded_at=now - timedelta(days=1),
                quantity=1,
                before_quantity=0,
                after_quantity=1,
                before_basis=0,
                after_basis=25,
                unit_epoch=0,
                cause_kind="opening",
                causal_key="fixture-past-exposure",
            )
        )
        await db.flush()
        assert [item.binding.coin_id for item in await candidates()] == [binding.coin_id]
        await db.execute(
            text("UPDATE accounts SET closed_at=:now WHERE id=:root"), {"now": now, "root": root}
        )
        assert await candidates() == ()


@pytest.mark.parametrize("catalog_monitor", [7], indirect=True)
async def test_catalog_action_candidates_reserve_space_for_current_selection(catalog_monitor):
    factory, _, _, original, _ = catalog_monitor
    now = datetime.now(UTC)
    async with factory() as db:
        instruments = (
            await db.scalars(
                select(StockCatalogInstrument).order_by(StockCatalogInstrument.coin_id)
            )
        ).all()
        assert len(instruments) == 9
        *held, selected = instruments
        owner = await db.scalar(
            text("INSERT INTO users(email) VALUES (:email) RETURNING id"),
            {"email": f"monitor-{uuid4()}@example.test"},
        )
        root = await db.scalar(text("SELECT initialize_portfolio(:owner)"), {"owner": owner})
        db.add_all(
            Holding(user_id=owner, portfolio_id=root, coin_id=item.coin_id, quantity=1)
            for item in held
        )
        state = await db.get(StockActionState, original.coin_id)
        assert state is not None
        scope = {"account": ACCOUNT, "server": SERVER, "allow_fixture": True}
        selection = ((selected.catalog_id, selected.listing_id),)

        async def candidates():
            await db.flush()
            return [
                row.binding.coin_id
                for row in await catalog_action_candidates(db, now, selected=selection, **scope)
            ]

        current = await candidates()
        assert len(current) == 8 and current[0] == selected.coin_id
        assert sum(item.coin_id in current for item in held) == 7
        db.add(Holding(user_id=owner, portfolio_id=root, coin_id=selected.coin_id, quantity=1))
        current = await candidates()
        assert len(current) == 8 and current[0] == selected.coin_id
        assert sum(item.coin_id in current for item in held) == 7
        state.staged_continuation = {
            "target_until": (now - timedelta(seconds=5)).isoformat(),
            "policy_key": "fixture-active-window",
        }
        assert await candidates() == [original.coin_id]
        state.staged_continuation = {
            **state.staged_continuation,
            "target_until": (now - timedelta(minutes=5)).isoformat(),
        }
        assert (await candidates())[0] == selected.coin_id


async def test_catalog_default_refresh_preserves_complete_lease_until_real_gap(
    catalog_monitor, redis_client
):
    factory, settings, origin, binding, _ = catalog_monitor
    settings.stock_actions_segment_days = 31
    leases = []
    gap = False
    capped = False

    async def replay_reply(request):
        if leases:
            async with factory() as db:
                state = await db.get(StockActionState, binding.coin_id)
                coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
                assert state is not None and coverage is not None
                assert state.health == "current"
                assert (state.epoch, state.valid_until) == leases[-1]
                assert state.valid_until == coverage.valid_until
                assert state.covered_until == coverage.covered_until
                assert request.url.params["since"] == coverage.covered_until.isoformat()
        if capped:
            return httpx.Response(
                200,
                content=b" " * (settings.stock_actions_max_response_bytes + 1),
                headers={"content-type": "text/event-stream"},
            )
        return httpx.Response(
            200,
            content=b"",
            headers={"content-type": "application/json" if gap else "text/event-stream"},
        )

    with respx.mock(assert_all_called=False) as router:
        rest = router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
            200, json={"corporate_actions": {}, "next_page_token": None}
        )
        replay = router.get(url__startswith="https://stream.data.alpaca.markets/").mock(
            side_effect=replay_reply
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            for _ in range(2):
                await redis_client.delete(stock_actions.WINDOW_KEY)
                assert (await cycle((factory, settings, origin), redis_client, http)).status == "ok"
                async with factory() as db:
                    state = await db.get(StockActionState, binding.coin_id)
                    assert state is not None and state.valid_until is not None
                    assert state.health == "current"
                    leases.append((state.epoch, state.valid_until))
            assert leases[1][0] == leases[0][0]
            assert leases[1][1] > leases[0][1]
            assert rest.call_count == 3 and replay.call_count == 2
            capped = True
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (
                await cycle((factory, settings, origin), redis_client, http)
            ).status == "source_error"
            async with factory() as db:
                partial = await db.get(StockActionState, binding.coin_id)
                assert partial is not None and partial.staged_continuation is not None
                assert (partial.epoch, partial.valid_until) == leases[-1]
                staged = partial.staged_continuation
                assert (
                    datetime.fromisoformat(staged["replay_at"])
                    < datetime.fromisoformat(staged["replay_end"])
                    < datetime.fromisoformat(staged["target_until"])
                )
            capped = False
            gap = True
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (
                await cycle((factory, settings, origin), redis_client, http)
            ).status == "source_error"
    async with factory() as db:
        state = await db.get(StockActionState, binding.coin_id)
        coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
        assert state is not None and coverage is not None
        assert state.health == "reconciling"
        assert state.valid_until is None and coverage.valid_until is None
        assert state.epoch > leases[-1][0]


async def test_catalog_action_scope_without_replay_ingress_keeps_first_fill_held(
    catalog_monitor, redis_client
):
    factory, settings, origin, binding, admission = catalog_monitor
    async with factory.begin() as db:
        grant = await db.get(StockCatalogAdmission, admission)
        assert grant is not None
        grant.scope = {**grant.scope, "all_us_replay_ingress": False}
    with respx.mock() as router:
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (
                await cycle((factory, settings, origin), redis_client, http)
            ).status == "source_error"
    assert not router.calls
    async with factory() as db:
        state = await db.get(StockActionState, binding.coin_id)
        assert state is not None and state.health == "unknown" and state.valid_until is None
        assert await db.get(StockCatalogActionCoverage, binding.coin_id) is None


@pytest.mark.parametrize(
    "problem",
    [
        "missing_state",
        "incomplete_journal",
        "unproved_owned_book",
        "lost_lease",
        "admission_before_preparing",
        "admission_at_preparation",
        "date_scope",
        "account_quota",
        "publication_epoch",
    ],
)
async def test_catalog_cycle_holds_incomplete_state_or_lost_authority(
    catalog_monitor, redis_client, monkeypatch, problem
):
    factory, settings, origin, binding, admission_id = catalog_monitor
    async with factory.begin() as db:
        state = await db.get(StockActionState, binding.coin_id)
        assert state is not None
        if problem == "incomplete_journal":
            state.journal_start_at = origin
            state.complete_from = None
        elif problem == "unproved_owned_book":
            owner = await db.scalar(
                text("INSERT INTO users(email) VALUES (:email) RETURNING id"),
                {"email": f"monitor-{uuid4()}@example.test"},
            )
            root = await db.scalar(text("SELECT initialize_portfolio(:owner)"), {"owner": owner})
            db.add(
                Holding(
                    user_id=owner,
                    portfolio_id=root,
                    coin_id=binding.coin_id,
                    quantity=1,
                    cost_basis=25,
                )
            )
        elif problem == "date_scope":
            grant = await db.get(StockCatalogAdmission, admission_id)
            assert grant is not None
            grant.scope = grant.scope | {"future_through": origin.date().isoformat()}

    if problem == "missing_state":
        real_get = AsyncSession.get

        async def missing_state(db, model, identity, *args, **kwargs):
            value = await real_get(db, model, identity, *args, **kwargs)
            if model is StockActionState and identity == binding.coin_id:
                assert value is not None
                return None
            return value

        monkeypatch.setattr(AsyncSession, "get", missing_state)
    elif problem == "lost_lease":
        real_get = redis_client.get

        async def no_owned_lock(key):
            return None if key == stock_actions.LOCK_KEY else await real_get(key)

        monkeypatch.setattr(redis_client, "get", no_owned_lock)
    elif problem in ("admission_before_preparing", "admission_at_preparation"):
        calls = 0

        async def reload_authority(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == (1 if problem == "admission_before_preparing" else 2):
                return None
            return await load_catalog_action_authority(*args, **kwargs)

        monkeypatch.setattr(stock_actions, "load_catalog_action_authority", reload_authority)
    elif problem == "account_quota":

        async def exhausted(*_args, **_kwargs):
            return False

        monkeypatch.setattr(stock_actions, "reserve_account_attempt", exhausted)

    async def provider_page(_request):
        assert problem == "publication_epoch"
        async with factory.begin() as db:
            state = await db.get(StockActionState, binding.coin_id)
            assert state is not None
            state.epoch += 1
        return httpx.Response(200, json={"corporate_actions": {}, "next_page_token": None})

    with respx.mock(assert_all_called=False) as router:
        rest = router.get("https://data.alpaca.markets/v1/corporate-actions").mock(
            side_effect=provider_page
        )
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle((factory, settings, origin), redis_client, http)
    assert result.status == "source_error"
    assert rest.call_count == (1 if problem == "publication_epoch" else 0)
    async with factory() as db:
        coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
        assert coverage is None or (coverage.valid_until is None and coverage.covered_until is None)


async def test_catalog_action_quota_is_bounded_without_starving_legacy_scope(
    catalog_monitor, redis_client, monkeypatch
):
    factory, settings, origin, binding, _ = catalog_monitor
    async with factory.begin() as db:
        for grant in (action_admitted(), admitted("reference")):
            db.add(
                StockDataAdmission(
                    **asdict(
                        replace(
                            grant,
                            reviewed_at=origin,
                            valid_from=origin,
                            valid_until=origin + timedelta(hours=1),
                        )
                    )
                )
            )
    settings.stock_actions_max_attempts = 8
    statuses = iter(("ok", "locked"))
    quotas = []

    async def catalog(_factory, _redis, _http, _settings, _token, _now, budget, authorities):
        assert [a.binding.coin_id for a in authorities] == [binding.coin_id]
        quotas.append(budget.max_attempts)
        budget.attempts = 1
        raise stock_actions.ActionError("source_gap")

    async def legacy(_factory, _redis, _http, _settings, _token, _now, budget):
        quotas.append(budget.max_attempts)
        assert budget.attempts == 1
        return stock_actions.CycleResult(next(statuses))

    monkeypatch.setattr(stock_actions, "_refresh_catalog", catalog)
    monkeypatch.setattr(stock_actions, "_refresh", legacy)
    with respx.mock() as router:
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (
                await cycle((factory, settings, origin), redis_client, http)
            ).status == "source_error"
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (await cycle((factory, settings, origin), redis_client, http)).status == "locked"
    assert quotas == [4, 8, 4, 8] and not router.calls


async def test_catalog_renewed_review_rechecks_retained_event_id(catalog_monitor, redis_client):
    factory, settings, origin, binding, admission_id = catalog_monitor
    now = datetime.now(UTC)
    async with factory() as db:
        authority = await load_catalog_action_authority(
            db, binding.coin_id, now, account=ACCOUNT, server=SERVER, allow_fixture=True
        )
    assert authority is not None
    # An action before the journal origin is intentionally excluded from an empty book.
    ex_date = next(
        session.session_date.isoformat()
        for session in build_sessions(now, authority.calendar)
        if session.exchange == binding.listing_exchange
        and session.opens_at is not None
        and session.opens_at > now
    )
    identity = str(uuid4())
    terms = {
        "id": identity,
        "symbol": authority.ticker,
        "process_date": now.date().isoformat(),
        "ex_date": ex_date,
        "record_date": ex_date,
        "payable_date": ex_date,
        "currency": "USD",
        "rate": 0.25,
        "sub_type": "ordinary",
        "foreign": False,
        "special": False,
        "due_bills": False,
    }
    requested_ids = []

    def source(request):
        ids = request.url.params.get("ids")
        if ids is not None:
            requested_ids.append(ids)
        return httpx.Response(
            200,
            json={
                "corporate_actions": {"cash_dividends": [terms]} if ids is None else {},
                "next_page_token": None,
            },
        )

    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=source)
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle((factory, settings, origin), redis_client, http)).status == "ok"
            async with factory.begin() as db:
                old = await db.get(StockCatalogAdmission, admission_id)
                assert old is not None
                old.revoked_at = datetime.now(UTC)
                replacement = StockCatalogAdmission(
                    artifact=old.artifact,
                    reference="Synthetic renewed exact action scope",
                    is_fixture=True,
                    reviewed_at=old.revoked_at,
                    valid_until=old.valid_until,
                    fields=old.fields,
                    scope=old.scope,
                )
                db.add(replacement)
                await db.flush()
                renewed_id = replacement.id
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (
                await cycle((factory, settings, origin), redis_client, http)
            ).status == "source_error"
    assert requested_ids == [identity]
    async with factory() as db:
        source_count = await db.scalar(text("SELECT count(*) FROM stock_action_sources"))
        state = await db.get(StockActionState, binding.coin_id)
        coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
        assert source_count == 1 and state is not None and coverage is not None
        assert state.admission_generation == coverage.admission_id == renewed_id
        assert state.health == "reconciling" and state.valid_until is coverage.valid_until is None


@pytest.mark.parametrize("limit", ["known_ids", "entitlements"])
async def test_catalog_monitor_refuses_truncated_work_sets(
    catalog_monitor, redis_client, monkeypatch, limit
):
    factory, settings, origin, binding, _ = catalog_monitor
    real_execute, real_scalars = AsyncSession.execute, AsyncSession.scalars

    async def known_or_actual(db, stmt, *args, **kwargs):
        if "SELECT stock_action_sources.provider_event_id, stock_action_events.coin_id" in str(
            stmt
        ):
            return SimpleNamespace(all=lambda: [(str(i), binding.coin_id) for i in range(1001)])
        return await real_execute(db, stmt, *args, **kwargs)

    async def events_or_actual(db, stmt, *args, **kwargs):
        if "SELECT stock_action_events.id" in str(stmt):
            return SimpleNamespace(all=lambda: list(range(1001)))
        return await real_scalars(db, stmt, *args, **kwargs)

    if limit == "known_ids":
        monkeypatch.setattr(AsyncSession, "execute", known_or_actual)
    else:
        monkeypatch.setattr(AsyncSession, "scalars", events_or_actual)
    with respx.mock(assert_all_called=False) as router:
        rest = router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
            200, json={"corporate_actions": {}, "next_page_token": None}
        )
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle((factory, settings, origin), redis_client, http)
    assert result.status == "source_error"
    assert rest.call_count == (0 if limit == "known_ids" else 1)
    async with factory() as db:
        coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
        assert coverage is not None and coverage.valid_until is coverage.covered_until is None


@pytest.mark.parametrize("deadline", ["review", "freshness"])
async def test_catalog_monitor_keeps_expired_publication_held(
    catalog_monitor, redis_client, monkeypatch, deadline
):
    factory, settings, origin, binding, _ = catalog_monitor
    real_clock, real_persist = stock_actions._clock, stock_actions.persist_action_batch
    completion_time = None

    async def after_persist(db, batch, authority, *, catalog, **scope):
        nonlocal completion_time
        result = await real_persist(db, batch, authority, catalog=catalog, **scope)
        completion_time = (
            catalog.valid_until
            if deadline == "review"
            else await real_clock(db)
            + timedelta(seconds=settings.stock_actions_health_max_age_seconds + 1)
        )
        return result

    async def publication_clock(db):
        return completion_time or await real_clock(db)

    monkeypatch.setattr(stock_actions, "_clock", publication_clock)
    monkeypatch.setattr(stock_actions, "persist_action_batch", after_persist)
    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
            200, json={"corporate_actions": {}, "next_page_token": None}
        )
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle((factory, settings, origin), redis_client, http)
    assert result.status == ("source_error" if deadline == "review" else "ok")
    async with factory() as db:
        state = await db.get(StockActionState, binding.coin_id)
        coverage = await db.get(StockCatalogActionCoverage, binding.coin_id)
        assert state is not None and coverage is not None
        assert state.health == "reconciling" and state.valid_until is coverage.valid_until is None


async def test_catalog_monitor_requires_current_collection_policy(catalog_monitor, redis_client):
    factory, settings, _, binding, _ = catalog_monitor
    now = datetime.now(UTC)
    async with factory() as db:
        reviewed = await load_catalog_action_authority(
            db, binding.coin_id, now, account=ACCOUNT, server=SERVER, allow_fixture=True
        )
    assert reviewed is not None and reviewed.policy is not None
    with respx.mock() as router:
        async with httpx.AsyncClient(trust_env=False) as http:
            with pytest.raises(stock_actions.ActionError, match="admission"):
                await stock_actions._refresh_catalog(
                    factory,
                    redis_client,
                    http,
                    settings,
                    "synthetic-lock",
                    lambda: now,
                    ActionBudget(),
                    (replace(reviewed, policy=None),),
                )
    assert not router.calls


async def test_catalog_action_parser_verifies_explicit_dates_and_keeps_missing_terms_held(
    catalog_monitor,
):
    factory, _, origin, binding, _ = catalog_monitor
    now = datetime.now(UTC)
    async with factory() as db:
        authority = await load_catalog_action_authority(
            db,
            binding.coin_id,
            now,
            account=ACCOUNT,
            server=SERVER,
            allow_fixture=True,
        )
    assert authority is not None
    day = next(
        row.session_date
        for row in build_sessions(now, authority.calendar)
        if row.exchange == binding.listing_exchange
        and row.opens_at is not None
        and row.session_date >= origin.date()
    )
    terms = {
        "id": str(uuid4()),
        "symbol": "FQA",
        "process_date": day.isoformat(),
        "ex_date": day.isoformat(),
        "record_date": day.isoformat(),
        "payable_date": day.isoformat(),
        "currency": "USD",
        "rate": 0.25,
        "sub_type": "ordinary",
        "foreign": False,
        "special": False,
        "due_bills": False,
    }
    incomplete = {name: value for name, value in terms.items() if name != "special"}
    incomplete["id"] = str(uuid4())
    mapping = StockMapping(binding.coin_id, "FQA", binding.provider_asset_id, origin, "NASDAQ")
    with respx.mock() as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
            200,
            json={
                "corporate_actions": {"cash_dividends": [terms, incomplete]},
                "next_page_token": None,
            },
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await fetch_action_snapshot(
                http,
                (mapping,),
                lambda: (authority,),
                lambda: now,
                ActionBudget(),
                start=day,
                end=day,
                catalog=(authority,),
            )
    assert result.complete and len(result.records) == 2
    assert all(row.dates_verified for row in result.records)
    assert [classify_action(row, catalog_symbol="FQA").kind for row in result.records] == [
        "supported_dividend",
        "uncertain",
    ]


async def test_catalog_action_reader_holds_unreviewed_requests_and_ambiguous_records(
    catalog_monitor,
):
    factory, _, origin, binding, _ = catalog_monitor
    now = datetime.now(UTC)
    async with factory() as db:
        authority = await load_catalog_action_authority(
            db, binding.coin_id, now, account=ACCOUNT, server=SERVER, allow_fixture=True
        )
    assert authority is not None and authority.policy is not None
    mapping = StockMapping(
        binding.coin_id, authority.ticker, binding.provider_asset_id, origin, "NASDAQ"
    )
    identity = str(uuid4())
    day = origin.date()

    with respx.mock(assert_all_called=False) as router:
        rest = router.get("https://data.alpaca.markets/v1/corporate-actions")
        async with httpx.AsyncClient(trust_env=False) as http:

            async def snapshot(scopes, mappings, *, observed=None, start=day):
                return await fetch_action_snapshot(
                    http,
                    mappings,
                    lambda: observed if observed is not None else scopes,
                    lambda: now,
                    ActionBudget(),
                    start=start,
                    end=day,
                    catalog=scopes,
                )

            unreviewed = await snapshot((authority,), (mapping,), start=day - timedelta(days=1))
            assert unreviewed.reason == "unreviewed_window"
            wrong_mapping = await snapshot((authority,), (replace(mapping, symbol="FQN"),))
            assert wrong_mapping.reason == "invalid_request"
            assert (
                await snapshot((authority,), (mapping,), observed=())
            ).reason == "admission_changed"
            expired = await snapshot((replace(authority, valid_until=now),), (mapping,))
            assert expired.reason == "admission"
            replay = await replay_action_mutations(
                http,
                (mapping,),
                lambda: (authority,),
                lambda: now,
                ActionBudget(),
                since=origin - timedelta(seconds=1),
                until=now,
                catalog=(authority,),
            )
            assert replay.reason == "unreviewed_window" and not router.calls

            entry = {"id": identity, "symbol": authority.ticker, "rate": 0.25, "currency": "USD"}
            rest.respond(
                200,
                json={"corporate_actions": {"cash_dividends": [entry]}, "next_page_token": None},
            )
            missing_date = await snapshot((authority,), (mapping,))
            assert missing_date.uncertain_coin_ids == {binding.coin_id} and not missing_date.records

            ambiguous = replace(authority, ambiguous_symbols=frozenset({authority.ticker}))
            held = await snapshot((ambiguous,), (mapping,))
            assert held.uncertain_coin_ids == {binding.coin_id} and not held.records
            known = await recheck_action_ids(
                http,
                (mapping,),
                lambda: (ambiguous,),
                lambda: now,
                ActionBudget(),
                ids={identity: authority.ticker},
                catalog=(ambiguous,),
            )
            assert known.uncertain_coin_ids == {binding.coin_id} and not known.records

            second = replace(
                authority,
                ticker="FQN",
                binding=replace(
                    binding,
                    coin_id=binding.coin_id + 1,
                    provider_symbol="FQN",
                    provider_asset_id="other-fixture-asset",
                ),
                policy=replace(authority.policy, rest_symbols=("FQN",)),
            )
            second_mapping = replace(
                mapping,
                coin_id=second.binding.coin_id,
                symbol=second.ticker,
                provider_asset_id=second.binding.provider_asset_id,
            )
            rest.respond(
                200,
                json={
                    "corporate_actions": {
                        "cash_dividends": [entry | {"process_date": day.isoformat()}]
                    },
                    "next_page_token": None,
                },
            )
            scoped = await snapshot((authority, second), (mapping, second_mapping))
            assert [record.coin_id for record in scoped.records] == [binding.coin_id]
            rest.respond(
                200,
                json={
                    "corporate_actions": {
                        "cash_dividends": [entry | {"old_symbol": second.ticker}]
                    },
                    "next_page_token": None,
                },
            )
            disputed = await snapshot((authority, second), (mapping, second_mapping))
            assert (
                disputed.uncertain_coin_ids == {binding.coin_id, second.binding.coin_id}
                and not disputed.records
            )


async def cycle(monitor, redis, http, *, catalog_redis=None):
    factory, settings, _ = monitor
    return await stock_actions.run_stock_action_cycle(
        sessionmaker=factory, redis=redis, http=http, settings=settings, catalog_redis=catalog_redis
    )


async def test_complete_snapshot_and_replay_publish_twenty_durable_current_states(
    monitor, redis_client
):
    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
            200, json={"corporate_actions": {}, "next_page_token": None}
        )
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    rows = await states(monitor[0])
    assert len(rows) == 20
    assert all(row.health == "current" for row in rows), [
        (r.health, r.staged_continuation) for r in rows[:1]
    ]
    assert all(row.covered_until > monitor[2] for row in rows)
    assert result.status == "ok"


def routes(router, *, rest_status=200, replay_status=200, body=None):
    rest = router.get("https://data.alpaca.markets/v1/corporate-actions").respond(
        rest_status, json=body or {"corporate_actions": {}, "next_page_token": None}
    )
    replay = router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
        replay_status, content=b"", headers={"content-type": "text/event-stream"}
    )
    return rest, replay


@pytest.mark.parametrize("status", [401, 403, 404, 429, 500])
async def test_failed_replay_never_publishes_current(monitor, redis_client, status):
    with respx.mock(assert_all_called=False) as router:
        routes(router, replay_status=status)
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    rows = await states(monitor[0])
    assert result.status == "source_error"
    assert len(rows) == 20 and all(r.health == "reconciling" for r in rows)
    assert all(r.covered_until is None and r.valid_until is None for r in rows)


async def test_durable_segments_resume_until_future_horizon_complete(monitor, redis_client):
    factory, settings, _ = monitor
    settings.stock_actions_segment_days = 31
    with respx.mock(assert_all_called=False) as router:
        rest, _ = routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            starts = []
            for _index in range(2):
                await redis_client.delete(stock_actions.WINDOW_KEY)
                assert (await cycle(monitor, redis_client, http)).status == "source_error"
                rows = await states(factory)
                assert all(r.health == "reconciling" and r.valid_until is None for r in rows)
                starts.append(rest.calls.last.request.url.params["start"])
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (await cycle(monitor, redis_client, http)).status == "ok"
            assert len(set(starts)) == 2
    assert all(r.health == "current" for r in await states(factory))


async def test_incomplete_pagination_keeps_start_and_records_continuation(monitor, redis_client):
    with respx.mock(assert_all_called=False) as router:
        routes(router, body={"corporate_actions": {}, "next_page_token": "same-page"})
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    rows = await states(monitor[0])
    assert all(r.staged_continuation["next_date"] == monitor[2].date().isoformat() for r in rows)
    assert all(r.health == "reconciling" for r in rows)


@pytest.mark.parametrize("product", ["actions", "calendar", "reference"])
async def test_revoked_rights_create_no_http_or_monitor_authority(monitor, redis_client, product):
    async with monitor[0].begin() as db:
        await db.execute(
            update(StockDataAdmission)
            .where(StockDataAdmission.product == product)
            .values(collection_allowed=False)
        )
    with respx.mock() as router:
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
        assert not router.calls
    assert not await states(monitor[0])


async def test_disabled_needs_no_datastore_or_provider(monitor, redis_client):
    monitor[1].stock_actions_enabled = False
    async with httpx.AsyncClient(trust_env=False) as http:
        assert (await cycle(monitor, redis_client, http)).status == "ok"
    assert not await states(monitor[0])


@pytest.mark.parametrize("key", [stock_actions.LOCK_KEY, stock_actions.WINDOW_KEY])
async def test_duplicate_cycle_and_cadence_are_independently_owned(monitor, redis_client, key):
    await redis_client.set(key, "other", px=60000)
    async with httpx.AsyncClient(trust_env=False) as http:
        assert (await cycle(monitor, redis_client, http)).status == "locked"
    assert await redis_client.get(key) == "other"


async def test_shared_account_budget_counts_real_attempts_and_rejects_excess(monitor, redis_client):
    from app.tasks.stock_scheduler import _admissions, reserve_account_attempt

    settings = monitor[1]
    settings.stock_account_requests_per_minute = 2
    async with monitor[0]() as db:
        auth = await _admissions(db)
    assert await reserve_account_attempt(redis_client, settings, auth)
    with respx.mock(assert_all_called=False) as router:
        rest, replay = routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
            assert http.event_hooks["request"] == []
    assert rest.call_count == 1 and replay.call_count == 0
    assert all(row.health == "reconciling" for row in await states(monitor[0]))
    assert not await reserve_account_attempt(redis_client, settings, auth)


async def test_account_budget_is_atomic_across_concurrent_products(monitor, redis_client):
    import asyncio

    from app.tasks.stock_scheduler import _admissions, reserve_account_attempt

    settings = monitor[1]
    settings.stock_account_requests_per_minute = 3
    async with monitor[0]() as db:
        auth = await _admissions(db)
    results = await asyncio.gather(
        *(reserve_account_attempt(redis_client, settings, auth) for _ in range(12))
    )
    assert sum(results) == 3
    settings.stock_data_account = "other-account"
    assert await reserve_account_attempt(redis_client, settings, auth)


@pytest.mark.parametrize("phase", ["acquire", "release"])
async def test_redis_failure_is_bounded_and_sanitized(monitor, redis_client, monkeypatch, phase):
    from redis.exceptions import RedisError

    async def failed(*args, **kwargs):
        raise RedisError("private-credential-never-log")

    monkeypatch.setattr(redis_client, "set" if phase == "acquire" else "eval", failed)
    with respx.mock(assert_all_called=False) as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            result = await cycle(monitor, redis_client, http)
    assert result.status == ("lock_error" if phase == "acquire" else "source_error")


async def test_hung_source_cancels_and_releases_only_own_lease(monitor, redis_client):
    import asyncio

    entered = asyncio.Event()

    async def hang(request):
        entered.set()
        await asyncio.Event().wait()

    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=hang)
        async with httpx.AsyncClient(trust_env=False) as http:
            task = asyncio.create_task(cycle(monitor, redis_client, http))
            await asyncio.wait_for(entered.wait(), 3)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert http.event_hooks["request"] == []
    assert not await redis_client.exists(stock_actions.LOCK_KEY)
    assert all(r.health == "reconciling" for r in await states(monitor[0]))


async def test_health_deadline_never_outlives_reviewed_calendar(monitor, redis_client):
    reviewed_until = datetime.now(UTC) + timedelta(seconds=10)
    async with monitor[0].begin() as db:
        row = (
            await db.execute(
                select(StockDataAdmission).where(StockDataAdmission.product == "calendar")
            )
        ).scalar_one()
        row.calendar = {**row.calendar, "review_valid_until": reviewed_until.isoformat()}
    with respx.mock() as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
    assert all(r.valid_until == reviewed_until for r in await states(monitor[0]))


def mixed_body():
    from uuid import UUID

    today = datetime.now(UTC).date()
    base = {
        "symbol": "AAPL",
        "cusip": "037833100",
        "process_date": today.isoformat(),
        "ex_date": (today + timedelta(days=2)).isoformat(),
    }
    return {
        "corporate_actions": {
            "cash_dividends": [
                {
                    **base,
                    "id": str(UUID(int=1)),
                    "rate": 1,
                    "currency": "USD",
                    "foreign": False,
                    "special": False,
                    "record_date": base["ex_date"],
                    "payable_date": (today + timedelta(days=5)).isoformat(),
                }
            ],
            "forward_splits": [{**base, "id": str(UUID(int=2)), "old_rate": 1, "new_rate": 2}],
            "reverse_splits": [{**base, "id": str(UUID(int=3)), "old_rate": 2, "new_rate": 1}],
        },
        "next_page_token": None,
    }


async def test_mixed_events_only_cash_dividends_receive_entitlement_derivation(
    monitor, redis_client
):
    from app.services.corporate_actions import persistent_action_holds

    with respx.mock() as router:
        routes(router, body=mixed_body())
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
    async with monitor[0]() as db:
        event = (await db.execute(select(StockActionEvent).limit(1))).scalar_one()
        assert await persistent_action_holds(db, event.coin_id)
    assert len(await states(monitor[0])) == 20


async def test_retained_old_ids_recheck_and_missing_hold_survives_recovery(monitor, redis_client):
    from app.services.corporate_actions import persistent_action_holds

    original = mixed_body()
    for group in original["corporate_actions"].values():
        for event in group:
            event["process_date"] = monitor[2].date().isoformat()
    phase = 0
    requests = []

    def respond(request):
        requests.append(dict(request.url.params))
        body = (
            original
            if phase == 0 or (phase == 2 and "ids" in request.url.params)
            else {"corporate_actions": {}, "next_page_token": None}
        )
        return httpx.Response(200, json=body)

    with respx.mock(assert_all_called=False) as router:
        routes(router)
        router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=respond)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
            for phase in (1, 2):
                await redis_client.delete(stock_actions.WINDOW_KEY)
                result = await cycle(monitor, redis_client, http)
                assert result.status == ("source_error" if phase == 1 else "ok")
    known_requests = [request for request in requests if "ids" in request]
    assert len(known_requests) == 2
    assert all(set(request) == {"ids", "limit"} for request in known_requests)
    async with monitor[0]() as db:
        cid = (await db.execute(select(StockActionEvent.coin_id).limit(1))).scalar_one()
        assert "source_gap" in await persistent_action_holds(db, cid)
        assert (await db.get(StockActionState, cid)).health == "reconciling"


async def test_eight_attempt_rest_bound_resumes_token_after_process_restart(monitor, redis_client):
    def page(request):
        token = int(request.url.params.get("page_token", "0"))
        return httpx.Response(
            200,
            json={
                "corporate_actions": {},
                "next_page_token": str(token + 1) if token < 8 else None,
            },
        )

    with respx.mock(assert_all_called=False) as router:
        rest = router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=page)
        replay = router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b"", headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
        rows = await states(monitor[0])
        assert rest.call_count == 8 and replay.call_count == 0
        assert all(r.staged_continuation["continuation"] == "8" for r in rows)
        target = rows[0].staged_continuation["target_until"]
        await redis_client.delete(stock_actions.WINDOW_KEY)
        # New HTTP client and service invocation use SQL-only recovery state.
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "ok"
        assert rest.calls[8].request.url.params["page_token"] == "8"
        assert replay.calls.last.request.url.params["until"] == target
    assert all(r.health == "current" for r in await states(monitor[0]))


async def test_large_replay_gap_bisects_and_advances_only_completed_frontier(monitor, redis_client):
    monitor[1].stock_actions_max_response_bytes = 1024
    intervals = []

    def replay(request):
        start = datetime.fromisoformat(request.url.params["since"])
        end = datetime.fromisoformat(request.url.params["until"])
        intervals.append((start, end))
        body = b":" * 1025 if end - start > timedelta(days=1, seconds=1) else b""
        return httpx.Response(200, content=body, headers={"content-type": "text/event-stream"})

    with respx.mock(assert_all_called=False) as router:
        rest, _ = routes(router)
        router.get(url__startswith="https://stream.data.alpaca.markets/").mock(side_effect=replay)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
            first = (await states(monitor[0]))[0]
            assert first.staged_continuation["replay_frontier"] == monitor[2].isoformat()
            assert first.covered_until is None
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
            second = (await states(monitor[0]))[0]
            assert second.covered_until is None
            assert second.staged_continuation["replay_frontier"] == intervals[1][1].isoformat()
            await redis_client.delete(stock_actions.WINDOW_KEY)
            assert (await cycle(monitor, redis_client, http)).status == "ok"
    assert rest.call_count == 1
    assert intervals[0][0] == intervals[1][0] == monitor[2]
    assert intervals[1][1] == intervals[2][0]  # Inclusive shared endpoint; no gap.
    assert intervals[0][1] == intervals[2][1]


async def test_unfinishable_same_instant_density_stays_explicitly_held(
    monitor, redis_client, monkeypatch
):
    fixed = datetime.now(UTC)
    monitor[1].stock_actions_coverage_start = fixed - timedelta(microseconds=1)
    monitor[1].stock_actions_max_response_bytes = 1024

    async def clock(db):
        return fixed

    monkeypatch.setattr(stock_actions, "_clock", clock)
    with respx.mock(assert_all_called=False) as router:
        routes(router)
        router.get(url__startswith="https://stream.data.alpaca.markets/").respond(
            200, content=b":" * 1025, headers={"content-type": "text/event-stream"}
        )
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    rows = await states(monitor[0])
    assert all(r.staged_continuation["reason"] == "replay_density_limit" for r in rows)
    assert all(r.covered_until is None and r.health == "reconciling" for r in rows)


@pytest.mark.parametrize("problem", ["baseline", "future", "mapping", "journal"])
async def test_invalid_baseline_mapping_or_journal(monitor, redis_client, problem):
    factory, settings, baseline = monitor
    if problem == "baseline":
        settings.stock_actions_coverage_start = None
    elif problem == "future":
        settings.stock_actions_coverage_start = datetime.now(UTC) + timedelta(days=1)
    else:
        async with factory.begin() as db:
            if problem == "mapping":
                await db.execute(update(StockInstrument).values(provider_verified_at=None))
            else:
                cid = (await db.execute(select(StockInstrument.coin_id).limit(1))).scalar_one()
                db.add(StockActionState(coin_id=cid, admission_generation=4))
    with respx.mock() as router:
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
        assert not router.calls


@pytest.mark.parametrize("problem", ["permission", "lease"])
async def test_post_await_authority_or_lease_loss(monitor, redis_client, problem):
    async def response(request):
        if problem == "permission":
            async with monitor[0].begin() as db:
                await db.execute(
                    update(StockDataAdmission)
                    .where(StockDataAdmission.product == "actions")
                    .values(derived_allowed=False)
                )
        else:
            await redis_client.set(stock_actions.LOCK_KEY, "new-owner", px=60000)
        return httpx.Response(200, json={"corporate_actions": {}, "next_page_token": None})

    with respx.mock(assert_all_called=False) as router:
        router.get("https://data.alpaca.markets/v1/corporate-actions").mock(side_effect=response)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    assert all(
        r.health == "reconciling" and r.valid_until is None for r in await states(monitor[0])
    )
    if problem == "lease":
        assert await redis_client.get(stock_actions.LOCK_KEY) == "new-owner"


@pytest.mark.parametrize("race", ["epoch", "delete", "covered", "permission", "expired"])
async def test_global_publication_race_rolls_back_all_twenty(
    monitor, redis_client, monkeypatch, race
):
    original = AsyncSession.execute
    clock = stock_actions._clock
    raced = False

    async def execute(db, statement, *args, **kwargs):
        nonlocal raced
        if (
            not raced
            and getattr(statement, "_for_update_arg", None) is not None
            and "stock_gate" not in db.info
            and "stock_action_state" in str(statement)
        ):
            raced = True
            async with monitor[0].begin() as other:
                cid = (
                    await other.execute(
                        select(StockActionState.coin_id).order_by(StockActionState.coin_id).limit(1)
                    )
                ).scalar_one()
                if race == "delete":
                    await other.execute(
                        delete(StockActionState).where(StockActionState.coin_id == cid)
                    )
                elif race == "permission":
                    await other.execute(
                        update(StockDataAdmission)
                        .where(StockDataAdmission.product == "actions")
                        .values(collection_allowed=False)
                    )
                elif race != "expired":
                    await other.execute(
                        update(StockActionState)
                        .where(StockActionState.coin_id == cid)
                        .values(
                            **(
                                {"epoch": StockActionState.epoch + 1}
                                if race == "epoch"
                                else {"covered_until": monitor[2]}
                            )
                        )
                    )
        return await original(db, statement, *args, **kwargs)

    async def checked_clock(db):
        value = await clock(db)
        return (
            value + timedelta(days=1)
            if race == "expired" and raced and "stock_gate" not in db.info
            else value
        )

    monkeypatch.setattr(AsyncSession, "execute", execute)
    monkeypatch.setattr(stock_actions, "_clock", checked_clock)
    with respx.mock() as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
    assert raced
    assert all(
        r.health == "reconciling" and r.valid_until is None for r in await states(monitor[0])
    )


@pytest.mark.parametrize("overflow", ["known", "entitlements"])
async def test_event_capacity_refuses_without_silent_truncation(monitor, redis_client, overflow):
    from uuid import uuid4

    factory = monitor[0]
    async with factory.begin() as db:
        cid = (await db.execute(select(StockInstrument.coin_id).limit(1))).scalar_one()
        for _ in range(1001):
            event = StockActionEvent(
                coin_id=cid, economic_key=str(uuid4()), first_observed_at=datetime.now(UTC)
            )
            db.add(event)
            await db.flush()
            source = StockActionSource(
                event_id=event.id,
                provider="alpaca" if overflow == "known" else "synthetic",
                product="actions",
                provider_event_id=str(uuid4()),
            )
            db.add(source)
            await db.flush()
            if overflow == "entitlements":
                revision = StockActionRevision(
                    event_id=event.id,
                    source_id=source.id,
                    ordinal=1,
                    fingerprint="a" * 64,
                    mutation_kind="snapshot",
                    observed_at=datetime.now(UTC),
                    admission_generation=4,
                    normalized_terms={"event_type": "cash_dividend"},
                    classification="supported_dividend",
                    reason="synthetic capacity proof",
                )
                db.add(revision)
                await db.flush()
                event.current_revision_id = revision.id
    with respx.mock(assert_all_called=False) as router:
        routes(router)
        async with httpx.AsyncClient(trust_env=False) as http:
            assert (await cycle(monitor, redis_client, http)).status == "source_error"
