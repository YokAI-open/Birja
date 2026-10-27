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
NODE_IMAGE=node:24.22.1-trixie-slim         # same pin as frontend/Dockerfile
KEEP_RELEASES=3                             # static releases kept on disk
BUILD_UID=1000                              # unprivileged uid for the npm build (node in the image)
REF="${DEPLOY_REF:-main}"                   # D-05: ref override

STEP="startup"

dc() {
  docker compose -f "$APP_DIR/docker-compose.prod.yml" --env-file "$ENV_FILE" "$@"
}

usage() {
  cat <<USAGE
Usage: deploy.sh [--rollback]
  (no args)    deploy origin/main (or the ref in DEPLOY_REF)
  DEPLOY_REF=<branch|tag|sha> deploy.sh   deploy that ref instead of main
  --rollback   return to the release that was live before the current one
               (see the header of this script for how it is chosen)
  -h, --help   this text
Note: rollback does not undo database migrations.
USAGE
}

on_err() {
  local rc=$?
  echo "FAILED at step: $STEP (exit $rc)" >&2
  if [ -n "${BUILD_TMP:-}" ]; then rm -rf -- "$BUILD_TMP" || true; fi
  echo "--- last 50 backend log lines (redacted) ---" >&2
  dc logs --no-color --tail 50 backend 2>&1 \
    | sed -E 's/code=[0-9]{6}/code=******/g; s/to=[^ ]+/to=***/g' >&2 || true
  echo "To roll back: /srv/birja/deploy/deploy.sh --rollback" >&2
  exit "$rc"
}

preflight() {
  STEP="preflight"
  [ "$(id -u)" -eq 0 ] || { echo "must run as root" >&2; exit 1; }
  exec 9>"$LOCK"
  flock -n 9 || { echo "another deploy is running" >&2; exit 1; }
  git -C "$APP_DIR" rev-parse --git-dir >/dev/null 2>&1 \
    || { echo "$APP_DIR is not a git checkout" >&2; exit 1; }
  [ -z "$(git -C "$APP_DIR" status --porcelain)" ] \
    || { echo "$APP_DIR has uncommitted changes, refusing" >&2; exit 1; }
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
}

health_check() {
  STEP="health check"
  local i
  for i in $(seq 1 15); do
    if curl -fsS --resolve "$HOST:443:127.0.0.1" "https://$HOST/api/v1/health" 2>/dev/null \
        | python3 -I -c 'import json,sys; sys.exit(0 if json.load(sys.stdin).get("status")=="ok" else 1)' 2>/dev/null \
      && curl -fsS --resolve "$HOST:443:127.0.0.1" "https://$HOST/" 2>/dev/null | grep -q 'id="root"'; then
      echo "Health check passed"
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
  local sha ts rel dist
  BUILD_TMP=$(mktemp -d)                    # root 700: host users cannot reach inside
  git -C "$APP_DIR" archive HEAD frontend | tar -x -C "$BUILD_TMP"
  chown -R "$BUILD_UID:$BUILD_UID" "$BUILD_TMP/frontend"
  docker run --rm --user "$BUILD_UID:$BUILD_UID" -e HOME=/tmp -e npm_config_cache=/tmp/.npm \
    -v "$BUILD_TMP/frontend":/app -w /app "$NODE_IMAGE" \
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
  install -d -m 755 "$STATE_DIR"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$PENDING_MARK"
  STEP="git fetch"
  git -C "$APP_DIR" fetch --prune --tags origin
  local sha
  if sha=$(git -C "$APP_DIR" rev-parse --verify --quiet "origin/$REF^{commit}"); then :
  elif sha=$(git -C "$APP_DIR" rev-parse --verify --quiet "$REF^{commit}"); then :
  else echo "cannot resolve ref '$REF'" >&2; exit 1
  fi
  STEP="git checkout"
  git -C "$APP_DIR" checkout --detach "$sha"
  echo "Deploying $REF = $(git -C "$APP_DIR" rev-parse --short HEAD)"

  if [ ! -d "$APP_DIR/backend" ] || [ ! -f "$APP_DIR/docker-compose.prod.yml" ]; then
    echo "ref '$REF' has no backend/ or docker-compose.prod.yml, refusing" >&2
    exit 1
  fi

  # Prepare everything that is likely to fail first (image build, npm,
  # nginx config test). Nothing live changes until all of it has passed.
  STEP="build backend"
  dc build backend
  build_frontend_release
  STEP="nginx config check"
  "$APP_DIR/deploy/check-nginx-config.sh"

  # Go live: schema, backend, static release, nginx.
  STEP="start postgres and redis"
  dc up -d --wait postgres redis
  STEP="migrate"
  dc run --rm --no-deps backend alembic upgrade head
  STEP="start backend"
  dc up -d --wait backend
  swap_current "$RELEASE_DIR"
  STEP="nginx install"
  "$APP_DIR/deploy/install-nginx.sh"
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
  echo "Rollback target: $sha ($rel)"
  STEP="rollback checkout"
  git -C "$APP_DIR" checkout --detach "$sha"
  echo "Rolling back to $(git -C "$APP_DIR" rev-parse --short HEAD)"
  STEP="rollback backend"
  dc build backend
  dc up -d --wait backend
  echo "WARNING: migrations are NOT undone; the schema stays at the newer revision." >&2
  echo "A schema-incompatible rollback needs a manual alembic downgrade (no backups until Phase 6)." >&2
  if [ -d "$rel" ]; then
    RELEASE_DIR="$rel"
  else
    build_frontend_release
  fi
  swap_current "$RELEASE_DIR"
  health_check
  record rollback
}

main() {
  case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "") MODE=deploy
        [ "$REF" != rollback ] || { echo "'rollback' is reserved in the deploy log, not a ref" >&2; exit 2; } ;;
    --rollback) MODE=rollback ;;
    *) usage >&2; exit 2 ;;
  esac
  trap on_err ERR
  RELEASE_DIR=""
  BUILD_TMP=""
  preflight
  if [ "$MODE" = rollback ]; then do_rollback; else do_deploy; fi
}

# Parsed as one compound command before it runs (the checkout rewrites this
# file), and skipped when sourced by deploy/tests/.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  main "$@"
  exit
fi
