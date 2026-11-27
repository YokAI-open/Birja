"""Add the private daily portfolio valuation ledger.

Revision ID: 0028
Revises: 0027
"""

from collections.abc import Sequence
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0028"
down_revision: str | Sequence[str] | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
SQL_SHA256 = "6982dea7fb2590633d622f53e856a079f15510766f3043bc4dda808458846954"


def _require_daily_value_migrator() -> None:
    if (
        op.get_context().as_sql
        or not op.get_bind()
        .execute(sa.text("SELECT session_user = 'birja_migrator' AND current_user = session_user"))
        .scalar_one()
    ):
        raise RuntimeError("Daily value migration requires authenticated birja_migrator")


def upgrade() -> None:
    _require_daily_value_migrator()
    sql = (Path(__file__).parents[1] / "sql/0028_portfolio_daily_values.sql").read_bytes()
    if sha256(sql).hexdigest() != SQL_SHA256:
        raise RuntimeError("Daily value migration SQL checksum mismatch")
    spec = spec_from_file_location(
        "portfolio_ownership_parser", Path(__file__).with_name("0017_portfolio_ownership.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing immutable portfolio SQL parser")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    bind = op.get_bind()
    for statement in module._statements(sql.decode("utf-8")):
        bind.exec_driver_sql(statement)


def downgrade() -> None:
    _require_daily_value_migrator()
    bind = op.get_bind()
    bind.exec_driver_sql("LOCK TABLE public.portfolio_daily_values IN ACCESS EXCLUSIVE MODE")
    if bind.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM public.portfolio_daily_values)")
    ).scalar_one():
        raise RuntimeError("Daily value downgrade refused; portfolio observations are retained")
    op.drop_table("portfolio_daily_values", schema="public")
    bind.exec_driver_sql("DROP FUNCTION public.check_portfolio_daily_value_root()")
    bind.exec_driver_sql("DROP FUNCTION public.lock_portfolio_daily_value_root(bigint,bigint)")
