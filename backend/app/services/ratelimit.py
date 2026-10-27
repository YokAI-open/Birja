import ipaddress

from redis.asyncio import Redis

IPV6_BUCKET_PREFIX = 64


class RateLimited(Exception):
    """A fixed-window limit was exceeded; retry_after is whole seconds until it resets."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"rate limited, retry in {retry_after}s")
        self.retry_after = retry_after


def ip_bucket(host: str) -> str:
    """Rate-limit bucket for a client address. IPv4 is used as-is; IPv6 is grouped
    by its /64, since one subscriber usually holds a whole /64 and could otherwise
    rotate through unlimited buckets. Unparseable values ("unknown") pass through."""
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return host
    if isinstance(addr, ipaddress.IPv6Address):
        if addr.ipv4_mapped is not None:
            return str(addr.ipv4_mapped)
        return str(ipaddress.IPv6Network((addr, IPV6_BUCKET_PREFIX), strict=False))
    return str(addr)


async def hit(redis: Redis, key: str, limit: int, window: int) -> tuple[bool, int]:
    """Count one hit in a fixed window. Returns (allowed, seconds until the window ends).

    INCR + EXPIRE NX + TTL run in one MULTI, so the key always gets a TTL on its
    first hit and later hits never extend it. Fixed window is enough for the MVP.
    Known trade-off: anyone can burn a victim's per-email request quota (a nuisance
    lockout of at most one window); accepted for a friends-only app.
    """
    pipe = redis.pipeline(transaction=True)
    pipe.incr(key)
    pipe.expire(key, window, nx=True)
    pipe.ttl(key)
    count, _, ttl = await pipe.execute()
    return count <= limit, max(int(ttl), 1)


async def enforce(redis: Redis, key: str, limit: int, window: int) -> None:
    allowed, retry_after = await hit(redis, key, limit, window)
    if not allowed:
        raise RateLimited(retry_after)
