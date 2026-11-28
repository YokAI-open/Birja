import asyncio
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from app.core.config import Settings
from tests.helpers import OutboxSender, csrf_headers, request_and_get_code, sign_in, unique_email


@pytest.fixture
def allowed_file(
    tmp_path: Path, running_app: FastAPI, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> Path:
    file = tmp_path / "allowed-emails.txt"
    monkeypatch.setattr(
        running_app.state,
        "settings",
        settings.model_copy(update={"auth_allowed_emails_file": str(file)}),
    )
    return file


def assert_registration_closed(response: httpx.Response) -> None:
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "registration_closed"
    assert response.headers["Cache-Control"] == "no-store"
    assert "set-cookie" not in response.headers


@pytest.mark.asyncio
async def test_file_controls_code_delivery_and_existing_sessions_without_restart(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, allowed_file: Path
) -> None:
    owner = unique_email("owner")
    newcomer = unique_email("new")
    await asyncio.to_thread(allowed_file.write_text, f"  {owner.upper()} \n\n", encoding="utf-8")
    await sign_in(auth_client, outbox, owner)
    assert (await auth_client.get("/api/v2/me")).status_code == 200
    assert (
        await auth_client.post("/api/v1/auth/refresh", headers=await csrf_headers(auth_client))
    ).status_code == 204

    replacement = allowed_file.with_suffix(".new")
    await asyncio.to_thread(replacement.write_text, f"{newcomer}\n", encoding="utf-8")
    await asyncio.to_thread(replacement.replace, allowed_file)
    assert (await auth_client.get("/api/v2/me")).status_code == 401

    headers = await csrf_headers(auth_client)
    blocked = await auth_client.post(
        "/api/v1/auth/request-code", json={"email": owner}, headers=headers
    )
    assert_registration_closed(blocked)
    never_registered = await auth_client.post(
        "/api/v1/auth/request-code", json={"email": unique_email()}, headers=headers
    )
    assert never_registered.status_code == blocked.status_code
    assert never_registered.json() == blocked.json()
    assert len(outbox.messages) == 1

    refresh = await auth_client.post("/api/v1/auth/refresh", headers=headers)
    assert refresh.status_code == 401
    assert "bj_refresh" not in auth_client.cookies
    await sign_in(auth_client, outbox, newcomer)


@pytest.mark.asyncio
async def test_removal_before_verification_denies_pending_code(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, allowed_file: Path
) -> None:
    email = unique_email()
    await asyncio.to_thread(allowed_file.write_text, email, encoding="utf-8")
    code = await request_and_get_code(auth_client, outbox, email)
    await asyncio.to_thread(allowed_file.unlink)
    headers = await csrf_headers(auth_client)
    request = {"email": email, "code": code}
    assert_registration_closed(
        await auth_client.post("/api/v2/auth/verify-code", json=request, headers=headers)
    )
    assert (await auth_client.get("/api/v2/me")).status_code == 401
    await asyncio.to_thread(allowed_file.write_text, email, encoding="utf-8")
    assert (
        await auth_client.post("/api/v2/auth/verify-code", json=request, headers=headers)
    ).status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_data", [b"", b"user@example.com\ninvalid", b"\xff", b" " * 16385])
async def test_invalid_file_closes_sign_in(
    auth_client: httpx.AsyncClient, outbox: OutboxSender, allowed_file: Path, bad_data: bytes
) -> None:
    await asyncio.to_thread(allowed_file.write_bytes, bad_data)
    assert_registration_closed(
        await auth_client.post(
            "/api/v1/auth/request-code",
            json={"email": "user@example.com"},
            headers=await csrf_headers(auth_client),
        )
    )
    assert outbox.messages == []
