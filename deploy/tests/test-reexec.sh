#!/usr/bin/env bash
# Offline test of deploy.sh's self re-exec after checkout (hotfix 0.2.1).
# Touches nothing on the host: sources deploy.sh (main does not run), checks
# the should_reexec decision, then runs maybe_reexec against a stub script in
# a temp dir and checks the flock handover the re-exec'd run relies on.
#   deploy/tests/test-reexec.sh
set -Eeuo pipefail

HERE="$(dirname "$(readlink -f "$0")")"
# shellcheck source=../deploy.sh
. "$HERE/../deploy.sh"
set +e
trap - ERR

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAILS=0
N=0

check() { # check <name> <want 0|1> <cmd...>: want 0 = command succeeds
  local name=$1 want=$2 got
  shift 2
  if "$@"; then got=0; else got=1; fi
  N=$((N + 1))
  if [ "$got" = "$want" ]; then echo "ok    $name"; else echo "FAIL  $name: want $want got $got"; FAILS=$((FAILS + 1)); fi
}

# decision
check "same hash -> no re-exec" 1 should_reexec aaa aaa ""
check "changed hash -> re-exec" 0 should_reexec aaa bbb ""
check "changed hash, guard set -> no second re-exec" 1 should_reexec aaa bbb 1
check "guard set, same hash -> no re-exec" 1 should_reexec aaa aaa 1
check "unknown running hash -> no re-exec" 1 should_reexec "" bbb ""
check "missing checked-out script -> no re-exec" 1 should_reexec aaa "" ""
check "guard value other than 1 is not the guard" 0 should_reexec aaa bbb 0

# SELF_HASH is the hash of the sourced deploy.sh
check "SELF_HASH matches deploy.sh on disk" 0 \
  [ "$SELF_HASH" = "$(sha256sum < "$HERE/../deploy.sh" | awk '{print $1}')" ]

# maybe_reexec against a stub "new" deploy.sh: it records what it was given
STUB=$TMP/deploy.sh
cat > "$STUB" <<'STUB'
#!/usr/bin/env bash
printf 'guard=%s sha=%s ref=%s args=%s\n' "${BIRJA_DEPLOY_REEXEC:-}" "${BIRJA_DEPLOY_SHA:-}" "${DEPLOY_REF:-}" "$*"
STUB
chmod +x "$STUB"
NEW_SCRIPT=$STUB
REF=v9.9.9

OUT=$( (SCRIPT_ARGS=(); unset BIRJA_DEPLOY_REEXEC; maybe_reexec abc123; echo "continued") 2>&1)
check "changed script -> logs and execs the new one with guard, sha, ref" 0 \
  [ "$OUT" = "deploy.sh changed in v9.9.9; re-running the new version
guard=1 sha=abc123 ref=v9.9.9 args=" ]

OUT=$( (SCRIPT_ARGS=(); BIRJA_DEPLOY_REEXEC=1; maybe_reexec abc123; echo "continued") 2>&1)
check "guard already set -> continues, no exec" 0 [ "$OUT" = continued ]

OUT=$( (SCRIPT_ARGS=(); unset BIRJA_DEPLOY_REEXEC; SELF_HASH=$(sha256sum < "$STUB" | awk '{print $1}'); maybe_reexec abc123; echo "continued") 2>&1)
check "unchanged script -> continues, no exec" 0 [ "$OUT" = continued ]

OUT=$( (SCRIPT_ARGS=(); unset BIRJA_DEPLOY_REEXEC; NEW_SCRIPT=$TMP/missing.sh; maybe_reexec abc123; echo "continued") 2>&1)
check "checked-out ref without deploy.sh -> continues, no exec" 0 [ "$OUT" = continued ]

# lock handover: exec keeps fd 9 (same open file, lock still held); the
# re-exec'd preflight recognises it and does not reopen it.
LOCKF=$TMP/lock
OUT=$( (
  exec 9>"$LOCKF"
  flock -n 9 || { echo "parent could not lock"; exit 1; }
  exec env BIRJA_DEPLOY_REEXEC=1 LOCKF="$LOCKF" bash -c '
    if [ "${BIRJA_DEPLOY_REEXEC:-}" = 1 ] && [ /dev/fd/9 -ef "$LOCKF" ]; then echo inherited; else echo reopened; fi
    flock -n 9 && echo relocked
    flock -n "$LOCKF" true && echo "others-could-lock" || echo "others-blocked"'
) 2>&1)
check "re-exec'd run inherits the held lock; others stay blocked" 0 \
  [ "$OUT" = "inherited
relocked
others-blocked" ]
check "lock is free once the deploy exits" 0 flock -n "$LOCKF" true

echo "$((N - FAILS))/$N passed"
[ "$FAILS" -eq 0 ]
