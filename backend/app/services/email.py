import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    async def send_code(self, to: str, code: str) -> None: ...


class ConsoleSender:
    """Dev-only sender: prints the code to the log instead of sending email."""

    async def send_code(self, to: str, code: str) -> None:
        logger.info("DEV EMAIL to=%s code=%s", to, code)
