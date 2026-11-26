#!/usr/bin/env bash
# Paired encrypted recovery against a disposable PostgreSQL and cache.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
PYTHON="${BIRJA_RECEIPT_PYTHON:-$ROOT/backend/.venv/bin/python}"
contracts="$ROOT/deploy/tests/test-portfolio-recovery-contracts.py"
restic_path=/tmp/birja-test-tools/restic-0.19.1/restic
lane=paired
if (( $# )); then
  [[ $# == 6 && $1 == --lane && $3 == --archive && $5 == --sha256 ]]
  lane=$2 archive=$4 archive_sha=$6
  [[ $lane =~ ^(retained0025|cold|roles|upgraded|fresh|rollback)$ ]]
  [[ $archive == /tmp/birja-backup-test-*/recovery.tar.gz && $archive == "$(realpath -- "$archive")" ]]
  [[ $archive_sha =~ ^[a-f0-9]{64}$ ]]
  archive_dir=${archive%/*}
  current_image=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' \
    "$archive_dir/current0027-image-binding.json")
  [[ $current_image =~ ^sha256:[a-f0-9]{64}$ ]]
  if [[ $lane =~ ^(cold|upgraded|rollback)$ ]]; then
    predecessor_image=$("$PYTHON" -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' \
      "$archive_dir/predecessor0023-image-binding.json")
    [[ $predecessor_image =~ ^sha256:[a-f0-9]{64}$ ]]
  fi
fi
test -x "$PYTHON"
printf '%s  %s\n' 20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639 "$restic_path" |
  sha256sum --check --status
stage=$(mktemp -d /tmp/birja-backup-test-catalog-finance.XXXXXXXX)
postgres=''
redis=''
original=''
candidate=''
network=''
volumes=()
cleanup() {
  local failed=0 container
  local -A removed=()
  for container in "$postgres" "$original" "$candidate"; do
    if [[ -n "$container" && -z "${removed[$container]:-}" ]]; then
      docker rm -f "$container" >/dev/null || failed=1
      removed[$container]=1
    fi
  done
  if [[ -n "$redis" ]]; then docker rm -f "$redis" >/dev/null || failed=1; fi
  if (("${#volumes[@]}")); then docker volume rm "${volumes[@]}" >/dev/null || failed=1; fi
  if [[ -n "$network" ]]; then docker network rm "$network" >/dev/null || failed=1; fi
  rm -r -- "$stage"
  return "$failed"
}
trap cleanup EXIT
chmod 755 "$stage"
retained="$stage/retained"
if [[ $lane == paired || $lane == retained0025 ]]; then
  mkdir "$retained"
  "$PYTHON" "$contracts" --materialize-catalog "$retained"
fi
if [[ $lane != paired ]]; then
  chmod 700 "$stage"
  "$PYTHON" "$contracts" --install-catalog-archive "$stage/host" "$archive" "$archive_sha" 0027
  installed="$stage/host/var/lib/birja/recovery/releases/$archive_sha"
  restic_path="$installed/tools/restic"
  network=$(docker network create --internal "${stage##*/}")
fi
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj /CN=birja-local-test \
  -addext subjectAltName=IP:127.0.0.1,DNS:postgres -keyout "$stage/server.key" -out "$stage/ca.crt" >/dev/null 2>&1
chmod 644 "$stage/ca.crt"
chmod 600 "$stage/server.key"
chown 70:70 "$stage/server.key"

start_postgres() {
  local name=$1 volume="${2:-}"
  local -a storage=(--tmpfs /var/lib/postgresql:uid=70,gid=70,mode=0750)
  if [[ -n "$volume" ]]; then
    storage=(-v "$volume:/var/lib/postgresql")
  fi
  postgres=$(docker run -d --pull never --user 70:70 --name "$name" \
    --label org.birja.fixture=catalog-finance \
    "${storage[@]}" \
    -e PGDATA=/var/lib/postgresql/18/docker -e POSTGRES_USER=birja_test \
    -e POSTGRES_PASSWORD=test -e POSTGRES_DB=birja_test \
    -v "$stage/ca.crt:/fixture-cert.crt:ro" -v "$stage/server.key:/fixture-key.key:ro" \
    -p 127.0.0.1:55434:5432 \
    cgr.dev/chainguard/postgres@sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de \
    -c ssl=on -c ssl_cert_file=/fixture-cert.crt -c ssl_key_file=/fixture-key.key)
  if [[ -n "$network" ]]; then
    # The host-only seed client uses the loopback port. Application image clients
    # enter only the isolated network with the CA-validated PostgreSQL alias.
    docker network connect --alias postgres "$network" "$postgres"
  fi
  export BIRJA_CATALOG_TEST_CONTAINER="$postgres"
  wait_postgres
}

wait_postgres() {
  local try
  for try in {1..30}; do
    if docker exec "$postgres" pg_isready -h 127.0.0.1 -U birja_test -d postgres >/dev/null 2>&1; then
      return
    fi
    sleep 1
  done
  return 1
}

sql() { docker exec -i "$postgres" psql -XqAt -v ON_ERROR_STOP=1 -U birja_test "$@"; }
roles() {
sql -d birja_test <<'SQL'
CREATE ROLE birja_migrator LOGIN NOINHERIT PASSWORD 'fixture-migrator-only';
CREATE ROLE birja_app LOGIN NOINHERIT PASSWORD 'test-app';
CREATE ROLE birja_scheduler LOGIN NOINHERIT PASSWORD 'test-scheduler';
CREATE ROLE birja_action_operator NOLOGIN NOINHERIT;
GRANT USAGE, CREATE ON SCHEMA public TO birja_migrator;
REVOKE CREATE ON SCHEMA public FROM PUBLIC,birja_app,birja_scheduler;
GRANT USAGE ON SCHEMA public TO birja_app,birja_scheduler;
SQL
}
export ENV=test DATABASE_SSL_CA_FILE="$stage/ca.crt" REDIS_URL=redis://:test@127.0.0.1:56381/0
export OTP_HMAC_SECRET=unused-test-otp-value-012345678901234567890 JWT_SECRET=unused-test-jwt-value-012345678901234567890
export DATABASE_URL=postgresql+asyncpg://birja_test:test@127.0.0.1:55434/birja_test
migration_url=postgresql+asyncpg://birja_migrator:fixture-migrator-only@127.0.0.1:55434/birja_test
migrate() {
  local root="$1" revision="$2"
  (cd "$root/backend" && PYTHONPATH="$PWD" DATABASE_URL="$migration_url" "$PYTHON" -m alembic upgrade "$revision")
}
bootstrap() {
  local root=$1 database=${2:-birja_test}
  sql -d "$database" -v bootstrap=birja_test -v db_name="$database" -v apply=on \
    -v app_password=test-app -v scheduler_password=test-scheduler \
    -v migrator_password=fixture-migrator-only < "$root/deploy/db/bootstrap-roles.sql" > "$stage/bootstrap.log"
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

seed_nyse_provenance() {
  sql -d birja_test <<'SQL'
SET ROLE birja_migrator;
WITH generation AS (
  INSERT INTO stock_catalog_generations
    (manifest_sha256,mode,published_at,valid_until,is_active,sources,coverage)
  VALUES(repeat('b',64),'fixture','2000-01-01Z','2000-01-02Z',false,'{}','{}')
  RETURNING id
), security AS (
  INSERT INTO stock_catalog_securities(identity_key,created_at)
  VALUES('fixture-openfigi-nyse','2000-01-01Z') RETURNING id
)
INSERT INTO stock_catalog_listings
  (generation_id,security_id,ticker,normalized_ticker,company_name,normalized_name,
   listing_exchange,state,reason,source,row_key,row_digest,valid_until)
SELECT generation.id,security.id,'FNYS','FNYS','Fixture NYSE','fixture nyse',
       'NYSE','review','fixture','openfigi_nyse','fixture-openfigi-nyse',
       repeat('c',64),'2000-01-02Z'
FROM generation,security;
SQL
}

encrypted_round_trip() {
  local root="$1" revision="$2" snapshot
  local -a payload=(database.dump manifest.json)
  mkdir "$stage/$revision"
  "$PYTHON" "$contracts" --catalog-snapshot "$root" "$revision" "$stage" "$restic_path"
  if [[ $lane != paired ]]; then
    cp --reflink=auto "$archive" "$stage/$revision/recovery.tar"
    payload+=(recovery.tar)
  fi
  snapshot=$(
    cd "$stage/$revision"
    "${restic[@]}" backup --json "${payload[@]}" |
      "$PYTHON" -c 'import json,sys; print(*(row["snapshot_id"] for row in map(json.loads,sys.stdin) if row.get("message_type") == "summary"))'
  )
  [[ "$snapshot" =~ ^[a-f0-9]{64}$ ]]
  "${restic[@]}" restore --verify "$snapshot" --target "$stage/restored-$revision" >/dev/null
  cmp "$stage/$revision/database.dump" "$stage/restored-$revision/database.dump"
  cmp "$stage/$revision/manifest.json" "$stage/restored-$revision/manifest.json"
  if [[ $lane != paired ]]; then
    printf '%s  %s\n' "$archive_sha" "$stage/restored-$revision/recovery.tar" |
      sha256sum --check --status
  fi
}

restore_database() {
  local root=$1 revision=$2 database=${3:-birja_restore_test}
  if [[ $database == birja_restore_test ]]; then
    docker exec "$postgres" createdb -U birja_test "$database"
  fi
  sql -d "$database" -c \
    'REVOKE CREATE ON SCHEMA public FROM PUBLIC; GRANT USAGE,CREATE ON SCHEMA public TO birja_migrator;'
  docker exec -i "$postgres" pg_restore -U birja_test -d "$database" --role=birja_migrator \
    --no-acl --no-owner --exit-on-error --single-transaction < "$stage/restored-$revision/database.dump"
  "$PYTHON" "$contracts" --catalog-restore "$root" "$stage/restored-$revision/manifest.json" "$database"
}

round_trip() {
  local root=$1 revision=$2
  encrypted_round_trip "$root" "$revision"
  restore_database "$root" "$revision"
  docker exec "$postgres" pg_dump -U birja_test -d birja_restore_test --data-only > "$stage/$revision.sql"
  "$PYTHON" "$contracts" --catalog-cache-absent "$stage" "$revision" "$canary"
}

observe() {
  "$PYTHON" "$contracts" --catalog-observe "$1" "$2" "$stage/$3.json"
}

runtime() {
  local image=$1 database=$2
  shift 2
  docker run --rm -i --pull never --network "$network" \
    -v "$stage/ca.crt:/run/birja/db-ca.crt:ro" \
    -e DATABASE_SSL_CA_FILE=/run/birja/db-ca.crt \
    -e "DATABASE_URL=postgresql+asyncpg://birja_test:test@postgres:5432/$database" \
    -e ENV -e OTP_HMAC_SECRET -e JWT_SECRET -e PRICE_SOURCE=fake -e EMAIL_BACKEND=console \
    -e REDIS_URL=redis://127.0.0.1:6379/0 \
    "$@" --entrypoint python "$image" -
}

old_runtime() {
  local mode=$1
  "$PYTHON" "$contracts" --catalog-runtime-program "$mode" "$predecessor" |
    runtime "$predecessor_image" birja_test \
      -e DATABASE_URL=postgresql+asyncpg://birja_migrator:fixture-migrator-only@postgres:5432/birja_source_test \
      -e FIXTURE_APP_PASSWORD=test-app -e FIXTURE_SCHEDULER_PASSWORD=test-scheduler
}

use_primary_name() {
  # The exact old fixture expects birja_source_test; perform its creation
  # there, then let the modern backup oracle read the same database as birja_test.
  sql -d postgres -c "ALTER DATABASE $1 RENAME TO $2;"
}

downgrade_refuses() {
  local database=$1
  if (cd backend && PYTHONPATH="$PWD" \
    DATABASE_URL="${migration_url%birja_test}$database" \
    "$PYTHON" -m alembic downgrade 0025) >"$stage/downgrade.log" 2>&1; then
    return 1
  fi
  grep -q 'ck_stock_catalog_listings_source_known.*is violated' "$stage/downgrade.log"
  test "$(sql -d "$database" -c 'SELECT version_num FROM alembic_version')" = 0027
  test "$(sql -d "$database" -c "SELECT count(*) FROM stock_catalog_listings
        WHERE source='openfigi_nyse' AND listing_exchange='NYSE'")" = 1
}

current_authority() {
  local database=$1
  "$PYTHON" "$contracts" --catalog-runtime-program roles /run/birja/catalog-receipts.json |
    runtime "$current_image" "$database"
  observe "$installed" "$database" authority
  "$PYTHON" "$contracts" --catalog-authority "$stage/authority.json"
}

if [[ $lane =~ ^(cold|upgraded|rollback)$ ]]; then
  predecessor="$stage/predecessor"
  mkdir "$predecessor"
  "$PYTHON" "$contracts" --materialize-predecessor "$predecessor"
  original_volume=$(docker volume create "${stage##*/}-original")
  volumes+=("$original_volume")
  start_postgres "${stage##*/}-predecessor" "$original_volume"
  roles
  # The independently pinned predecessor opens the existing restricted roles.
  use_primary_name birja_test birja_source_test
  old_runtime predecessor-seed > "$stage/predecessor-before.log"
  grep -q '^portfolio_verified_tls=true$' "$stage/predecessor-before.log"
  use_primary_name birja_source_test birja_test
  observe "$predecessor" birja_test predecessor
  docker volume inspect "$original_volume" > "$stage/original-fingerprint"
  encrypted_round_trip "$predecessor" 0023
  docker stop "$postgres" >/dev/null
  original=$postgres
  postgres=''

  candidate_volume=$(docker volume create "${stage##*/}-candidate")
  volumes+=("$candidate_volume")
  start_postgres "${stage##*/}-candidate" "$candidate_volume"
  roles
  restore_database "$installed" 0023 birja_test
  migrate "$ROOT" 0027
  bootstrap "$ROOT"
  observe "$installed" birja_test successor
  "$PYTHON" "$contracts" --compare-predecessor "$stage/predecessor.json" "$stage/successor.json"
  printf '%s\n' 'populated_0023_to_0027=true predecessor_books_and_sequences_exact=true'
  if [[ $lane == upgraded ]]; then
    current_authority birja_test
    exit
  fi

  if [[ $lane == rollback ]]; then
    candidate=$postgres
    docker stop "$candidate" >/dev/null
    # The candidate has never been used by app/scheduler writers.
    docker start "$original" >/dev/null
    postgres=$original
    export BIRJA_CATALOG_TEST_CONTAINER=$postgres
    wait_postgres
    docker volume inspect "$original_volume" | cmp "$stage/original-fingerprint"
    observe "$predecessor" birja_test predecessor-reopened
    cmp "$stage/predecessor.json" "$stage/predecessor-reopened.json"
    use_primary_name birja_test birja_source_test
    old_runtime predecessor-read > "$stage/predecessor-replay.log"
    diff <(grep '^portfolio_projection=' "$stage/predecessor-before.log") \
      <(grep '^portfolio_projection=' "$stage/predecessor-replay.log")
    use_primary_name birja_source_test birja_test
    docker stop "$original" >/dev/null
    docker start "$candidate" >/dev/null
    postgres=$candidate
    export BIRJA_CATALOG_TEST_CONTAINER=$postgres
    wait_postgres
    docker volume inspect "$candidate_volume" > "$stage/candidate-fingerprint"
    printf '%s\n' 'prewrite_predecessor_restarted=true original_volume_and_ledger_exact=true'
  fi

  PYTHONPATH="$ROOT/backend" "$PYTHON" "$contracts" --catalog-economics seed "$stage/current-receipts.json"
  seed_nyse_provenance
  chmod 444 "$stage/current-receipts.json"
  start_cache
  test "$(docker exec "$redis" redis-cli SET fixture:stock:quote:FQA "$canary" EX 600)" = OK
  # Move to a fresh PostgreSQL server for cold replay, or restart this exact
  # candidate volume after application writes to prove the containment path.
  encrypted_round_trip "$installed" 0027
  if [[ $lane == cold ]]; then
    docker rm -f "$postgres" >/dev/null
    postgres=''
    start_postgres "${stage##*/}-restored"
    roles
    restore_database "$installed" 0027
    replay_db=birja_restore_test
  else
    docker restart "$postgres" >/dev/null
    wait_postgres
    docker volume inspect "$candidate_volume" | cmp "$stage/candidate-fingerprint"
    observe "$installed" birja_test candidate-restarted
    "$PYTHON" "$contracts" --catalog-exact "$stage/restored-0027/manifest.json" "$stage/candidate-restarted.json"
    replay_db=birja_test
  fi
  docker rm -f "$redis" >/dev/null
  redis=''
  start_cache
  test "$(docker exec "$redis" redis-cli DBSIZE)" = 0
  docker exec "$postgres" pg_dump -U birja_test -d "$replay_db" --data-only > "$stage/0027.sql"
  "$PYTHON" "$contracts" --catalog-cache-absent "$stage" 0027 "$canary"
  "$PYTHON" "$contracts" --catalog-runtime-program replay /run/birja/catalog-receipts.json |
    runtime "$current_image" "$replay_db" \
      -v "$stage/current-receipts.json:/run/birja/catalog-receipts.json:ro"
  downgrade_refuses "$replay_db"
  "${restic[@]}" check --read-data >/dev/null
  if [[ $lane == rollback ]]; then
    use_primary_name birja_test birja_source_test
    if old_runtime predecessor-read > "$stage/incompatible.log" 2>&1; then
      exit 1
    fi
    grep -q '0023 only before import' "$stage/incompatible.log"
    use_primary_name birja_source_test birja_test
    printf '%s\n' 'postwrite_0027_restarted=true candidate_volume_and_receipts_exact=true predecessor_on_0027_refused=true'
  else
    current_authority "$replay_db"
    printf '%s\n' 'cold_encrypted_0027_exact=true fresh_restore_server=true'
  fi
  exit
fi

start_postgres "${stage##*/}-primary"
roles
start_cache
test "$(docker exec "$redis" redis-cli SET fixture:stock:quote:FQA "$canary" EX 600)" = OK

if [[ $lane == fresh || $lane == roles ]]; then
  migrate "$ROOT" 0027
  bootstrap "$ROOT"
  current_authority birja_test
  exit
fi

if [[ $lane == paired || $lane == retained0025 ]]; then
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
  if [[ $lane == retained0025 ]]; then
    "${restic[@]}" check --read-data >/dev/null
    printf '%s\n' 'retained_0025_exact=true'
    exit
  fi
fi

migrate "$ROOT" 0027
bootstrap "$ROOT"
PYTHONPATH="$ROOT/backend" "$PYTHON" "$contracts" --catalog-economics seed "$stage/current-receipts.json"
seed_nyse_provenance
test "$(docker exec "$redis" redis-cli GET fixture:stock:quote:FQA)" = "$canary"
round_trip "$ROOT" 0027
docker rm -f "$redis" >/dev/null
redis=''
start_cache
test "$(docker exec "$redis" redis-cli DBSIZE)" = 0
PYTHONPATH="$ROOT/backend" DATABASE_URL="${DATABASE_URL%birja_test}birja_restore_test" \
  "$PYTHON" "$contracts" --catalog-economics replay "$stage/current-receipts.json"
downgrade_refuses birja_restore_test
"${restic[@]}" check --read-data >/dev/null
printf '%s\n' 'retained_0025_exact=true successor_0027_exact=true redis_display_cache_excluded=true'
printf '%s\n' 'cold_fill_and_actions_replay_exact=true populated_downgrade_refused=true encrypted_integrity=true'
