"""Read the current operator-managed access list without caching file contents."""

import asyncio
import os
import stat

from app.schemas.auth import RequestCodeIn

_MAX_FILE_BYTES = 16 * 1024


def read_allowed_emails(path: str) -> frozenset[str]:
    """A missing or invalid configured file admits nobody."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as file:
            if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                return frozenset()
            data = file.read(_MAX_FILE_BYTES + 1)
        if len(data) > _MAX_FILE_BYTES:
            return frozenset()
        return frozenset(
            RequestCodeIn(email=line).email
            for line in data.decode("utf-8").splitlines()
            if line.strip()
        )
    except OSError, ValueError:
        return frozenset()


async def email_allowed(path: str, email: str | None) -> bool:
    if not path:
        return True
    return email in await asyncio.to_thread(read_allowed_emails, path)
