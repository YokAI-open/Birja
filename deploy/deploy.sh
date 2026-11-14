#!/usr/bin/env bash
# Birja production deploy (the single deploy command, D-02).
#
#   /srv/birja/deploy/deploy.sh              deploy main
#   DEPLOY_REF=<branch|tag|sha> /srv/birja/deploy/deploy.sh
#   /srv/birja/deploy/deploy.sh --rollback   return to the previous deploy
#
# Rollback target (deploys.log, one line per successful deploy or rollback:
# "time sha release ref", ref "rollback" for rollbacks):
#   The log is replayed as a stack of live releases. A deploy pushes its
#   entry. A rollback entry pops entries until its own SHA is on top, so a
#   rolled-back release is never picked again.
#   - Normal case: the target is the newest stack entry below the top whose
#     SHA differs from the top (skips repeated deploys of the same SHA).
#   - After a failed deploy (it never logs; $PENDING_MARK is left behind, or
#     the checkout HEAD differs from the top SHA) the top entry itself is the
#     last good release, so that is the target.
#   Migrations are never undone.
#   The price scheduler (Phase 3) is built and started with the backend; a
#   rollback to a release without it removes it (--remove-orphans).
# Self re-exec: if the checked-out ref changes deploy/deploy.sh, the deploy
#   re-runs the new script once (BIRJA_DEPLOY_REEXEC guard) for the same SHA,
#   keeping the lock. Rollback never re-execs: it runs this script's logic.
#
# Undo / teardown:
#   docker compose -p birja-prod down   stops the stack; volumes are kept.
#   (down -v deletes ALL prod data: only run it with explicit intent.)
#   Then: rm -rf /srv/birja /var/www/birja /var/lib/birja
set -Eeuo pipefail
umask 022

APP_DIR=/srv/birja                          # prod checkout; never the dev tree
ENV_FILE=/etc/birja/prod.env                # root-600 prod secrets
WEB_ROOT=/var/www/birja                     # releases/ + current symlink served by nginx
STATE_DIR=/var/lib/birja                    # deploy history
DEPLOY_LOG=$STATE_DIR/deploys.log           # time sha release ref, one line per deploy
PENDING_MARK=$STATE_DIR/deploy.pending      # exists while a deploy is unfinished/failed
LOCK=/var/lock/birja-deploy.lock            # prevents concurrent deploys
HOST=birja.nist.one                         # public host name
CERT=/etc/nginx/certs/nist.one/fullchain.pem  # installed origin certificate
NODE_BASE_IMAGE=cgr.dev/chainguard/wolfi-base@sha256:24f549a7fcace88e69b9557941168c74645688ecc4acf7fb6d734a6b74e9019d # frontend toolchain base
KEEP_RELEASES=3                             # static releases kept on disk
BUILD_UID=1000                              # unprivileged uid for the npm build (node in the image)
REF="${DEPLOY_REF:-main}"                   # D-05: ref override
NEW_SCRIPT=$APP_DIR/deploy/deploy.sh        # this script as checked out by a deploy
if [ -n "${BIRJA_RETAINED_DIR:-}" ]; then
  # The entrypoint verified the immutable bundle before executing this file.
  NEW_SCRIPT=$BIRJA_RETAINED_DIR/deploy/deploy.sh
fi
# Hash of the script bash is running now, taken before any checkout can
# replace it on disk (compared after checkout, see maybe_reexec).
SELF_HASH=$(sha256sum 2>/dev/null < "${BASH_SOURCE[0]}" | awk '{print $1}' || true)

STEP="startup"

bindings() {
  BIRJA_BACKUP_LOCK_FD=9 python3 "$BIRJA_RETAINED_DIR/deploy/datastore-bindings.py" "$@"
}

dc() {
  if [ -n "${BIRJA_RETAINED_DIR:-}" ]; then
    bindings --write-overlay || return 1
    if [ "${1:-}" = up ]; then bindings --check-volumes || return 1; fi
    local suffix=""
    if [ "$(git -C "$APP_DIR" rev-parse HEAD)" = "$(git -C "$APP_DIR" rev-parse 'v0.3.1^{commit}')" ]; then suffix='?ssl=verify-full'; fi
    BIRJA_OLD_TLS_SUFFIX=$suffix BIRJA_APP_DIR=$APP_DIR BIRJA_OPS_DIR=$BIRJA_RETAINED_DIR BIRJA_MIGRATOR_CONTEXT=$BIRJA_RETAINED_DIR/backend \
      docker compose -p birja-prod -f "$BIRJA_RETAINED_DIR/docker-compose.prod.yml" \
        -f "$BIRJA_RETAINED_DIR/deploy/db-security.compose.yml" \
        -f /var/lib/birja/ops/datastore-volumes.json --env-file "$ENV_FILE" "$@"
  else
    docker compose -f "$APP_DIR/docker-compose.prod.yml" --env-file "$ENV_FILE" "$@"
  fi
}

supported_ref() {
  # Explicit compatibility set: other releases require a reviewed bundle update.
  case "$1" in main|v0.3.1|"${BIRJA_TESTED_SOURCE:-unsupported}") return 0 ;; *) return 1 ;; esac
}

application_schema_incompatible() {
  echo 'application_schema_incompatible=true' >&2
  return 1
}

admit_application_source() {
  # ADMITTED_REVISION is authenticated by recovery_gate; tested_source is
  # pinned by the retained manifest. A mutable ref name proves neither.
  [[ "${1:-}" =~ ^[0-9a-f]{40}$ ]] || { application_schema_incompatible; return 1; }
  case "${ADMITTED_REVISION:-}" in
    0007|0008|0009|0010|0011|0012|0013) return 0 ;;
    0014)
      [[ "${BIRJA_TESTED_SOURCE:-}" =~ ^[0-9a-f]{40}$ ]] &&
        [ "$1" = "$BIRJA_TESTED_SOURCE" ] && return 0 ;;
  esac
  application_schema_incompatible
}

checkout_source() {
  # The installer owns this launcher outside the sparse application source.
  # Git still detects an existing excluded tracked path as a local change.
  # Remove only our exact launcher during checkout, then restore it even if
  # checkout fails. The path is absent, never an old executable, in between.
  python3 - "$APP_DIR" "$1" "$LOCK" <<'PY'
import importlib.util, os, pathlib, stat, subprocess, sys
sys.dont_write_bytecode = True
app = pathlib.Path(sys.argv[1])
launcher = app / 'deploy/deploy.sh'
content = '#!/bin/bash\nexec /usr/local/sbin/birja-deploy "$@"\n'
s = launcher.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid == 0 and not s.st_mode & 0o022
assert launcher.read_text() == content
patterns = subprocess.run(['git','-C',str(app),'sparse-checkout','list'], capture_output=True, check=True).stdout.decode().splitlines()
assert patterns == ['/*', '!/deploy/']
status = subprocess.run(['git','-C',str(app),'status','--porcelain','-z'], capture_output=True, check=True).stdout
assert status in [b'', b' M deploy/deploy.sh\0'], 'unapproved source changes'
if sys.argv[2] == '--check':
    sys.exit(0)
helper = pathlib.Path('/var/lib/birja/recovery/current/deploy/backup-snapshot.py')
spec = importlib.util.spec_from_file_location('backup_lock', helper)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
held = module.acquire_operation_lock(pathlib.Path(sys.argv[3]), '9')
launcher.unlink()
try:
    result = subprocess.run(['git','-C',str(app),'checkout','--detach',sys.argv[2]], capture_output=True)
finally:
    # Sparse checkout must never produce an old privileged launcher.
    assert not launcher.exists() and not launcher.is_symlink()
    launcher.parent.mkdir(mode=0o755, exist_ok=True)
    assert not launcher.parent.is_symlink()
    temporary = launcher.with_name('deploy.sh.handoff')
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o500)
    with os.fdopen(fd, 'w') as out:
        out.write(content)
    os.replace(temporary, launcher)
assert result.returncode == 0, 'source checkout failed; diagnostics=redacted'
PY
}

startup_revision() {
  python3 - "$1" "$2" <<'PY'
import json, re, stat, sys
from pathlib import Path
p = Path('/var/lib/birja/backup/restore-last-success.json')
assert p == p.resolve()
s, parent = p.lstat(), p.parent.lstat()
assert stat.S_ISREG(s.st_mode) and s.st_uid == 0 and stat.S_IMODE(s.st_mode) == 0o600
assert stat.S_ISDIR(parent.st_mode) and parent.st_uid == 0 and stat.S_IMODE(parent.st_mode) == 0o700
d = json.loads(p.read_text())
assert d['ok'] is True and d['source_release'] == sys.argv[1] and d['snapshot_id'] == sys.argv[2]
assert isinstance(d['source_revision'], str) and re.fullmatch('[A-Za-z0-9_]{1,64}', d['source_revision'])
print(d['source_revision'])
PY
}

recovery_gate() {
  local recovery snapshot source_sha revision bundle
  recovery=$(readlink -f /var/lib/birja/recovery/current)
  [[ "$recovery" =~ ^/var/lib/birja/recovery/releases/[0-9a-f]{64}$ ]] || return 1
  bundle=${recovery##*/}
  source_sha=$(live_sha "$DEPLOY_LOG")
  if [ -z "$source_sha" ]; then source_sha=$(git -C "$APP_DIR" rev-parse HEAD); fi
  [[ "$source_sha" =~ ^[0-9a-f]{40}$ ]] || return 1
  snapshot=$(python3 -I -c 'import json; print(json.load(open("/var/lib/birja/backup/last-success.json"))["snapshot_id"])' 2>/dev/null)
  [[ "$snapshot" =~ ^[0-9a-f]{64}$ ]] || return 1
  if [ "${MODE:-}" = start-selected ]; then
    # Limited first-start admission: all material was prepared before the
    # fresh backup/restore, and remains unchanged while datastores are stopped.
    # The unchanged gate authenticates this exact completed profile below.
    revision=$(startup_revision "$source_sha" "$snapshot") || return 1
  else
    bindings --check-running || return 1
    revision=$(dc exec -T postgres sh -c 'exec psql -XqAt -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version_num FROM alembic_version"' 2>/dev/null) || return 1
  fi
  [[ "$revision" =~ ^[A-Za-z0-9_]{1,64}$ ]] || return 1
  BIRJA_BACKUP_LOCK_FD=9 python3 "$recovery/deploy/backup-snapshot.py" recovery-gate \
    --snapshot "$snapshot" --source-release "$source_sha" --source-revision "$revision" --bundle-sha "$bundle" >/dev/null 2>&1 || return 1
  ADMITTED_REVISION=$revision
}

# app_services: the services deploy/rollback build and start. Releases before
# Phase 3 have no scheduler, so it is listed only if this checkout defines it.
# A failing "dc config" fails this function: guessing "backend" would leave the
# old scheduler running silently. Call it as its own assignment
# (services=$(app_services)) so set -e and the ERR trap see the failure.
app_services() {
  local svcs
  svcs=$(dc config --services) || {
    echo "docker compose config failed; cannot tell which services to deploy" >&2
    return 1
  }
  if grep -qx scheduler <<<"$svcs"; then echo "backend scheduler"; else echo "backend"; fi
}

usage() {
  cat <<USAGE
Usage: deploy.sh [--rollback]
  (no args)    deploy origin/main (or the ref in DEPLOY_REF)
  DEPLOY_REF=<branch|tag|sha> deploy.sh   deploy that ref instead of main
  --rollback   return to the release that was live before the current one
  --start-selected-datastores   start only bound existing datastores after TLS checks
               (see the header of this script for how it is chosen)
  -h, --help   this text
Note: rollback does not undo database migrations.
USAGE
}

on_err() {
  local rc=$?
  echo "FAILED at step: $STEP (exit $rc)" >&2
  if [ -n "${BUILD_TMP:-}" ]; then rm -rf -- "$BUILD_TMP" || true; fi
  echo "Diagnostics withheld; inspect private service state through the approved runbook." >&2
  echo "To roll back: /usr/local/sbin/birja-deploy --rollback" >&2
  exit "$rc"
}

preflight() {
  STEP="preflight"
  [ "$(id -u)" -eq 0 ] || { echo "must run as root" >&2; exit 1; }
  # A re-exec'd run (maybe_reexec) inherits fd 9 with the lock still held by
  # the same open file; reopening it would drop the lock for a moment.
  if { [ "${BIRJA_DEPLOY_REEXEC:-}" = 1 ] || [ "${BIRJA_RETAINED_LOCK:-}" = 1 ]; } && [ /dev/fd/9 -ef "$LOCK" ]; then :
  else exec 9>"$LOCK"
  fi
  flock -n 9 || { echo "another deploy is running" >&2; exit 1; }
  # A valid held lock is independently checked by recovery-gate's kernel-backed
  # helper; its duplicate closes without dropping this parent's lock.
  git -C "$APP_DIR" rev-parse --git-dir >/dev/null 2>&1 \
    || { echo "$APP_DIR is not a git checkout" >&2; exit 1; }
  checkout_source --check \
    || { echo "$APP_DIR has unapproved source changes, refusing" >&2; exit 1; }
  [ -f "$ENV_FILE" ] || { echo "$ENV_FILE missing (run deploy/init-prod-env.sh)" >&2; exit 1; }
  [ "$(stat -c '%a %U' "$ENV_FILE")" = "600 root" ] \
    || { echo "$ENV_FILE must be mode 600 owned by root" >&2; exit 1; }
  grep -qE '^RESEND_API_KEY=.+' "$ENV_FILE" \
    || { echo "RESEND_API_KEY is empty in $ENV_FILE" >&2; exit 1; }
  grep -qE '^EMAIL_FROM=.+' "$ENV_FILE" \
    || { echo "EMAIL_FROM is empty in $ENV_FILE" >&2; exit 1; }
  [ -f "$CERT" ] || { echo "certificate $CERT missing" >&2; exit 1; }
  openssl x509 -checkend 0 -noout -in "$CERT" >/dev/null \
    || { echo "certificate $CERT is expired" >&2; exit 1; }
  if ! openssl x509 -checkend $((30 * 86400)) -noout -in "$CERT" >/dev/null; then
    echo "WARNING: certificate expires within 30 days, renew it (see deploy/RUNBOOK.md)" >&2
  fi
  STEP="fresh exact recovery gate"
  recovery_gate || { echo "fresh exact recovery and completed restore required" >&2; exit 1; }
  if [ "${MODE:-}" = start-selected ]; then return; fi
  STEP="read-only database compatibility preflight"
  BIRJA_BACKUP_LOCK_FD=9 "$BIRJA_RETAINED_DIR/deploy/configure-db.sh" --production --inspect
}

start_selected_datastores() {
  STEP="selected datastore secure startup prerequisites"
  bindings --check-volumes || return 1
  BIRJA_BACKUP_LOCK_FD=9 "$BIRJA_RETAINED_DIR/deploy/provision-db-tls.sh" --production --check || return 1
  # The entrypoint authenticated the HBA and fixed Compose bytes in MANIFEST.
  [ -f "$BIRJA_RETAINED_DIR/deploy/db/pg_hba.conf" ] || return 1
  dc up -d --wait postgres redis || return 1
  bindings --check-running || return 1
  local actual
  actual=$(dc exec -T postgres sh -c 'exec psql -XqAt -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version_num FROM alembic_version"') || return 1
  [ "$actual" = "$ADMITTED_REVISION" ] || { echo "candidate_revision_mismatch=true" >&2; return 1; }
  echo "selected_datastores_started=true writers_started=false"
}

# Passes only if the API is healthy and nginx serves this release's exact
# index.html (it names the hashed assets, so it identifies the build).
health_check() {
  STEP="health check"
  local i
  for i in $(seq 1 15); do
    if curl -fsS --resolve "$HOST:443:127.0.0.1" "https://$HOST/api/v1/health" 2>/dev/null \
        | python3 -I -c 'import json,sys; sys.exit(0 if json.load(sys.stdin).get("status")=="ok" else 1)' 2>/dev/null \
      && cmp -s "$RELEASE_DIR/index.html" \
           <(curl -fsS --resolve "$HOST:443:127.0.0.1" "https://$HOST/" 2>/dev/null); then
      echo "Health check passed (serving $RELEASE_DIR)"
      return 0
    fi
    sleep 2
  done
  echo "Health check failed after 15 tries" >&2
  return 1
}

# The frontend is built from a clean `git archive` copy, as an unprivileged
# user, without npm lifecycle scripts (WR-06: a hostile dependency must not
# get host root). Only regular files from dist/ are copied out, by root;
# nothing else the container wrote is used or executed.
build_frontend_release() {
  STEP="frontend build"
  local sha ts rel dist toolchain_file node_image
  BUILD_TMP=$(mktemp -d)                    # root 700: host users cannot reach inside
  toolchain_file="$APP_DIR/frontend/Dockerfile"
  if [ -n "${BIRJA_RETAINED_DIR:-}" ]; then
    toolchain_file="$BIRJA_RETAINED_DIR/frontend/Dockerfile"
  fi
  grep -qx "FROM $NODE_BASE_IMAGE AS toolchain" "$toolchain_file"
  mkdir "$BUILD_TMP/toolchain-context"
  docker build --target toolchain --iidfile "$BUILD_TMP/node-image-id" \
    -f "$toolchain_file" "$BUILD_TMP/toolchain-context"
  node_image=$(cat "$BUILD_TMP/node-image-id")
  [[ "$node_image" =~ ^sha256:[0-9a-f]{64}$ ]]
  node_image=$(docker image inspect "$node_image" --format '{{.Id}}')
  [[ "$node_image" =~ ^sha256:[0-9a-f]{64}$ ]]
  git -C "$APP_DIR" archive HEAD frontend | tar -x -C "$BUILD_TMP"
  chown -R "$BUILD_UID:$BUILD_UID" "$BUILD_TMP/frontend"
  docker run --rm --user "$BUILD_UID:$BUILD_UID" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
    -v "$BUILD_TMP/frontend":/app -w /app "$node_image" \
    sh -c 'npm ci --ignore-scripts && npm run build'
  STEP="frontend release"
  dist="$BUILD_TMP/frontend/dist"
  [ -f "$dist/index.html" ] || { echo "build produced no dist/index.html" >&2; return 1; }
  if [ -n "$(find "$dist" ! -type f ! -type d -print -quit)" ]; then
    echo "dist/ contains links or special files, refusing" >&2
    return 1
  fi
  sha=$(git -C "$APP_DIR" rev-parse --short HEAD)
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  rel="$WEB_ROOT/releases/$sha-$ts"
  install -d "$rel"
  cp -R --no-preserve=all "$dist/." "$rel/"
  chown -R root:root "$rel"
  chmod -R u=rwX,go=rX "$rel"
  rm -rf -- "$BUILD_TMP"
  BUILD_TMP=""
  RELEASE_DIR="$rel"
}

swap_current() {
  STEP="frontend swap"
  ln -sfn "$1" "$WEB_ROOT/current.tmp"
  mv -Tf "$WEB_ROOT/current.tmp" "$WEB_ROOT/current"
}

record() {
  STEP="record deploy"
  install -d -m 755 "$STATE_DIR"
  printf '%s %s %s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    "$(git -C "$APP_DIR" rev-parse HEAD)" "$RELEASE_DIR" "$1" >> "$DEPLOY_LOG"
  rm -f "$PENDING_MARK"
}

# rollback_target <log> <failed 0|1>: prints "sha release" of the rollback
# target, or nothing if there is none. Pure function (tested by
# deploy/tests/test-rollback-target.sh).
rollback_target() {
  [ -f "$1" ] || return 0
  awk -v failed="$2" '
    NF < 4 { next }
    $4 == "rollback" {
      while (n > 0 && sha[n] != $2) n--
      if (n == 0) { n = 1; sha[1] = $2; rel[1] = $3 }
      next
    }
    { n++; sha[n] = $2; rel[n] = $3 }
    END {
      if (n == 0) exit
      if (failed == 1) { print sha[n], rel[n]; exit }
      for (i = n - 1; i >= 1; i--) if (sha[i] != sha[n]) { print sha[i], rel[i]; exit }
    }' "$1"
}

# should_reexec <running hash> <checked-out hash> <guard>: succeeds if the
# deploy must re-run the newly checked-out deploy.sh. Only when both hashes
# are known and differ, and at most once (guard BIRJA_DEPLOY_REEXEC=1).
# Pure function (tested by deploy/tests/test-reexec.sh).
should_reexec() {
  [ "${3:-}" != 1 ] && [ -n "$1" ] && [ -n "$2" ] && [ "$1" != "$2" ]
}

# maybe_reexec <sha>: bash keeps running the functions it parsed from the old
# file even after the checkout replaced it, so a release that changes
# deploy.sh would be deployed with the previous release's logic. Re-run the
# new script once instead. It inherits fd 9 (the lock stays held) and is
# told the already resolved SHA, so it deploys exactly the same commit.
maybe_reexec() {
  STEP="re-exec check"
  local new_hash=""
  if [ -f "$NEW_SCRIPT" ]; then new_hash=$(sha256sum < "$NEW_SCRIPT" | awk '{print $1}'); fi
  if should_reexec "$SELF_HASH" "$new_hash" "${BIRJA_DEPLOY_REEXEC:-}"; then
    echo "deploy.sh changed in $REF; re-running the new version"
    exec env BIRJA_DEPLOY_REEXEC=1 BIRJA_DEPLOY_SHA="$1" DEPLOY_REF="$REF" "$NEW_SCRIPT" "${SCRIPT_ARGS[@]}"
  fi
}

# live_sha <log>: SHA on top of the replayed stack (the last good release).
live_sha() {
  [ -f "$1" ] || return 0
  awk '
    NF < 4 { next }
    $4 == "rollback" {
      while (n > 0 && sha[n] != $2) n--
      if (n == 0) { n = 1; sha[1] = $2 }
      next
    }
    { n++; sha[n] = $2 }
    END { if (n > 0) print sha[n] }' "$1"
}

prune_releases() {
  STEP="prune releases"
  local cur keep d n=0
  cur=$(readlink -f "$WEB_ROOT/current")
  # keep the release a future --rollback would return to
  keep=$(rollback_target "$DEPLOY_LOG" 0 | awk '{print $2}')
  # newest first
  while IFS= read -r d; do
    n=$((n + 1))
    [ "$n" -le "$KEEP_RELEASES" ] && continue
    [ "$(readlink -f "$d")" = "$cur" ] && continue
    if printf '%s\n' "$keep" | grep -qxF "$d"; then continue; fi
    rm -rf -- "$d"
  done < <(ls -1dt "$WEB_ROOT"/releases/*/ 2>/dev/null | sed 's:/$::')
}

do_deploy() {
  local sha
  if [ "${BIRJA_DEPLOY_REEXEC:-}" = 1 ] && [ -n "${BIRJA_DEPLOY_SHA:-}" ]; then
    # re-exec'd by the previous script: same commit, no second fetch
    STEP="git rev-parse"
    sha=$(git -C "$APP_DIR" rev-parse --verify --quiet "$BIRJA_DEPLOY_SHA^{commit}") \
      || { application_schema_incompatible; return 1; }
  else
    STEP="git fetch"
    git -C "$APP_DIR" fetch --prune --tags origin
    if sha=$(git -C "$APP_DIR" rev-parse --verify --quiet "origin/$REF^{commit}"); then :
    elif sha=$(git -C "$APP_DIR" rev-parse --verify --quiet "$REF^{commit}"); then :
    else application_schema_incompatible; return 1
    fi
  fi
  STEP="application schema compatibility"
  admit_application_source "$sha" || return 1
  install -d -m 755 "$STATE_DIR"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$PENDING_MARK"
  STEP="git checkout"
  checkout_source "$sha"
  maybe_reexec "$sha"
  echo "Deploying $REF = $(git -C "$APP_DIR" rev-parse --short HEAD)"

  if [ ! -d "$APP_DIR/backend" ] || [ ! -f "$APP_DIR/docker-compose.prod.yml" ]; then
    echo "ref '$REF' has no backend/ or docker-compose.prod.yml, refusing" >&2
    exit 1
  fi

  # Prepare everything that is likely to fail first (image build, npm,
  # nginx config test). Nothing live changes until all of it has passed.
  STEP="list services"
  local services
  services=$(app_services)
  STEP="build backend"
  # shellcheck disable=SC2086 # $services is a word list on purpose
  dc build $services
  build_frontend_release
  STEP="nginx config check"
  "$BIRJA_RETAINED_DIR/deploy/check-nginx-config.sh"

  # Go live: schema, backend, static release, nginx.
  STEP="start postgres and redis"
  dc up -d --wait postgres redis
  bindings --check-running
  STEP="migrate"
  dc --profile migrate build migrate
  dc --profile migrate run --rm --no-deps migrate >/dev/null 2>&1
  STEP="start backend"
  # shellcheck disable=SC2086 # word list on purpose; --remove-orphans drops a scheduler this release lacks
  dc up -d --wait --remove-orphans $services
  bindings --check-running
  swap_current "$RELEASE_DIR"
  STEP="nginx install"
  "$BIRJA_RETAINED_DIR/deploy/install-nginx.sh"
  health_check
  record "$REF"
  prune_releases
  echo "Deploy complete: $REF"
}

do_rollback() {
  STEP="rollback lookup"
  local failed=0 target sha rel live
  live=$(live_sha "$DEPLOY_LOG")
  if [ -e "$PENDING_MARK" ] || { [ -n "$live" ] && [ "$(git -C "$APP_DIR" rev-parse HEAD)" != "$live" ]; }; then
    failed=1
    echo "The last deploy did not finish: returning to the last good release."
  fi
  target=$(rollback_target "$DEPLOY_LOG" "$failed")
  if [ -z "$target" ]; then
    echo "nothing to roll back to (no earlier release with a different SHA)" >&2
    exit 1
  fi
  sha=${target%% *}
  rel=${target#* }
  STEP="rollback application schema compatibility"
  admit_application_source "$sha" || return 1
  # Rollback logs store immutable SHAs. Accept only the tested release or the
  # retained bundle's tested current source, never arbitrary historical refs.
  local old_sha
  old_sha=$(git -C "$APP_DIR" rev-parse --verify 'v0.3.1^{commit}')
  [ "$sha" = "$old_sha" ] || [ "$sha" = "$BIRJA_TESTED_SOURCE" ] \
    || { echo "rollback target is outside the supported compatibility set" >&2; return 1; }
  echo "Rollback target: $sha ($rel)"
  STEP="rollback checkout"
  checkout_source "$sha"
  echo "Rolling back to $(git -C "$APP_DIR" rev-parse --short HEAD)"
  STEP="rollback list services"
  local services
  services=$(app_services)
  STEP="rollback build backend"
  # shellcheck disable=SC2086 # $services is a word list on purpose
  dc build $services
  if [ -d "$rel" ]; then
    RELEASE_DIR="$rel"
  else
    build_frontend_release
  fi
  # The rolled-back frontend gets the nginx config (CSP etc.) of its own
  # release. Files that release does not know (e.g. newer birja-* confs)
  # stay installed.
  if [ -x "$BIRJA_RETAINED_DIR/deploy/check-nginx-config.sh" ]; then
    STEP="rollback nginx config check"
    "$BIRJA_RETAINED_DIR/deploy/check-nginx-config.sh"
  fi
  STEP="rollback backend"
  # shellcheck disable=SC2086 # word list on purpose; --remove-orphans removes the scheduler when the target has none
  dc up -d --wait --remove-orphans $services
  bindings --check-running
  echo "WARNING: migrations are NOT undone; the schema stays at the newer revision." >&2
  echo "Incompatible schema recovery requires a separately approved manual procedure." >&2
  swap_current "$RELEASE_DIR"
  STEP="rollback nginx install"
  "$BIRJA_RETAINED_DIR/deploy/install-nginx.sh"
  health_check
  record rollback
}

main() {
  [ -n "${BIRJA_RETAINED_DIR:-}" ] || { echo "Use /usr/local/sbin/birja-deploy (retained security bundle required)." >&2; exit 1; }
  BIRJA_TESTED_SOURCE=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["tested_source"])' "$BIRJA_RETAINED_DIR/MANIFEST.json")
  supported_ref "$REF" || { echo "unsupported deployment ref" >&2; exit 2; }
  SCRIPT_ARGS=("$@")
  case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "") MODE=deploy
        [ "$REF" != rollback ] || { echo "'rollback' is reserved in the deploy log, not a ref" >&2; exit 2; } ;;
    --rollback) MODE=rollback ;;
    --start-selected-datastores) MODE=start-selected ;;
    *) usage >&2; exit 2 ;;
  esac
  trap on_err ERR
  RELEASE_DIR=""
  BUILD_TMP=""
  preflight
  case "$MODE" in
    rollback) do_rollback ;;
    start-selected) start_selected_datastores ;;
    *) do_deploy ;;
  esac
}

# Everything above only defines functions and variables; this block is parsed
# as one compound command before it runs and exits, so bash never reads this
# file again after the checkout rewrites it. Skipped when sourced by
# deploy/tests/.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
  exit
fi
