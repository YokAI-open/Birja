#!/usr/bin/env bash
# Birja production deploy (the single deploy command, D-02).
#
#   /srv/birja/deploy/deploy.sh              deploy main
#   DEPLOY_REF=<branch|tag|sha> /srv/birja/deploy/deploy.sh
#   /srv/birja/deploy/deploy.sh --rollback   return to the previous deploy
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
LOCK=/var/lock/birja-deploy.lock            # prevents concurrent deploys
HOST=birja.nist.one                         # public host name
CERT=/etc/nginx/certs/nist.one/fullchain.pem  # installed origin certificate
NODE_IMAGE=node:24.22.1-trixie-slim         # same pin as frontend/Dockerfile
KEEP_RELEASES=3                             # static releases kept on disk
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
  --rollback   redeploy the previous entry of $DEPLOY_LOG
  -h, --help   this text
Note: rollback does not undo database migrations.
USAGE
}

on_err() {
  local rc=$?
  echo "FAILED at step: $STEP (exit $rc)" >&2
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

build_frontend_release() {
  STEP="frontend build"
  docker run --rm -v "$APP_DIR/frontend":/app -w /app "$NODE_IMAGE" sh -c 'npm ci && npm run build'
  STEP="frontend release"
  local sha ts rel
  sha=$(git -C "$APP_DIR" rev-parse --short HEAD)
  ts=$(date -u +%Y%m%dT%H%M%SZ)
  rel="$WEB_ROOT/releases/$sha-$ts"
  install -d "$rel"
  cp -a "$APP_DIR/frontend/dist/." "$rel/"
  chmod -R a+rX "$rel"
  RELEASE_DIR="$rel"
  swap_current "$rel"
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
}

prune_releases() {
  STEP="prune releases"
  local cur keep d n=0
  cur=$(readlink -f "$WEB_ROOT/current")
  keep=$(tail -n 2 "$DEPLOY_LOG" 2>/dev/null | awk '{print $3}' || true)
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

  STEP="start postgres and redis"
  dc up -d --wait postgres redis
  STEP="build backend"
  dc build backend
  STEP="migrate"
  dc run --rm --no-deps backend alembic upgrade head
  STEP="start backend"
  dc up -d --wait backend
  build_frontend_release
  STEP="nginx install"
  "$APP_DIR/deploy/install-nginx.sh"
  health_check
  record "$REF"
  prune_releases
  echo "Deploy complete: $REF"
}

do_rollback() {
  STEP="rollback lookup"
  local lines line sha rel
  lines=$(wc -l < "$DEPLOY_LOG" 2>/dev/null || echo 0)
  if [ "$lines" -lt 2 ]; then
    echo "nothing to roll back to" >&2
    exit 1
  fi
  line=$(tail -n 2 "$DEPLOY_LOG" | head -n 1)
  sha=$(printf '%s\n' "$line" | awk '{print $2}')
  rel=$(printf '%s\n' "$line" | awk '{print $3}')
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
    swap_current "$rel"
  else
    build_frontend_release
  fi
  health_check
  record rollback
}

main() {
  case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    "") MODE=deploy ;;
    --rollback) MODE=rollback ;;
    *) usage >&2; exit 2 ;;
  esac
  trap on_err ERR
  RELEASE_DIR=""
  preflight
  if [ "$MODE" = rollback ]; then do_rollback; else do_deploy; fi
}

main "$@"
exit
