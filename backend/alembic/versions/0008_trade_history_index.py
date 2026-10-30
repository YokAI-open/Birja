"""trade history index

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-30 08:34:41.634538

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Existing fills stay writable during the index build. CONCURRENTLY must
    # run outside a transaction; env.py commits each preceding revision.
    with op.get_context().autocommit_block():
        op.create_index(
            "ix_trades_user_created_id",
            "trades",
            ["user_id", "created_at", "id"],
            unique=False,
            postgresql_concurrently=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.get_context().autocommit_block():
        op.drop_index(
            "ix_trades_user_created_id", table_name="trades", postgresql_concurrently=True
        )
