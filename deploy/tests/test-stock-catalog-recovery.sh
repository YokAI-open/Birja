#!/usr/bin/env bash
# Disposable catalog and retained financial snapshots, with a separate cache.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON="${BIRJA_RECEIPT_PYTHON:-$ROOT/backend/.venv/bin/python}"
test -x "$PYTHON"
stage=$(mktemp -d /tmp/birja-catalog-tls-check.XXXXXXXX)
postgres=''
redis=''
cleanup() {
  if [ -n "$postgres" ]; then docker rm -f "$postgres" >/dev/null; fi
  if [ -n "$redis" ]; then docker rm -f "$redis" >/dev/null; fi
  rm -r -- "$stage"
}
trap cleanup EXIT
chmod 755 "$stage"
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
export PYTHONPATH="$PWD/backend" BIRJA_CATALOG_TEST_CONTAINER="$postgres"
migration_url=postgresql+asyncpg://birja_migrator:fixture-migrator-only@127.0.0.1:55434/birja_test
admin_url=postgresql+asyncpg://birja_test:test@127.0.0.1:55434/birja_test
migrate() { (cd backend && DATABASE_URL="$migration_url" "$PYTHON" -m alembic upgrade "$1"); }
bootstrap() {
  sql -d birja_test -v bootstrap=birja_test -v db_name=birja_test -v apply=on \
    -v app_password=test-app -v scheduler_password=test-scheduler \
    -v migrator_password=fixture-migrator-only < deploy/db/bootstrap-roles.sql > "$stage/bootstrap.log"
}
seed_receipt() {
  DATABASE_URL="$admin_url" "$PYTHON" - "$1" > "$2" <<'PY'
import asyncio
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('stock_fixture', 'deploy/tests/stock-execution-fixture.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
asyncio.run(fixture.reported_receipt_fixture(sys.argv[1]))
PY
}

migrate 0023
bootstrap
seed_receipt alpaca "$stage/legacy-receipt.json"
migrate 0024
bootstrap
seed_receipt nasdaq-rss "$stage/reported-receipts.json"

restic_path=/tmp/birja-test-tools/restic-0.19.1/restic
printf '%s  %s\n' 20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639 "$restic_path" |
  sha256sum --check --status
openssl rand -hex 32 > "$stage/restic-password"
restic=("$restic_path" --repo "$stage/repository" --password-file "$stage/restic-password" --no-cache)
"${restic[@]}" init >/dev/null

round_trip() {
  local revision="$1" snapshot
  mkdir "$stage/$revision"
  "$PYTHON" - "$revision" "$stage" "$restic_path" <<'PY'
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time

spec = importlib.util.spec_from_file_location('producer', 'deploy/backup-snapshot.py')
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)
container = os.environ['BIRJA_CATALOG_TEST_CONTAINER']
revision, stage, restic_path = sys.argv[1:]
assert revision in ('0024', '0025')
stage = Path(stage)
docker = shutil.which('docker')
assert docker
job = producer.Job({
    '_synthetic': True, 'state_dir': str(stage), 'password_file': str(stage / 'restic-password'),
    'repository': str(stage / 'repository'), 'source_project': 'birja-phase19-local-fixture',
    'docker_binary': docker, 'restic_binary': restic_path, 'db_user': 'birja_test',
    'db_name': 'birja_test', 'release': 'fixture-phase19', 'timeout_seconds': 60,
    'max_stage_bytes': 32 * 1024 * 1024,
})
job.dc = [docker, 'exec', '-i', container]
job.bundle = stage / revision
job.start_utc = producer.utc()
job.data_epoch = int(time.time())
job.snapshot()
source = json.loads((job.bundle / 'manifest.json').read_text())
assert source['revision'] == revision
assert source['tables']['stock_fill_facts']['count'] == 3
PY
  snapshot=$(
    cd "$stage/$revision"
    "${restic[@]}" backup --json database.dump manifest.json |
      "$PYTHON" -c 'import json,sys; print(*(row["snapshot_id"] for row in map(json.loads,sys.stdin) if row.get("message_type") == "summary"))'
  )
  [[ "$snapshot" =~ ^[a-f0-9]{64}$ ]]
  if [ "$revision" = 0025 ]; then
    docker rm -f "$redis" >/dev/null
    redis=''
  fi
  "${restic[@]}" restore --verify "$snapshot" --target "$stage/restored-$revision" >/dev/null
  cmp "$stage/$revision/database.dump" "$stage/restored-$revision/database.dump"
  cmp "$stage/$revision/manifest.json" "$stage/restored-$revision/manifest.json"
  docker exec "$postgres" createdb -U birja_test birja_restore_test
  sql -d birja_restore_test -c \
    'REVOKE CREATE ON SCHEMA public FROM PUBLIC; GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator;'
  docker exec -i "$postgres" pg_restore -U birja_test -d birja_restore_test --role=birja_migrator \
    --no-acl --no-owner --exit-on-error --single-transaction < "$stage/restored-$revision/database.dump"
  "$PYTHON" - "$stage/restored-$revision/manifest.json" <<'PY'
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

spec = importlib.util.spec_from_file_location('restore', 'deploy/verify-restore.py')
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)
container = os.environ['BIRJA_CATALOG_TEST_CONTAINER']

def isolated_sql(dc, query, db=restore.CLONE):
    assert db == restore.CLONE
    return subprocess.run(
        ['docker', 'exec', '-i', container, 'psql', '-XqAt', '-v', 'ON_ERROR_STOP=1',
         '-U', 'birja_test', '-d', db], input=query.encode(), stdout=subprocess.PIPE, check=True,
    ).stdout

restore.sql = isolated_sql
source = json.loads(Path(sys.argv[1]).read_text())
restore.restore_closure_authority([], source)
restore.verify([], source, quarantined=False)
PY
}

round_trip 0024
docker exec "$postgres" dropdb -U birja_test birja_restore_test
migrate 0025
bootstrap
sql -d birja_test <<'SQL'
BEGIN;
SET LOCAL ROLE birja_migrator;
INSERT INTO stock_catalog_generations
    (manifest_sha256, mode, published_at, valid_until, is_active, sources, coverage)
VALUES
    (repeat('1',64),'fixture','2000-01-01Z','2000-01-02Z',false,'{"fixture":"old"}','{"included":1}'),
    (repeat('2',64),'fixture','2001-01-01Z','2001-01-02Z',true,'{"fixture":"new"}','{"included":1}');
INSERT INTO stock_catalog_securities (identity_key,created_at)
VALUES ('fixture:first-class','2000-01-01Z'),('fixture:replacement-class','2001-01-01Z');
INSERT INTO stock_catalog_admissions (artifact,reference,reviewed_at,valid_until,fields,scope,is_fixture)
VALUES ('fixture.provider','fixture:provider-approval','2000-01-01Z','2001-01-02Z',
        '{"provider_asset_id":["storage","backup"]}','{"venue":"NASDAQ"}',true);
INSERT INTO stock_catalog_listings (
    generation_id,security_id,ticker,normalized_ticker,company_name,normalized_name,listing_exchange,
    share_class,classification,state,reason,source,row_key,row_digest,evidence_digest,evidence_at,valid_until,
    directory_admission_id,name_admission_id,classification_admission_id,
    provider_asset_id,provider_symbol,provider_evidence_digest,provider_verified_at,provider_valid_until,
    provider_admission_id,unit_evidence_digest,unit_evidence_at,currency,units_per_share
)
SELECT g.id,s.id,'ZXFIX','ZXFIX','Fixture '||g.id,'fixture '||g.id,'NASDAQ',
       'Common','common_stock','active','fixture','nasdaqlisted','fixture:'||g.id,
       repeat('a',64),repeat('b',64),g.published_at,g.valid_until,
       a.id,a.id,a.id,'fixture-asset-'||s.id,'ZXFIX',repeat('c',64),
       g.published_at,g.valid_until,a.id,repeat('d',64),g.published_at,'USD',1
FROM stock_catalog_generations g JOIN stock_catalog_securities s ON s.id=g.id
CROSS JOIN stock_catalog_admissions a;
INSERT INTO stock_catalog_aliases(listing_id,security_id,namespace,symbol,normalized_symbol,verified_at,valid_until)
SELECT id,security_id,'nasdaq','ZXFIX','ZXFIX',evidence_at,valid_until FROM stock_catalog_listings;
COMMIT;
SQL
redis=$(docker run -d --pull never --network none \
  cgr.dev/chainguard/redis@sha256:26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48 \
  --save '' --appendonly no)
for try in {1..10}; do
  if [ "$(docker exec "$redis" redis-cli ping 2>/dev/null)" = PONG ]; then break; fi
  sleep 1
done
canary=fixture_phase19_ephemeral_quote_54987cc6731a
test "$(docker exec "$redis" redis-cli SET fixture:stock:quote:ZXFIX "$canary" EX 300)" = OK
test "$(docker exec "$redis" redis-cli GET fixture:stock:quote:ZXFIX)" = "$canary"
round_trip 0025
docker exec -i "$postgres" pg_restore --data-only --file=- \
  < "$stage/restored-0025/database.dump" > "$stage/extracted-data.sql"
docker exec "$postgres" pg_dump -U birja_test -d birja_restore_test --data-only \
  > "$stage/clone-data.sql"
"$PYTHON" - "$stage" "$canary" <<'PY'
import json
from pathlib import Path
import sys

stage = Path(sys.argv[1])
canary = sys.argv[2].encode()
for artifact in (
    'restored-0024/database.dump', 'restored-0024/manifest.json',
    'restored-0025/database.dump', 'restored-0025/manifest.json',
    'extracted-data.sql', 'clone-data.sql',
):
    assert canary not in (stage / artifact).read_bytes(), artifact
before = json.loads((stage / 'restored-0024/manifest.json').read_text())
after = json.loads((stage / 'restored-0025/manifest.json').read_text())
assert all(after['tables'][key] == value for key, value in before['tables'].items()
           if key != 'alembic_version')
assert before['financial'] == after['financial']
assert set(map(tuple, before['identity_state'])) <= set(map(tuple, after['identity_state']))
assert after['catalog_active_generation'] == 2
assert all(after['tables'][name]['count'] == expected for name, expected in (
    ('stock_catalog_generations', 2), ('stock_catalog_admissions', 1),
    ('stock_catalog_securities', 2), ('stock_catalog_listings', 2),
    ('stock_catalog_aliases', 2),
))
PY
test "$(sql -d birja_restore_test -c "
    SELECT count(DISTINCT l.security_id)=2
       AND count(DISTINCT l.ticker)=1
       AND count(DISTINCT l.provider_asset_id)=2
       AND bool_and(a.valid_until=TIMESTAMPTZ '2001-01-02Z' AND a.valid_until<now())
    FROM stock_catalog_listings l JOIN stock_catalog_admissions a ON a.id=l.provider_admission_id
")" = t
test "$(sql -d birja_restore_test -c "
    SELECT NOT EXISTS (
        SELECT FROM stock_catalog_listings l JOIN stock_catalog_generations g ON g.id=l.generation_id
        JOIN stock_catalog_admissions a ON a.id=l.provider_admission_id
        WHERE g.is_active AND l.state='active'
          AND least(g.valid_until,l.provider_valid_until,a.valid_until)>now()
    )
")" = t
if (cd backend && DATABASE_URL="${migration_url%birja_test}birja_restore_test" \
  "$PYTHON" -m alembic downgrade 0024) 2>"$stage/downgrade.log"; then
  exit 1
fi
grep -Fq 'Stock catalog downgrade refused; catalog evidence is retained' "$stage/downgrade.log"
test "$(sql -d birja_restore_test -c 'SELECT version_num FROM alembic_version')" = 0025
"${restic[@]}" check --read-data >/dev/null
printf '%s\n' 'paired_encrypted_snapshot_integrity=true original_0024_financial_projection_exact=true'
printf '%s\n' 'catalog_identity_continuity=true original_expiry=true no_restored_eligibility=true redis_canary_excluded=true'
printf '%s\n' 'evidence_bearing_downgrade_refused=true retained_candidate_revision=0025'
