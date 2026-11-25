#!/usr/bin/env python3
"""Real final portfolio bootstrap on exclusively owned fresh/upgraded dev stacks."""

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def stage_program(revision):
    assert revision in ("0015", "0016", "0024", "0025")
    return r'''
import asyncio,os,sys
import asyncpg
from unittest.mock import patch
from app.db.dev_bootstrap import bootstrap
original=asyncio.create_subprocess_exec
target=TARGET
async def child(*args,**kwargs):
 return await original(sys.executable,'-m','alembic','upgrade',target,**kwargs)
async def main():
 try:
  with patch('app.db.dev_bootstrap.asyncio.create_subprocess_exec',child):
   await bootstrap('dev',os.environ['DATABASE_URL'],migrate=True)
 except asyncpg.RaiseError as exc:
  assert 'final revision required' in str(exc)
 else:raise AssertionError('staged schema bootstrapped')
 c=await asyncpg.connect(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://'))
 try:
  assert await c.fetchval('SELECT version_num FROM alembic_version')==target
  assert not await c.fetchval("SELECT rolcanlogin FROM pg_roles WHERE rolname='birja_migrator'")
  from sqlalchemy.ext.asyncio import create_async_engine
  from sqlalchemy import text
  from app.db.portfolio_migrate import require_migrator
  e=create_async_engine(os.environ['DATABASE_URL'])
  try:
   async with e.connect() as x:
    await x.execute(text('SET ROLE birja_migrator'))
    try:await require_migrator(x)
    except ValueError as exc:assert 'Authenticated restricted migrator' in str(exc)
    else:raise AssertionError('SET ROLE bypass')
  finally:await e.dispose()
  print('actual_staged_migration_durable=true revision='+target,flush=True)
 finally:await c.close()
asyncio.run(main())
'''.replace('TARGET', repr(revision))


def retained_catalog_program():
    return r'''
import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from app.db.schema_contract import SchemaAdmissionError, require_schema

async def main():
    engine = create_async_engine(os.environ['DATABASE_URL'])
    try:
        async with engine.connect() as conn:
            assert await require_schema(conn, consumer='retained0025') == '0025'
            try:
                await require_schema(conn)
            except SchemaAdmissionError as exc:
                assert exc.reason == 'incompatible_schema'
            else:
                raise AssertionError('current consumer admitted retained 0025')
        print('actual_retained0025_admitted=true current_refused=true', flush=True)
    finally:
        await engine.dispose()

asyncio.run(main())
'''


def financial_program():
    return r'''
import asyncio,os
from decimal import Decimal as D
import asyncpg
from app.db.portfolio_bootstrap import PREFLIGHT_0026_SQL
async def main():
 c=await asyncpg.connect(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://'))
 try:
  assert await c.fetchval("SELECT current_database()='birja' AND session_user='birja'")
  assert await c.fetchval("SELECT version_num FROM alembic_version")=='0026'
  await c.execute(PREFLIGHT_0026_SQL)
  from app.db.schema_contract import require_schema, SchemaAdmissionError
  # Disposable administrative fixture only: retain the original custom-baseline
  # economic oracle without granting ordinary account INSERT or rewriting a baseline.
  uid=await c.fetchval("INSERT INTO users(email) VALUES ('bootstrap@example.test') RETURNING id")
  root=await c.fetchval("INSERT INTO accounts(user_id,name,name_key,cash,starting_cash) VALUES ($1,'Custom baseline',portfolio_name_key('Custom baseline'),123.45,7777) RETURNING id",uid)
  await c.execute("INSERT INTO portfolio_initializations(user_id,origin) VALUES ($1,'legacy')",uid)
  await c.execute("SET ROLE birja_app")
  await c.fetch("SELECT id,ticker FROM public.stock_catalog_listings")
  assert await c.fetchval("SELECT has_column_privilege(current_user,'stock_catalog_admissions','fields','SELECT')")
  assert not await c.fetchval("SELECT has_column_privilege(current_user,'stock_catalog_admissions','reference','SELECT')")
  assert not await c.fetchval("SELECT has_table_privilege(current_user,'stock_catalog_listings','INSERT,UPDATE,DELETE')")
  try:await c.execute("INSERT INTO accounts(user_id,cash,starting_cash) VALUES ($1,123.45,7777)",uid)
  except asyncpg.InsufficientPrivilegeError:pass
  else:raise AssertionError('ordinary account INSERT admitted')
  await c.execute("UPDATE accounts SET cash=cash+1 WHERE id=$1",root)
  assert await c.fetchval("SELECT cash FROM accounts WHERE id=$1",root)==D('124.45')
  for column in ('starting_cash','name','closed_at','user_id'):
   assert not await c.fetchval("SELECT has_column_privilege(current_user,'accounts',$1,'UPDATE')",column)
  await c.execute("RESET ROLE; SET ROLE birja_scheduler")
  assert not await c.fetchval("SELECT has_column_privilege(current_user,'accounts','cash','UPDATE')")
  assert await c.fetchval("SELECT has_function_privilege(current_user,'lock_stock_portfolio_roots(bigint)','EXECUTE')")
  assert not await c.fetchval("SELECT has_function_privilege(current_user,'check_portfolio_financial_write()','EXECUTE')")
  assert not await c.fetchval("SELECT has_table_privilege(current_user,'portfolio_stock_closures','INSERT,UPDATE,DELETE')")
  await c.execute("RESET ROLE")
  before=await c.fetch("SELECT id,user_id,cash,starting_cash,name,closed_at FROM accounts ORDER BY id")
  from app.db.dev_bootstrap import bootstrap
  await bootstrap('dev',os.environ['DATABASE_URL'],after_migrations=True)
  assert await c.fetch("SELECT id,user_id,cash,starting_cash,name,closed_at FROM accounts ORDER BY id")==before
  assert not await c.fetchval("SELECT rolcanlogin FROM pg_roles WHERE rolname='birja_migrator'")
  import secrets
  from sqlalchemy.engine import make_url
  from sqlalchemy.ext.asyncio import create_async_engine
  from app.db.portfolio_migrate import require_migrator
  password=secrets.token_hex(32)
  await c.execute(await c.fetchval("SELECT format('ALTER ROLE birja_migrator LOGIN PASSWORD %L',$1::text)",password))
  e=create_async_engine(make_url(os.environ['DATABASE_URL']).set(username='birja_migrator',password=password))
  try:
   for change,undo,reason in [
    ('GRANT CREATE ON SCHEMA public TO PUBLIC','REVOKE CREATE ON SCHEMA public FROM PUBLIC','Unsafe migration schema'),
    ('ALTER ROLE birja_app CREATEROLE','ALTER ROLE birja_app NOCREATEROLE','Unsafe migration schema'),
    ("UPDATE alembic_version SET version_num='0018'","UPDATE alembic_version SET version_num='0026'",'migration_only')]:
    await c.execute(change)
    try:
     async with e.connect() as x:
      try:
       # Partial revisions are valid for the migration client, never the app.
       if reason=='migration_only':await require_schema(x)
       else:await require_migrator(x)
      except (ValueError,SchemaAdmissionError) as exc:assert reason in str(exc)
      else:raise AssertionError('unsafe migration admitted')
    finally:await c.execute(undo)
   await c.execute("CREATE FUNCTION public.reject_stock_record_mutation(bigint) RETURNS text LANGUAGE sql AS 'SELECT NULL::text'")
   await c.execute('ALTER FUNCTION public.reject_stock_record_mutation(bigint) OWNER TO birja_migrator')
   try:
    async with e.connect() as x:
     try:await require_migrator(x)
     except ValueError as exc:assert 'Unexpected migration routine' in str(exc)
     else:raise AssertionError('unknown overload admitted')
   finally:await c.execute('DROP FUNCTION public.reject_stock_record_mutation(bigint)')
  finally:
   await e.dispose()
   await c.execute('ALTER ROLE birja_migrator NOLOGIN PASSWORD NULL')
  assert await c.fetch("SELECT id,user_id,cash,starting_cash,name,closed_at FROM accounts ORDER BY id")==before
  print('actual_dev_final_roles_exact_cash_baseline_repeat_no_grant=true',flush=True)
 finally:await c.close()
asyncio.run(main())
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="birja-backend-runtime:pr31-dns")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG") if key in os.environ}
    env.update(COMPOSE_DISABLE_ENV_FILE="1", ENV="dev", POSTGRES_USER="birja",
               POSTGRES_DB="birja", POSTGRES_PASSWORD="syntheticDevProof17",
               REDIS_PASSWORD="syntheticRedisProof17",
               OTP_HMAC_SECRET="synthetic-dev-proof-otp-" + "a" * 64,
               JWT_SECRET="synthetic-dev-proof-jwt-" + "b" * 64,
               EMAIL_BACKEND="console", PRICE_SOURCE="fake",
               STOCK_DATA_ENABLED="false", STOCK_ACTIONS_ENABLED="false")

    def command(argv, *, input=None, check=True):
        result = subprocess.run(argv, env=env, input=input, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, timeout=240)
        print(result.stdout, flush=True)
        if check:
            result.check_returncode()
        return result

    command(["docker", "image", "inspect", args.image, "--format", "{{.Id}}"])
    with tempfile.TemporaryDirectory(prefix="birja-phase12-dev-financial-") as directory:
        for lane in (("0015", "0016") if args.staged else ("fresh", "upgrade")):
            tick = time.monotonic()
            project = "birja-phase12-dev-" + lane + "-test"
            for kind in ("container", "network", "volume"):
                assert not command(["docker", kind, "ls", "-q", "--filter",
                                    "label=com.docker.compose.project=" + project]).stdout.strip(), "Refuse preexisting owned resources"
            services = {n: {"restart": "no"} for n in ("postgres", "redis", "backend", "scheduler", "frontend")}
            for name in ("backend", "scheduler"):
                services[name]["image"] = args.image
                # Exercise the complete selected image. A dev bind would
                # replace its authenticated source with host-owned files,
                # whose private checkout modes need not be readable by app.
                services[name]["volumes"] = "RESET"
            services["backend"]["ports"] = "RESET"
            services["frontend"]["ports"] = "RESET"
            override = Path(directory) / (lane + ".yml")
            override.write_text("services:\n" + "".join("  " + name + ":\n" + "".join(
                "    " + key + ": " + ("!reset []" if value == "RESET" else json.dumps(value)) + "\n"
                for key, value in values.items()) for name, values in services.items()))
            dc = ["docker", "compose", "-p", project, "--env-file", "/dev/null", "-f",
                  str(ROOT / "docker-compose.yml"), "-f", str(ROOT / "docker-compose.override.yml"), "-f", str(override)]

            def sql(statement):
                return command(dc + ["exec", "-T", "postgres", "psql", "-U", "birja", "-d", "birja",
                                     "-v", "ON_ERROR_STOP=1", "-Atc", statement]).stdout.strip()

            def refused(expected):
                result = command(dc + ["run", "--rm", "--no-deps", "-T", "backend", "python", "-m", "app.db.dev_bootstrap", "--after-migrations"], check=False)
                assert result.returncode != 0 and expected in result.stdout, result.stdout

            try:
                command(dc + ["up", "--no-build", "-d", "--wait", "postgres", "redis"])
                if lane != "fresh":
                    command(dc + ["run", "--rm", "--no-deps", "backend", "python", "-m", "app.db.dev_bootstrap"])
                    command(dc + ["run", "--rm", "--no-deps", "backend", "alembic", "upgrade", "0014"])
                    sql("INSERT INTO users(email) VALUES ('retained@example.test'); INSERT INTO accounts(user_id,cash,starting_cash) SELECT id,321.12,8765 FROM users")
                if lane == "upgrade":
                    command(dc + ["run", "--rm", "--no-deps", "-T", "backend", "python", "-"],
                            input=stage_program("0024"))
                    command(dc + ["run", "--rm", "--no-deps", "backend", "python", "-m",
                                  "app.db.dev_bootstrap", "--after-migrations"])
                    assert sql("SELECT version_num FROM alembic_version") == "0024"
                    assert sql("SELECT to_regclass('public.stock_catalog_generations') IS NULL") == "t"
                    command(dc + ["run", "--rm", "--no-deps", "-T", "backend", "python", "-"],
                            input=stage_program("0025"))
                    command(dc + ["run", "--rm", "--no-deps", "-T", "backend", "python", "-m",
                                  "app.db.dev_bootstrap", "--after-migrations"])
                    assert sql("SELECT to_regclass('public.stock_catalog_instruments') IS NULL") == "t"
                    command(dc + ["run", "--rm", "--no-deps", "-T", "backend", "python", "-"],
                            input=retained_catalog_program())
                if lane in ("0015", "0016"):
                    command(dc + ["run", "--rm", "--no-deps", "-T", "backend", "python", "-"],
                            input=stage_program(lane))
                    before = sql("SELECT cash||':'||starting_cash FROM accounts")
                    refused("migration_only; refusing normal dev bootstrap")
                    prefix = "\\set bootstrap 'birja'\n\\set db_name 'birja'\n\\set apply false\n"
                    result = command(dc + ["exec", "-T", "postgres", "psql", "-XqAt", "-U",
                        "birja", "-d", "birja", "-v", "ON_ERROR_STOP=1"],
                        input=prefix + (ROOT / "deploy/db/bootstrap-roles.sql").read_text(), check=False)
                    assert result.returncode and "migration_only" in result.stdout
                    assert sql("SELECT cash||':'||starting_cash FROM accounts") == before
                command(dc + ["run", "--rm", "--no-deps", "backend", "python", "-m", "app.db.dev_bootstrap", "--migrate"])
                prefix = "\\set bootstrap 'birja'\n\\set db_name 'birja'\n\\set apply true\n" + "".join(
                    "\\set " + role + "_password '" + "c" * 64 + "'\n"
                    for role in ("app", "scheduler", "migrator"))
                command(dc + ["exec", "-T", "postgres", "psql", "-XqAt", "-U", "birja",
                              "-d", "birja", "-v", "ON_ERROR_STOP=1"],
                        input=prefix + (ROOT / "deploy/db/bootstrap-roles.sql").read_text())
                command(dc + ["run", "--rm", "--no-deps", "-T", "backend", "python", "-"], input=financial_program())
                command(dc + ["run", "--rm", "--no-deps", "-T", "backend", "python", "-m", "app.db.dev_bootstrap", "--after-migrations"])
                assert sql("SELECT version_num FROM alembic_version") == "0026"
                assert sql("SELECT cash||':'||starting_cash FROM accounts WHERE user_id=(SELECT id FROM users WHERE email='bootstrap@example.test')") == "124.45000000:7777.00000000"
                if lane != "fresh":
                    assert sql("SELECT cash||':'||starting_cash FROM accounts WHERE user_id=(SELECT id FROM users WHERE email='retained@example.test')") == "321.12000000:8765.00000000"
                sql("ALTER ROLE birja_migrator CREATEROLE")
                refused("Unsafe existing dev migration owner; refusing repair")
                assert sql("SELECT rolcreaterole FROM pg_roles WHERE rolname='birja_migrator'") == "t"
                sql("ALTER ROLE birja_migrator NOCREATEROLE; CREATE ROLE dev_bootstrap_probe NOLOGIN; GRANT birja_migrator TO dev_bootstrap_probe")
                refused("Unsafe existing dev migration owner; refusing repair")
                assert sql("SELECT count(*) FROM pg_auth_members WHERE roleid='birja_migrator'::regrole OR member='birja_migrator'::regrole") == "1"
                sql("REVOKE birja_migrator FROM dev_bootstrap_probe; ALTER TABLE stock_action_events OWNER TO dev_bootstrap_probe")
                refused("management catalogue mismatch")
                assert sql("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='stock_action_events'::regclass") == "dev_bootstrap_probe"
                print(lane + "_ordinary_dev_financial_and_unsafe_role_membership_object_refusals=true seconds=" + str(round(time.monotonic() - tick, 3)), flush=True)
            finally:
                command(dc + ["down", "--volumes", "--remove-orphans"])
                for kind in ("container", "network", "volume"):
                    assert not command(["docker", kind, "ls", "-q", "--filter",
                                        "label=com.docker.compose.project=" + project]).stdout.strip()
    print("all_owned_dev_financial_resources_clean=true", flush=True)


if __name__ == "__main__":
    main()
