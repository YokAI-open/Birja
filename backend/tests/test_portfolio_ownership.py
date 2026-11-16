"""Real ownership and retry scenario matrix; domain plans extend these proofs."""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.portfolio_fixtures import (
    portfolio_session,
    portfolio_world,
    seed_owned_crypto_trade,
)

__all__ = ["portfolio_world"]


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
