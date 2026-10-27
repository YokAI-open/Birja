import hashlib
import hmac

from pydantic import SecretStr


def hmac_hex(secret: SecretStr, message: str) -> str:
    """HMAC-SHA256 hexdigest of message, keyed with the server secret."""
    return hmac.new(
        secret.get_secret_value().encode(), message.encode(), hashlib.sha256
    ).hexdigest()
