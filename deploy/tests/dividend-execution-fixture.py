"""Synthetic retained dividend evidence with real restricted SQL cash effects.

Only owned ops clients embed this program. External announcements and opening
holdings are synthetic; payment/adjustment effects always use the SQL authority.
Clone verification never grants execution or changes restored financial rows.
"""

PROGRAM = r'''
import asyncio,hashlib,json,uuid
from dataclasses import asdict
from datetime import UTC,datetime,timedelta
from decimal import Decimal as D
from urllib.parse import urlsplit,urlunsplit
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.core.config import SchedulerSettings,Settings
from app.db.connection import database_connect_args
from app.services.stock_admission import ProductAdmission
from app.services.stock_quote_rules import CURATED_SYMBOLS
from app.services.stock_sessions import build_sessions
from app.services import stock_sessions,stock_trading
from app.schemas.stock_trades import TradeIn
from app.services.stock_status import persist_status_batch
from app.services.stock_status_rules import StatusBatch,StatusEvent
from app.services.corporate_actions import derive_dividend_entitlements,latest_verified_entitlements
from app.services.trading import execute as crypto_execute,Order

EMAIL='actual-dividend-sql@example.invalid'
SYMBOL='AMD'
EVENT='a1111111-1111-4111-8111-111111111111'

def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,default=str,separators=(',',':')).encode()).hexdigest()

async def connect(role=None):
 s=SchedulerSettings(env='test');args=database_connect_args(s)
 url=urlsplit(str(s.database_url).replace('postgresql+asyncpg://','postgresql://'))
 assert s.env=='test' and url.hostname=='postgres' and url.path=='/birja_source_test'
 if role:
  char={'app':'a','scheduler':'b'}[role] if args.get('ssl') else 'a'
  url=url._replace(netloc='birja_'+role+':'+char*64+'@postgres:5432')
 if DIVIDEND_DATABASE:url=url._replace(path='/'+DIVIDEND_DATABASE)
 conn=await asyncpg.connect(urlunsplit(url),**args)
 assert bool(await conn.fetchval('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))==bool(args.get('ssl'))
 return conn

def admission(product,now):
 scope={'application':'birja','audience':'authenticated-users','account':'birja','server':'birja',
  'feed':'iex','durable_accounting':True,'backup_restore':True,'retention_mode':'durable-accounting'}
 if product=='actions':scope.update(feed='alpaca-corporate-actions',capabilities=['rest','replay'],
  rest_symbols=sorted(CURATED_SYMBOLS),replay_region='us',all_us_replay_ingress=True)
 fields={'quotes':['bid','ask','event_at','symbol'],'status':['symbol','status','event_at'],'reference':['symbol','name','exchange','provider_asset_id'],
  'actions':['provider_event_id','symbol','event_type','process_date'],
  'calendar':['exchange','session_date','opens_at','closes_at']}
 calendar={} if product!='calendar' else {'exchanges':['XNYS','XNAS'],
  'version':'exchange-calendars-4.13.2/synthetic-dividend-dataset',
  'sources':['https://www.nyse.com/trade/hours-calendars','https://www.nasdaq.com/market-activity/stock-market-holiday-schedule'],
  'review_valid_until':(now+timedelta(hours=2)).isoformat(),
  'coverage_start':(now.date()-timedelta(days=45)).isoformat(),
  'coverage_end':(now.date()+timedelta(days=90)).isoformat(),'overrides':[]}
 return ProductAdmission(product=product,state='approved',generation=2000,
  reviewed_at=now-timedelta(hours=1),valid_from=now-timedelta(hours=1),valid_until=now+timedelta(hours=2),
  evidence_ref='synthetic-dividend-only:no-provider-rights',terms_version='synthetic-dividend-v1',
  collection_allowed=True,display_allowed=True,derived_allowed=True,retention_allowed=True,
  scope=scope,quota={'requests_per_minute':20,'symbols_per_request':20,'max_response_bytes':262144,
   'retention_seconds':315360000 if product=='actions' else 86400},
  allowed_fields=fields[product],attribution='IEX prices synthetic dividend fixture',calendar=calendar)

def calendar_dataset(base):
 # Explicit synthetic current-day session, while historical entitlement cutoffs
 # still use the reviewed package calendar. This makes actual service sells
 # deterministic outside US trading hours without changing historical times.
 original=stock_sessions._calendar_bounds
 def bounds(alias,start,end):
  return tuple((day,base-timedelta(hours=1),base+timedelta(hours=1)) if day==base.date() else (day,op,cl) for day,op,cl in original(alias,start,end))
 stock_sessions._calendar_bounds=bounds

async def derive(event_id,expected_quantity=D(2)):
 s=SchedulerSettings(env='test');engine=create_async_engine(s.database_url,connect_args=database_connect_args(s))
 try:
  async with async_sessionmaker(engine).begin() as db:
   rows=await derive_dividend_entitlements(db,event_id)
   assert len(rows)==1 and rows[0].state=='eligible' and rows[0].eligible_quantity==expected_quantity,rows
 finally:await engine.dispose()

async def prepare(owner):
 now=await owner.fetchval('SELECT clock_timestamp()')
 calendar_dataset(now)
 cid=await owner.fetchval('SELECT i.coin_id FROM stock_instruments i JOIN coins c ON c.id=i.coin_id WHERE c.symbol=$1',SYMBOL)
 assert cid
 async with owner.transaction():
  uid=await owner.fetchval('INSERT INTO users(email) VALUES ($1) RETURNING id',EMAIL)
  await owner.execute('INSERT INTO accounts(user_id,cash,starting_cash) VALUES ($1,100,10000)',uid)
  await owner.execute("UPDATE stock_instruments SET provider_asset_id='synthetic-dividend-AMD',provider_verified_at=$1 WHERE coin_id=$2",now,cid)
  for product in ('reference','actions','calendar','quotes','status'):
   values=asdict(admission(product,now));names=list(values)
   args=[json.dumps(v) if isinstance(v,(dict,list)) else v for v in values.values()]
   await owner.execute('INSERT INTO stock_data_admissions('+','.join(names)+') VALUES ('+
    ','.join('$'+str(i+1) for i in range(len(names)))+') ON CONFLICT(product) DO UPDATE SET '+
    ','.join(n+'=excluded.'+n for n in names if n!='product'),*args)
  sessions=build_sessions(now,admission('calendar',now))
  exchange=await owner.fetchval('SELECT listing_exchange FROM stock_instruments WHERE coin_id=$1',cid)
  eligible=[r for r in sessions if r.exchange==exchange and r.opens_at and r.closes_at<now-timedelta(days=2)]
  cutoff=max(eligible,key=lambda r:r.session_date)
  await owner.execute('DELETE FROM stock_sessions')
  for session in sessions:
   await owner.execute('INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation) VALUES ($1,$2,$3,$4,$5,$6,$7)',*asdict(session).values())
  await owner.execute("INSERT INTO stock_quotes(coin_id,bid,ask,mid,source,feed,event_at,collected_at,session_date,admission_generation,unit_epoch) VALUES ($1,10,12,11,'alpaca','iex',$2,$2,$3,2000,0) ON CONFLICT(coin_id) DO UPDATE SET bid=excluded.bid,ask=excluded.ask,mid=excluded.mid,event_at=excluded.event_at,collected_at=excluded.collected_at,session_date=excluded.session_date,admission_generation=excluded.admission_generation,unit_epoch=excluded.unit_epoch",cid,now,now.date())
  await owner.execute("INSERT INTO stock_action_state(coin_id,admission_generation,health,checked_at,valid_until,coverage_start,covered_until,journal_start_at,complete_from,sequence) VALUES ($1,2000,'current',$2,$2::timestamptz+interval '2 hours',$3,$2,$3,$3,1)",cid,now,cutoff.opens_at-timedelta(days=2))
  await owner.execute('INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) VALUES ($1,$2,2,0)',uid,cid)
  await owner.execute("INSERT INTO stock_ownership_movements(coin_id,user_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key) VALUES ($1,$2,1,$3,$4,2,0,2,0,0,0,'opening','synthetic-dividend-opening')",cid,uid,cutoff.opens_at-timedelta(days=1),now)
  event=await owner.fetchval('INSERT INTO stock_action_events(coin_id,economic_key,first_observed_at) VALUES ($1,$2,$3) RETURNING id',cid,EVENT,now)
  source=await owner.fetchval("INSERT INTO stock_action_sources(event_id,provider,product,provider_event_id) VALUES ($1,'alpaca','actions',$2) RETURNING id",event,EVENT)
  terms={'event_type':'cash_dividend','currency':'USD','subtype':'ordinary','foreign':False,
   'special':False,'due_bills':False,'identity_verified':True,'dates_verified':True,
   'cancelled':False,'identity_changed':False,'symbol':SYMBOL,
   'coin_id':cid,'process_date':str(cutoff.session_date),
   'rate':'0.5','ex_date':str(cutoff.session_date),'record_date':str(cutoff.session_date),
   'payable_date':str(cutoff.session_date+timedelta(days=1))}
  revision=await owner.fetchval("INSERT INTO stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason) VALUES ($1,$2,1,$3,'snapshot',$4,2000,$5::jsonb,'supported_dividend','supported') RETURNING id",event,source,digest(terms),now,json.dumps(terms))
  await owner.execute('UPDATE stock_action_events SET current_revision_id=$1 WHERE id=$2',revision,event)
 await derive(event)
 return event

async def target(owner,event):
 row=await owner.fetchrow('SELECT e.event_id,e.id entitlement_id,e.fingerprint entitlement_fingerprint,r.fingerprint revision_fingerprint FROM stock_dividend_entitlements e JOIN stock_action_events a ON a.id=e.event_id JOIN stock_action_revisions r ON r.id=a.current_revision_id WHERE e.event_id=$1 AND e.revision_id=r.id ORDER BY e.version DESC,e.id DESC LIMIT 1',event)
 assert row
 return dict(row)

async def apply(scheduler,work):
 row=await scheduler.fetchrow('SELECT * FROM public.apply_stock_dividend($1,$2,$3,$4)',work['event_id'],work['entitlement_id'],work['revision_fingerprint'],work['entitlement_fingerprint'])
 return dict(row)

async def revise(owner,event,rate,*,uncertain=False,reconcile=False):
 async with owner.transaction():
  old=await owner.fetchrow('SELECT r.* FROM stock_action_events a JOIN stock_action_revisions r ON r.id=a.current_revision_id WHERE a.id=$1',event)
  terms=json.loads(old['normalized_terms']);terms['rate']=rate;terms['cancelled']=uncertain
  fp=digest([terms,old['ordinal']+1])
  rid=await owner.fetchval("INSERT INTO stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason) VALUES ($1,$2,$3,$4,'snapshot',clock_timestamp(),2000,$5::jsonb,$6,'synthetic-revision') RETURNING id",event,old['source_id'],old['ordinal']+1,fp,json.dumps(terms),'cancelled' if uncertain else 'supported_dividend')
  await owner.execute('UPDATE stock_action_events SET current_revision_id=$1 WHERE id=$2',rid,event)
  await owner.execute('UPDATE stock_action_state SET epoch=epoch+1 WHERE coin_id=(SELECT coin_id FROM stock_action_events WHERE id=$1)',event)
  if reconcile:
   await owner.execute("""INSERT INTO stock_action_resolutions(event_id,coin_id,
    expected_revision,admission_generation,epoch,decision,decision_key,evidence,
    evidence_hash,before_digest,after_digest,actor_ref,created_at)
    SELECT a.id,a.coin_id,a.current_revision_id,2000,s.epoch,
    'accept_corrected_supported_revision','synthetic-dividend-reconciliation-'||a.current_revision_id,
    jsonb_build_object('format',1,'held_revision_ids',
     (SELECT jsonb_agg(r.id ORDER BY r.id) FROM stock_action_revisions r WHERE r.event_id=a.id)),
    repeat('a',64),repeat('b',64),repeat('c',64),'synthetic-reviewed-operator',clock_timestamp()
    FROM stock_action_events a JOIN stock_action_state s ON s.coin_id=a.coin_id WHERE a.id=$1""",event)
 if not uncertain:await derive(event)
 return fp

async def crypto(owner,side):
 s=SchedulerSettings(env='test');args=database_connect_args(s)
 url=urlsplit(str(s.database_url));url=url._replace(netloc='birja_app:'+'a'*64+'@postgres:5432')
 engine=create_async_engine(urlunsplit(url),connect_args=args)
 uid=await owner.fetchval('SELECT id FROM users WHERE email=$1',EMAIL)
 await owner.execute("INSERT INTO prices(coin_id,mid,as_of,source) SELECT id,10000,clock_timestamp(),'fake' FROM coins WHERE symbol='BTC' ON CONFLICT(coin_id) DO UPDATE SET mid=excluded.mid,as_of=excluded.as_of,source=excluded.source")
 amount=await owner.fetchval('SELECT cash FROM accounts WHERE user_id=$1',uid) if side=='buy' else await owner.fetchval("SELECT quantity FROM holdings h JOIN coins c ON c.id=h.coin_id WHERE h.user_id=$1 AND c.symbol='BTC'",uid)
 settings=Settings(env='test',database_url=urlunsplit(url),price_source='fake',redis_url='redis://localhost:6379/0',otp_hmac_secret='synthetic-only-otp-secret-'+'a'*64,jwt_secret='synthetic-only-jwt-secret-'+'a'*64)
 try:
  async with async_sessionmaker(engine)() as db:
   fill,created=await crypto_execute(db,user_id=uid,order=Order('BTC',side,'usd' if side=='buy' else 'quantity',amount),expected_mid=D(10000),idempotency_key=uuid.uuid4(),settings=settings)
   assert created
   return fill.cash_after
 finally:await engine.dispose()

async def sold_after_cutoff(owner):
 s=SchedulerSettings(env='test');args=database_connect_args(s);url=urlsplit(str(s.database_url))
 base=await owner.fetchval("SELECT reviewed_at+interval '1 hour' FROM stock_data_admissions WHERE product='calendar'")
 calendar_dataset(base)
 cid=await owner.fetchval('SELECT coin_id FROM stock_instruments i JOIN coins c ON c.id=i.coin_id WHERE c.symbol=$1',SYMBOL)
 uid=await owner.fetchval('SELECT id FROM users WHERE email=$1',EMAIL)
 engine=create_async_engine(s.database_url,connect_args=args)
 try:
  async with async_sessionmaker(engine).begin() as db:
   now=await owner.fetchval('SELECT clock_timestamp()')
   await owner.execute('UPDATE stock_quotes SET event_at=$2,collected_at=$2,session_date=$3 WHERE coin_id=$1',cid,now,now.date())
   await owner.execute('UPDATE stock_action_state SET checked_at=$2,covered_until=$2 WHERE coin_id=$1',cid,now)
   await persist_status_batch(db,StatusBatch((StatusEvent(cid,'synthetic-dividend-AMD','normal',now,now.date(),1,'synthetic-dividend-status'),),now,2000,1,baseline_verified=True,contiguous=True,complete=True,end_marker=True),coin_id=cid)
 finally:await engine.dispose()
 appurl=urlunsplit(url._replace(netloc='birja_app:'+'a'*64+'@postgres:5432'))
 engine=create_async_engine(appurl,connect_args=args)
 settings=Settings(env='test',database_url=appurl,price_source='fake',redis_url='redis://localhost:6379/0',otp_hmac_secret='synthetic-only-otp-secret-'+'a'*64,jwt_secret='synthetic-only-jwt-secret-'+'a'*64)
 try:
  async with async_sessionmaker(engine)() as db:
   fill,created=await stock_trading.execute(db,user_id=uid,order=TradeIn(symbol=SYMBOL,side='sell',quantity='2',expected_exec_price='10',idempotency_key=uuid.uuid4()),settings=settings)
   assert created and fill.cash_after==120
 finally:await engine.dispose()
 assert await owner.fetchval('SELECT quantity FROM holdings WHERE user_id=$1 AND coin_id=$2',uid,cid)==0

async def fingerprint(owner):
 rows=await owner.fetch("SELECT to_jsonb(p)::text value FROM stock_dividend_payments p JOIN users u ON u.id=p.user_id WHERE u.email=$1 UNION ALL SELECT to_jsonb(d)::text FROM stock_dividend_decisions d JOIN users u ON u.id=d.user_id WHERE u.email=$1 ORDER BY value",EMAIL)
 cash=await owner.fetchval('SELECT cash FROM accounts JOIN users ON users.id=accounts.user_id WHERE email=$1',EMAIL)
 return digest({'rows':[r['value'] for r in rows],'cash':str(cash)})

async def account_wait_revalidation(owner,scheduler,event):
 uid=await owner.fetchval('SELECT id FROM users WHERE email=$1',EMAIL)
 for kind,rate in [('rights','0.2'),('revision','0.3')]:
  await revise(owner,event,rate,reconcile=True)
  work=await target(owner,event)
  current=await owner.fetchval('SELECT current_revision_id FROM stock_action_events WHERE id=$1',event)
  before=await fingerprint(owner)
  lock=owner.transaction();await lock.start()
  task=None
  try:
   await owner.fetchval('SELECT cash FROM accounts WHERE user_id=$1 FOR UPDATE',uid)
   pid=scheduler.get_server_pid()
   task=asyncio.create_task(apply(scheduler,work))
   for _ in range(100):
    if await owner.fetchval('SELECT pg_backend_pid()=ANY(pg_blocking_pids($1))',pid):break
    if task.done():await task;raise AssertionError('authority finished before account wait')
    await asyncio.sleep(.02)
   else:raise AssertionError('restricted authority did not actually wait on account lock')
   if kind=='rights':await owner.execute("UPDATE stock_data_admissions SET state='denied' WHERE product='actions'")
   else:await owner.execute('UPDATE stock_action_events SET current_revision_id=(SELECT min(id) FROM stock_action_revisions WHERE event_id=$1) WHERE id=$1',event)
   await lock.commit()
   try:await asyncio.wait_for(task,5)
   except asyncpg.PostgresError as exc:assert exc.sqlstate=='22023',(kind,exc.sqlstate)
   else:raise AssertionError('changed '+kind+' accepted after genuine account wait')
   assert await fingerprint(owner)==before
  finally:
   if owner.is_in_transaction():await lock.rollback()
   if task and not task.done():task.cancel();await asyncio.gather(task,return_exceptions=True)
   if kind=='rights':await owner.execute("UPDATE stock_data_admissions SET state='approved' WHERE product='actions'")
   else:await owner.execute('UPDATE stock_action_events SET current_revision_id=$2 WHERE id=$1',event,current)
  result=await apply(scheduler,work)
  assert result['outcome']=='applied' and await apply(scheduler,work)==result

async def zero_original(owner,scheduler,event):
 old=await owner.fetchrow('SELECT r.*,a.coin_id FROM stock_action_revisions r JOIN stock_action_events a ON a.current_revision_id=r.id WHERE a.id=$1',event)
 terms=json.loads(old['normalized_terms']);terms['rate']='0.5'
 day=await owner.fetchval("SELECT max(session_date) FROM stock_sessions WHERE exchange=(SELECT listing_exchange FROM stock_instruments WHERE coin_id=$1) AND opens_at<(SELECT min(economic_at) FROM stock_ownership_movements WHERE coin_id=$1)",old['coin_id'])
 assert day
 terms.update(ex_date=str(day),record_date=str(day),payable_date=str(day+timedelta(days=1)),process_date=str(day))
 async with owner.transaction():
  await owner.execute('UPDATE stock_action_state SET journal_start_at=$2,complete_from=$2,coverage_start=$2 WHERE coin_id=$1',old['coin_id'],datetime.combine(day-timedelta(days=2),datetime.min.time(),tzinfo=UTC))
  zero=await owner.fetchval('INSERT INTO stock_action_events(coin_id,economic_key,first_observed_at) VALUES ($1,$2,clock_timestamp()) RETURNING id',old['coin_id'],'a2222222-2222-4222-8222-222222222222')
  source=await owner.fetchval("INSERT INTO stock_action_sources(event_id,provider,product,provider_event_id) VALUES ($1,'alpaca','actions','synthetic-zero-dividend') RETURNING id",zero)
  rid=await owner.fetchval("INSERT INTO stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason) VALUES ($1,$2,1,$3,'snapshot',clock_timestamp(),2000,$4::jsonb,'supported_dividend','supported') RETURNING id",zero,source,digest(terms),json.dumps(terms))
  await owner.execute('UPDATE stock_action_events SET current_revision_id=$2 WHERE id=$1',zero,rid)
 await derive(zero,D(0))
 cash=await owner.fetchval('SELECT cash FROM accounts JOIN users ON users.id=accounts.user_id WHERE email=$1',EMAIL)
 work=await target(owner,zero);result=await apply(scheduler,work)
 assert result['outcome']=='original' and result['decision_id'] is None and await apply(scheduler,work)==result
 assert await owner.fetchval('SELECT original_amount FROM stock_dividend_payments WHERE id=$1',result['payment_id'])==0
 assert await owner.fetchval('SELECT cash FROM accounts JOIN users ON users.id=accounts.user_id WHERE email=$1',EMAIL)==cash

async def denied(conn,query):
 try:
  async with conn.transaction():await conn.execute(query)
 except asyncpg.PostgresError as exc:assert exc.sqlstate=='42501',(query,exc.sqlstate)
 else:raise AssertionError('forbidden dividend operation succeeded: '+query)

async def exercise(owner):
 scheduler=await connect('scheduler');app=await connect('app')
 try:
  await sold_after_cutoff(owner)
  event=await owner.fetchval('SELECT id FROM stock_action_events WHERE economic_key=$1',EVENT)
  work=await target(owner,event);original=await apply(scheduler,work)
  assert original['outcome']=='original' and original['decision_id'] is None
  assert await apply(scheduler,work)==original
  assert await owner.fetchval('SELECT original_amount FROM stock_dividend_payments WHERE id=$1',original['payment_id'])==D(1)
  original_saved=await owner.fetchval('SELECT to_jsonb(p)::text FROM stock_dividend_payments p WHERE id=$1',original['payment_id'])
  for rate,delta,outcome in [('0.75',D('.5'),'applied'),('0.5',D('-.5'),'applied'),('0.5',D(0),'verified_no_change')]:
   await revise(owner,event,rate);new=await target(owner,event);result=await apply(scheduler,new)
   assert result['outcome']==outcome and await apply(scheduler,new)==result
   assert await owner.fetchval('SELECT applied_delta FROM stock_dividend_decisions WHERE id=$1',result['decision_id'])==delta
  uncertain=await revise(owner,event,'0.5',uncertain=True)
  settings=SchedulerSettings(env='test');engine=create_async_engine(settings.database_url,connect_args=database_connect_args(settings))
  try:
   async with async_sessionmaker(engine)() as db:assert await latest_verified_entitlements(db,event)==()
  finally:await engine.dispose()
  held=dict(await scheduler.fetchrow('SELECT * FROM public.record_stock_dividend_hold($1,$2)',original['payment_id'],uncertain))
  assert held['outcome']=='held_uncertain'
  assert dict(await scheduler.fetchrow('SELECT * FROM public.record_stock_dividend_hold($1,$2)',original['payment_id'],uncertain))==held
  assert await owner.fetchval('SELECT applied_delta FROM stock_dividend_decisions WHERE id=$1',held['decision_id'])==0
  unknown=await owner.fetchrow('SELECT desired_total,proposed_delta,entitlement_id FROM stock_dividend_decisions WHERE id=$1',held['decision_id'])
  assert all(value is None for value in unknown.values())
  await revise(owner,event,'0.75',reconcile=True)
  corrected=await target(owner,event);result=await apply(scheduler,corrected)
  assert result['outcome']=='applied' and await apply(scheduler,corrected)==result
  assert await owner.fetchval('SELECT previous_decision_id FROM stock_dividend_decisions WHERE id=$1',result['decision_id'])==held['decision_id']
  assert await crypto(owner,'buy')==0
  await revise(owner,event,'0.1',reconcile=True)
  deficit=await target(owner,event);held=await apply(scheduler,deficit)
  assert held['outcome']=='held_unaffordable' and await apply(scheduler,deficit)==held
  funded=await crypto(owner,'sell')
  success=await apply(scheduler,deficit)
  assert success['outcome']=='applied' and await apply(scheduler,deficit)==success
  assert await owner.fetchval('SELECT previous_decision_id FROM stock_dividend_decisions WHERE id=$1',success['decision_id'])==held['decision_id']
  assert await owner.fetchval('SELECT cash FROM accounts JOIN users ON users.id=accounts.user_id WHERE email=$1',EMAIL)==funded-D('1.3')
  assert await owner.fetchval('SELECT to_jsonb(p)::text FROM stock_dividend_payments p WHERE id=$1',original['payment_id'])==original_saved
  assert await apply(scheduler,work)==original
  await account_wait_revalidation(owner,scheduler,event)
  await zero_original(owner,scheduler,event)
  assert await owner.fetchval('SELECT count(*) FROM stock_dividend_payments p JOIN users u ON u.id=p.user_id WHERE u.email=$1',EMAIL)==2
  assert await owner.fetchval('SELECT count(*) FROM stock_dividend_decisions d JOIN users u ON u.id=d.user_id WHERE u.email=$1',EMAIL)==9
  for conn in (app,scheduler):
   for query in ('UPDATE stock_dividend_payments SET original_amount=original_amount','DELETE FROM stock_dividend_decisions',"SELECT public.stock_dividend_authority(1,1,'a','b',true,NULL)",'SET ROLE birja_migrator','CREATE TABLE public.forbidden_dividend_ddl(id bigint)','ALTER FUNCTION public.apply_stock_dividend(bigint,bigint,text,text) RENAME TO forbidden_dividend_replace'):
    await denied(conn,query)
  await denied(app,"SELECT * FROM public.apply_stock_dividend(1,1,repeat('a',64),repeat('b',64))")
  await denied(app,"SELECT * FROM public.record_stock_dividend_hold(1,repeat('a',64))")
  await denied(scheduler,'UPDATE accounts SET cash=cash')
  print('dividend_actual_sold_after_cutoff=true original_replay=true positive_negative_zero=true verified_zero_original=true uncertain_hold_reconcile=true crypto_deficit_successor=true actual_account_wait_rights_revision_refused=true',flush=True)
 finally:await scheduler.close();await app.close()

async def verify(owner):
 before=await fingerprint(owner)
 assert before==DIVIDEND_EXPECTED
 for role in ('app','scheduler'):
  conn=await connect(role)
  try:
   for query in ("SELECT * FROM public.apply_stock_dividend(1,1,repeat('a',64),repeat('b',64))", "SELECT * FROM public.record_stock_dividend_hold(1,repeat('a',64))",'UPDATE accounts SET cash=cash'):
    await denied(conn,query)
  finally:await conn.close()
 assert await fingerprint(owner)==before

async def main():
 owner=await connect()
 try:
  if DIVIDEND_MODE=='prepare':await prepare(owner)
  elif DIVIDEND_MODE=='exercise':await exercise(owner)
  elif DIVIDEND_MODE=='verify':await verify(owner)
  fp=await fingerprint(owner) if DIVIDEND_MODE not in ('prepare','snapshot') else digest([dict(r) for r in await owner.fetch("SELECT e.* FROM stock_dividend_entitlements e JOIN stock_action_events a ON a.id=e.event_id WHERE a.economic_key=$1 ORDER BY e.id",EVENT)])
  print('dividend_fixture_sha256='+fp,flush=True)
  print('dividend_sql_'+DIVIDEND_MODE+'=true verified_tls='+str(bool(database_connect_args(SchedulerSettings()).get('ssl'))).lower(),flush=True)
 finally:await owner.close()
asyncio.run(main())
'''


def program(*, mode: str, database: str | None = None, expected: str | None = None) -> str:
    if mode not in {"prepare", "snapshot", "exercise", "verify"}:
        raise ValueError("Unexpected dividend fixture operation")
    if database not in (None, "birja_restore_test") or (mode != "verify" and database):
        raise ValueError("Financial intent is source-only")
    if mode == "verify" and (
        database != "birja_restore_test" or expected is None or len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected)
    ):
        raise ValueError("Expected retained dividend fingerprint required")
    return (
        f"DIVIDEND_MODE={mode!r}\nDIVIDEND_DATABASE={database!r}\nDIVIDEND_EXPECTED={expected!r}\n"
        + PROGRAM
    )
