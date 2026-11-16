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
