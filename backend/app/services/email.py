import asyncio
import logging
import random
import secrets
from typing import Protocol

import httpx
from pydantic import SecretStr

from app.core.config import Settings

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
MAX_ATTEMPTS = 3
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})
MAX_RETRY_AFTER = 5.0


class EmailSender(Protocol):
    async def send_code(self, to: str, code: str) -> None: ...


class ConsoleSender:
    """Dev-only sender: prints the code to the log instead of sending email."""

    async def send_code(self, to: str, code: str) -> None:
        logger.info("DEV EMAIL to=%s code=%s", to, code)


def _retry_after(response: httpx.Response) -> float:
    try:
        return min(max(float(response.headers.get("retry-after", "0")), 0.0), MAX_RETRY_AFTER)
    except ValueError:
        return 0.0


class ResendSender:
    """Sends sign-in codes through the Resend HTTP API (plain httpx, no SDK).

    Never logs the code, the API key or the recipient address.
    """

    def __init__(self, client: httpx.AsyncClient, api_key: SecretStr, sender: str) -> None:
        self._client = client
        self._api_key = api_key
        self._sender = sender

    async def send_code(self, to: str, code: str) -> None:
        payload = {
            "from": self._sender,
            "to": [to],
            "subject": "Your YokaiExchange sign-in code",
            "text": f"Your sign-in code is {code}. It expires in 10 minutes.",
        }
        headers = {
            "Authorization": f"Bearer {self._api_key.get_secret_value()}",
            # One key per send, reused by retries, so a retry cannot double-send.
            "Idempotency-Key": secrets.token_urlsafe(16),
        }
        status: str = "network"
        for attempt in range(MAX_ATTEMPTS):
            retry_after = 0.0
            try:
                response = await self._client.post(RESEND_URL, json=payload, headers=headers)
            except httpx.TransportError:
                status = "network"
            else:
                if response.is_success:
                    logger.info("email sent")
                    return
                status = str(response.status_code)
                if response.status_code not in RETRYABLE_STATUSES:
                    break
                retry_after = _retry_after(response)
            if attempt < MAX_ATTEMPTS - 1:
                backoff = min(2**attempt, 4) + random.random()  # noqa: S311 - jitter only
                await asyncio.sleep(max(backoff, retry_after))
        logger.error("email send failed: status=%s", status)


def build_email_sender(settings: Settings, http: httpx.AsyncClient) -> EmailSender:
    key, sender = settings.resend_api_key, settings.email_from
    # Settings validation guarantees both are present when the backend is resend.
    if settings.email_backend == "resend" and key is not None and sender is not None:
        return ResendSender(http, key, sender)
    return ConsoleSender()
