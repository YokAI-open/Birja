#!/usr/bin/env bash
# Manual renewal of the *.nist.one + nist.one ZeroSSL ECC cert (D-03, D-07, D-08).
# No API token is used: DNS-01 validation is done by hand in acme.sh's manual
# DNS mode, as a two-step procedure:
#   1. renew-cert.sh start          order the cert, print the TXT record(s)
#      (the owner adds them in the Cloudflare dashboard, DNS only)
#   2. renew-cert.sh check [--wait] confirm the TXT value(s) over public DoH
#   3. renew-cert.sh finish         validate the same order, install the cert
# Run `start` exactly once per renewal: it saves the pending order inside
# acme.sh, and re-running it would consume that order.
# The existing acme.sh cron line stays untouched (D-06). In manual DNS mode it
# cannot renew this cert and only logs a failure (to /dev/null).
# The directory name and the conf file name contain a literal '*'.
# Undo: rm -r /etc/nginx/certs/nist.one
set -Eeuo pipefail

ACME=/root/.acme.sh/acme.sh
CERT_DIR='/root/.acme.sh/*.nist.one_ecc'
CONF="$CERT_DIR/"'*.nist.one.conf'
OUT_DIR=/etc/nginx/certs/nist.one
PENDING=/var/lib/birja/acme-txt.pending
MANUAL=--yes-I-know-dns-manual-mode-enough-go-ahead-please

usage() {
    cat <<'EOF'
usage: deploy/renew-cert.sh start | check [--wait] | finish | --help
  start         order the cert and print the TXT record(s) to add (run once)
  check         confirm the pending TXT value(s) are visible over DoH
  check --wait  same, retrying every 15 s for up to 10 minutes
  finish        validate, install to /etc/nginx/certs/nist.one, print dates
EOF
}

case "${1:-}" in
    -h | --help | help) usage; exit 0 ;;
esac

[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }

cmd_start() {
    if [ -e "$PENDING" ]; then
        echo "a challenge is already pending: run check/finish, or delete $PENDING to start over" >&2
        exit 1
    fi
    local out rc=0
    out="$(mktemp)"
    # shellcheck disable=SC2064
    trap "rm -f '$out'" EXIT
    set +e
    if [ -f "$CONF" ]; then
        "$ACME" --renew -d '*.nist.one' --ecc --force "$MANUAL" 2>&1 | tee "$out"
    else
        "$ACME" --issue --dns -d '*.nist.one' -d nist.one --keylength ec-256 --server zerossl "$MANUAL" 2>&1 | tee "$out"
    fi
    rc="${PIPESTATUS[0]}"
    set -e
    # Exit code 3 (CODE_DNS_MANUAL) is the expected result of step 1.
    if [ "$rc" != 0 ] && [ "$rc" != 3 ]; then
        echo "step 1 failed (exit $rc); read the acme.sh output above, do not loop" >&2
        exit 1
    fi
    local pairs
    pairs="$(python3 -I - "$out" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
names = re.findall(r"Domain: '([^']+)'", text)
vals = re.findall(r"TXT value: '([^']+)'", text)
for n, v in zip(names, vals):
    print(n, v)
PY
)"
    if [ -z "$pairs" ]; then
        if grep -q 'Cert success' "$out"; then
            echo "no challenge needed (valid authorizations): run 'finish' directly" >&2
            exit 0
        fi
        echo "step 1 failed; read the acme.sh output above, do not loop" >&2
        exit 1
    fi
    install -d -m 755 /var/lib/birja
    printf '%s\n' "$pairs" > "$PENDING"
    chmod 644 "$PENDING"
    echo
    echo "=== Add these DNS records in Cloudflare ==="
    while read -r name value; do
        echo "Type: TXT"
        echo "Name: _acme-challenge   (full: $name)"
        echo "Content: $value"
        echo "Proxy status: DNS only"
        echo "TTL: Auto"
        echo
    done < "$PENDING"
    echo "The apex and the wildcard share one name, so there may be two TXT"
    echo "records with the same name and different contents; both must exist."
    echo "Cloudflare dashboard -> nist.one -> DNS -> Records -> Add record"
    echo "Pending values are stored in $PENDING. Do not run 'start' again."
}

doh_check() {
    [ -f "$PENDING" ] || { echo "no pending challenge ($PENDING missing)" >&2; return 1; }
    local ok=0 name value json
    while read -r name value; do
        json="$(curl -fsS --max-time 10 -H 'accept: application/dns-json' \
            "https://cloudflare-dns.com/dns-query?name=${name}&type=TXT" || true)"
        if printf '%s' "$json" | python3 -I -c '
import json, sys
want = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(1)
have = [a["data"].strip("\"") for a in data.get("Answer", []) if a.get("type") == 16]
sys.exit(0 if want in have else 1)
' "$value"; then
            echo "found:   $name $value"
        else
            echo "missing: $name $value"
            ok=1
        fi
    done < "$PENDING"
    return "$ok"
}

cmd_check() {
    if [ "${1:-}" = "--wait" ]; then
        local i
        for i in $(seq 1 40); do
            doh_check && return 0
            [ "$i" -lt 40 ] && sleep 15
        done
        return 1
    fi
    doh_check
}

cmd_finish() {
    cmd_check || { echo "TXT record(s) not visible yet; not finishing" >&2; exit 1; }
    if ! "$ACME" --renew -d '*.nist.one' --ecc --force "$MANUAL"; then
        echo "step 2 failed; keeping $PENDING. Re-check DNS and retry 'finish' once; never re-run 'start' automatically" >&2
        exit 1
    fi
    install -d -m 750 "$OUT_DIR"
    "$ACME" --install-cert --ecc -d '*.nist.one' \
        --key-file "$OUT_DIR/key.pem" \
        --fullchain-file "$OUT_DIR/fullchain.pem" \
        --reloadcmd "systemctl try-reload-or-restart nginx"
    chmod 600 "$OUT_DIR/key.pem"
    rm -f "$PENDING"
    echo "--- installed certificate ---"
    openssl x509 -in "$OUT_DIR/fullchain.pem" -noout -subject -enddate -ext subjectAltName
    local end
    end="$(openssl x509 -in "$OUT_DIR/fullchain.pem" -noout -enddate | cut -d= -f2)"
    echo "Expires: $(date -u -d "$end" +%Y-%m-%d)"
    echo "Renew by: $(date -u -d "$end - 30 days" +%Y-%m-%d)"
    echo "--- acme.sh cron line (stays; cannot renew this cert in manual mode) ---"
    crontab -l | grep acme.sh || true
    echo "You may now delete the _acme-challenge TXT record(s) in Cloudflare"
}

case "${1:-}" in
    start) cmd_start ;;
    check) cmd_check "${2:-}" ;;
    finish) cmd_finish ;;
    *) usage >&2; exit 2 ;;
esac
