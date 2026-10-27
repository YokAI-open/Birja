import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI
from redis.asyncio import Redis

from app.core.config import Settings
from app.main import create_app
from app.services.ratelimit import RateLimited, enforce, hit
from tests.helpers import OutboxSender, csrf_headers, request_and_get_code, unique_email

REQ = "/api/v1/auth/request-code"
VER = "/api/v1/auth/verify-code"


def _key() -> str:
    return f"sim:rl:test:{uuid.uuid4().hex}"


# ---- unit: limiter -------------------------------------------------------------


async def test_hit_allows_up_to_limit_then_denies(redis_client: Redis) -> None:
    key = _key()
    for _ in range(3):
        allowed, _ = await hit(redis_client, key, 3, 60)
        assert allowed
    allowed, retry_after = await hit(redis_client, key, 3, 60)
    assert not allowed
    assert 1 <= retry_after <= 60


async def test_counter_has_ttl_and_later_hits_do_not_extend_it(redis_client: Redis) -> None:
    key = _key()
    await hit(redis_client, key, 5, 100)
    await redis_client.expire(key, 40)
    await hit(redis_client, key, 5, 100)  # EXPIRE NX must leave the shorter TTL alone
    ttl = await redis_client.ttl(key)
    assert 0 < ttl <= 40


async def test_window_expiry_resets_the_counter(redis_client: Redis) -> None:
    key = _key()
    assert (await hit(redis_client, key, 1, 1))[0]
    assert not (await hit(redis_client, key, 1, 1))[0]
    await asyncio.sleep(1.2)
    assert (await hit(redis_client, key, 1, 1))[0]


async def test_enforce_raises_with_retry_after_and_returns_none_on_allow(
    redis_client: Redis,
) -> None:
    key = _key()
    assert await enforce(redis_client, key, 1, 60) is None
    with pytest.raises(RateLimited) as exc_info:
        await enforce(redis_client, key, 1, 60)
    assert 1 <= exc_info.value.retry_after <= 60


# ---- API ----------------------------------------------------------------------


@asynccontextmanager
async def _custom_app(**limits: int) -> AsyncIterator[tuple[FastAPI, OutboxSender]]:
    settings = Settings().model_copy(update=limits)
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        outbox = OutboxSender()
        app.state.email_sender = outbox
        yield app, outbox


def _client(app: FastAPI, ip: str = "127.0.0.1") -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app, client=(ip, 1234)), base_url="https://test"
    )


async def _post(client: httpx.AsyncClient, path: str, body: dict[str, str]) -> httpx.Response:
    return await client.post(path, json=body, headers=await csrf_headers(client))


async def test_sixth_request_for_one_email_is_429_and_sends_nothing(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    email = unique_email()
    for _ in range(5):
        assert (await _post(auth_client, REQ, {"email": email})).status_code == 202
    resp = await _post(auth_client, REQ, {"email": email})
    assert resp.status_code == 429
    assert resp.json() == {
        "detail": {"code": "rate_limited", "message": "Too many requests. Try again later."}
    }
    assert 0 < int(resp.headers["Retry-After"]) <= 600
    assert len([m for m in outbox.messages if m[0] == email]) == 5
    # Another email from the same IP is unaffected.
    assert (await _post(auth_client, REQ, {"email": unique_email()})).status_code == 202


async def test_request_limit_is_per_ip() -> None:
    async with _custom_app() as (app, _):  # noqa: SIM117
        async with _client(app, "203.0.113.9") as a, _client(app, "198.51.100.7") as b:
            for _ in range(20):
                assert (await _post(a, REQ, {"email": unique_email()})).status_code == 202
            assert (await _post(a, REQ, {"email": unique_email()})).status_code == 429
            assert (await _post(b, REQ, {"email": unique_email()})).status_code == 202


async def test_verify_limit_is_per_email(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    email = unique_email()
    await request_and_get_code(auth_client, outbox, email)
    for _ in range(10):
        resp = await _post(auth_client, VER, {"email": email, "code": "000000"})
        assert resp.status_code == 400
    fresh = await request_and_get_code(auth_client, outbox, email)
    resp = await _post(auth_client, VER, {"email": email, "code": fresh})
    assert resp.status_code == 429
    assert int(resp.headers["Retry-After"]) > 0


async def test_verify_limit_is_per_ip() -> None:
    async with _custom_app(rl_verify_ip_limit=2) as (app, _):  # noqa: SIM117
        async with _client(app, "203.0.113.9") as a, _client(app, "198.51.100.7") as b:
            for _ in range(2):
                resp = await _post(a, VER, {"email": unique_email(), "code": "000000"})
                assert resp.status_code == 400
            resp = await _post(a, VER, {"email": unique_email(), "code": "000000"})
            assert resp.status_code == 429
            resp = await _post(b, VER, {"email": unique_email(), "code": "000000"})
            assert resp.status_code == 400


async def test_global_send_cap() -> None:
    async with _custom_app(rl_send_global_limit=2) as (app, outbox):
        async with _client(app) as c:
            assert (await _post(c, REQ, {"email": unique_email()})).status_code == 202
            assert (await _post(c, REQ, {"email": unique_email()})).status_code == 202
            assert (await _post(c, REQ, {"email": unique_email()})).status_code == 429
        assert len(outbox.messages) == 2


async def test_every_rate_limit_key_has_a_ttl(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, redis_client: Redis
) -> None:
    email = unique_email()
    await request_and_get_code(auth_client, outbox, email)
    await _post(auth_client, VER, {"email": email, "code": "000000"})
    keys = [k async for k in redis_client.scan_iter(match="sim:rl:*")]
    assert len(keys) >= 5
    for key in keys:
        assert await redis_client.ttl(key) > 0
        assert email not in key


async def test_429_is_identical_for_known_and_unknown_emails(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    from tests.helpers import sign_in

    known, unknown = unique_email("known"), unique_email("unknown")
    await sign_in(auth_client, outbox, known)  # creates the account (1 request used)
    seen = []
    for email in (known, unknown):
        for _ in range(5):
            await _post(auth_client, REQ, {"email": email})
        resp = await _post(auth_client, REQ, {"email": email})
        seen.append((resp.status_code, resp.json(), sorted(resp.headers.keys())))
    assert seen[0][0] == seen[1][0] == 429
    assert seen[0][1] == seen[1][1]
    assert seen[0][2] == seen[1][2]


async def test_forwarded_for_header_does_not_change_the_ip_bucket(
    auth_client: httpx.AsyncClient, redis_client: Redis
) -> None:
    for xff in ("1.2.3.4", "5.6.7.8"):
        headers = await csrf_headers(auth_client)
        headers["X-Forwarded-For"] = xff
        resp = await auth_client.post(REQ, json={"email": unique_email()}, headers=headers)
        assert resp.status_code == 202
    keys = [k async for k in redis_client.scan_iter(match="sim:rl:req:ip:*")]
    assert keys == ["sim:rl:req:ip:127.0.0.1"]
    assert await redis_client.get(keys[0]) == "2"


async def test_missing_client_address_uses_unknown_bucket(redis_client: Redis) -> None:
    async with _custom_app() as (app, _):  # noqa: SIM117
        transport = httpx.ASGITransport(app=app, client=None)  # type: ignore[arg-type]
        async with httpx.AsyncClient(transport=transport, base_url="https://test") as c:
            assert (await _post(c, REQ, {"email": unique_email()})).status_code == 202
    assert await redis_client.get("sim:rl:req:ip:unknown") == "1"


def test_uvicorn_trusts_forwarded_headers_only_from_localhost_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import uvicorn

    monkeypatch.delenv("FORWARDED_ALLOW_IPS", raising=False)
    config = uvicorn.Config(app="app.main:create_app", factory=True)
    assert config.proxy_headers is True
    # Loopback only (this uvicorn version also lists ::1); never a wildcard.
    allowed = config.forwarded_allow_ips
    hosts = allowed.split(",") if isinstance(allowed, str) else list(allowed or [])
    assert "127.0.0.1" in hosts
    assert set(hosts) <= {"127.0.0.1", "::1"}
