"""Permit reviewed OpenFIGI NYSE listing provenance.

Revision ID: 0027
Revises: 0026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | Sequence[str] | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PREVIOUS_SOURCES = "source IN ('nasdaqlisted', 'otherlisted')"
CURRENT_SOURCES = PREVIOUS_SOURCES + " OR (source = 'openfigi_nyse' AND listing_exchange = 'NYSE')"


def _replace_constraint(predicate: str) -> None:
    if (
        op.get_context().as_sql
        or not op.get_bind()
        .execute(sa.text("SELECT session_user = 'birja_migrator' AND current_user = session_user"))
        .scalar_one()
    ):
        raise RuntimeError("Catalog provenance migration requires authenticated birja_migrator")
    constraint = op.f("ck_stock_catalog_listings_source_known")
    op.drop_constraint(constraint, "stock_catalog_listings", type_="check", schema="public")
    op.create_check_constraint(constraint, "stock_catalog_listings", predicate, schema="public")


def upgrade() -> None:
    _replace_constraint(CURRENT_SOURCES)


def downgrade() -> None:
    # The old constraint rejects a downgrade once a new-source row exists.
    _replace_constraint(PREVIOUS_SOURCES)
