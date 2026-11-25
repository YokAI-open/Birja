"""Bounded, expiring action-monitoring interest for selected catalog listings."""

import asyncio
import json
from hashlib import sha256

from redis.asyncio import Redis
from redis.exceptions import RedisError

_TTL_MS = 180_000
_PENDING_LIMIT = 64
_CACHE_TIMEOUT_SECONDS = 0.5
_CLOCK_MS = """
local t = redis.call('TIME')
local now = tonumber(t[1]) * 1000 + math.floor(tonumber(t[2]) / 1000)
"""
_RECORD = (
    _CLOCK_MS
    + """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)
if redis.call('ZSCORE', KEYS[1], ARGV[1]) or
   redis.call('ZCARD', KEYS[1]) < tonumber(ARGV[2]) then
    local ttl = tonumber(ARGV[3])
    redis.call('ZADD', KEYS[1], now + ttl, ARGV[1])
    redis.call('PEXPIRE', KEYS[1], ttl)
end
"""
)
_READ = (
    _CLOCK_MS
    + """
return redis.call('ZRANGEBYSCORE', KEYS[1], '(' .. now, '+inf', 'LIMIT', 0, ARGV[1])
"""
)


def _key(account: str, server: str) -> str:
    scope = json.dumps([account, server], separators=(",", ":")).encode()
    return "sim:stock-catalog-actions:interest:" + sha256(scope).hexdigest()


async def record_catalog_action_interest(
    redis: Redis, *, account: str, server: str, catalog_id: int, listing_id: int
) -> None:
    """Coalesce a selected exact listing while the user waits for normal checks."""
    try:
        async with asyncio.timeout(_CACHE_TIMEOUT_SECONDS):
            await redis.eval(
                _RECORD,
                1,
                _key(account, server),
                f"{catalog_id}:{listing_id}",
                _PENDING_LIMIT,
                _TTL_MS,
            )
    except RedisError, TimeoutError:
        # A cold or unavailable cache leaves the ordinary action gate in force.
        return


async def selected_catalog_actions(
    redis: Redis, *, account: str, server: str
) -> tuple[tuple[int, int], ...]:
    """Return selection hints only. The scheduler resolves current SQL authority."""
    try:
        async with asyncio.timeout(_CACHE_TIMEOUT_SECONDS):
            members = await redis.eval(_READ, 1, _key(account, server), _PENDING_LIMIT)
    except RedisError, TimeoutError:
        return ()
    result = []
    for member in members:
        try:
            value = member.decode("ascii") if isinstance(member, bytes) else member
            catalog_id, listing_id = (int(part) for part in value.split(":"))
        except ValueError:
            continue
        if 0 < catalog_id < 2**63 and 0 < listing_id < 2**63:
            result.append((catalog_id, listing_id))
    return tuple(result)
