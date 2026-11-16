"""Migration-only portfolio expansion; no runnable service revision.

Revision ID: 0015
Revises: 0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | Sequence[str] | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNED_TABLES = (
    "holdings",
    "trades",
    "stock_fill_facts",
    "stock_ownership_movements",
    "stock_dividend_entitlements",
    "stock_dividend_payments",
    "stock_dividend_decisions",
)

# Replacing the BEFORE mutation triggers does not replace the retained deferred
# fill-integrity or dividend INSERT-link checks. No global event is associable.
ASSOCIATION_GUARD = """CREATE FUNCTION public.associate_legacy_portfolio_only()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER
SET search_path=pg_catalog,public,pg_temp AS $association$
DECLARE original_root bigint; roots bigint;
BEGIN
 IF TG_OP='UPDATE' AND TG_TABLE_SCHEMA='public'
 AND TG_TABLE_NAME IN ('holdings','trades','stock_fill_facts',
   'stock_ownership_movements','stock_dividend_entitlements',
   'stock_dividend_payments','stock_dividend_decisions')
 AND session_user='birja_migrator' THEN
   SELECT count(*),min(id) INTO roots,original_root
     FROM public.accounts WHERE user_id=OLD.user_id;
   IF roots=1 AND OLD.portfolio_id IS NULL
   AND NEW.portfolio_id=original_root
   AND to_jsonb(NEW)-'portfolio_id'=to_jsonb(OLD)-'portfolio_id' THEN
     RETURN NEW;
   END IF;
 END IF;
 RAISE EXCEPTION 'immutable portfolio association rejected' USING ERRCODE='23514';
END $association$"""


def _prepare_account_identity() -> None:
    name = "uq_accounts_id_user"
    existing = None
    if not op.get_context().as_sql:
        existing = (
            op.get_bind()
            .execute(
                sa.text("""SELECT c.relkind::text AS kind,
                c.relowner=t.relowner AS table_owned,
                pg_get_userbyid(c.relowner)=current_user AS migration_owned,
                pg_get_indexdef(c.oid) AS definition,i.indisvalid,i.indisready,i.indislive,
                EXISTS(SELECT FROM pg_constraint WHERE conindid=c.oid) AS attached
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                JOIN pg_class t ON t.oid='public.accounts'::regclass
                LEFT JOIN pg_index i ON i.indexrelid=c.oid
                WHERE n.nspname='public' AND c.relname=:name"""),
                {"name": name},
            )
            .mappings()
            .one_or_none()
        )
        if existing is not None and (
            existing["kind"] != "i"
            or not existing["table_owned"]
            or not existing["migration_owned"]
            or not existing["indislive"]
            or existing["attached"]
            or existing["definition"]
            != (
                "CREATE UNIQUE INDEX uq_accounts_id_user ON public.accounts "
                "USING btree (id, user_id)"
            )
        ):
            raise RuntimeError("incompatible preexisting portfolio root index")
    if existing is None or not (existing["indisvalid"] and existing["indisready"]):
        with op.get_context().autocommit_block():
            if existing is not None:
                op.drop_index(name, table_name="accounts", postgresql_concurrently=True)
            op.create_index(
                name, "accounts", ["id", "user_id"], unique=True, postgresql_concurrently=True
            )


def upgrade() -> None:
    _prepare_account_identity()
    op.execute(
        "ALTER TABLE public.accounts ADD CONSTRAINT uq_accounts_id_user "
        "UNIQUE USING INDEX uq_accounts_id_user"
    )
    op.add_column(
        "accounts", sa.Column("name", sa.Text(), server_default="My portfolio", nullable=False)
    )
    op.add_column("accounts", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))
    # Keep unique(accounts.user_id) throughout the migration-only stages.
    for table in OWNED_TABLES:
        op.add_column(table, sa.Column("portfolio_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "stock_split_applications",
        sa.Column("owner_digest_version", sa.SmallInteger(), nullable=True),
    )
    op.create_check_constraint(
        "owner_digest_version_known",
        "stock_split_applications",
        "owner_digest_version IS NULL OR owner_digest_version=2",
    )
    op.create_table(
        "portfolio_stock_closures",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("portfolio_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("coin_id", sa.BigInteger(), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closing_sequence", sa.BigInteger(), nullable=False),
        sa.Column("unit_epoch", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_portfolio_stock_closures"),
        sa.UniqueConstraint("portfolio_id", "coin_id", name="uq_portfolio_stock_closure_root_coin"),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["accounts.id", "accounts.user_id"],
            name="fk_portfolio_stock_closure_owner",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["coin_id"], ["stock_instruments.coin_id"]),
        sa.CheckConstraint(
            "closing_sequence BETWEEN 0 AND 9007199254740991", name="closing_sequence_safe"
        ),
        sa.CheckConstraint("unit_epoch BETWEEN 0 AND 9007199254740991", name="unit_epoch_safe"),
    )
    op.create_index("ix_portfolio_stock_closures_user_id", "portfolio_stock_closures", ["user_id"])
    op.create_index("ix_portfolio_stock_closures_coin_id", "portfolio_stock_closures", ["coin_id"])
    op.execute(ASSOCIATION_GUARD)
    op.execute("ALTER FUNCTION public.associate_legacy_portfolio_only() OWNER TO birja_migrator")
    op.execute("REVOKE ALL ON FUNCTION public.associate_legacy_portfolio_only() FROM PUBLIC")
    for table in OWNED_TABLES:
        if table in {"trades", "stock_fill_facts", "stock_ownership_movements"}:
            trigger = "stock_record_immutable"
        elif table in {"stock_dividend_payments", "stock_dividend_decisions"}:
            trigger = "stock_dividend_immutable"
        else:
            trigger = "portfolio_association_only"
        op.execute(f"DROP TRIGGER IF EXISTS {trigger} ON public.{table}")
        op.execute(
            f"CREATE TRIGGER {trigger} BEFORE UPDATE OR DELETE ON public.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.associate_legacy_portfolio_only()"
        )
    for table in ("stock_split_applications", "portfolio_stock_closures"):
        op.execute(
            f"CREATE TRIGGER portfolio_record_immutable BEFORE UPDATE OR DELETE ON public.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.reject_stock_dividend_mutation()"
        )
    op.execute("REVOKE ALL ON public.portfolio_stock_closures FROM PUBLIC")
    op.execute("REVOKE ALL ON SEQUENCE public.portfolio_stock_closures_id_seq FROM PUBLIC")


def downgrade() -> None:
    # Reversing this stage can remove retained identity/terminal evidence. Do not
    # perform even an initial DROP before the operator chooses a qualified path.
    raise RuntimeError("portfolio expansion downgrade refused; migration-to-final required")
