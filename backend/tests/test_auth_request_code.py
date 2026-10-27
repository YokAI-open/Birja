import logging
import re

import httpx
import pytest
from fastapi import FastAPI
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from app.services.email import ConsoleSender
from tests.helpers import OutboxSender, csrf_headers, unique_email

REQ = "/api/v1/auth/request-code"


async def test_identical_response_for_any_email(
    auth_client: httpx.AsyncClient, outbox: OutboxSender
) -> None:
    headers = await csrf_headers(auth_client)
    r1 = await auth_client.post(REQ, json={"email": unique_email("a")}, headers=headers)
    r2 = await auth_client.post(REQ, json={"email": unique_email("b")}, headers=headers)
    assert r1.status_code == r2.status_code == 202
    assert r1.json() == r2.json() == {"status": "code_sent"}
    assert len(outbox.messages) == 2


async def test_code_is_emailed_and_verifies(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, running_app: FastAPI
) -> None:
    headers = await csrf_headers(auth_client)
    email = unique_email()
    await auth_client.post(REQ, json={"email": email}, headers=headers)
    ((to, code),) = outbox.messages
    assert to == email
    assert re.fullmatch(r"\d{6}", code)
    assert await running_app.state.otp_store.verify(email, code) is True


async def test_email_is_normalized(
    auth_client: httpx.AsyncClient,
    outbox: OutboxSender,
    running_app: FastAPI,
    redis_client: Redis,
) -> None:
    headers = await csrf_headers(auth_client)
    raw = f" Foo.{unique_email('Bar').upper()} "
    norm = raw.strip().lower()
    r = await auth_client.post(REQ, json={"email": raw}, headers=headers)
    assert r.status_code == 202
    assert outbox.messages[0][0] == norm
    key = "sim:otp:" + running_app.state.otp_store.email_key(norm)
    assert await redis_client.exists(key) == 1


@pytest.mark.parametrize("email", ["not-an-email", "a" * 250 + "@example.com", 5])
async def test_invalid_email_is_422(auth_client: httpx.AsyncClient, email: object) -> None:
    headers = await csrf_headers(auth_client)
    r = await auth_client.post(REQ, json={"email": email}, headers=headers)
    assert r.status_code == 422


async def test_redis_down_gives_503(
    auth_client: httpx.AsyncClient, running_app: FastAPI, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def boom(email: str) -> str:
        raise RedisConnectionError("down")

    monkeypatch.setattr(running_app.state.otp_store, "issue", boom)
    headers = await csrf_headers(auth_client)
    r = await auth_client.post(REQ, json={"email": unique_email()}, headers=headers)
    assert r.status_code == 503
    assert r.headers["retry-after"] == "5"
    assert r.json()["detail"]["code"] == "service_unavailable"


async def test_console_sender_logs_one_line(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="app.services.email"):
        await ConsoleSender().send_code("a@example.com", "123456")
    records = [r for r in caplog.records if r.name == "app.services.email"]
    assert [r.getMessage() for r in records] == ["DEV EMAIL to=a@example.com code=123456"]
