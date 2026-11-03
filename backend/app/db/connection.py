"""Shared asyncpg connection policy."""

from typing import Any, Protocol


class DatabaseSettings(Protocol):
    @property
    def env(self) -> str: ...

    @property
    def database_ssl_ca_file(self) -> str | None: ...


def database_connect_args(settings: DatabaseSettings, *, migration: bool = False) -> dict[str, Any]:
    return {
        "timeout": 5,
        "server_settings": {
            "statement_timeout": "30000",
            "idle_in_transaction_session_timeout": "30000",
        },
    }
