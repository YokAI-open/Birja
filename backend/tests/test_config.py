import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_invalid_database_url_error_hides_password() -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(database_url="postgresql://u:SuperSecret@h/db", redis_url="redis://:pw@h:6379/0")

    assert "database_url must start with" in str(exc_info.value)
    assert "SuperSecret" not in str(exc_info.value)
