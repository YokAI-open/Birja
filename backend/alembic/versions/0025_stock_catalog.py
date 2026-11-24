"""Add independent, versioned stock discovery storage.

Revision ID: 0025
Revises: 0024
"""

import hashlib
from collections.abc import Sequence
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | Sequence[str] | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STOCK_CATALOG_SQL_SHA256 = "7665f5df6c828f681f6d7db7dda8b4cbf1a19d4f645fa4003fec94c1a5fa32fa"
CATALOG_TABLES = (
    "stock_catalog_aliases",
    "stock_catalog_listings",
    "stock_catalog_admissions",
    "stock_catalog_securities",
    "stock_catalog_generations",
)


def _require_catalog_migrator() -> None:
    if (
        op.get_context().as_sql
        or op.get_bind().execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator"
    ):
        raise RuntimeError("Stock catalog migration requires authenticated birja_migrator")


def upgrade() -> None:
    _require_catalog_migrator()
    source = (Path(__file__).parents[1] / "sql" / "0025_stock_catalog.sql").read_bytes()
    if hashlib.sha256(source).hexdigest() != STOCK_CATALOG_SQL_SHA256:
        raise RuntimeError("Stock catalog SQL checksum mismatch")
    spec = spec_from_file_location(
        "portfolio_ownership_parser", Path(__file__).with_name("0017_portfolio_ownership.py")
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Missing immutable portfolio SQL parser")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    for statement in module._statements(source.decode("utf-8")):
        op.execute(statement)


def downgrade() -> None:
    _require_catalog_migrator()
    bind = op.get_bind()
    for table in reversed(CATALOG_TABLES):
        bind.execute(sa.text(f"LOCK TABLE public.{table} IN ACCESS EXCLUSIVE MODE"))
    for table in CATALOG_TABLES:
        evidence_exists = sa.text(
            f"SELECT EXISTS (SELECT 1 FROM public.{table})"  # noqa: S608 - fixed migration table names
        )
        if bind.execute(evidence_exists).scalar_one():
            raise RuntimeError("Stock catalog downgrade refused; catalog evidence is retained")
    for table in CATALOG_TABLES:
        op.drop_table(table, schema="public")
