import pytest

from tests.guard import ensure_test_stack

DB = "postgresql+asyncpg://yokai_test:test@127.0.0.1:55432/yokai_test"
REDIS = "redis://:test@127.0.0.1:56379/0"


def test_accepts_default_test_urls() -> None:
    ensure_test_stack(DB, REDIS)


@pytest.mark.parametrize(
    ("db", "redis"),
    [
        ("postgresql+asyncpg://u:p@127.0.0.1:5432/yokai_test", REDIS),
        ("postgresql+asyncpg://u:p@postgres:55432/yokai_test", REDIS),
        ("postgresql+asyncpg://u:p@127.0.0.1:55432/yokai", REDIS),
        (DB, "redis://:test@127.0.0.1:6379/0"),
        (DB, "redis://:test@redis:56379/0"),
    ],
)
def test_rejects_non_test_stack(db: str, redis: str) -> None:
    with pytest.raises(RuntimeError):
        ensure_test_stack(db, redis)
