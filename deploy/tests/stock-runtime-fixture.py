"""Actual stock services on isolated source/TLS/restored connections.

Synthetic external inputs are constructed independently of application tests.
Restored financial tables remain quarantined: owner replay/read proof and actual
app denial are separate, with no grant repair or new financial intent on clones.
"""

PROGRAM = r"""
import asyncio,hashlib,os,uuid
from dataclasses import asdict
from datetime import UTC,datetime,timedelta
from decimal import Decimal as D
from sqlalchemy import select,func,delete,update,text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.core.config import SchedulerSettings,Settings
from app.db.connection import database_connect_args
from app.models.stock import StockInstrument,StockDataAdmission,StockSession,StockQuote
from app.models.stock_execution import StockStatusEvidence
from app.models.corporate_action import StockActionState
from app.models.price import Coin
from app.models.trade import Holding,Trade
from app.models.user import User,Account
from app.schemas.stock_trades import QuoteIn,TradeIn
from app.services import stock_sessions,stock_trading,portfolio,corporate_actions
from app.services.stock_admission import ProductAdmission
from app.services.stock_quote_rules import CURATED_SYMBOLS
from app.services.stock_status import persist_status_batch
from app.services.stock_status_rules import StatusBatch,StatusEvent
from app.services.accounts import get_or_create_user
from app.services.stock_ownership import assert_ownership_consistent,reconstruct_stock_quantity
from app.services.corporate_action_rules import CutoffEvidence,NormalizedAction
from app.services.alpaca_actions import ActionBatch,ActionObservation
from app.services.trading import execute as crypto_execute,Order
from app.services.prices import AcceptedPrice,upsert_prices
from app.services.trade_math import TradeRefused
from app.services.event_history import list_event_history

KEY=uuid.UUID('88888888-2222-4222-8222-222222222222')
EMAIL='actual-stock-runtime@example.invalid'

def admission(product,base):
 fields={'reference':['symbol','name','exchange','provider_asset_id'],'quotes':['bid','ask','event_at','symbol'],'status':['symbol','status','event_at'],'calendar':['exchange','session_date','opens_at','closes_at'],'actions':['provider_event_id','symbol','event_type','process_date']}
 scope={'application':'birja','audience':'authenticated-users','account':'birja','server':'birja','feed':'iex','durable_accounting':True,'backup_restore':True,'retention_mode':'durable-accounting'}
 if product=='actions':scope.update(feed='alpaca-corporate-actions',capabilities=['rest','replay'],rest_symbols=sorted(CURATED_SYMBOLS),replay_region='us',all_us_replay_ingress=True)
 calendar={} if product!='calendar' else {'exchanges':['XNYS','XNAS'],'version':'exchange-calendars-4.13.2/synthetic-runtime-dataset','sources':['https://www.nyse.com/trade/hours-calendars','https://www.nasdaq.com/market-activity/stock-market-holiday-schedule'],'review_valid_until':(base+timedelta(hours=1)).isoformat(),'coverage_start':(base.date()-timedelta(days=45)).isoformat(),'coverage_end':(base.date()+timedelta(days=90)).isoformat(),'overrides':[]}
 return ProductAdmission(product=product,state='approved',generation=2000,reviewed_at=base-timedelta(hours=1),valid_from=base-timedelta(hours=1),valid_until=base+timedelta(hours=1),evidence_ref='synthetic-runtime-only:no-provider-rights',terms_version='synthetic-runtime-v1',collection_allowed=True,display_allowed=True,derived_allowed=True,retention_allowed=True,scope=scope,quota={'requests_per_minute':20,'symbols_per_request':20,'max_response_bytes':262144,'retention_seconds':315360000 if product=='actions' else 86400},allowed_fields=fields[product],attribution='IEX prices synthetic runtime only',calendar=calendar)

def calendar_dataset(base):
 original=stock_sessions._calendar_bounds
 def bounds(alias,start,end):
  return tuple((day,base-timedelta(hours=1),base+timedelta(hours=1)) if day==base.date() else (day,op,cl) for day,op,cl in original(alias,start,end))
 stock_sessions._calendar_bounds=bounds

def fingerprint(fill):return hashlib.sha256(fill.model_dump_json().encode()).hexdigest()

async def main():
 s=SchedulerSettings(env='test');args=database_connect_args(s);url=make_url(s.database_url)
 assert s.env=='test' and url.host=='postgres' and url.database=='birja_source_test'
 if RUNTIME_DATABASE:url=url.set(database=RUNTIME_DATABASE)
 engines={'owner':create_async_engine(url,connect_args=args)}
 for role,char in [('app','a'),('scheduler','b')]:
  engines[role]=create_async_engine(url.set(username='birja_'+role,password=(char if args.get('ssl') else 'a')*64),connect_args=args)
 sessions={role:async_sessionmaker(e,expire_on_commit=False) for role,e in engines.items()}
 settings=Settings(env='test',database_url=str(url.render_as_string(hide_password=False)),redis_url='redis://:synthetic-only@redis:6379/0',otp_hmac_secret='synthetic-runtime-otp-'+'a'*64,jwt_secret='synthetic-runtime-jwt-'+'b'*64)
 try:
  async with sessions['owner']() as db:
   actual=(await db.execute(select(func.current_database()))).scalar_one()
   assert actual==('birja_restore_test' if RUNTIME_DATABASE else 'birja_source_test')
   tls=(await db.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))).scalar_one()
   assert bool(tls)==bool(args.get('ssl'))
   base=(await db.execute(select(func.clock_timestamp()))).scalar_one() if RUNTIME_SEED else (await db.execute(select(StockDataAdmission.reviewed_at).where(StockDataAdmission.product=='calendar'))).scalar_one()+timedelta(hours=1)
   cid=(await db.execute(select(StockInstrument.coin_id).join(Coin).where(Coin.symbol=='MCD'))).scalar_one()
   exchange=(await db.execute(select(StockInstrument.listing_exchange).where(StockInstrument.coin_id==cid))).scalar_one()
  calendar_dataset(base)
  if RUNTIME_SEED:
   async with sessions['owner'].begin() as db:
    for product in ('reference','quotes','actions','status','calendar'):
     values=asdict(admission(product,base))
     await db.execute(insert(StockDataAdmission).values(**values).on_conflict_do_update(index_elements=['product'],set_={k:v for k,v in values.items() if k!='product'}))
    await db.execute(update(StockInstrument).where(StockInstrument.coin_id==cid).values(provider_asset_id='synthetic-actual-MCD',provider_verified_at=base))
    await db.execute(delete(StockSession))
    await db.execute(insert(StockSession),[asdict(r) for r in stock_sessions.build_sessions(base,admission('calendar',base))])
    await db.execute(insert(StockActionState).values(coin_id=cid,admission_generation=2000,health='current',checked_at=base,valid_until=base+timedelta(hours=1),coverage_start=base-timedelta(days=1),covered_until=base,journal_start_at=base-timedelta(days=1),complete_from=base-timedelta(days=1)))
    quote_values=dict(coin_id=cid,bid=D(100),ask=D(102),mid=D(101),source='alpaca',feed='iex',event_at=base,collected_at=base,session_date=base.date(),admission_generation=2000,unit_epoch=0)
    await db.execute(insert(StockQuote).values(**quote_values).on_conflict_do_update(index_elements=['coin_id'],set_={k:v for k,v in quote_values.items() if k!='coin_id'}))
   async with sessions['scheduler'].begin() as db:
    now=(await db.execute(select(func.clock_timestamp()))).scalar_one()
    await persist_status_batch(db,StatusBatch((StatusEvent(cid,'synthetic-actual-MCD','normal',now,now.date(),1,'synthetic-independent-runtime-status'),),now,2000,1,baseline_verified=True,contiguous=True,complete=True,end_marker=True),coin_id=cid)
    btc=(await db.execute(select(Coin.id).where(Coin.symbol=='BTC',Coin.asset_class=='crypto'))).scalar_one()
    await upsert_prices(db,[AcceptedPrice(btc,D(10000),now)],'fake')
   for email in (EMAIL,'actual-stock-second@example.invalid'):
    async with sessions['app']() as db:
     uid,created=await get_or_create_user(db,email);assert created
     await db.commit()
    async with sessions['app']() as db:
     draft=QuoteIn(symbol='MCD',side='buy',quantity='2' if email==EMAIL else '1')
     q=await stock_trading.quote(db,user_id=uid,order=draft,settings=settings)
     assert q.exec_price==102 and q.fee==0
     order=TradeIn(**draft.model_dump(mode="json"),expected_exec_price='102',idempotency_key=KEY)
     filled,created=await stock_trading.execute(db,user_id=uid,order=order,settings=settings)
     assert created
     again,created=await stock_trading.execute(db,user_id=uid,order=order,settings=settings)
     assert not created and again==filled
     c=await stock_trading.context(db,user_id=uid,symbol='MCD',settings=settings)
     assert c.held_quantity==draft.quantity and c.execution_enabled
     await db.rollback()
    if email==EMAIL:
     original=filled
     async with sessions['app'].begin() as db:
      before=CutoffEvidence(filled.executed_at,exchange,filled.executed_at.date(),2000,'synthetic-runtime-calendar')
      after=CutoffEvidence(filled.executed_at+timedelta(microseconds=1),exchange,filled.executed_at.date(),2000,'synthetic-runtime-calendar')
      assert (await reconstruct_stock_quantity(db,uid,cid,before,0)).quantity==0
      assert (await reconstruct_stock_quantity(db,uid,cid,after,0)).quantity==2
   async with sessions['app']() as db:
    uid=(await db.execute(select(User.id).where(User.email==EMAIL))).scalar_one()
    sold,created=await stock_trading.execute(db,user_id=uid,order=TradeIn(symbol='MCD',side='sell',quantity='1',expected_exec_price='100',idempotency_key=uuid.uuid4()),settings=settings)
    assert created and sold.cash_after==9896
    crypto,created=await crypto_execute(db,user_id=uid,order=Order('BTC','buy','usd',D(100)),expected_mid=D(10000),idempotency_key=uuid.uuid4(),settings=settings)
    assert created and crypto.cash_after==9796
    mixed=await portfolio.get_portfolio(db,user_id=uid,settings=settings)
    assert mixed.valuation_complete and mixed.total_value==D('9996.50')
    assert [h.symbol for h in mixed.holdings]==['BTC','MCD'] and mixed.starting_cash==10000
    await db.rollback()
    try:await crypto_execute(db,user_id=uid,order=Order('BTC','buy','usd',D(100)),expected_mid=D(10000),idempotency_key=KEY,settings=settings)
    except TradeRefused as exc:assert exc.code=='idempotency_conflict'
    else:raise AssertionError('cross-asset key accepted')
   # Actual supported forward split follows actual fills under scheduler grants.
   async with sessions['scheduler'].begin() as db:
    now=(await db.execute(select(func.clock_timestamp()))).scalar_one();cutoff=now+timedelta(milliseconds=200)
    event=NormalizedAction('synthetic-runtime-forward-split',cid,'MCD','forward_split',now.date(),now,new_rate=D(4),old_rate=D(1),units='pre_split',economic_at=cutoff,ex_date=cutoff.date(),record_date=cutoff.date(),payable_date=cutoff.date()+timedelta(days=1),due_bills=False,identity_verified=True,dates_verified=True)
    authority=await corporate_actions._load_admission(db,'actions')
    await corporate_actions.persist_action_batch(db,ActionBatch(records=(event,),observations=(ActionObservation(event),),complete=True),authority)
   async with sessions['scheduler'].begin() as db:
    await db.execute(text("SELECT pg_sleep(GREATEST(0,EXTRACT(EPOCH FROM CAST(:cutoff AS timestamptz)-clock_timestamp()))+0.02)"),{'cutoff':cutoff})
    applied=await corporate_actions.apply_due_actions(db,cid);assert len(applied)==1
   async with sessions['scheduler'].begin() as db:
    assert await corporate_actions.apply_due_actions(db,cid)==applied
    state,rows=await assert_ownership_consistent(db,cid)
    assert state.unit_epoch==1 and len([r for r in rows if r.cause_kind=='split'])==2
   async with sessions['app']() as db:
    held=(await db.execute(select(Holding.quantity,Holding.cost_basis).where(Holding.user_id==uid,Holding.coin_id==cid))).one()
    assert tuple(held)==(D(4),D(102))
    replay,created=await stock_trading.execute(db,user_id=uid,order=TradeIn(symbol='MCD',side='buy',quantity='2',expected_exec_price='999',idempotency_key=KEY),settings=settings)
    assert not created and replay==original and replay.held_after==2
    mixed=await portfolio.get_portfolio(db,user_id=uid,settings=settings)
    assert not mixed.valuation_complete and mixed.total_value is None
    assert mixed.cash==9796 and mixed.unvalued_holding_count==1
    await db.rollback()
   digest=fingerprint(original)
  else:
   # Quarantined clone: actual app cannot read financial tables; do not repair ACLs.
   async with sessions['app']() as db:
    try:await db.execute(select(Trade.id))
    except Exception as exc:
     assert getattr(getattr(exc,'orig',None),'sqlstate',None)=='42501'
     await db.rollback()
    else:raise AssertionError('quarantined financial ACL was broadened')
   async with sessions['owner']() as db:
    uid=(await db.execute(select(User.id).where(User.email==EMAIL))).scalar_one()
    before=(await db.execute(select(Account.cash).where(Account.user_id==uid))).scalar_one()
    count=(await db.execute(select(func.count()).select_from(Trade))).scalar_one()
    order=TradeIn(symbol='MCD',side='buy',quantity='2',expected_exec_price='999',idempotency_key=KEY)
    first,created=await stock_trading.execute(db,user_id=uid,order=order,settings=settings);assert not created
    second,created=await stock_trading.execute(db,user_id=uid,order=order,settings=settings);assert not created and first==second
    digest=fingerprint(first);assert digest==RUNTIME_EXPECTED
    assert (await db.execute(select(Account.cash).where(Account.user_id==uid))).scalar_one()==before==9796
    assert (await db.execute(select(func.count()).select_from(Trade))).scalar_one()==count
    result=await portfolio.get_portfolio(db,user_id=uid,settings=settings)
    assert result.cash==9796 and not result.valuation_complete and result.unvalued_holding_count==1
    revision=(await db.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
    assert revision in ('0013','0014')
    if revision=='0014':
     page=await list_event_history(db,user_id=uid,limit=100)
     assert {'trade','split'}<={item.kind for item in page.items}
     assert len({item.id for item in page.items})==len(page.items)
     print('runtime_current_mixed_history=true revision0014=true',flush=True)
    await stock_trading.context(db,user_id=uid,symbol='MCD',settings=settings)
    await db.rollback()
   # Actual scheduler service must also respect the clone's stock quarantine.
   async with sessions['scheduler']() as db:
    old=await db.get(StockStatusEvidence,cid);now=(await db.execute(select(func.clock_timestamp()))).scalar_one()
    status=StatusBatch((StatusEvent(cid,'synthetic-actual-MCD','normal',now,now.date(),old.sequence+1,'synthetic-restored-status'),),now,2000,old.continuity_generation+1,baseline_verified=True,contiguous=True,complete=True,end_marker=True)
    try:await persist_status_batch(db,status,coin_id=cid)
    except Exception as exc:
     assert getattr(getattr(exc,'orig',None),'sqlstate',None)=='42501'
     await db.rollback()
    else:raise AssertionError('quarantined stock ACL was broadened')
  print('runtime_original_receipt_sha256='+digest,flush=True)
  print('runtime_stock_quote_execute_replay_context_portfolio=true actual_split_cutoff=true crypto_shared_cash=true restored_owner_reads_only='+str(bool(RUNTIME_DATABASE)).lower()+' verified_tls='+str(bool(args.get('ssl'))).lower(),flush=True)
 finally:
  for e in engines.values():await e.dispose()
asyncio.run(main())
"""


def program(
    *, seed: bool, database: str | None = None, expected: str | None = None
) -> str:
    if type(seed) is not bool or (seed and database is not None):
        raise ValueError("New financial intent is source-only")
    if database not in (None, "birja_restore_test"):
        raise ValueError("Unexpected synthetic database")
    if not seed and (
        expected is None
        or len(expected) != 64
        or any(c not in "0123456789abcdef" for c in expected)
    ):
        raise ValueError("Expected original receipt digest required")
    return (
        f"RUNTIME_SEED={seed!r}\nRUNTIME_DATABASE={database!r}\nRUNTIME_EXPECTED={expected!r}\n"
        + PROGRAM
    )
