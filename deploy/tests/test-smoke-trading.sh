#!/usr/bin/env bash
# Offline test of smoke-prod.sh's trading_requires_auth check (04-05).
# Sources smoke-prod.sh (returns before any check runs) and stubs curlq,
# pass and fail. Touches no network and no host state.
#   deploy/tests/test-smoke-trading.sh
set -uo pipefail

HERE="$(dirname "$(readlink -f "$0")")"
# shellcheck source=../smoke-prod.sh
. "$HERE/../smoke-prod.sh"

HOLD=401
QUOTE=403
curlq() { # prints the status chosen for the requested URL (last argument)
  local a url=""
  for a in "$@"; do url=$a; done
  case "$url" in
    */holdings/BTC) printf '%s' "$HOLD" ;;
    */trades/quote) printf '%s' "$QUOTE" ;;
    *) printf '000' ;;
  esac
}
PASSES=0
FAILS_SEEN=0
pass() { PASSES=$((PASSES + 1)); }
fail() { FAILS_SEEN=$((FAILS_SEEN + 1)); }

FAILS=0
N=0
ok() { N=$((N + 1)); echo "ok    $1"; }
bad() { N=$((N + 1)); FAILS=$((FAILS + 1)); echo "FAIL  $1"; }

# expect <name> <holdings status> <quote status> <want passes> <want fails>
expect() {
  HOLD=$2
  QUOTE=$3
  PASSES=0
  FAILS_SEEN=0
  trading_requires_auth
  if [ "$PASSES" = "$4" ] && [ "$FAILS_SEEN" = "$5" ]; then
    ok "$1"
  else
    bad "$1: passes=$PASSES fails=$FAILS_SEEN (want $4/$5)"
  fi
}

expect "holdings 401 + quote 403 -> 2 passes" 401 403 2 0
expect "holdings 401 + quote 401 -> 2 passes" 401 401 2 0
expect "holdings 200 -> fail" 200 403 1 1
expect "quote 200 -> fail" 401 200 1 1
expect "quote 404 (release missing) -> fail" 401 404 1 1
expect "quote 500 -> fail" 401 500 1 1
expect "both 404 -> 2 fails" 404 404 0 2

echo "$((N - FAILS))/$N passed"
[ "$FAILS" -eq 0 ]
