"""Shared asyncpg trust and bounded timeout policy for every engine."""

import ssl
from typing import Any, Protocol
from urllib.parse import parse_qsl, unquote, urlsplit


class DatabaseSettings(Protocol):
    @property
    def env(self) -> str: ...

    @property
    def database_ssl_ca_file(self) -> str | None: ...

    @property
    def database_url(self) -> str: ...


def validate_database_url(value: str, *, production: bool = False) -> str:
    if not value.startswith("postgresql+asyncpg://"):
        raise ValueError("database_url must start with 'postgresql+asyncpg://'")
    try:
        url = urlsplit(value)
        hostname = url.hostname
        query = parse_qsl(url.query, keep_blank_values=True)
    except ValueError:
        raise ValueError("database_url is invalid") from None
    # Trust belongs exclusively in the shared context, not asyncpg URL modes
    # or libpq-style sslmode parameters.
    if any(key.lower().startswith("ssl") for key, _ in query):
        raise ValueError("database TLS options must not appear in URL query")
    # asyncpg skips TLS over Unix sockets. Keep production on the single named
    # TCP host, with no query-string host override that can select a socket.
    if production and (
        not hostname
        or unquote(hostname).startswith("/")
        or any(key.lower() == "host" for key, _ in query)
    ):
        raise ValueError(
            "production database_url requires a TCP hostname without host query override"
        )
    return value


def database_ssl_context(settings: DatabaseSettings) -> ssl.SSLContext | None:
    validate_database_url(settings.database_url, production=settings.env == "prod")
    ca_file = settings.database_ssl_ca_file
    if not ca_file:
        if settings.env == "prod":
            raise ValueError("database_ssl_ca_file is required in prod")
        return None
    try:
        return ssl.create_default_context(cafile=ca_file)
    except OSError, ValueError:
        # OpenSSL/filesystem exceptions can contain private paths. Fail closed
        # without embedding certificate data, credentials or paths in errors.
        raise ValueError("database_ssl_ca_file must be a readable valid CA file") from None


def database_connect_args(settings: DatabaseSettings, *, migration: bool = False) -> dict[str, Any]:
    args: dict[str, Any] = {
        "timeout": 5,
        "server_settings": {
            "statement_timeout": "120000" if migration else "30000",
            "idle_in_transaction_session_timeout": "30000",
        },
    }
    if migration:
        args["server_settings"]["lock_timeout"] = "5000"
    context = database_ssl_context(settings)
    if context is not None:
        args["ssl"] = context
    return args
