#!/usr/bin/env bash
# Cloudflare DNS helper for birja.nist.one (D-04).
#   cloudflare-dns.sh check    verify token, zone access and show current record
#   cloudflare-dns.sh ensure   idempotently create/fix the proxied A record
# Token: /root/.secrets/cloudflare.env (root, 600) with CF_Token and CF_Zone_ID.
# The token never goes on a command line or to stdout.
# Undo: delete the record in the Cloudflare dashboard (DNS, Records, birja,
# Delete), or DELETE $API/zones/<zone>/dns_records/<id> with the same token.
# Revoke the token in My Profile, API Tokens, when it is no longer needed.
set -Eeuo pipefail

API=https://api.cloudflare.com/client/v4
NAME=birja.nist.one
ORIGIN_IP=151.243.171.52
ENV_FILE=/root/.secrets/cloudflare.env

[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }

load_token() {
    [ -f "$ENV_FILE" ] || { echo "missing $ENV_FILE" >&2; exit 1; }
    [ "$(stat -c '%U %a' "$ENV_FILE")" = "root 600" ] \
        || { echo "$ENV_FILE must be owned by root with mode 600" >&2; exit 1; }
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
    [ -n "${CF_Token:-}" ] || { echo "token variable is empty or missing" >&2; exit 1; }
    [ -n "${CF_Zone_ID:-}" ] || { echo "CF_Zone_ID is empty or missing" >&2; exit 1; }
    [[ "$CF_Zone_ID" =~ ^[0-9a-f]{32}$ ]] || { echo "CF_Zone_ID is not 32 hex chars" >&2; exit 1; }
}

cf() {
    curl -sS --max-time 20 -K <(printf 'header = "Authorization: Bearer %s"\n' "$CF_Token") \
        -H 'Content-Type: application/json' "$@"
}

# Prints "OK" or the error code/message pairs; exit 0 when success is true.
report() { # label  (JSON on stdin)
    python3 -I -c '
import json, sys
label = sys.argv[1]
try:
    d = json.load(sys.stdin)
except Exception:
    print(label + ": FAILED (unparseable response)"); sys.exit(1)
if d.get("success"):
    print(label + ": success")
    sys.exit(0)
print(label + ": FAILED")
for e in d.get("errors", []):
    print("  error %s: %s" % (e.get("code"), e.get("message")))
sys.exit(1)
' "$1"
}

cmd_check() {
    local tmp
    tmp="$(mktemp)"
    # shellcheck disable=SC2064
    trap "rm -f '$tmp'" RETURN

    cf "$API/user/tokens/verify" > "$tmp"
    report "token verify" < "$tmp" || exit 1
    python3 -I -c '
import json, sys
d = json.load(open(sys.argv[1]))
st = d.get("result", {}).get("status")
print("token status: %s" % st)
sys.exit(0 if st == "active" else 1)
' "$tmp" || exit 1

    cf "$API/zones/$CF_Zone_ID" > "$tmp"
    report "zone read (needs Zone:Zone:Read)" < "$tmp" || exit 1
    python3 -I -c '
import json, sys
d = json.load(open(sys.argv[1]))
n = d.get("result", {}).get("name")
print("zone name: %s" % n)
sys.exit(0 if n == "nist.one" else 1)
' "$tmp" || { echo "zone is not nist.one" >&2; exit 1; }

    cf "$API/zones/$CF_Zone_ID/dns_records?name=$NAME" > "$tmp"
    report "dns records read (needs Zone:DNS:Edit)" < "$tmp" || exit 1
    python3 -I -c '
import json, sys
d = json.load(open(sys.argv[1]))
rs = d.get("result", [])
if not rs:
    print("record: absent")
for r in rs:
    print("record: %s %s %s proxied=%s" % (r.get("name"), r.get("type"), r.get("content"), r.get("proxied")))
' "$tmp"
}

cmd_ensure() {
    cmd_check
    local tmp plan id
    tmp="$(mktemp)"
    # shellcheck disable=SC2064
    trap "rm -f '$tmp'" RETURN

    cf "$API/zones/$CF_Zone_ID/dns_records?name=$NAME" > "$tmp"
    # Output: "none", "ok", "patch <id>", or "conflict".
    plan="$(python3 -I -c '
import json, sys
rs = json.load(open(sys.argv[1])).get("result", [])
ip = sys.argv[2]
if not rs:
    print("none")
elif any(r.get("type") != "A" for r in rs) or len(rs) > 1:
    print("conflict")
else:
    r = rs[0]
    if r.get("content") == ip and r.get("proxied") is True:
        print("ok")
    else:
        print("patch " + r["id"])
' "$tmp" "$ORIGIN_IP")"

    case "$plan" in
        conflict)
            echo "ABORT: $NAME has a non-A or multiple records; resolve manually" >&2
            exit 1 ;;
        none)
            cf -X POST "$API/zones/$CF_Zone_ID/dns_records" \
                --data '{"type":"A","name":"birja","content":"151.243.171.52","proxied":true,"ttl":1,"comment":"Birja prod (phase 02.1)"}' \
                | report "create A record" || exit 1 ;;
        patch\ *)
            id="${plan#patch }"
            [[ "$id" =~ ^[0-9a-f]{32}$ ]] || { echo "unexpected record id" >&2; exit 1; }
            cf -X PATCH "$API/zones/$CF_Zone_ID/dns_records/$id" \
                --data '{"content":"151.243.171.52","proxied":true}' \
                | report "update A record" || exit 1 ;;
        ok)
            echo "unchanged" ;;
        *)
            echo "unexpected plan" >&2; exit 1 ;;
    esac

    cf "$API/zones/$CF_Zone_ID/dns_records?name=$NAME&type=A" > "$tmp"
    python3 -I -c '
import json, sys
rs = json.load(open(sys.argv[1])).get("result", [])
if len(rs) != 1 or rs[0].get("proxied") is not True or rs[0].get("content") != sys.argv[2]:
    print("ASSERT FAILED: record not proxied to origin"); sys.exit(1)
r = rs[0]
print("record: %s %s %s proxied=%s" % (r["name"], r["type"], r["content"], r["proxied"]))
' "$tmp" "$ORIGIN_IP"
}

case "${1:-}" in
    check)  load_token; cmd_check ;;
    ensure) load_token; cmd_ensure ;;
    *) echo "usage: $0 check|ensure" >&2; exit 2 ;;
esac
