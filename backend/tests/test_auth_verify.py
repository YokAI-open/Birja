import asyncio
from decimal import Decimal

import httpx
from redis.asyncio import Redis

from tests.helpers import OutboxSender, csrf_headers, request_and_get_code, unique_email

URL = "/api/v1/auth/verify-code"


async def _verify(client: httpx.AsyncClient, email: str, code: str) -> httpx.Response:
    return await client.post(
        URL, json={"email": email, "code": code}, headers=await csrf_headers(client)
    )


async def test_success_creates_account(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    email = unique_email("Mixed")
    code = await request_and_get_code(auth_client, outbox, email.lower())
    resp = await _verify(auth_client, email.upper(), code)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == email.lower()
    assert isinstance(body["cash_usd"], str)
    assert Decimal(body["cash_usd"]) == Decimal("10000.00")


async def test_reused_code_is_400(auth_client: httpx.AsyncClient, outbox: OutboxSender) -> None:
    email = unique_email()
    code = await request_and_get_code(auth_client, outbox, email)
    assert (await _verify(auth_client, email, code)).status_code == 200
    resp = await _verify(auth_client, email, code)
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "invalid_code"


async def test_all_failures_share_one_body(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, redis_client: Redis
) -> None:
    bodies = []
    # wrong
    e1 = unique_email()
    code = await request_and_get_code(auth_client, outbox, e1)
    wrong = "000000" if code != "000000" else "111111"
    bodies.append(await _verify(auth_client, e1, wrong))
    # reused
    e2 = unique_email()
    c2 = await request_and_get_code(auth_client, outbox, e2)
    await _verify(auth_client, e2, c2)
    bodies.append(await _verify(auth_client, e2, c2))
    # expired (key deleted)
    e3 = unique_email()
    c3 = await request_and_get_code(auth_client, outbox, e3)
    async for key in redis_client.scan_iter(match="sim:otp:*"):
        await redis_client.delete(key)
    bodies.append(await _verify(auth_client, e3, c3))
    # replaced
    e4 = unique_email()
    old = await request_and_get_code(auth_client, outbox, e4)
    new = await request_and_get_code(auth_client, outbox, e4)
    if old != new:
        bodies.append(await _verify(auth_client, e4, old))
    for r in bodies:
        assert r.status_code == 400
        assert r.json() == bodies[0].json()


async def test_five_wrong_then_right_is_400(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    email = unique_email()
    code = await request_and_get_code(auth_client, outbox, email)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert (await _verify(auth_client, email, wrong)).status_code == 400
    assert (await _verify(auth_client, email, code)).status_code == 400


async def test_concurrent_verify_one_wins(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    email = unique_email()
    code = await request_and_get_code(auth_client, outbox, email)
    headers = await csrf_headers(auth_client)

    async def go() -> int:
        r = await auth_client.post(URL, json={"email": email, "code": code}, headers=headers)
        return r.status_code

    statuses = sorted(await asyncio.gather(go(), go()))
    assert statuses == [200, 400]


async def test_bad_code_format_is_422(auth_client: httpx.AsyncClient) -> None:
    for bad in ("12345", "1234567", "abcdef"):
        assert (await _verify(auth_client, unique_email(), bad)).status_code == 422


async def test_missing_csrf_is_403(auth_client: httpx.AsyncClient) -> None:
    resp = await auth_client.post(URL, json={"email": unique_email(), "code": "123456"})
    assert resp.status_code == 403
