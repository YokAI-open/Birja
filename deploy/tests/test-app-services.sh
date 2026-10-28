#!/usr/bin/env bash
# Offline test of deploy.sh's app_services (hotfix 0.2.2, WR-05).
# Touches nothing on the host: sources deploy.sh (main does not run) and
# replaces dc with stubs, so docker is never called.
#   deploy/tests/test-app-services.sh
set -Eeuo pipefail

HERE="$(dirname "$(readlink -f "$0")")"
# shellcheck source=../deploy.sh
. "$HERE/../deploy.sh"
set +e
trap - ERR

FAILS=0
N=0

check() { # check <name> <want> <got>
  N=$((N + 1))
  if [ "$3" = "$2" ]; then echo "ok    $1"; else echo "FAIL  $1: want '$2' got '$3'"; FAILS=$((FAILS + 1)); fi
}

dc() { printf 'postgres\nredis\nbackend\nscheduler\n'; }
check "scheduler defined -> backend scheduler" "backend scheduler" "$(app_services)"

dc() { printf 'postgres\nredis\nbackend\n'; }
check "no scheduler (pre-Phase 3 release) -> backend" "backend" "$(app_services)"

dc() { printf 'scheduler-old\nbackend\n'; }
check "only an exact 'scheduler' line counts" "backend" "$(app_services)"

dc() { echo "invalid interpolation format" >&2; return 1; }
OUT=$(app_services 2>/dev/null); RC=$?
check "dc config failure -> non-zero" 1 "$RC"
check "dc config failure -> no service list printed" "" "$OUT"

# The deploy and rollback paths must abort on that failure: run the call
# site pattern under set -e and see that the build line is never reached.
OUT=$(bash -c '
  set -Eeuo pipefail
  . "$1"
  dc() { [ "$1" = config ] && return 1; echo "dc $*"; }
  services=$(app_services)
  dc build $services
' _ "$HERE/../deploy.sh" 2>/dev/null); RC=$?
check "set -e stops before 'dc build' when dc config fails" "1:" "$RC:$OUT"

# Every caller assigns the list on its own line; an inline $(app_services) in
# a dc command would swallow the failure again.
check "no inline \$(app_services) in dc commands" "0" \
  "$(grep -cE '^[^#]*dc .*\$\(app_services\)' "$HERE/../deploy.sh")"
check "deploy and rollback both assign services=\$(app_services)" "2" \
  "$(grep -cE '^[[:space:]]*services=\$\(app_services\)$' "$HERE/../deploy.sh")"

echo "$((N - FAILS))/$N passed"
[ "$FAILS" = 0 ]
