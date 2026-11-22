#!/usr/bin/env python3
"""Independent retained0017 oracle and immutable synthetic snapshot commands.

No application test fixture is imported. The transport is supplied by the owned
TLS harness; command tests may inject a transport but cannot claim a DB proof.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

MODES = {"create", "projection", "verify", "compare"}
DATABASES = {None, "birja_restore_test"}
TABLES = (
    "accounts", "holdings", "trades", "stock_fill_facts",
    "stock_ownership_movements", "stock_split_applications",
    "stock_dividend_entitlements", "stock_dividend_payments",
    "stock_dividend_decisions", "portfolio_stock_closures", "stock_action_state",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def fingerprint(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require_projection(value):
    """Independent money/units oracle, in addition to whole-evidence equality."""
    if not isinstance(value, dict) or set(value) != {"revision", "books", "tables", "sequences", "journal"}:
        raise ValueError("projection shape")
    if value["revision"] != "0017":
        raise ValueError("current0017 only")
    expected = [
        ["Original", "25.00000000", "9999.00000000", False, "8.00000000", "20.00000000"],
        ["Sibling", "334.00000000", "1234.00000000", False, "4.00000000", "30.00000000"],
        ["Frozen", "123.00000000", "7777.00000000", True, "4.00000000", "20.00000000"],
    ]
    if value["books"] != expected:
        raise ValueError("independent cash/baseline/quantity/basis oracle")
    if set(value["tables"]) != set(TABLES) or not value["sequences"]:
        raise ValueError("incomplete evidence")
    applications = value["tables"]["stock_split_applications"]
    if len(applications) != 2 or [r["owner_digest_version"] for r in applications] != [None, 2]:
        raise ValueError("mixed global digest markers")
    for row in applications:
        if "portfolio_id" in row or "user_id" in row:
            raise ValueError("global application acquired owner")
        if not all(re.fullmatch("[0-9a-f]{64}", row[n]) for n in ("before_digest", "after_digest")):
            raise ValueError("digest bytes")
    if (len(value["tables"]["portfolio_stock_closures"]) != 1 or value["journal"] != [2, 3]
            or not all(value["tables"][name] for name in ("stock_dividend_entitlements",
                "stock_dividend_payments", "stock_dividend_decisions", "trades"))):
        raise ValueError("terminal journal oracle")
    return value


def private_snapshot(path, *, existing):
    path = Path(path)
    if (not path.is_absolute() or path.is_symlink() or path.resolve() != path
            or not str(path).startswith("/tmp/birja-") or path.exists() != existing):
        raise ValueError("private synthetic snapshot path")
    if existing and (not path.is_file() or path.stat().st_mode & 0o077):
        raise ValueError("private immutable snapshot")
    return path


def save_snapshot(path, value):
    require_projection(value)
    path = private_snapshot(path, existing=False)
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(canonical(value))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_snapshot(path, digest, value):
    path = private_snapshot(path, existing=True)
    if not isinstance(digest, str) or not re.fullmatch("[0-9a-f]{64}", digest):
        raise ValueError("immutable expected hash required")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError("expected snapshot hash mismatch")
    expected = require_projection(json.loads(data))
    require_projection(value)
    if canonical(expected) != canonical(value):
        raise ValueError("exact restored interpretation/evidence mismatch")
    return digest


COMMON = r'''
import asyncio,hashlib,json,os,uuid
from dataclasses import asdict
from datetime import UTC,datetime,timedelta
from decimal import Decimal as D
from sqlalchemy import text,select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.core.config import Settings
from app.db.connection import database_connect_args
from app.services.stock_ownership import assert_ownership_consistent

def digest(rows):
 return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def setup():
 settings=Settings();url=make_url(settings.database_url)
 if url.host!='postgres' or url.port!=5432 or url.database!='birja_source_test' or url.username!='birja_migrator' or url.query:
  raise ValueError('owned synthetic source identity required')
 if not settings.database_ssl_ca_file:raise ValueError('verified TLS required')
 if DATABASE:url=url.set(database=DATABASE)
 args=database_connect_args(settings,migration=True)
 if not args.get('ssl'):raise ValueError('TLS connection required')
 engine=create_async_engine(url,connect_args=args)
 return settings,engine,async_sessionmaker(engine,expire_on_commit=False),args

async def project(db):
 if (await db.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()!='0017':
  raise ValueError('current0017 only')
 cid=(await db.execute(text('SELECT min(coin_id) FROM stock_split_applications'))).scalar_one()
 state,rows=await assert_ownership_consistent(db,cid)
 books=(await db.execute(text("""SELECT a.name,a.cash::text,a.starting_cash::text,
 a.closed_at IS NOT NULL,h.quantity::text,h.cost_basis::text FROM accounts a JOIN holdings h
 ON (h.portfolio_id,h.user_id)=(a.id,a.user_id) WHERE h.coin_id=:c
 ORDER BY CASE a.name WHEN 'Original' THEN 0 WHEN 'Sibling' THEN 1 ELSE 2 END"""),{'c':cid})).all()
 tables={}
 for table in TABLES:
  key='trade_id' if table=='stock_fill_facts' else 'coin_id' if table=='stock_action_state' else 'id'
  tables[table]=json.loads((await db.execute(text('SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY '+key+'),\'[]\'::jsonb)::text FROM public.'+table+' t'))).scalar_one())
 sequences={}
 names=(await db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"))).scalars()
 for name in names:
  seq=(await db.execute(text("SELECT pg_get_serial_sequence(:t,'id') WHERE EXISTS(SELECT FROM information_schema.columns WHERE table_schema='public' AND table_name=:t AND column_name='id')"),{'t':name})).scalar_one_or_none()
  if seq:sequences[name]=list((await db.execute(text('SELECT last_value,is_called FROM '+seq))).one())
 return {'revision':'0017','books':[list(r) for r in books],'tables':tables,'sequences':sequences,'journal':[state.unit_epoch,len({r.portfolio_id for r in rows})]}

async def event(db,cid,key,at,terms=None):
 e=(await db.execute(text("INSERT INTO stock_action_events(coin_id,economic_key,first_observed_at) VALUES (:c,:k,:n) RETURNING id"),{'c':cid,'k':str(uuid.uuid5(uuid.NAMESPACE_URL,key)),'n':at})).scalar_one()
 s=(await db.execute(text("INSERT INTO stock_action_sources(event_id,provider,product,provider_event_id) VALUES (:e,'alpaca','actions',:k) RETURNING id"),{'e':e,'k':key})).scalar_one()
 r=(await db.execute(text("INSERT INTO stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason,verified_cutoff) VALUES (:e,:s,1,:f,'snapshot',:n,1,CAST(:terms AS jsonb),'supported_forward_split','none',:cutoff) RETURNING id"),{'e':e,'s':s,'f':digest([key]),'n':at,'terms':json.dumps(terms or {}),'cutoff':at-timedelta(days=1)})).scalar_one()
 await db.execute(text('UPDATE stock_action_events SET current_revision_id=:r WHERE id=:e'),{'e':e,'r':r})
 return e,r

async def legacy(factory):
 async with factory.begin() as db:
  assert (await db.execute(text('SELECT session_user'))).scalar_one()=='birja_migrator'
  assert (await db.execute(text('SELECT count(*) FROM users'))).scalar_one()==0
  cid=(await db.execute(text('SELECT min(coin_id) FROM stock_instruments'))).scalar_one()
  now=(await db.execute(text('SELECT clock_timestamp()'))).scalar_one();users=[]
  for name,baseline in [('Original',9999),('Frozen',7777)]:
   u=(await db.execute(text('INSERT INTO users(email) VALUES (:e) RETURNING id'),{'e':name.lower()+'@portfolio-fixture.invalid'})).scalar_one();users.append(u)
   await db.execute(text('INSERT INTO accounts(user_id,cash,starting_cash) VALUES (:u,123,:b)'),{'u':u,'b':baseline})
   await db.execute(text('INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) VALUES (:u,:c,4,20)'),{'u':u,'c':cid})
  await db.execute(text("INSERT INTO stock_action_state(coin_id,health,admission_generation,journal_start_at,complete_from,unit_epoch,sequence) VALUES (:c,'current',1,:start,:start,1,4)"),{'c':cid,'start':now-timedelta(days=15)})
  e,r=await event(db,cid,'legacy-two-owner-global',now-timedelta(days=10))
  before=digest([(u,'2.00000000','20.00000000') for u in users]);after=digest([(u,'4','20.00000000') for u in users])
  a=(await db.execute(text("INSERT INTO stock_split_applications(economic_event_id,coin_id,revision_id,new_rate,old_rate,cutoff,processed_at,prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest) VALUES (:e,:c,:r,'2','1',:cut,:n,0,1,2,:b,:a) RETURNING id"),{'e':e,'c':cid,'r':r,'cut':now-timedelta(days=11),'n':now-timedelta(days=10),'b':before,'a':after})).scalar_one()
  for i,u in enumerate(users,1):
   for split in (False,True):
    await db.execute(text("INSERT INTO stock_ownership_movements(user_id,coin_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,application_id,causal_key) VALUES (:u,:c,:s,:at,:at,2,:b,:a,:bb,20,:epoch,:kind,:app,:key)"),{'u':u,'c':cid,'s':i+2 if split else i,'at':now-timedelta(days=11 if split else 12),'b':2 if split else 0,'a':4 if split else 2,'bb':20 if split else 0,'epoch':1 if split else 0,'kind':'split' if split else 'opening','app':a if split else None,'key':f'legacy:{u}:{split}'})

def admission(now):
 from app.services.stock_admission import ProductAdmission
 from app.services.stock_quote_rules import CURATED_SYMBOLS
 return ProductAdmission(product='actions',state='approved',generation=1,reviewed_at=now-timedelta(hours=1),valid_from=now-timedelta(hours=2),valid_until=now+timedelta(hours=2),evidence_ref='synthetic-private-fixture',terms_version='synthetic-v1',collection_allowed=True,display_allowed=True,derived_allowed=True,retention_allowed=True,scope={'application':'birja','audience':'authenticated-users','account':'birja','server':'birja','feed':'alpaca-corporate-actions','capabilities':['rest','replay'],'rest_symbols':sorted(CURATED_SYMBOLS),'replay_region':'us','all_us_replay_ingress':True,'durable_accounting':True,'backup_restore':True,'retention_mode':'durable-accounting'},quota={'requests_per_minute':20,'symbols_per_request':20,'max_response_bytes':262144,'retention_seconds':315360000},allowed_fields=['provider_event_id','symbol','event_type','process_date'],attribution='IEX prices')

async def current(factory,settings,args):
 from app.models.user import Account
 from app.models.stock import StockDataAdmission
 from app.services.corporate_action_rules import NormalizedAction
 from app.services.alpaca_actions import ActionBatch,ActionObservation
 from app.services.corporate_actions import persist_action_batch,apply_due_actions
 from app.services.trading import execute,Order
 from app.services.portfolios import OwnedActivePortfolio
 async with factory.begin() as db:
  roots=list((await db.execute(select(Account).order_by(Account.id))).scalars());first,closed=roots
  first.name='Original';closed.name='Frozen'
  now=(await db.execute(text('SELECT clock_timestamp()'))).scalar_one()
  cid=(await db.execute(text('SELECT min(coin_id) FROM stock_split_applications'))).scalar_one()
  sibling=Account(user_id=first.user_id,name='Sibling',cash=D(333),starting_cash=D(1234));db.add(sibling);await db.flush()
  await db.execute(text('INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis) VALUES (:p,:u,:c,2,30)'),{'p':sibling.id,'u':first.user_id,'c':cid})
  await db.execute(text("INSERT INTO stock_ownership_movements(portfolio_id,user_id,coin_id,sequence,economic_at,recorded_at,quantity,before_quantity,after_quantity,before_basis,after_basis,unit_epoch,cause_kind,causal_key) VALUES (:p,:u,:c,5,:at,:at,2,0,2,0,30,1,'opening','sibling-opening')"),{'p':sibling.id,'u':first.user_id,'c':cid,'at':now-timedelta(days=5)})
  closed.closed_at=now;await db.flush()
  await db.execute(text('INSERT INTO portfolio_stock_closures(portfolio_id,user_id,coin_id,closed_at,closing_sequence,unit_epoch) VALUES (:p,:u,:c,:n,5,1)'),{'p':closed.id,'u':closed.user_id,'c':cid,'n':now})
  evidence=admission(now);db.add(StockDataAdmission(**asdict(evidence)))
  await db.execute(text("UPDATE stock_instruments SET provider_asset_id='portfolio-synthetic-asset',provider_verified_at=:n WHERE coin_id=:c"),{'n':now,'c':cid})
  await db.execute(text("UPDATE stock_action_state SET health='current',admission_generation=1,valid_until=:until,covered_until=:n WHERE coin_id=:c"),{'until':now+timedelta(hours=1),'n':now,'c':cid})
  symbol=(await db.execute(text('SELECT symbol FROM coins WHERE id=:c'),{'c':cid})).scalar_one()
  at=now-timedelta(days=4)
  action=NormalizedAction('later-global-two-siblings',cid,symbol,'forward_split',at.date(),now,economic_at=at,currency=None,new_rate=D(2),old_rate=D(1),ex_date=at.date(),record_date=at.date(),payable_date=at.date(),subtype='ordinary',foreign=False,special=False,due_bills=False,identity_verified=True,dates_verified=True,units='pre_split')
  await persist_action_batch(db,ActionBatch(records=(action,),observations=(ActionObservation(action),),complete=True),evidence)
  first_id,uid=first.id,first.user_id
 # Actual separately authenticated scheduler, not SET ROLE/admin imitation.
 url=make_url(settings.database_url)
 scheduler=create_async_engine(url.set(username='birja_scheduler',password=os.environ['FIXTURE_SCHEDULER_PASSWORD']),connect_args=args)
 app=create_async_engine(url.set(username='birja_app',password=os.environ['FIXTURE_APP_PASSWORD']),connect_args=args)
 try:
  async with async_sessionmaker(scheduler,expire_on_commit=False).begin() as db:
   assert (await db.execute(text('SELECT session_user'))).scalar_one()=='birja_scheduler'
   await apply_due_actions(db,cid)
  async with factory.begin() as db:
   btc=(await db.execute(text("SELECT id FROM coins WHERE symbol='BTC'"))).scalar_one()
   await db.execute(text("INSERT INTO prices(coin_id,mid,as_of,source) VALUES (:c,10000,clock_timestamp(),'fake') ON CONFLICT(coin_id) DO UPDATE SET mid=10000,as_of=clock_timestamp(),source='fake'"),{'c':btc})
  async with async_sessionmaker(app,expire_on_commit=False)() as db:
   assert (await db.execute(text('SELECT session_user'))).scalar_one()=='birja_app'
   result,new=await execute(db,portfolio=OwnedActivePortfolio(first_id,uid),order=Order('BTC','buy','usd',D(100)),expected_mid=D(10000),idempotency_key=uuid.UUID('12181818-1818-4818-8818-181818181818'),settings=settings)
   assert new and result.cash_after==D(23)
   await db.commit()
   replay,new=await execute(db,portfolio=OwnedActivePortfolio(first_id,uid),order=Order('BTC','buy','usd',D(100)),expected_mid=D(10000),idempotency_key=uuid.UUID('12181818-1818-4818-8818-181818181818'),settings=settings)
   assert not new and replay==result
  # Independent synthetic historical source/entitlements; payout and hold use
  # the actual separately authenticated scheduler and unchanged SQL authority.
  from dataclasses import replace
  from app.services.stock_sessions import build_sessions
  from app.services.dividends import process_dividend,record_dividend_hold
  async with factory.begin() as db:
   base=admission(now)
   calendar=replace(base,product='calendar',scope={**base.scope,'feed':'iex'},quota={**base.quota,'retention_seconds':86400},allowed_fields=['exchange','session_date','opens_at','closes_at'],calendar={'exchanges':['XNYS','XNAS'],'version':'exchange-calendars-4.13.2/synthetic-fixture','sources':['https://www.nyse.com/trade/hours-calendars','https://www.nasdaq.com/market-activity/stock-market-holiday-schedule'],'review_valid_until':(now+timedelta(hours=2)).isoformat(),'coverage_start':(now.date()-timedelta(days=45)).isoformat(),'coverage_end':(now.date()+timedelta(days=90)).isoformat(),'overrides':[]})
   reference=replace(base,product='reference',scope={**base.scope,'feed':'iex'},quota={**base.quota,'retention_seconds':86400},allowed_fields=['symbol','name','exchange','provider_asset_id'])
   db.add_all([StockDataAdmission(**asdict(item)) for item in (calendar,reference)])
   exchange=(await db.execute(text('SELECT listing_exchange FROM stock_instruments WHERE coin_id=:c'),{'c':cid})).scalar_one()
   session=max((s for s in build_sessions(now,calendar) if s.exchange==exchange and s.opens_at and s.opens_at<now),key=lambda s:s.opens_at)
   cutoff=session.opens_at
   await db.execute(text('INSERT INTO stock_sessions(exchange,session_date,opens_at,closes_at,coverage_start,coverage_end,calendar_admission_generation) VALUES (:e,:d,:o,:cl,:d,:d,1)'),{'e':exchange,'d':session.session_date,'o':cutoff,'cl':session.closes_at})
   await db.execute(text('UPDATE stock_action_state SET checked_at=:n,coverage_start=:start,covered_until=:n WHERE coin_id=:c'),{'start':now-timedelta(days=15),'n':now,'c':cid})
   event_id,revision_id=await event(db,cid,'ordinary-dividend-two-strategies',now)
   terms={'event_type':'cash_dividend','currency':'USD','subtype':'ordinary','foreign':False,'special':False,'due_bills':False,'identity_verified':True,'dates_verified':True,'cancelled':False,'identity_changed':False,'rate':'0.25','ex_date':str(cutoff.date()),'record_date':str(cutoff.date()),'payable_date':str(cutoff.date())}
   fp=digest(['ordinary-dividend-two-strategies'])
   await db.execute(text("UPDATE stock_action_revisions SET classification='supported_dividend',normalized_terms=CAST(:t AS jsonb),verified_cutoff=:cut WHERE id=:r"),{'t':json.dumps(terms),'cut':cutoff,'r':revision_id})
   targets=[]
   for root,quantity in ((first_id,8),(sibling.id,4)):
    entfp=digest(['entitlement',root])
    ent=(await db.execute(text("INSERT INTO stock_dividend_entitlements(event_id,portfolio_id,user_id,revision_id,cutoff,cutoff_rule,version,units_basis,unit_epoch,last_movement_sequence,eligible_quantity,state,fingerprint) VALUES (:e,:p,:u,:r,:cut,'exclusive-regular-session-open',1,'unit_epoch:2',2,7,:q,'eligible',:fp) RETURNING id"),{'e':event_id,'p':root,'u':uid,'r':revision_id,'cut':cutoff,'q':quantity,'fp':entfp})).scalar_one()
    targets.append({'portfolio_id':root,'event_id':event_id,'entitlement_id':ent,'expected_revision_fingerprint':fp,'expected_entitlement_fingerprint':entfp})
  payments=[]
  for target in targets:
   async with async_sessionmaker(scheduler,expire_on_commit=False)() as db:
    try:
     payments.append(await process_dividend(db,**target))
    except Exception as exc:
     # Synthetic-only diagnostic: domain codes contain no retained owner data,
     # DSN or credentials. Never weaken financial authority to make smoke pass.
     code=getattr(exc,'code',type(exc).__name__)
     if code=='authority_unavailable':
      from sqlalchemy.exc import DBAPIError
      try:
       await db.execute(text('SELECT * FROM public.apply_stock_dividend(:event_id,:entitlement_id,:revision,:entitlement)'),{'event_id':target['event_id'],'entitlement_id':target['entitlement_id'],'revision':target['expected_revision_fingerprint'],'entitlement':target['expected_entitlement_fingerprint']})
      except DBAPIError as error:
       # Only known fixed database messages are exposed, never statement params.
       message=str(error.orig).splitlines()[0]
       fixed=message.split(': ',1)[-1]
       if fixed.startswith('dividend '):code+=' / '+fixed
       await db.rollback()
     raise AssertionError('synthetic dividend refusal: '+code) from None
  async with factory.begin() as db:
   source_id=(await db.execute(text('SELECT source_id FROM stock_action_revisions WHERE id=:r'),{'r':revision_id})).scalar_one()
   heldfp=digest(['uncertain-correction'])
   heldrev=(await db.execute(text("INSERT INTO stock_action_revisions(event_id,source_id,ordinal,fingerprint,mutation_kind,observed_at,admission_generation,normalized_terms,classification,reason) VALUES (:e,:s,2,:fp,'update',clock_timestamp(),1,'{}','uncertain','source_gap') RETURNING id"),{'e':event_id,'s':source_id,'fp':heldfp})).scalar_one()
   await db.execute(text('UPDATE stock_action_events SET current_revision_id=:r WHERE id=:e'),{'r':heldrev,'e':event_id})
  async with async_sessionmaker(scheduler,expire_on_commit=False)() as db:
   outcome=await record_dividend_hold(db,portfolio_id=first_id,payment_id=payments[0].payment_id,expected_revision_fingerprint=heldfp)
   assert outcome.outcome=='held_uncertain'
 finally:await scheduler.dispose();await app.dispose()
'''


def program(*, mode, database=None, expected=None):
    if mode not in MODES or database not in DATABASES or (mode == "create" and database):
        raise ValueError("unsafe mode/database")
    if mode == "compare" and (not isinstance(expected, str) or not re.fullmatch("[0-9a-f]{64}", expected)):
        raise ValueError("immutable expected hash required")
    prelude = "MODE=" + repr(mode) + "\nDATABASE=" + repr(database) + "\nTABLES=" + repr(TABLES) + "\n"
    runner = r'''
async def run():
 settings,engine,factory,args=setup()
 try:
  if MODE=='create':
   from alembic import command
   from alembic.config import Config
   await asyncio.to_thread(command.upgrade,Config('/app/alembic.ini'),'0014')
   await legacy(factory)
   await asyncio.to_thread(command.upgrade,Config('/app/alembic.ini'),'0017')
   async with factory.begin() as db:
    from app.db.portfolio_bootstrap import GRANTS_SQL
    raw=await (await db.connection()).get_raw_connection()
    await raw.driver_connection.execute(GRANTS_SQL)
   await current(factory,settings,args)
  async with factory() as db:
   result=await project(db)
   print('portfolio_projection='+json.dumps(result,sort_keys=True,separators=(',',':')),flush=True)
   print('portfolio_verified_tls=true',flush=True)
 finally:await engine.dispose()
asyncio.run(run())
'''
    # This fixture is retained, not a way to run future application imports
    # against0017. The source dispatcher extracts the complete tested release.
    source_guard = r'''
import hashlib
from pathlib import Path
if hashlib.sha256(Path('/app/app/db/portfolio_bootstrap.py').read_bytes()).hexdigest()!='ee352f8659fd3bac96b90e583b1c30c41e4cd5819ce59928568c9d75ee02654e':
 raise ValueError('retained0017 source mismatch before application import')
'''
    return prelude + source_guard + COMMON + runner


def command_transport(source):
    """Explicit command vector only; inherited credentials are never displayed."""
    command = os.environ.get("BIRJA_PORTFOLIO_FIXTURE_TRANSPORT")
    if not command:
        raise ValueError("owned isolated transport required; no default database")
    argv = json.loads(command)
    if not isinstance(argv, list) or not argv or not all(isinstance(v, str) and v for v in argv):
        raise ValueError("explicit argv required")
    result = subprocess.run(argv, input=source.encode(), capture_output=True, timeout=240, check=False)
    if result.returncode:
        raise ValueError("isolated fixture program failed")
    rows = [line.split(b"=", 1)[1] for line in result.stdout.splitlines() if line.startswith(b"portfolio_projection=")]
    if len(rows) != 1 or b"portfolio_verified_tls=true" not in result.stdout.splitlines():
        raise ValueError("missing exact TLS projection")
    return json.loads(rows[0])


def main(argv=None, *, transport=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=sorted(MODES))
    parser.add_argument("--database", choices=["birja_restore_test"])
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)
    if args.mode == "compare":
        private_snapshot(args.snapshot, existing=True)
    if args.mode == "projection":
        private_snapshot(args.snapshot, existing=False)
    value = (transport or command_transport)(program(mode=args.mode, database=args.database,
                                                    expected=args.expected_sha256))
    require_projection(value)
    if args.mode == "projection":
        digest = save_snapshot(args.snapshot, value)
    elif args.mode == "compare":
        digest = compare_snapshot(args.snapshot, args.expected_sha256, value)
    else:
        digest = fingerprint(value)
    print("portfolio_fixture_sha256=" + digest)
    return digest


if __name__ == "__main__":
    main()
