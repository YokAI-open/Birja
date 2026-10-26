"""baseline

Revision ID: 0001
Revises:
"""

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Intentionally empty: establishes the migration history (no domain tables yet)."""


def downgrade() -> None:
    """Intentionally empty: the baseline has nothing to undo."""
