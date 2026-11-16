"""Real ownership and retry scenario matrix; domain plans extend these proofs."""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import UniqueConstraint, text
from sqlalchemy.exc import IntegrityError

from tests.portfolio_fixtures import (
    portfolio_session,
    portfolio_world,
    seed_owned_crypto_trade,
)

__all__ = ["portfolio_world"]


def test_model_metadata_root_retains_identity_economics_and_owned_candidate_key():
    from sqlalchemy import BigInteger, DateTime, Numeric, Text

    from app.models.user import Account

    table = Account.__table__
    assert isinstance(table.c.id.type, BigInteger)
    assert table.c.id.primary_key and table.c.id.identity.always
    assert isinstance(table.c.name.type, Text)
    assert not table.c.name.nullable
    assert table.c.name.server_default.arg == "My portfolio"
    assert isinstance(table.c.closed_at.type, DateTime)
    assert table.c.closed_at.type.timezone and table.c.closed_at.nullable
    assert table.c.closed_at.default is None and table.c.closed_at.server_default is None
    unique = {
        tuple(c.name for c in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("id", "user_id") in unique
    assert ("user_id",) not in unique
    assert any(tuple(index.columns.keys()) == ("user_id",) for index in table.indexes)
    assert "description" not in table.c
    for column in (table.c.cash, table.c.starting_cash):
        assert isinstance(column.type, Numeric)
        assert (column.type.precision, column.type.scale) == (20, 8)
        assert not column.nullable
        assert column.default is None and column.server_default is None
    assert table.c.created_at.type.timezone


@pytest.mark.parametrize("cash", ["0.00", "8765.43", "999999999999.99"])
def test_model_metadata_existing_cash_schema_serializes_exact_decimal_strings(cash):
    import json

    from app.schemas.auth import MeOut

    payload = MeOut(email="synthetic@example.test", cash_usd=Decimal(cash))
    assert json.loads(payload.model_dump_json())["cash_usd"] == cash


@pytest.mark.parametrize("model_name", ["Holding", "Trade"])
def test_model_metadata_financial_rows_require_paired_owned_root_without_cascade(model_name):
    from sqlalchemy import BigInteger

    from app.models.trade import Holding, Trade

    table = {"Holding": Holding, "Trade": Trade}[model_name].__table__
    assert isinstance(table.c.portfolio_id.type, BigInteger)
    assert not table.c.portfolio_id.nullable
    assert table.c.portfolio_id.default is None
    assert table.c.portfolio_id.server_default is None
    paired = [
        fk
        for fk in table.foreign_key_constraints
        if tuple(fk.column_keys) == ("portfolio_id", "user_id")
    ]
    assert len(paired) == 1
    assert tuple(e.target_fullname for e in paired[0].elements) == (
        "accounts.id",
        "accounts.user_id",
    )
    assert all(fk.ondelete is None and fk.onupdate is None for fk in table.foreign_key_constraints)
    assert any(tuple(idx.columns.keys())[0] == "user_id" for idx in table.indexes) or any(
        tuple(c.columns.keys())[0] == "user_id"
        for c in table.constraints
        if isinstance(c, UniqueConstraint)
    )


def test_model_metadata_holdings_unique_per_root_and_preserve_exact_basis():
    from sqlalchemy import Numeric

    from app.models.trade import Holding

    table = Holding.__table__
    unique = {tuple(c.columns.keys()) for c in table.constraints if isinstance(c, UniqueConstraint)}
    assert ("portfolio_id", "coin_id") in unique
    assert ("user_id", "coin_id") not in unique
    for column in (table.c.quantity, table.c.cost_basis):
        assert isinstance(column.type, Numeric)
        assert (column.type.precision, column.type.scale) == (20, 8)
        assert not column.nullable
    checks = {c.name for c in table.constraints}
    assert {
        "ck_holdings_quantity_non_negative",
        "ck_holdings_cost_basis_non_negative",
        "ck_holdings_cost_basis_cents",
        "ck_holdings_empty_has_no_cost",
    } <= checks


def test_model_metadata_trade_owned_cause_key_keeps_user_global_retry_and_fill_fields():
    from sqlalchemy import Numeric

    from app.models.trade import Trade

    table = Trade.__table__
    unique = {tuple(c.columns.keys()) for c in table.constraints if isinstance(c, UniqueConstraint)}
    assert ("id", "portfolio_id", "coin_id", "user_id") in unique
    assert ("user_id", "idempotency_key") in unique
    assert ("portfolio_id", "idempotency_key") not in unique
    assert ("portfolio_id", "created_at", "id") in {
        tuple(idx.columns.keys()) for idx in table.indexes
    }
    for name in (
        "input_value",
        "quantity",
        "mid_price",
        "exec_price",
        "fee",
        "cash_delta",
        "cash_after",
    ):
        column = table.c[name]
        assert isinstance(column.type, Numeric)
        assert (column.type.precision, column.type.scale) == (20, 8)
        assert not column.nullable and column.default is None and column.server_default is None
    for name in ("price_as_of", "created_at"):
        assert table.c[name].type.timezone
    assert set(table.c.keys()) == {
        "id",
        "portfolio_id",
        "user_id",
        "coin_id",
        "side",
        "input_kind",
        "input_value",
        "quantity",
        "mid_price",
        "price_as_of",
        "exec_price",
        "fee",
        "cash_delta",
        "cash_after",
        "idempotency_key",
        "created_at",
    }


async def test_final_sql_same_root_coin_holding_is_unique(portfolio_world):
    conn, world = portfolio_world
    with pytest.raises(IntegrityError) as err:
        async with conn.begin_nested():
            await conn.execute(
                text(
                    "INSERT INTO holdings (portfolio_id,user_id,coin_id,quantity,cost_basis) "
                    "VALUES (:p,:u,:c,1,1)"
                ),
                {"p": world.first, "u": world.owner, "c": world.crypto},
            )
    assert err.value.orig.sqlstate == "23505"


async def test_final_sql_foreign_owner_tuple_cannot_link_trade(portfolio_world):
    conn, world = portfolio_world
    with pytest.raises(IntegrityError) as err:
        async with conn.begin_nested():
            await seed_owned_crypto_trade(conn, world, world.foreign)
    assert err.value.orig.sqlstate == "23503"


@pytest.mark.parametrize("target", [None, 9223372036854775807])
async def test_final_sql_missing_or_unknown_root_cannot_link_holding(portfolio_world, target):
    conn, world = portfolio_world
    with pytest.raises(IntegrityError) as err:
        async with conn.begin_nested():
            await conn.execute(
                text(
                    "INSERT INTO holdings (portfolio_id,user_id,coin_id,quantity,cost_basis) "
                    "VALUES (:p,:u,:c,1,1)"
                ),
                {"p": target, "u": world.owner, "c": world.crypto},
            )
    assert err.value.orig.sqlstate == ("23502" if target is None else "23503")


async def test_final_sql_root_metadata_preserves_named_active_and_closed_roots(portfolio_world):
    conn, world = portfolio_world
    rows = (
        await conn.execute(
            text("SELECT id,name,closed_at,cash,starting_cash FROM accounts WHERE user_id=:u"),
            {"u": world.owner},
        )
    ).all()
    roots = {row.id: row for row in rows}
    assert roots[world.first].name
    assert roots[world.sibling].name
    assert roots[world.first].closed_at is None
    assert roots[world.sibling].closed_at is None
    assert roots[world.closed].closed_at is not None
    assert roots[world.first].cash == Decimal("1234.56")
    assert roots[world.sibling].cash == Decimal("4321.09")


async def test_final_sql_owner_counts_and_sibling_finances_are_independent(portfolio_world):
    conn, world = portfolio_world
    rows = (
        await conn.execute(
            text(
                "SELECT user_id,count(*) FROM accounts "
                "WHERE closed_at IS NULL GROUP BY user_id ORDER BY user_id"
            )
        )
    ).all()
    counts = dict(rows)
    assert counts.get(world.empty_owner, 0) == 0
    assert counts[world.single_owner] == 1
    assert counts[world.owner] == 2
    assert counts[world.foreign_owner] == 1
    assert (
        await conn.execute(
            text("SELECT id,cash FROM accounts WHERE id IN (:a,:b) ORDER BY id"),
            {"a": world.first, "b": world.sibling},
        )
    ).all() == [(world.first, Decimal("1234.56")), (world.sibling, Decimal("4321.09"))]
    assert (
        await conn.execute(
            text(
                "SELECT portfolio_id,quantity,cost_basis FROM holdings "
                "WHERE user_id=:u ORDER BY portfolio_id"
            ),
            {"u": world.owner},
        )
    ).all() == [
        (world.first, Decimal("0.1"), Decimal("123.00")),
        (world.sibling, Decimal("0.2"), Decimal("456.00")),
    ]


async def test_final_sql_foreign_owner_tuple_cannot_link_holding(portfolio_world):
    conn, world = portfolio_world
    with pytest.raises(IntegrityError) as err:
        async with conn.begin_nested():
            await conn.execute(
                text(
                    "INSERT INTO holdings "
                    "(portfolio_id,user_id,coin_id,quantity,cost_basis) VALUES (:p,:u,:c,1,1)"
                ),
                {"p": world.foreign, "u": world.owner, "c": world.crypto},
            )
    assert err.value.orig.sqlstate == "23503"


async def test_final_sql_retry_key_is_global_across_sibling_roots(portfolio_world):
    conn, world = portfolio_world
    _, key = await seed_owned_crypto_trade(conn, world, world.first)
    with pytest.raises(IntegrityError) as err:
        async with conn.begin_nested():
            await seed_owned_crypto_trade(conn, world, world.sibling, key)
    assert err.value.orig.sqlstate == "23505"
    assert (
        await conn.execute(
            text("SELECT count(*) FROM trades WHERE user_id=:u AND idempotency_key=:k"),
            {"u": world.owner, "k": key},
        )
    ).scalar_one() == 1


async def test_original_retry_lookup_keeps_active_root_when_sibling_is_closed(portfolio_world):
    from app.services.trade_idempotency import find_user_trade
    from tests.portfolio_fixtures import seed_owned_crypto_trade

    conn, world = portfolio_world
    tid, key = await seed_owned_crypto_trade(conn, world, world.first)
    async with portfolio_session(conn) as db:
        original = await find_user_trade(db, world.owner, key)
        assert original is not None
        assert (original.id, original.portfolio_id, original.user_id) == (
            tid,
            world.first,
            world.owner,
        )
        assert original.cash_delta == Decimal("-50.25")
        assert original.portfolio_id != world.closed


@pytest.mark.parametrize("target", ["foreign", "closed", "unknown"])
async def test_resolver_refuses_unavailable_targets_without_retargeting(portfolio_world, target):
    from app.services.portfolios import resolve_owned_active_portfolio

    from app.models.user import User

    conn, world = portfolio_world
    root = {"foreign": world.foreign, "closed": world.closed, "unknown": 9223372036854775807}[
        target
    ]
    async with portfolio_session(conn) as db:
        with pytest.raises(HTTPException) as err:
            await resolve_owned_active_portfolio(db, User(id=world.owner), root)
    assert err.value.status_code == 404
    assert err.value.detail["code"] == "portfolio_unavailable"


async def test_resolver_returns_only_explicit_owned_active_root(portfolio_world):
    from app.services.portfolios import resolve_owned_active_portfolio

    from app.models.user import User

    conn, world = portfolio_world
    async with portfolio_session(conn) as db:
        resolved = await resolve_owned_active_portfolio(db, User(id=world.owner), world.sibling)
        assert (resolved.portfolio_id, resolved.user_id) == (world.sibling, world.owner)
