"""Static0017 dividend contracts and real final-schema authority proofs.

The final_sql cases require real Alembic0017. Before Plan07 only collection
and static asset contracts run; no test fabricates or installs a final schema.
"""

import ast
import json
import re
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
            ).scalar_one() == "0027"
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
                            text("""INSERT INTO accounts(user_id,name,name_key,cash,starting_cash)
                            VALUES (:u,:n,public.portfolio_name_key(:n),100,12345.67)
                            RETURNING id"""),
                            {"u": uid, "n": label},
                        )
                    ).scalar_one()
                )
            cid = (
                await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))
            ).scalar_one()
            await conn.execute(
                text(
                    "SELECT pg_advisory_xact_lock(hashtextextended("
                    "'birja.stock.instrument:' || CAST(:c AS text),0))"
                ),
                {"c": str(cid)},
            )
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
    # This independent SQL negative remains uncommitted and rolls back. A paid
    # operation sets constraints immediate; defer only the new root guard so
    # the original dividend authority's closed-state refusal is still tested.
    await conn.execute(text("SET CONSTRAINTS portfolio_terminal_root DEFERRED"))
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
    await conn.execute(text("SET CONSTRAINTS portfolio_terminal_root DEFERRED"))
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


@pytest.mark.parametrize("forgery", ["sibling", "foreign", "owner"])
async def test_final_sql_dividend_payment_tuple_cannot_pair_foreign_entitlement(
    dividend_portfolio_case, forgery
):
    conn, targets = dividend_portfolio_case
    original = await apply(conn, targets[0])
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            # Actual migration owner can INSERT, so this proves causal SQL
            # constraints rather than merely scheduler's lack of DML grants.
            await conn.execute(text("SET LOCAL ROLE birja_migrator"))
            await conn.execute(
                text("""INSERT INTO stock_dividend_payments(event_id,coin_id,portfolio_id,
                user_id,revision_id,revision_fingerprint,entitlement_id,entitlement_fingerprint,
                symbol,company_name,cutoff,cutoff_rule,units_basis,unit_epoch,eligible_quantity,
                rate,ex_date,record_date,payable_date,original_amount,recorded_at,cash_after)
                SELECT event_id,coin_id,:p,:u,revision_id,revision_fingerprint,entitlement_id,
                entitlement_fingerprint,symbol,company_name,cutoff,cutoff_rule,units_basis,
                unit_epoch,eligible_quantity,rate,ex_date,record_date,payable_date,
                original_amount,recorded_at,cash_after
                FROM stock_dividend_payments WHERE id=:id"""),
                {
                    "p": targets[1 if forgery == "sibling" else 2]["portfolio_id"],
                    "u": targets[0 if forgery != "foreign" else 2]["user_id"],
                    "id": original["payment_id"],
                },
            )
            await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert error.value.orig.sqlstate == "23503"
    assert await balances(conn, targets) == [Decimal(101), Decimal(100), Decimal(100)]


async def test_final_sql_dividend_exact_routine_security_and_guarded_database(
    dividend_portfolio_case,
):
    conn, _ = dividend_portfolio_case
    rows = (
        await conn.execute(
            text("""SELECT p.oid::regprocedure::text,p.prosecdef,
        r.rolname,p.proconfig FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
        JOIN pg_roles r ON r.oid=p.proowner WHERE n.nspname='public'
        AND p.proname IN ('stock_dividend_authority','apply_stock_dividend',
        'record_stock_dividend_hold','reject_stock_dividend_mutation')""")
        )
    ).all()
    assert {r[0].replace(" ", "") for r in rows} == SIGNATURES
    for signature, definer, owner, config in rows:
        assert owner == "birja_migrator"
        assert definer == signature.startswith(
            ("apply_stock_dividend(", "record_stock_dividend_hold(")
        )
        assert "search_path=pg_catalog, public, pg_temp" in config
    # Local pytest transport is guarded in conftest; verified-TLS ops proofs
    # run independently in16/18/27, not fabricated by this local SQL fixture.
    assert (await conn.execute(text("SELECT current_database()"))).scalar_one() == "birja_test"


def sql_function(sql, name):
    match = re.search(rf"CREATE OR REPLACE FUNCTION public\.{name}\(.*?END \$[a-z]+\$;", sql, re.S)
    assert match is not None, name
    return match.group()


def test_asset_contract_exact_retained_signatures_security_and_private_inventory():
    sql = ASSET.read_text()
    assert re.findall(r"CREATE OR REPLACE FUNCTION public\.(\w+)\(", sql) == [
        "reject_stock_dividend_mutation",
        "stock_dividend_authority",
        "apply_stock_dividend",
        "record_stock_dividend_hold",
    ]
    assert "p_event bigint,p_entitlement bigint,p_revision text,p_fingerprint text," in sql
    assert "p_verified boolean,p_expected jsonb)" in sql
    assert "record_stock_dividend_hold(p_payment bigint,p_revision text)" in sql
    for name in ("apply_stock_dividend", "record_stock_dividend_hold"):
        body = sql_function(sql, name)
        assert "RETURNS TABLE(payment_id bigint,decision_id bigint,outcome text)" in body
        assert "SECURITY DEFINER" in body
    for name in ("reject_stock_dividend_mutation", "stock_dividend_authority"):
        assert "SECURITY INVOKER" in sql_function(sql, name)
    for signature in SIGNATURES:
        assert f"REVOKE ALL ON FUNCTION public.{signature} FROM PUBLIC;" in sql
        assert f"ALTER FUNCTION public.{signature} OWNER TO birja_migrator;" in sql
    for name in (
        "reject_stock_dividend_mutation",
        "stock_dividend_authority",
        "apply_stock_dividend",
        "record_stock_dividend_hold",
    ):
        assert "SET search_path=pg_catalog,public,pg_temp" in sql_function(sql, name)
    assert re.findall(r"GRANT EXECUTE ON FUNCTION (.*?) TO (\w+);", sql, re.S) == [
        (
            "public.apply_stock_dividend(bigint,bigint,text,text),\n "
            "public.record_stock_dividend_hold(bigint,text)",
            "birja_scheduler",
        )
    ]
    assert "GRANT UPDATE" not in sql
    assert "GRANT INSERT" not in sql
    assert "REVOKE UPDATE(cash) ON public.accounts FROM birja_scheduler;" in sql
    assert "public.stock_dividend_decisions_id_seq FROM birja_app,birja_scheduler;" in sql


def test_asset_contract_preserves_0014_independent_economics_and_refusal_outcomes():
    sql = ASSET.read_text()
    tree = ast.parse((ASSET.parent.parent / "versions/0014_dividend_accounting.py").read_text())
    old = {
        n.targets[0].id: ast.literal_eval(n.value)
        for n in tree.body
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)
    }
    for key, name in (
        ("AUTHORITY", "stock_dividend_authority"),
        ("APPLY", "apply_stock_dividend"),
        ("HOLD", "record_stock_dividend_hold"),
        ("IMMUTABILITY", "reject_stock_dividend_mutation"),
    ):
        body = sql_function(sql, name)
        messages = re.findall(r"RAISE EXCEPTION '([^']+)'", old[key])
        assert messages and all(f"RAISE EXCEPTION '{message}'" in body for message in messages)
    body = sql_function(sql, "apply_stock_dividend")
    for expression in (
        "raw:=en.eligible_quantity*(terms->>'rate')::numeric",
        "raw*100-cents=0.5 AND mod(cents,2)=1",
        "delta:=desired-cumulative",
        "WHEN cash+delta<0 THEN 'held_unaffordable'",
        "ELSE 'applied' END",
        "applied:=CASE WHEN result_outcome='applied' THEN delta ELSE 0 END",
        "SET CONSTRAINTS ALL IMMEDIATE",
        "ON CONFLICT DO NOTHING",
    ):
        assert expression in body
    authority = sql_function(sql, "stock_dividend_authority")
    for expression in (
        "r.entitlement).eligible_quantity=r.historical_quantity",
        "r.entitlement).last_movement_sequence=r.historical_sequence",
        "NOT r.unresolved_split",
        "NOT r.held",
        "OR r.newer",
        "r.revision).classification='supported_dividend'",
        "terms->>'currency'='USD'",
        "terms->>'subtype'='ordinary'",
        "r.action).complete_from<=(r.entitlement).cutoff",
        "r.action).covered_until>=(r.entitlement).cutoff",
        "dividend hold needs uncertainty",
        "backup_restore",
        "durable_accounting",
        "retention_mode",
        "dividend cutoff calendar changed",
    ):
        assert expression in authority


def test_asset_contract_entitlement_derived_active_root_and_same_root_correction_chain():
    sql = ASSET.read_text()
    authority = sql_function(sql, "stock_dividend_authority")
    for expression in (
        "ac.id=en.portfolio_id AND ac.user_id=en.user_id",
        "r.portfolio_id IS NULL OR r.portfolio_closed_at IS NOT NULL",
        "m.portfolio_id=en.portfolio_id AND m.user_id=en.user_id",
        "newer.portfolio_id=en.portfolio_id",
        "result IS DISTINCT FROM p_expected",
    ):
        assert expression in authority
    body = sql_function(sql, "apply_stock_dividend")
    assert "en0.user_id,en0.portfolio_id INTO cid,uid,pid" in body
    assert body.index("pg_advisory_xact_lock") < body.index("FOR UPDATE")
    assert "ac.id=pid AND ac.user_id=uid AND ac.closed_at IS NULL FOR UPDATE" in body
    assert body.index("dividend portfolio unavailable") < body.index("original.id IS NOT NULL")
    assert "p.event_id=p_event AND p.portfolio_id=pid AND p.user_id=uid" in body
    assert body.count("WHERE id=pid AND user_id=uid AND closed_at IS NULL") == 2
    assert "WHERE user_id=uid;" not in body
    assert "d.portfolio_id=pid AND d.user_id=uid" in body
    assert "VALUES(original.id,pid,uid,p_event" in body
    hold_body = sql_function(sql, "record_stock_dividend_hold")
    assert hold_body.index("pg_advisory_xact_lock") < hold_body.index("FOR UPDATE")
    assert "ac.id=original.portfolio_id AND ac.user_id=original.user_id" in hold_body
    assert "e.portfolio_id=original.portfolio_id" in hold_body
    assert "d.portfolio_id=original.portfolio_id" in hold_body
    assert "VALUES(original.id,original.portfolio_id,original.user_id" in hold_body
    assert hold_body.index("dividend portfolio unavailable") < hold_body.index("IF did IS NULL")
    assert "d.portfolio_id=NEW.portfolio_id" in sql_function(sql, "reject_stock_dividend_mutation")


def test_asset_contract_final_validation_is_last_business_statement():
    sql = ASSET.read_text()
    for name in ("apply_stock_dividend", "record_stock_dividend_hold"):
        body = sql_function(sql, name)
        before, after = body.rsplit("final_authority:=public.stock_dividend_authority(", 1)
        assert "SET CONSTRAINTS ALL IMMEDIATE;" in before
        assert not re.search(r"\b(?:FROM|JOIN) public\.", after)
        assert not re.search(r"\b(?:UPDATE|INSERT|DELETE|PERFORM|FOR UPDATE)\b", after)
        assert after.count("RETURN QUERY SELECT") == 1
    authority = sql_function(sql, "stock_dividend_authority")
    before, after = authority.split("n:=clock_timestamp();")
    assert "INTO r FROM public.stock_action_events" in before
    assert not re.search(r"\b(?:FROM|JOIN) public\.", after)
    assert not re.search(r"\b(?:UPDATE|INSERT|DELETE|PERFORM|FOR UPDATE)\b", authority)
