"""Real final-schema root journals and terminal/digest reconstruction."""

from datetime import timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.corporate_action import StockOwnershipMovement, StockSplitApplication
from app.services.corporate_action_rules import CutoffEvidence
from app.services.stock_ownership import (
    OwnershipHeld,
    StockMovementInput,
    _check_closures,
    _check_units,
    append_stock_movement,
    assert_ownership_consistent,
    ownership_digest,
    portfolio_digest_rows,
    reconstruct_stock_quantity,
)
from tests.portfolio_fixtures import migrate_to, portfolio_migration_db
from tests.test_portfolio_stock_authority import stock_authority_case

__all__ = ["stock_authority_case", "portfolio_migration_db"]


@pytest_asyncio.fixture
async def journal_case(stock_authority_case):
    conn, case = stock_authority_case
    at = case["now"] - timedelta(days=2)
    await conn.execute(
        text(
            "UPDATE stock_action_state SET journal_start_at=:at,complete_from=:at WHERE coin_id=:c"
        ),
        {"at": at - timedelta(days=1), "c": case["coin"]},
    )
    for seq, root in enumerate((case["first"], case["sibling"]), 1):
        await conn.execute(
            text("""INSERT INTO stock_ownership_movements
          (portfolio_id,user_id,coin_id,sequence,economic_at,recorded_at,quantity,
           before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key)
          VALUES (:p,:u,:c,:s,:at,:at,2,0,2,0,20,0,'opening',:k)"""),
            {
                "p": root,
                "u": case["owner"],
                "c": case["coin"],
                "s": seq,
                "at": at,
                "k": f"opening:{root}",
            },
        )
    db = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
    try:
        yield db, conn, case
    finally:
        await db.close()


async def test_root_journals_same_owner_do_not_merge(journal_case):
    db, _, case = journal_case
    _, rows = await assert_ownership_consistent(db, case["coin"])
    assert [(r.portfolio_id, r.after_quantity, r.after_basis) for r in rows] == [
        (case["first"], Decimal(2), Decimal(20)),
        (case["sibling"], Decimal(2), Decimal(20)),
    ]
    at = case["now"] - timedelta(days=1)
    cutoff = CutoffEvidence(at, "NASDAQ", at.date(), 1, "synthetic")
    for root in (case["first"], case["sibling"]):
        snapshot = await reconstruct_stock_quantity(db, root, case["coin"], cutoff, 0)
        assert snapshot.quantity == Decimal(2)


@pytest.mark.parametrize("damage", ["owner", "closed"])
async def test_unjournaled_holding_identity_and_closure_refused(stock_authority_case, damage):
    """Real loaded holdings remain subject to root checks even without journals."""
    from app.models.trade import Holding

    conn, case = stock_authority_case
    await conn.execute(
        text("UPDATE stock_action_state SET journal_start_at=:n,complete_from=:n WHERE coin_id=:c"),
        {"n": case["now"] - timedelta(days=1), "c": case["coin"]},
    )
    async with AsyncSession(bind=conn) as db:
        held = (
            await db.scalars(
                select(Holding).where(
                    Holding.portfolio_id == case["first"], Holding.coin_id == case["coin"]
                )
            )
        ).one()
        if damage == "owner":
            # A stale/inconsistent in-memory object must also be rejected. The
            # invalid pair is deliberately never flushed through the SQL FK.
            held.user_id = case["foreign_owner"]
        else:
            await conn.execute(
                text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"),
                {"p": case["first"]},
            )
        with (
            db.no_autoflush,
            pytest.raises(
                OwnershipHeld, match="holding_mismatch" if damage == "owner" else "invalid_closure"
            ),
        ):
            await assert_ownership_consistent(db, case["coin"])
        db.expire_all()


async def test_explicit_root_append_does_not_accept_user_only(journal_case):
    db, _, case = journal_case
    with pytest.raises(OwnershipHeld, match="invalid_movement"):
        await append_stock_movement(
            db,
            StockMovementInput(
                case["owner"], case["coin"], Decimal(1), Decimal(20), "missing", application_id=1
            ),
        )


async def test_closed_or_foreign_root_append_refused_before_replay(journal_case):
    db, _, case = journal_case
    for root in (case["closed"], case["foreign"]):
        with pytest.raises(OwnershipHeld, match="portfolio_unavailable"):
            await append_stock_movement(
                db,
                StockMovementInput(
                    case["owner"],
                    case["coin"],
                    Decimal(1),
                    Decimal(20),
                    "missing",
                    application_id=1,
                    portfolio_id=root,
                ),
            )


async def close_root(db, conn, case, root):
    """Complete closure proof inside the uncommitted SQL-negative fixture.

    The outer disposable transaction remains rollback-only; integrated lifecycle
    acceptance uses public DELETE in the dedicated closure tests.
    """
    assert (await conn.execute(text("SELECT current_database(),session_user"))).one() == (
        "birja_test",
        "birja_test",
    )
    await db.flush()
    from uuid import uuid4

    from app.services.portfolio_closure import ClosureIntent, close_portfolio

    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    await conn.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    name = await conn.scalar(text("SELECT name FROM accounts WHERE id=:p"), {"p": root})
    async with AsyncSession(bind=conn, join_transaction_mode="rollback_only") as closure:
        result = await close_portfolio(closure, ClosureIntent(case["owner"], root, uuid4(), name))
        assert result.outcome == "closed"
    db.expire_all()


async def test_terminal_root_reconstructs_at_own_cutoff(journal_case):
    db, conn, case = journal_case
    await close_root(db, conn, case, case["first"])
    await assert_ownership_consistent(db, case["coin"])
    at = case["now"] - timedelta(days=1)
    result = await reconstruct_stock_quantity(
        db, case["first"], case["coin"], CutoffEvidence(at, "NASDAQ", at.date(), 1, "synthetic"), 0
    )
    assert result.quantity == 2


async def test_closed_root_without_terminal_record_is_corruption(journal_case):
    db, conn, case = journal_case
    await conn.execute(
        text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"), {"p": case["first"]}
    )
    with pytest.raises(OwnershipHeld, match="invalid_closure"):
        await assert_ownership_consistent(db, case["coin"])


@pytest.mark.parametrize(
    "damage",
    [
        "future_sequence",
        "early_sequence",
        "wrong_epoch",
        "wrong_owner",
        "wrong_time",
        "future_time",
    ],
)
async def test_contradictory_terminal_record_fails_closed(journal_case, damage):
    db, conn, case = journal_case
    await close_root(db, conn, case, case["first"])
    from app.models.corporate_action import PortfolioStockClosure
    from app.models.user import Account

    rows = list(
        (
            await db.execute(
                select(StockOwnershipMovement).where(StockOwnershipMovement.coin_id == case["coin"])
            )
        ).scalars()
    )
    roots = {r.id: r for r in (await db.execute(select(Account))).scalars()}
    closure = (
        await db.execute(
            select(PortfolioStockClosure).where(PortfolioStockClosure.portfolio_id == case["first"])
        )
    ).scalar_one()
    from types import SimpleNamespace

    values = {c.name: getattr(closure, c.name) for c in PortfolioStockClosure.__table__.columns}
    if damage == "future_sequence":
        values["closing_sequence"] = 99
    if damage == "early_sequence":
        values["closing_sequence"] = 1
    if damage == "wrong_epoch":
        values["unit_epoch"] = 1
    if damage == "wrong_owner":
        values["user_id"] = case["foreign_owner"]
    if damage == "wrong_time":
        values["closed_at"] -= timedelta(days=10)
    if damage == "future_time":
        values["closed_at"] += timedelta(days=1)
    with pytest.raises(OwnershipHeld, match="invalid_closure"):
        _check_closures(
            rows, [], roots, {closure.portfolio_id: SimpleNamespace(**values)}, case["now"]
        )


@pytest.mark.parametrize("version", [None, 1, 2, 3, -1])
async def test_unverifiable_digest_identity_or_version_fails_closed(journal_case, version):
    db, _, case = journal_case
    rows = list(
        (
            await db.execute(
                select(StockOwnershipMovement)
                .where(StockOwnershipMovement.coin_id == case["coin"])
                .order_by(StockOwnershipMovement.sequence)
            )
        ).scalars()
    )
    # NULL-v1 cannot represent these same-owner sibling roots; version2 must
    # authenticate the exact root tuples. Unknown versions must never be guessed.
    app = StockSplitApplication(
        id=9,
        coin_id=case["coin"],
        prior_unit_epoch=0,
        new_unit_epoch=1,
        sequence_boundary=2,
        cutoff=case["now"],
        owner_digest_version=version,
        before_digest="0" * 64,
    )
    with pytest.raises(OwnershipHeld, match="invalid_digest"):
        _check_units(rows, [app], 1, 9, {})


async def test_journal_cannot_resolve_an_absent_owner_root(journal_case):
    db, _, case = journal_case
    _, rows = await assert_ownership_consistent(db, case["coin"])
    with pytest.raises(OwnershipHeld, match="history_gap"):
        _check_closures(rows, [], {}, {})


async def test_reconstruction_cannot_select_missing_or_postclosure_root(journal_case):
    db, conn, case = journal_case
    at = case["now"] - timedelta(days=1)
    cutoff = CutoffEvidence(at, "NASDAQ", at.date(), 1, "synthetic")
    with pytest.raises(OwnershipHeld, match="portfolio_unavailable"):
        await reconstruct_stock_quantity(db, 9223372036854775807, case["coin"], cutoff, 0)
    await close_root(db, conn, case, case["first"])
    # A real time after closure, already in the past when the reader checks its
    # database clock. Future cutoffs correctly fail the earlier baseline guard.
    after = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
    with pytest.raises(OwnershipHeld, match="invalid_closure"):
        await reconstruct_stock_quantity(
            db,
            case["first"],
            case["coin"],
            CutoffEvidence(after, "NASDAQ", after.date(), 1, "synthetic"),
            0,
        )


async def test_canonical_v2_digest_uses_portfolio_identity_and_exact_strings(journal_case):
    db, _, case = journal_case
    _, rows = await assert_ownership_consistent(db, case["coin"])
    values = portfolio_digest_rows(rows, 2, case["coin"], 0)
    assert values == [
        (r, case["owner"], case["coin"], "2.00000000", "20.00000000", i, 0)
        for i, r in enumerate((case["first"], case["sibling"]), 1)
    ]
    assert ownership_digest(values) != ownership_digest(
        [(case["owner"], "2.00000000", "20.00000000")]
    )


@pytest.mark.parametrize("later_split", [False, True])
async def test_real_two_user_legacy_digest_reload_preserves_original_bytes(
    portfolio_migration_db, later_split
):
    from uuid import uuid4

    from tests.test_stock_action_migrations import event

    engine = portfolio_migration_db
    await migrate_to("0014")
    async with engine.begin() as conn:
        cid = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
        users = []
        for _ in range(2):
            uid = (
                await conn.execute(
                    text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                    {"e": f"legacy-journal-{uuid4()}@example.test"},
                )
            ).scalar_one()
            users.append(uid)
            await conn.execute(
                text("INSERT INTO accounts(user_id,cash,starting_cash) VALUES (:u,123,9999)"),
                {"u": uid},
            )
            await conn.execute(
                text(
                    "INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) VALUES (:u,:c,4,20)"
                ),
                {"u": uid, "c": cid},
            )
        await conn.execute(
            text("""INSERT INTO stock_action_state
          (coin_id,health,admission_generation,journal_start_at,complete_from,unit_epoch,sequence)
          VALUES (:c,'current',1,:start,:start,1,4)"""),
            {"c": cid, "start": now - timedelta(days=3)},
        )
        eid, _, rid = await event(conn, cid)
        await conn.execute(
            text("""UPDATE stock_action_revisions SET
          classification='supported_forward_split',reason='none',verified_cutoff=:at
          WHERE id=:r"""),
            {"at": now - timedelta(days=1), "r": rid},
        )
        before = ownership_digest([(u, "2.00000000", "20.00000000") for u in users])
        after = ownership_digest([(u, "4", "20.00000000") for u in users])
        aid = (
            await conn.execute(
                text("""INSERT INTO stock_split_applications
          (economic_event_id,coin_id,revision_id,new_rate,old_rate,cutoff,processed_at,
           prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest)
          VALUES (:e,:c,:r,'2','1',:cutoff,:now,0,1,2,:before,:after) RETURNING id"""),
                {
                    "e": eid,
                    "c": cid,
                    "r": rid,
                    "cutoff": now - timedelta(days=1),
                    "now": now,
                    "before": before,
                    "after": after,
                },
            )
        ).scalar_one()
        for i, u in enumerate(users, 1):
            for split in (False, True):
                await conn.execute(
                    text("""INSERT INTO stock_ownership_movements
                  (user_id,coin_id,sequence,economic_at,recorded_at,quantity,before_quantity,
                   after_quantity,before_basis,after_basis,unit_epoch,cause_kind,application_id,causal_key)
                  VALUES (:u,:c,:s,:at,:at,2,:b,:a,:bb,20,:epoch,:kind,:app,:key)"""),
                    {
                        "u": u,
                        "c": cid,
                        "s": i + 2 if split else i,
                        "at": now - timedelta(days=1 if split else 2),
                        "b": 2 if split else 0,
                        "a": 4 if split else 2,
                        "bb": 20 if split else 0,
                        "epoch": 1 if split else 0,
                        "kind": "split" if split else "opening",
                        "app": aid if split else None,
                        "key": f"legacy:{u}:{split}",
                    },
                )
        original = (
            await conn.execute(
                text(
                    "SELECT id,economic_event_id,before_digest,after_digest "
                    "FROM stock_split_applications WHERE id=:a"
                ),
                {"a": aid},
            )
        ).one()
    await migrate_to("0017")
    async with engine.connect() as conn:
        assert (
            await conn.execute(
                text(
                    "SELECT id,economic_event_id,before_digest,after_digest "
                    "FROM stock_split_applications WHERE id=:a"
                ),
                {"a": aid},
            )
        ).one() == original
    # Current ORM/service consumers require the current schema, not retained0017.
    # Preserve the independent legacy bytes above before the explicit0023 upgrade.
    await migrate_to("0023")
    async with AsyncSession(engine) as db:
        _, rows = await assert_ownership_consistent(db, cid)
        app = await db.get(StockSplitApplication, aid)
        assert app.owner_digest_version is None
        assert (app.id, app.economic_event_id, app.before_digest, app.after_digest) == original
        assert len(rows) == 4 and len({r.portfolio_id for r in rows}) == 2
        if later_split:
            await apply_later_mixed_split(db, cid, users, original)


async def apply_later_mixed_split(db, cid, users, original):
    """Real old/global event plus two new same-owner roots and frozen old owner."""
    import asyncio
    from dataclasses import asdict, replace
    from uuid import uuid4

    from app.models.price import Coin
    from app.models.stock import StockDataAdmission, StockInstrument
    from app.models.user import Account
    from app.services import corporate_actions as actions
    from tests.test_corporate_action_rules import dividend
    from tests.test_corporate_actions import batch, split_action
    from tests.test_stock_admission import action_admitted

    now = (await db.execute(text("SELECT clock_timestamp()"))).scalar_one()
    roots = list((await db.execute(select(Account).order_by(Account.id))).scalars())
    first, closed = [next(r for r in roots if r.user_id == u) for u in users]
    sibling = Account(
        user_id=users[0],
        name="Later sibling",
        name_key="later sibling",
        cash=Decimal(333),
        starting_cash=Decimal(1234),
    )
    db.add(sibling)
    await db.flush()
    await db.execute(
        text("""INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis)
      VALUES (:p,:u,:c,2,30)"""),
        {"p": sibling.id, "u": users[0], "c": cid},
    )
    await db.execute(
        text("""INSERT INTO stock_ownership_movements
      (portfolio_id,user_id,coin_id,sequence,economic_at,recorded_at,quantity,before_quantity,
       after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key)
      VALUES (:p,:u,:c,5,:at,:at,2,0,2,0,30,1,'opening',:k)"""),
        {
            "p": sibling.id,
            "u": users[0],
            "c": cid,
            "at": now - timedelta(hours=12),
            "k": f"new:{sibling.id}",
        },
    )
    conn = await db.connection()
    first_id, sibling_id = first.id, sibling.id
    await close_root(db, conn, {"owner": users[1], "coin": cid}, closed.id)
    evidence = replace(
        action_admitted(),
        reviewed_at=now - timedelta(hours=1),
        valid_from=now - timedelta(hours=2),
        valid_until=now + timedelta(hours=2),
    )
    db.add(StockDataAdmission(**asdict(evidence)))
    instrument = await db.get(StockInstrument, cid)
    instrument.provider_asset_id = "synthetic-current-asset"
    instrument.provider_verified_at = now - timedelta(days=1)
    await db.execute(
        text("""UPDATE stock_action_state SET health='current',
      admission_generation=1,valid_until=:until,covered_until=:now WHERE coin_id=:c"""),
        {"until": now + timedelta(hours=1), "now": now, "c": cid},
    )
    symbol = (await db.execute(select(Coin.symbol).where(Coin.id == cid))).scalar_one()
    action = replace(
        dividend(), coin_id=cid, symbol=symbol, provider_event_id=str(uuid4()), observed_at=now
    )
    await actions.persist_action_batch(
        db, batch(split_action(action, now - timedelta(hours=1), new_rate=Decimal(2))), evidence
    )
    # This disposable migration fixture owns schema teardown, so it can publish
    # the seed and exercise two genuinely independent scheduler transactions.
    await db.commit()

    async def processor():
        async with AsyncSession(db.bind, expire_on_commit=False) as worker, worker.begin():
            await worker.execute(text("SET LOCAL ROLE birja_scheduler"))
            return await actions.apply_due_actions(worker, cid)

    first_result, second_result = await asyncio.wait_for(
        asyncio.gather(processor(), processor()), timeout=15
    )
    assert first_result == second_result
    ids = first_result
    assert len(ids) == 2
    db.expire_all()
    apps = list(
        (
            await db.execute(
                select(StockSplitApplication).order_by(StockSplitApplication.new_unit_epoch)
            )
        ).scalars()
    )
    assert [a.owner_digest_version for a in apps] == [None, 2]
    assert (
        apps[0].id,
        apps[0].economic_event_id,
        apps[0].before_digest,
        apps[0].after_digest,
    ) == original
    state, rows = await assert_ownership_consistent(db, cid)
    assert state.unit_epoch == 2
    effects = [r for r in rows if r.application_id == apps[1].id]
    assert {r.portfolio_id for r in effects} == {first_id, sibling_id}
    assert {r.after_quantity for r in effects} == {Decimal(8), Decimal(4)}
