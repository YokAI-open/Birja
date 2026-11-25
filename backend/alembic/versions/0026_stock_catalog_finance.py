"""Add stable stock catalog financial identity and retained authority facts.

Revision ID: 0026
Revises: 0025
"""

import hashlib
import re
from collections.abc import Sequence
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | Sequence[str] | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATALOG_FINANCE_SQL_SHA256 = "eb4a44fd9a2812aa693607db00d7d53240d8afb4d7e0bd1305035b1e15845a04"
CATALOG_EXECUTION_SQL_SHA256 = "b8cc7ea9d8c9227bf420778912f86d7f2cbddca0494e608cd157f929917630fe"
CATALOG_ACTIONS_SQL_SHA256 = "6aa0c43d7554fdb7ab85ee557bfcbee6a0fc8e286a5b118d999b3937139a28c3"
SQL_DIR = Path(__file__).parents[1] / "sql"
SQL_ASSETS = {
    "0026_stock_catalog_finance.sql": CATALOG_FINANCE_SQL_SHA256,
    "0026_stock_catalog_execution.sql": CATALOG_EXECUTION_SQL_SHA256,
    "0026_stock_catalog_actions.sql": CATALOG_ACTIONS_SQL_SHA256,
}
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


def _read_pinned(path: Path, checksum: str) -> str:
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != checksum:
        raise RuntimeError(f"Catalog finance migration checksum mismatch for {path.name}")
    return source.decode("utf-8")


def _load_revision(filename: str) -> ModuleType:
    path = Path(__file__).with_name(filename)
    spec = spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Missing immutable Alembic revision {filename}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def upgrade() -> None:
    _require_catalog_migrator()
    statements = _load_revision("0017_portfolio_ownership.py")._statements
    bind = op.get_bind()
    for asset, digest in SQL_ASSETS.items():
        for statement in statements(_read_pinned(SQL_DIR / asset, digest)):
            # SQLAlchemy bind detection would interpret JSON literals in SQL bodies.
            bind.exec_driver_sql(statement)


def _restore_prior_routines() -> None:
    # Replace only functions changed by the action companion. CREATE OR
    # REPLACE keeps their object identities and existing caller grants.
    portfolio_revision = _load_revision("0017_portfolio_ownership.py")
    bind = op.get_bind()
    for asset, names in (
        (
            "0017_dividend_portfolio.sql",
            {"stock_dividend_authority", "apply_stock_dividend", "record_stock_dividend_hold"},
        ),
        ("0017_stock_portfolio.sql", {"check_stock_split_digest_version"}),
    ):
        source = _read_pinned(SQL_DIR / asset, portfolio_revision.SQL_ASSETS[asset])
        restored = set()
        for statement in portfolio_revision._statements(source):
            match = re.search(r"^CREATE OR REPLACE FUNCTION public\.(\w+)\(", statement, re.M)
            if match and match[1] in names:
                bind.exec_driver_sql(statement)
                restored.add(match[1])
        if restored != names:
            raise RuntimeError(f"Missing prior routine in {asset}")

    filename = "0012_stock_action_resolution.py"
    _read_pinned(
        Path(__file__).with_name(filename),
        "439a36e6c10c67600d0388c5d1ee11be6425fb4b2c3b71523d6c430928bd8ce0",
    )
    resolution = _load_revision(filename).FUNCTION
    bind.exec_driver_sql(resolution.replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))


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
    _restore_prior_routines()
    op.execute("DROP TRIGGER stock_catalog_split_movements ON public.stock_split_applications")
    op.execute("DROP FUNCTION public.check_stock_catalog_split_movements()")
    op.execute(
        "DROP FUNCTION public.stock_catalog_action_context("
        "bigint,bigint,bigint,timestamptz,timestamptz,boolean)"
    )
    op.execute("DROP TRIGGER catalog_stock_trade_requires_fill_evidence ON public.trades")
    op.execute(
        "DROP TRIGGER catalog_stock_fill_evidence_requires_trade "
        "ON public.stock_catalog_fill_evidence"
    )
    op.execute(
        "DROP TRIGGER catalog_stock_fill_evidence_immutable ON public.stock_catalog_fill_evidence"
    )
    op.execute("DROP FUNCTION public.check_catalog_stock_fill()")
    op.execute("DROP FUNCTION public.assert_catalog_stock_execution_current(bigint,bigint,jsonb)")
    op.execute(
        "DROP FUNCTION public.stock_catalog_scope_current("
        "bigint,text,public.stock_catalog_instruments,public.stock_catalog_listings,timestamptz,jsonb)"
    )
    for table in FINANCIAL_TABLES:
        op.drop_table(table, schema="public")
    op.drop_constraint(op.f("ck_coins_symbol_length"), "coins", type_="check", schema="public")
    op.create_check_constraint(
        op.f("ck_coins_symbol_length"), "coins", "length(symbol) BETWEEN 1 AND 10", schema="public"
    )
