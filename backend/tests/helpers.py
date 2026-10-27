import uuid

import httpx


class OutboxSender:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def send_code(self, to: str, code: str) -> None:
        self.messages.append((to, code))


async def csrf_headers(client: httpx.AsyncClient) -> dict[str, str]:
    await client.get("/api/v1/auth/csrf")
    return {"X-CSRF-Token": client.cookies["bj_csrf"]}


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


async def request_and_get_code(client: httpx.AsyncClient, outbox: OutboxSender, email: str) -> str:
    headers = await csrf_headers(client)
    resp = await client.post("/api/v1/auth/request-code", json={"email": email}, headers=headers)
    assert resp.status_code == 202
    return [code for to, code in outbox.messages if to == email][-1]


async def sign_in(client: httpx.AsyncClient, outbox: OutboxSender, email: str) -> httpx.Response:
    code = await request_and_get_code(client, outbox, email)
    headers = {"X-CSRF-Token": client.cookies["bj_csrf"]}
    resp = await client.post(
        "/api/v1/auth/verify-code", json={"email": email, "code": code}, headers=headers
    )
    assert resp.status_code == 200
    return resp
