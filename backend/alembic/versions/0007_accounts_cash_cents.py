"""accounts cash whole cents

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-28 21:10:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ck_accounts_cash_cents, refusing to run if existing rows break it."""
    accounts = sa.table("accounts", sa.column("cash", sa.Numeric(20, 8)))
    bad = (
        op.get_bind()
        .execute(
            sa.select(sa.func.count())
            .select_from(accounts)
            .where(accounts.c.cash != sa.func.round(accounts.c.cash, 2))
        )
        .scalar_one()
    )
    if bad > 0:
        raise RuntimeError(
            f"accounts has {bad} rows with sub-cent cash; fix them in a data migration "
            "before adding ck_accounts_cash_cents"
        )
    # Tiny table, so the brief ACCESS EXCLUSIVE lock while validating is acceptable.
    op.create_check_constraint(op.f("ck_accounts_cash_cents"), "accounts", "cash = round(cash, 2)")


def downgrade() -> None:
    """Drop ck_accounts_cash_cents."""
    op.drop_constraint(op.f("ck_accounts_cash_cents"), "accounts", type_="check")
