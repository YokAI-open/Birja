"""Migration-only additive management expansion; no funding or runtime admission.

Revision ID: 0018
Revises: 0017
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0018"
down_revision: str | Sequence[str] | None = "0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("management expansion requires online authenticated migration")
    if op.get_bind().execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator":
        raise RuntimeError("management expansion requires authenticated birja_migrator")
    op.add_column(
        "accounts", sa.Column("description", sa.Text(), nullable=False, server_default="")
    )
    op.add_column("accounts", sa.Column("name_key", sa.Text(collation="C"), nullable=True))
    op.create_table(
        "portfolio_creations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("creation_key", UUID(as_uuid=True), nullable=False),
        sa.Column("portfolio_id", sa.BigInteger(), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("payload_version", sa.SmallInteger(), nullable=False),
        sa.Column("canonical_payload", JSONB(), nullable=False),
        sa.Column("amount", sa.Numeric(20, 8), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", "creation_key", name="uq_portfolio_creation_owner_key"),
        sa.UniqueConstraint("portfolio_id", name="uq_portfolio_creation_root"),
        sa.UniqueConstraint("id", "portfolio_id", "user_id", name="uq_portfolio_creation_lineage"),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_portfolio_creation_owner",
        ),
        sa.CheckConstraint("origin IN ('initial','explicit')", name="origin_known"),
        sa.CheckConstraint("amount=10000", name="fixed_grant"),
        sa.CheckConstraint("payload_version=1", name="payload_version_known"),
        sa.CheckConstraint(
            "jsonb_typeof(canonical_payload)='object' AND "
            "canonical_payload ?& ARRAY['name','description'] AND "
            "canonical_payload - ARRAY['name','description'] = '{}'::jsonb AND "
            "jsonb_typeof(canonical_payload->'name')='string' AND "
            "jsonb_typeof(canonical_payload->'description')='string'",
            name="payload_shape",
        ),
    )
    op.create_index(
        "ix_portfolio_creation_owner_created",
        "portfolio_creations",
        ["user_id", "created_at", "id"],
    )
    op.create_table(
        "portfolio_initializations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("origin", sa.Text(), nullable=False),
        sa.Column("portfolio_id", sa.BigInteger(), nullable=True),
        sa.Column("creation_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("user_id", name="uq_portfolio_initialization_user"),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_portfolio_initialization_owner",
        ),
        sa.ForeignKeyConstraint(
            ["creation_id", "portfolio_id", "user_id"],
            [
                "portfolio_creations.id",
                "portfolio_creations.portfolio_id",
                "portfolio_creations.user_id",
            ],
            name="fk_portfolio_initialization_creation",
        ),
        sa.CheckConstraint(
            "(origin='legacy' AND portfolio_id IS NULL AND creation_id IS NULL) OR "
            "(origin='initial' AND portfolio_id IS NOT NULL AND creation_id IS NOT NULL)",
            name="provenance_exact",
        ),
    )
    op.create_index(
        "ix_portfolio_initialization_root", "portfolio_initializations", ["portfolio_id"]
    )
    op.create_index(
        "ix_portfolio_initialization_creation", "portfolio_initializations", ["creation_id"]
    )
    for table in ("portfolio_creations", "portfolio_initializations"):
        op.execute(f"REVOKE ALL ON public.{table} FROM PUBLIC,birja_app,birja_scheduler")
        op.execute(
            f"REVOKE ALL ON SEQUENCE public.{table}_id_seq FROM PUBLIC,birja_app,birja_scheduler"
        )
        op.execute(
            "CREATE TRIGGER portfolio_provenance_immutable BEFORE UPDATE OR DELETE "
            f"ON public.{table} FOR EACH ROW "
            "EXECUTE FUNCTION public.reject_stock_dividend_mutation()"
        )


def downgrade() -> None:
    raise RuntimeError("management expansion downgrade refused before writes; provenance retained")
