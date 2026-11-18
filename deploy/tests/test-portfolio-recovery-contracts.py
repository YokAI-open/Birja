#!/usr/bin/env python3
"""Offline exact0017 producer/consumer contracts; no provider operations."""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "deploy" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortfolioRecoveryContracts(unittest.TestCase):
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
    """Actual mixed NULL/2 no-owner/no-ACL restore on the guarded test server.

    This is a logical-contract proof, not the encrypted same-archive/TLS image
    campaign in18/27. Every writer targets the exact throwaway birja-test stack.
    """
    dc=['docker','compose','-f',str(ROOT/'docker-compose.test.yml')]
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
    env['PYTHONPATH']=str(ROOT/'backend')
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
    result=subprocess.run([str(ROOT/'backend/.venv/bin/python'),'-c',seed],cwd=ROOT,
                          env=env,capture_output=True,timeout=180)
    if result.returncode:raise AssertionError(result.stderr.decode()[-2000:])
    producer,restore=load('backup-snapshot'),load('verify-restore')
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
        result=subprocess.run([str(ROOT/'backend/.venv/bin/python'),'-c',reader],cwd=ROOT,
                              env=env,capture_output=True,timeout=30)
        if result.returncode:raise AssertionError(result.stderr.decode()[-2000:])
        print('actual mixed0017 logical restore, marker refusal and reader interpretation PASS')
    finally:
        if created:query('DROP DATABASE birja_restore_test WITH (FORCE);')
        cleanup="""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import tests.conftest
from tests.portfolio_fixtures import reset_disposable_schema,migrate_to
async def main():
 engine=create_async_engine(tests.conftest.TEST_DATABASE_URL)
 try:
  await reset_disposable_schema(engine)
  await migrate_to('0017')
 finally:await engine.dispose()
asyncio.run(main())
"""
        result=subprocess.run([str(ROOT/'backend/.venv/bin/python'),'-c',cleanup],cwd=ROOT,
                              env=env,capture_output=True,timeout=180)
        if result.returncode:raise AssertionError(result.stderr.decode()[-2000:])


if __name__ == "__main__":
    if '--postgres' in sys.argv:
        sys.argv.remove('--postgres')
        postgres_proof()
    unittest.main()
