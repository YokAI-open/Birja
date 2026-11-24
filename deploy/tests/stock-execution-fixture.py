"""Synthetic execution and receipt consumers for disposable PostgreSQL fixtures.

The operations driver owns every container, database, and fixture credential.
"""

PROGRAM = r'''
import asyncio,json,uuid,os
from urllib.parse import urlsplit,urlunsplit
import asyncpg
from app.core.config import SchedulerSettings
from app.db.connection import database_connect_args

async def connect(role=None,database=None):
 s=SchedulerSettings();args=database_connect_args(s)
 url=urlsplit(str(s.database_url).replace('postgresql+asyncpg://','postgresql://'))
 if role:
  char={'app':'a','scheduler':'b'}[role] if args.get('ssl') else 'a'
  url=url._replace(netloc='birja_'+role+':'+char*64+'@'+url.hostname+':'+str(url.port or 5432))
 if database:url=url._replace(path='/'+database)
 conn=await asyncpg.connect(urlunsplit(url),**args)
 if args.get('ssl'):assert await conn.fetchval('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
 return conn

async def seed(conn):
 async with conn.transaction():
  now=await conn.fetchval('SELECT clock_timestamp()')
  cid=await conn.fetchval('SELECT max(coin_id) FROM stock_instruments')
  uid=await conn.fetchval("INSERT INTO users(email) VALUES ($1) RETURNING id",str(uuid.uuid4())+'@execution.invalid')
  await conn.execute('INSERT INTO accounts(user_id,cash,starting_cash) VALUES ($1,9980,10000)',uid)
  await conn.execute("UPDATE stock_instruments SET provider_asset_id='synthetic-execution',provider_verified_at=$1 WHERE coin_id=$2",now,cid)
  for product in ('reference','quotes','actions','status','calendar'):
   await conn.execute("""INSERT INTO stock_data_admissions
    (product,state,generation,reviewed_at,valid_from,valid_until,evidence_ref,terms_version,
     collection_allowed,display_allowed,derived_allowed,retention_allowed,calendar)
    VALUES ($1,'approved',1000,$2,$2::timestamptz-interval '1 hour',$2::timestamptz+interval '1 hour',
     'synthetic-execution','fixture',true,true,true,true,
     CASE WHEN $1='calendar' THEN jsonb_build_object('review_valid_until',$2::timestamptz+interval '1 hour') ELSE '{}'::jsonb END)
    ON CONFLICT(product) DO UPDATE SET state=excluded.state,generation=excluded.generation,
    reviewed_at=excluded.reviewed_at,valid_from=excluded.valid_from,valid_until=excluded.valid_until,
    evidence_ref=excluded.evidence_ref,terms_version=excluded.terms_version,
    collection_allowed=true,display_allowed=true,derived_allowed=true,retention_allowed=true,calendar=excluded.calendar""",product,now)
  await conn.execute("""INSERT INTO stock_quotes(coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation,unit_epoch)
   VALUES ($1,10,10,10,'alpaca','iex',$2,$2,$2::timestamptz::date,1000,0)
   ON CONFLICT(coin_id) DO UPDATE SET bid=10,ask=10,mid=10,event_at=excluded.event_at,
    collected_at=excluded.collected_at,session_date=excluded.session_date,admission_generation=1000,unit_epoch=0""",cid,now)
  await conn.execute("""INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation)
   SELECT listing_exchange,$2::timestamptz::date,$2::timestamptz-interval '1 hour',$2::timestamptz+interval '1 hour',
    $2::timestamptz::date,$2::timestamptz::date,1000 FROM stock_instruments WHERE coin_id=$1
   ON CONFLICT(exchange,session_date) DO UPDATE SET opens_at=excluded.opens_at,closes_at=excluded.closes_at,
    coverage_start=excluded.coverage_start,coverage_end=excluded.coverage_end,calendar_admission_generation=1000""",cid,now)
  await conn.execute("""INSERT INTO stock_status_evidence
   (coin_id,provider_asset_id,state,event_at,observed_at,session_date,admission_generation,continuity_generation,
    sequence,valid_until,bootstrap_verified,continuity_current,source_ref)
   VALUES ($1,'synthetic-execution','normal',$2,$2,$2::timestamptz::date,1000,1,1,$2::timestamptz+interval '60 seconds',true,true,'synthetic-execution')
   ON CONFLICT(coin_id) DO UPDATE SET event_at=excluded.event_at,observed_at=excluded.observed_at,
    session_date=excluded.session_date,valid_until=excluded.valid_until""",cid,now)
  await conn.execute("""INSERT INTO stock_action_state
   (coin_id,health,admission_generation,checked_at,valid_until,coverage_start,covered_until,
    journal_start_at,complete_from)
   VALUES ($1,'current',1000,$2,$2::timestamptz+interval '1 hour',$2::timestamptz-interval '1 day',$2,
    $2::timestamptz-interval '1 day',$2::timestamptz-interval '1 day')
   ON CONFLICT(coin_id) DO UPDATE SET health='current',admission_generation=1000,checked_at=excluded.checked_at,
    valid_until=excluded.valid_until,coverage_start=excluded.coverage_start,covered_until=excluded.covered_until,
    journal_start_at=coalesce(stock_action_state.journal_start_at,excluded.journal_start_at),
    complete_from=coalesce(stock_action_state.complete_from,excluded.complete_from)""",cid,now)
  snapshot=await conn.fetchval("""SELECT jsonb_build_object(
   'coin_id',i.coin_id,'provider_asset_id',i.provider_asset_id,
   'admissions',(SELECT jsonb_agg(jsonb_build_object('product',product,'generation',generation,
    'row_hash',encode(sha256(convert_to(to_jsonb(a)::text,'UTF8')),'hex'),'valid_from',valid_from,
    'valid_until',valid_until,'approved',true) ORDER BY product) FROM stock_data_admissions a),
   'action_current',true,'action_valid_until',ac.valid_until,'next_blocking_at',null,
   'safety_epoch',ac.epoch,'unit_epoch',ac.unit_epoch,'status',to_jsonb(st),
   'session_state','open','session_date',se.session_date,'opens_at',se.opens_at,'closes_at',se.closes_at,
   'session_valid_until',ac.valid_until,'calendar_generation',se.calendar_admission_generation,
   'quote',(to_jsonb(q)-'mid')||jsonb_build_object('provider_asset_id',i.provider_asset_id))
   FROM stock_instruments i JOIN stock_quotes q USING(coin_id) JOIN stock_status_evidence st USING(coin_id)
   JOIN stock_action_state ac USING(coin_id) JOIN stock_sessions se ON se.exchange=i.listing_exchange
   AND se.session_date=q.session_date WHERE i.coin_id=$1""",cid)
  tid=await conn.fetchval("""INSERT INTO trades(user_id,coin_id,side,input_kind,input_value,quantity,
   mid_price,price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key)
   VALUES ($1,$2,'buy','quantity',2,2,10,$3,10,0,-20,9980,$4) RETURNING id""",uid,cid,now,uuid.UUID('99999999-1111-4111-8111-111111111111'))
  await conn.execute("""INSERT INTO stock_fill_facts(trade_id,coin_id,user_id,provider_asset_id,symbol,
   company_name,listing_exchange,source,feed,bid,ask,exact_mid,held_after,event_at,collected_at,observed_at,
   session_date,opens_at,closes_at,authority)
   SELECT $1,i.coin_id,$2,i.provider_asset_id,c.symbol,c.name,i.listing_exchange,'alpaca','iex',
    10,10,10,2,$3,$3,$3,$3::timestamptz::date,$3::timestamptz-interval '1 hour',$3::timestamptz+interval '1 hour',$4::jsonb
   FROM stock_instruments i JOIN coins c ON c.id=i.coin_id WHERE i.coin_id=$5""",tid,uid,now,snapshot,cid)
  await conn.execute("""INSERT INTO stock_ownership_movements(coin_id,user_id,sequence,economic_at,
   recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,trade_id,causal_key)
   SELECT $1,$2,coalesce(max(sequence),0)+1,$3,$3,2,0,2,0,20,0,'fill',$4,
    'synthetic-execution:'||($4::bigint)::text FROM stock_ownership_movements WHERE coin_id=$1""",cid,uid,now,tid)
  await conn.execute('INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) VALUES ($1,$2,2,20)',uid,cid)
  await conn.execute('SET CONSTRAINTS ALL IMMEDIATE')
  await conn.execute('SELECT public.assert_stock_execution_current($1,$2,$3::jsonb)',tid,uid,snapshot)
 return tid,uid,cid,snapshot

async def denied(conn,query,expected='42501'):
 try:
  async with conn.transaction():await conn.execute(query)
 except asyncpg.PostgresError as exc:assert exc.sqlstate==expected,(query,exc.sqlstate)
 else:raise AssertionError('forbidden execution operation succeeded: '+query)

async def check_history(database,coin_id):
 from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
 from app.services.stock_ownership import assert_ownership_consistent
 settings=SchedulerSettings()
 url=urlsplit(str(settings.database_url))
 if database:url=url._replace(path='/'+database)
 engine=create_async_engine(urlunsplit(url),connect_args=database_connect_args(settings))
 try:
  async with async_sessionmaker(engine).begin() as db:
   await assert_ownership_consistent(db,coin_id)
 finally:await engine.dispose()

async def consume(database=None):
 app=await connect('app',database);scheduler=await connect('scheduler',database)
 reader=await connect(database=database) if database else app
 try:
  row=await reader.fetchrow("""SELECT t.id,t.user_id,t.coin_id,t.idempotency_key,t.cash_after,
    f.held_after,f.authority FROM trades t JOIN stock_fill_facts f ON f.trade_id=t.id
    WHERE t.idempotency_key='99999999-1111-4111-8111-111111111111'""")
  assert row and row['cash_after']==9980 and row['held_after']==2
  await check_history(database,row['coin_id'])
  assert await app.fetchval('SELECT held_after FROM stock_fill_facts WHERE trade_id=$1',row['id'])==2
  if database:await denied(app,'SELECT * FROM trades')
  before=await reader.fetchval('SELECT count(*) FROM trades')
  await denied(reader,"""INSERT INTO trades(id,user_id,coin_id,side,input_kind,input_value,quantity,
   mid_price,price_as_of,exec_price,fee,cash_delta,cash_after,idempotency_key)
   OVERRIDING SYSTEM VALUE SELECT 9223372036854775806,user_id,coin_id,side,input_kind,input_value,quantity,mid_price,price_as_of,
   exec_price,fee,cash_delta,cash_after,idempotency_key FROM trades
   WHERE idempotency_key='99999999-1111-4111-8111-111111111111'""",'23505')
  assert await reader.fetchval('SELECT count(*) FROM trades')==before
  for query in ('UPDATE stock_fill_facts SET held_after=held_after','DELETE FROM stock_fill_facts',
    'UPDATE stock_status_evidence SET sequence=sequence','UPDATE stock_data_admissions SET reviewed_at=now()',
    'SET ROLE birja_migrator'):
   await denied(app,query)
  for query in ('SELECT * FROM stock_fill_facts','UPDATE accounts SET cash=cash',
    "SELECT public.assert_stock_execution_current(1,1,'{}')",'SET ROLE birja_migrator'):
   await denied(scheduler,query)
  # A permitted status write is tested in a rolled-back transaction so restore
  # equality still covers the original exact row and sequence values.
  transaction=scheduler.transaction();await transaction.start()
  try:
   await scheduler.execute('UPDATE stock_status_evidence SET sequence=sequence+1 WHERE coin_id=$1',row['coin_id'])
  finally:await transaction.rollback()
 finally:
  if reader is not app:await reader.close()
  await app.close();await scheduler.close()

async def run():
 conn=await connect(database=FIXTURE_DATABASE)
 verified_tls=await conn.fetchval('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()')
 try:
  if FIXTURE_SEED:
   # Distinct receipts for the same stock exercise unique canonical hash order.
   await seed(conn)
   tid,uid,cid,snapshot=await seed(conn)
   app=await connect('app')
   try:await app.execute('SELECT public.assert_stock_execution_current($1,$2,$3::jsonb)',tid,uid,snapshot)
   finally:await app.close()
  await consume(FIXTURE_DATABASE)
 finally:await conn.close()
 return verified_tls
actual_tls=asyncio.run(run())
print('execution_receipt_exact=true duplicate_fill_rejected=true ownership_consistent=true guard_consumer='+str(FIXTURE_SEED).lower()+' verified_tls='+str(actual_tls).lower()+' runtime_grants_narrow=true')
'''


def program(*, seed: bool, database: str | None = None) -> str:
    if database not in (None, "birja_restore_test"):
        raise ValueError("Unexpected synthetic database")
    return f"FIXTURE_SEED={seed!r}\nFIXTURE_DATABASE={database!r}\n" + PROGRAM


async def reported_receipt_fixture(mode, before=None):
    """Exercise exact receipt replay through restricted TLS on a disposable PG18 clone."""
    import hashlib
    import inspect
    import json
    from dataclasses import asdict, replace
    from datetime import UTC, datetime, time, timedelta
    from decimal import Decimal
    from urllib.parse import urlsplit, urlunsplit
    from uuid import UUID

    from sqlalchemy import insert, text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.core.config import Settings
    from app.db.connection import database_connect_args
    from app.db.schema_contract import require_schema
    from app.models.stock import StockDataAdmission, StockSession
    from app.schemas.stock_trades import TradeIn
    from app.services import stock_sessions, stock_trading
    from app.services.accounts import get_or_create_user
    from app.services.portfolios import OwnedActivePortfolio
    from tests.test_stock_admission import action_admitted, admitted
    from tests.test_stock_sessions import evidence

    if mode not in {"alpaca", "nasdaq-rss", "replay", "replay-legacy"}:
        raise ValueError("Unknown synthetic receipt fixture mode")
    replaying = mode in {"replay", "replay-legacy"}
    revision = "0023" if mode in {"alpaca", "replay-legacy"} else "0024"
    consumer = "retained0023" if revision == "0023" else "retained0024"
    settings = Settings(stock_data_enabled=True)
    url = urlsplit(settings.database_url)
    database = "/birja_restore_test" if replaying else "/birja_test"
    if (
        settings.env != "test"
        or url.hostname != "127.0.0.1"
        or url.port != 55434
        or url.username != "birja_test"
        or url.path != database
        or url.query
        or not settings.database_ssl_ca_file
    ):
        raise ValueError("Owned disposable TLS database required")
    args = database_connect_args(settings)
    admin = create_async_engine(settings.database_url, connect_args=args)
    restricted = url._replace(netloc="birja_app:test-app@127.0.0.1:55434")
    app = create_async_engine(urlunsplit(restricted), connect_args=args)
    scheduler_url = url._replace(
        netloc="birja_scheduler:test-scheduler@127.0.0.1:55434"
    )
    scheduler = create_async_engine(urlunsplit(scheduler_url), connect_args=args)
    client = async_sessionmaker(app, expire_on_commit=False)
    sides = ("buy",) if mode == "alpaca" else ("buy", "sell")
    prefix = 18 if mode == "alpaca" else 24
    try:
        for role in (app, scheduler):
            async with role.connect() as conn:
                assert await conn.scalar(
                    text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
                )
                assert await require_schema(conn, consumer=consumer) == revision
        if not replaying:
            async with client.begin() as db:
                uid, created = await get_or_create_user(
                    db, f"disposable-{prefix}@execution.invalid"
                )
                assert created
                pid = await db.scalar(
                    text("SELECT id FROM accounts WHERE user_id=:uid"), {"uid": uid}
                )
            now = datetime.now(UTC)
            calendar = evidence(now)

            def synthetic_bounds(alias, start, end):
                today = now.date()
                tomorrow = today + timedelta(days=1)
                midnight = datetime.combine(today, time.min, UTC)
                start_at = datetime.combine(tomorrow, time(14), UTC)
                return (
                    (
                        today,
                        max(midnight, now - timedelta(hours=1)),
                        now + timedelta(hours=1),
                    ),
                    (tomorrow, start_at, start_at + timedelta(hours=6)),
                )

            stock_sessions._calendar_bounds = synthetic_bounds
            async with async_sessionmaker(admin).begin() as db:
                for item in (
                    admitted("reference"),
                    admitted("quotes"),
                    action_admitted(),
                    admitted("status"),
                    calendar,
                ):
                    scope = {
                        **item.scope,
                        "durable_accounting": True,
                        "backup_restore": True,
                        "retention_mode": "durable-accounting",
                    }
                    if item.product == "status" and mode == "nasdaq-rss":
                        scope["feed"] = mode
                    row = replace(
                        item,
                        reviewed_at=now - timedelta(hours=1),
                        valid_from=now - timedelta(hours=1),
                        valid_until=now + timedelta(hours=1),
                        scope=scope,
                    )
                    await db.execute(
                        text(
                            "DELETE FROM stock_data_admissions WHERE product=:product"
                        ),
                        {"product": item.product},
                    )
                    await db.execute(insert(StockDataAdmission).values(**asdict(row)))
                cid = await db.scalar(text("SELECT id FROM coins WHERE symbol='AAPL'"))
                values = {
                    "cid": cid,
                    "at": now,
                    "day": now.date(),
                    "source": mode,
                    "legacy": mode == "alpaca",
                    "sequence": int(mode == "alpaca"),
                    "digest": "previous-report" if mode == "alpaca" else "b" * 64,
                }
                await db.execute(
                    text(
                        "UPDATE stock_instruments SET provider_asset_id='synthetic-AAPL', provider_verified_at=:at WHERE coin_id=:cid"
                    ),
                    values,
                )
                await db.execute(text("DELETE FROM stock_sessions"))
                await db.execute(
                    insert(StockSession),
                    [
                        asdict(row)
                        for row in stock_sessions.build_sessions(now, calendar)
                    ],
                )
                await db.execute(
                    text("DELETE FROM stock_quotes WHERE coin_id=:cid"), values
                )
                await db.execute(
                    text("""INSERT INTO stock_quotes (coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation,unit_epoch)
                    VALUES (:cid,100,102,101,'alpaca','iex',:at,:at,:day,4,0)"""),
                    values,
                )
                await db.execute(
                    text("""INSERT INTO stock_action_state (coin_id,health,admission_generation,checked_at,valid_until,coverage_start,covered_until,journal_start_at,complete_from)
                    VALUES (:cid,'current',4,:at,CAST(:at AS timestamptz)+interval '1 hour',CAST(:at AS timestamptz)-interval '1 day',:at,CAST(:at AS timestamptz)-interval '1 day',CAST(:at AS timestamptz)-interval '1 day')
                    ON CONFLICT (coin_id) DO UPDATE SET checked_at=excluded.checked_at,valid_until=excluded.valid_until,covered_until=excluded.covered_until"""),
                    values,
                )
                await db.execute(
                    text("DELETE FROM stock_status_evidence WHERE coin_id=:cid"), values
                )
                await db.execute(
                    text("""INSERT INTO stock_status_evidence (coin_id,provider_asset_id,source,state,event_at,observed_at,valid_until,session_date,admission_generation,continuity_generation,sequence,bootstrap_verified,continuity_current,source_ref)
                    VALUES (:cid,'synthetic-AAPL',:source,'normal',:at,:at,CAST(:at AS timestamptz)+interval '60 seconds',:day,4,1,:sequence,:legacy,:legacy,:digest)"""),
                    values,
                )
            receipts = []
            for index, side in enumerate(sides):
                order = TradeIn(
                    symbol="AAPL",
                    side=side,
                    quantity="1",
                    expected_exec_price="102" if side == "buy" else "100",
                    idempotency_key=UUID(int=prefix + index),
                )
                async with client() as db:
                    fill, created = await stock_trading.execute(
                        db,
                        portfolio=OwnedActivePortfolio(pid, uid),
                        order=order,
                        settings=settings,
                    )
                    assert created and fill.fee == 0
                    assert fill.cash_after == Decimal(9898 if side == "buy" else 9998)
                    receipts.append(
                        {
                            "uid": uid,
                            "order": order.model_dump(mode="json"),
                            "fill": fill.model_dump(mode="json"),
                        }
                    )
            print("stock_receipts=" + json.dumps(receipts, sort_keys=True))
            return receipts

        assert len(before) == (1 if mode == "replay-legacy" else 3)
        # The exact released _receipt reader from v0.7.0 has this source hash.
        reader = inspect.getsource(stock_trading._receipt).strip().encode()
        assert (
            hashlib.sha256(reader).hexdigest()
            == "5eeb442388041b4534949d27bccbb70d81c07218e65dd984c9d989b4d4879e4d"
        )
        async with admin.connect() as conn:
            assert await conn.scalar(
                text(
                    "SELECT count(*) FROM stock_status_evidence WHERE source='nasdaq-rss' AND valid_until <= clock_timestamp()"
                )
            ) == int(mode == "replay")
            assert await conn.scalar(
                text("SELECT count(*) FROM stock_fill_facts")
            ) == len(before)
        for original in before:
            uid = original["uid"]
            order = TradeIn.model_validate(original["order"])
            portfolio = OwnedActivePortfolio(int(original["fill"]["portfolio_id"]), uid)
            async with client() as db:
                replay, created = await stock_trading.execute(
                    db, portfolio=portfolio, order=order, settings=settings
                )
            assert not created and replay.model_dump(mode="json") == original["fill"]
        if mode == "replay-legacy":
            print("legacy_stock_receipt_replay=true verified_tls=true")
        else:
            print(
                "stock_receipt_replay=true retained_reader_exact=true expired_report_retained=true verified_tls=true"
            )
    finally:
        await scheduler.dispose()
        await app.dispose()
        await admin.dispose()
