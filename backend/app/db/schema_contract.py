"""Explicit source/schema admission; checks never migrate or repair a database."""

from typing import Literal

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection

Consumer = Literal["portfolio", "retained0017", "retained0014", "retained0008"]
SUPPORTED = {
    "portfolio": frozenset({"0020"}),
    "retained0017": frozenset({"0017"}),
    "retained0014": frozenset({"0013", "0014"}),
    "retained0008": frozenset({"0007", "0008"}),
}
MIGRATION_ONLY = frozenset({"0015", "0016", "0018", "0019"})


class SchemaAdmissionError(RuntimeError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


async def require_schema(conn: AsyncConnection, *, consumer: Consumer = "portfolio") -> str:
    """Bind a reviewed consumer to its finite schema contract before any writes."""
    try:
        versions = (
            (await conn.execute(text("SELECT version_num FROM public.alembic_version")))
            .scalars()
            .all()
        )
    except DBAPIError:
        raise SchemaAdmissionError("schema_unavailable") from None
    if len(versions) != 1:
        raise SchemaAdmissionError("schema_unavailable")
    revision = versions[0]
    if not isinstance(revision, str):
        raise SchemaAdmissionError("schema_unavailable")
    if revision in MIGRATION_ONLY:
        raise SchemaAdmissionError("migration_only")
    if consumer not in SUPPORTED or revision not in SUPPORTED[consumer]:
        raise SchemaAdmissionError("incompatible_schema")
    return revision
