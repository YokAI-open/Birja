#!/usr/bin/env bash
# Paired encrypted recovery against a disposable PostgreSQL and cache.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON="${BIRJA_RECEIPT_PYTHON:-$ROOT/backend/.venv/bin/python}"
contracts="$ROOT/deploy/tests/test-portfolio-recovery-contracts.py"
restic_path=/tmp/birja-test-tools/restic-0.19.1/restic
test -x "$PYTHON"
printf '%s  %s\n' 20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639 "$restic_path" |
  sha256sum --check --status
stage=$(mktemp -d /tmp/birja-catalog-finance-recovery.XXXXXXXX)
postgres=''
redis=''
cleanup() {
  if [[ -n "$postgres" ]]; then docker rm -f "$postgres" >/dev/null; fi
  if [[ -n "$redis" ]]; then docker rm -f "$redis" >/dev/null; fi
  rm -r -- "$stage"
}
trap cleanup EXIT
chmod 755 "$stage"
mkdir "$stage/retained"
"$PYTHON" "$contracts" --materialize-catalog "$stage/retained"
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=birja-local-test \
  -addext subjectAltName=IP:127.0.0.1 -keyout "$stage/server.key" -out "$stage/ca.crt" >/dev/null 2>&1
chmod 644 "$stage/ca.crt"
chmod 600 "$stage/server.key"
chown 70:70 "$stage/server.key"
postgres=$(docker run -d --pull never --user 70:70 \
  --tmpfs /var/lib/postgresql:uid=70,gid=70,mode=0750 \
  -e PGDATA=/var/lib/postgresql/18/docker -e POSTGRES_USER=birja_test \
  -e POSTGRES_PASSWORD=test -e POSTGRES_DB=birja_test \
  -v "$stage/ca.crt:/fixture-cert.crt:ro" -v "$stage/server.key:/fixture-key.key:ro" \
  -p 127.0.0.1:55434:5432 \
  cgr.dev/chainguard/postgres@sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de \
  -c ssl=on -c ssl_cert_file=/fixture-cert.crt -c ssl_key_file=/fixture-key.key)
for try in {1..30}; do
  if docker exec "$postgres" pg_isready -h 127.0.0.1 -U birja_test -d birja_test >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
sql() { docker exec -i "$postgres" psql -XqAt -v ON_ERROR_STOP=1 -U birja_test "$@"; }
sql -d birja_test <<'SQL'
CREATE ROLE birja_migrator LOGIN NOINHERIT PASSWORD 'fixture-migrator-only';
CREATE ROLE birja_app LOGIN NOINHERIT PASSWORD 'test-app';
CREATE ROLE birja_scheduler LOGIN NOINHERIT PASSWORD 'test-scheduler';
CREATE ROLE birja_action_operator NOLOGIN NOINHERIT;
GRANT USAGE, CREATE ON SCHEMA public TO birja_migrator;
REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler;
GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;
SQL
export ENV=test DATABASE_SSL_CA_FILE="$stage/ca.crt" REDIS_URL=redis://:test@127.0.0.1:56381/0
export OTP_HMAC_SECRET=unused-test-otp-value-012345678901234567890 JWT_SECRET=unused-test-jwt-value-012345678901234567890
export BIRJA_CATALOG_TEST_CONTAINER="$postgres"
export DATABASE_URL=postgresql+asyncpg://birja_test:test@127.0.0.1:55434/birja_test
migration_url=postgresql+asyncpg://birja_migrator:fixture-migrator-only@127.0.0.1:55434/birja_test
migrate() {
  local root="$1" revision="$2"
  (cd "$root/backend" && PYTHONPATH="$PWD" DATABASE_URL="$migration_url" "$PYTHON" -m alembic upgrade "$revision")
}
bootstrap() {
  sql -d birja_test -v bootstrap=birja_test -v db_name=birja_test -v apply=on \
    -v app_password=test-app -v scheduler_password=test-scheduler \
    -v migrator_password=fixture-migrator-only < "$1/deploy/db/bootstrap-roles.sql" > "$stage/bootstrap.log"
}
seed_retained() {
  (cd "$stage/retained" && PYTHONPATH="$PWD/backend" "$PYTHON" - "$1" > "$stage/receipt-$1.json" <<'PY'
import asyncio
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('stock_fixture', 'deploy/tests/stock-execution-fixture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
asyncio.run(fixture.reported_receipt_fixture(sys.argv[1]))
PY
  )
}
start_cache() {
  redis=$(docker run -d --pull never --network none \
    cgr.dev/chainguard/redis@sha256:26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48 \
    --save '' --appendonly no)
  for try in {1..10}; do
    if [[ "$(docker exec "$redis" redis-cli ping 2>/dev/null)" == PONG ]]; then return; fi
    sleep 1
  done
  return 1
}

openssl rand -hex 32 > "$stage/restic-password"
restic=("$restic_path" --repo "$stage/repository" --password-file "$stage/restic-password" --no-cache)
"${restic[@]}" init >/dev/null
canary=fixture_catalog_finance_ephemeral_quote_bbb5b660b739
start_cache
test "$(docker exec "$redis" redis-cli SET fixture:stock:quote:FQA "$canary" EX 600)" = OK

round_trip() {
  local root="$1" revision="$2" snapshot
  mkdir "$stage/$revision"
  "$PYTHON" "$contracts" --catalog-snapshot "$root" "$revision" "$stage" "$restic_path"
  snapshot=$(
    cd "$stage/$revision"
    "${restic[@]}" backup --json database.dump manifest.json |
      "$PYTHON" -c 'import json,sys; print(*(row["snapshot_id"] for row in map(json.loads,sys.stdin) if row.get("message_type") == "summary"))'
  )
  [[ "$snapshot" =~ ^[a-f0-9]{64}$ ]]
  "${restic[@]}" restore --verify "$snapshot" --target "$stage/restored-$revision" >/dev/null
  cmp "$stage/$revision/database.dump" "$stage/restored-$revision/database.dump"
  cmp "$stage/$revision/manifest.json" "$stage/restored-$revision/manifest.json"
  docker exec "$postgres" createdb -U birja_test birja_restore_test
  sql -d birja_restore_test -c \
    'REVOKE CREATE ON SCHEMA public FROM PUBLIC; GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator;'
  docker exec -i "$postgres" pg_restore -U birja_test -d birja_restore_test --role=birja_migrator \
    --no-acl --no-owner --exit-on-error --single-transaction < "$stage/restored-$revision/database.dump"
  "$PYTHON" "$contracts" --catalog-restore "$root" "$stage/restored-$revision/manifest.json"
  docker exec "$postgres" pg_dump -U birja_test -d birja_restore_test --data-only > "$stage/$revision.sql"
  "$PYTHON" "$contracts" --catalog-cache-absent "$stage" "$revision" "$canary"
}

retained="$stage/retained"
migrate "$retained" 0023
bootstrap "$retained"
seed_retained alpaca
migrate "$retained" 0024
bootstrap "$retained"
seed_retained nasdaq-rss
migrate "$retained" 0025
bootstrap "$retained"
sql -d birja_test <<'SQL'
SET ROLE birja_migrator;
INSERT INTO stock_catalog_generations
  (manifest_sha256,mode,published_at,valid_until,is_active,sources,coverage)
VALUES(repeat('1',64),'fixture','2000-01-01Z','2000-01-02Z',false,'{"fixture":"retained"}','{"included":0}');
SQL
round_trip "$retained" 0025
docker exec "$postgres" dropdb -U birja_test birja_restore_test

migrate "$ROOT" 0026
bootstrap "$ROOT"
PYTHONPATH="$ROOT/backend" "$PYTHON" "$contracts" --catalog-economics seed "$stage/current-receipts.json"
test "$(docker exec "$redis" redis-cli GET fixture:stock:quote:FQA)" = "$canary"
round_trip "$ROOT" 0026
docker rm -f "$redis" >/dev/null
redis=''
start_cache
test "$(docker exec "$redis" redis-cli DBSIZE)" = 0
PYTHONPATH="$ROOT/backend" DATABASE_URL="${DATABASE_URL%birja_test}birja_restore_test" \
  "$PYTHON" "$contracts" --catalog-economics replay "$stage/current-receipts.json"
if (cd backend && PYTHONPATH="$PWD" DATABASE_URL="${migration_url%birja_test}birja_restore_test" \
    "$PYTHON" -m alembic downgrade 0025) >"$stage/downgrade.log" 2>&1; then
  exit 1
fi
rg -q 'Catalog finance downgrade refused' "$stage/downgrade.log"
test "$(sql -d birja_restore_test -c 'SELECT version_num FROM alembic_version')" = 0026
"${restic[@]}" check --read-data >/dev/null
printf '%s\n' 'retained_0025_exact=true successor_0026_exact=true redis_display_cache_excluded=true'
printf '%s\n' 'cold_fill_and_actions_replay_exact=true populated_downgrade_refused=true encrypted_integrity=true'
