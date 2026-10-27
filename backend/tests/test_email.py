import logging

import httpx
import pytest
import respx
from pydantic import SecretStr

from app.core.config import Settings
from app.main import create_app
from app.services.email import (
    RESEND_URL,
    ConsoleSender,
    ResendSender,
    build_email_sender,
)

KEY = "dummy-key-not-real"
FROM = "YokaiExchange <login@example.com>"
TO = "friend.user@example.org"
CODE = "483920"


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    delays: list[float] = []

    async def fake_sleep(d: float) -> None:
        delays.append(d)

    monkeypatch.setattr("app.services.email.asyncio.sleep", fake_sleep)
    return delays


def _assert_clean(caplog: pytest.LogCaptureFixture) -> None:
    for rec in caplog.records:
        msg = rec.getMessage()
        assert CODE not in msg
        assert KEY not in msg
        assert TO not in msg


async def _send(caplog: pytest.LogCaptureFixture, router: respx.MockRouter) -> None:
    caplog.set_level(logging.DEBUG)
    async with httpx.AsyncClient() as http:
        await ResendSender(http, SecretStr(KEY), FROM).send_code(TO, CODE)


async def test_success_posts_expected_request(caplog: pytest.LogCaptureFixture) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        route = router.post(RESEND_URL).respond(200, json={"id": "x"})
        await _send(caplog, router)
    assert route.call_count == 1
    req = route.calls[0].request
    assert req.headers["Authorization"] == f"Bearer {KEY}"
    assert req.headers["Idempotency-Key"]
    import json

    body = json.loads(req.content)
    assert body["from"] == FROM
    assert body["to"] == [TO]
    assert body["subject"] == "Your YokaiExchange sign-in code"
    assert CODE in body["text"]
    assert "10 minutes" in body["text"]
    _assert_clean(caplog)


async def test_retries_5xx_with_same_idempotency_key(
    caplog: pytest.LogCaptureFixture, no_sleep: list[float]
) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        route = router.post(RESEND_URL).mock(
            side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200)]
        )
        await _send(caplog, router)
    assert route.call_count == 3
    keys = {c.request.headers["Idempotency-Key"] for c in route.calls}
    assert len(keys) == 1
    assert len(no_sleep) == 2
    assert no_sleep[1] >= 2  # exponential
    _assert_clean(caplog)


async def test_429_exhausts_retries_and_logs_status_only(
    caplog: pytest.LogCaptureFixture, no_sleep: list[float]
) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        route = router.post(RESEND_URL).respond(429, headers={"retry-after": "4"})
        await _send(caplog, router)
    assert route.call_count == 3
    assert all(d >= 4 for d in no_sleep)
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert [r.getMessage() for r in errors] == ["email send failed: status=429"]
    _assert_clean(caplog)


async def test_retry_after_is_capped_and_garbage_ignored(no_sleep: list[float]) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        router.post(RESEND_URL).mock(
            side_effect=[
                httpx.Response(429, headers={"retry-after": "9999"}),
                httpx.Response(429, headers={"retry-after": "soon"}),
                httpx.Response(200),
            ]
        )
        async with httpx.AsyncClient() as http:
            await ResendSender(http, SecretStr(KEY), FROM).send_code(TO, CODE)
    assert 5 <= no_sleep[0] < 6  # max(backoff 1..2, cap 5)
    assert 2 <= no_sleep[1] < 3


async def test_4xx_is_not_retried(caplog: pytest.LogCaptureFixture) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        route = router.post(RESEND_URL).respond(422, json={"message": TO})
        await _send(caplog, router)
    assert route.call_count == 1
    assert "email send failed: status=422" in [r.getMessage() for r in caplog.records]
    _assert_clean(caplog)


async def test_network_errors_are_retried(caplog: pytest.LogCaptureFixture) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        route = router.post(RESEND_URL).mock(
            side_effect=[
                httpx.ConnectError("boom"),
                httpx.ConnectError("boom"),
                httpx.Response(200),
            ]
        )
        await _send(caplog, router)
    assert route.call_count == 3
    _assert_clean(caplog)


async def test_persistent_network_error_logs_network(caplog: pytest.LogCaptureFixture) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        router.post(RESEND_URL).mock(side_effect=httpx.ConnectError("boom"))
        await _send(caplog, router)
    assert "email send failed: status=network" in [r.getMessage() for r in caplog.records]
    _assert_clean(caplog)


async def test_console_sender_still_logs_code(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    await ConsoleSender().send_code(TO, CODE)
    assert f"DEV EMAIL to={TO} code={CODE}" in caplog.text


def _settings(**kw: object) -> Settings:
    args: dict[str, object] = {
        "database_url": "postgresql+asyncpg://u:pw@h/db",
        "redis_url": "redis://:pw@127.0.0.1:1/0",
        "otp_hmac_secret": "a" * 40,
        "jwt_secret": "b" * 40,
        **kw,
    }
    return Settings(**args)  # type: ignore[arg-type]


async def test_build_email_sender_selects_backend() -> None:
    async with httpx.AsyncClient() as http:
        assert isinstance(build_email_sender(_settings(), http), ConsoleSender)
        resend = _settings(email_backend="resend", resend_api_key=KEY, email_from=FROM)
        assert isinstance(build_email_sender(resend, http), ResendSender)


async def test_lifespan_wires_and_closes_http_client() -> None:
    settings = _settings(email_backend="resend", resend_api_key=KEY, email_from=FROM)
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        assert isinstance(app.state.email_sender, ResendSender)
        assert not app.state.http.is_closed
    assert app.state.http.is_closed
