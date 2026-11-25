#!/usr/bin/env bash
# Runs only one local synthetic PostgreSQL 18 fixture and clone.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON="${BIRJA_RECEIPT_PYTHON:-$ROOT/backend/.venv/bin/python}"
test -x "$PYTHON"
stage=$(mktemp -d /tmp/birja-stock-tls-check.XXXXXXXX)
container_id=''
cleanup() {
  if [ -n "$container_id" ]; then docker rm -f "$container_id" >/dev/null; fi
  rm -r -- "$stage"
}
trap cleanup EXIT
chmod 755 "$stage"
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=birja-local-test -addext subjectAltName=IP:127.0.0.1 -keyout "$stage/server.key" -out "$stage/ca.crt" >/dev/null 2>&1
chmod 644 "$stage/ca.crt"
chmod 600 "$stage/server.key"
chown 70:70 "$stage/server.key"
container_id=$(docker run -d --pull never --name birja-phase18-receipts-check --user 70:70 --tmpfs /var/lib/postgresql:uid=70,gid=70,mode=0750 -e PGDATA=/var/lib/postgresql/18/docker -e POSTGRES_USER=birja_test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=birja_test -v "$stage/ca.crt:/fixture-cert.crt:ro" -v "$stage/server.key:/fixture-key.key:ro" -p 127.0.0.1:55434:5432 cgr.dev/chainguard/postgres@sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de -c ssl=on -c ssl_cert_file=/fixture-cert.crt -c ssl_key_file=/fixture-key.key)
for try in {1..30}; do
  if docker exec "$container_id" pg_isready -h 127.0.0.1 -U birja_test -d birja_test >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec -i "$container_id" psql -v ON_ERROR_STOP=1 -U birja_test -d birja_test >/dev/null <<'SQL'
CREATE ROLE birja_migrator LOGIN NOINHERIT PASSWORD 'fixture-migrator-only';
CREATE ROLE birja_app LOGIN NOINHERIT PASSWORD 'test-app';
CREATE ROLE birja_scheduler LOGIN NOINHERIT PASSWORD 'test-scheduler';
CREATE ROLE birja_action_operator NOLOGIN NOINHERIT;
GRANT USAGE, CREATE ON SCHEMA public TO birja_migrator;
REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler;
GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;
SQL
export ENV=test DATABASE_SSL_CA_FILE="$stage/ca.crt" REDIS_URL=redis://:test@127.0.0.1:56381/0 OTP_HMAC_SECRET=unused-test-otp-value-012345678901234567890 JWT_SECRET=unused-test-jwt-value-012345678901234567890
export PYTHONPATH="$PWD/backend" BIRJA_MANIFEST_TEST_CONTAINER="$container_id" BIRJA_FIXTURE_STAGE="$stage"
migration_url=postgresql+asyncpg://birja_migrator:fixture-migrator-only@127.0.0.1:55434/birja_test
admin_url=postgresql+asyncpg://birja_test:test@127.0.0.1:55434/birja_test
migrate() { (cd backend && DATABASE_URL="$migration_url" "$PYTHON" -m alembic upgrade "$1") 2>"$stage/migrate.log"; }
migrate 0023
docker exec -i "$container_id" psql -X --quiet -v ON_ERROR_STOP=1 -U birja_test -d birja_test -v bootstrap=birja_test -v db_name=birja_test -v apply=on -v app_password=test-app -v scheduler_password=test-scheduler -v migrator_password=fixture-migrator-only < deploy/db/bootstrap-roles.sql >"$stage/bootstrap.log"
seed() { DATABASE_URL="$admin_url" "$PYTHON" - "$1" >"$2" <<'PY'
import asyncio, importlib.util, sys
spec=importlib.util.spec_from_file_location('stock_fixture','deploy/tests/stock-execution-fixture.py')
fixture=importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
asyncio.run(fixture.reported_receipt_fixture(sys.argv[1]))
PY
}
restore_and_replay() {
  local snapshot
  docker exec "$container_id" pg_dump -U birja_test -d birja_test -Fc > "$stage/database.dump"
  snapshot=$(
    cd "$stage"
    "${restic[@]}" backup --json database.dump |
      "$PYTHON" -c 'import json,sys; print(*(row["snapshot_id"] for row in map(json.loads, sys.stdin) if row.get("message_type") == "summary"))'
  )
  [[ "$snapshot" =~ ^[a-f0-9]{64}$ ]]
  "${restic[@]}" restore --verify "$snapshot" --target "$stage/restored" >/dev/null
  cmp "$stage/database.dump" "$stage/restored/database.dump"
  docker exec "$container_id" createdb -U birja_test birja_restore_test
  docker exec "$container_id" psql -X --quiet -v ON_ERROR_STOP=1 -U birja_test -d birja_restore_test -c 'REVOKE CREATE ON SCHEMA public FROM PUBLIC; GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator;'
  docker exec -i "$container_id" pg_restore -U birja_test -d birja_restore_test --role=birja_migrator --no-acl --no-owner --exit-on-error --single-transaction < "$stage/restored/database.dump"
  rm -- "$stage/database.dump" "$stage/restored/database.dump"
  rmdir -- "$stage/restored"
  DATABASE_URL="${admin_url%birja_test}birja_restore_test" "$PYTHON" - "$@" <<'PY'
import asyncio, importlib.util, json, os, subprocess, sys
from pathlib import Path
mode, *files = sys.argv[1:]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result
restore=module('restore', 'deploy/verify-restore.py')
fixture=module('fixture', 'deploy/tests/stock-execution-fixture.py')
container=os.environ['BIRJA_MANIFEST_TEST_CONTAINER']
def isolated_sql(dc, query, db=restore.CLONE):
    assert db in ('birja_test', restore.CLONE)
    return subprocess.run(['docker','exec','-i',container,'psql','-XqAt','-v','ON_ERROR_STOP=1','-U','birja_test','-d',db],input=query.encode(),stdout=subprocess.PIPE,check=True).stdout
restore.sql=isolated_sql
source=restore.canonical([], 'birja_test')
assert source['tables']['stock_status_evidence']['count'] == 1
assert source['tables']['stock_fill_facts']['count'] == (1 if mode == 'replay-legacy' else 3)
restore.restore_closure_authority([],source)
restore.verify([],source,quarantined=False)
stage=Path(os.environ['BIRJA_FIXTURE_STAGE'])
before=[]
for name in files:
    before.extend(json.loads((stage/name).read_text().removeprefix('stock_receipts=')))
asyncio.run(fixture.reported_receipt_fixture(mode, before))
PY
}
restic_path=/tmp/birja-test-tools/restic-0.19.1/restic
printf '%s  %s\n' 20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639 "$restic_path" |
  sha256sum --check --status
openssl rand -hex 32 > "$stage/restic-password"
restic=("$restic_path" --repo "$stage/repository" --password-file "$stage/restic-password" --no-cache)
"${restic[@]}" init >/dev/null
seed alpaca "$stage/original.json"
restore_and_replay replay-legacy original.json
docker exec "$container_id" dropdb -U birja_test birja_restore_test
migrate 0024
seed nasdaq-rss "$stage/successor.json"
docker exec "$container_id" psql -U birja_test -d birja_test -v ON_ERROR_STOP=1 -c "UPDATE stock_status_evidence SET event_at=clock_timestamp()-interval '70 seconds',observed_at=clock_timestamp()-interval '69 seconds',valid_until=clock_timestamp()-interval '10 seconds' WHERE source='nasdaq-rss'" >/dev/null
restore_and_replay replay original.json successor.json
if (cd backend && DATABASE_URL="${migration_url%birja_test}birja_restore_test" "$PYTHON" -m alembic downgrade 0023) 2>"$stage/migrate.log"; then
  exit 1
fi
grep -Fq 'Stock halt snapshot downgrade refused; reported evidence is retained' "$stage/migrate.log"
test "$(docker exec "$container_id" psql -XqAt -U birja_test -d birja_restore_test -c 'SELECT version_num FROM alembic_version')" = 0024
"${restic[@]}" check --read-data >/dev/null
printf '%s\n' 'paired_encrypted_snapshot_integrity=true'
printf '%s\n' 'evidence_bearing_downgrade_refused=true retained_candidate_revision=0024'
