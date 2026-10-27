import asyncio
import re
import uuid

import pytest
from pydantic import SecretStr
from redis.asyncio import Redis

import app.services.otp as otp_module
from app.services.otp import OtpStore


def _email() -> str:
    return f"otp-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def store(redis_client: Redis) -> OtpStore:
    return OtpStore(redis_client, SecretStr("unit-test-otp-secret-0123456789-abcdef"))


async def test_issue_stores_only_hmac_with_ttl(store: OtpStore, redis_client: Redis) -> None:
    email = _email()
    code = await store.issue(email)

    assert re.fullmatch(r"\d{6}", code)
    key = "sim:otp:" + store.email_key(email)
    data = await redis_client.hgetall(key)  # type: ignore[misc]
    assert set(data) == {"mac", "attempts"}
    assert data["attempts"] == "0"
    assert code not in data["mac"]
    assert code not in key
    assert 0 < await redis_client.ttl(key) <= 600


async def test_right_code_works_once(store: OtpStore) -> None:
    email = _email()
    code = await store.issue(email)
    assert await store.verify(email, code) is True
    assert await store.verify(email, code) is False


async def test_four_wrong_then_right_succeeds(store: OtpStore) -> None:
    email = _email()
    code = await store.issue(email)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(4):
        assert await store.verify(email, wrong) is False
    assert await store.verify(email, code) is True


async def test_five_wrong_kills_code(store: OtpStore, redis_client: Redis) -> None:
    email = _email()
    code = await store.issue(email)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert await store.verify(email, wrong) is False
    assert await redis_client.exists("sim:otp:" + store.email_key(email)) == 0
    assert await store.verify(email, code) is False


async def test_kill_spares_code_issued_after_the_failed_check(
    store: OtpStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = _email()
    old = await store.issue(email)
    wrong = "000000" if old != "000000" else "111111"
    for _ in range(4):
        assert await store.verify(email, wrong) is False

    fresh: list[str] = []
    real_attempt = store._attempt

    async def attempt_then_reissue(**kwargs: object) -> object:
        res = await real_attempt(**kwargs)
        # "Send a new code" lands between the 5th wrong check and the kill.
        code = await store.issue(email)
        while code == old:
            code = await store.issue(email)
        fresh.append(code)
        return res

    monkeypatch.setattr(store, "_attempt", attempt_then_reissue)
    assert await store.verify(email, wrong) is False
    monkeypatch.undo()
    assert await store.verify(email, fresh[0]) is True


async def test_reissue_invalidates_old_code(store: OtpStore) -> None:
    email = _email()
    first = await store.issue(email)
    second = await store.issue(email)
    if first != second:
        assert await store.verify(email, first) is False
    assert await store.verify(email, second) is True


async def test_unknown_or_deleted_key_fails(store: OtpStore, redis_client: Redis) -> None:
    email = _email()
    assert await store.verify(email, "123456") is False
    code = await store.issue(email)
    await redis_client.delete("sim:otp:" + store.email_key(email))
    assert await store.verify(email, code) is False


async def test_concurrent_correct_verifies_only_one_wins(store: OtpStore) -> None:
    email = _email()
    code = await store.issue(email)
    results = await asyncio.gather(*(store.verify(email, code) for _ in range(5)))
    assert results.count(True) == 1


async def test_concurrent_wrong_guesses_capped(store: OtpStore, redis_client: Redis) -> None:
    email = _email()
    code = await store.issue(email)
    wrong = "000000" if code != "000000" else "111111"
    key = "sim:otp:" + store.email_key(email)
    results = await asyncio.gather(*(store.verify(email, wrong) for _ in range(10)))
    assert not any(results)
    assert await redis_client.exists(key) == 0


def test_email_key_is_keyed_hmac(store: OtpStore) -> None:
    a, b = store.email_key("a@example.com"), store.email_key("b@example.com")
    assert a == store.email_key("a@example.com")
    assert a != b
    assert re.fullmatch(r"[0-9a-f]{64}", a)
    other = OtpStore(store._redis, SecretStr("another-secret-0123456789-abcdefghijkl"))
    assert other.email_key("a@example.com") != a


async def test_uses_compare_digest(store: OtpStore, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str]] = []
    real = otp_module.hmac.compare_digest

    def spy(a: str, b: str) -> bool:
        calls.append((a, b))
        return real(a, b)

    monkeypatch.setattr(otp_module.hmac, "compare_digest", spy)
    email = _email()
    code = await store.issue(email)
    assert await store.verify(email, code) is True
    assert len(calls) == 1
