#!/usr/bin/env bash
# Offline test of smoke-prod.sh's published-port checks (hotfix 0.2.1).
# Touches nothing on the host: sources smoke-prod.sh (it returns before any
# check runs) and replaces `docker` with a stub that prints canned output.
#   deploy/tests/test-smoke-ports.sh
set -uo pipefail

HERE="$(dirname "$(readlink -f "$0")")"
# shellcheck source=../smoke-prod.sh
. "$HERE/../smoke-prod.sh"

FAILS=0
N=0
ok() { N=$((N + 1)); echo "ok    $1"; }
bad() { N=$((N + 1)); FAILS=$((FAILS + 1)); echo "FAIL  $1"; }

# expect_pub <name> <want 0|1> <lines>: want 0 = only_backend_published passes
expect_pub() {
  local got
  if printf '%s\n' "$3" | only_backend_published; then got=0; else got=1; fi
  if [ "$got" = "$2" ]; then ok "$1"; else bad "$1: want $2 got $got"; fi
}

expect_pub "backend loopback only -> pass" 0 "backend 8000/tcp -> 127.0.0.1:18000"
expect_pub "no bindings at all -> fail" 1 ""
expect_pub "backend on 0.0.0.0 -> fail" 1 "backend 8000/tcp -> 0.0.0.0:18000"
expect_pub "backend also on [::] -> fail" 1 "backend 8000/tcp -> 127.0.0.1:18000
backend 8000/tcp -> [::]:18000"
expect_pub "backend wrong host port -> fail" 1 "backend 8000/tcp -> 127.0.0.1:8000"
expect_pub "postgres published too -> fail" 1 "backend 8000/tcp -> 127.0.0.1:18000
postgres 5432/tcp -> 127.0.0.1:5432"
expect_pub "scheduler published too -> fail" 1 "scheduler 8000/tcp -> 127.0.0.1:18001
backend 8000/tcp -> 127.0.0.1:18000"
expect_pub "docker error -> fail" 1 "backend docker-port-error"

# host_bindings uses `docker port`; the stub mimics the v0.2.0 host, where
# `docker ps` showed "8000/tcp" for the scheduler (image EXPOSE, no binding).
docker() {
  [ "$1" = port ] || return 99
  case "$2" in
    sched) ;;                                         # EXPOSE only: empty, exit 0
    back) echo "8000/tcp -> 127.0.0.1:18000" ;;
    gone) echo "Error: No such container: gone" >&2; return 1 ;;
  esac
}
[ -z "$(host_bindings sched)" ] && ok "EXPOSE-only scheduler has no bindings" || bad "EXPOSE-only scheduler has no bindings"
[ "$(host_bindings back)" = "8000/tcp -> 127.0.0.1:18000" ] && ok "backend binding read from docker port" || bad "backend binding read from docker port"
[ "$(host_bindings gone)" = docker-port-error ] && ok "docker port failure is reported, not empty" || bad "docker port failure is reported, not empty"

echo "$((N - FAILS))/$N passed"
[ "$FAILS" -eq 0 ]
