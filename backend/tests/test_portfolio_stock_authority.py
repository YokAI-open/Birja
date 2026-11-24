"""Static0017 contracts and real final-schema restricted stock authority proofs.

The final_sql cases require actual Alembic0017. Collection before Plan07 is
intentional; this module never installs SQL or fabricates a final schema.
"""

import ast
import json
import re
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from tests.portfolio_fixtures import close_empty_test_root, portfolio_world
from tests.test_migrations import EXPECTED_HEAD

__all__ = ["portfolio_world"]

ASSET = Path(__file__).parents[1] / "alembic/sql/0017_stock_portfolio.sql"
SIGNATURES = {
    "check_stock_fill_integrity()",
    "assert_stock_execution_current(bigint,bigint,jsonb)",
    "check_stock_split_digest_version()",
}


@pytest_asyncio.fixture
async def stock_authority_case(engine, migrated):
    """Private setup; each business call below explicitly assumes a narrow role.

    The admin connection is the repository's disposable test harness only. No
    authority grant is invented here:0017 must create all runtime privileges.
    All setup is rolled back, including the fresh synthetic owners and roots.
    """
    async with engine.connect() as conn:
        tx = await conn.begin()
        assert (
            await conn.execute(text("SELECT version_num FROM alembic_version"))
        ).scalar_one() == EXPECTED_HEAD
        owners = []
        for label in ("owned", "foreign"):
            owners.append(
                (
                    await conn.execute(
                        text("INSERT INTO users(email) VALUES (:e) RETURNING id"),
                        {"e": f"{label}-{uuid4()}@example.test"},
                    )
                ).scalar_one()
            )
        roots = []
        for owner, label, closed in (
            (owners[0], "First", False),
            (owners[0], "Sibling", False),
            (owners[0], "Closed", True),
            (owners[1], "Foreign", False),
        ):
            roots.append(
                (
                    await conn.execute(
                        text("""INSERT INTO accounts
              (user_id,name,name_key,cash,starting_cash) VALUES
              (:u,:name,public.portfolio_name_key(:name),9980,12000)
              RETURNING id"""),
                        {"u": owner, "name": label, "closed": closed},
                    )
                ).scalar_one()
            )
            if closed:
                await close_empty_test_root(conn, roots[-1])
        cid = (await conn.execute(text("SELECT min(coin_id) FROM stock_instruments"))).scalar_one()
        await conn.execute(
            text(
                "SELECT pg_advisory_xact_lock(hashtextextended("
                "'birja.stock.instrument:' || CAST(:c AS text),0))"
            ),
            {"c": str(cid)},
        )
        now = (await conn.execute(text("SELECT clock_timestamp()"))).scalar_one()
        await conn.execute(
            text("""UPDATE stock_instruments SET provider_asset_id='fixture-asset',
          provider_verified_at=:n WHERE coin_id=:c"""),
            {"n": now, "c": cid},
        )
        for product in ("reference", "quotes", "actions", "status", "calendar"):
            await conn.execute(
                text("""INSERT INTO stock_data_admissions
              (product,state,generation,reviewed_at,valid_from,valid_until,evidence_ref,terms_version,
              collection_allowed,display_allowed,derived_allowed,retention_allowed,scope,calendar)
              VALUES (:p,'approved',1,:n,CAST(:n AS timestamptz)-interval '1 hour',
              CAST(:n AS timestamptz)+interval '1 hour','synthetic-only','fixture',
              true,true,true,true,
              jsonb_build_object('feed','iex'),
              CASE WHEN :p='calendar' THEN jsonb_build_object('review_valid_until',
              CAST(:n AS timestamptz)+interval '1 hour') ELSE '{}'::jsonb END)"""),
                {"p": product, "n": now},
            )
        await conn.execute(
            text("""INSERT INTO stock_quotes
          (coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation,unit_epoch)
          VALUES (:c,10,10,10,'alpaca','iex',:n,:n,CAST(:n AS timestamptz)::date,1,0)"""),
            {"c": cid, "n": now},
        )
        await conn.execute(
            text("""INSERT INTO stock_sessions
          (exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation)
          SELECT listing_exchange,CAST(:n AS timestamptz)::date,
          CAST(:n AS timestamptz)-interval '1 hour',CAST(:n AS timestamptz)+interval '1 hour',
          CAST(:n AS timestamptz)::date,CAST(:n AS timestamptz)::date,1
          FROM stock_instruments WHERE coin_id=:c"""),
            {"c": cid, "n": now},
        )
        await conn.execute(
            text("""INSERT INTO stock_status_evidence
          (coin_id,provider_asset_id,state,event_at,observed_at,session_date,admission_generation,
          continuity_generation,sequence,valid_until,bootstrap_verified,continuity_current,source_ref)
          VALUES (:c,'fixture-asset','normal',:n,:n,CAST(:n AS timestamptz)::date,1,1,1,
          CAST(:n AS timestamptz)+interval '60 seconds',true,true,'synthetic-only')"""),
            {"c": cid, "n": now},
        )
        await conn.execute(
            text("""INSERT INTO stock_action_state
          (coin_id,health,admission_generation,checked_at,valid_until,coverage_start,covered_until)
          VALUES (:c,'current',1,:n,CAST(:n AS timestamptz)+interval '1 hour',
          CAST(:n AS timestamptz)-interval '1 day',:n)"""),
            {"c": cid, "n": now},
        )
        for root, owner in ((roots[0], owners[0]), (roots[1], owners[0])):
            await conn.execute(
                text("""INSERT INTO holdings
              (portfolio_id,user_id,coin_id,quantity,cost_basis) VALUES (:p,:u,:c,2,20)"""),
                {"p": root, "u": owner, "c": cid},
            )
        snapshot = (
            await conn.execute(
                text("""SELECT jsonb_build_object(
          'portfolio_id',CAST(:p AS bigint),'coin_id',i.coin_id,
          'provider_asset_id',i.provider_asset_id,
          'admissions',(SELECT jsonb_agg(jsonb_build_object(
          'product',product,'generation',generation,
          'row_hash',encode(sha256(convert_to(to_jsonb(a)::text,'UTF8')),'hex'),
          'valid_from',valid_from,'valid_until',valid_until,'approved',true) ORDER BY product)
          FROM stock_data_admissions a),
          'action_current',true,'action_valid_until',ac.valid_until,'next_blocking_at',null,
          'safety_epoch',ac.epoch,'unit_epoch',ac.unit_epoch,'status',to_jsonb(st),
          'session_state','open','session_date',se.session_date,'opens_at',se.opens_at,
          'closes_at',se.closes_at,'session_valid_until',ac.valid_until,
          'calendar_generation',se.calendar_admission_generation,
          'quote',(to_jsonb(q)-'mid')||jsonb_build_object('provider_asset_id',i.provider_asset_id))
          FROM stock_instruments i JOIN stock_quotes q USING(coin_id)
          JOIN stock_status_evidence st USING(coin_id) JOIN stock_action_state ac USING(coin_id)
          JOIN stock_sessions se ON se.exchange=i.listing_exchange
            AND se.session_date=q.session_date
          WHERE i.coin_id=:c"""),
                {"p": roots[0], "c": cid},
            )
        ).scalar_one()
        case = {
            "coin": cid,
            "owner": owners[0],
            "foreign_owner": owners[1],
            "first": roots[0],
            "sibling": roots[1],
            "closed": roots[2],
            "foreign": roots[3],
            "now": now,
            "snapshot": snapshot,
        }
        try:
            yield conn, case
        finally:
            await tx.rollback()


async def append_fill(conn, case, *, root=None, fact_root=None, movement_root=None, key=None):
    """Direct SQL receipt; independent literal money expected values."""
    root = case["first"] if root is None else root
    tid = (
        await conn.execute(
            text("""INSERT INTO trades
      (portfolio_id,user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
      exec_price,fee,cash_delta,cash_after,idempotency_key)
      VALUES (:p,:u,:c,'buy','quantity',2,2,10,:n,10,0,-20,9980,:key) RETURNING id"""),
            {
                "p": root,
                "u": case["owner"],
                "c": case["coin"],
                "n": case["now"],
                "key": key or uuid4(),
            },
        )
    ).scalar_one()
    await conn.execute(
        text("""INSERT INTO stock_fill_facts
      (trade_id,portfolio_id,coin_id,user_id,provider_asset_id,symbol,company_name,listing_exchange,
      source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,observed_at,session_date,
      opens_at,closes_at,authority)
      VALUES (:t,:p,:c,:u,'fixture-asset','AAPL','Synthetic company','NASDAQ','alpaca','iex',
      10,10,10,2,:n,:n,:n,CAST(:n AS timestamptz)::date,
      CAST(:n AS timestamptz)-interval '1 hour',CAST(:n AS timestamptz)+interval '1 hour',
      CAST(:authority AS jsonb))"""),
        {
            "t": tid,
            "p": root if fact_root is None else fact_root,
            "c": case["coin"],
            "u": case["owner"],
            "n": case["now"],
            "authority": json.dumps(case["snapshot"]),
        },
    )
    await conn.execute(
        text("""INSERT INTO stock_ownership_movements
      (portfolio_id,coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,
      after_quantity,before_basis,after_basis,unit_epoch,cause_kind,trade_id,causal_key)
      VALUES (:p,:c,:u,:seq,:n,:n,2,0,2,0,20,0,'fill',:t,:key)"""),
        {
            "p": root if movement_root is None else movement_root,
            "c": case["coin"],
            "u": case["owner"],
            "seq": tid,
            "n": case["now"],
            "t": tid,
            "key": f"fill:{tid}",
        },
    )
    return tid


async def assert_current(conn, tid, case, snapshot=None, owner=None):
    await conn.execute(
        text("SELECT public.assert_stock_execution_current(:t,:u,CAST(:s AS jsonb))"),
        {
            "t": tid,
            "u": case["owner"] if owner is None else owner,
            "s": json.dumps(case["snapshot"] if snapshot is None else snapshot),
        },
    )


async def test_final_sql_stock_current_exact_owned_receipt_and_sibling_unchanged(
    stock_authority_case,
):
    conn, case = stock_authority_case
    await conn.execute(text("SET LOCAL ROLE birja_app"))
    tid = await append_fill(conn, case)
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    await assert_current(conn, tid, case)  # Last business statement before commit/release.
    await conn.execute(text("RESET ROLE"))
    assert (
        await conn.execute(
            text("SELECT cash,starting_cash FROM accounts WHERE id=:p"), {"p": case["sibling"]}
        )
    ).one() == (Decimal("9980"), Decimal("12000"))
    assert (
        await conn.execute(
            text("SELECT quantity,cost_basis FROM holdings WHERE portfolio_id=:p AND coin_id=:c"),
            {"p": case["sibling"], "c": case["coin"]},
        )
    ).one() == (Decimal("2"), Decimal("20"))


@pytest.mark.parametrize("part", ["fact", "movement", "foreign"])
async def test_final_sql_stock_cross_root_causes_refused(stock_authority_case, part):
    conn, case = stock_authority_case
    await conn.execute(text("SET LOCAL ROLE birja_app"))
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await append_fill(
                conn,
                case,
                fact_root=case["foreign"]
                if part == "foreign"
                else case["sibling"]
                if part == "fact"
                else None,
                movement_root=case["sibling"] if part == "movement" else None,
            )
            await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert error.value.orig.sqlstate in {"23503", "23514"}


@pytest.mark.parametrize("target", ["closed", "foreign"])
async def test_final_sql_stock_inactive_or_foreign_root_refused(stock_authority_case, target):
    conn, case = stock_authority_case
    await conn.execute(text("SET LOCAL ROLE birja_app"))
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await append_fill(conn, case, root=case[target])
            await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    assert error.value.orig.sqlstate in {"23503", "23514"}


@pytest.mark.parametrize(
    "change", ["missing_root", "sibling_root", "foreign_owner", "cash", "holding", "closed"]
)
async def test_final_sql_stock_final_validator_rejects_changed_root_state(
    stock_authority_case, change
):
    conn, case = stock_authority_case
    await conn.execute(text("SET LOCAL ROLE birja_app"))
    tid = await append_fill(conn, case)
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    await conn.execute(text("RESET ROLE"))
    body = dict(case["snapshot"])
    if change == "missing_root":
        body.pop("portfolio_id")
    if change == "sibling_root":
        body["portfolio_id"] = case["sibling"]
    if change == "cash":
        await conn.execute(
            text("UPDATE accounts SET cash=cash+1 WHERE id=:p"), {"p": case["first"]}
        )
    if change == "holding":
        await conn.execute(
            text("UPDATE holdings SET quantity=3 WHERE portfolio_id=:p AND coin_id=:c"),
            {"p": case["first"], "c": case["coin"]},
        )
    if change == "closed":
        # Deliberately inconsistent UNCOMMITTED negative fixture. Retain the
        # final-validator refusal independently of the new deferred root guard;
        # the outer transaction always rolls back and never publishes it.
        await conn.execute(text("SET CONSTRAINTS portfolio_terminal_root DEFERRED"))
        await conn.execute(
            text("UPDATE accounts SET closed_at=clock_timestamp() WHERE id=:p"),
            {"p": case["first"]},
        )
    await conn.execute(text("SET LOCAL ROLE birja_app"))
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await assert_current(
                conn, tid, case, body, case["foreign_owner"] if change == "foreign_owner" else None
            )
    assert error.value.orig.sqlstate == "22023"


async def test_final_sql_stock_user_global_key_cannot_execute_in_sibling(stock_authority_case):
    conn, case = stock_authority_case
    key = uuid4()
    await conn.execute(text("SET LOCAL ROLE birja_app"))
    await append_fill(conn, case, key=key)
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await append_fill(conn, case, root=case["sibling"], key=key)
    assert error.value.orig.sqlstate == "23505"


@pytest.mark.parametrize("table", ["trades", "stock_fill_facts", "stock_ownership_movements"])
@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
async def test_final_sql_stock_facts_and_payload_bytes_immutable(stock_authority_case, table, verb):
    conn, case = stock_authority_case
    await conn.execute(text("SET LOCAL ROLE birja_app"))
    tid = await append_fill(conn, case)
    await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    before = (
        await conn.execute(
            text("SELECT authority::text FROM stock_fill_facts WHERE trade_id=:t"), {"t": tid}
        )
    ).scalar_one()
    column = "id" if table == "trades" else "trade_id"
    field = "cash_after" if table == "trades" else column
    sql = (
        f"UPDATE public.{table} SET {field}={field} WHERE {column}=:t"  # noqa: S608 - fixed inventory
        if verb == "UPDATE"
        else f"DELETE FROM public.{table} WHERE {column}=:t"  # noqa: S608 - fixed inventory
    )  # noqa: S608 - fixed parametrized inventory
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await conn.execute(text(sql), {"t": tid})
    assert error.value.orig.sqlstate in {"23514", "42501"}
    assert (
        await conn.execute(
            text("SELECT authority::text FROM stock_fill_facts WHERE trade_id=:t"), {"t": tid}
        )
    ).scalar_one() == before


async def test_final_sql_stock_function_inventory_owners_paths_and_grants(portfolio_world):
    conn, _ = portfolio_world
    rows = (
        (
            await conn.execute(
                text("""SELECT p.proname,p.prosecdef,p.proconfig,
      pg_get_userbyid(p.proowner) owner,
      EXISTS(SELECT FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner)))
        WHERE grantee=0 AND privilege_type='EXECUTE') public,
      has_function_privilege('birja_app',p.oid,'EXECUTE') app,
      has_function_privilege('birja_scheduler',p.oid,'EXECUTE') scheduler
      FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
      WHERE n.nspname='public' AND p.proname IN
      ('check_stock_fill_integrity','assert_stock_execution_current','check_stock_split_digest_version')""")
            )
        )
        .mappings()
        .all()
    )
    assert len(rows) == 3
    for row in rows:
        assert row["owner"] == "birja_migrator" and not row["prosecdef"] and not row["public"]
        assert row["proconfig"] == ["search_path=pg_catalog, public, pg_temp"]
        assert row["app"] == (row["proname"] == "assert_stock_execution_current")
        assert not row["scheduler"]


@pytest.mark.parametrize("marker", [None, 0, 1, 3])
async def test_final_sql_stock_new_split_marker_requires_explicit_two(stock_authority_case, marker):
    from tests.test_stock_action_migrations import event

    conn, case = stock_authority_case
    eid, _, rid = await event(conn, case["coin"])
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await conn.execute(
                text("""INSERT INTO stock_split_applications
              (economic_event_id,coin_id,revision_id,new_rate,old_rate,cutoff,
              processed_at,prior_unit_epoch,new_unit_epoch,sequence_boundary,
              before_digest,after_digest,owner_digest_version)
              VALUES (:e,:c,:r,'2','1',clock_timestamp(),clock_timestamp(),0,1,0,:d,:d,:v)"""),
                {"e": eid, "c": case["coin"], "r": rid, "f": "a" * 64, "d": "b" * 64, "v": marker},
            )
    assert error.value.orig.sqlstate == "23514"


async def append_split(conn, case, marker=2):
    from tests.test_stock_action_migrations import event

    eid, _, rid = await event(conn, case["coin"])
    return (
        await conn.execute(
            text("""INSERT INTO stock_split_applications
      (economic_event_id,coin_id,revision_id,new_rate,old_rate,cutoff,processed_at,
      prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest,owner_digest_version)
      VALUES (:e,:c,:r,'2','1',clock_timestamp(),clock_timestamp(),0,1,0,:d,:d,:v)
      RETURNING id"""),
            {"e": eid, "c": case["coin"], "r": rid, "d": "b" * 64, "v": marker},
        )
    ).scalar_one()


@pytest.mark.parametrize("verb", ["UPDATE", "DELETE"])
async def test_final_sql_stock_explicit_two_marker_and_immutable_global_application(
    stock_authority_case, verb
):
    conn, case = stock_authority_case
    sid = await append_split(conn, case)
    assert (
        await conn.execute(
            text("SELECT owner_digest_version FROM stock_split_applications WHERE id=:s"),
            {"s": sid},
        )
    ).scalar_one() == 2
    statement = (
        "UPDATE stock_split_applications SET owner_digest_version=NULL WHERE id=:s"
        if verb == "UPDATE"
        else "DELETE FROM stock_split_applications WHERE id=:s"
    )
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await conn.execute(text(statement), {"s": sid})
    assert error.value.orig.sqlstate == "23514"


@pytest.mark.parametrize("variant", ["sibling_once", "forged_epoch", "closed"])
async def test_final_sql_stock_split_global_cause_with_owned_effects(stock_authority_case, variant):
    conn, case = stock_authority_case
    sid = await append_split(conn, case)
    statement = text("""INSERT INTO stock_ownership_movements
      (portfolio_id,coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,
      after_quantity,before_basis,after_basis,unit_epoch,cause_kind,application_id,causal_key)
      VALUES (:p,:c,:u,:seq,clock_timestamp(),clock_timestamp(),
      2,2,4,20,20,:epoch,'split',:s,:key)""")
    params = {
        "p": case["first"],
        "c": case["coin"],
        "u": case["owner"],
        "seq": 1,
        "epoch": 1,
        "s": sid,
        "key": f"split:{sid}",
    }
    await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
    if variant == "sibling_once":
        await conn.execute(statement, params)
        await conn.execute(statement, {**params, "p": case["sibling"], "seq": 2})
        with pytest.raises(DBAPIError) as error:
            async with conn.begin_nested():
                await conn.execute(statement, {**params, "seq": 3})
        assert error.value.orig.sqlstate == "23505"
    else:
        with pytest.raises(DBAPIError) as error:
            async with conn.begin_nested():
                await conn.execute(
                    statement,
                    {
                        **params,
                        "p": case["closed"] if variant == "closed" else case["first"],
                        "epoch": 2 if variant == "forged_epoch" else 1,
                    },
                )
                await conn.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        assert error.value.orig.sqlstate in {"23503", "23514"}


async def test_final_sql_stock_scheduler_cannot_call_execution_validator(stock_authority_case):
    conn, case = stock_authority_case
    await conn.execute(text("SET LOCAL ROLE birja_scheduler"))
    with pytest.raises(DBAPIError) as error:
        async with conn.begin_nested():
            await assert_current(conn, 1, case)
    assert error.value.orig.sqlstate == "42501"


def sql_function(sql, name):
    match = re.search(
        rf"CREATE OR REPLACE FUNCTION public\.{name}\(.*?END \$[a-z]+\$;",
        sql,
        re.S,
    )
    assert match is not None, name
    return match.group()


def test_asset_contract_exact_private_function_inventory_and_invoker_search_paths():
    sql = ASSET.read_text()
    assert re.findall(r"CREATE OR REPLACE FUNCTION public\.(\w+)\(", sql) == [
        "check_stock_fill_integrity",
        "assert_stock_execution_current",
        "check_stock_split_digest_version",
    ]
    for name in (
        "check_stock_fill_integrity",
        "assert_stock_execution_current",
        "check_stock_split_digest_version",
    ):
        function = sql_function(sql, name)
        assert "LANGUAGE plpgsql SECURITY INVOKER" in function
        assert "SET search_path=pg_catalog,public,pg_temp" in function
        assert "SECURITY DEFINER" not in function
    assert "assert_stock_execution_current(p_trade bigint,p_user bigint,p_expected jsonb)" in sql
    assert "RETURNS void" in sql_function(sql, "assert_stock_execution_current")
    for signature in SIGNATURES:
        assert f"ALTER FUNCTION public.{signature} OWNER TO birja_migrator;" in sql


def test_asset_contract_retains_independent_0013_economic_and_market_checks():
    sql = ASSET.read_text()
    retained = ast.parse((ASSET.parent.parent / "versions/0013_stock_execution.py").read_text())
    old = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in retained.body
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
    }
    for name, function in (
        ("INTEGRITY", "check_stock_fill_integrity"),
        ("FINAL_GUARD", "assert_stock_execution_current"),
    ):
        current = sql_function(sql, function)
        # Independent retained source is immutable: none of its explicit refusal
        # outcomes may disappear when adding portfolio ownership.
        messages = re.findall(r"RAISE EXCEPTION '([^']+)'", old[name])
        assert messages and all(f"RAISE EXCEPTION '{message}'" in current for message in messages)
    integrity = sql_function(sql, "check_stock_fill_integrity")
    for expression in (
        "t.fee<>0",
        "t.input_kind<>'quantity'",
        "t.input_value<>t.quantity",
        "t.quantity=trunc(t.quantity)",
        "t.price_as_of<>f.event_at",
        "mod(trunc(n*100),2)=1",
        "mod(trunc(f.exact_mid*1e8),2)=1",
        "m.after_basis<>expected_basis",
        "m.cause_kind<>'fill'",
        "m.application_id IS NOT NULL",
    ):
        assert expression in integrity
    authority = sql_function(sql, "assert_stock_execution_current")
    for expression in (
        "facts.authority IS DISTINCT FROM p_expected",
        "jsonb_array_length(r.admissions)<>5",
        "a->>'state'<>'approved'",
        "a->'collection_allowed'",
        "a->'display_allowed'",
        "a->'retention_allowed'",
        "a->'derived_allowed'",
        "r.held OR r.changed_split",
        "r.pending_boundary",
        "ac.health<>'current'",
        "ac.next_blocking_at",
        "st.state<>'normal'",
        "st.bootstrap_verified AND st.continuity_current",
        "ses.opens_at<=now_at AND now_at<ses.closes_at",
        "q.source='alpaca' AND q.feed='iex'",
        "q.event_at>now_at-interval '120 seconds'",
        "tr.exec_price<>",
    ):
        assert expression in authority


def test_asset_contract_final_snapshot_pairs_every_financial_root_and_finishes_with_validation():
    sql = ASSET.read_text()
    authority = sql_function(sql, "assert_stock_execution_current")
    for expression in (
        "root.id=t.portfolio_id AND root.user_id=t.user_id",
        "h.portfolio_id=t.portfolio_id AND h.user_id=t.user_id",
        "r.portfolio_closed_at IS NOT NULL",
        "r.portfolio_owner<>p_user",
        "r.portfolio_id::text IS DISTINCT FROM p_expected->>'portfolio_id'",
        "facts.portfolio_id IS DISTINCT FROM tr.portfolio_id",
        "r.movement_portfolio IS DISTINCT FROM tr.portfolio_id",
        "r.movement_owner IS DISTINCT FROM tr.user_id",
        "r.portfolio_cash IS DISTINCT FROM tr.cash_after",
        "r.portfolio_held IS DISTINCT FROM facts.held_after",
        "r.portfolio_basis IS DISTINCT FROM r.after_basis",
        "en.portfolio_id=t.portfolio_id",
    ):
        assert expression in authority
    before, after = authority.split("now_at:=clock_timestamp();")
    assert "INTO r FROM public.trades" in before
    # No new table read, lock or mutation can follow the final authority snapshot
    # and its post-read clock sample. Only record/JSON comparisons remain.
    assert not re.search(r"\b(?:FROM|JOIN) public\.", after)
    assert not re.search(r"\b(?:UPDATE|INSERT|DELETE|PERFORM|FOR UPDATE)\b", authority)
    assert after.rstrip().endswith("END $final$;")
    integrity = sql_function(sql, "check_stock_fill_integrity")
    for expression in (
        "TG_WHEN='BEFORE' AND TG_OP='INSERT'",
        "id=NEW.portfolio_id AND user_id=NEW.user_id",
        "root.closed_at IS NOT NULL",
        "t.portfolio_id IS DISTINCT FROM f.portfolio_id",
        "t.portfolio_id IS DISTINCT FROM m.portfolio_id",
    ):
        assert expression in integrity


def test_asset_contract_new_split_marker_is_explicit_with_no_legacy_mutation_path():
    sql = ASSET.read_text()
    marker = sql_function(sql, "check_stock_split_digest_version")
    assert "NEW.owner_digest_version IS DISTINCT FROM 2::smallint" in marker
    assert "USING ERRCODE='23514'" in marker
    assert "BEFORE INSERT ON public.stock_split_applications" in sql
    assert "EXECUTE FUNCTION public.check_stock_split_digest_version()" in sql
    assert not re.search(r"\b(?:UPDATE|DELETE FROM) public\.stock_split_applications", sql)
    assert "associate_legacy_portfolio_only" not in sql
    # The expansion owns column/check shape;0017 must preserve the no-default
    # legacy NULL interpretation rather than backfill global applications.
    expansion = (ASSET.parent.parent / "versions/0015_portfolio_expansion.py").read_text()
    assert '"owner_digest_version", sa.SmallInteger(), nullable=True' in expansion
    assert "owner_digest_version IS NULL OR owner_digest_version=2" in expansion


def test_asset_contract_insert_triggers_and_execute_grants_are_narrow():
    sql = ASSET.read_text()
    assert re.findall(r"CREATE TRIGGER (\w+) BEFORE INSERT ON public\.(\w+)", sql) == [
        ("stock_split_digest_version", "stock_split_applications"),
        ("portfolio_stock_active_insert", "trades"),
        ("portfolio_stock_active_insert", "stock_fill_facts"),
        ("portfolio_stock_active_insert", "stock_ownership_movements"),
    ]
    assert sql.count("EXECUTE FUNCTION public.check_stock_fill_integrity();") == 3
    assert "public.check_stock_split_digest_version() FROM PUBLIC;" in sql
    assert re.findall(r"GRANT EXECUTE ON FUNCTION public\.(.*?)\s+TO (\w+);", sql, re.S) == [
        ("assert_stock_execution_current(bigint,bigint,jsonb)", "birja_app")
    ]
    assert "FROM birja_scheduler;" in sql and "FROM birja_app;" in sql
    assert not re.search(r"\bGRANT\s+(?:ALL|UPDATE|INSERT|DELETE|CREATE)", sql)
