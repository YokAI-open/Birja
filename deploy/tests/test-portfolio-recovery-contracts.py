#!/usr/bin/env python3
"""Offline exact0017 producer/consumer contracts; no provider operations."""

import ast
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
RETAINED_0023 = "07d3aa5c627b5ba550aa2d11baa13e2becaf3aa9"
RETAINED_0024 = "33b9b5fdc6f89ef810d588bd7c7b2962b2c80352"
RETAINED_0025 = "31cba00ca3f0c9d4214b6bb0b66892a4c81779fb"


def load(name, root=ROOT):
    spec = importlib.util.spec_from_file_location(name, root / "deploy" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_git(*arguments):
    return subprocess.check_output(
        ['git', '-c', 'safe.directory=' + str(ROOT), *arguments], cwd=ROOT,
    )


def retained_catalog(root, *, runtime=False):
    if runtime:
        source = source_git('archive', '--format=tar', RETAINED_0025, 'backend')
        with tarfile.open(fileobj=io.BytesIO(source), mode='r:') as archive:
            archive.extractall(root, filter='data')
    current = load('backup-snapshot')
    for name in {
        *current.PORTFOLIO_PAYLOAD_V5,
        'deploy/backup-manifest.sql',
        'deploy/backup-snapshot.py',
        'deploy/verify-restore.py',
        'deploy/tests/stock-execution-fixture.py',
    }:
        contents = source_git('show', RETAINED_0025 + ':' + name)
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
    current.require_closure_source(root, revision='0025', allow_successor=False)


def predecessor_catalog(root):
    """Use the immutable production predecessor tree for the synthetic book."""
    source = source_git('archive', '--format=tar', RETAINED_0023)
    with tarfile.open(fileobj=io.BytesIO(source), mode='r:') as archive:
        archive.extractall(root, filter='data')
    load('backup-snapshot', root).require_closure_source(root)


def catalog_snapshot(root, revision, stage, restic_path):
    import shutil

    producer = load('backup-snapshot', root)
    if revision == '0023':
        producer.require_closure_source(root)
    else:
        producer.require_closure_source(root, revision=revision, allow_successor=False)
    docker = shutil.which('docker')
    assert docker
    job = producer.Job({
        '_synthetic': True, 'state_dir': str(stage),
        'password_file': str(stage / 'restic-password'), 'repository': str(stage / 'repository'),
        'source_project': 'birja-phase20-local-fixture', 'docker_binary': docker,
        'restic_binary': restic_path, 'db_user': 'birja_test', 'db_name': 'birja_test',
        'release': 'fixture-phase20', 'timeout_seconds': 60, 'max_stage_bytes': 32 * 1024 * 1024,
    })
    job.dc = [docker, 'exec', '-i', catalog_container()]
    job.bundle = stage / revision
    job.start_utc = producer.utc()
    job.data_epoch = int(time.time())
    job.snapshot()
    source = json.loads((job.bundle / 'manifest.json').read_text())
    assert source['revision'] == revision
    if not (stage / 'host').exists():
        assert source['tables']['stock_fill_facts']['count'] == (3 if revision == '0025' else 5)
    if revision in ('0026', '0027'):
        assert source['catalog_finance_invalid'] == 0
        assert source['tables']['stock_catalog_fill_evidence']['count'] == 2


def catalog_container():
    container = os.environ['BIRJA_CATALOG_TEST_CONTAINER']
    if not re.fullmatch(r'[a-f0-9]{64}', container):
        raise ValueError('Owned catalog fixture container required')
    label = subprocess.check_output(
        ['docker', 'inspect', '--type', 'container', '--format',
         '{{index .Config.Labels "org.birja.fixture"}}', container],
    )
    if label.strip() != b'catalog-finance':
        raise ValueError('Owned catalog fixture container required')
    return container


def catalog_sql(container, query, db):
    return subprocess.run(
        ['docker', 'exec', '-i', container, 'psql', '-XqAt', '-v', 'ON_ERROR_STOP=1',
         '-U', 'birja_test', '-d', db], input=query.encode(), capture_output=True, check=True,
    ).stdout


def catalog_restore(root, manifest, database='birja_restore_test'):
    restore = load('verify-restore', root)
    container = catalog_container()
    if database not in {'birja_test', restore.CLONE}:
        raise ValueError('Unexpected disposable database')

    def isolated_sql(dc, query, db=restore.CLONE):
        assert db == restore.CLONE
        return catalog_sql(container, query, database)

    with mock.patch.object(restore, 'sql', isolated_sql):
        source = json.loads(manifest.read_text())
        restore.restore_closure_authority([], source)
        restore.verify([], source, quarantined=False)


def catalog_observe(root, database, output):
    if database not in {'birja_test', 'birja_restore_test'}:
        raise ValueError('Unexpected disposable database')
    restore = load('verify-restore', root)
    container = catalog_container()
    with mock.patch.object(
        restore, 'sql', lambda _, query, db=restore.CLONE: catalog_sql(container, query, db),
    ):
        manifest = restore.canonical([], database)
    restore.recovery_contract().validate_manifest(manifest)
    with output.open('x') as stream:
        json.dump(manifest, stream, sort_keys=True)


def compare_predecessor(before, after):
    """Migrations through 0027 add catalog tables and leaves the prior book intact."""
    prior = json.loads(before.read_text())
    successor = json.loads(after.read_text())
    assert prior['revision'] == '0023' and successor['revision'] == '0027'
    for key in ('financial', 'portfolio_state', 'management_state', 'closure_state'):
        assert prior[key] == successor[key], key
    for table, entry in prior['tables'].items():
        if table != 'alembic_version':
            assert successor['tables'][table] == entry, table
    assert all(row in successor['identity_state'] for row in prior['identity_state'])


def catalog_authority(path):
    contract = json.loads(path.read_text())['closure_contract']
    print('catalog_authority=' + json.dumps([contract[key] for key in ('catalogue', 'acl', 'defaults')]))


def catalog_runtime_program(kind, path):
    import inspect

    if kind in {'predecessor-seed', 'predecessor-read'}:
        load('backup-snapshot', path).require_closure_source(path)
        spec = importlib.util.spec_from_file_location(
            'predecessor_fixture', path / 'deploy/tests/portfolio-closure-recovery-fixture.py',
        )
        fixture = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture)
        print(fixture.program(mode='create' if kind == 'predecessor-seed' else 'projection'))
        return
    if kind == 'roles' and path == Path('/run/birja/catalog-receipts.json'):
        print(CATALOG_ROLE_PROBE)
        return
    if kind != 'replay' or path != Path('/run/birja/catalog-receipts.json'):
        raise ValueError('Unexpected disposable runtime program')
    print('import asyncio, json\nfrom pathlib import Path')
    print(inspect.getsource(catalog_economics))
    print(f'asyncio.run(catalog_economics("replay", Path({str(path)!r})))')


CATALOG_ROLE_PROBE = """
import asyncio
from urllib.parse import urlsplit
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import Settings
from app.db.connection import database_connect_args
from app.db.schema_contract import require_schema

async def main():
    settings = Settings()
    assert settings.env == 'test'
    target = urlsplit(settings.database_url)
    assert (target.hostname, target.port, target.username) == ('postgres', 5432, 'birja_test')
    assert target.path in {'/birja_test', '/birja_restore_test'} and not target.query
    assert settings.database_ssl_ca_file
    for role, password in (('birja_app', 'test-app'), ('birja_scheduler', 'test-scheduler')):
        url = settings.database_url.replace('birja_test:test@', f'{role}:{password}@')
        assert url != settings.database_url
        engine = create_async_engine(url, connect_args=database_connect_args(settings))
        try:
            async with engine.connect() as conn:
                assert await require_schema(conn) == '0027'
                assert await conn.scalar(text(
                    'SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'
                ))
                assert await conn.scalar(text('SELECT current_user')) == role
                assert not await conn.scalar(text(
                    'SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolreplication OR rolbypassrls '
                    'FROM pg_roles WHERE rolname=current_user'
                ))
                assert not await conn.scalar(text(
                    "SELECT has_table_privilege(current_user,'stock_catalog_admissions','INSERT')"
                ))
        finally:
            await engine.dispose()
    print('catalog_runtime_verified_tls=true')

asyncio.run(main())
"""


def catalog_cache_absent(stage, revision, canary):
    restored = stage / ('restored-' + revision)
    for path in (restored / 'manifest.json', restored / 'database.dump', stage / (revision + '.sql')):
        assert canary.encode() not in path.read_bytes(), path.name


async def catalog_economics(mode, receipt_path):
    """Use the production services and restricted TLS roles on the owned clone."""
    from dataclasses import asdict, replace
    from datetime import UTC, datetime, time, timedelta
    from decimal import Decimal
    from types import SimpleNamespace
    from urllib.parse import urlsplit, urlunsplit

    from sqlalchemy import delete, text
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from app.core.config import Settings
    from app.db.connection import database_connect_args
    from app.db.schema_contract import require_schema
    from app.models.stock import StockDataAdmission, StockSession
    from app.schemas.stock_catalog_quotes import CatalogConfirmIn
    from app.services import stock_sessions, stock_catalog_trading
    from app.services.corporate_actions import apply_due_actions
    from app.services.dividends import process_dividend
    from app.services.event_history import list_event_history
    from app.services.portfolio import get_portfolio
    from app.services.portfolios import OwnedActivePortfolio
    from app.services.stock_catalog_actions import load_catalog_action_authority, lock_catalog_action_scope
    from app.services.stock_ownership import acquire_stock_gate
    if mode == 'seed':
        from tests.test_stock_catalog_financial_actions import _derive, _dividend, _ingest
        from tests.test_stock_catalog_promotion import OTHER_ASSET, _listing, _promote, _reviewed_grant
        from tests.test_stock_catalog_sql_actions import ACTION_FIELDS
        from tests.test_stock_catalog_sql_authority import execution_market
        from tests.test_stock_catalog_trading import _confirmation
        from tests.test_stock_sessions import evidence

    if mode not in {'seed', 'replay'}:
        raise ValueError('Unknown synthetic economics mode')
    settings = Settings(stock_data_enabled=mode == 'seed', stock_data_account='birja',
                        stock_data_server='birja')
    url = urlsplit(settings.database_url)
    databases = {'/birja_test'} if mode == 'seed' else {'/birja_restore_test'}
    fixture_hosts = {('127.0.0.1', 55434)}
    if mode == 'replay' and receipt_path == Path('/run/birja/catalog-receipts.json'):
        fixture_hosts.add(('postgres', 5432))
        databases.add('/birja_test')
    if (settings.env != 'test' or (url.hostname, url.port) not in fixture_hosts
        or url.username != 'birja_test' or url.path not in databases or url.query
        or not settings.database_ssl_ca_file):
        raise ValueError('Owned disposable TLS database required')

    def engine(user, password):
        target = url._replace(netloc=f'{user}:{password}@{url.hostname}:{url.port}')
        return create_async_engine(urlunsplit(target), connect_args=database_connect_args(settings))

    app = engine('birja_app', 'test-app')
    scheduler = engine('birja_scheduler', 'test-scheduler')
    owner = engine('birja_migrator', 'fixture-migrator-only')
    app_sessions = async_sessionmaker(app, expire_on_commit=False)
    scheduler_sessions = async_sessionmaker(scheduler, expire_on_commit=False)
    owner_sessions = async_sessionmaker(owner, expire_on_commit=False)

    def wire(value):
        return json.loads(json.dumps(value, default=str))

    async def confirm(market, order):
        async with app_sessions() as db:
            fill, created = await stock_catalog_trading.execute(
                db, catalog_id=market['catalog'], portfolio=OwnedActivePortfolio(market['p'], market['u']),
                order=order, settings=settings,
            )
            return fill.model_dump(mode='json'), created

    async def observe(market, action_coin):
        portfolio = market['p']
        async with app_sessions() as db:
            history = await list_event_history(db, portfolio=OwnedActivePortfolio(portfolio, market['u']))
        async with owner_sessions() as db:
            cash = await db.scalar(text('SELECT cash FROM accounts WHERE id=:p'), {'p': portfolio})
            rows = (await db.execute(text('''
                SELECT h.coin_id,h.quantity,h.cost_basis FROM holdings h
                JOIN stock_catalog_instruments b ON b.coin_id=h.coin_id
                WHERE h.portfolio_id=:p ORDER BY h.coin_id
            '''), {'p': portfolio})).all()
            counts = (await db.execute(text('''
                SELECT (SELECT count(*) FROM stock_catalog_fill_evidence),
                       (SELECT count(*) FROM stock_dividend_payments WHERE portfolio_id=:p),
                       (SELECT count(*) FROM stock_dividend_decisions WHERE portfolio_id=:p),
                       (SELECT count(*) FROM stock_split_applications WHERE coin_id=:c),
                       (SELECT count(*) FROM stock_ownership_movements WHERE portfolio_id=:p)
            '''), {'p': portfolio, 'c': action_coin})).one()
            return wire({'cash': cash, 'holdings': [list(row) for row in rows],
                         'history': history.model_dump(mode='json')['items'], 'counts': list(counts)})

    async def split_again(action_coin):
        async with scheduler_sessions.begin() as db:
            now = await db.scalar(text('SELECT clock_timestamp()'))
            authority = await load_catalog_action_authority(
                db, action_coin, now, account='birja', server='birja', allow_fixture=True,
            )
            assert authority is not None
            return list(await apply_due_actions(db, action_coin, catalog=authority))

    async def pay(work):
        async with scheduler_sessions() as db:
            return wire(asdict(await process_dividend(db, **work)))

    try:
        for role in (app, scheduler):
            async with role.connect() as conn:
                assert await conn.scalar(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))
                assert await require_schema(conn) == '0027'
        if mode == 'replay':
            saved = json.loads(receipt_path.read_text())
            market = saved['market']
            assert await observe(market, saved['action_coin']) == saved['economics']
            for payload, expected in saved['orders']:
                assert await confirm(market, CatalogConfirmIn.model_validate(payload)) == (expected, False)
            for work, expected in saved['payments']:
                assert await pay(work) == expected
            assert await split_again(saved['action_coin']) == saved['splits']
            assert await observe(market, saved['action_coin']) == saved['economics']
            if url.hostname == 'postgres':
                async with app_sessions() as db:
                    active = (await db.execute(text("""
                        SELECT a.id, a.user_id FROM accounts a
                        JOIN holdings h ON h.portfolio_id = a.id
                        JOIN coins c ON c.id = h.coin_id
                        WHERE a.closed_at IS NULL AND c.symbol = 'BTC' AND h.quantity > 0
                        ORDER BY a.id LIMIT 1
                    """))).one()
                    portfolio = await get_portfolio(
                        db, portfolio=OwnedActivePortfolio(*active), settings=settings,
                    )
                    assert any(row.symbol == 'BTC' and row.quantity > 0 for row in portfolio.holdings)
                print('stock_switches_disabled=true original_crypto_holding_available=true')
            print('restricted_tls_replay=true buy_sell_dividend_correction_split_exact=true')
            return

        async with owner_sessions.begin() as db:
            await db.execute(delete(StockDataAdmission).where(StockDataAdmission.product == 'calendar'))
            await db.execute(delete(StockSession))
        day = timedelta(days=1)
        market = await execution_market.__wrapped__(owner_sessions, catalog_age=2 * day)
        # The shared trade fixture creates already-initialized legacy roots.
        # The archive also requires their owner initialization lineage.
        async with owner_sessions.begin() as db:
            initialized = await db.scalar(text('''
                WITH added AS (
                    INSERT INTO portfolio_initializations(user_id,origin)
                    SELECT u.id,'legacy' FROM users u
                    JOIN accounts a ON a.user_id=u.id
                    LEFT JOIN portfolio_initializations i ON i.user_id=u.id
                    WHERE i.id IS NULL GROUP BY u.id RETURNING id
                ) SELECT count(*) FROM added
            '''))
            assert initialized == 3
        today, opens, end, now = (market[key] for key in ('session', 'opens', 'end', 'now'))
        # A previous session's cash dividend is due even when the current UTC
        # session date is still ahead of New York's payment date.
        dividend_day = today - day
        dividend_open = datetime.combine(dividend_day, time(14, 30), UTC)
        dividend_origin = dividend_open - timedelta(minutes=5)
        bounds = (
            (dividend_day, dividend_open, dividend_open + timedelta(hours=6, minutes=30)),
            (today, opens, end),
            (today + day, opens + day, end + day),
        )
        stock_sessions._calendar_bounds = lambda *args: bounds
        reviewed = evidence(now)
        reviewed = replace(
            reviewed, generation=1, valid_until=end,
            calendar={**reviewed.calendar, 'review_valid_until': end.isoformat()},
            scope={**reviewed.scope, 'durable_accounting': True, 'backup_restore': True,
                   'retention_mode': 'durable-accounting'},
        )
        async with owner_sessions.begin() as db:
            await db.execute(delete(StockDataAdmission).where(StockDataAdmission.product == 'calendar'))
            db.add(StockDataAdmission(**asdict(reviewed)))
            await db.execute(delete(StockSession))
            db.add_all(StockSession(**asdict(row)) for row in stock_sessions.build_sessions(now, reviewed))
            await db.execute(text('''
                INSERT INTO stock_catalog_financial_quotes
                  (coin_id,catalog_id,listing_id,provider_asset_id,provider_admission_id,
                   execution_admission_id,bid,ask,unit_epoch,event_at,collected_at,observed_at,
                   session_date,calendar_generation,opens_at,closes_at,valid_until)
                VALUES(:c,:catalog,:listing,:asset,:provider,:execution,9.995,10.005,0,
                       CAST(:now AS timestamptz)-interval '1 second',:now,:now,:session,1,:opens,:end,:end)
            '''), market)
        orders = []
        for order in (_confirmation(market, quantity='3'),
                      _confirmation(market, side='sell', expected_exec_price='9.995')):
            original, created = await confirm(market, order)
            assert created
            orders.append((order.model_dump(mode='json'), original))

        async with owner_sessions() as db:
            generation = await db.scalar(text('SELECT id FROM stock_catalog_generations WHERE is_active'))
        listing = await _listing(owner_sessions, generation, 'FQN')
        grant = await _reviewed_grant(
            owner_sessions, listing, OTHER_ASSET, dividend_origin, asset_valid_until=end,
        )
        binding = await _promote(owner_sessions, listing, grant, dividend_origin)
        case = SimpleNamespace(binding=binding, listing=listing, now=now, cutoff=dividend_open)
        async with owner_sessions.begin() as db:
            await lock_catalog_action_scope(db)
            await acquire_stock_gate(db, binding.coin_id)
            conn = await db.connection()
            scope = {
                'account': binding.account, 'server': binding.server,
                'catalog_id': str(binding.catalog_id), 'listing_id': str(binding.listing_id),
                'provider_asset_id': binding.provider_asset_id, 'feed': 'alpaca-corporate-actions',
            }
            grant = await db.scalar(text('''
                INSERT INTO stock_catalog_admissions
                  (artifact,reference,reviewed_at,valid_until,fields,scope,is_fixture)
                VALUES ('catalog_actions','Disposable action recovery review',:origin,:end,
                        CAST(:fields AS jsonb),CAST(:scope AS jsonb),true) RETURNING id
            '''), {'origin': dividend_origin, 'end': end, 'fields': json.dumps(ACTION_FIELDS),
                   'scope': json.dumps(scope)})
            values = market | {'c': binding.coin_id, 'catalog': binding.catalog_id,
                               'listing': binding.listing_id, 'actions': grant,
                               'origin': dividend_origin}
            for query in (
                '''INSERT INTO stock_catalog_action_coverage
                   (coin_id,catalog_id,listing_id,admission_id,journal_origin,coverage_start,
                    covered_until,observed_at,valid_until)
                   VALUES (:c,:catalog,:listing,:actions,:origin,:origin,:now,:now,:end)''',
                '''UPDATE stock_action_state SET health='current',admission_generation=:actions,
                    checked_at=:now,valid_until=:end,journal_start_at=:origin,complete_from=:origin,
                    coverage_start=:origin,covered_until=:now,sequence=1 WHERE coin_id=:c''',
                '''INSERT INTO holdings (portfolio_id,coin_id,user_id,quantity,cost_basis)
                   VALUES (:p,:c,:u,2,87.65)''',
                '''INSERT INTO stock_ownership_movements
                   (portfolio_id,coin_id,user_id,sequence,economic_at,recorded_at,quantity,
                    before_quantity,after_quantity,before_basis,after_basis,unit_epoch,
                    cause_kind,causal_key)
                   VALUES (:p,:c,:u,1,:origin,:now,2,0,2,0,87.65,0,'opening','opening')''',
            ):
                await conn.execute(text(query), values)

        dividend = _dividend(case)
        payments = []
        for action, outcome in ((dividend, 'original'), (replace(dividend, rate=Decimal('0.90')), 'applied')):
            async with scheduler.begin() as conn:
                work = await _derive(conn, case, action)
            result = await pay(work)
            assert result['outcome'] == outcome
            payments.append((work, result))
        case.cutoff = opens
        split = _dividend(case, event_type='forward_split', rate=None, units='pre_split',
                          economic_at=opens, new_rate=Decimal(2), old_rate=Decimal(1))
        async with scheduler_sessions.begin() as db:
            authority, revision = await _ingest(db, case, split)
            assert revision.classification == 'supported_forward_split'
            splits = list(await apply_due_actions(db, binding.coin_id, catalog=authority))
        assert len(splits) == 1
        economics = await observe(market, binding.coin_id)
        assert Decimal(economics['cash']) == Decimal('1216.34')
        assert [(Decimal(quantity), Decimal(basis)) for _, quantity, basis in economics['holdings']] == [
            (Decimal(2), Decimal('20.01')), (Decimal(4), Decimal('87.65')),
        ]
        assert [row['kind'] for row in economics['history']] == [
            'split', 'dividend_correction', 'dividend', 'trade', 'trade',
        ]
        assert all(row['symbol'] == listing.ticker and row['name'] == listing.company_name
                   for row in economics['history'][:3])
        assert economics['counts'] == [2, 1, 1, 1, 4]
        receipt_path.write_text(json.dumps({
            'market': {key: market[key] for key in ('catalog', 'p', 'u')},
            'action_coin': binding.coin_id, 'orders': orders, 'payments': payments,
            'splits': splits, 'economics': economics,
        }))
    finally:
        for role in (app, scheduler, owner):
            await role.dispose()


class PortfolioRecoveryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        producer = load('backup-snapshot')
        directory = tempfile.TemporaryDirectory(prefix='birja-retained-0024-')
        cls.addClassCleanup(directory.cleanup)
        cls.retained_0024 = Path(directory.name)
        source = subprocess.check_output(
            ['git', 'archive', '--format=tar', RETAINED_0024, *producer.PORTFOLIO_PAYLOAD_V4],
            cwd=ROOT,
        )
        with tarfile.open(fileobj=io.BytesIO(source), mode='r:') as archive:
            archive.extractall(cls.retained_0024, filter='data')
        directory = tempfile.TemporaryDirectory(prefix='birja-retained-0025-')
        cls.addClassCleanup(directory.cleanup)
        cls.retained_0025 = Path(directory.name)
        retained_catalog(cls.retained_0025)

    def test_ops_archive_family_is_authenticated_and_finite(self):
        spec=importlib.util.spec_from_file_location('ops_contracts',ROOT/'deploy/tests/ops-fixtures.py')
        ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)
        for profile,version,revision in (('deploy-recovery-v3',2,'0020'),('deploy-recovery-v4',3,'0023'),
                                         ('deploy-recovery-v5',4,'0024')):
            inventory={'recovery_profile':profile,'portfolio_payload':{'version':version,'revision':revision}}
            with mock.patch.object(ops.r,'bundle_verify',return_value=inventory) as authenticate:
                self.assertEqual(ops.archive_profile(Path('/synthetic/archive'),'digest'),profile)
                authenticate.assert_called_once_with(Path('/synthetic/archive'),'digest')
            for field,value in (('version',1),('revision','0022')):
                changed=copy.deepcopy(inventory);changed['portfolio_payload'][field]=value
                with mock.patch.object(ops.r,'bundle_verify',return_value=changed),self.assertRaises(ValueError):
                    ops.archive_profile(Path('/synthetic/archive'),'digest')
        with mock.patch.object(ops.r,'bundle_verify',side_effect=ValueError('integrity')), \
             self.assertRaisesRegex(ValueError,'integrity'):
            ops.archive_profile(Path('/synthetic/archive'),'digest')

    def test_ops_restore_always_supplies_the_saved_source_manifest(self):
        for name in ('ops-fixtures.py','portfolio-smoke.py'):
            tree=ast.parse((ROOT/'deploy/tests'/name).read_text())
            calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call)
                   and isinstance(node.func,ast.Attribute) and node.func.attr=='restored']
            self.assertTrue(calls,name)
            for call in calls:
                self.assertTrue(any(keyword.arg=='manifest' for keyword in call.keywords),(name,call.lineno))

    def test_v4_consumer_requires_exact_revision_inventory_and_profile(self):
        producer, consumer = load('backup-snapshot'), load('verify-restore')
        payload = producer.halt_payload_inventory(self.retained_0024)
        inventory = {'portfolio_payload': payload}
        self.assertEqual(consumer.portfolio_payload_files(inventory), producer.PORTFOLIO_PAYLOAD_V4)
        consumer.verify_portfolio_inventory(inventory, payload['sha256'])
        for field, value in (('version', True), ('version', 2), ('revision', '0020'),
                             ('revision', '0022')):
            changed = copy.deepcopy(inventory)
            changed['portfolio_payload'][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                consumer.verify_portfolio_inventory(changed, payload['sha256'])
        for name in producer.PORTFOLIO_PAYLOAD_V4:
            changed = copy.deepcopy(inventory)
            del changed['portfolio_payload']['sha256'][name]
            with self.subTest(missing=name), self.assertRaises(ValueError):
                consumer.verify_portfolio_inventory(changed, payload['sha256'])

    def test_v3_consumer_checks_every_source_projection_before_regrant(self):
        consumer = load('verify-restore')
        saved = json.loads((ROOT/'deploy/tests/fixtures/portfolio-recovery-0023.json').read_text())
        for section in ('tables','identity_state','financial','schema','portfolio_state',
                        'management_state','closure_state','stock_invalid'):
            changed = copy.deepcopy(saved['quarantined'])
            if section == 'tables': changed[section]['accounts']['sha256'] = '0'*64
            elif section == 'identity_state': changed[section][0][1] += 1
            elif section == 'stock_invalid': changed[section] = 1
            else: changed[section] = {}
            with self.subTest(section=section), \
                 mock.patch.object(consumer,'canonical',return_value=changed), \
                 mock.patch.object(consumer,'sql',return_value=b'[]') as statement, \
                 self.assertRaises((ValueError,KeyError)):
                consumer.restore_closure_authority([],saved['manifest'])
            self.assertTrue(all('GRANT ' not in call.args[1] for call in statement.call_args_list))
        with mock.patch.object(consumer,'canonical',side_effect=[saved['quarantined'],saved['quarantined'],saved['manifest']]), \
             mock.patch.object(consumer,'sql',side_effect=[b'[]',b'0',b'',b'']) as statement:
            consumer.restore_closure_authority([],saved['manifest'])
            self.assertIn('GRANT EXECUTE ON FUNCTION public.close_portfolio',statement.call_args_list[-1].args[1])
        for grants in ([['relation','accounts','birja_app','UPDATE',False]],
                       [['routine','close_portfolio(bigint,bigint,uuid,text,text)','birja_app','EXECUTE',False]]):
            with mock.patch.object(consumer,'canonical',return_value=saved['quarantined']), \
                 mock.patch.object(consumer,'sql',return_value=json.dumps(grants).encode()) as statement, \
                 self.assertRaises(ValueError):
                consumer.restore_closure_authority([],saved['manifest'])
            self.assertEqual(statement.call_count,1)

    def test_retained_contract_import_uses_complete_authenticated_source(self):
        consumer = load('verify-restore')
        spec = importlib.util.spec_from_file_location('fixed_recovery_sources',ROOT/'deploy/tests/portfolio-sources.py')
        sources = importlib.util.module_from_spec(spec);spec.loader.exec_module(sources)
        with tempfile.TemporaryDirectory(prefix='birja-retained-consumer-') as tmp:
            root=Path(tmp);(root/'deploy').mkdir();(root/'sources').mkdir()
            with mock.patch.object(consumer,'HERE',root/'deploy'):
                for revision in ('0017','0020'):
                    lane='portfolio'+revision
                    archive=root/'sources'/(lane+'.tar')
                    archive.write_bytes(sources.source_archive(lane))
                    contract=consumer.recovery_contract(revision)
                    self.assertNotEqual(contract.HERE,ROOT/'deploy')
                    self.assertTrue((contract.HERE.parent/'backend/app/db/portfolio_bootstrap.py').is_file())
                    original=json.loads((contract.HERE.parent/('deploy/tests/fixtures/portfolio-recovery-'+revision+'.json')).read_text())
                    contract.validate_manifest(original)
                    self.assertNotIn('0023',contract.SUPPORTED_REVISIONS)
                    archive.write_bytes(archive.read_bytes()+b'coherent alteration')
                    with self.assertRaises(ValueError):consumer.recovery_contract(revision)
        for contract in consumer._RETAINED_CONTRACTS.values():contract._retained_directory.cleanup()
    def test_retained_halt_payload_is_explicit_and_every_required_member_is_bound(self):
        producer = load('backup-snapshot')
        root = self.retained_0024
        inventory = producer.halt_payload_inventory(root)
        self.assertEqual((inventory['version'],inventory['revision']), (4,'0024'))
        producer.verify_halt_inventory(root,inventory)
        self.assertEqual(len(producer.contract_columns('0024')),31)
        self.assertEqual(len(producer.identity_tables('0024')),24)
        for table in producer.CLOSURE_COLUMNS:
            self.assertIn(table,producer.contract_columns('0024'))
        for name in producer.PORTFOLIO_PAYLOAD_V4:
            damaged=copy.deepcopy(inventory);del damaged['sha256'][name]
            with self.subTest(omitted=name),self.assertRaises(ValueError):
                producer.verify_halt_inventory(root,damaged)
            damaged=copy.deepcopy(inventory);damaged['sha256'][name]='0'*64
            with self.subTest(changed=name),self.assertRaises(ValueError):
                producer.verify_halt_inventory(root,damaged)
        for key,value in (('version',True),('version',2),('revision','0020'),('revision','0022')):
            damaged=copy.deepcopy(inventory);damaged[key]=value
            with self.assertRaises(ValueError):producer.verify_halt_inventory(root,damaged)
        for revision in ('0021','0022'):
            for command in (producer.contract_columns,producer.identity_tables,producer.manifest_sql):
                with self.assertRaisesRegex(ValueError,'migration_only'):command(revision)

    def test_current_closure_exact_manifest_and_coherent_mutations_refuse(self):
        producer=load('backup-snapshot')
        saved=json.loads((ROOT/'deploy/tests/fixtures/portfolio-recovery-0023.json').read_text())
        producer.validate_manifest(saved['manifest'])
        producer.validate_manifest(saved['quarantined'],quarantined=True)
        with self.assertRaises(ValueError):producer.validate_manifest(saved['quarantined'])
        mutations=[
            lambda m:m['tables'].pop('portfolio_lifecycle_closures'),
            lambda m:m['tables'].pop('portfolio_closure_intents'),
            lambda m:m['identity_state'].pop(),
            lambda m:m['schema']['constraints'].pop(),
            lambda m:m['schema']['indexes'].pop(),
            lambda m:m['portfolio_authority']['functions'].pop(),
            lambda m:m['portfolio_authority']['functions'][0].__setitem__('definition','SELECT true'),
            lambda m:m['portfolio_authority']['roles'][0].__setitem__(2,True),
            lambda m:m['closure_contract'].__setitem__('catalogue','0'*64),
            lambda m:m['closure_contract'].__setitem__('acl','0'*64),
            lambda m:m['closure_contract'].__setitem__('defaults','0'*64),
            lambda m:m['closure_state'].__setitem__('invalid',1),
            lambda m:m['closure_state'].__setitem__('closures',0),
            lambda m:m['management_state'].__setitem__('initializations',0),
        ]
        for original,quarantined in ((saved['manifest'],False),(saved['quarantined'],True)):
            for mutate in mutations:
                changed=copy.deepcopy(original);mutate(changed)
                with self.assertRaises((ValueError,KeyError)):
                    producer.validate_manifest(changed,quarantined=quarantined)

    def test_current_source_tampering_refuses_before_authority_import(self):
        current = load('backup-snapshot')
        historical = load('backup-snapshot', self.retained_0025)
        profiles = (
            ('0025', self.retained_0025, historical, current.CATALOG_SOURCE_SHA256),
            ('0027', ROOT, current, current.CATALOG_NYSE_SOURCE_SHA256),
        )
        for revision, source, producer, pins in profiles:
            with tempfile.TemporaryDirectory(prefix='birja-closure-source-') as tmp:
                root = Path(tmp)
                for name in pins:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((source / name).read_bytes())
                producer.require_closure_source(root, revision=revision, allow_successor=False)
                for name in pins:
                    path = root / name
                    original = path.read_bytes()
                    path.write_bytes(original + b'\n# Unreviewed fixture content\n')
                    with self.subTest(revision=revision, name=name), \
                         mock.patch.object(producer, 'HERE', root / 'deploy'), \
                         mock.patch.object(producer.importlib.util, 'spec_from_file_location',
                                           side_effect=AssertionError('authority import before validation')), \
                         self.assertRaises(ValueError):
                        producer.closure_bootstrap(revision)
                    path.write_bytes(original)

    def test_v1_inventory_remains_explicit_and_cannot_inherit_current_revision(self):
        consumer = load("verify-restore")
        hashes = {name: "a" * 64 for name in consumer.PORTFOLIO_PAYLOAD_V1}
        inventory = {"portfolio_payload": {"version": 1, "sha256": hashes}}
        consumer.verify_portfolio_inventory(inventory, hashes)
        for field, value in [("version", 2), ("revision", "0020")]:
            damaged = copy.deepcopy(inventory)
            damaged["portfolio_payload"][field] = value
            with self.assertRaises((ValueError, KeyError)):
                consumer.verify_portfolio_inventory(damaged, hashes)

    def test_final_columns_have_complete_owned_lineage_and_global_marker(self):
        producer = load("backup-snapshot")
        columns = producer.contract_columns("0017")
        self.assertEqual(len(columns), 27)
        self.assertEqual(columns["portfolio_stock_closures"], {
            "id", "portfolio_id", "user_id", "coin_id", "closed_at", "closing_sequence", "unit_epoch"
        })
        for table in ("holdings", "trades", "stock_fill_facts", "stock_ownership_movements",
                      "stock_dividend_entitlements", "stock_dividend_payments", "stock_dividend_decisions"):
            self.assertIn("portfolio_id", columns[table])
        self.assertTrue({"name", "closed_at"} <= columns["accounts"])
        self.assertIn("owner_digest_version", columns["stock_split_applications"])
        self.assertNotIn("portfolio_id", columns["stock_split_applications"])
        self.assertNotIn("user_id", columns["stock_split_applications"])

    def test_stages_refuse_explicitly(self):
        producer = load("backup-snapshot")
        for revision in ("0015", "0016"):
            for function in (producer.contract_columns, producer.manifest_sql, producer.schema_guard_sql):
                with self.assertRaisesRegex(ValueError, "migration_only"):
                    function(revision)

    def test_legacy_manifest_queries_remain_byte_exact(self):
        producer = load("backup-snapshot")
        hashes = {
            "0008": "52753d97387ec491c6494d327a6037d847cdc323bafb571c2dac6bdb0d28b5a5",
            "0011": "a4917389531c8ded7ba4e080a529490661ffdee1d3058d44efd428aa2004c72d",
            "0012": "d8ae9ab6d6d307c4b6a37b9871aa0462c6cf593a485d184f6d505ec1f93eba46",
            "0013": "2306b52d3f9f5a6bfafa60b2d475390e4ce4d7d03d2bf162e44ce338d9d72734",
        }
        for revision, expected in hashes.items():
            self.assertEqual(hashlib.sha256(producer.manifest_sql(revision).encode()).hexdigest(), expected)

    def fixture(self):
        import json
        return json.loads((ROOT / 'deploy/tests/fixtures/portfolio-recovery-0017.json').read_text())

    def test_independent_final_catalogue_and_identity_inventory(self):
        producer = load('backup-snapshot')
        manifest = self.fixture()
        producer.validate_manifest(manifest)
        self.assertEqual(len(manifest['schema']['relations']), 27)
        self.assertEqual(sum(r[2] == 'f' for r in manifest['schema']['constraints']), 65)
        self.assertEqual(len(manifest['portfolio_authority']['functions']), 10)
        self.assertEqual(len(producer.identity_tables('0017')), 20)
        expected = {'check_portfolio_financial_write()', 'lock_stock_portfolio_roots(bigint)',
                    'check_stock_split_digest_version()'}
        self.assertTrue(expected <= {r['signature'] for r in manifest['portfolio_authority']['functions']})

    def test_every_owned_projection_and_terminal_boundary_is_archived(self):
        producer = load('backup-snapshot')
        query = producer.manifest_sql('0017')
        for table in producer.PORTFOLIO_OWNED:
            line = next(line for line in query.splitlines() if "SELECT '"+table+"'," in line)
            self.assertIn('portfolio_id::text', line)
        for name in ('portfolio_stock_closures', 'closing_sequence', 'owner_digest_version',
                     'pg_get_functiondef', 'has_column_privilege', 'has_sequence_privilege'):
            self.assertIn(name, query)
        self.assertEqual(query.count('FROM portfolio_stock_closures_id_seq'), 1)

    def test_mutated_schema_marker_constraints_and_authority_fail_independently(self):
        producer = load('backup-snapshot')
        original = self.fixture()
        mutations = []
        for index, row in enumerate(original['schema']['columns']):
            if row[:2] == ['stock_split_applications','owner_digest_version']:
                for column, value in ((2,'integer'),(3,'NO'),(4,'2')):
                    mutations.append(lambda m,i=index,c=column,v=value:m['schema']['columns'][i].__setitem__(c,v))
        mutations += [lambda m:m['schema']['identities'].pop(),
            lambda m:m['schema']['constraints'].pop(),
            lambda m:m['schema']['indexes'].pop(),
            lambda m:m['schema']['relations'].append(['unreviewed','r']),
            lambda m:m['portfolio_authority']['functions'].pop(),
            lambda m:m['portfolio_authority']['functions'][0].__setitem__('definition','SELECT true'),
            lambda m:m['portfolio_authority']['functions'][0].__setitem__('owner','birja_app'),
            lambda m:m['portfolio_authority']['functions'][0].__setitem__('acl',[['PUBLIC','EXECUTE',False]]),
            lambda m:m['portfolio_authority']['functions'].append(copy.deepcopy(m['portfolio_authority']['functions'][0])),
            lambda m:m['portfolio_authority']['triggers'].pop(),
            lambda m:m['portfolio_authority']['tables'][0].__setitem__(4,True),
            lambda m:m['portfolio_authority']['columns'][0].__setitem__(5,True),
            lambda m:m['portfolio_authority']['roles'][0].__setitem__(2,True),
            lambda m:m['portfolio_state'].__setitem__('invalid',1),
            lambda m:m['portfolio_state'].__setitem__('closed',1),
            lambda m:m['portfolio_state'].__setitem__('v2_markers',1),
            lambda m:m['identity_state'].pop()]
        for mutation in mutations:
            candidate = copy.deepcopy(original)
            mutation(candidate)
            with self.assertRaises(ValueError):
                producer.validate_manifest(candidate)

    def quarantined(self, manifest):
        result = copy.deepcopy(manifest)
        for function in result['portfolio_authority']['functions']:
            if function['signature'].split('(')[0] in (
                'apply_stock_dividend','record_stock_dividend_hold','lock_stock_portfolio_roots'
            ):
                function['acl'] = []
        return result

    def test_consumer_compares_every_projection_before_identity_queries(self):
        restore, producer = load('verify-restore'), load('backup-snapshot')
        source = self.fixture()
        actual = self.quarantined(source)
        producer.validate_manifest(actual, quarantined=True)
        with mock.patch.object(restore,'recovery_contract',return_value=producer), \
             mock.patch.object(restore,'canonical',return_value=actual), \
             mock.patch.object(restore,'sql',return_value=b't') as sql:
            restore.verify([],source)
            self.assertEqual(sql.call_count,20)
        for table in ('accounts','holdings','trades','stock_fill_facts',
                      'stock_split_applications','stock_ownership_movements',
                      'stock_dividend_payments','stock_dividend_decisions',
                      'portfolio_stock_closures'):
            changed = copy.deepcopy(actual)
            changed['tables'][table]['sha256'] = 'f'*64
            with mock.patch.object(restore,'recovery_contract',return_value=producer), \
                 mock.patch.object(restore,'canonical',return_value=changed), \
                 mock.patch.object(restore,'sql') as sql:
                with self.assertRaises(ValueError):restore.verify([],source)
                sql.assert_not_called()

    def no_acl(self, manifest):
        result = copy.deepcopy(manifest)
        authority = result['portfolio_authority']
        for function in authority['functions']:
            function['acl'] = [['PUBLIC','EXECUTE',False]]
        for key, start in (('tables',2),('columns',3),('sequences',2),('schema_create',1)):
            for row in authority[key]:row[start:] = [False]*len(row[start:])
        return result

    def test_no_acl_restore_authenticates_before_any_fixed_grants(self):
        restore, producer = load('verify-restore'), load('backup-snapshot')
        source = self.fixture()
        no_acl = self.no_acl(source)
        self.assertEqual(producer.canonical_hash(no_acl['portfolio_authority']),producer.PORTFOLIO_NO_ACL_SHA256)
        for key in ('schema','portfolio_authority'):
            damaged = copy.deepcopy(no_acl)
            damaged[key] = {}
            with mock.patch.object(restore,'recovery_contract',return_value=producer), \
                 mock.patch.object(restore,'canonical',return_value=damaged), \
                 mock.patch.object(restore,'sql') as sql:
                with self.assertRaises(ValueError):restore.restore_portfolio_authority([])
                self.assertEqual(sql.call_count,1)
                self.assertNotIn('GRANT',sql.call_args.args[1])
        with mock.patch.object(restore,'recovery_contract',return_value=producer), \
             mock.patch.object(restore,'canonical',side_effect=[no_acl,self.quarantined(source)]), \
             mock.patch.object(restore,'sql') as sql:
            restore.restore_portfolio_authority([])
            self.assertEqual(sql.call_count,2)
            grants=sql.call_args.args[1]
            self.assertIn('REVOKE ALL ON FUNCTION public.apply_stock_dividend',grants)
            self.assertNotIn('CREATE FUNCTION',grants)

    def test_final_marker_and_private_helpers_are_pinned_independent_of_archive(self):
        producer=load('backup-snapshot')
        source=self.fixture()
        self.assertEqual({f['signature'] for f in source['portfolio_authority']['functions']},producer.PORTFOLIO_SIGNATURES)
        for signature in ('check_portfolio_financial_write()','check_stock_split_digest_version()'):
            function=next(f for f in source['portfolio_authority']['functions'] if f['signature']==signature)
            self.assertEqual(function['acl'],[])
            self.assertEqual(function['owner'],'birja_migrator')
        for mutation in (
            lambda m:m['portfolio_authority'].__setitem__('unsafe_acl',1),
            lambda m:m['portfolio_authority']['functions'][0].__setitem__('acl',[['birja_app','EXECUTE',True]]),
            lambda m:m['identity_state'][0].__setitem__(1,0),
        ):
            damaged=copy.deepcopy(source);mutation(damaged)
            with self.assertRaises(ValueError):producer.validate_manifest(damaged)

    def test_wrapper_import_and_dispatch_have_no_operational_side_effects(self):
        program = "source deploy/backup.sh; source deploy/restore-check.sh; declare -F backup_main restore_main"
        result = subprocess.run(['bash','-c',program],cwd=ROOT,capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.splitlines(),['backup_main','restore_main'])
        producer=load('backup-snapshot')
        for revision in ('0015','0016'):
            with self.assertRaisesRegex(ValueError,'migration_only'):
                producer.validate_manifest({'revision':revision})


def postgres_proof():
    """Use the complete authenticated 0017 test/application tree for old readers."""
    spec = importlib.util.spec_from_file_location('proof_sources', ROOT/'deploy/tests/portfolio-sources.py')
    sources = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sources)
    data = sources.source_archive('portfolio0017')
    with tempfile.TemporaryDirectory(prefix='birja-p14-15-retained-proof-') as tmp:
        historical = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
            archive.extractall(historical, filter='data')
        sources.verify_source_tree(historical,data)
        _postgres_proof(historical)


def _postgres_proof(historical):
    """Actual mixed NULL/2 no-owner/no-ACL restore on the guarded test server.

    This is a logical-contract proof, not the encrypted same-archive/TLS image
    campaign in18/27. Every writer targets the exact throwaway birja-test stack.
    """
    project=os.environ.get('COMPOSE_PROJECT_NAME','birja-test')
    if project not in ('birja-test','birja-p14-15'):
        raise ValueError('owned test project required')
    dc=['docker','compose','--env-file','/dev/null','-p',project,'-f',str(ROOT/'docker-compose.test.yml')]
    def command(args,data=None):
        result=subprocess.run(dc+['exec','-T','postgres',*args],input=data,
                              capture_output=True,timeout=180)
        if result.returncode:raise AssertionError(result.stderr.decode()[-2000:])
        return result.stdout
    def query(statement,db='birja_test'):
        return command(['psql','-XqAt','-v','ON_ERROR_STOP=1','-U','birja_test','-d',db],statement.encode())
    if query('SELECT current_database(),session_user;').strip()!=b'birja_test|birja_test':
        raise AssertionError('isolated identity required')
    clone='birja_restore_test'
    if query("SELECT 1 FROM pg_database WHERE datname='birja_restore_test';").strip():
        raise AssertionError('clone must not preexist')
    env={k:os.environ[k] for k in ('PATH','HOME','LANG') if k in os.environ}
    env.update(COMPOSE_PROJECT_NAME=project,COMPOSE_DISABLE_ENV_FILE='1')
    env['PYTHONPATH']=str(historical/'backend')
    seed="""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import tests.conftest
from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_portfolio_stock_ownership import test_real_two_user_legacy_digest_reload_preserves_original_bytes
async def main():
 engine=create_async_engine(tests.conftest.TEST_DATABASE_URL)
 try:
  await reset_disposable_schema(engine)
  await test_real_two_user_legacy_digest_reload_preserves_original_bytes(engine,True)
 finally:await engine.dispose()
asyncio.run(main())
"""
    result=subprocess.run([str(ROOT/'backend/.venv/bin/python'),'-c',seed],cwd=historical/'backend',
                          env=env,capture_output=True,timeout=180)
    if result.returncode:raise AssertionError(result.stderr.decode()[-2000:])
    # Both the retained application and its authority contract come from the
    # same complete, hash-authenticated source; no current-source overlay.
    spec=importlib.util.spec_from_file_location('fixed0017_producer',historical/'deploy/backup-snapshot.py')
    producer=importlib.util.module_from_spec(spec);spec.loader.exec_module(producer)
    restore=load('verify-restore')
    current_contract=restore.recovery_contract
    restore.recovery_contract=lambda revision=None: producer if revision=='0017' else current_contract(revision)
    # Fixed source-owned grants; no manifest-selected SQL is executed.
    query(producer.PORTFOLIO_RESTORE_GRANTS)
    source=json.loads(query("SET TIME ZONE 'UTC';\n"+producer.schema_guard_sql('0017')+producer.manifest_sql('0017')))
    producer.validate_manifest(source)
    assert source['portfolio_state']['legacy_markers']==1 and source['portfolio_state']['v2_markers']==1
    assert source['portfolio_state']['closed']==1
    archive=command(['pg_dump','-U','birja_test','-d','birja_test','-Fc','--compress=none'])
    created=False
    try:
        query('CREATE DATABASE birja_restore_test OWNER birja_migrator TEMPLATE template0;')
        created=True
        query('REVOKE CONNECT ON DATABASE birja_restore_test FROM PUBLIC;')
        command(['pg_restore','-U','birja_test','-d',clone,'--role=birja_migrator',
                 '--no-owner','--no-acl','--exit-on-error','--single-transaction'],archive)
        def clone_sql(_dc,statement,db=restore.CLONE):
            return query(statement,'birja_test' if db=='birja_ops_test' else clone)
        with mock.patch.object(restore,'sql',side_effect=clone_sql):
            try:
                restore.restore_portfolio_authority([])
            except ValueError:
                actual=restore.canonical([])
                expected=PortfolioRecoveryContracts().quarantined(source)
                for key in actual['portfolio_authority']:
                    if actual['portfolio_authority'][key]!=expected['portfolio_authority'][key]:
                        a=actual['portfolio_authority'][key];b=expected['portfolio_authority'][key]
                        if isinstance(a,list) and isinstance(b,list):
                            delta=[r for r in a if r not in b]
                            raise AssertionError('clone authority mismatch '+key+': '+repr(delta)[:1500]) from None
                        raise AssertionError('clone authority mismatch '+key) from None
                raise
            restore.verify([],source)
        # Same archived marker/digest rows are admitted; new missing markers
        # and mutation remain forbidden under actual restricted SQL roles.
        insert="""BEGIN; SET LOCAL ROLE birja_scheduler;
INSERT INTO stock_split_applications(coin_id,economic_event_id,revision_id,new_rate,old_rate,
cutoff,prior_unit_epoch,new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at)
SELECT coin_id,economic_event_id,revision_id,new_rate,old_rate,cutoff,prior_unit_epoch,
new_unit_epoch,sequence_boundary,before_digest,after_digest,processed_at FROM stock_split_applications LIMIT 1;"""
        for statement in (insert,
            'BEGIN; SET LOCAL ROLE birja_app; UPDATE stock_split_applications SET owner_digest_version=2 WHERE owner_digest_version IS NULL;',
            'BEGIN; SET LOCAL ROLE birja_migrator; UPDATE stock_split_applications SET owner_digest_version=2 WHERE owner_digest_version IS NULL;'):
            result=subprocess.run(dc+['exec','-T','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1',
                '-U','birja_test','-d',clone],input=statement.encode(),capture_output=True,timeout=15)
            assert result.returncode!=0,'protected marker operation admitted'
        reader="""
import asyncio,os
os.environ.update(ENV='test',DATABASE_URL='postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_test',REDIS_URL='redis://:test@127.0.0.1:56379/0',OTP_HMAC_SECRET='test-only-otp-secret-01234567890123456789',JWT_SECRET='test-only-jwt-secret-01234567890123456789')
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine
from app.services.stock_ownership import assert_ownership_consistent
async def main():
 engine=create_async_engine('postgresql+asyncpg://birja_test:test@127.0.0.1:55432/birja_restore_test')
 try:
  async with AsyncSession(engine) as db:
   cid=(await db.execute(text('SELECT min(coin_id) FROM stock_split_applications'))).scalar_one()
   state,rows=await assert_ownership_consistent(db,cid)
   assert state.unit_epoch==2 and len({r.portfolio_id for r in rows})==3
 finally:await engine.dispose()
asyncio.run(main())
"""
        result=subprocess.run([str(ROOT/'backend/.venv/bin/python'),'-c',reader],cwd=historical/'backend',
                              env=env,capture_output=True,timeout=30)
        if result.returncode:raise AssertionError(result.stderr.decode()[-2000:])
        print('actual mixed0017 logical restore, marker refusal and reader interpretation PASS')
    finally:
        if created:query('DROP DATABASE birja_restore_test WITH (FORCE);')
        # Return the exclusive shared test lane to its current source, rather
        # than leaving a historical revision for the next current consumer.
        env['PYTHONPATH']=str(ROOT/'backend')
        cleanup="""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import tests.conftest
from tests.portfolio_fixtures import restore_current_test_schema
async def main():
 engine=create_async_engine(tests.conftest.TEST_DATABASE_URL)
 try:
  await restore_current_test_schema(engine)
 finally:await engine.dispose()
asyncio.run(main())
"""
        result=subprocess.run([str(ROOT/'backend/.venv/bin/python'),'-c',cleanup],cwd=ROOT,
                              env=env,capture_output=True,timeout=180)
        if result.returncode:raise AssertionError(result.stderr.decode()[-2000:])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] in {'--materialize-catalog', '--materialize-predecessor'}:
        destination = Path(sys.argv[2]).resolve()
        if not destination.is_dir() or any(destination.iterdir()):
            raise ValueError('Expected an empty disposable source directory')
        if sys.argv[1] == '--materialize-predecessor':
            predecessor_catalog(destination)
        else:
            retained_catalog(destination, runtime=True)
        sys.exit(0)
    if len(sys.argv) == 6 and sys.argv[1] == '--install-catalog-archive':
        host = Path(sys.argv[2])
        consumer = load('verify-restore')
        consumer.bundle_install(
            Path(sys.argv[3]), sys.argv[4], str(host), required_profile='deploy-recovery-v8',
        )
        release = host / 'var/lib/birja/recovery/releases' / sys.argv[4]
        consumer.private(release / 'deploy' / 'verify-restore.py')
        if consumer.digest(release / 'tools/restic') != consumer.RESTIC_SHA:
            raise ValueError('Archived restic checksum mismatch')
        if sys.argv[5] != '0027':
            raise ValueError('Only the exact successor release is supported')
        sys.exit(0)
    if len(sys.argv) == 5 and sys.argv[1] == '--catalog-observe':
        catalog_observe(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]))
        sys.exit(0)
    if len(sys.argv) == 4 and sys.argv[1] == '--compare-predecessor':
        compare_predecessor(Path(sys.argv[2]), Path(sys.argv[3]))
        sys.exit(0)
    if len(sys.argv) == 4 and sys.argv[1] == '--catalog-exact':
        source, observed = (json.loads(Path(name).read_text()) for name in sys.argv[2:])
        load('verify-restore').closure_evidence_matches(observed, source)
        assert observed['closure_contract'] == source['closure_contract']
        sys.exit(0)
    if len(sys.argv) == 3 and sys.argv[1] == '--catalog-authority':
        catalog_authority(Path(sys.argv[2]))
        sys.exit(0)
    if len(sys.argv) == 4 and sys.argv[1] == '--catalog-runtime-program':
        catalog_runtime_program(sys.argv[2], Path(sys.argv[3]))
        sys.exit(0)
    if len(sys.argv) == 6 and sys.argv[1] == '--catalog-snapshot':
        catalog_snapshot(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]), sys.argv[5])
        sys.exit(0)
    if len(sys.argv) in {4, 5} and sys.argv[1] == '--catalog-restore':
        catalog_restore(Path(sys.argv[2]), Path(sys.argv[3]), *sys.argv[4:])
        sys.exit(0)
    if len(sys.argv) == 5 and sys.argv[1] == '--catalog-cache-absent':
        catalog_cache_absent(Path(sys.argv[2]), sys.argv[3], sys.argv[4])
        sys.exit(0)
    if len(sys.argv) == 4 and sys.argv[1] == '--catalog-economics':
        import asyncio

        asyncio.run(catalog_economics(sys.argv[2], Path(sys.argv[3])))
        sys.exit(0)
    if '--postgres' in sys.argv:
        sys.argv.remove('--postgres')
        postgres_proof()
    unittest.main()
