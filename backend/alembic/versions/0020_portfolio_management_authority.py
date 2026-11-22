"""Install narrow management authority; runtime admission is finalized separately.

Revision ID: 0020
Revises: 0019
"""

import hashlib
from collections.abc import Sequence
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | Sequence[str] | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SQL_SHA256 = "9fe1fd5706df5ac319f7a70dcfe73a437f0886ba7e4a827758fa8c414106963d"


def upgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("management authority requires online authenticated migration")
    sql = (Path(__file__).parents[1] / "sql/0020_portfolio_management.sql").read_bytes()
    if hashlib.sha256(sql).hexdigest() != SQL_SHA256:
        raise RuntimeError("management authority SQL checksum mismatch; refusing before writes")
    if op.get_bind().execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator":
        raise RuntimeError("management authority requires authenticated birja_migrator")
    # Reuse the immutable SQL splitter, including dollar-quoted bodies.
    spec = spec_from_file_location(
        "portfolio_ownership_parser", Path(__file__).with_name("0017_portfolio_ownership.py")
    )
    module = module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("missing immutable portfolio SQL parser")
    spec.loader.exec_module(module)
    for statement in module._statements(sql.decode("utf-8")):
        op.execute(statement)


def downgrade() -> None:
    raise RuntimeError("management authority downgrade refused before writes; provenance retained")
