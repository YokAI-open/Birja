"""users and accounts

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-27 14:26:04.061166

"""

from collections.abc import Sequence

import sqlalchemy as sa  # noqa: F401
from alembic import op  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("email = lower(email)", name=op.f("ck_users_email_lowercase")),
        sa.CheckConstraint("length(email) <= 254", name=op.f("ck_users_email_length")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "accounts",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("cash", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("starting_cash", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("cash >= 0", name=op.f("ck_accounts_cash_non_negative")),
        sa.CheckConstraint(
            "starting_cash >= 0", name=op.f("ck_accounts_starting_cash_non_negative")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_accounts_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_accounts")),
        sa.UniqueConstraint("user_id", name=op.f("uq_accounts_user_id")),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("accounts")
    op.drop_table("users")
