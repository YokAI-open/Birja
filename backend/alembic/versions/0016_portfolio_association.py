"""Migration-only, bounded legacy portfolio association with durable batch progress.

Revision ID: 0016
Revises: 0015
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | Sequence[str] | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# A fixed causal order. Global split applications are deliberately absent.
OWNED_KEYS = (
    ("holdings", "id"),
    ("trades", "id"),
    ("stock_fill_facts", "trade_id"),
    ("stock_ownership_movements", "id"),
    ("stock_dividend_entitlements", "id"),
    ("stock_dividend_payments", "id"),
    ("stock_dividend_decisions", "id"),
)
BATCH_SIZE = 500


def _validate_lineage() -> None:
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator":
        raise RuntimeError("portfolio association requires authenticated birja_migrator")
    for table, _ in OWNED_KEYS:
        invalid = bind.execute(
            sa.text(
                f"SELECT EXISTS(SELECT FROM public.{table} r "  # noqa: S608 - fixed migration/test allowlist
                "LEFT JOIN public.accounts a ON a.user_id=r.user_id "
                "WHERE a.id IS NULL OR (r.portfolio_id IS NOT NULL "
                "AND r.portfolio_id<>a.id) OR "
                "(SELECT count(*) FROM public.accounts x WHERE x.user_id=r.user_id)<>1)"
            )
        ).scalar_one()
        if invalid:
            raise RuntimeError("missing, ambiguous or contradictory legacy portfolio lineage")
    # Validate old causes explicitly before the first committed batch; do not
    # infer owner from an unrelated valid primary key or repair contradictory data.
    for query in (
        "SELECT FROM stock_fill_facts f JOIN trades t ON t.id=f.trade_id "
        "WHERE (f.user_id,f.coin_id) IS DISTINCT FROM (t.user_id,t.coin_id)",
        "SELECT FROM stock_ownership_movements m JOIN trades t ON t.id=m.trade_id "
        "WHERE (m.user_id,m.coin_id) IS DISTINCT FROM (t.user_id,t.coin_id)",
        "SELECT FROM stock_dividend_payments p JOIN stock_dividend_entitlements e "
        "ON e.id=p.entitlement_id WHERE (p.user_id,p.event_id) "
        "IS DISTINCT FROM (e.user_id,e.event_id)",
        "SELECT FROM stock_dividend_decisions d JOIN stock_dividend_payments p "
        "ON p.id=d.payment_id WHERE (d.user_id,d.event_id,d.coin_id) "
        "IS DISTINCT FROM (p.user_id,p.event_id,p.coin_id)",
    ):
        if bind.execute(sa.text(f"SELECT EXISTS({query})")).scalar_one():
            raise RuntimeError("contradictory legacy portfolio cause")


def upgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("portfolio association requires online authenticated migration")
    _validate_lineage()
    # Each UPDATE commits independently. Its non-NULL association is the durable
    # per-row checkpoint: interruption re-enters only unassociated keys. The
    # finite trigger prevents changing any other field or reassigning a row.
    with op.get_context().autocommit_block():
        bind = op.get_bind()
        for table, key in OWNED_KEYS:
            while True:
                changed = bind.execute(
                    sa.text(
                        f"WITH batch AS (SELECT {key} FROM public.{table} "  # noqa: S608 - fixed migration/test allowlist
                        f"WHERE portfolio_id IS NULL ORDER BY {key} LIMIT :batch), "
                        f"associated AS (UPDATE public.{table} r SET portfolio_id=a.id "
                        "FROM public.accounts a,batch b "
                        f"WHERE r.{key}=b.{key} AND a.user_id=r.user_id "
                        f"AND r.portfolio_id IS NULL RETURNING r.{key}) "
                        "SELECT count(*) FROM associated"
                    ),
                    {"batch": BATCH_SIZE},
                ).scalar_one()
                if changed == 0:
                    break
    _validate_lineage()
    for table, _ in OWNED_KEYS:
        if (
            op.get_bind()
            .execute(
                sa.text(f"SELECT EXISTS(SELECT FROM public.{table} WHERE portfolio_id IS NULL)")  # noqa: S608 - fixed migration/test allowlist
            )
            .scalar_one()
        ):
            raise RuntimeError("incomplete legacy portfolio association")


def downgrade() -> None:
    raise RuntimeError("portfolio association downgrade refused before writes; migrate to final")
