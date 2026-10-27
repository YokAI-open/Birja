import hmac
import secrets

from pydantic import SecretStr
from redis.asyncio import Redis

from app.core.security import hmac_hex

OTP_TTL_SECONDS = 600
OTP_MAX_ATTEMPTS = 5
KEY_PREFIX = "sim:otp:"

# Counts the attempt atomically before any comparison; the attempt that exceeds
# the limit deletes the code.
_ATTEMPT_LUA = """
local mac = redis.call('HGET', KEYS[1], 'mac')
if not mac then return nil end
local n = redis.call('HINCRBY', KEYS[1], 'attempts', 1)
if n > tonumber(ARGV[1]) then
  redis.call('DEL', KEYS[1])
  return nil
end
return {mac, n}
"""

# Compare-and-delete: only one concurrent caller can consume a code.
_CONSUME_LUA = """
if redis.call('HGET', KEYS[1], 'mac') == ARGV[1] then
  redis.call('DEL', KEYS[1])
  return 1
end
return 0
"""


class OtpStore:
    def __init__(
        self,
        redis: Redis,
        secret: SecretStr,
        ttl_seconds: int = OTP_TTL_SECONDS,
        max_attempts: int = OTP_MAX_ATTEMPTS,
    ) -> None:
        self._redis = redis
        self._secret = secret
        self._ttl = ttl_seconds
        self._max = max_attempts
        self._attempt = redis.register_script(_ATTEMPT_LUA)
        self._consume = redis.register_script(_CONSUME_LUA)

    def email_key(self, email: str) -> str:
        return hmac_hex(self._secret, "email:" + email)

    def _mac(self, email: str, code: str) -> str:
        return hmac_hex(self._secret, f"otp:{email}:{code}")

    async def issue(self, email: str) -> str:
        code = f"{secrets.randbelow(10**6):06d}"
        key = KEY_PREFIX + self.email_key(email)
        pipe = self._redis.pipeline(transaction=True)
        pipe.delete(key)
        pipe.hset(key, mapping={"mac": self._mac(email, code), "attempts": 0})
        pipe.expire(key, self._ttl)
        await pipe.execute()
        return code

    async def verify(self, email: str, code: str) -> bool:
        key = KEY_PREFIX + self.email_key(email)
        res = await self._attempt(keys=[key], args=[self._max])
        if res is None:
            return False
        stored_mac, attempts = res[0], int(res[1])
        candidate = self._mac(email, code)
        if hmac.compare_digest(stored_mac, candidate):
            return bool(await self._consume(keys=[key], args=[candidate]) == 1)
        if attempts >= self._max:
            # Compare-and-delete: a code issued since the attempt above must survive.
            await self._consume(keys=[key], args=[stored_mac])
        return False
