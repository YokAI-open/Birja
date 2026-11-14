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
git -C "$APP_DIR" -c user.name=Test -c user.email=test@example.invalid commit -q --allow-empty -m tested
BIRJA_TESTED_SOURCE=$(git -C "$APP_DIR" rev-parse HEAD)
git -C "$APP_DIR" branch -f main
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
  fi
  # A separate open description cannot take the inherited operation lock.
  ( exec 8>"$LOCK"; ! flock -n 8 )
  echo "ok $mode revision=$revision target=$target pending=$pending $want"
}
for ref in v0.3.1 "$OLD" deadbeef missing ''; do run_case deploy 0014 "$ref" no refuse; done
git -C "$APP_DIR" branch -f main "$OLD"
run_case deploy 0014 main yes refuse
git -C "$APP_DIR" branch -f main "$BIRJA_TESTED_SOURCE"
for revision in '' 0015 invalid 0014-bad; do run_case deploy "$revision" main no refuse; done
run_case deploy 0014 "$BIRJA_TESTED_SOURCE" no pass
run_case deploy 0014 main no pass
run_case rollback 0014 main no refuse
run_case rollback 0014 main yes pass
for revision in 0007 0008 0013; do run_case deploy "$revision" v0.3.1 no pass; done
