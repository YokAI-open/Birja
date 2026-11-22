"""Migration-only bounded all-user latch and canonical metadata backfill.

Revision ID: 0019
Revises: 0018

Writers must remain stopped through0020. Each batch is durable; restart at0018
after interruption. Failed concurrent index construction is inspected before
rebuilding ONLY the exact source-owned invalid index, never a foreign object.
"""

from collections.abc import Sequence
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | Sequence[str] | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
BATCH_SIZE = 500
SQL_SHA256 = "a26d4230843f75af9202fce71a771818d0bd7f041777a8a01a0d53a8df7a7c65"


def _sql_statements(source: str) -> list[str]:
    # Reuse the immutable reviewed parser, without rewriting its source/bytes.
    path = Path(__file__).with_name("0017_portfolio_ownership.py")
    spec = spec_from_file_location("portfolio_ownership_parser", path)
    module = module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("missing immutable portfolio SQL parser")
    spec.loader.exec_module(module)
    return module._statements(source)


def _preflight() -> None:
    bind = op.get_bind()
    if bind.execute(
        sa.text("""SELECT EXISTS(SELECT FROM accounts
        WHERE name IS DISTINCT FROM public.portfolio_display_name(name)
           OR description IS DISTINCT FROM public.portfolio_description(description)
           OR (name_key IS NOT NULL AND name_key IS DISTINCT FROM
               public.portfolio_name_key(name)))""")
    ).scalar_one():
        raise RuntimeError("noncanonical legacy portfolio metadata; no automatic rename")
    if bind.execute(
        sa.text("""SELECT EXISTS(SELECT user_id,
        public.portfolio_name_key(name) COLLATE pg_catalog.\"C\" FROM accounts
        WHERE closed_at IS NULL GROUP BY user_id,
        public.portfolio_name_key(name) COLLATE pg_catalog.\"C\" HAVING count(*)>1)""")
    ).scalar_one():
        raise RuntimeError("duplicate legacy active portfolio name; no automatic rename")
    if bind.execute(
        sa.text("""SELECT EXISTS(SELECT FROM portfolio_creations)
        OR EXISTS(SELECT FROM portfolio_initializations WHERE origin<>'legacy')""")
    ).scalar_one():
        raise RuntimeError("unexpected management evidence before legacy backfill")


def _backfill_batch(table: str) -> int:
    bind = op.get_bind()
    if table == "users":
        query = """WITH batch AS (SELECT u.id FROM users u WHERE NOT EXISTS(
            SELECT FROM portfolio_initializations i WHERE i.user_id=u.id)
            ORDER BY u.id LIMIT :batch), inserted AS (
            INSERT INTO portfolio_initializations(user_id,origin)
            SELECT id,'legacy' FROM batch ON CONFLICT(user_id) DO NOTHING RETURNING id)
            SELECT count(*) FROM inserted"""
    elif table == "accounts":
        query = """WITH batch AS (SELECT id FROM accounts WHERE name_key IS NULL
            ORDER BY id LIMIT :batch), updated AS (
            UPDATE accounts a SET name_key=public.portfolio_name_key(a.name)
            FROM batch b WHERE a.id=b.id AND a.name_key IS NULL RETURNING a.id)
            SELECT count(*) FROM updated"""
    else:
        raise ValueError("unknown fixed backfill table")
    return bind.execute(sa.text(query), {"batch": BATCH_SIZE}).scalar_one()


def _active_name_index() -> None:
    expected = (
        "CREATE UNIQUE INDEX uq_accounts_active_name ON public.accounts "
        "USING btree (user_id, name_key) WHERE (closed_at IS NULL)"
    )
    row = (
        op.get_bind()
        .execute(
            sa.text("""SELECT c.relkind::text AS kind,
        c.relowner=t.relowner AS table_owned,pg_get_userbyid(c.relowner)=current_user
        AS migration_owned,pg_get_indexdef(c.oid) AS definition,
        i.indisvalid,i.indisready,i.indislive,
        EXISTS(SELECT FROM pg_constraint WHERE conindid=c.oid) AS attached
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        JOIN pg_class t ON t.oid='public.accounts'::regclass
        LEFT JOIN pg_index i ON i.indexrelid=c.oid
        WHERE n.nspname='public' AND c.relname='uq_accounts_active_name'""")
        )
        .mappings()
        .one_or_none()
    )
    if row is not None and (
        row["kind"] != "i"
        or not row["table_owned"]
        or not row["migration_owned"]
        or not row["indislive"]
        or row["attached"]
        or row["definition"] != expected
    ):
        raise RuntimeError("incompatible preexisting portfolio active-name index")
    if row is None or not (row["indisvalid"] and row["indisready"]):
        with op.get_context().autocommit_block():
            if row is not None:
                op.drop_index(
                    "uq_accounts_active_name", table_name="accounts", postgresql_concurrently=True
                )
            op.create_index(
                "uq_accounts_active_name",
                "accounts",
                ["user_id", "name_key"],
                unique=True,
                postgresql_where=sa.text("closed_at IS NULL"),
                postgresql_concurrently=True,
            )


def upgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("management backfill requires online authenticated migration")
    if op.get_bind().execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator":
        raise RuntimeError("management backfill requires authenticated birja_migrator")
    data = (Path(__file__).resolve().parent.parent / "sql/0019_portfolio_metadata.sql").read_bytes()
    if sha256(data).hexdigest() != SQL_SHA256:
        raise RuntimeError("management metadata SQL asset checksum mismatch")
    for statement in _sql_statements(data.decode("utf-8")):
        op.execute(statement)
    _preflight()
    # Swap only the row guard, with a source-owned narrow UPDATE exception for
    # NULL→canonical key and full equality of EVERY other field, including money.
    op.execute("DROP TRIGGER portfolio_root_immutable ON public.accounts")
    op.execute(
        "CREATE TRIGGER portfolio_root_immutable BEFORE UPDATE ON public.accounts "
        "FOR EACH ROW EXECUTE FUNCTION public.associate_portfolio_metadata_only()"
    )
    with op.get_context().autocommit_block():
        for table in ("users", "accounts"):
            while _backfill_batch(table):
                pass
    _preflight()
    if (
        op.get_bind()
        .execute(
            sa.text("""SELECT EXISTS(SELECT FROM accounts WHERE name_key IS NULL)
        OR EXISTS(SELECT FROM users u WHERE NOT EXISTS(
        SELECT FROM portfolio_initializations i WHERE i.user_id=u.id))""")
        )
        .scalar_one()
    ):
        raise RuntimeError("incomplete portfolio management backfill")
    op.execute("DROP TRIGGER portfolio_root_immutable ON public.accounts")
    op.execute(
        "CREATE TRIGGER portfolio_root_immutable BEFORE UPDATE ON public.accounts "
        "FOR EACH ROW EXECUTE FUNCTION public.check_portfolio_financial_write()"
    )
    op.execute("DROP FUNCTION public.associate_portfolio_metadata_only()")
    op.alter_column("accounts", "name_key", nullable=False)
    # Constraints are installed transactionally after the resumable portion;
    # index construction below may itself be interrupted after this commit.
    for table in ("accounts", "portfolio_creations", "portfolio_initializations"):
        op.execute(f"DROP TRIGGER IF EXISTS portfolio_metadata_canonical ON public.{table}")
        op.execute(
            f"CREATE TRIGGER portfolio_metadata_canonical BEFORE INSERT OR UPDATE "
            f"ON public.{table} FOR EACH ROW "
            "EXECUTE FUNCTION public.check_portfolio_management_metadata()"
        )
    _active_name_index()


def downgrade() -> None:
    raise RuntimeError("management backfill downgrade refused before writes; provenance retained")
