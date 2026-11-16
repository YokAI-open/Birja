"""Static0017 dividend contracts and real final-schema authority proofs.

The final_sql cases require real Alembic0017. Before Plan07 only collection
and static asset contracts run; no test fabricates or installs a final schema.
"""

import json
from dataclasses import asdict, replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.test_stock_action_migrations import event
from tests.test_stock_admission import action_admitted, admitted
from tests.test_stock_sessions import evidence

ASSET = Path(__file__).parents[1] / "alembic/sql/0017_dividend_portfolio.sql"
SIGNATURES = {
    "stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)",
    "apply_stock_dividend(bigint,bigint,text,text)",
    "record_stock_dividend_hold(bigint,text)",
    "reject_stock_dividend_mutation()",
}


@pytest_asyncio.fixture
async def dividend_portfolio_case(engine, migrated):
    """Admin-only synthetic evidence setup; business calls use installed roles.

    No privileges or functions are created here. The actual0017 migration must
    provide all production authority; every synthetic row rolls back afterward.
    """
    async with engine.connect() as conn:
        tx = await conn.begin()
        try:
            assert (
                await conn.execute(text("SELECT version_num FROM alembic_version"))
            ).scalar_one() == "0017"
            now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
            owners = []
            for label in ("owner", "foreign"):
                owners.append(
                    (
                        await conn.execute(
                            text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                            {"e": f"{label}-dividend-{uuid4()}@example.test"},
                        )
                    ).scalar_one()
                )
            roots = []
            for uid, label in (
                (owners[0], "First"),
                (owners[0], "Sibling"),
                (owners[1], "Foreign"),
            ):
                roots.append(
                    (
                        await conn.execute(
                            text("""INSERT INTO accounts(user_id,name,cash,starting_cash)
                            VALUES (:u,:n,100,12345.67) RETURNING id"""),
                            {"u": uid, "n": label},
                        )
                    ).scalar_one()
                )
            cid = (
                await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))
            ).scalar_one()
            eid, _, rid = await event(conn, cid)
            cutoff = now - timedelta(days=3)
            terms = {
                "event_type": "cash_dividend",
                "currency": "USD",
                "subtype": "ordinary",
                "foreign": False,
                "special": False,
                "due_bills": False,
                "identity_verified": True,
                "dates_verified": True,
                "cancelled": False,
                "identity_changed": False,
                "rate": "0.5",
                "ex_date": str(cutoff.date()),
                "record_date": str((now - timedelta(days=2)).date()),
                "payable_date": str((now - timedelta(days=1)).date()),
            }
            await conn.execute(
                text("""UPDATE stock_action_revisions SET classification='supported_dividend',
                normalized_terms=CAST(:terms AS jsonb),admission_generation=4,
                verified_cutoff=:cutoff
                WHERE id=:r"""),
                {"r": rid, "terms": json.dumps(terms), "cutoff": cutoff},
            )
            for admission in (admitted("reference"), action_admitted(), evidence(now)):
                admission = replace(
                    admission,
                    reviewed_at=now - timedelta(hours=1),
                    valid_from=now - timedelta(hours=1),
                    valid_until=now + timedelta(hours=1),
                    scope={
                        **admission.scope,
                        "durable_accounting": True,
                        "backup_restore": True,
                        "retention_mode": "durable-accounting",
                    },
                )
                values = asdict(admission)
                for field in ("scope", "quota", "allowed_fields", "calendar"):
                    values[field] = json.dumps(values[field])
                columns = list(values)
                expressions = [
                    f"CAST(:{k} AS jsonb)"
                    if k in ("scope", "quota", "allowed_fields", "calendar")
                    else f":{k}"
                    for k in columns
                ]
                await conn.execute(
                    text(
                        f"INSERT INTO stock_data_admissions ({','.join(columns)}) "  # noqa: S608 - fixed dataclass fields
                        f"VALUES ({','.join(expressions)})"
                    ),
                    values,
                )
            await conn.execute(
                text("""INSERT INTO stock_action_state(coin_id,admission_generation,health,
                checked_at,valid_until,journal_start_at,complete_from,coverage_start,covered_until)
                VALUES (:c,4,'current',CAST(:n AS timestamptz)-interval '1 hour',
                CAST(:n AS timestamptz)+interval '1 hour',
                CAST(:n AS timestamptz)-interval '10 days',
                CAST(:n AS timestamptz)-interval '10 days',
                CAST(:n AS timestamptz)-interval '10 days',:n)"""),
                {"c": cid, "n": now},
            )
            await conn.execute(
                text("""INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,
                calendar_admission_generation,coverage_start,coverage_end)
                SELECT listing_exchange,CAST(:cutoff AS timestamptz)::date,:cutoff,
                CAST(:cutoff AS timestamptz)+interval '6 hours',4,
                CAST(:cutoff AS timestamptz)::date,CAST(:cutoff AS timestamptz)::date
                FROM stock_instruments WHERE coin_id=:c"""),
                {"c": cid, "cutoff": cutoff},
            )
            targets = []
            for sequence, (root, uid, quantity) in enumerate(
                ((roots[0], owners[0], 2), (roots[1], owners[0], 4), (roots[2], owners[1], 6)), 1
            ):
                await conn.execute(
                    text("""INSERT INTO stock_ownership_movements(portfolio_id,coin_id,user_id,
                    sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,
                    before_basis,after_basis,unit_epoch,cause_kind,causal_key)
                    VALUES (:p,:c,:u,:seq,CAST(:cutoff AS timestamptz)-interval '1 day',:n,
                    :q,0,:q,0,0,0,'opening',:key)"""),
                    {
                        "p": root,
                        "c": cid,
                        "u": uid,
                        "seq": sequence,
                        "cutoff": cutoff,
                        "n": now,
                        "q": quantity,
                        "key": str(uuid4()),
                    },
                )
                fp = str(sequence) * 64
                entitlement = (
                    await conn.execute(
                        text("""INSERT INTO stock_dividend_entitlements(
                        event_id,portfolio_id,user_id,
                        revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,
                        last_movement_sequence,eligible_quantity,state,fingerprint)
                        VALUES (:e,:p,:u,:r,:cutoff,'exclusive-regular-session-open',1,
                        'unit_epoch:0',0,3,:q,'eligible',:f) RETURNING id"""),
                        {
                            "e": eid,
                            "p": root,
                            "u": uid,
                            "r": rid,
                            "cutoff": cutoff,
                            "q": quantity,
                            "f": fp,
                        },
                    )
                ).scalar_one()
                targets.append(
                    {
                        "event_id": eid,
                        "coin_id": cid,
                        "user_id": uid,
                        "portfolio_id": root,
                        "revision_id": rid,
                        "revision_fingerprint": "a" * 64,
                        "entitlement_id": entitlement,
                        "entitlement_fingerprint": fp,
                    }
                )
            yield conn, targets
        finally:
            await tx.rollback()


async def apply(conn, target, role="birja_scheduler"):
    assert role in {"birja_scheduler", "birja_app"}
    async with conn.begin_nested():
        await conn.execute(text(f"SET LOCAL ROLE {role}"))
        row = dict(
            (
                await conn.execute(
                    text("""SELECT * FROM public.apply_stock_dividend(
            :event_id,:entitlement_id,:revision_fingerprint,:entitlement_fingerprint)"""),
                    target,
                )
            )
            .mappings()
            .one()
        )
        await conn.execute(text("RESET ROLE"))
        return row


async def hold(conn, payment, revision):
    async with conn.begin_nested():
        await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
        row = dict(
            (
                await conn.execute(
                    text("SELECT * FROM public.record_stock_dividend_hold(:p,:r)"),
                    {"p": payment, "r": revision},
                )
            )
            .mappings()
            .one()
        )
        await conn.execute(text("RESET ROLE"))
        return row


async def balances(conn, targets):
    return [
        Decimal(
            (
                await conn.execute(
                    text("SELECT cash FROM accounts WHERE id=:p"), {"p": t["portfolio_id"]}
                )
            ).scalar_one()
        )
        for t in targets
    ]


async def successor(
    conn, target, *, rate="0.75", classification="supported_dividend", eligible=True
):
    fp = uuid4().hex * 2
    rid = (
        await conn.execute(
            text("""INSERT INTO stock_action_revisions(event_id,source_id,
        ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,
        classification,reason,verified_cutoff)
        SELECT event_id,source_id,ordinal+1,:fp,'snapshot',clock_timestamp(),admission_generation,
        jsonb_set(normalized_terms,'{rate}',to_jsonb(CAST(:rate AS text))),
        :classification,'fixture',
        NULL FROM stock_action_revisions WHERE id=:revision_id RETURNING id"""),
            {**target, "fp": fp, "rate": rate, "classification": classification},
        )
    ).scalar_one()
    await conn.execute(
        text("UPDATE stock_action_events SET current_revision_id=:r WHERE id=:event_id"),
        {**target, "r": rid},
    )
    await conn.execute(
        text("UPDATE stock_action_state SET epoch=epoch+1 WHERE coin_id=:coin_id"), target
    )
    new = {**target, "revision_id": rid, "revision_fingerprint": fp}
    if eligible:
        efp = uuid4().hex * 2
        eid = (
            await conn.execute(
                text("""INSERT INTO stock_dividend_entitlements(event_id,
            portfolio_id,user_id,revision_id,cutoff,cutoff_rule,units_basis,unit_epoch,
            last_movement_sequence,eligible_quantity,state,version,supersedes_id,fingerprint)
            SELECT event_id,portfolio_id,user_id,:r,cutoff,cutoff_rule,units_basis,unit_epoch,
            last_movement_sequence,eligible_quantity,'eligible',version+1,id,:f
            FROM stock_dividend_entitlements WHERE id=:entitlement_id RETURNING id"""),
                {**target, "r": rid, "f": efp},
            )
        ).scalar_one()
        new.update(entitlement_id=eid, entitlement_fingerprint=efp)
    return new


async def test_final_sql_dividend_each_sibling_paid_once_without_touching_foreign(
    dividend_portfolio_case,
):
    conn, targets = dividend_portfolio_case
    first = await apply(conn, targets[0])
    sibling = await apply(conn, targets[1])
    assert first["payment_id"] != sibling["payment_id"]
    assert await apply(conn, targets[0]) == first and await apply(conn, targets[1]) == sibling
    assert await balances(conn, targets) == [Decimal(101), Decimal(102), Decimal(100)]
    rows = (
        await conn.execute(
            text(
                "SELECT portfolio_id,eligible_quantity,original_amount "
                "FROM stock_dividend_payments ORDER BY id"
            )
        )
    ).all()
    assert [tuple(r) for r in rows] == [
        (targets[0]["portfolio_id"], Decimal(2), Decimal(1)),
        (targets[1]["portfolio_id"], Decimal(4), Decimal(2)),
    ]


async def test_final_sql_dividend_foreign_entitlement_fingerprint_cannot_cross_root(
    dividend_portfolio_case,
):
    conn, targets = dividend_portfolio_case
    with pytest.raises(DBAPIError):
        await apply(conn, {**targets[0], "entitlement_id": targets[2]["entitlement_id"]})
    assert await balances(conn, targets) == [Decimal(100)] * 3
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0


@pytest.mark.parametrize("paid", [False, True])
async def test_final_sql_dividend_closed_root_refuses_unpaid_and_corrected_effects(
    dividend_portfolio_case, paid
):
    conn, targets = dividend_portfolio_case
    target = targets[0]
    if paid:
        await apply(conn, target)
        target = await successor(conn, target)
    before = await balances(conn, targets)
    await conn.execute(
        text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:portfolio_id"), target
    )
    with pytest.raises(DBAPIError, match="portfolio"):
        await apply(conn, target)
    assert await balances(conn, targets) == before
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_decisions"))
    ).scalar_one() == 0


async def test_final_sql_dividend_corrections_are_same_root_and_append_only(
    dividend_portfolio_case,
):
    conn, targets = dividend_portfolio_case
    original = await apply(conn, targets[0])
    await apply(conn, targets[1])
    corrected = await successor(conn, targets[0])
    result = await apply(conn, corrected)
    assert result["outcome"] == "applied" and await apply(conn, corrected) == result
    assert await balances(conn, targets) == [Decimal("101.50"), Decimal(102), Decimal(100)]
    row = (
        await conn.execute(
            text("""SELECT portfolio_id,payment_id,desired_total,
        cumulative_applied_before,applied_delta FROM stock_dividend_decisions WHERE id=:d"""),
            {"d": result["decision_id"]},
        )
    ).one()
    assert tuple(row) == (
        targets[0]["portfolio_id"],
        original["payment_id"],
        Decimal("1.50"),
        Decimal(1),
        Decimal(".50"),
    )
    with pytest.raises(DBAPIError):
        async with conn.begin_nested():
            await conn.execute(
                text("UPDATE stock_dividend_decisions SET applied_delta=0 WHERE id=:d"),
                {"d": result["decision_id"]},
            )


async def test_final_sql_dividend_unaffordable_hold_and_retry_never_spends_sibling(
    dividend_portfolio_case,
):
    conn, targets = dividend_portfolio_case
    await apply(conn, targets[0])
    corrected = await successor(conn, targets[0], rate=".1")
    await conn.execute(text("UPDATE accounts SET cash=.79 WHERE id=:portfolio_id"), targets[0])
    result = await apply(conn, corrected)
    assert result["outcome"] == "held_unaffordable" and await apply(conn, corrected) == result
    assert await balances(conn, targets) == [Decimal(".79"), Decimal(100), Decimal(100)]
    await conn.execute(text("UPDATE accounts SET cash=.80 WHERE id=:portfolio_id"), targets[0])
    paid = await apply(conn, corrected)
    assert paid["outcome"] == "applied"
    assert await balances(conn, targets) == [Decimal(0), Decimal(100), Decimal(100)]
    rows = (
        await conn.execute(
            text(
                "SELECT applied_delta,previous_decision_id "
                "FROM stock_dividend_decisions ORDER BY id"
            )
        )
    ).all()
    assert [tuple(r) for r in rows] == [
        (Decimal(0), None),
        (Decimal("-.80"), result["decision_id"]),
    ]


async def test_final_sql_dividend_uncertain_hold_uses_original_root_and_freezes(
    dividend_portfolio_case,
):
    conn, targets = dividend_portfolio_case
    original = await apply(conn, targets[0])
    uncertain = await successor(conn, targets[0], classification="uncertain", eligible=False)
    result = await hold(conn, original["payment_id"], uncertain["revision_fingerprint"])
    assert result["outcome"] == "held_uncertain"
    assert await hold(conn, original["payment_id"], uncertain["revision_fingerprint"]) == result
    assert await balances(conn, targets) == [Decimal(101), Decimal(100), Decimal(100)]
    await conn.execute(
        text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:portfolio_id"), targets[0]
    )
    with pytest.raises(DBAPIError, match="portfolio"):
        await hold(conn, original["payment_id"], uncertain["revision_fingerprint"])
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_decisions"))
    ).scalar_one() == 1


async def test_final_sql_dividend_app_cannot_execute_scheduler_authority(dividend_portfolio_case):
    conn, targets = dividend_portfolio_case
    with pytest.raises(DBAPIError) as error:
        await apply(conn, targets[0], role="birja_app")
    assert error.value.orig.sqlstate == "42501"


async def test_final_sql_dividend_scheduler_cannot_invoke_private_validator_or_write_cash(
    dividend_portfolio_case,
):
    conn, targets = dividend_portfolio_case
    for sql in (
        "SELECT public.stock_dividend_authority(1,1,'x','x',true,NULL)",
        "UPDATE accounts SET cash=0 WHERE id=:portfolio_id",
        "DELETE FROM stock_dividend_payments",
    ):
        with pytest.raises(DBAPIError) as error:
            async with conn.begin_nested():
                await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
                await conn.execute(text(sql), targets[0])
        assert error.value.orig.sqlstate == "42501"


async def test_final_sql_dividend_missing_fingerprint_rolls_back_all_effects(
    dividend_portfolio_case,
):
    conn, targets = dividend_portfolio_case
    with pytest.raises(DBAPIError):
        await apply(conn, {**targets[0], "entitlement_fingerprint": "f" * 64})
    assert await balances(conn, targets) == [Decimal(100)] * 3
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_payments"))
    ).scalar_one() == 0
    assert (
        await conn.execute(text("SELECT count(*) FROM stock_dividend_decisions"))
    ).scalar_one() == 0


@pytest.mark.parametrize(
    "field", ["portfolio_id", "user_id", "entitlement_id", "previous_application_id"]
)
async def test_final_sql_dividend_causal_row_rewrites_are_refused(dividend_portfolio_case, field):
    conn, targets = dividend_portfolio_case
    await apply(conn, targets[0])
    changed = await apply(conn, await successor(conn, targets[0]))
    with pytest.raises(DBAPIError):
        async with conn.begin_nested():
            await conn.execute(
                text(
                    f"UPDATE stock_dividend_decisions SET {field}=9223372036854775807 WHERE id=:d"  # noqa: S608 - fixed test parameter
                ),
                {"d": changed["decision_id"]},
            )
