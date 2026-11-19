#!/usr/bin/env python3
"""0020 producer/oracle contracts; offline tests never claim encrypted proof."""

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load("producer", "deploy/backup-snapshot.py")


def independent_projection():
    """Literal economic oracle, independent of seed/project implementations."""
    roots = [
        {
            "id": 1,
            "user_id": 1,
            "name": "Legacy",
            "description": "",
            "closed_at": None,
            "cash": "123.45000000",
            "starting_cash": "7777.00000000",
        }
    ]
    creations = []
    for index in range(11):
        root = {
            "id": index + 2,
            "user_id": 3,
            "name": "Renamed"
            if index == 0
            else "Reusable"
            if index < 3
            else "Strategy " + str(index - 1),
            "description": "changed\nmetadata"
            if index == 0
            else "original " + str(index - 1),
            "closed_at": "2026-01-01T00:00:00+00:00" if index == 1 else None,
            "cash": "10000.00000000",
            "starting_cash": "10000.00000000",
        }
        roots.append(root)
        creations.append(
            {
                "id": index + 1,
                "user_id": 3,
                "portfolio_id": index + 2,
                "creation_key": "00000000-0000-4000-8000-" + str(index + 1).zfill(12),
                "origin": "initial" if index == 0 else "explicit",
                "payload_version": 1,
                "amount": "10000.00000000",
                "canonical_payload": {
                    "name": "My portfolio" if index == 0 else root["name"],
                    "description": "" if index == 0 else root["description"],
                },
            }
        )
    return {
        "revision": "0020",
        "tables": {
            "users": [
                {"id": 1, "email": "legacy@example.test"},
                {"id": 2, "email": "empty@example.test"},
                {"id": 3, "email": "management@example.test"},
            ],
            "accounts": roots,
            "portfolio_creations": creations,
            "portfolio_initializations": [
                {
                    "id": 1,
                    "user_id": 1,
                    "origin": "legacy",
                    "portfolio_id": None,
                    "creation_id": None,
                },
                {
                    "id": 2,
                    "user_id": 2,
                    "origin": "legacy",
                    "portfolio_id": None,
                    "creation_id": None,
                },
                {
                    "id": 3,
                    "user_id": 3,
                    "origin": "initial",
                    "portfolio_id": 2,
                    "creation_id": 1,
                },
            ],
        },
        "sequences": {name: [12, True] for name in producer.identity_tables("0020")},
    }


def closure_postgres_proof(*, write_fixture=False):
    """Owned current producer/causal oracle proof, not encrypted/TLS restore."""
    labels = json.loads(subprocess.check_output(
        ['docker', 'inspect', 'birja-p14-05-postgres-1']))[0]['Config']['Labels']
    if labels.get('com.docker.compose.project') != 'birja-p14-05':
        raise ValueError('exclusive owned closure proof required')
    env = {'PATH':os.environ['PATH'], 'HOME':'/tmp', 'ENV':'test',
           'PRICE_SOURCE':'fake', 'EMAIL_BACKEND':'console',
           'UV_NO_SYNC':'1', 'UV_OFFLINE':'1',
           'CLOSURE_WRITE_FIXTURE':'1' if write_fixture else '0'}
    code = r'''
import asyncio,copy,importlib.util,json,os,secrets
from pathlib import Path
import tests.conftest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import ensure_dividend_test_owner,run_test_migration,test_migration_url
from app.core.config import Settings
from app.db.portfolio_bootstrap import PREFLIGHT_0023_SQL,GRANTS_0023_SQL
root=Path.cwd().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,root/path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
fixture=load('closure_fixture','deploy/tests/portfolio-closure-recovery-fixture.py')
producer=load('closure_producer','deploy/backup-snapshot.py')
async def sql(conn,statement):
 raw=await conn.get_raw_connection();await raw.driver_connection.execute(statement)
async def main():
 await ensure_dividend_test_owner()
 admin=create_async_engine(tests.conftest.TEST_DATABASE_URL)
 migrator=app=scheduler=None
 try:
  await reset_disposable_schema(admin)
  await asyncio.to_thread(run_test_migration,'0023')
  passwords={r:secrets.token_hex(32) for r in ('birja_app','birja_scheduler')}
  async with admin.begin() as conn:
   await sql(conn,PREFLIGHT_0023_SQL);await sql(conn,GRANTS_0023_SQL)
   for role,password in passwords.items():
    await sql(conn,"ALTER ROLE "+role+" LOGIN PASSWORD '"+password+"'")
  migrator=create_async_engine(test_migration_url())
  app=create_async_engine(make_url(tests.conftest.TEST_DATABASE_URL).set(username='birja_app',password=passwords['birja_app']))
  scheduler=create_async_engine(make_url(tests.conftest.TEST_DATABASE_URL).set(username='birja_scheduler',password=passwords['birja_scheduler']))
  factory=async_sessionmaker(migrator,expire_on_commit=False)
  helpers,_=fixture.historical_helpers()
  await fixture.seed(factory,Settings(),app,scheduler,helpers)
  async with factory() as db:
   value=await fixture.project(db);fixture.require_projection(value)
  async with admin.connect() as conn:
   await conn.execute(text("SET TIME ZONE 'UTC'"))
   manifest=(await conn.execute(text(producer.manifest_sql('0023')))).scalar_one()
   producer.validate_manifest(manifest)
   quarantine_tx=await conn.begin_nested()
   try:
    await sql(conn,'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator; REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator; REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator;')
    for table,columns in producer.contract_columns('0023').items():
     await sql(conn,'REVOKE ALL('+','.join(sorted(columns))+') ON public.'+table+' FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator')
    noacl=(await conn.execute(text(producer.manifest_sql('0023')))).scalar_one()
    producer.validate_manifest(noacl,quarantined=True)
   finally:await quarantine_tx.rollback()
   before=fixture.canonical(value)
   snapshot=Path('/tmp/birja-phase14-plan05/before-backup.json')
   if snapshot.exists():snapshot.unlink()
   digest=fixture.save_snapshot(snapshot,value)
   assert fixture.compare_snapshot(snapshot,digest,value)==digest
   for damage in ("ALTER ROLE birja_action_operator LOGIN",
      "GRANT EXECUTE ON FUNCTION check_stock_terminal_clock() TO PUBLIC",
      "ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator GRANT EXECUTE ON FUNCTIONS TO PUBLIC",
      "CREATE FUNCTION public.unreviewed_closure_helper() RETURNS int LANGUAGE sql AS 'SELECT 1'"):
    tx=await conn.begin_nested()
    try:
     await sql(conn,damage)
     actual=(await conn.execute(text(producer.manifest_sql('0023')))).scalar_one()
     try:producer.validate_manifest(actual)
     except ValueError:pass
     else:raise AssertionError('producer admitted altered authority')
    finally:await tx.rollback()
   for table in ('portfolio_lifecycle_closures','portfolio_closure_intents'):
    await sql(conn,'ALTER TABLE '+table+' DISABLE TRIGGER USER')
    await conn.execute(text("UPDATE "+table+" SET confirmation_name='Joint corruption' WHERE portfolio_id=(SELECT min(portfolio_id) FROM portfolio_lifecycle_closures)"))
    await sql(conn,'ALTER TABLE '+table+' ENABLE TRIGGER USER')
   corrupted=(await conn.execute(text(producer.manifest_sql('0023')))).scalar_one()
   try:producer.validate_manifest(corrupted)
   except ValueError:pass
   else:raise AssertionError('producer admitted corrupt terminal names')
   await conn.rollback()
  async with factory() as db:
   after=await fixture.project(db)
   assert fixture.canonical(after)==before
  if os.environ['CLOSURE_WRITE_FIXTURE']=='1':
   (root/'deploy/tests/fixtures/portfolio-recovery-0023.json').write_text(json.dumps({'format':3,'manifest':manifest,'quarantined':noacl,'projection':value},sort_keys=True,separators=(',',':'))+'\n')
  print(json.dumps({'manifest':manifest,'quarantined':noacl,'projection':value,'oracle_sha256':digest,'actual_postgres':True,'encrypted_restore':False},sort_keys=True))
 finally:
  for engine in (app,scheduler,migrator):
   if engine:await engine.dispose()
  await reset_disposable_schema(admin);await admin.dispose()
asyncio.run(main())
'''
    result = subprocess.run([str(ROOT/'backend/.venv/bin/python'), '-c', code],
                            cwd=ROOT/'backend',env=env,capture_output=True,text=True,timeout=300)
    if result.returncode:
        raise AssertionError(result.stderr[-7000:])
    return json.loads(result.stdout.splitlines()[-1])


def postgres_proof():
    """Owned synthetic logical producer proof; not encrypted/cold/TLS proof."""
    labels = json.loads(
        subprocess.check_output(["docker", "inspect", "birja-p13-04-postgres-1"])
    )[0]["Config"]["Labels"]
    if labels.get("com.docker.compose.project") != "birja-p13-04":
        raise ValueError("exclusive owned synthetic lane required")
    env = {
        "PATH": os.environ["PATH"],
        "HOME": "/tmp",
        "PYTHONPATH": str(ROOT / "backend"),
        "ENV": "test",
        "PRICE_SOURCE": "fake",
        "EMAIL_BACKEND": "console",
    }
    code = r"""
import asyncio,importlib.util,json,tempfile,subprocess,io,tarfile,types,copy
from unittest.mock import patch
import tests.conftest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from tests.portfolio_fixtures import reset_disposable_schema
from tests.test_migrations import run_test_migration,test_migration_url
from app.db.portfolio_bootstrap import GRANTS_SQL,PREFLIGHT_SQL
from pathlib import Path
root=Path.cwd().parent
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,root/path)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
fixture=load('fixture','deploy/tests/portfolio-management-recovery-fixture.py')
producer=load('producer','deploy/backup-snapshot.py')
async def sql(conn,statement):
 raw=await conn.get_raw_connection();await raw.driver_connection.execute(statement)
async def main():
 admin=create_async_engine(tests.conftest.TEST_DATABASE_URL)
 migrator=None
 try:
  await reset_disposable_schema(admin)
  await asyncio.to_thread(run_test_migration,'0014')
  migrator=create_async_engine(test_migration_url())
  async with migrator.begin() as conn:
   await conn.execute(text("INSERT INTO users(email) VALUES ('legacy@example.test'),('empty@example.test')"))
   await conn.execute(text("INSERT INTO accounts(user_id,cash,starting_cash) SELECT id,123.45,7777 FROM users WHERE email='legacy@example.test'"))
  await asyncio.to_thread(run_test_migration,'0017')
  async with migrator.begin() as conn:await conn.execute(text("UPDATE accounts SET name='Legacy'"))
  await asyncio.to_thread(run_test_migration,'0020')
  async with admin.begin() as conn:
   await sql(conn,PREFLIGHT_SQL);await sql(conn,GRANTS_SQL)
   await fixture.seed_management(conn)
  async with admin.connect() as conn:
   await conn.execute(text("SET TIME ZONE 'UTC'"))
   value=await fixture.project(conn);fixture.require_projection(value)
   manifest=(await conn.execute(text(producer.manifest_sql('0020')))).scalar_one()
   producer.validate_manifest(manifest)
   try:
    await conn.execute(text('ALTER ROLE birja_action_operator LOGIN'))
    assert (await conn.execute(text("SELECT rolcanlogin FROM pg_roles WHERE rolname='birja_action_operator'"))).scalar_one()
    unsafe=(await conn.execute(text(producer.manifest_sql('0020')))).scalar_one()
    try:producer.validate_manifest(unsafe)
    except ValueError:pass
    else:raise AssertionError('LOGIN-enabled action operator admitted by actual0020 producer')
   finally:
    await conn.rollback()
    await conn.execute(text('ALTER ROLE birja_action_operator NOLOGIN'))
    await conn.commit()
   assert not (await conn.execute(text("SELECT rolcanlogin FROM pg_roles WHERE rolname='birja_action_operator'"))).scalar_one()
   await conn.rollback()
   quarantine='REVOKE EXECUTE ON FUNCTION public.create_portfolio(bigint,uuid,text,text),public.initialize_portfolio(bigint),public.update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean) FROM birja_app; REVOKE EXECUTE ON FUNCTION public.apply_stock_dividend(bigint,bigint,text,text),public.record_stock_dividend_hold(bigint,text),public.lock_stock_portfolio_roots(bigint) FROM birja_scheduler;'
   await sql(conn,quarantine)
   quarantined=(await conn.execute(text(producer.manifest_sql('0020')))).scalar_one()
   await conn.rollback()
   await sql(conn,'REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator; REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator; REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator; GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO PUBLIC;')
   for name,columns in producer.contract_columns('0020').items():
    await sql(conn,'REVOKE ALL('+','.join(sorted(columns))+') ON public.'+name+' FROM PUBLIC,birja_app,birja_scheduler,birja_action_operator')
   noacl=(await conn.execute(text(producer.manifest_sql('0020')))).scalar_one()
   await conn.rollback()
   await conn.execute(text("ALTER ROLE birja_app LOGIN PASSWORD 'synthetic-p13-04-app-only'"));await conn.commit()
  app=create_async_engine(make_url(tests.conftest.TEST_DATABASE_URL).set(username='birja_app',password='synthetic-p13-04-app-only'))
  try:
   async with app.connect() as conn:
    assert (await conn.execute(text('SELECT session_user'))).scalar_one()=='birja_app'
    initial=next(r for r in value['tables']['portfolio_creations'] if r['origin']=='initial')
    replay=(await conn.execute(text("SELECT * FROM create_portfolio(:u,:k,'My portfolio','')"),{'u':initial['user_id'],'k':initial['creation_key']})).one()
    assert replay.replayed and replay.portfolio_id==initial['portfolio_id']
    await conn.rollback()
    closed=next(r for r in value['tables']['accounts'] if r['closed_at'])
    original=next(r for r in value['tables']['portfolio_creations'] if r['portfolio_id']==closed['id'])
    for name,description,message in [(original['canonical_payload']['name'],original['canonical_payload']['description'],'portfolio_unavailable'),('changed','changed','creation_key_conflict')]:
     try:await conn.execute(text('SELECT * FROM create_portfolio(:u,:k,:n,:d)'),{'u':original['user_id'],'k':original['creation_key'],'n':name,'d':description})
     except DBAPIError as error:
      assert message in str(error.orig);await conn.rollback()
     else:raise AssertionError('closed/conflicting creation replay admitted')
  finally:await app.dispose()
  # Exact old schema consumer from the authenticated complete release, using
  # an actual DB connection, must refuse0020 after its sole read and no writes.
  sources=load('sources','deploy/tests/portfolio-sources.py')
  payload=sources.source_archive('portfolio0017')
  with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
   old=archive.extractfile('backend/app/db/schema_contract.py').read()
  retained=types.ModuleType('immutable_schema0017');exec(compile(old,'<authenticated0017-schema>','exec'),retained.__dict__)
  async with admin.connect() as conn:
   try:await retained.require_schema(conn)
   except retained.SchemaAdmissionError as error:assert error.reason=='incompatible_schema'
   else:raise AssertionError('actual old source admitted0020')
  try:await asyncio.to_thread(run_test_migration,'0019',down=True)
  except Exception as error:assert 'downgrade refused before writes' in str(error)
  else:raise AssertionError('populated downgrade succeeded')
  recovery=load('consumer','deploy/verify-restore.py');recovery.BOOT='birja_test'
  for damage in ('journal','latch','sequence','schema','helper','acl','source','unsafe'):
   changed=copy.deepcopy(noacl)
   if damage=='journal':changed['tables'].pop('portfolio_creations')
   elif damage=='latch':changed['management_state']['initializations']-=1
   elif damage=='sequence':changed['identity_state'].pop()
   elif damage=='schema':changed['schema']['constraints'].pop()
   elif damage=='helper':changed['portfolio_authority']['functions'].pop()
   elif damage=='acl':changed['management_contract']['acl']='0'*64
   elif damage=='source':changed['management_contract']['catalogue']='0'*64
   else:changed['management_contract']['unsafe']=1
   with patch.object(recovery,'canonical',return_value=changed),patch.object(recovery,'sql',side_effect=AssertionError('pregrant write')) as write:
    try:recovery.restore_management_authority([])
    except ValueError:pass
    else:raise AssertionError('damaged noACL state admitted: '+damage)
    write.assert_not_called()
  dc=['docker','compose','--env-file','/dev/null','-p','birja-p13-04','-f',str(root/'docker-compose.test.yml')]
  dump=recovery.call(dc+['exec','-T','postgres','pg_dump','-U','birja_migrator','-d','birja_test','--format=custom','--no-owner','--no-acl'])
  recovery.call(dc+['exec','-T','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-U','birja_test','-d','birja_test'],b'CREATE DATABASE birja_ops_test;')
  try:
   with recovery.restored(dc,dump):
    recovery.verify(dc,manifest)
    restored_engine=create_async_engine(make_url(tests.conftest.TEST_DATABASE_URL).set(database='birja_restore_test'))
    try:
     async with restored_engine.connect() as conn:
      await conn.execute(text("SET TIME ZONE 'UTC'"))
      clone=await fixture.project(conn)
      with tempfile.TemporaryDirectory(prefix='birja-restored-oracle-') as tmp:
       path=Path(tmp)/'before.json';digest=fixture.save_snapshot(path,value)
       fixture.compare_snapshot(path,digest,clone)
      for role,signature in [('birja_app','create_portfolio(bigint,uuid,text,text)'),('birja_app','initialize_portfolio(bigint)'),('birja_app','update_portfolio_metadata(bigint,bigint,text,text,boolean,boolean)'),('birja_scheduler','apply_stock_dividend(bigint,bigint,text,text)'),('birja_scheduler','record_stock_dividend_hold(bigint,text)'),('birja_scheduler','lock_stock_portfolio_roots(bigint)')]:
       assert not (await conn.execute(text("SELECT has_function_privilege(:r,:f,'EXECUTE')"),{'r':role,'f':signature})).scalar_one()
      assert not (await conn.execute(text("SELECT has_table_privilege('birja_app','accounts','INSERT')"))).scalar_one()
      assert not (await conn.execute(text("SELECT has_column_privilege('birja_app','accounts','description','UPDATE')"))).scalar_one()
    finally:await restored_engine.dispose()
  finally:recovery.call(dc+['exec','-T','postgres','psql','-XqAt','-v','ON_ERROR_STOP=1','-U','birja_test','-d','birja_test'],b'DROP DATABASE birja_ops_test;')
  async with admin.connect() as conn:
   after=await fixture.project(conn)
   with tempfile.TemporaryDirectory(prefix='birja-management-live-oracle-') as tmp:
    path=Path(tmp)/'before.json';digest=fixture.save_snapshot(path,value)
    assert fixture.compare_snapshot(path,digest,after)==digest
   print(json.dumps({'manifest':manifest,'projection':value,'quarantined':quarantined,'noacl':noacl,'restored':True},sort_keys=True))
  # Independent fresh source lane, without substituting a retained bootstrap.
  await reset_disposable_schema(admin)
  await asyncio.to_thread(run_test_migration,'0020')
  async with admin.begin() as conn:
   await sql(conn,PREFLIGHT_SQL);await sql(conn,GRANTS_SQL)
   fresh=(await conn.execute(text(producer.manifest_sql('0020')))).scalar_one()
   producer.validate_manifest(fresh)
   assert fresh['tables']['portfolio_creations']['count']==fresh['tables']['portfolio_initializations']['count']==0
 finally:
  if migrator:await migrator.dispose()
  await reset_disposable_schema(admin);await admin.dispose()
asyncio.run(main())
"""
    result = subprocess.run(
        [str(ROOT / "backend/.venv/bin/python"), "-c", code],
        cwd=ROOT / "backend",
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr[-5000:])
    return json.loads(result.stdout.splitlines()[-1])


class ManagementRecoveryContracts(unittest.TestCase):
    def test_consumer_version_dispatch_and_exact_management_equality(self):
        recovery = load("consumer", "deploy/verify-restore.py")
        inventory = producer.portfolio_payload_inventory(ROOT)
        hashes = inventory["sha256"]
        recovery.verify_portfolio_inventory({"portfolio_payload": inventory}, hashes)
        for version in (True, 0, 3, "2"):
            damaged = copy.deepcopy(inventory)
            damaged["version"] = version
            with self.assertRaises(ValueError):
                recovery.verify_portfolio_inventory(
                    {"portfolio_payload": damaged}, hashes
                )
        expected = json.loads(
            (ROOT / "deploy/tests/fixtures/portfolio-recovery-0020.json").read_text()
        )
        with (
            mock.patch.object(recovery, "canonical", return_value=expected),
            mock.patch.object(recovery, "sql", return_value=b"t"),
        ):
            recovery.verify([], expected, quarantined=False)
            for section in ("tables", "identity_state", "management_state"):
                damaged = copy.deepcopy(expected)
                if section == "tables":
                    damaged[section]["accounts"]["sha256"] = "0" * 64
                elif section == "identity_state":
                    damaged[section][0][1] += 1
                else:
                    damaged[section]["initializations"] -= 1
                with (
                    self.subTest(section=section),
                    mock.patch.object(recovery, "canonical", return_value=damaged),
                    self.assertRaises(ValueError),
                ):
                    recovery.verify([], expected, quarantined=False)

    def test_consumer_source_authentication_before_sql_or_import(self):
        recovery = load("consumer_source", "deploy/verify-restore.py")
        recovery.management_source()
        with tempfile.TemporaryDirectory(prefix="birja-consumer-source-") as tmp:
            root = Path(tmp)
            for name in recovery.MANAGEMENT_SOURCE_SHA256:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / "backend" / name).read_bytes())
            recovery.management_source(root)
            for name in recovery.MANAGEMENT_SOURCE_SHA256:
                path = root / name
                original = path.read_bytes()
                path.write_bytes(original + b"\nraise RuntimeError('must not import')")
                with self.subTest(source=name), self.assertRaises(ValueError):
                    recovery.management_source(root)
                path.write_bytes(original)

    def test_v2_package_assembles_exact_current_and_retained_bytes(self):
        recovery = load("assembly_recovery", "deploy/verify-restore.py")
        original_run = subprocess.run

        def external(argv, **kwargs):
            if argv[:3] == ["docker", "image", "save"]:
                kwargs["stdout"].write(b"synthetic-image-transport")
                return subprocess.CompletedProcess(argv, 0)
            return original_run(argv, **kwargs)

        def saved(stream, index, manifest):
            self.assertEqual(stream.read(), b"synthetic-image-transport")
            self.assertEqual((index, manifest), (b"index", b"manifest"))

        with (
            tempfile.TemporaryDirectory(prefix="birja-backup-test-p13-package-") as tmp,
            mock.patch.object(recovery, "runtime", return_value={"synthetic": True}),
            mock.patch.object(recovery, "image_inspect"),
            mock.patch.object(
                recovery, "registry_manifests", return_value=(b"index", b"manifest")
            ),
            mock.patch.object(recovery, "verify_saved_image", side_effect=saved),
            mock.patch.object(subprocess, "run", side_effect=external),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            output = Path(tmp) / "recovery.tar"
            producer.bundle_package_v2(output, recovery=recovery)
            recovery.bundle_verify(
                output, recovery.digest(output), required_profile="deploy-recovery-v3"
            )
            with tarfile.open(output, "r:") as archive:
                names = recovery.tar_members(archive)
                inventory = json.load(archive.extractfile("INVENTORY.json"))
                self.assertEqual(inventory["portfolio_payload"]["version"], 2)
                self.assertEqual(inventory["portfolio_payload"]["revision"], "0020")
                self.assertEqual(inventory["schema_contract"]["revisions"][-1], "0020")
                self.assertEqual(
                    set(inventory["files"]), names - {"INVENTORY.json", "SHA256SUMS"}
                )
                for line in (
                    archive.extractfile("SHA256SUMS").read().decode().splitlines()
                ):
                    expected, name = line.split("  ")
                    self.assertEqual(
                        hashlib.sha256(archive.extractfile(name).read()).hexdigest(),
                        expected,
                    )
                retained = archive.extractfile("sources/portfolio0017.tar").read()
                self.assertEqual(
                    hashlib.sha256(retained).hexdigest(),
                    "361a0fafbb6f1645d7beb9caeadb8bd46c85abc739d957dce7fc439b64eba248",
                )
                for name, digest in inventory["portfolio_payload"]["sha256"].items():
                    self.assertEqual(
                        hashlib.sha256(archive.extractfile(name).read()).hexdigest(),
                        digest,
                    )
                members = {
                    m.name: archive.extractfile(m).read()
                    for m in archive.getmembers()
                    if m.isfile()
                }
            for missing in (
                *recovery.CORE,
                *recovery.UNITS,
                "images/postgres.tar",
                "sources/portfolio0017.tar",
            ):
                damaged = Path(tmp) / "damaged.tar"
                with tarfile.open(damaged, "w:") as archive:
                    for name, data in members.items():
                        if name == missing:
                            continue
                        member = tarfile.TarInfo(name)
                        member.size = len(data)
                        archive.addfile(member, io.BytesIO(data))
                damaged.chmod(0o600)
                with self.subTest(missing=missing), self.assertRaises(ValueError):
                    recovery.bundle_verify(damaged, recovery.digest(damaged))

            def coherent_archive(name, metadata, content):
                """Rewrite every affected checksum; never rely on stale hashes."""
                content = dict(content)
                content.pop("SHA256SUMS", None)
                metadata["files"] = sorted(set(content) - {"INVENTORY.json"})
                content["INVENTORY.json"] = json.dumps(
                    metadata, sort_keys=True
                ).encode()
                content["SHA256SUMS"] = "".join(
                    hashlib.sha256(data).hexdigest() + "  " + path + "\n"
                    for path, data in sorted(content.items())
                ).encode()
                path = Path(tmp) / name
                with tarfile.open(path, "w:") as archive:
                    for member_name, data in content.items():
                        member = tarfile.TarInfo(member_name)
                        member.size = len(data)
                        archive.addfile(member, io.BytesIO(data))
                path.chmod(0o600)
                return path

            for omissions in (
                ("retained_source_payloads",),
                ("schema_contract",),
                ("retained_source_payloads", "schema_contract"),
            ):
                metadata = copy.deepcopy(inventory)
                content = dict(members)
                for field in omissions:
                    del metadata[field]
                if "retained_source_payloads" in omissions:
                    content = {
                        name: data
                        for name, data in content.items()
                        if not name.startswith("sources/")
                    }
                damaged = coherent_archive(
                    "coherent-" + "-".join(omissions) + ".tar", metadata, content
                )
                with (
                    self.subTest(coherent_omissions=omissions),
                    mock.patch.object(recovery, "runtime") as runtime,
                    mock.patch.object(recovery, "verify_saved_image") as image,
                ):
                    with self.assertRaises(ValueError):
                        recovery.bundle_verify(
                            damaged,
                            recovery.digest(damaged),
                            required_profile="deploy-recovery-v3",
                        )
                    runtime.assert_not_called()
                    image.assert_not_called()

            # Real fixed-release V1 source bytes, with coherent V1 inventories.
            # Legacy absence semantics remain valid for each optional field.
            with tarfile.open(
                fileobj=io.BytesIO(members["sources/portfolio0017.tar"])
            ) as retained:
                original = {
                    m.name: retained.extractfile(m).read()
                    for m in retained.getmembers()
                    if m.isfile()
                }
            for omissions in (
                (),
                ("retained_source_payloads",),
                ("schema_contract",),
                ("retained_source_payloads", "schema_contract"),
            ):
                metadata = copy.deepcopy(inventory)
                content = {
                    name: data
                    for name, data in members.items()
                    if name
                    not in set(recovery.PORTFOLIO_PAYLOAD_V2)
                    - set(recovery.PORTFOLIO_PAYLOAD_V1)
                    and name != "sources/portfolio0017.tar"
                }
                for name in (
                    *recovery.CORE,
                    *recovery.UNITS,
                    *recovery.PORTFOLIO_PAYLOAD_V1,
                ):
                    content[name] = original[name]
                metadata["portfolio_payload"] = {
                    "version": 1,
                    "sha256": {
                        name: hashlib.sha256(content[name]).hexdigest()
                        for name in recovery.PORTFOLIO_PAYLOAD_V1
                    },
                }
                metadata["recovery_profile"] = "deploy-recovery-v2"
                metadata["retained_source_payloads"] = dict(
                    recovery.RETAINED_SOURCE_PAYLOADS
                )
                metadata["schema_contract"] = {
                    "revisions": [
                        r for r in producer.SUPPORTED_REVISIONS if r != "0020"
                    ],
                    "payload_sha256": {
                        name: hashlib.sha256(content[name]).hexdigest()
                        for name in recovery.CONTRACT_PAYLOAD
                    },
                }
                for field in omissions:
                    del metadata[field]
                if "retained_source_payloads" in omissions:
                    content = {
                        name: data
                        for name, data in content.items()
                        if not name.startswith("sources/")
                    }
                control = coherent_archive(
                    "v1-" + "-".join(omissions) + ".tar", metadata, content
                )
                with self.subTest(v1_optional_omissions=omissions):
                    recovery.bundle_verify(
                        control,
                        recovery.digest(control),
                        required_profile="deploy-recovery-v2",
                    )
            with self.assertRaises(ValueError):
                producer.bundle_package_v2(output, recovery=recovery)

    def test_before_backup_oracle_preserves_every_retry_and_economic_byte(self):
        fixture = load(
            "management_fixture",
            "deploy/tests/portfolio-management-recovery-fixture.py",
        )
        value = independent_projection()
        for name in fixture.TABLE_NAMES:
            value["tables"].setdefault(name, [])
        fixture.require_projection(value)
        with tempfile.TemporaryDirectory(prefix="birja-management-oracle-") as tmp:
            path = Path(tmp) / "before.json"
            digest = fixture.save_snapshot(path, value)
            original = path.read_bytes()
            self.assertEqual(
                fixture.compare_snapshot(path, digest, copy.deepcopy(value)), digest
            )
            mutations = [
                lambda v: v["tables"]["portfolio_initializations"].pop(1),
                lambda v: v["tables"]["portfolio_creations"][0].__setitem__(
                    "user_id", 1
                ),
                lambda v: v["tables"]["portfolio_creations"][0][
                    "canonical_payload"
                ].__setitem__("name", "Renamed"),
                lambda v: v["tables"]["portfolio_creations"][1].__setitem__(
                    "creation_key", "changed"
                ),
                lambda v: v["tables"]["portfolio_creations"][1].__setitem__(
                    "portfolio_id", 4
                ),
                lambda v: v["tables"]["accounts"][0].__setitem__(
                    "starting_cash", "10000.00000000"
                ),
                lambda v: v["tables"]["accounts"][2].__setitem__("closed_at", None),
                lambda v: v["sequences"]["portfolio_creations"].__setitem__(0, 99),
                lambda v: v["sequences"].pop("portfolio_initializations"),
            ]
            for mutate in mutations:
                damaged = copy.deepcopy(value)
                mutate(damaged)
                with self.assertRaises(ValueError):
                    fixture.compare_snapshot(path, digest, damaged)
                self.assertEqual(path.read_bytes(), original)
            with self.assertRaises(ValueError):
                fixture.save_snapshot(path, value)
            with self.assertRaises(ValueError):
                fixture.compare_snapshot(path, "0" * 64, value)

    def test_current_source_and_revision_authentication_precede_import(self):
        fixture = load(
            "management_fixture",
            "deploy/tests/portfolio-management-recovery-fixture.py",
        )
        fixture.require_source(ROOT / "backend")
        with tempfile.TemporaryDirectory(prefix="birja-management-source-") as tmp:
            root = Path(tmp)
            for name in fixture.SOURCE_SHA256:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / "backend" / name).read_bytes())
            fixture.require_source(root)
            for name in fixture.SOURCE_SHA256:
                path = root / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n# drift")
                with self.subTest(source=name), self.assertRaises(ValueError):
                    fixture.require_source(root)
                path.write_bytes(original)
        code = fixture.program(mode="verify")
        self.assertLess(
            code.index("0020 source mismatch before import"),
            code.index("from sqlalchemy"),
        )
        self.assertLess(
            code.index("0020 schema required before import"),
            code.index("from sqlalchemy"),
        )
        compile(code, "<0020-source-bound-program>", "exec")
        for mode, database in [
            ("create", "birja_restore_test"),
            ("verify", "production"),
            ("projection", "../birja"),
        ]:
            with self.assertRaises(ValueError):
                fixture.program(mode=mode, database=database)

    def test_versioned_exact_inventory_preserves_0017(self):
        self.assertIn("0020", producer.SUPPORTED_REVISIONS)
        v2 = producer.PORTFOLIO_PAYLOAD_V2
        for name in (
            "backend/app/models/portfolio_creation.py",
            "backend/alembic/sql/0020_portfolio_management.sql",
            "backend/alembic/sql/0019_portfolio_metadata.sql",
            "deploy/tests/portfolio-management-recovery-fixture.py",
        ):
            self.assertIn(name, v2)
        self.assertEqual(len(v2), len(set(v2)))
        self.assertEqual(len(producer.contract_columns("0017")), 27)
        self.assertEqual(len(producer.identity_tables("0017")), 20)
        self.assertEqual(len(producer.contract_columns("0020")), 29)
        self.assertEqual(len(producer.identity_tables("0020")), 22)
        for revision in ("0018", "0019", "0021", "head"):
            with self.assertRaises(ValueError):
                producer.manifest_sql(revision)

    def test_exact_populated_manifest_and_mutations(self):
        value = json.loads(
            (ROOT / "deploy/tests/fixtures/portfolio-recovery-0020.json").read_text()
        )
        producer.validate_manifest(value)
        self.assertEqual(value["management_state"]["initializations"], 3)
        self.assertEqual(value["management_state"]["creations"], 11)
        self.assertEqual(value["portfolio_state"]["active"], 11)
        self.assertEqual(value["portfolio_state"]["closed"], 1)
        mutations = [
            lambda m: m["schema"]["constraints"].pop(),
            lambda m: m["portfolio_authority"]["functions"].pop(),
            lambda m: m["management_state"].__setitem__("invalid", 1),
            lambda m: m["identity_state"].pop(),
            lambda m: m["tables"].pop("portfolio_creations"),
            lambda m: m["management_state"].__setitem__("initializations", 2),
            lambda m: m["management_contract"].__setitem__("unsafe", 1),
        ]
        for mutate in mutations:
            damaged = copy.deepcopy(value)
            mutate(damaged)
            with self.assertRaises(ValueError):
                producer.validate_manifest(damaged)

    def test_source_inventory_tampering_is_rejected(self):
        inventory = producer.portfolio_payload_inventory(ROOT)
        producer.validate_payload_inventory(inventory, ROOT)
        for field, replacement in (("version", 1), ("revision", "0017")):
            changed = copy.deepcopy(inventory)
            changed[field] = replacement
            with self.assertRaises(ValueError):
                producer.validate_payload_inventory(changed, ROOT)
        for name in inventory["sha256"]:
            changed = copy.deepcopy(inventory)
            changed["sha256"][name] = "0" * 64
            with self.subTest(name=name), self.assertRaises(ValueError):
                producer.validate_payload_inventory(changed, ROOT)


if __name__ == "__main__":
    if sys.argv[1:] in (["--postgres"], ["--postgres-operator-login"]):
        result = postgres_proof()
        producer.validate_manifest(result["manifest"])
        producer.validate_manifest(result["quarantined"], quarantined=True)
        assert (
            producer.canonical_hash(result["noacl"]["schema"])
            == producer.MANAGEMENT_SCHEMA_SHA256
        )
        assert (
            producer.canonical_hash(result["noacl"]["portfolio_authority"])
            == producer.MANAGEMENT_NO_ACL_SHA256
        )
        assert (
            result["noacl"]["management_contract"]["acl"]
            == producer.MANAGEMENT_NO_ACL_PRIVILEGES_SHA256
        )
        print("0020 logical producer and independent populated oracle passed")
    else:
        unittest.main()
