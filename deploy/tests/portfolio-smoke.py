#!/usr/bin/env python3
"""Owned current0023 and complete immutable0020/0017 verified-TLS smoke."""

import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "birja-portfolio-fixture-test"
PG = "cgr.dev/chainguard/postgres@sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de"


def load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), Path(__file__).with_name(name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def campaign_image_binding(sources, env, *, archive, archive_sha, revision,
                           source_commit, app_tree, context_sha256, run):
    """Reuse only this archive's first-use immutable image, never a mutable tag.

    Missing or altered recorded images are an integrity failure. Rebuilding an
    equivalent filesystem can change its OCI index ID and invalidate another
    stage's authenticated identity, so that is deliberately not a fallback.
    """
    if archive is None:
        return None
    archive = Path(archive)
    parent = archive.parent
    if (parent.is_symlink() or not parent.is_dir()
            or parent.stat().st_uid != os.getuid() or parent.stat().st_mode & 0o077):
        raise ValueError("private campaign image directory required")
    sources.verify_archive_binding(archive, archive_sha)
    if archive.stat().st_uid != os.getuid() or archive.stat().st_mode & 0o077:
        raise ValueError("private campaign archive required")
    record = parent / ("current" + revision + "-image-binding.json")
    if record.is_symlink():
        raise ValueError("private campaign image record required")
    if not record.exists():
        return None
    if (not record.is_file() or record.stat().st_uid != os.getuid()
            or record.stat().st_mode & 0o077):
        raise ValueError("private campaign image record required")
    binding = json.loads(record.read_text())
    if (not isinstance(binding, dict)
            or binding.get("source_commit") != source_commit
            or binding.get("app_tree") != app_tree
            or binding.get("context_sha256") != context_sha256
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(binding.get("id")))):
        raise ValueError("campaign image source binding mismatch")
    result = run(["docker", "image", "inspect", binding["id"]],
                 env=env, capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError("recorded campaign immutable image missing")
    sources.verify_image(binding, json.loads(result.stdout))
    sources.verify_archive_binding(archive, archive_sha)
    if json.loads(record.read_text()) != binding:
        raise ValueError("campaign image binding replaced during reuse")
    return binding


def campaign_image_tag(tag, archive):
    if archive is None:
        return tag
    parent = Path(archive).parent.resolve(strict=True)
    identity = parent.stat()
    namespace = hashlib.sha256(
        os.fsencode(str(parent)) + f":{identity.st_dev}:{identity.st_ino}".encode()
    ).hexdigest()[:16]
    return tag + "-" + namespace


def authenticate_campaign_images(archive, archive_sha, *, inspect_image=None):
    """Recheck exact content IDs AND this private campaign's mutable aliases.

    A missing alias/ID is refusal, never a reason to rebuild or retag an image.
    The archived source builders still authenticate complete contexts before use.
    """
    sources = load("portfolio-sources")
    sources.verify_archive_binding(archive, archive_sha)
    if Path(archive).stat().st_uid != os.getuid() or Path(archive).stat().st_mode & 0o077:
        raise ValueError("private campaign archive required")
    directory = Path(archive).parent
    if directory.is_symlink() or directory.stat().st_uid != os.getuid() or directory.stat().st_mode & 0o077:
        raise ValueError("private campaign image directory required")
    if inspect_image is None:
        def inspect_image(ref):
            return json.loads(subprocess.check_output(["docker", "image", "inspect", ref],
                env={key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ}, timeout=30))
    namespace = campaign_image_tag("", archive)
    for record in directory.glob("*-image-binding.json"):
        if record.is_symlink() or record.stat().st_uid != os.getuid() or record.stat().st_mode & 0o077:
            raise ValueError("private campaign image record required")
        binding = json.loads(record.read_text())
        lane = record.name.removesuffix("-image-binding.json")
        if lane in {"current0023", "current0020", "current0017", "retained0020-refusal", "retained0017-refusal"}:
            prefix = "birja-portfolio-current:" if lane == "current0023" else "birja-portfolio-retained:"
            alias = campaign_image_tag(prefix + binding["source_commit"][:12] + "-" + binding["context_sha256"][:20], archive)
        elif lane in sources.FIXED_RELEASES:
            alias = "birja-retained-portfolio:" + binding["source_commit"][:12] + "-" + archive_sha[:16] + namespace
        else:
            raise ValueError("unrecognized campaign image lane")
        sources.verify_image(binding, inspect_image(binding["id"]))
        sources.verify_image(binding, inspect_image(alias))
    sources.verify_archive_binding(archive, archive_sha)


def build_current_runtime(sources, env, *, archive=None, archive_sha=None, run=subprocess.run):
    """Build the actual declared runtime from one authenticated Git context.

    A fresh CI runner must be able to create this image without any previous
    workstation image. Only the committed backend tree is sent to Docker;
    neither host source overlays nor an alternate dependency base are used.
    """
    commit = sources.git("rev-parse", "HEAD").decode().strip()
    if sources.git("diff", "--name-only", "HEAD", "--", "backend").strip():
        raise ValueError("current source must be frozen before image build")
    app_tree = sources.git("rev-parse", commit + ":backend/app").decode().strip()
    payload = sources.git("archive", commit, "backend")
    context = hashlib.sha256(payload).hexdigest()
    binding = campaign_image_binding(
        sources, env, archive=archive, archive_sha=archive_sha, revision="0023",
        source_commit=commit, app_tree=app_tree, context_sha256=context, run=run,
    )
    if binding is not None:
        if (sources.git("rev-parse", "HEAD").decode().strip() != commit
                or sources.git("diff", "--name-only", "HEAD", "--", "backend").strip()):
            raise ValueError("current source changed during image reuse")
        return binding
    tag = campaign_image_tag("birja-portfolio-current:" + commit[:12] + "-" + context[:20], archive)
    with tempfile.TemporaryDirectory(
        prefix="birja-portfolio-current-image-"
    ) as image_tmp:
        image_root = Path(image_tmp)
        with tarfile.open(fileobj=io.BytesIO(payload)) as source_tar:
            source_tar.extractall(image_root, filter="data")
        sources.verify_source_tree(image_root, payload)
        result = run(
            [
                "docker",
                "build",
                "--target",
                "runtime",
                "--label",
                "org.opencontainers.image.revision=" + commit,
                "-t",
                tag,
                str(image_root / "backend"),
            ],
            env=env,
            capture_output=True,
            timeout=600,
        )
        if result.returncode:
            raise AssertionError(
                "declared runtime image build failed: " + result.stderr.decode()[-1200:]
            )
        sources.verify_source_tree(image_root, payload)
    if (
        sources.git("rev-parse", "HEAD").decode().strip() != commit
        or sources.git("diff", "--name-only", "HEAD", "--", "backend").strip()
    ):
        raise ValueError("current source changed during image build")
    result = run(
        ["docker", "image", "inspect", tag], env=env, capture_output=True, timeout=30
    )
    if result.returncode:
        raise AssertionError("declared runtime image inspection failed")
    binding = sources.image_binding(
        json.loads(result.stdout),
        source_commit=commit,
        app_tree=app_tree,
        context_sha256=context,
    )
    result = run(
        ["docker", "image", "inspect", binding["id"]],
        env=env,
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise AssertionError("declared runtime immutable image missing")
    sources.verify_image(binding, json.loads(result.stdout))
    if archive is not None:
        sources.verify_archive_binding(archive, archive_sha)
        sources.record_image_binding(archive, "current0023", binding)
    return binding


def build_selected_runtime(
    sources, env, *, revision, archive=None, archive_sha=None, run=subprocess.run
):
    profile = sources.profile_for(revision)
    if revision == "0023":
        return build_current_runtime(sources, env, archive=archive, archive_sha=archive_sha, run=run)
    if revision not in {"0017", "0020"}:
        raise ValueError("unsupported portfolio smoke schema")
    payload = sources.source_archive(
        "portfolio" + revision, archive=archive, archive_sha=archive_sha
    )
    context = hashlib.sha256(payload).hexdigest()
    binding = campaign_image_binding(
        sources, env, archive=archive, archive_sha=archive_sha, revision=revision,
        source_commit=profile["commit"], app_tree=profile["app_tree"],
        context_sha256=context, run=run,
    )
    if binding is not None:
        return binding
    tag = campaign_image_tag("birja-portfolio-retained:" + profile["commit"][:12] + "-" + context[:20], archive)
    with tempfile.TemporaryDirectory(prefix="birja-portfolio-retained-image-") as tmp:
        root = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(payload)) as source:
            source.extractall(root, filter="data")
        sources.verify_source_tree(root, payload)
        result = run(
            [
                "docker",
                "build",
                "--target",
                "runtime",
                "--label",
                "org.opencontainers.image.revision=" + profile["commit"],
                "-t",
                tag,
                str(root / "backend"),
            ],
            env=env,
            capture_output=True,
            timeout=600,
        )
        if result.returncode:
            raise AssertionError("retained runtime image build failed")
        sources.verify_source_tree(root, payload)
    result = run(
        ["docker", "image", "inspect", tag], env=env, capture_output=True, timeout=30
    )
    if result.returncode:
        raise ValueError("retained runtime image missing")
    binding = sources.image_binding(
        json.loads(result.stdout),
        source_commit=profile["commit"],
        app_tree=profile["app_tree"],
        context_sha256=context,
    )
    result = run(
        ["docker", "image", "inspect", binding["id"]],
        env=env,
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise ValueError("retained immutable image missing")
    sources.verify_image(binding, json.loads(result.stdout))
    if archive is not None:
        sources.verify_archive_binding(archive, archive_sha)
        sources.record_image_binding(archive, "current" + revision, binding)
    return binding


def selected_fixture(sources, revision, *, archive=None, archive_sha=None):
    sources.profile_for(revision)
    if revision == "0023":
        return load("portfolio-closure-recovery-fixture")
    if revision not in {"0017", "0020"}:
        raise ValueError("unsupported portfolio fixture schema")
    payload = sources.source_archive(
        "portfolio" + revision, archive=archive, archive_sha=archive_sha
    )
    name = "portfolio-management-recovery-fixture.py" if revision == "0020" else "portfolio-execution-fixture.py"
    # The0020 generator imports its producer at generation time. Its complete
    # authenticated source tree must remain present, never the current overlay.
    directory = tempfile.TemporaryDirectory(prefix="birja-retained-smoke-" + revision + "-")
    with tarfile.open(fileobj=io.BytesIO(payload)) as source:
        source.extractall(directory.name, filter="data")
    sources.verify_source_tree(directory.name, payload)
    path = Path(directory.name) / "deploy/tests" / name
    fixture = types.ModuleType("immutable_portfolio" + revision + "_fixture")
    fixture.__file__ = str(path)
    fixture._source_directory = directory
    exec(compile(path.read_bytes(), str(path), "exec"), fixture.__dict__)  # noqa: S102 - fixed archive hash authenticated before imports
    return fixture


def admitted_program(code, revision, *, prepared_legacy14=False):
    """Read exact schema through verified TLS before application imports."""
    if revision not in ("0017", "0020", "0023"):
        raise ValueError("unsupported smoke source/schema")
    create = bool(re.search(r"^MODE\s*=\s*['\"]create['\"]", code, re.MULTILINE))
    if prepared_legacy14 and (revision != "0023" or not create
            or not code.startswith("UPGRADED=True\nUPGRADED_FROM='0014'\n")):
        raise ValueError("explicit current legacy14 diagnostic required")
    prelude = (
        "SMOKE_REVISION=" + repr(revision) + "\nSMOKE_CREATE=" + repr(create) + "\n"
        + "SMOKE_LEGACY14=" + repr(prepared_legacy14) + "\n"
    )
    prelude += r"""
import asyncio,asyncpg,os,ssl
from urllib.parse import urlsplit,urlunsplit
async def smoke_admit():
 parts=urlsplit(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://'))
 if parts.hostname!='postgres' or parts.port!=5432 or parts.username!='birja_migrator' or parts.path!='/birja_source_test' or parts.query:
  raise ValueError('owned smoke identity required before import')
 if "DATABASE='birja_restore_test'" in SMOKE_BODY:parts=parts._replace(path='/birja_restore_test')
 conn=await asyncpg.connect(urlunsplit(parts),ssl=ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE']))
 try:
  if SMOKE_LEGACY14:
   if await conn.fetchval('SELECT version_num FROM alembic_version')!='0014':
    raise ValueError('prepared legacy14 schema required before import')
  elif SMOKE_CREATE:
   if await conn.fetchval("SELECT count(*) FROM pg_tables WHERE schemaname='public'"):
    raise ValueError('empty owned schema required before import')
  elif await conn.fetchval('SELECT version_num FROM alembic_version')!=SMOKE_REVISION:
   raise ValueError('selected source/schema mismatch before application import')
 finally:await conn.close()
 if SMOKE_LEGACY14:
  from sqlalchemy.ext.asyncio import create_async_engine
  from app.db.portfolio_migrate import require_migrator,require_source
  require_source()
  engine=create_async_engine(os.environ['DATABASE_URL'],connect_args={'ssl':ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE'])})
  try:
   async with engine.connect() as authority:
    if await require_migrator(authority)!='0014':
     raise ValueError('authenticated legacy14 authority required before import')
  finally:await engine.dispose()
asyncio.run(smoke_admit())
"""
    return "SMOKE_BODY=" + repr(code) + "\n" + prelude + code


def management_role_program(code):
    """Actual restricted clients verify replay and scheduler authority via TLS."""
    checks = r"""
   if MODE=='verify':
    from sqlalchemy import text
    from app.db.portfolio_bootstrap import CATALOGUE_SQL,ACL_SQL
    async with engine.connect() as authority:
     catalogue=(await authority.execute(text(CATALOGUE_SQL))).scalar_one()
     acl=(await authority.execute(text(ACL_SQL))).scalar_one()
     print('portfolio_authority='+json.dumps([catalogue,acl]))
    for role in ('app','scheduler'):
     client=create_async_engine(url.set(username='birja_'+role,password=os.environ['FIXTURE_'+role.upper()+'_PASSWORD']),connect_args={'ssl':ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE'])})
     try:
      async with client.connect() as restricted:
       assert (await restricted.execute(text('SELECT session_user'))).scalar_one()=='birja_'+role
       from app.db.schema_contract import require_schema
       assert await require_schema(restricted)=='0020'
       if role=='app':
        initial=next(r for r in value['tables']['portfolio_creations'] if r['origin']=='initial')
        replay=(await restricted.execute(text("SELECT * FROM create_portfolio(:u,:k,'My portfolio','')"),{'u':initial['user_id'],'k':initial['creation_key']})).one()
        assert replay.replayed and replay.portfolio_id==initial['portfolio_id']
        assert not (await restricted.execute(text("SELECT has_table_privilege(current_user,'accounts','INSERT')"))).scalar_one()
       else:
        assert not (await restricted.execute(text("SELECT has_function_privilege(current_user,'initialize_portfolio(bigint)','EXECUTE')"))).scalar_one()
     finally:await client.dispose()
"""
    marker = "   print('portfolio_projection='"
    if marker not in code:
        raise ValueError("management projection boundary changed")
    return code.replace(marker, checks + "\n" + marker, 1)


def management_fresh_authority_program():
    """Genuine empty-schema0020 migration and restricted TLS clients, no staged reset."""
    return r"""
MODE='create'
import asyncio,json,os,ssl
from uuid import uuid4
from decimal import Decimal
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
async def run():
 await asyncio.to_thread(command.upgrade,Config('/app/alembic.ini'),'0020')
 from app.db.portfolio_bootstrap import PREFLIGHT_SQL,GRANTS_SQL,CATALOGUE_SQL,ACL_SQL
 from app.db.schema_contract import require_schema
 url=make_url(os.environ['DATABASE_URL'])
 args={'ssl':ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE'])}
 engine=create_async_engine(url,connect_args=args)
 try:
  async with engine.begin() as conn:
   raw=await conn.get_raw_connection()
   await raw.driver_connection.execute(PREFLIGHT_SQL)
   await raw.driver_connection.execute(GRANTS_SQL)
   uid=(await conn.execute(text("INSERT INTO users(email) VALUES ('fresh@example.test') RETURNING id"))).scalar_one()
  for role in ('app','scheduler'):
   client=create_async_engine(url.set(username='birja_'+role,password=os.environ['FIXTURE_'+role.upper()+'_PASSWORD']),connect_args=args)
   try:
    async with client.begin() as restricted:
     assert await require_schema(restricted)=='0020'
     assert (await restricted.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))).scalar_one()
     assert not (await restricted.execute(text("SELECT has_table_privilege(current_user,'accounts','INSERT')"))).scalar_one()
     if role=='app':
      key=uuid4()
      original=(await restricted.execute(text("SELECT * FROM create_portfolio(:u,:k,'Fresh strategy','')"),{'u':uid,'k':key})).one()
      replay=(await restricted.execute(text("SELECT * FROM create_portfolio(:u,:k,'Fresh strategy','')"),{'u':uid,'k':key})).one()
      assert not original.replayed and replay.replayed and original.portfolio_id==replay.portfolio_id
      assert (await restricted.execute(text('SELECT cash FROM accounts WHERE id=:p'),{'p':original.portfolio_id})).scalar_one()==Decimal('10000')
     else:
      assert not (await restricted.execute(text("SELECT has_function_privilege(current_user,'create_portfolio(bigint,uuid,text,text)','EXECUTE')"))).scalar_one()
   finally:await client.dispose()
  async with engine.connect() as conn:
   catalogue=(await conn.execute(text(CATALOGUE_SQL))).scalar_one()
   acl=(await conn.execute(text(ACL_SQL))).scalar_one()
   assert (await conn.execute(text('SELECT count(*) FROM portfolio_creations'))).scalar_one()==1
   print('portfolio_authority='+json.dumps([catalogue,acl]))
   print('portfolio_projection='+json.dumps({'revision':'0020','fresh':True}))
   print('portfolio_verified_tls=true')
 finally:await engine.dispose()
asyncio.run(run())
"""


def closure_role_program(code):
    """Measure final object/effective-default authority through real TLS roles."""
    checks = r"""
   if MODE=='verify' or globals().get('AUTHORITY_DIAGNOSTIC',False):
    from app.db.portfolio_bootstrap import CATALOGUE_0023_SQL,CATALOGUE_0023_SHA256,ACL_SQL,ACL_0023_SHA256,DEFAULT_ACL_0023_SQL,DEFAULT_ACL_0023_SHA256
    from app.db.schema_contract import require_schema,SchemaAdmissionError
    from app.services.portfolio_closure import ClosureIntent as ReplayClosureIntent,close_portfolio as replay_close_portfolio
    from sqlalchemy.ext.asyncio import AsyncSession as ReplaySession
    from uuid import UUID
    async with engine.connect() as authority:
     measured=[(await authority.execute(text(query))).scalar_one() for query in (CATALOGUE_0023_SQL,ACL_SQL,DEFAULT_ACL_0023_SQL)]
     assert measured==[CATALOGUE_0023_SHA256,ACL_0023_SHA256,DEFAULT_ACL_0023_SHA256]
     assert (await authority.execute(text("SELECT count(*) FROM pg_tables WHERE schemaname='public'"))).scalar_one()==31
     assert (await authority.execute(text("SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='S'"))).scalar_one()==24
     print('portfolio_authority='+json.dumps(measured))
     # Missing global function defaults mean implicit PUBLIC EXECUTE. Runtime
     # must reject that state, even with unchanged final object ACLs.
     nested=await authority.begin_nested()
     try:
      await authority.execute(text('ALTER DEFAULT PRIVILEGES FOR ROLE birja_migrator GRANT EXECUTE ON FUNCTIONS TO PUBLIC'))
      try:await require_schema(authority)
      except SchemaAdmissionError:pass
      else:raise AssertionError('implicit public function defaults admitted')
     finally:await nested.rollback()
    for role,client in (('app',app),('scheduler',scheduler)):
     async with client.connect() as restricted:
      assert (await restricted.execute(text('SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()'))).scalar_one()
      assert (await restricted.execute(text('SELECT session_user'))).scalar_one()=='birja_'+role
      assert await require_schema(restricted)=='0023'
      assert (await restricted.execute(text("SELECT has_function_privilege(current_user,'close_portfolio(bigint,bigint,uuid,text,text)','EXECUTE')"))).scalar_one()==(role=='app')
      for table in ('portfolio_lifecycle_closures','portfolio_closure_intents'):
       assert not (await restricted.execute(text("SELECT has_table_privilege(current_user,:t,'INSERT,UPDATE,DELETE')"),{'t':table})).scalar_one()
       assert not (await restricted.execute(text("SELECT has_sequence_privilege(current_user,:s,'USAGE')"),{'s':table+'_id_seq'})).scalar_one()
    for original in value.get('tables',{}).get('portfolio_closure_intents',[]):
     async with ReplaySession(app) as replay:
      result=await replay_close_portfolio(replay,ReplayClosureIntent(original['user_id'],original['portfolio_id'],UUID(original['intent_key']),original['confirmation_name'],original['policy_version']))
      assert result.replayed and result.outcome==original['outcome']
"""
    marker = "   print('portfolio_projection='"
    if marker not in code:
        raise ValueError("closure projection boundary changed")
    return code.replace(marker, checks + "\n" + marker, 1)


def fresh_authority_program(revision="0023", *, upgraded=False, upgraded_from="0020"):
    """Fresh current or genuine14/20→23 TLS, preserving old columns and tails."""
    if upgraded_from not in {"0014", "0020"} or (not upgraded and upgraded_from != "0020"):
        raise ValueError("explicit finite upgraded source required")
    if revision == "0020" and not upgraded:
        return management_fresh_authority_program()
    if revision != "0023":
        raise ValueError("unsupported fresh/upgraded authority family")
    producer = load("portfolio-closure-recovery-fixture").producer()
    old_columns = producer.contract_columns(upgraded_from)
    current_columns = producer.contract_columns("0023")
    extras = {table: sorted(current_columns[table] - columns) for table, columns in old_columns.items()}
    prelude = ("UPGRADED=" + repr(upgraded) + "\nUPGRADED_FROM=" + repr(upgraded_from)
               + "\nOLD_TABLES=" + repr(sorted(old_columns)) + "\nOLD_IDENTITIES="
               + repr(producer.identity_tables(upgraded_from)) + "\nEXTRA_COLUMNS=" + repr(extras) + "\n")
    return prelude + r"""
MODE='create'
AUTHORITY_DIAGNOSTIC=True
import asyncio,json,os,ssl
from uuid import uuid4
from decimal import Decimal
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.services.portfolio_closure import ClosureIntent,close_portfolio
async def snapshot(conn):
 expression='to_jsonb(t)-CAST(:extra AS text[])'
 rows={table:(await conn.execute(text('SELECT ('+expression+')::text FROM public.'+table+' t ORDER BY ('+expression+')::text'),{'extra':EXTRA_COLUMNS[table]})).scalars().all() for table in OLD_TABLES if table!='alembic_version'}
 tails={table:list((await conn.execute(text('SELECT last_value,is_called FROM public.'+table+'_id_seq'))).one()) for table in OLD_IDENTITIES}
 return rows,tails
async def run():
 url=make_url(os.environ['DATABASE_URL'])
 args={'ssl':ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE'])}
 engine=create_async_engine(url,connect_args=args)
 app=create_async_engine(url.set(username='birja_app',password=os.environ['FIXTURE_APP_PASSWORD']),connect_args=args)
 scheduler=create_async_engine(url.set(username='birja_scheduler',password=os.environ['FIXTURE_SCHEDULER_PASSWORD']),connect_args=args)
 try:
  if UPGRADED:
   await asyncio.to_thread(command.upgrade,Config('/app/alembic.ini'),UPGRADED_FROM)
   async with engine.begin() as conn:
    if UPGRADED_FROM=='0020':
     from app.db.portfolio_bootstrap import PREFLIGHT_SQL,GRANTS_SQL
     raw=await conn.get_raw_connection()
     await raw.driver_connection.execute(PREFLIGHT_SQL)
     await raw.driver_connection.execute(GRANTS_SQL)
    uid=(await conn.execute(text("INSERT INTO users(email) VALUES ('retained-before-upgrade@example.test') RETURNING id"))).scalar_one()
    if UPGRADED_FROM=='0014':
     original=(await conn.execute(text('INSERT INTO accounts(user_id,cash,starting_cash) VALUES (:u,123.45,8765) RETURNING id'),{'u':uid})).scalar_one()
     await conn.execute(text("INSERT INTO holdings(user_id,coin_id,quantity,cost_basis) SELECT :u,id,.001,12.34 FROM coins WHERE symbol='BTC'"),{'u':uid})
    else:
     original=(await conn.execute(text('SELECT initialize_portfolio(:u)'),{'u':uid})).scalar_one()
     await conn.execute(text('UPDATE accounts SET cash=123.45 WHERE id=:p'),{'p':original})
     await conn.execute(text("INSERT INTO holdings(portfolio_id,user_id,coin_id,quantity,cost_basis) SELECT :p,:u,id,.001,12.34 FROM coins WHERE symbol='BTC'"),{'p':original,'u':uid})
   async with engine.connect() as conn:before=await snapshot(conn)
   from app.db.portfolio_migrate import require_migrator
   async with engine.connect() as conn:
    assert await require_migrator(conn)==UPGRADED_FROM
  await asyncio.to_thread(command.upgrade,Config('/app/alembic.ini'),'0023')
  from app.db.portfolio_bootstrap import PREFLIGHT_0023_SQL,GRANTS_0023_SQL
  async with engine.begin() as conn:
   raw=await conn.get_raw_connection()
   await raw.driver_connection.execute(PREFLIGHT_0023_SQL)
   await raw.driver_connection.execute(GRANTS_0023_SQL)
   if UPGRADED:
    assert await snapshot(conn)==before
    assert (await conn.execute(text('SELECT cash,starting_cash FROM accounts WHERE id=:p'),{'p':original})).one()==(Decimal('123.45'),Decimal('8765') if UPGRADED_FROM=='0014' else Decimal('10000'))
    if UPGRADED_FROM=='0014':
     assert (await conn.execute(text('SELECT name,description,closed_at FROM accounts WHERE id=:p'),{'p':original})).one()==('My portfolio','',None)
     assert (await conn.execute(text("SELECT origin FROM portfolio_initializations WHERE user_id=(SELECT user_id FROM accounts WHERE id=:p)"),{'p':original})).scalar_one()=='legacy'
     assert (await conn.execute(text('SELECT count(*) FROM portfolio_creations WHERE portfolio_id=:p'),{'p':original})).scalar_one()==0
     assert (await conn.execute(text('SELECT portfolio_id,user_id,quantity,cost_basis FROM holdings WHERE portfolio_id=:p'),{'p':original})).one()==(original,uid,Decimal('.001'),Decimal('12.34'))
   uid=(await conn.execute(text("INSERT INTO users(email) VALUES ('fresh-current@example.test') RETURNING id"))).scalar_one()
  key=uuid4()
  async with app.begin() as restricted:
   created=(await restricted.execute(text("SELECT * FROM create_portfolio(:u,:k,'Fresh strategy','')"),{'u':uid,'k':key})).one()
   replay=(await restricted.execute(text("SELECT * FROM create_portfolio(:u,:k,'Fresh strategy','')"),{'u':uid,'k':key})).one()
   assert not created.replayed and replay.replayed and created.portfolio_id==replay.portfolio_id
  async with async_sessionmaker(app)() as db:
   original_intent=ClosureIntent(uid,created.portfolio_id,uuid4(),'Fresh strategy')
   assert (await close_portfolio(db,original_intent)).outcome=='closed'
   assert (await close_portfolio(db,original_intent)).replayed
  async with engine.connect() as conn:
   assert (await conn.execute(text('SELECT count(*) FROM portfolio_closure_intents'))).scalar_one()==1
   assert (await conn.execute(text('SELECT count(*) FROM portfolio_creations'))).scalar_one()==(2 if UPGRADED and UPGRADED_FROM=='0020' else 1)
   assert (await conn.execute(text('SELECT cash,starting_cash FROM accounts WHERE id=:p'),{'p':created.portfolio_id})).one()==(Decimal('10000'),Decimal('10000'))
   value={'revision':'0023','fresh':not UPGRADED,'upgraded':UPGRADED,'upgraded_from':UPGRADED_FROM if UPGRADED else None}
   print('portfolio_projection='+json.dumps(value))
   print('portfolio_verified_tls=true')
 finally:await app.dispose();await scheduler.dispose();await engine.dispose()
asyncio.run(run())
"""


def authority_probe_program():
    return r"""
MODE='verify'
import asyncio,json,os,ssl
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
async def run():
 url=make_url(os.environ['DATABASE_URL'])
 args={'ssl':ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE'])}
 engine=create_async_engine(url,connect_args=args)
 app=create_async_engine(url.set(username='birja_app',password=os.environ['FIXTURE_APP_PASSWORD']),connect_args=args)
 scheduler=create_async_engine(url.set(username='birja_scheduler',password=os.environ['FIXTURE_SCHEDULER_PASSWORD']),connect_args=args)
 try:
  async with engine.connect() as conn:
   value={'revision':'0023','authority_probe':True}
   print('portfolio_projection='+json.dumps(value))
   print('portfolio_verified_tls=true')
 finally:await app.dispose();await scheduler.dispose();await engine.dispose()
asyncio.run(run())
"""


def retained_writer_refusal_program(revision="0023", retained="0020"):
    if (revision, retained) not in {("0023", "0020"), ("0020", "0017")}:
        raise ValueError("unsupported retained writer refusal")
    return (r"""
import asyncio,os,ssl
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
async def run():
 url=make_url(os.environ['DATABASE_URL']).set(username='birja_app',password=os.environ['FIXTURE_APP_PASSWORD'])
 engine=create_async_engine(url,connect_args={'ssl':ssl.create_default_context(cafile=os.environ['DATABASE_SSL_CA_FILE'])})
 try:
  async with engine.connect() as conn:
   revision=(await conn.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()
   session_user=(await conn.execute(text('SELECT session_user'))).scalar_one()
   assert session_user=='birja_app'
   if revision != '0020':raise ValueError('expected current schema before old consumer import')
   from app.db.schema_contract import require_schema,SchemaAdmissionError
   try:await require_schema(conn)
   except SchemaAdmissionError:pass
   else:raise AssertionError('retained0017 writer admitted current0020')
   print('retained0017_current0020_write_refused=true')
 finally:await engine.dispose()
asyncio.run(run())
""").replace("0020", revision).replace("retained0017", "retained" + retained)


def run(*, archive=None, archive_sha=None, cold=False, revision="0023", fresh_bootstrap=False,
        upgraded_bootstrap=False, upgraded_from="0020"):
    if fresh_bootstrap and (revision not in {"0020", "0023"} or cold or upgraded_bootstrap):
        raise ValueError("fresh authority requires an explicit supported non-cold lane")
    if upgraded_bootstrap and (revision != "0023" or cold):
        raise ValueError("upgraded authority requires current0023 non-cold lane")
    if upgraded_from not in {"0014", "0020"} or (upgraded_from == "0014" and not upgraded_bootstrap):
        raise ValueError("explicit finite upgraded source required")
    sources = load("portfolio-sources")
    fixture = selected_fixture(
        sources, revision, archive=archive, archive_sha=archive_sha
    )
    if cold:
        if archive is None:
            raise ValueError("cold lane requires selected recovery archive")
        sources.verify_archive_binding(archive, archive_sha)
    env = {
        key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ
    }
    env["COMPOSE_DISABLE_ENV_FILE"] = "1"

    def call(argv, *, data=None, timeout=240, fail=False):
        result = subprocess.run(
            argv, input=data, env=env, capture_output=True, timeout=timeout
        )
        if (result.returncode == 0) == fail:
            raise AssertionError(
                "owned portfolio command failed: "
                + Path(argv[0]).name
                + "\n"
                + result.stderr.decode()[-2500:]
            )
        return result.stdout

    for kind in ("container", "network", "volume"):
        if call(
            [
                "docker",
                kind,
                "ls",
                "-q",
                "--filter",
                "label=com.docker.compose.project=" + PROJECT,
            ]
        ).strip():
            raise ValueError("refuse preexisting owned fixture resources")
    binding = build_selected_runtime(
        sources, env, revision=revision, archive=archive, archive_sha=archive_sha
    )
    commit = binding["source_commit"]
    if archive is not None:
        sources.record_image_binding(archive, "current" + revision, binding)
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-portfolio-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        immutable = root / "source-image-binding.json"
        with immutable.open("x") as stream:
            json.dump(binding, stream, sort_keys=True)
        immutable.chmod(0o400)
        call(
            [
                "bash",
                str(ROOT / "deploy/provision-db-tls.sh"),
                "--synthetic",
                str(root),
                "--create",
                "--approved-custody",
                "owner-off-server-password-manager",
            ]
        )
        hba = root / "hba"
        hba.mkdir(mode=0o755)
        hba.chmod(0o755)
        (hba / "pg_hba.conf").write_text(
            "local all all trust\nhostssl all all samenet scram-sha-256\nhostnossl all all all reject\n"
        )
        (hba / "pg_hba.conf").chmod(0o644)
        compose = root / "compose.json"
        compose.write_text(
            json.dumps(
                {
                    "name": PROJECT,
                    "services": {
                        "postgres": {
                            "image": PG,
                            "pull_policy": "never",
                            "user": "70:70",
                            "environment": {
                                "PGDATA": "/var/lib/postgresql/18/docker",
                                "POSTGRES_USER": "birja_ops_bootstrap",
                                "POSTGRES_PASSWORD": "synthetic-only-ops",
                                "POSTGRES_DB": "birja_source_test",
                            },
                            "tmpfs": [
                                "/var/lib/postgresql:size=268435456,uid=70,gid=70,mode=0750"
                            ],
                            "volumes": [
                                str(root / "db-tls/server")
                                + ":/run/birja/db-server:ro",
                                str(root / "db-tls/ca.crt") + ":/run/birja/db-ca.crt:ro",
                                str(hba) + ":/run/birja/db-hba:ro",
                            ],
                            "command": [
                                "-c",
                                "ssl=on",
                                "-c",
                                "ssl_cert_file=/run/birja/db-server/server.crt",
                                "-c",
                                "ssl_key_file=/run/birja/db-server/server.key",
                                "-c",
                                "hba_file=/run/birja/db-hba/pg_hba.conf",
                            ],
                            "networks": ["isolated"],
                            "mem_limit": "512m",
                            "pids_limit": 128,
                            "healthcheck": {
                                "test": [
                                    "CMD-SHELL",
                                    "pg_isready -U birja_ops_bootstrap -d birja_source_test",
                                ],
                                "interval": "2s",
                                "timeout": "3s",
                                "retries": 30,
                            },
                        }
                    },
                    "networks": {"isolated": {"internal": True}},
                }
            )
        )
        dc = [
            "docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-p",
            PROJECT,
            "-f",
            str(compose),
        ]
        clone_project = PROJECT + "-cold"
        clone_dc = [
            "docker",
            "compose",
            "--env-file",
            "/dev/null",
            "-p",
            clone_project,
            "-f",
            str(compose),
        ]
        for kind in ("container", "network", "volume"):
            if call(
                [
                    "docker",
                    kind,
                    "ls",
                    "-q",
                    "--filter",
                    "label=com.docker.compose.project=" + clone_project,
                ]
            ).strip():
                raise ValueError("refuse preexisting cold resources")
        client_network = PROJECT + "_isolated"
        passwords = {"app": "a" * 64, "scheduler": "b" * 64, "migrator": "c" * 64}
        try:
            call(dc + ["up", "-d", "--wait"], timeout=120)
            setup = "REVOKE CREATE ON SCHEMA public FROM PUBLIC;\n"
            for role, password in passwords.items():
                if upgraded_bootstrap and upgraded_from == "0014" and role in {"app", "scheduler"}:
                    continue
                setup += (
                    "CREATE ROLE birja_"
                    + role
                    + " LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '"
                    + password
                    + "';\n"
                )
            setup += "CREATE ROLE birja_action_operator NOLOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS; GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator;\n"
            call(
                dc
                + [
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-XqAt",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-U",
                    "birja_ops_bootstrap",
                    "-d",
                    "birja_source_test",
                ],
                data=setup.encode(),
            )
            client_env = {
                "ENV": "test",
                "DATABASE_URL": "postgresql+asyncpg://birja_migrator:"
                + passwords["migrator"]
                + "@postgres:5432/birja_source_test",
                "DATABASE_SSL_CA_FILE": "/run/birja/db-ca.crt",
                "REDIS_URL": "redis://localhost:6379/0",
                "OTP_HMAC_SECRET": "synthetic-portfolio-fixture-otp-" + "x" * 32,
                "JWT_SECRET": "synthetic-portfolio-fixture-jwt-" + "y" * 32,
                "EMAIL_BACKEND": "console",
                "PRICE_SOURCE": "fake",
                "FIXTURE_APP_PASSWORD": passwords["app"],
                "FIXTURE_SCHEDULER_PASSWORD": passwords["scheduler"],
                "FIXTURE_BOOT_PASSWORD": "synthetic-only-ops",
            }

            if upgraded_bootstrap and upgraded_from == "0014":
                # Reproduce the genuine old dev role-creation order using only
                # the explicit migrator. No current financial service runs14.
                preparation = "from alembic import command\nfrom alembic.config import Config\ncommand.upgrade(Config('/app/alembic.ini'),'0014')\nprint('legacy14_migration_prepared=true')\n"
                argv = ["docker", "run", "--rm", "-i", "--network", client_network,
                        "-v", str(root / "db-tls/ca.crt") + ":/run/birja/db-ca.crt:ro"]
                for key, value in client_env.items():
                    argv += ["-e", key + "=" + value]
                argv += ["--entrypoint", "python", binding["id"], "-"]
                sources.verify_image(binding, json.loads(call(["docker", "image", "inspect", binding["id"]])))
                if archive is not None:
                    sources.verify_archive_binding(archive, archive_sha)
                if b"legacy14_migration_prepared=true" not in call(argv, data=preparation.encode()).splitlines():
                    raise ValueError("legacy14 preparation refused")
                setup = "".join("CREATE ROLE birja_" + role
                    + " LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '"
                    + passwords[role] + "';\n" for role in ("app", "scheduler"))
                setup += "GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;\n"
                call(dc + ["exec", "-T", "postgres", "psql", "-XqAt", "-v", "ON_ERROR_STOP=1",
                           "-U", "birja_ops_bootstrap", "-d", "birja_source_test"], data=setup.encode())

            authorities = []
            def transport(code, *, prepared_legacy14=False):
                if revision == "0020" and not fresh_bootstrap:
                    code = management_role_program(code)
                if revision == "0023":
                    code = closure_role_program(code)
                code = admitted_program(code, revision, prepared_legacy14=prepared_legacy14)
                sources.verify_image(
                    binding,
                    json.loads(call(["docker", "image", "inspect", binding["id"]])),
                )
                if revision == "0023" and (
                    sources.git("rev-parse", "HEAD").decode().strip() != commit
                    or sources.git(
                        "diff", "--name-only", "HEAD", "--", "backend"
                    ).strip()
                ):
                    raise ValueError("current source drift")
                if archive is not None:
                    sources.verify_archive_binding(archive, archive_sha)
                argv = [
                    "docker",
                    "run",
                    "--rm",
                    "-i",
                    "--network",
                    client_network,
                    "-v",
                    str(root / "db-tls/ca.crt") + ":/run/birja/db-ca.crt:ro",
                ]
                for key, value in client_env.items():
                    argv += ["-e", key + "=" + value]
                argv += ["--entrypoint", "python", binding["id"], "-"]
                output = call(argv, data=code.encode())
                for line in output.splitlines():
                    if line.startswith(b'portfolio_authority='):
                        authorities.append(json.loads(line.split(b'=', 1)[1]))
                rows = [
                    line.split(b"=", 1)[1]
                    for line in output.splitlines()
                    if line.startswith(b"portfolio_projection=")
                ]
                if (
                    len(rows) != 1
                    or b"portfolio_verified_tls=true" not in output.splitlines()
                ):
                    raise AssertionError("missing actual verified TLS projection")
                if "MODE='replay-restored'\n" in code:
                    reports = [line.split(b'=', 1)[1] for line in output.splitlines()
                               if line.startswith(b'portfolio_restored_replay=')]
                    if len(reports) != 1:
                        raise ValueError('actual restored retry report required')
                    return {'projection': json.loads(rows[0]), 'replay': json.loads(reports[0])}
                return json.loads(rows[0])

            def production_bootstrap():
                # Invoke the independent source-owned SQL over verified TLS;
                # these are private synthetic credentials, never host config.
                variables = {'apply':'true','bootstrap':'birja_ops_bootstrap',
                             'db_name':'birja_source_test',
                             **{role + '_password':password for role,password in passwords.items()}}
                prefix = ''.join('\\set ' + key + ' ' + value + '\n' for key,value in variables.items())
                command = dc + ['exec','-T','-e','PGPASSWORD=synthetic-only-ops',
                                '-e','PGSSLMODE=verify-full','-e','PGSSLROOTCERT=/run/birja/db-ca.crt',
                                'postgres','psql','-XqAt','-v','ON_ERROR_STOP=1',
                                '-h','postgres','-U','birja_ops_bootstrap','-d','birja_source_test']
                call(command, data=(prefix + (ROOT/'deploy/db/bootstrap-roles.sql').read_text()).encode())

            if fresh_bootstrap or upgraded_bootstrap:
                transport(fresh_authority_program(revision, upgraded=upgraded_bootstrap,
                                                  upgraded_from=upgraded_from),
                          prepared_legacy14=(upgraded_bootstrap and upgraded_from == "0014"))
                if revision == '0023':
                    production_bootstrap()
                    transport(authority_probe_program())
                if len(authorities) != (2 if revision == '0023' else 1) or any(value != authorities[0] for value in authorities):
                    raise ValueError('missing measured fresh authority')
                print('actual_current' + revision + ('_upgraded' if upgraded_bootstrap else '_fresh') + '_tls_restricted_roles=true', flush=True)
                return authorities[0]
            fixture.main(["create"], transport=transport)
            expected = root / "immutable-before.json"
            digest = fixture.main(
                ["projection", "--snapshot", str(expected)], transport=transport
            )
            expected.chmod(0o400)
            if revision == '0023':
                transport(authority_probe_program())
                production_bootstrap()
            fixture.main(["verify"], transport=transport)
            if revision in {"0020", "0023"} and archive is not None:
                old_revision = "0020" if revision == "0023" else "0017"
                old_binding = build_selected_runtime(sources, env, revision=old_revision,
                    archive=archive, archive_sha=archive_sha)
                sources.record_image_binding(archive, 'retained' + old_revision + '-refusal', old_binding)
                sources.verify_archive_binding(archive, archive_sha)
                sources.verify_image(old_binding, json.loads(call(['docker', 'image', 'inspect', old_binding['id']])))
                old_argv = ['docker', 'run', '--rm', '-i', '--network', client_network,
                    '-v', str(root / 'db-tls/ca.crt') + ':/run/birja/db-ca.crt:ro']
                for key, value in client_env.items():
                    old_argv += ['-e', key + '=' + value]
                old_argv += ['--entrypoint', 'python', old_binding['id'], '-']
                refusal = call(old_argv, data=retained_writer_refusal_program(revision, old_revision).encode())
                if ('retained' + old_revision + '_current' + revision + '_write_refused=true').encode() not in refusal.splitlines():
                    raise AssertionError('missing genuine retained writer refusal')
            fixture.main(
                ["compare", "--snapshot", str(expected), "--expected-sha256", digest],
                transport=transport,
            )
            if cold:
                # One immutable pre-backup oracle, one encrypted repository,
                # and a genuinely new server after the source is destroyed.
                import shutil

                with installed_recovery_verifier(archive, archive_sha) as r:
                    manifest = r.canonical(dc, "birja_source_test")
                    r.recovery_contract().validate_manifest(manifest)
                    stage = root / "backup-input"
                    stage.mkdir(mode=0o700)
                    dump = call(
                        dc
                        + [
                            "exec",
                            "-T",
                            "postgres",
                            "pg_dump",
                            "-U",
                            "birja_migrator",
                            "-d",
                            "birja_source_test",
                            "--format=custom",
                            "--no-owner",
                            "--no-acl",
                        ]
                    )
                    (stage / "database.dump").write_bytes(dump)
                    (stage / "manifest.json").write_text(
                        json.dumps(manifest, sort_keys=True)
                    )
                    shutil.copyfile(archive, stage / "recovery.tar")
                    password = root / "restic-password"
                    password.write_text(os.urandom(32).hex())
                    password.chmod(0o600)
                    restic = Path("/tmp/birja-test-tools/restic-0.19.1/restic")
                    if r.digest(restic) != r.RESTIC_SHA:
                        raise ValueError("unverified local restic")
                    restic_args = [
                        str(restic),
                        "--repo",
                        str(root / "repository"),
                        "--password-file",
                        str(password),
                        "--no-cache",
                    ]
                    call(restic_args + ["init"])
                    # Relative paths are fixed: no host/private path may enter backup.
                    result = subprocess.run(
                        restic_args + ["backup", "--json", "."],
                        cwd=stage,
                        env=env,
                        capture_output=True,
                        check=True,
                        timeout=180,
                    )
                    rows = [json.loads(line) for line in result.stdout.splitlines()]
                    ids = [
                        row["snapshot_id"]
                        for row in rows
                        if row.get("message_type") == "summary"
                    ]
                    if len(ids) != 1 or not re.fullmatch("[0-9a-f]{64}", ids[0]):
                        raise ValueError("missing exact encrypted snapshot")
                    hashes = {p.name: r.digest(p) for p in stage.iterdir()}
                    shutil.rmtree(stage)
                    call(dc + ["down", "-v", "--remove-orphans"])
                    call(restic_args + ["check", "--read-data"])
                    recovered = root / "cold-restored"
                    call(
                        restic_args
                        + ["restore", ids[0], "--target", str(recovered), "--verify"]
                    )
                    if {p.name: r.digest(p) for p in recovered.iterdir()} != hashes:
                        raise ValueError("encrypted cold payload changed")
                    sources.verify_archive_binding(recovered / "recovery.tar", archive_sha)
                    call(clone_dc + ["up", "-d", "--wait"])
                    r.sql(clone_dc, "CREATE DATABASE birja_ops_test;", "birja_source_test")
                    source_manifest = json.loads((recovered / "manifest.json").read_text())
                    with r.restored(clone_dc, (recovered / "database.dump").read_bytes(), manifest=source_manifest):
                        r.verify(
                            clone_dc, source_manifest, quarantined=revision != "0023"
                        )
                        # Source evidence is checked before finite regrant. The
                        # current closure family now has its exact runtime ACL;
                        # historical families retain their original contract.
                        r.sql(
                            clone_dc,
                            "ALTER ROLE birja_migrator LOGIN PASSWORD '"
                            + passwords["migrator"]
                            + "';",
                            "birja_ops_test",
                        )
                        client_network = clone_project + "_isolated"
                        fixture.main(
                            [
                                "compare",
                                "--database",
                                "birja_restore_test",
                                "--snapshot",
                                str(expected),
                                "--expected-sha256",
                                digest,
                            ],
                            transport=transport,
                        )
                        if revision == '0023':
                            fixture.main(
                                ['replay-restored', '--database', 'birja_restore_test',
                                 '--snapshot', str(expected), '--expected-sha256', digest],
                                transport=transport,
                            )
                    print(
                        "actual_current"
                        + revision
                        + "_encrypted_cold_restore=true source_destroyed=true immutable_before_oracle=true quarantine=true",
                        flush=True,
                    )
            assert json.loads(immutable.read_text()) == binding
            print(
                "actual_current"
                + revision
                + "_portfolio_tls_restricted_roles=true immutable_snapshot_compare=true",
                flush=True,
            )
            if revision in {"0020", "0023"}:
                if len(authorities) != (2 if revision == '0023' else 1) or any(value != authorities[0] for value in authorities):
                    raise ValueError('missing measured upgraded authority')
                return authorities[0]
        finally:
            if hasattr(fixture, '_source_directory'):
                fixture._source_directory.cleanup()
            call(dc + ["down", "-v", "--remove-orphans"], timeout=120)
            call(clone_dc + ["down", "-v", "--remove-orphans"], timeout=120)
            for kind in ("container", "network", "volume"):
                for project in (PROJECT, clone_project):
                    if call(
                        [
                            "docker",
                            kind,
                            "ls",
                            "-q",
                            "--filter",
                            "label=com.docker.compose.project=" + project,
                        ]
                    ).strip():
                        raise AssertionError("owned portfolio resources leaked")


@contextmanager
def installed_recovery_verifier(archive, archive_sha):
    """Keep the authenticated consumer and adjacent retained sources alive."""
    trusted = load_recovery()
    trusted.bundle_verify(archive, archive_sha, required_profile="deploy-recovery-v4")
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-verifier-context-") as temporary:
        host = Path(temporary) / "host"
        host.mkdir(mode=0o700)
        trusted.bundle_install(
            archive, archive_sha, str(host), required_profile="deploy-recovery-v4"
        )
        selected = host / "var/lib/birja/recovery/releases" / archive_sha / "deploy/verify-restore.py"
        yield load_recovery(selected)


def load_recovery(path=None):
    spec = importlib.util.spec_from_file_location(
        "portfolio_cold_recovery", path if path is not None else ROOT / "deploy/verify-restore.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    run()
