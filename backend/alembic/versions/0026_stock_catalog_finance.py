"""Add stable stock catalog financial identity and retained authority facts.

Revision ID: 0026
Revises: 0025
"""

import hashlib
from collections.abc import Sequence
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | Sequence[str] | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATALOG_FINANCE_SQL_SHA256 = "eb4a44fd9a2812aa693607db00d7d53240d8afb4d7e0bd1305035b1e15845a04"
FINANCIAL_TABLES = (
    "stock_catalog_fill_evidence",
    "stock_catalog_action_coverage",
    "stock_catalog_status",
    "stock_catalog_financial_quotes",
    "stock_catalog_instruments",
)


def _require_catalog_migrator() -> None:
    if (
        op.get_context().as_sql
        or not op.get_bind()
        .execute(sa.text("SELECT session_user = 'birja_migrator' AND current_user = session_user"))
        .scalar_one()
    ):
        raise RuntimeError("Catalog finance migration requires authenticated birja_migrator")


def upgrade() -> None:
    _require_catalog_migrator()
    source = (Path(__file__).parents[1] / "sql" / "0026_stock_catalog_finance.sql").read_bytes()
    if hashlib.sha256(source).hexdigest() != CATALOG_FINANCE_SQL_SHA256:
        raise RuntimeError("Catalog finance SQL checksum mismatch")
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
    for table in (*reversed(FINANCIAL_TABLES), "coins", "stock_catalog_admissions"):
        bind.execute(sa.text(f"LOCK TABLE public.{table} IN ACCESS EXCLUSIVE MODE"))
    retained_scope = sa.text("""
        SELECT EXISTS (
            SELECT 1 FROM public.coins WHERE asset_class = 'stock' AND left(symbol, 1) = '@'
            UNION ALL
            SELECT 1 FROM public.stock_catalog_admissions
            WHERE artifact IN (
                'catalog_execution', 'catalog_mark', 'catalog_halt', 'catalog_actions'
            )
        )
        """)
    for table in FINANCIAL_TABLES:
        if bind.execute(
            sa.text(f"SELECT EXISTS (SELECT 1 FROM public.{table})")  # noqa: S608 - fixed names
        ).scalar_one():
            raise RuntimeError("Catalog finance downgrade refused; successor evidence is retained")
    if bind.execute(retained_scope).scalar_one():
        raise RuntimeError("Catalog finance downgrade refused; successor evidence is retained")
    for table in FINANCIAL_TABLES:
        op.drop_table(table, schema="public")
    op.drop_constraint(op.f("ck_coins_symbol_length"), "coins", type_="check", schema="public")
    op.create_check_constraint(
        op.f("ck_coins_symbol_length"), "coins", "length(symbol) BETWEEN 1 AND 10", schema="public"
    )
