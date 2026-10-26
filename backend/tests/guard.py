"""Refuse to run tests against anything but the isolated test stack."""

from urllib.parse import urlsplit

_LOCAL_HOSTS = {"127.0.0.1", "localhost"}
_TEST_DB_PORT = 55432
_TEST_REDIS_PORT = 56379


def ensure_test_stack(database_url: str, redis_url: str) -> None:
    db = urlsplit(database_url.replace("+asyncpg", "", 1))
    redis = urlsplit(redis_url)
    db_name = db.path.lstrip("/")

    if db.hostname not in _LOCAL_HOSTS or db.port != _TEST_DB_PORT:
        raise RuntimeError(
            f"Refusing to run tests: database must be on 127.0.0.1:{_TEST_DB_PORT} "
            f"(got host={db.hostname!r}, port={db.port!r})"
        )
    if not db_name.endswith("_test"):
        raise RuntimeError(f"Refusing to run tests: database name {db_name!r} must end in '_test'")
    if redis.hostname not in _LOCAL_HOSTS or redis.port != _TEST_REDIS_PORT:
        raise RuntimeError(
            f"Refusing to run tests: Redis must be on 127.0.0.1:{_TEST_REDIS_PORT} "
            f"(got host={redis.hostname!r}, port={redis.port!r})"
        )
