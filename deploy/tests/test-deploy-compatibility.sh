#!/usr/bin/env bash
# Offline actual deploy/rollback control flow. No Docker or host config.
set -Eeuo pipefail
HERE=$(dirname "$(readlink -f "$0")")
. "$HERE/../deploy.sh"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
APP_DIR=$TMP/app
STATE_DIR=$TMP/state
DEPLOY_LOG=$STATE_DIR/deploys.log
PENDING_MARK=$STATE_DIR/deploy.pending
WEB_ROOT=$TMP/web
BIRJA_RETAINED_DIR=$TMP/retained
LOCK=$TMP/lock
mkdir -p "$APP_DIR/backend" "$STATE_DIR" "$WEB_ROOT/releases/good" "$BIRJA_RETAINED_DIR/deploy"
touch "$APP_DIR/docker-compose.prod.yml"
for name in check-nginx-config install-nginx; do
  printf '#!/bin/sh\nexit 0\n' > "$BIRJA_RETAINED_DIR/deploy/$name.sh"
  chmod 700 "$BIRJA_RETAINED_DIR/deploy/$name.sh"
done
git -C "$APP_DIR" init -q
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q --allow-empty -m old
git -C "$APP_DIR" tag v0.3.1
OLD=$(git -C "$APP_DIR" rev-parse HEAD)
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q --allow-empty -m legacy-tested
LEGACY_TESTED=$(git -C "$APP_DIR" rev-parse HEAD)
# Exercise the real authenticated source predicate, never stub it to pass.
mkdir -p "$APP_DIR/backend/alembic/versions"
cp "$HERE/../../backend/alembic/versions/0017_portfolio_ownership.py" \
  "$APP_DIR/backend/alembic/versions/0017_portfolio_ownership.py"
git -C "$APP_DIR" add backend/alembic/versions/0017_portfolio_ownership.py
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q -m portfolio-tested
PORTFOLIO_TESTED=$(git -C "$APP_DIR" rev-parse HEAD)
printf '\n# corrupted synthetic source\n' >> "$APP_DIR/backend/alembic/versions/0017_portfolio_ownership.py"
git -C "$APP_DIR" add backend/alembic/versions/0017_portfolio_ownership.py
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q -m corrupted-marker
CORRUPTED_TESTED=$(git -C "$APP_DIR" rev-parse HEAD)
git -C "$APP_DIR" checkout -q --detach "$PORTFOLIO_TESTED"
BIRJA_TESTED_SOURCE=$PORTFOLIO_TESTED
git -C "$APP_DIR" branch -f main "$PORTFOLIO_TESTED"
export BIRJA_TEST_CALLS="$TMP/calls"
cat > "$BIRJA_RETAINED_DIR/deploy/configure-db.sh" <<'CONFIGURE'
#!/bin/sh
set -eu
[ "$*" = '--production --resume-portfolio-migration --approved-operation portfolio-migration-to-final' ]
[ "${BIRJA_BACKUP_LOCK_FD:-}" = 9 ]
[ -e "/proc/$$/fd/9" ]
printf 'configure-db %s\n' "$*" >> "$BIRJA_TEST_CALLS"
CONFIGURE
chmod 700 "$BIRJA_RETAINED_DIR/deploy/configure-db.sh"
git() { if [[ "$*" == *' fetch '* ]]; then return; fi; command git "$@"; }
event() { echo "$*" >> "$TMP/calls"; }
checkout_source() { event checkout; }
maybe_reexec() { :; }
app_services() { echo 'backend scheduler'; }
dc() { event "dc $*"; }
bindings() { event bindings; }
build_frontend_release() { event build; RELEASE_DIR=$WEB_ROOT/releases/good; }
swap_current() { event swap; }
health_check() { event health; }
record() { event record; }
prune_releases() { event prune; }
exec 9>"$LOCK"
flock -n 9
run_case() {
  local mode=$1 revision=$2 target=$3 pending=$4 want=$5 rc=0 before
  ADMITTED_REVISION=$revision REF=$target
  printf 't %s %s v0.3.1\nt %s %s main\n' "$OLD" "$WEB_ROOT/releases/good" "$BIRJA_TESTED_SOURCE" "$WEB_ROOT/releases/good" > "$DEPLOY_LOG"
  rm -f "$PENDING_MARK"
  [ "$pending" = yes ] && echo original-pending > "$PENDING_MARK"
  : > "$TMP/calls"
  before=$(sha256sum "$DEPLOY_LOG"; if [ -e "$PENDING_MARK" ]; then sha256sum "$PENDING_MARK"; fi)
  ( set -e; "do_$mode" ) > "$TMP/output" 2>&1 || rc=$?
  if [ "$want" = refuse ]; then
    [ "$rc" != 0 ] || { echo "FAIL admitted $mode $revision $target"; return 1; }
    grep -q 'application_schema_incompatible=true' "$TMP/output"
    [ ! -s "$TMP/calls" ]
    [ "$before" = "$(sha256sum "$DEPLOY_LOG"; if [ -e "$PENDING_MARK" ]; then sha256sum "$PENDING_MARK"; fi)" ]
  else
    [ "$rc" = 0 ] || { cat "$TMP/output"; return 1; }
    grep -q checkout "$TMP/calls"
    grep -q record "$TMP/calls"
    if [ "$mode" = deploy ]; then
      grep -q '^dc stop backend scheduler$' "$TMP/calls"
      grep -q '^configure-db --production --resume-portfolio-migration --approved-operation portfolio-migration-to-final$' "$TMP/calls"
      python3 - "$TMP/calls" <<'ORDER'
import sys
from pathlib import Path
calls = Path(sys.argv[1]).read_text().splitlines()
stop = calls.index('dc stop backend scheduler')
configure = next(i for i, line in enumerate(calls) if line.startswith('configure-db '))
start = calls.index('dc up -d --wait --remove-orphans backend scheduler')
assert stop < configure < start, calls
ORDER
    else
      ! grep -q '^configure-db ' "$TMP/calls"
    fi
  fi
  # A separate open description cannot take the inherited operation lock.
  ( exec 8>"$LOCK"; ! flock -n 8 )
  echo "ok $mode revision=$revision target=$target pending=$pending $want"
}
for ref in v0.3.1 "$OLD" "$LEGACY_TESTED" "$CORRUPTED_TESTED" deadbeef missing ''; do
  run_case deploy 0014 "$ref" no refuse
done
git -C "$APP_DIR" branch -f main "$OLD"
run_case deploy 0014 main yes refuse
git -C "$APP_DIR" branch -f main "$PORTFOLIO_TESTED"
for revision in '' 0015 0016 0018 0019 0020 invalid 0014-bad; do
  run_case deploy "$revision" main no refuse
done
for revision in 0007 0008 0009 0010 0011 0012 0013 0014 0017; do
  run_case deploy "$revision" "$PORTFOLIO_TESTED" no pass
  run_case deploy "$revision" v0.3.1 no refuse
done
run_case deploy 0014 main no pass
# A corrupted marker refuses even if its SHA is the manifest's tested source.
BIRJA_TESTED_SOURCE=$CORRUPTED_TESTED
run_case deploy 0014 "$CORRUPTED_TESTED" no refuse
BIRJA_TESTED_SOURCE=$PORTFOLIO_TESTED
run_case rollback 0017 main no refuse
run_case rollback 0017 main yes pass
run_case rollback 0020 main yes refuse
# Retained runtime rollback remains separate from the portfolio-upgrade lane.
BIRJA_TESTED_SOURCE=$LEGACY_TESTED
git -C "$APP_DIR" checkout -q --detach "$LEGACY_TESTED"
run_case rollback 0014 main no refuse
run_case rollback 0014 main yes pass
for revision in 0007 0008 0013; do
  run_case deploy "$revision" v0.3.1 no refuse
  run_case rollback "$revision" main no pass
done
# Current closure authority is a separate authenticated candidate family. A
# familiar0017 marker alone cannot admit current0023 or migrate0020 safely.
git -C "$APP_DIR" checkout -q --detach "$PORTFOLIO_TESTED"
for name in backend/alembic/versions/0023_portfolio_closure_authority.py \
  backend/alembic/sql/0023_portfolio_closure.sql backend/app/db/portfolio_bootstrap.py \
  backend/app/db/schema_contract.py backend/app/db/portfolio_migrate.py; do
  mkdir -p "$APP_DIR/$(dirname "$name")"
  git -C "$HERE/../.." show "v0.7.0:$name" > "$APP_DIR/$name"
  git -C "$APP_DIR" add "$name"
done
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q -m closure-tested
CLOSURE_TESTED=$(git -C "$APP_DIR" rev-parse HEAD)
printf '\n-- corrupted closure authority\n' >> "$APP_DIR/backend/alembic/sql/0023_portfolio_closure.sql"
git -C "$APP_DIR" add backend/alembic/sql/0023_portfolio_closure.sql
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q -m closure-corrupt
CLOSURE_CORRUPT=$(git -C "$APP_DIR" rev-parse HEAD)
git -C "$APP_DIR" checkout -q --detach "$CLOSURE_TESTED"
BIRJA_TESTED_SOURCE=$CLOSURE_TESTED
for revision in 0007 0008 0014 0017 0020 0023; do
  run_case deploy "$revision" "$CLOSURE_TESTED" no pass
done
for revision in 0021 0022 invalid; do
  run_case deploy "$revision" "$CLOSURE_TESTED" no refuse
done
ADMITTED_REVISION=0023 admit_application_source "$CLOSURE_TESTED"
for revision in 0020 0023; do
  run_case deploy "$revision" "$PORTFOLIO_TESTED" no refuse
  run_case rollback "$revision" main no refuse
done
# Pending rollback selects the already-tested current source, not the older
# previous log entry. It may retain0023 with the same exact compatible app.
run_case rollback 0023 main yes pass
BIRJA_TESTED_SOURCE=$CLOSURE_CORRUPT
run_case deploy 0023 "$CLOSURE_CORRUPT" no refuse
ADMITTED_REVISION=0023
if admit_application_source "$CLOSURE_CORRUPT"; then
  echo 'FAIL corrupted successor runtime admitted'; exit 1
fi
git -C "$APP_DIR" checkout -q --detach "$CLOSURE_TESTED"
printf '\n# corrupted migration-entry authentication\n' >> "$APP_DIR/backend/app/db/portfolio_migrate.py"
git -C "$APP_DIR" add backend/app/db/portfolio_migrate.py
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q -m migrator-corrupt
CLOSURE_MIGRATOR_CORRUPT=$(git -C "$APP_DIR" rev-parse HEAD)
BIRJA_TESTED_SOURCE=$CLOSURE_MIGRATOR_CORRUPT
run_case deploy 0023 "$CLOSURE_MIGRATOR_CORRUPT" no refuse
if admit_application_source "$CLOSURE_MIGRATOR_CORRUPT"; then
  echo 'FAIL corrupted migration authentication admitted'; exit 1
fi

git -C "$APP_DIR" checkout -q --detach "$CLOSURE_TESTED"
for name in backend/alembic/versions/0024_stock_halt_snapshot.py \
  backend/alembic/sql/0024_stock_halt_snapshot.sql backend/app/db/portfolio_bootstrap.py \
  backend/app/db/schema_contract.py backend/app/db/portfolio_migrate.py; do
  cp "$HERE/../../$name" "$APP_DIR/$name"
  git -C "$APP_DIR" add "$name"
done
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q -m reported-halt-tested
HALT_TESTED=$(git -C "$APP_DIR" rev-parse HEAD)
BIRJA_TESTED_SOURCE=$HALT_TESTED
for revision in 0023 0024; do
  run_case deploy "$revision" "$HALT_TESTED" no pass
  ADMITTED_REVISION=$revision admit_application_source "$HALT_TESTED"
done
run_case rollback 0024 main yes pass
run_case rollback 0024 main no refuse
BIRJA_TESTED_SOURCE=$CLOSURE_TESTED
if ADMITTED_REVISION=0024 admit_application_source "$CLOSURE_TESTED"; then
  echo 'FAIL predecessor runtime admitted on 0024'; exit 1
fi
