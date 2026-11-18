"""Funded management HTTP uses real sessions, current admission and restricted SQL."""

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.security import create_access_token
from app.db.portfolio_bootstrap import GRANTS_SQL
from app.main import create_app
from tests import test_portfolio_management_authority as authority_harness
from tests.test_portfolio_management_authority import close, create, owner

authority = authority_harness.authority


@pytest_asyncio.fixture
async def management_api(authority, engine, settings):
    restricted, migrator = authority
    async with engine.begin() as conn:
        raw = await conn.get_raw_connection()
        await raw.driver_connection.execute(GRANTS_SQL)
    config = settings.model_copy(
        update={
            "database_url": restricted.url.render_as_string(hide_password=False),
            "price_source": "fake",
            "email_backend": "console",
        }
    )
    app = create_app(config)
    clients, owners = [], []
    async with app.router.lifespan_context(app):
        for _ in range(2):
            uid = await owner(migrator)
            async with migrator.begin() as conn:
                sid = (
                    await conn.execute(
                        text("INSERT INTO auth_sessions(user_id) VALUES (:u) RETURNING id"),
                        {"u": uid},
                    )
                ).scalar_one()
            client = httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="https://test"
            )
            client.cookies.set("bj_access", create_access_token(uid, sid, config.jwt_secret))
            client.cookies.set("bj_csrf", "test-csrf")
            clients.append(client)
            owners.append(uid)
        try:
            yield SimpleNamespace(
                client=clients[0],
                other=clients[1],
                uid=owners[0],
                other_uid=owners[1],
                app=app,
                migrator=migrator,
                restricted=restricted,
            )
        finally:
            for client in clients:
                await client.aclose()


async def post(api, name="Strategy", *, key=None, description="", client=None):
    return await (client or api.client).post(
        "/api/v2/portfolios",
        json={"name": name, "description": description},
        headers={"X-CSRF-Token": "test-csrf", "Idempotency-Key": str(key or uuid4())},
    )


async def patch(api, root, payload, *, client=None):
    return await (client or api.client).patch(
        f"/api/v2/portfolios/{root}", json=payload, headers={"X-CSRF-Token": "test-csrf"}
    )


async def counts(api):
    async with api.migrator.connect() as conn:
        return (
            await conn.execute(
                text(
                    "SELECT (SELECT count(*) FROM accounts), "
                    "(SELECT count(*) FROM portfolio_creations), "
                    "(SELECT coalesce(sum(amount),0) FROM portfolio_creations)"
                )
            )
        ).one()


async def test_actual_app_lost_response_replay_normalization_rename_and_conflict(management_api):
    api = management_api
    key = uuid4()
    first = await post(api, "\u2003e\u0301 strategy\u3000", key=key, description="line\r\nnext")
    assert first.status_code == 201, first.text
    root = first.json()["id"]
    assert first.json() == {"id": root, "name": "é strategy", "description": "line\nnext"}
    assert root.isdecimal() and first.headers["cache-control"] == "no-store"
    # Discard the response as a browser would after response loss; use original intent.
    assert (await post(api, "é strategy", key=key, description="line\nnext")).status_code == 200
    assert (
        await patch(api, root, {"name": "Renamed", "description": "changed"})
    ).status_code == 200
    replay = await post(api, "é strategy", key=key, description="line\nnext")
    assert replay.status_code == 200 and replay.json() == {
        "id": root,
        "name": "Renamed",
        "description": "changed",
    }
    conflict = await post(api, "Renamed", key=key, description="changed")
    assert (
        conflict.status_code == 409 and conflict.json()["detail"]["code"] == "creation_key_conflict"
    )
    assert await counts(api) == (1, 1, 10000)
    async with api.migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT canonical_payload,amount FROM portfolio_creations"))
        ).one() == ({"name": "é strategy", "description": "line\nnext"}, 10000)


async def test_same_key_name_and_last_slot_races_replay_before_mutable_cap(management_api):
    api = management_api
    key = uuid4()
    results = await asyncio.gather(*(post(api, "Original", key=key) for _ in range(4)))
    assert sorted(r.status_code for r in results) == [200, 200, 200, 201]
    root = results[0].json()["id"]
    for n in range(8):
        assert (await post(api, f"Saved {n}")).status_code == 201
    results = await asyncio.gather(*(post(api, f"Final {n}") for n in range(3)))
    assert sorted(r.status_code for r in results) == [201, 409, 409]
    assert all(
        r.json()["detail"]["code"] == "portfolio_limit" for r in results if r.status_code == 409
    )
    assert (await patch(api, root, {"name": "Updated"})).status_code == 200
    assert (await post(api, "Original", key=key)).status_code == 200
    await close(api.migrator, int(root))
    reused = await post(api, "Original")
    assert reused.status_code == 201 and reused.json()["id"] != root
    unavailable = await post(api, "Original", key=key)
    assert unavailable.status_code == 404 and unavailable.json()["detail"] == {
        "code": "portfolio_unavailable"
    }
    assert await counts(api) == (11, 11, 110000)


async def test_name_uniqueness_uses_sql_unicode_casefold_and_owner_scope(management_api):
    api = management_api
    for a, b in [("Straße", "STRASSE"), ("Σ", "ς"), ("e\u0301", "é")]:
        results = await asyncio.gather(post(api, a), post(api, b))
        assert sorted(r.status_code for r in results) == [201, 409]
        assert (
            next(r for r in results if r.status_code == 409).json()["detail"]["code"]
            == "name_taken"
        )
        assert (await post(api, b, client=api.other)).status_code == 201
    assert (await post(api, "😀" * 60)).status_code == 201
    before = await counts(api)
    assert (await post(api, "😀" * 61)).status_code == 422
    assert await counts(api) == before


async def test_daily_sql_quota_is_durable_replay_exempt_and_rejections_leave_no_rows(
    management_api,
):
    api = management_api
    key = uuid4()
    first = await post(api, "Original", key=key)
    assert first.status_code == 201
    for n in range(99):
        row = await create(api.restricted, api.uid, f"Retired {n}")
        await close(api.migrator, row.portfolio_id)
    before = await counts(api)
    rejected = await post(api, "Beyond quota")
    assert rejected.status_code == 429 and rejected.json()["detail"]["code"] == "creation_quota"
    assert 0 < int(rejected.headers["Retry-After"]) <= 86400
    assert (await post(api, "Original", key=key)).status_code == 200
    assert await counts(api) == before == (100, 100, 1000000)


async def test_auth_csrf_precede_untrusted_body_and_no_failed_intent_growth(management_api):
    api = management_api
    url = "/api/v2/portfolios"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api.app), base_url="https://test"
    ) as guest:
        refused = await guest.post(url, content=b"{" + b" " * 9000)
        assert refused.status_code == 401 and refused.headers["cache-control"] == "no-store"
    csrf = await api.client.post(url, content=b"{" + b" " * 9000)
    assert csrf.status_code == 403 and csrf.headers["vary"] == "Cookie, Authorization"
    for key in (None, "x" * 10000, str(uuid4()).upper(), "00000000-0000-0000-0000-000000000000"):
        headers = {"X-CSRF-Token": "test-csrf"}
        if key is not None:
            headers["Idempotency-Key"] = key
        assert (
            await api.client.post(url, json={"name": "Good"}, headers=headers)
        ).status_code == 422
    for payload in (
        {"name": None},
        {"name": "\tBad"},
        {"name": "Bad\x85"},
        {"name": "ok", "cash": "10000"},
        {"name": "ok", "description": None},
    ):
        r = await api.client.post(
            url,
            json=payload,
            headers={"X-CSRF-Token": "test-csrf", "Idempotency-Key": str(uuid4())},
        )
        assert r.status_code == 422 and r.headers["cache-control"] == "no-store"

    async def oversized():
        yield b" " * 5000
        yield b" " * 4000

    r = await api.client.post(
        url,
        content=oversized(),
        headers={
            "X-CSRF-Token": "test-csrf",
            "Idempotency-Key": str(uuid4()),
            "content-type": "application/json",
            "content-length": "1",
        },
    )
    assert r.status_code == 413
    r = await api.client.post(
        url,
        content=b"{}",
        headers={
            "X-CSRF-Token": "test-csrf",
            "Idempotency-Key": str(uuid4()),
            "content-type": "text/plain",
        },
    )
    assert r.status_code == 415
    assert await counts(api) == (0, 0, 0)


async def test_attempt_limit_counts_replays_and_invalid_keys_without_journal_growth(management_api):
    api = management_api
    api.app.state.settings = api.app.state.settings.model_copy(
        update={"portfolio_create_owner_limit": 2}
    )
    key = uuid4()
    assert (await post(api, key=key)).status_code == 201
    assert (await post(api, key=key)).status_code == 200
    limited = await post(api, "New")
    assert limited.status_code == 429 and int(limited.headers["Retry-After"]) > 0
    assert await counts(api) == (1, 1, 10000)


async def test_actual_committed_response_failure_is_private_and_original_retry_recovers(
    management_api, monkeypatch
):
    from app.api.v2 import portfolios

    api = management_api
    key = uuid4()
    original = portfolios.create_portfolio

    async def lost_response(*args, **kwargs):
        await original(*args, **kwargs)
        raise RuntimeError("private credentials and committed result lost")

    with monkeypatch.context() as scoped:
        scoped.setattr(portfolios, "create_portfolio", lost_response)
        failed = await post(api, key=key)
    assert failed.status_code == 500 and "original" in failed.text
    assert failed.headers["cache-control"] == "no-store"
    assert "credentials" not in failed.text
    assert await counts(api) == (1, 1, 10000)
    replay = await post(api, key=key)
    assert replay.status_code == 200
    assert await counts(api) == (1, 1, 10000)


async def test_real_owner_lock_timeout_rolls_back_and_retry_does_not_regrant(management_api):
    api = management_api
    key = uuid4()
    async with api.migrator.begin() as conn:
        await conn.execute(text("SELECT id FROM users WHERE id=:u FOR UPDATE"), {"u": api.uid})
        refused = await asyncio.wait_for(post(api, key=key), timeout=6)
        assert refused.status_code == 503 and refused.headers["Retry-After"] == "5"
        assert refused.json()["detail"] == {"code": "service_unavailable"}
        assert await counts(api) == (0, 0, 0)
    assert (await post(api, key=key)).status_code == 201


async def test_redis_failure_and_revoked_session_fail_closed_before_any_grant(
    management_api, monkeypatch
):
    from redis.exceptions import ConnectionError as RedisConnectionError

    from app.api.v2 import portfolio_management

    api = management_api

    async def unavailable(*args, **kwargs):
        raise RedisConnectionError("private redis credential")

    with monkeypatch.context() as scoped:
        scoped.setattr(portfolio_management, "enforce", unavailable)
        response = await post(api)
    assert response.status_code == 503 and response.headers["Retry-After"] == "5"
    assert response.headers["cache-control"] == "no-store" and "credential" not in response.text
    async with api.migrator.begin() as conn:
        await conn.execute(
            text("UPDATE auth_sessions SET revoked_at=clock_timestamp() WHERE user_id=:u"),
            {"u": api.uid},
        )
    response = await post(api)
    assert response.status_code == 401
    assert await counts(api) == (0, 0, 0)


async def test_services_roll_back_known_and_unknown_actual_sql_failures(management_api):
    from app.models.user import User
    from app.schemas.portfolios import PortfolioCreate, PortfolioPatch
    from app.services.portfolios import create_portfolio, update_portfolio_metadata

    api = management_api
    user = User(id=api.uid, email="owned-service@example.test")
    sessions = async_sessionmaker(api.restricted, expire_on_commit=False)
    root = (await post(api)).json()["id"]
    before = await counts(api)
    async with sessions() as db:
        # Deliberately bypass the transport model to prove SQL is authoritative
        # and rollback permits a later valid service transaction.
        with pytest.raises(HTTPException) as invalid:
            await create_portfolio(
                db, user, uuid4(), PortfolioCreate.model_construct(name="\tBad", description="")
            )
        assert invalid.value.status_code == 422 and not db.in_transaction()
        with pytest.raises(HTTPException) as invalid:
            await update_portfolio_metadata(
                db, user, int(root), PortfolioPatch.model_construct(description="\x1f")
            )
        assert invalid.value.status_code == 422 and not db.in_transaction()

    # Exercise the unrecognized-database-error branch using actual42501, never
    # a fake database. This direct service test intentionally has no API/schema
    # admission claim while its owned test-only EXECUTE grant is revoked.
    for signature, operation in [
        (
            "create_portfolio(bigint,uuid,text,text)",
            lambda db: create_portfolio(db, user, uuid4(), PortfolioCreate(name="New")),
        ),
        (
            "update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean)",
            lambda db: update_portfolio_metadata(
                db, user, int(root), PortfolioPatch(description="changed")
            ),
        ),
    ]:
        async with api.migrator.begin() as conn:
            await conn.execute(
                text(f"REVOKE EXECUTE ON FUNCTION public.{signature} FROM birja_app")
            )  # noqa: S608 - fixed signatures above
        try:
            async with sessions() as db:
                with pytest.raises(DBAPIError) as denied:
                    await operation(db)
                assert denied.value.orig.sqlstate == "42501" and not db.in_transaction()
        finally:
            async with api.migrator.begin() as conn:
                await conn.execute(
                    text(f"GRANT EXECUTE ON FUNCTION public.{signature} TO birja_app")
                )  # noqa: S608
    assert await counts(api) == before


async def test_existing_statement_still_uses_owned_root_and_stored_fixed_baseline(management_api):
    api = management_api
    root = (await post(api)).json()["id"]
    statement = await api.client.get(f"/api/v2/portfolios/{root}")
    assert statement.status_code == 200, statement.text
    assert statement.json()["portfolio_id"] == root
    assert statement.json()["cash"] == statement.json()["starting_cash"] == "10000.00"
    assert "description" not in statement.json()
    denied = await api.other.get(f"/api/v2/portfolios/{root}")
    assert denied.status_code == 404 and denied.headers["cache-control"] == "no-store"


async def test_initial_winner_rollback_unblocks_explicit_http_creation(management_api):
    """Uncommitted onboarding must neither latch nor supplement a later root."""
    api = management_api
    async with api.restricted.connect() as conn:
        tx = await conn.begin()
        initial = (
            await conn.execute(text("SELECT public.initialize_portfolio(:u)"), {"u": api.uid})
        ).scalar_one()
        pending = asyncio.create_task(post(api, "Explicit after rollback"))
        # The second independent connection must wait on the owner lock.
        await asyncio.sleep(0.1)
        assert not pending.done()
        await tx.rollback()
        created = await asyncio.wait_for(pending, 6)
    assert created.status_code == 201, created.text
    assert created.json()["id"] != str(initial)
    async with api.migrator.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*),sum(cash),sum(starting_cash) FROM accounts"))
        ).one() == (1, 10000, 10000)
        assert (
            await conn.execute(text("SELECT count(*) FROM portfolio_initializations"))
        ).scalar_one() == 0
    assert await counts(api) == (1, 1, 10000)
