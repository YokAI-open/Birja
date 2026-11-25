"""Short-lived quote requests. Accepted quotes remain in PostgreSQL."""

import asyncio
import secrets
from hashlib import sha256

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.services.stock_quote_rules import CURATED_SYMBOLS

POLL_SECONDS = 1
_REQUEST_TTL_SECONDS = 10
_WAIT_SECONDS = 7
_WAIT_POLL_SECONDS = 0.25
_CLEAR_REQUEST = """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
end
return 0
"""


def _key(account: str, server: str, symbol: str) -> str:
    scope = sha256(f"{account}\0{server}".encode()).hexdigest()
    return f"sim:stock-quote-demand:{scope}:{symbol}"


async def request_stock_quote(redis: Redis, symbol: str, *, account: str, server: str) -> bool:
    """Wait for the scheduler to finish a coalesced attempt, within a short bound."""
    if symbol not in CURATED_SYMBOLS:
        return False
    key = _key(account, server, symbol)
    token = secrets.token_hex(16)
    try:
        async with asyncio.timeout(_WAIT_SECONDS):
            previous = await redis.set(key, token, nx=True, ex=_REQUEST_TTL_SECONDS, get=True)
            request = previous.encode() if isinstance(previous, str) else previous or token.encode()
            while True:
                await asyncio.sleep(_WAIT_POLL_SECONDS)
                current = await redis.get(key)
                if (current.encode() if isinstance(current, str) else current) != request:
                    return True
    except RedisError, TimeoutError:
        return False


async def pending_stock_quotes(
    redis: Redis, *, account: str, server: str
) -> dict[str, str | bytes]:
    symbols = sorted(CURATED_SYMBOLS)
    tokens = await redis.mget([_key(account, server, symbol) for symbol in symbols])
    return {symbol: token for symbol, token in zip(symbols, tokens, strict=True) if token}


async def complete_stock_quotes(
    redis: Redis, requests: dict[str, str | bytes], *, account: str, server: str
) -> None:
    if requests:
        async with redis.pipeline(transaction=False) as pipeline:
            for symbol, token in requests.items():
                pipeline.eval(_CLEAR_REQUEST, 1, _key(account, server, symbol), token)
            await pipeline.execute()
