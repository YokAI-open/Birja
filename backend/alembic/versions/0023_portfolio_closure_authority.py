"""Install narrow terminal closure authority; runtime admission is separate.

Revision ID:0023
Revises:0022
"""

import hashlib
from collections.abc import Sequence
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | Sequence[str] | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
SQL_SHA256 = "87a58845ea307ba98909802a46061eec6113919dc5af509571d03b316648f3b8"


def upgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("closure authority requires online authenticated migration")
    sql = (Path(__file__).parents[1] / "sql/0023_portfolio_closure.sql").read_bytes()
    if hashlib.sha256(sql).hexdigest() != SQL_SHA256:
        raise RuntimeError("closure authority SQL checksum mismatch; refusing before writes")
    if op.get_bind().execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator":
        raise RuntimeError("closure authority requires authenticated birja_migrator")
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
    raise RuntimeError("closure authority downgrade refused before writes; evidence retained")
