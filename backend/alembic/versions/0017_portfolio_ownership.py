"""Finalize owned financial lineage; intermediate revisions are migration-only.

Revision ID: 0017
Revises: 0016
"""

from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | Sequence[str] | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OWNED = (
    "holdings",
    "trades",
    "stock_fill_facts",
    "stock_ownership_movements",
    "stock_dividend_entitlements",
    "stock_dividend_payments",
    "stock_dividend_decisions",
)
SQL_ASSETS = {
    "0017_stock_portfolio.sql": "265262fa8377b801605867ebe692accd43acc29a8764f401633ffdabff25383e",
    "0017_dividend_portfolio.sql": (
        "fc5cb6864bb553c5116f2580a79ece2ea86188aba6eb309af857b68b88918734"
    ),
}


def upgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("portfolio finalization requires online validated migration")
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT session_user")).scalar_one() != "birja_migrator":
        raise RuntimeError("portfolio finalization requires authenticated birja_migrator")
    for table in OWNED:
        if bind.execute(
            sa.text(
                f"SELECT EXISTS(SELECT FROM public.{table} r LEFT JOIN public.accounts a "  # noqa: S608
                "ON (a.id,a.user_id)=(r.portfolio_id,r.user_id) WHERE a.id IS NULL)"
            )
        ).scalar_one():
            raise RuntimeError("incomplete or mismatched portfolio lineage")
    _constraints()
    for table in OWNED:
        op.alter_column(table, "portfolio_id", nullable=False)
    for table in OWNED:
        trigger = (
            "stock_record_immutable"
            if table in {"trades", "stock_fill_facts", "stock_ownership_movements"}
            else "stock_dividend_immutable"
            if table in {"stock_dividend_payments", "stock_dividend_decisions"}
            else "portfolio_association_only"
        )
        op.execute(f"DROP TRIGGER {trigger} ON public.{table}")
        if table != "holdings":
            op.execute(
                f"CREATE TRIGGER {trigger} BEFORE UPDATE OR DELETE ON public.{table} "
                "FOR EACH ROW EXECUTE FUNCTION public.reject_stock_dividend_mutation()"
            )
    op.execute("DROP FUNCTION public.associate_legacy_portfolio_only()")
    sources = []
    for asset, digest in SQL_ASSETS.items():
        data = (Path(__file__).resolve().parent.parent / "sql" / asset).read_bytes()
        if sha256(data).hexdigest() != digest:
            raise RuntimeError("immutable portfolio SQL asset checksum mismatch")
        sources.append(data.decode("utf-8"))
    for source in sources:
        # The driver supports one statement at a time; the fixed source uses
        # dollar-quoted routine bodies, split by the migration's SQL parser.
        for statement in _statements(source):
            op.execute(statement)
    op.execute("""CREATE FUNCTION public.check_portfolio_financial_write()
    RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
    SET search_path=pg_catalog,public,pg_temp AS $root$
    DECLARE r public.accounts%ROWTYPE;
    BEGIN
      IF TG_TABLE_NAME='accounts' THEN
        IF (NEW.id,NEW.user_id) IS DISTINCT FROM (OLD.id,OLD.user_id)
        OR (OLD.closed_at IS NOT NULL AND NEW IS DISTINCT FROM OLD) THEN
          RAISE EXCEPTION 'immutable closed portfolio' USING ERRCODE='23514'; END IF;
        RETURN NEW;
      END IF;
      IF TG_OP='UPDATE' THEN
        IF (NEW.portfolio_id,NEW.user_id) IS DISTINCT FROM (OLD.portfolio_id,OLD.user_id) THEN
          RAISE EXCEPTION 'immutable portfolio identity' USING ERRCODE='23514'; END IF;
        IF TG_TABLE_NAME='holdings' THEN
          IF NEW.coin_id<>OLD.coin_id THEN
            RAISE EXCEPTION 'immutable portfolio holding' USING ERRCODE='23514'; END IF;
        END IF;
      END IF;
      IF TG_OP='DELETE' THEN
        SELECT * INTO r FROM public.accounts WHERE (id,user_id)=(OLD.portfolio_id,OLD.user_id)
          FOR UPDATE;
      ELSE
        SELECT * INTO r FROM public.accounts WHERE (id,user_id)=(NEW.portfolio_id,NEW.user_id)
          FOR UPDATE;
      END IF;
      IF r.id IS NULL THEN RETURN NEW; END IF; -- paired FK supplies23503
      IF r.closed_at IS NOT NULL THEN
        RAISE EXCEPTION 'portfolio unavailable' USING ERRCODE='23514'; END IF;
      IF TG_OP='DELETE' THEN RETURN OLD; ELSE RETURN NEW; END IF;
    END $root$""")
    op.execute("REVOKE ALL ON FUNCTION public.check_portfolio_financial_write() FROM PUBLIC")
    op.execute(
        "CREATE TRIGGER portfolio_root_immutable BEFORE UPDATE ON public.accounts "
        "FOR EACH ROW EXECUTE FUNCTION public.check_portfolio_financial_write()"
    )
    for table in OWNED:
        op.execute(
            f"CREATE TRIGGER portfolio_active_write BEFORE INSERT ON public.{table} "
            "FOR EACH ROW EXECUTE FUNCTION public.check_portfolio_financial_write()"
        )
    op.execute(
        "CREATE TRIGGER portfolio_holding_mutation BEFORE UPDATE OR DELETE ON public.holdings "
        "FOR EACH ROW EXECUTE FUNCTION public.check_portfolio_financial_write()"
    )
    if not bind.execute(
        sa.text(
            "SELECT has_schema_privilege('birja_app','public','USAGE') "
            "AND has_schema_privilege('birja_scheduler','public','USAGE')"
        )
    ).scalar_one():
        raise RuntimeError("preprovision restricted runtime schema usage before finalization")
    # Explicit read inventory; mutation is restricted to existing domain paths.
    op.execute("GRANT SELECT ON public.alembic_version TO birja_app,birja_scheduler")
    op.execute(
        "GRANT SELECT ON public.accounts,public.coins,public.prices,public.holdings,"
        "public.trades,public.stock_instruments,public.stock_quotes,public.stock_sessions,"
        "public.stock_data_admissions,public.stock_action_events,public.stock_action_sources,"
        "public.stock_action_revisions,public.stock_action_observations,public.stock_action_state,"
        "public.stock_split_applications,public.stock_ownership_movements,"
        "public.stock_dividend_entitlements,public.stock_action_resolutions,"
        "public.stock_fill_facts,public.stock_status_evidence,public.stock_dividend_payments,"
        "public.stock_dividend_decisions,public.portfolio_stock_closures "
        "TO birja_app,birja_scheduler"
    )
    op.execute(
        "GRANT INSERT ON public.trades,public.holdings,public.stock_fill_facts,"
        "public.stock_ownership_movements TO birja_app"
    )
    op.execute(
        "GRANT USAGE ON SEQUENCE public.trades_id_seq,public.holdings_id_seq,"
        "public.stock_ownership_movements_id_seq TO birja_app"
    )
    op.execute("REVOKE UPDATE ON public.accounts,public.holdings FROM birja_app")
    op.execute("GRANT UPDATE(cash) ON public.accounts TO birja_app")
    op.execute("GRANT UPDATE(quantity,cost_basis) ON public.holdings TO birja_app")
    op.drop_constraint("uq_accounts_user_id", "accounts", type_="unique")


def _statements(source: str) -> list[str]:
    """Split fixed checked-in SQL while retaining dollar-quoted routine bodies."""
    import re

    result, start, quote = [], 0, None
    token = re.compile(r"\$[A-Za-z_]*\$|'(?:''|[^'])*'|--[^\n]*|;")
    for match in token.finditer(source):
        value = match.group()
        if value.startswith("$"):
            if quote is None:
                quote = value
            elif quote == value:
                quote = None
        elif value == ";" and quote is None:
            statement = source[start : match.start()].strip()
            if statement:
                result.append(statement)
            start = match.end()
    if source[start:].strip():
        result.append(source[start:].strip())
    if quote is not None:
        raise RuntimeError("unterminated immutable SQL asset")
    return result


def _index(table: str, name: str, columns: tuple[str, ...], *, unique: bool = False) -> None:
    """Prepare only fixed owned indexes, recover invalid concurrent remnants."""
    bind = op.get_bind()
    existing = (
        bind.execute(
            sa.text("""SELECT c.relkind::text,
        pg_get_userbyid(c.relowner)=current_user AS owned,
        i.indrelid=to_regclass(:table) AS correct_table,
        i.indisvalid,i.indisready,i.indislive,pg_get_indexdef(c.oid) AS definition,
        EXISTS(SELECT FROM pg_constraint WHERE conindid=c.oid) AS attached
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        LEFT JOIN pg_index i ON i.indexrelid=c.oid
        WHERE n.nspname='public' AND c.relname=:name"""),
            {"table": "public." + table, "name": name},
        )
        .mappings()
        .one_or_none()
    )
    expected = (
        f"CREATE {'UNIQUE ' if unique else ''}INDEX {name} ON public.{table} "
        f"USING btree ({', '.join(columns)})"
    )
    previous = (
        "CREATE INDEX ix_stock_entitlement_current_work ON "
        "public.stock_dividend_entitlements USING btree (event_id, user_id, id)"
    )
    if existing is not None:
        definitions = {expected}
        if name == "ix_stock_entitlement_current_work":
            definitions.add(previous)
        if (
            existing["relkind"] != "i"
            or not existing["owned"]
            or not existing["correct_table"]
            or not existing["indislive"]
            or existing["attached"]
            or existing["definition"] not in definitions
        ):
            raise RuntimeError("incompatible preexisting portfolio index")
        if existing["indisvalid"] and existing["indisready"] and existing["definition"] == expected:
            return
    with op.get_context().autocommit_block():
        if existing is not None:
            op.drop_index(name, table_name=table, postgresql_concurrently=True)
        op.create_index(name, table, list(columns), unique=unique, postgresql_concurrently=True)


def _unique(table: str, name: str, columns: tuple[str, ...]) -> None:
    _index(table, name, columns, unique=True)
    op.execute(f"ALTER TABLE public.{table} ADD CONSTRAINT {name} UNIQUE USING INDEX {name}")


def _constraints() -> None:
    """Fixed final constraint definitions, never imported from application models."""
    # Drop causal FKs before replacing their referenced candidate keys.
    op.execute("ALTER TABLE public.holdings DROP CONSTRAINT IF EXISTS fk_holdings_portfolio_owner")
    op.execute("ALTER TABLE public.trades DROP CONSTRAINT IF EXISTS fk_trades_portfolio_owner")
    op.execute(
        "ALTER TABLE public.stock_fill_facts DROP CONSTRAINT IF EXISTS "
        "fk_stock_fill_portfolio_owner"
    )
    op.execute(
        "ALTER TABLE public.stock_fill_facts DROP CONSTRAINT IF EXISTS "
        "fk_stock_fill_trade_owner_coin"
    )
    op.execute(
        "ALTER TABLE public.stock_ownership_movements DROP CONSTRAINT IF EXISTS "
        "fk_stock_ownership_portfolio_owner"
    )
    op.execute(
        "ALTER TABLE public.stock_ownership_movements DROP CONSTRAINT IF EXISTS "
        "fk_stock_ownership_trade_owner_coin"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_entitlements DROP CONSTRAINT IF "
        "EXISTS fk_stock_entitlement_portfolio_owner"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_entitlements DROP CONSTRAINT IF "
        "EXISTS fk_stock_entitlement_supersedes_owner_event"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_payments DROP CONSTRAINT IF EXISTS "
        "fk_dividend_payment_portfolio_owner"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_payments DROP CONSTRAINT IF EXISTS "
        "fk_dividend_payment_entitlement_identity"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_decisions DROP CONSTRAINT IF EXISTS "
        "fk_dividend_decision_portfolio_owner"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_decisions DROP CONSTRAINT IF EXISTS "
        "fk_dividend_decision_previous_owner"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_decisions DROP CONSTRAINT IF EXISTS "
        "fk_dividend_decision_entitlement_identity"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_decisions DROP CONSTRAINT IF EXISTS "
        "fk_dividend_decision_payment_owner"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_decisions DROP CONSTRAINT IF EXISTS "
        "fk_dividend_decision_application_owner"
    )
    op.execute("ALTER TABLE public.holdings DROP CONSTRAINT IF EXISTS uq_holdings_portfolio_coin")
    op.execute(
        "ALTER TABLE public.trades DROP CONSTRAINT IF EXISTS uq_trades_id_portfolio_coin_user"
    )
    op.execute(
        "ALTER TABLE public.stock_ownership_movements DROP CONSTRAINT IF EXISTS "
        "uq_stock_ownership_application_portfolio"
    )
    op.execute(
        "ALTER TABLE public.stock_ownership_movements DROP CONSTRAINT IF EXISTS "
        "uq_stock_ownership_cause"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_entitlements DROP CONSTRAINT IF "
        "EXISTS uq_stock_entitlement_id_event_user"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_entitlements DROP CONSTRAINT IF "
        "EXISTS uq_stock_entitlement_dividend_identity"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_entitlements DROP CONSTRAINT IF "
        "EXISTS uq_stock_entitlement_revision_fingerprint"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_payments DROP CONSTRAINT IF EXISTS "
        "uq_stock_dividend_payment_event_portfolio"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_payments DROP CONSTRAINT IF EXISTS "
        "uq_stock_dividend_payment_owner_event_coin"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_decisions DROP CONSTRAINT IF EXISTS "
        "uq_stock_dividend_decision_lineage"
    )
    op.execute("ALTER TABLE public.holdings DROP CONSTRAINT IF EXISTS uq_holdings_user_coin")
    op.execute(
        "ALTER TABLE public.stock_ownership_movements DROP CONSTRAINT IF EXISTS "
        "uq_stock_ownership_application_user"
    )
    op.execute(
        "ALTER TABLE public.stock_dividend_payments DROP CONSTRAINT IF EXISTS "
        "uq_stock_dividend_payment_event_user"
    )
    _unique("holdings", "uq_holdings_portfolio_coin", ("portfolio_id", "coin_id"))
    _unique(
        "trades", "uq_trades_id_portfolio_coin_user", ("id", "portfolio_id", "coin_id", "user_id")
    )
    _unique(
        "stock_ownership_movements",
        "uq_stock_ownership_application_portfolio",
        ("application_id", "portfolio_id"),
    )
    _unique(
        "stock_ownership_movements",
        "uq_stock_ownership_cause",
        ("coin_id", "causal_key", "portfolio_id"),
    )
    _unique(
        "stock_dividend_entitlements",
        "uq_stock_entitlement_id_event_user",
        ("id", "event_id", "portfolio_id", "user_id"),
    )
    _unique(
        "stock_dividend_entitlements",
        "uq_stock_entitlement_dividend_identity",
        ("id", "event_id", "portfolio_id", "user_id", "revision_id", "fingerprint"),
    )
    _unique(
        "stock_dividend_entitlements",
        "uq_stock_entitlement_revision_fingerprint",
        ("event_id", "portfolio_id", "revision_id", "fingerprint"),
    )
    _unique(
        "stock_dividend_payments",
        "uq_stock_dividend_payment_event_portfolio",
        ("event_id", "portfolio_id"),
    )
    _unique(
        "stock_dividend_payments",
        "uq_stock_dividend_payment_owner_event_coin",
        ("id", "event_id", "portfolio_id", "user_id", "coin_id"),
    )
    _unique(
        "stock_dividend_decisions",
        "uq_stock_dividend_decision_lineage",
        ("id", "payment_id", "portfolio_id", "user_id", "event_id"),
    )
    op.execute(
        "ALTER TABLE holdings ADD CONSTRAINT fk_holdings_portfolio_owner FOREIGN "
        "KEY(portfolio_id, user_id) REFERENCES accounts (id, user_id)"
    )
    op.execute(
        "ALTER TABLE trades ADD CONSTRAINT fk_trades_portfolio_owner FOREIGN "
        "KEY(portfolio_id, user_id) REFERENCES accounts (id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_fill_facts ADD CONSTRAINT "
        "fk_stock_fill_portfolio_owner FOREIGN KEY(portfolio_id, user_id) "
        "REFERENCES accounts (id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_fill_facts ADD CONSTRAINT "
        "fk_stock_fill_trade_owner_coin FOREIGN KEY(trade_id, portfolio_id, "
        "coin_id, user_id) REFERENCES trades (id, portfolio_id, coin_id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_ownership_movements ADD CONSTRAINT "
        "fk_stock_ownership_portfolio_owner FOREIGN KEY(portfolio_id, user_id) "
        "REFERENCES accounts (id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_ownership_movements ADD CONSTRAINT "
        "fk_stock_ownership_trade_owner_coin FOREIGN KEY(trade_id, portfolio_id, "
        "coin_id, user_id) REFERENCES trades (id, portfolio_id, coin_id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_entitlements ADD CONSTRAINT "
        "fk_stock_entitlement_portfolio_owner FOREIGN KEY(portfolio_id, user_id) "
        "REFERENCES accounts (id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_entitlements ADD CONSTRAINT "
        "fk_stock_entitlement_supersedes_owner_event FOREIGN KEY(supersedes_id, "
        "event_id, portfolio_id, user_id) REFERENCES stock_dividend_entitlements "
        "(id, event_id, portfolio_id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_payments ADD CONSTRAINT "
        "fk_dividend_payment_portfolio_owner FOREIGN KEY(portfolio_id, user_id) "
        "REFERENCES accounts (id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_payments ADD CONSTRAINT "
        "fk_dividend_payment_entitlement_identity FOREIGN KEY(entitlement_id, "
        "event_id, portfolio_id, user_id, revision_id, entitlement_fingerprint) "
        "REFERENCES stock_dividend_entitlements (id, event_id, portfolio_id, "
        "user_id, revision_id, fingerprint)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_decisions ADD CONSTRAINT "
        "fk_dividend_decision_portfolio_owner FOREIGN KEY(portfolio_id, user_id) "
        "REFERENCES accounts (id, user_id)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_decisions ADD CONSTRAINT "
        "fk_dividend_decision_previous_owner FOREIGN KEY(previous_decision_id, "
        "payment_id, portfolio_id, user_id, event_id) REFERENCES "
        "stock_dividend_decisions (id, payment_id, portfolio_id, user_id, "
        "event_id)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_decisions ADD CONSTRAINT "
        "fk_dividend_decision_entitlement_identity FOREIGN KEY(entitlement_id, "
        "event_id, portfolio_id, user_id, revision_id, entitlement_fingerprint) "
        "REFERENCES stock_dividend_entitlements (id, event_id, portfolio_id, "
        "user_id, revision_id, fingerprint)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_decisions ADD CONSTRAINT "
        "fk_dividend_decision_payment_owner FOREIGN KEY(payment_id, event_id, "
        "portfolio_id, user_id, coin_id) REFERENCES stock_dividend_payments (id, "
        "event_id, portfolio_id, user_id, coin_id)"
    )
    op.execute(
        "ALTER TABLE stock_dividend_decisions ADD CONSTRAINT "
        "fk_dividend_decision_application_owner FOREIGN "
        "KEY(previous_application_id, payment_id, portfolio_id, user_id, "
        "event_id) REFERENCES stock_dividend_decisions (id, payment_id, "
        "portfolio_id, user_id, event_id)"
    )
    _index("accounts", "ix_accounts_user_id", ("user_id",))
    _index("holdings", "ix_holdings_user_id", ("user_id",))
    _index("trades", "ix_trades_portfolio_created_id", ("portfolio_id", "created_at", "id"))
    _index("stock_fill_facts", "ix_stock_fill_facts_portfolio_id", ("portfolio_id",))
    _index(
        "stock_ownership_movements",
        "ix_stock_ownership_portfolio_economic_id",
        ("portfolio_id", "economic_at", "id"),
    )
    _index(
        "stock_ownership_movements",
        "ix_stock_ownership_portfolio_recorded_id",
        ("portfolio_id", "recorded_at", "id"),
    )
    _index(
        "stock_dividend_entitlements",
        "ix_stock_entitlement_current_work",
        ("event_id", "portfolio_id", "id"),
    )
    _index("stock_dividend_entitlements", "ix_stock_entitlement_portfolio_id", ("portfolio_id",))
    _index(
        "stock_dividend_payments",
        "ix_stock_dividend_payment_portfolio_recorded_id",
        ("portfolio_id", "recorded_at", "id"),
    )
    _index(
        "stock_dividend_decisions",
        "ix_stock_dividend_decision_portfolio_recorded_id",
        ("portfolio_id", "recorded_at", "id"),
    )


def downgrade() -> None:
    raise RuntimeError(
        "portfolio ownership downgrade refused before writes; qualified source required"
    )
