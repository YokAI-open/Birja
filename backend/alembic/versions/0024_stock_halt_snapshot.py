"""Admit fresh reported stock halt snapshots for simulator execution.

Revision ID: 0024
Revises: 0023
"""

import hashlib
from collections.abc import Sequence
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | Sequence[str] | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STOCK_HALT_SQL_SHA256 = "fa19099943dd885cfa3548cd45f25fb5d5150307524ea41d0cae0aa4b2c6e986"
LEGACY_STOCK_SQL_SHA256 = "3dc967baccb425ba26f73bb2fab66b7947aff73f5454ea2f85e03a6e0aa5e08b"


def _checked_sql(filename: str, expected: str) -> str:
    source = (Path(__file__).parents[1] / "sql" / filename).read_bytes()
    if hashlib.sha256(source).hexdigest() != expected:
        raise RuntimeError("Stock execution SQL checksum mismatch")
    return source.decode("utf-8")


def _stock_migrator() -> None:
    if (
        op.get_context().as_sql
        or op.get_bind().execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator"
    ):
        raise RuntimeError("Stock halt snapshot migration requires authenticated birja_migrator")


def _statements(source: str) -> list[str]:
    spec = spec_from_file_location(
        "portfolio_ownership_parser", Path(__file__).with_name("0017_portfolio_ownership.py")
    )
    module = module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("Missing immutable portfolio SQL parser")
    spec.loader.exec_module(module)
    return module._statements(source)


def upgrade() -> None:
    _stock_migrator()
    for statement in _statements(
        _checked_sql("0024_stock_halt_snapshot.sql", STOCK_HALT_SQL_SHA256)
    ):
        op.execute(statement)


def downgrade() -> None:
    _stock_migrator()
    previous = _checked_sql("0017_stock_portfolio.sql", LEGACY_STOCK_SQL_SHA256)
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM public.stock_status_evidence WHERE source<>'alpaca')"
            )
        )
        .scalar_one()
    ):
        raise RuntimeError("Stock halt snapshot downgrade refused; reported evidence is retained")
    assert_statement = next(
        statement
        for statement in _statements(previous)
        if statement.startswith("CREATE OR REPLACE FUNCTION public.assert_stock_execution_current(")
    )
    op.execute(assert_statement)
    op.execute("""
        ALTER TABLE public.stock_status_evidence
         DROP CONSTRAINT ck_stock_status_evidence_reported_shape,
         DROP CONSTRAINT ck_stock_status_evidence_lease_bound,
         DROP CONSTRAINT ck_stock_status_evidence_source_known,
         ADD CONSTRAINT ck_stock_status_evidence_source_known CHECK (source='alpaca'),
         ADD CONSTRAINT ck_stock_status_evidence_lease_bound CHECK (
          valid_until IS NULL OR (observed_at IS NOT NULL AND observed_at<valid_until
             AND valid_until<=observed_at+interval '60 seconds'))
    """)
