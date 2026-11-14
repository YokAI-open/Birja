#!/usr/bin/env python3
"""Real ordinary-Compose dividend authority, on exclusively owned dev test stacks."""

import argparse
import json
import os
import runpy
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def financial_program():
    program = runpy.run_path(str(ROOT / "deploy/tests/dividend-execution-fixture.py"))["PROGRAM"]
    program = program.split("asyncio.run(main())")[0]
    # A new synthetic ordinary account receives the original10000 grant, once.
    old = "INSERT INTO accounts(user_id,cash,starting_cash) VALUES ($1,100,10000)"
    assert program.count(old) == 1
    program = program.replace(old, old.replace("$1,100,", "$1,10000,"))
    return program + r'''
import os
def service_engine(role=None):
 return create_async_engine(os.environ['DATABASE_URL'])

async def actual_dev_financial():
 owner=await asyncpg.connect(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://','postgresql://'))
 try:
  assert await owner.fetchval("SELECT current_database()='birja' AND current_user='birja'")
  event=await prepare(owner)
  work=await target(owner,event)
  original=await service_work(work)
  assert original['outcome']=='original'
  assert await service_work(work)==original
  uid=await owner.fetchval('SELECT user_id FROM stock_dividend_entitlements WHERE id=$1',work['entitlement_id'])
  cash=lambda:owner.fetchval('SELECT cash FROM accounts WHERE user_id=$1',uid)
  assert await cash()==D(10001)
  before=await owner.fetchrow('SELECT * FROM stock_dividend_payments WHERE id=$1',original['payment_id'])
  await revise(owner,event,'1.5')
  await cycle()
  correction=await service_work(await target(owner,event))
  assert correction['outcome']=='applied' and await cash()==D(10003)
  assert await service_work(await target(owner,event))==correction
  revision=await revise(owner,event,'0.5',uncertain=True)
  await cycle()
  held=await service_work({'payment_id':original['payment_id'],'revision_fingerprint':revision},hold=True)
  assert held['outcome']=='held_uncertain' and await cash()==D(10003)
  count=await owner.fetchval('SELECT count(*) FROM stock_dividend_decisions')
  await cycle()
  assert await owner.fetchval('SELECT count(*) FROM stock_dividend_decisions')==count
  await revise(owner,event,'2',reconcile=True)
  await cycle()
  successor=await service_work(await target(owner,event))
  assert successor['outcome']=='applied' and await cash()==D(10004)
  assert await service_work(await target(owner,event))==successor
  await cycle()
  assert await cash()==D(10004)
  assert dict(await owner.fetchrow('SELECT * FROM stock_dividend_payments WHERE id=$1',original['payment_id']))==dict(before)
  assert await owner.fetchval('SELECT count(*) FROM stock_dividend_payments')==1
  assert await owner.fetchval('SELECT count(*) FROM stock_dividend_decisions')==3
  assert await owner.fetchval('SELECT starting_cash FROM accounts WHERE user_id=$1',uid)==D(10000)
  engine=service_engine()
  try:
   async with async_sessionmaker(engine)() as db:
    page=await list_event_history(db,user_id=uid,limit=100)
    assert len(page.items)==4
    assert sum(D(x.cash_delta) for x in page.items)==D(4)
  finally:await engine.dispose()
  print('actual_ordinary_dev_original_hold_correction_worker_history_replay=true cash10004_starting10000_original_unchanged=true',flush=True)
 finally:await owner.close()
asyncio.run(actual_dev_financial())
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="birja-backend-test:phase05-07")
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
    with tempfile.TemporaryDirectory(prefix="birja-phase10-dev-financial-") as directory:
        for lane in ("fresh", "upgrade"):
            tick = time.monotonic()
            project = "birja-phase10-dev-" + lane + "-test"
            for kind in ("container", "network", "volume"):
                assert not command(["docker", kind, "ls", "-q", "--filter",
                                    "label=com.docker.compose.project=" + project]).stdout.strip(), "Refuse preexisting owned resources"
            services = {n: {"restart": "no"} for n in ("postgres", "redis", "backend", "scheduler", "frontend")}
            for name in ("backend", "scheduler"):
                services[name]["image"] = args.image
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

            def refused():
                result = command(dc + ["exec", "-T", "backend", "python", "-m", "app.db.dev_bootstrap", "--after-migrations"], check=False)
                assert result.returncode != 0 and "refusing" in result.stdout.lower(), result.stdout

            try:
                command(dc + ["up", "--no-build", "-d", "--wait", "postgres", "redis"])
                if lane == "upgrade":
                    command(dc + ["run", "--rm", "--no-deps", "backend", "alembic", "upgrade", "0013"])
                command(dc + ["up", "--no-build", "-d", "--wait", "backend"])
                command(dc + ["exec", "-T", "backend", "python", "-"], input=financial_program())
                command(dc + ["exec", "-T", "backend", "python", "-m", "app.db.dev_bootstrap", "--after-migrations"])
                assert sql("SELECT cash||':'||starting_cash FROM accounts") == "10004.00000000:10000.00000000"
                sql("ALTER ROLE birja_migrator CREATEROLE")
                refused()
                assert sql("SELECT rolcreaterole FROM pg_roles WHERE rolname='birja_migrator'") == "t"
                sql("ALTER ROLE birja_migrator NOCREATEROLE; CREATE ROLE dev_bootstrap_probe NOLOGIN; GRANT birja_migrator TO dev_bootstrap_probe")
                refused()
                assert sql("SELECT count(*) FROM pg_auth_members WHERE roleid='birja_migrator'::regrole OR member='birja_migrator'::regrole") == "1"
                sql("REVOKE birja_migrator FROM dev_bootstrap_probe; ALTER TABLE stock_action_events OWNER TO dev_bootstrap_probe")
                refused()
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
