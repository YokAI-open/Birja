import uuid

import httpx


class OutboxSender:
    def __init__(self) -> None:
        self.messages: list[tuple[str, str]] = []

    async def send_code(self, to: str, code: str) -> None:
        self.messages.append((to, code))


async def csrf_headers(client: httpx.AsyncClient) -> dict[str, str]:
    await client.get("/api/v1/auth/csrf")
    return {"X-CSRF-Token": client.cookies["yk_csrf"]}


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"
