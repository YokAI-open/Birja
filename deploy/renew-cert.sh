#!/usr/bin/env bash
# Manual re-issue of the *.nist.one + nist.one ZeroSSL ECC cert (D-03, D-07).
# Nothing renews unattended (D-07): after install, the cert is removed from
# acme.sh's renewal list and saved Cloudflare credentials are stripped, so the
# existing acme.sh cron line (left untouched, D-06) has nothing to renew.
# Run it once in 02.1-05 and again at each renewal, from /srv/birja (or the
# dev checkout). Token: /root/.secrets/cloudflare.env (root, 600).
# Undo: automatic renewal can be re-enabled by moving the
# '*.nist.one.conf.removed' file in the cert dir back to '.conf'. Not desired
# per D-07; listed only for completeness.
set -Eeuo pipefail

ENV_FILE=/root/.secrets/cloudflare.env
ACME=/root/.acme.sh/acme.sh
OUT_DIR=/etc/nginx/certs/nist.one
CERT_DIR='/root/.acme.sh/*.nist.one_ecc'
HERE="$(dirname "$(readlink -f "$0")")"

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
    # Exported so dns_cf saves them to the domain conf, not account.conf.
    export CF_Token CF_Zone_ID
}

load_token

# Preflight: no CA call.
"$HERE/cloudflare-dns.sh" check || { echo "preflight failed" >&2; exit 1; }

# A leftover .removed conf would make --remove refuse in step 6.
rm -f "$CERT_DIR/"'*.nist.one.conf.removed'

# Single attempt, no retry loop (CA rate limits).
if ! "$ACME" --issue --dns dns_cf -d '*.nist.one' -d nist.one --keylength ec-256 --server zerossl --force; then
    echo "issue failed; read the acme.sh output above, do not loop" >&2
    exit 1
fi

install -d -m 750 "$OUT_DIR"
"$ACME" --install-cert --ecc -d '*.nist.one' \
    --key-file "$OUT_DIR/key.pem" \
    --fullchain-file "$OUT_DIR/fullchain.pem" \
    --reloadcmd "systemctl try-reload-or-restart nginx"
chmod 600 "$OUT_DIR/key.pem"

# Take the cert off the renewal list (D-07). Key and cert files stay.
"$ACME" --remove -d '*.nist.one' --ecc

# Strip saved Cloudflare credentials; the only copy is the user's file.
PAT='^(SAVED_)?CF_(Token|Zone_ID|Account_ID|Key|Email)='
FILES=(/root/.acme.sh/account.conf)
for f in "$CERT_DIR/"'*.nist.one.conf.removed'; do
    [ -f "$f" ] && FILES+=("$f")
done
for f in "${FILES[@]}"; do
    [ -f "$f" ] || continue
    sed -i -E '/^(SAVED_)?CF_(Token|Zone_ID|Account_ID|Key|Email)=/d' "$f"
    left="$(grep -cE "$PAT" "$f" || true)"
    [ "$left" = 0 ] || { echo "credentials still present in $f" >&2; exit 1; }
done

echo "--- installed certificate ---"
openssl x509 -in "$OUT_DIR/fullchain.pem" -noout -subject -enddate -ext subjectAltName
END="$(openssl x509 -in "$OUT_DIR/fullchain.pem" -noout -enddate | cut -d= -f2)"
echo "Renew by: $(date -u -d "$END - 30 days" +%Y-%m-%d)"
echo "--- acme.sh --list ---"
"$ACME" --list
echo "--- acme.sh cron line ---"
crontab -l | grep acme.sh || true
