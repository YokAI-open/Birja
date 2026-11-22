"""Backfill verified historical closure policy without inventing confirmation.

Revision ID:0022
Revises:0021

Migration-only maintenance: writers remain stopped through0023. Batches commit
independently; restart at0021 resumes only missing immutable retained boundaries.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession
from sqlalchemy.util import await_only

revision: str = "0022"
down_revision: str | Sequence[str] | None = "0021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
BATCH_SIZE = 500


def _preflight() -> None:
    bind = op.get_bind()
    # All curated instrument gates precede account/table locks. This is only a
    # stopped-writer migration, not an alternative public closure transaction.
    coins = list(
        bind.execute(
            sa.text("SELECT coin_id FROM public.stock_instruments ORDER BY coin_id")
        ).scalars()
    )
    if len(coins) > 20:
        raise RuntimeError("retained closure instrument inventory exceeded")
    for coin in coins:
        bind.execute(
            sa.text("""SELECT pg_advisory_xact_lock(hashtextextended(
            'birja.stock.instrument:' || CAST(:c AS text),0))"""),
            {"c": str(coin)},
        )
    bind.execute(
        sa.text("""LOCK TABLE public.accounts,public.holdings,public.trades,
        public.stock_ownership_movements,public.stock_split_applications,
        public.stock_action_state,public.portfolio_stock_closures,
        public.portfolio_lifecycle_closures,public.portfolio_closure_intents
        IN SHARE ROW EXCLUSIVE MODE""")
    )
    if bind.execute(
        sa.text("""SELECT EXISTS(SELECT FROM portfolio_closure_intents)
        OR EXISTS(SELECT FROM portfolio_lifecycle_closures c JOIN accounts a
          ON a.id=c.portfolio_id WHERE c.provenance<>'retained_boundary'
          OR c.confirmation_name IS NOT NULL OR c.intent_id IS NOT NULL
          OR (c.user_id,c.closed_at) IS DISTINCT FROM (a.user_id,a.closed_at)
          OR a.closed_at IS NULL)
        OR EXISTS(SELECT FROM portfolio_stock_closures c JOIN accounts a ON a.id=c.portfolio_id
          WHERE a.closed_at IS NULL OR (c.user_id,c.closed_at)
          IS DISTINCT FROM (a.user_id,a.closed_at))""")
    ).scalar_one():
        raise RuntimeError("invalid retained closure provenance")
    if bind.execute(
        sa.text("""WITH participation AS (
          SELECT portfolio_id,user_id,coin_id FROM stock_ownership_movements
          UNION SELECT h.portfolio_id,h.user_id,h.coin_id FROM holdings h
          JOIN stock_instruments s ON s.coin_id=h.coin_id)
        SELECT EXISTS(SELECT FROM participation p JOIN accounts a ON a.id=p.portfolio_id
          LEFT JOIN portfolio_stock_closures c
            ON (c.portfolio_id,c.coin_id)=(p.portfolio_id,p.coin_id)
          WHERE a.closed_at IS NOT NULL AND (c.id IS NULL OR c.user_id<>p.user_id))""")
    ).scalar_one():
        raise RuntimeError("missing retained closure stock boundary")
    involved = list(
        bind.execute(
            sa.text("""SELECT DISTINCT c.coin_id
        FROM portfolio_stock_closures c ORDER BY c.coin_id""")
        ).scalars()
    )
    # Reuse the complete qualified verifier on THIS connection/transaction,
    # including fill economics, global tails, unit/digest chains and holdings.
    # No copied partial validator and no external connection can miss uncommitted
    # migration evidence. SQLAlchemy's async proxy is documented as a thin
    # wrapper reconstructable from its sync engine/connection.
    async_bind = AsyncConnection(AsyncEngine(bind.engine), sync_connection=bind)
    from app.services.stock_ownership import OwnershipHeld, assert_ownership_consistent

    async def validate() -> None:
        for coin in involved:
            async with AsyncSession(bind=async_bind) as session:
                await assert_ownership_consistent(session, coin)

    try:
        await_only(validate())
    except OwnershipHeld as exc:
        raise RuntimeError("invalid retained closure stock history") from exc


def _backfill_batch() -> int:
    return (
        op.get_bind()
        .execute(
            sa.text("""WITH batch AS (
        SELECT a.id,a.user_id,a.closed_at FROM accounts a WHERE a.closed_at IS NOT NULL
        AND NOT EXISTS(SELECT FROM portfolio_lifecycle_closures c WHERE c.portfolio_id=a.id)
        ORDER BY a.id LIMIT :size), inserted AS (
        INSERT INTO portfolio_lifecycle_closures
          (portfolio_id,user_id,closed_at,policy_version,provenance)
        SELECT id,user_id,closed_at,'freeze_at_closure_v1','retained_boundary' FROM batch
        RETURNING id) SELECT count(*) FROM inserted"""),
            {"size": BATCH_SIZE},
        )
        .scalar_one()
    )


ROOT_GUARD_SQL = """CREATE FUNCTION public.check_portfolio_terminal_root()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path=pg_catalog,public,pg_temp AS $terminal$
BEGIN
  IF NEW.closed_at IS NULL THEN
    IF EXISTS(SELECT FROM public.portfolio_lifecycle_closures WHERE portfolio_id=NEW.id) THEN
      RAISE EXCEPTION 'active portfolio has terminal evidence' USING ERRCODE='23514';
    END IF;
  ELSIF NOT EXISTS(SELECT FROM public.portfolio_lifecycle_closures c
      WHERE (c.portfolio_id,c.user_id,c.closed_at)=(NEW.id,NEW.user_id,NEW.closed_at)) THEN
    RAISE EXCEPTION 'missing portfolio lifecycle boundary' USING ERRCODE='23514';
  END IF;
  RETURN NEW;
END $terminal$"""


def upgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("closure backfill requires online authenticated migration")
    if op.get_bind().execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator":
        raise RuntimeError("closure backfill requires authenticated birja_migrator")
    op.execute("SET LOCAL lock_timeout='5s'")
    op.execute("SET LOCAL statement_timeout='30s'")
    _preflight()
    with op.get_context().autocommit_block():
        while _backfill_batch():
            pass
    _preflight()
    if (
        op.get_bind()
        .execute(
            sa.text("""SELECT EXISTS(SELECT FROM accounts a
        WHERE a.closed_at IS NOT NULL AND NOT EXISTS(SELECT FROM portfolio_lifecycle_closures c
        WHERE (c.portfolio_id,c.user_id,c.closed_at)=(a.id,a.user_id,a.closed_at)))""")
        )
        .scalar_one()
    ):
        raise RuntimeError("incomplete retained closure backfill")
    op.execute("""ALTER TABLE public.portfolio_stock_closures
        ADD CONSTRAINT fk_portfolio_stock_closure_lifecycle
        FOREIGN KEY(portfolio_id,user_id,closed_at)
        REFERENCES public.portfolio_lifecycle_closures(portfolio_id,user_id,closed_at)
        DEFERRABLE INITIALLY DEFERRED NOT VALID""")
    op.execute("""ALTER TABLE public.portfolio_stock_closures
        VALIDATE CONSTRAINT fk_portfolio_stock_closure_lifecycle""")
    op.execute(ROOT_GUARD_SQL)
    op.execute("REVOKE ALL ON FUNCTION public.check_portfolio_terminal_root() FROM PUBLIC")
    op.execute("""CREATE CONSTRAINT TRIGGER portfolio_terminal_root
        AFTER INSERT OR UPDATE ON public.accounts DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW EXECUTE FUNCTION public.check_portfolio_terminal_root()""")


def downgrade() -> None:
    raise RuntimeError("closure provenance downgrade refused before writes; evidence retained")
