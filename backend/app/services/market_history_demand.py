"""Expiring, coalesced demand and display results in memory-only Redis."""

import asyncio
import secrets
from dataclasses import dataclass
from hashlib import sha256
from typing import Annotated

from pydantic import Field, ValidationError
from redis.asyncio import Redis

from app.schemas.market_history import HistoryState, MarketHistoryQuery, MarketHistoryResponse
from app.services.ratelimit import hit

_PENDING_MS = 30_000
_LOCK_MS = 10_000
_MAX_RESULT = 131072
_TIME = """
local t = redis.call('TIME')
local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
"""
_ENQUEUE = (
    _TIME
    + """
if redis.call('EXISTS', KEYS[3]) ~= 0 then return 'cached' end
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
if redis.call('EXISTS', KEYS[2]) ~= 0 then return 'pending' end
if redis.call('ZCARD', KEYS[1]) >= 64 then return 'unavailable' end
local ttl = tonumber(ARGV[3])
redis.call('SET', KEYS[2], ARGV[2], 'PX', ttl)
redis.call('ZADD', KEYS[1], now + ttl, ARGV[1])
redis.call('PEXPIRE', KEYS[1], ttl)
return 'pending'
"""
)
_CLAIM = (
    _TIME
    + """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
if redis.call('EXISTS', KEYS[2]) ~= 0 then return {} end
local wanted = redis.call('ZRANGE', KEYS[1], 0, 0)
if #wanted == 0 then return {} end
local member = wanted[1]
local pending = redis.call('GET', KEYS[1] .. ':pending:' .. member)
if not pending then
    redis.call('ZREM', KEYS[1], member)
    return {}
end
redis.call('SET', KEYS[2], ARGV[1], 'PX', ARGV[2])
return {member, pending}
"""
)
_IS_CURRENT = """
if redis.call('GET', KEYS[1]) ~= ARGV[1] then return 0 end
if redis.call('GET', KEYS[2]) ~= ARGV[2] then return 0 end
return 1
"""
_READ_CACHED = """
local value = redis.call('GET', KEYS[1])
if not value then return {} end
return {value, redis.call('PEXPIRETIME', KEYS[1])}
"""
_COMPLETE = (
    _TIME
    + """
if redis.call('GET', KEYS[2]) ~= ARGV[2] then return 0 end
if redis.call('GET', KEYS[3]) ~= ARGV[3] then return 0 end
local completed = 1
if ARGV[4] ~= '' then
    if tonumber(ARGV[5]) > now then
        redis.call('SET', KEYS[4], ARGV[4], 'PXAT', ARGV[5])
    else
        completed = 0
    end
end
redis.call('DEL', KEYS[2], KEYS[3])
redis.call('ZREM', KEYS[1], ARGV[1])
return completed
"""
)
_RELEASE = """
if redis.call('GET', KEYS[1]) == ARGV[1] then redis.call('DEL', KEYS[1]) end
"""


class _Pending(MarketHistoryQuery):
    token: Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]


@dataclass(frozen=True, slots=True)
class HistoryJob:
    fingerprint: str
    query: MarketHistoryQuery
    pending: str
    lock_token: str


def _queue(server: str) -> str:
    return "sim:market-history:v1:" + sha256(server.encode()).hexdigest()


def _text(raw: str | bytes) -> str:
    return raw.decode() if isinstance(raw, bytes) else raw


def history_response(query: MarketHistoryQuery, state: HistoryState) -> MarketHistoryResponse:
    return MarketHistoryResponse(instrument=query.instrument, range=query.range, state=state)


async def _cached(
    redis: Redis, key: str, query: MarketHistoryQuery
) -> tuple[MarketHistoryResponse, int] | None:
    entry = await redis.eval(_READ_CACHED, 1, key)
    if not entry:
        return None
    raw, expires_at_ms = entry
    if expires_at_ms <= 0 or len(raw) > _MAX_RESULT:
        return None
    try:
        result = MarketHistoryResponse.model_validate_json(raw)
    except ValidationError:
        return None
    if result.instrument != query.instrument or result.range != query.range:
        return None
    return result, expires_at_ms


async def request_history(
    redis: Redis,
    *,
    server: str,
    owner_id: int,
    query: MarketHistoryQuery,
    fingerprint: str,
) -> tuple[MarketHistoryResponse, int | None]:
    queue = _queue(server)
    cache = f"{queue}:result:{fingerprint}"
    async with asyncio.timeout(2):
        result = await _cached(redis, cache, query)
        if result is not None:
            return result
        allowed, _ = await hit(redis, f"{queue}:owner:{owner_id}", 12, 60)
        if not allowed:
            return history_response(query, "unavailable"), None
        pending = _Pending(
            instrument=query.instrument, range=query.range, token=secrets.token_hex(16)
        )
        response = _text(
            await redis.eval(
                _ENQUEUE,
                3,
                queue,
                f"{queue}:pending:{fingerprint}",
                cache,
                fingerprint,
                pending.model_dump_json(),
                _PENDING_MS,
            )
        )
        if response == "cached":
            result = await _cached(redis, cache, query)
            if result is not None:
                return result
        return history_response(query, "pending" if response == "pending" else "unavailable"), None


async def claim_history(redis: Redis, server: str) -> HistoryJob | None:
    queue = _queue(server)
    token = secrets.token_hex(16)
    claim = await redis.eval(_CLAIM, 2, queue, f"{queue}:lock", token, _LOCK_MS)
    if not claim:
        return None
    fingerprint, raw = map(_text, claim)
    try:
        parsed = _Pending.model_validate_json(raw)
    except ValidationError:
        await redis.eval(_RELEASE, 1, f"{queue}:lock", token)
        return None
    return HistoryJob(
        fingerprint,
        MarketHistoryQuery(instrument=parsed.instrument, range=parsed.range),
        raw,
        token,
    )


async def current_history_job(redis: Redis, server: str, job: HistoryJob) -> bool:
    queue = _queue(server)
    return bool(
        await redis.eval(
            _IS_CURRENT,
            2,
            f"{queue}:pending:{job.fingerprint}",
            f"{queue}:lock",
            job.pending,
            job.lock_token,
        )
    )


async def complete_history(
    redis: Redis,
    server: str,
    job: HistoryJob,
    result: MarketHistoryResponse | None = None,
    *,
    expires_at_ms: int = 0,
) -> bool:
    queue = _queue(server)
    serialized = result.model_dump_json() if result is not None else ""
    if len(serialized) > _MAX_RESULT:
        serialized = ""
    return bool(
        await redis.eval(
            _COMPLETE,
            4,
            queue,
            f"{queue}:pending:{job.fingerprint}",
            f"{queue}:lock",
            f"{queue}:result:{job.fingerprint}",
            job.fingerprint,
            job.pending,
            job.lock_token,
            serialized,
            expires_at_ms,
        )
    )


async def release_history(redis: Redis, server: str, job: HistoryJob) -> None:
    await redis.eval(_RELEASE, 1, f"{_queue(server)}:lock", job.lock_token)
