"""Public deletion preserves identity, original outcomes and independent grants."""

import asyncio
from uuid import uuid4

import httpx
import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy import text

from tests.helpers import OutboxSender, sign_in
from tests.test_portfolio_closure_api import CSRF, authority, closure_api, create, delete, intent

__all__ = ["authority", "closure_api"]


async def counts(api):
    async with api.migrator.connect() as conn:
        return (
            await conn.execute(
                text(
                    "SELECT (SELECT count(*) FROM accounts), "
                    "(SELECT count(*) FROM portfolio_creations),"
                    "(SELECT coalesce(sum(amount),0) FROM portfolio_creations),"
                    "(SELECT count(*) FROM portfolio_closure_intents)"
                )
            )
        ).one()


async def rename(api, root, name):
    response = await api.client.patch(
        f"/api/v2/portfolios/{root}", json={"name": name}, headers=CSRF
    )
    assert response.status_code == 200, response.text


async def test_committed_response_loss_replays_original_not_same_name_replacement(
    closure_api, monkeypatch
):
    from app.api.v2 import portfolios

    api = closure_api
    creation_key = uuid4()
    root = (await create(api, key=creation_key)).json()["id"]
    payload = intent()
    original = portfolios.close_owned_portfolio

    async def lose_ack(*args, **kwargs):
        await original(*args, **kwargs)
        raise RuntimeError("private postcommit response details")

    with monkeypatch.context() as scoped:
        scoped.setattr(portfolios, "close_owned_portfolio", lose_ack)
        lost = await delete(api, root, payload)
    assert lost.status_code == 500 and "original" in lost.text.lower()
    assert "private" not in lost.text and lost.headers["cache-control"] == "no-store"
    assert await counts(api) == (1, 1, 10000, 1)
    replacement = (await create(api)).json()["id"]
    assert replacement != root
    replay = await delete(api, root, payload)
    assert replay.status_code == 200 and replay.json() == {"portfolio_id": root, "state": "closed"}
    foreign = await delete(api, root, payload, client=api.other)
    assert foreign.status_code == 404 and foreign.json() == {
        "detail": {"code": "portfolio_unavailable"}
    }
    wrong = await delete(api, replacement, payload)
    assert wrong.status_code == 409 and wrong.json()["detail"]["code"] == "closure_intent_conflict"
    assert (await create(api, key=creation_key)).status_code == 404
    assert await counts(api) == (2, 2, 20000, 1)
    async with api.migrator.connect() as conn:
        assert (
            await conn.execute(
                text("SELECT cash,closed_at FROM accounts WHERE id=:p"), {"p": int(replacement)}
            )
        ).one() == (10000, None)


async def test_response_503_after_commit_remains_original_recoverable(closure_api, monkeypatch):
    from app.api.v2 import portfolios

    api = closure_api
    root = (await create(api)).json()["id"]
    payload = intent()
    original = portfolios.close_owned_portfolio

    async def lose_ack(*args, **kwargs):
        await original(*args, **kwargs)
        raise RedisConnectionError("private aftercommit transport detail")

    with monkeypatch.context() as scoped:
        scoped.setattr(portfolios, "close_owned_portfolio", lose_ack)
        response = await delete(api, root, payload)
    assert response.status_code == 503 and response.headers["Retry-After"] == "5"
    assert response.headers["cache-control"] == "no-store" and "private" not in response.text
    assert await counts(api) == (1, 1, 10000, 1)
    assert (await delete(api, root, payload)).status_code == 200
    assert await counts(api) == (1, 1, 10000, 1)


async def test_response_client_cancellation_after_commit_keeps_original_recovery(
    closure_api, monkeypatch
):
    from app.api.v2 import portfolios

    api = closure_api
    root = (await create(api)).json()["id"]
    payload = intent()
    original = portfolios.close_owned_portfolio
    committed, release = asyncio.Event(), asyncio.Event()

    async def wait_after_commit(*args, **kwargs):
        result = await original(*args, **kwargs)
        committed.set()
        await release.wait()
        return result

    with monkeypatch.context() as scoped:
        scoped.setattr(portfolios, "close_owned_portfolio", wait_after_commit)
        request = asyncio.create_task(delete(api, root, payload))
        try:
            await asyncio.wait_for(committed.wait(), timeout=10)
            request.cancel()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(request, timeout=5)
        finally:
            release.set()
            if not request.done():
                request.cancel()
                await asyncio.gather(request, return_exceptions=True)
    assert await counts(api) == (1, 1, 10000, 1)
    assert (await delete(api, root, payload)).status_code == 200
    assert await counts(api) == (1, 1, 10000, 1)


async def test_concurrent_duplicate_and_delayed_original_cannot_reverse_terminal_refusal(
    closure_api,
):
    api = closure_api
    root = (await create(api)).json()["id"]
    payload = intent()
    await rename(api, root, "Renamed")
    refusal = await delete(api, root, payload)
    assert (
        refusal.status_code == 409
        and refusal.json()["detail"]["code"] == "portfolio_confirmation_changed"
    )
    await rename(api, root, "Strategy")
    # These are actual later network invocations with the immutable original;
    # a mutable active GET/name restoration cannot turn their result to success.
    responses = await asyncio.gather(*(delete(api, root, payload) for _ in range(3)))
    assert all(
        r.status_code == 409 and r.json()["detail"]["code"] == "portfolio_confirmation_changed"
        for r in responses
    )
    assert await counts(api) == (1, 1, 10000, 1)
    fresh = intent()
    responses = await asyncio.gather(*(delete(api, root, fresh) for _ in range(3)))
    assert all(r.status_code == 200 and r.json()["portfolio_id"] == root for r in responses)
    assert await counts(api) == (1, 1, 10000, 2)


async def test_delete_last_stays_signed_in_through_otp_refresh_and_explicit_replacement(
    closure_api,
):
    api = closure_api
    creation_key = uuid4()
    root = (await create(api, key=creation_key)).json()["id"]
    assert (await delete(api, root)).status_code == 200
    async with api.migrator.connect() as conn:
        email = (
            await conn.execute(text("SELECT email FROM users WHERE id=:u"), {"u": api.uid})
        ).scalar_one()
    for _ in range(2):
        assert (await api.client.get("/api/v2/me")).status_code == 200
        assert (await api.client.get("/api/v2/portfolios")).json() == []
        assert (await api.client.get("/api/v2/portfolios/overview")).json() == []
        assert (await api.client.get(f"/api/v2/portfolios/{root}/metadata")).status_code == 404
    assert await counts(api) == (1, 1, 10000, 1)
    sender = OutboxSender()
    api.app.state.email_sender = sender
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api.app), base_url="https://test"
    ) as browser:
        result = await sign_in(browser, sender, email)
        assert result.json() == {"email": email}
        assert (await browser.get("/api/v2/portfolios")).json() == []
        refreshed = await browser.post(
            "/api/v1/auth/refresh", headers={"X-CSRF-Token": browser.cookies["bj_csrf"]}
        )
        assert refreshed.status_code == 204, refreshed.text
        assert (await browser.get("/api/v2/portfolios/overview")).json() == []
        assert (await browser.get("/api/v2/me")).json() == {"email": email}
        assert await counts(api) == (1, 1, 10000, 1)
        assert (await create(api, key=creation_key, client=browser)).status_code == 404
        made = await create(api, client=browser)
        assert made.status_code == 201 and made.json()["id"] != root
        assert await counts(api) == (2, 2, 20000, 1)
        assert (
            await browser.post(
                "/api/v1/auth/logout", headers={"X-CSRF-Token": browser.cookies["bj_csrf"]}
            )
        ).status_code == 204
        assert (await browser.get("/api/v2/me")).status_code == 401


async def test_closure_quota_refuses_new_but_owned_closed_ack_survives(closure_api):
    api = closure_api
    closed = (await create(api, "Closed")).json()["id"]
    active = (await create(api, "Active")).json()["id"]
    original = intent("Closed")
    assert (await delete(api, closed, original)).status_code == 200
    # Finite original outcomes produced by the actual authority, not fake rows
    # or a mocked quota. HTTP attempt limits are separately proven by API tests.
    async with api.restricted.begin() as conn:
        for _ in range(199):
            result = await conn.execute(
                text(
                    "SELECT outcome FROM close_portfolio(:u,:p,:k,'Wrong','freeze_at_closure_v1')"
                ),
                {"u": api.uid, "p": int(active), "k": uuid4()},
            )
            assert result.scalar_one() == "confirmation_changed"
    refused = await delete(api, active, intent("Active"))
    assert refused.status_code == 429 and refused.json()["detail"]["code"] == "closure_quota"
    assert 0 < int(refused.headers["Retry-After"]) <= 86400
    assert (await delete(api, closed, original)).status_code == 200
    assert (await delete(api, closed, intent("Another incoming review"))).status_code == 200
    assert await counts(api) == (2, 2, 20000, 200)
