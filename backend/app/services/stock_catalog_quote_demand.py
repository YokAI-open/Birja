"""Bounded, expiring selection demand for display-only catalog quotes."""

import asyncio
import secrets
from dataclasses import dataclass
from hashlib import sha256
from typing import Literal, cast, get_args

from redis.asyncio import Redis
from redis.exceptions import RedisError

CatalogQuoteOutcome = Literal[
    "ready",
    "quote_unavailable",
    "throttled",
    "source_error",
    "identity_review",
    "queue_full",
    "failed_check",
]
_OUTCOMES = frozenset(get_args(CatalogQuoteOutcome))
_REQUEST_TTL_MS = 10_000
_WAIT_SECONDS = 7
_WAIT_POLL_SECONDS = 0.25
_PENDING_LIMIT = 64
_BATCH_LIMIT = 8

# The sorted set bounds work across every server sharing the provider account.
# All deadlines use Redis time so app and worker clocks cannot extend a request.
_TIME_MS = """
local t = redis.call('TIME')
local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
"""
_ENQUEUE = (
    _TIME_MS
    + """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
local existing = redis.call('GET', KEYS[2])
if existing then return existing end
if redis.call('ZCARD', KEYS[1]) >= tonumber(ARGV[3]) then return '' end
local ttl = tonumber(ARGV[4])
redis.call('SET', KEYS[2], ARGV[2], 'PX', ttl)
redis.call('ZADD', KEYS[1], now + ttl, ARGV[1])
redis.call('PEXPIRE', KEYS[1], ttl)
return ARGV[2]
"""
)
_PENDING = (
    _TIME_MS
    + """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
local items = {}
local prefix = ARGV[1]
for _, member in ipairs(redis.call('ZRANGE', KEYS[1], 0, -1)) do
    if string.sub(member, 1, string.len(prefix)) == prefix then
        local token = redis.call('GET', KEYS[1] .. ':pending:' .. member)
        if token then
            table.insert(items, member)
            table.insert(items, token)
            if #items >= tonumber(ARGV[2]) * 2 then break end
        end
    end
end
return items
"""
)
_COMPLETE = """
if redis.call('GET', KEYS[2]) ~= ARGV[2] then return 0 end
if ARGV[4] ~= '' then
    redis.call('SET', KEYS[4], ARGV[4], 'PX', ARGV[5])
end
redis.call('SET', KEYS[3], ARGV[3], 'PX', ARGV[6])
redis.call('DEL', KEYS[2])
redis.call('ZREM', KEYS[1], ARGV[1])
return 1
"""


@dataclass(frozen=True, slots=True)
class CatalogQuoteRequest:
    catalog_id: int
    listing_version: int
    fingerprint: str
    token: str


def _queue(account: str) -> str:
    return "sim:stock-catalog-demand:" + sha256(account.encode()).hexdigest()


def _server(server: str) -> str:
    return sha256(server.encode()).hexdigest() + ":"


def _member(server: str, catalog_id: int, listing_version: int, fingerprint: str) -> str:
    return f"{_server(server)}{catalog_id}:{listing_version}:{fingerprint}"


def _text(raw: str | bytes) -> str:
    return raw.decode("ascii") if isinstance(raw, bytes) else raw


def catalog_quote_key(
    *, account: str, server: str, catalog_id: int, listing_version: int, fingerprint: str
) -> str:
    member = _member(server, catalog_id, listing_version, fingerprint)
    return f"{_queue(account)}:display:{member}"


async def request_catalog_quote(
    redis: Redis,
    *,
    account: str,
    server: str,
    catalog_id: int,
    listing_version: int,
    fingerprint: str,
) -> CatalogQuoteOutcome:
    """Coalesce one admitted selection and wait briefly for its exact request."""
    queue = _queue(account)
    member = _member(server, catalog_id, listing_version, fingerprint)
    request_key = f"{queue}:pending:{member}"
    try:
        async with asyncio.timeout(_WAIT_SECONDS):
            token = await redis.eval(
                _ENQUEUE,
                2,
                queue,
                request_key,
                member,
                secrets.token_hex(16),
                _PENDING_LIMIT,
                _REQUEST_TTL_MS,
            )
            if not token:
                return "queue_full"
            token = _text(token)
            outcome_key = f"{queue}:outcome:{token}"
            while True:
                # A result and its request removal are written atomically.
                outcome, current = await redis.mget([outcome_key, request_key])
                if outcome is not None and _text(outcome) in _OUTCOMES:
                    return cast(CatalogQuoteOutcome, _text(outcome))
                if current is None or _text(current) != token:
                    return "quote_unavailable"
                await asyncio.sleep(_WAIT_POLL_SECONDS)
    except RedisError, TimeoutError, UnicodeError:
        return "quote_unavailable"


async def pending_catalog_quotes(
    redis: Redis, *, account: str, server: str, limit: int = _BATCH_LIMIT
) -> tuple[CatalogQuoteRequest, ...]:
    """Return a bounded FIFO-like view for the dedicated scheduler."""
    if not 1 <= limit <= _BATCH_LIMIT:
        raise ValueError("invalid catalog quote batch size")
    items = await redis.eval(_PENDING, 1, _queue(account), _server(server), limit)
    result = []
    for member, token in zip(items[::2], items[1::2], strict=True):
        _, catalog_id, version, fingerprint = _text(member).split(":")
        result.append(CatalogQuoteRequest(int(catalog_id), int(version), fingerprint, _text(token)))
    return tuple(result)


async def current_catalog_quote_request(
    redis: Redis, request: CatalogQuoteRequest, *, account: str, server: str
) -> bool:
    member = _member(server, request.catalog_id, request.listing_version, request.fingerprint)
    token = await redis.get(f"{_queue(account)}:pending:{member}")
    return token is not None and _text(token) == request.token


async def complete_catalog_quote(
    redis: Redis,
    request: CatalogQuoteRequest,
    *,
    account: str,
    server: str,
    reason: CatalogQuoteOutcome,
    quote_json: str | None = None,
    quote_ttl_ms: int = 0,
) -> bool:
    """Set the result once and discard only the matching pending token."""
    if quote_json is not None and (reason != "ready" or not 1 <= quote_ttl_ms <= 600_000):
        raise ValueError("invalid catalog quote cache write")
    member = _member(server, request.catalog_id, request.listing_version, request.fingerprint)
    queue = _queue(account)
    return bool(
        await redis.eval(
            _COMPLETE,
            4,
            queue,
            f"{queue}:pending:{member}",
            f"{queue}:outcome:{request.token}",
            f"{queue}:display:{member}",
            member,
            request.token,
            reason,
            quote_json or "",
            quote_ttl_ms,
            _REQUEST_TTL_MS,
        )
    )
