#!/usr/bin/env bash
# Offline test of deploy.sh's rollback target selection (CR-01).
# Touches nothing on the host: sources deploy.sh (main does not run) and
# feeds sample deploys.log files from a temp dir.
#   deploy/tests/test-rollback-target.sh
set -Eeuo pipefail

HERE="$(dirname "$(readlink -f "$0")")"
# shellcheck source=../deploy.sh
. "$HERE/../deploy.sh"
set +e

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAILS=0
N=0

# log <file> <entry>...: entry is "sha ref", release dir is derived from sha
log() {
  local f=$1 e i=0
  shift
  : > "$f"
  for e in "$@"; do
    i=$((i + 1))
    printf '2026-10-27T00:00:%02dZ %s /var/www/birja/releases/%s-%02d %s\n' \
      "$i" "${e% *}" "${e% *}" "$i" "${e#* }" >> "$f"
  done
}

# expect <name> <file> <failed> <want sha or "">
expect() {
  local got
  got=$(rollback_target "$2" "$3" | awk '{print $1}')
  N=$((N + 1))
  if [ "$got" = "$4" ]; then
    echo "ok    $1"
  else
    echo "FAIL  $1: want '${4}' got '${got}'"
    FAILS=$((FAILS + 1))
  fi
}

expect_live() {
  local got
  got=$(live_sha "$2")
  N=$((N + 1))
  if [ "$got" = "$3" ]; then echo "ok    $1"; else echo "FAIL  $1: want '$3' got '$got'"; FAILS=$((FAILS + 1)); fi
}

L=$TMP/log

# basics
expect "missing log -> nothing" "$TMP/none" 0 ""
log "$L" "aaa main"
expect "single deploy -> nothing" "$L" 0 ""
expect "single deploy, failed next deploy -> that deploy" "$L" 1 aaa
log "$L" "aaa main" "bbb main"
expect "two deploys -> previous" "$L" 0 aaa

# (a) duplicate consecutive SHAs
log "$L" "aaa main" "bbb main" "bbb main"
expect "(a) same SHA deployed twice -> skip to the distinct one" "$L" 0 aaa
log "$L" "aaa main" "aaa main"
expect "(a) only one distinct SHA -> nothing" "$L" 0 ""

# (b) a failed deploy never logged: the last logged deploy is the last good one
log "$L" "aaa main" "bbb main"
expect "(b) failed deploy of ccc -> last good bbb, not aaa" "$L" 1 bbb
log "$L" "aaa main" "bbb main" "bbb rollback"
expect "(b) after rolling back the failed deploy -> next is aaa" "$L" 0 aaa
log "$L" "aaa main" "bbb main" "bbb main"
expect "(b) failed deploy after duplicates -> bbb" "$L" 1 bbb

# (c) repeated rollbacks never return to a rolled-back release
log "$L" "aaa main" "bbb main" "ccc main" "bbb rollback"
expect "(c) second rollback -> aaa, not ccc" "$L" 0 aaa
expect_live "(c) live after first rollback is bbb" "$L" bbb
log "$L" "aaa main" "bbb main" "ccc main" "bbb rollback" "aaa rollback"
expect "(c) third rollback -> nothing, not bbb/ccc" "$L" 0 ""
expect_live "(c) live after second rollback is aaa" "$L" aaa
log "$L" "aaa main" "bbb main" "bbb main" "ccc main" "bbb rollback"
expect "(c)+(a) rollback past duplicates -> aaa" "$L" 0 aaa
log "$L" "aaa main" "bbb main" "aaa rollback" "ccc main"
expect "(c) deploy after rollback -> aaa (bbb was rolled back)" "$L" 0 aaa
log "$L" "aaa main" "bbb main" "aaa main" "ccc main" "aaa rollback"
expect "(c) redeployed SHA in history -> bbb" "$L" 0 bbb

# the live host's log at the time of the review (old script wrote these)
cat > "$L" <<'LOG'
2026-10-27T19:12:32Z 54b21b363f4f93d0f8f79224c0588c70c61ffdba /var/www/birja/releases/54b21b3-20261027T191231Z feature/deploy-nist-one
2026-10-27T19:12:41Z 54b21b363f4f93d0f8f79224c0588c70c61ffdba /var/www/birja/releases/54b21b3-20261027T191137Z rollback
2026-10-27T19:13:12Z 54b21b363f4f93d0f8f79224c0588c70c61ffdba /var/www/birja/releases/54b21b3-20261027T191311Z feature/deploy-nist-one
2026-10-27T19:53:11Z 11a0161f7559d418ea62de0ec58b3c81f19f3cd4 /var/www/birja/releases/11a0161-20261027T195310Z main
2026-10-27T19:53:52Z 11a0161f7559d418ea62de0ec58b3c81f19f3cd4 /var/www/birja/releases/11a0161-20261027T195351Z main
LOG
expect "live host log -> 54b21b3, not a no-op" "$L" 0 54b21b363f4f93d0f8f79224c0588c70c61ffdba
REL=$(rollback_target "$L" 0 | awk '{print $2}')
N=$((N + 1))
if [ "$REL" = /var/www/birja/releases/54b21b3-20261027T191311Z ]; then echo "ok    live host log -> newest 54b21b3 release"; else echo "FAIL  release: $REL"; FAILS=$((FAILS + 1)); fi

echo "$((N - FAILS))/$N passed"
[ "$FAILS" -eq 0 ]
