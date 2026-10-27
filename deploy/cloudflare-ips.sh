#!/usr/bin/env bash
# Generate /etc/nginx/snippets/birja-cloudflare-realip.conf from Cloudflare's
# published ranges. Manual refresh (D-06, no cron):
#   /srv/birja/deploy/cloudflare-ips.sh [--no-reload]
# ufw is never modified; drift is only reported (--check-ufw: report only).
# Undo: restore /var/lib/birja/nginx-prev/birja-cloudflare-realip.conf.prev
# (if present) to the target path and reload nginx.
set -Eeuo pipefail

RELOAD=1
[ "${1:-}" = "--no-reload" ] && RELOAD=0
[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }

TARGET=/etc/nginx/snippets/birja-cloudflare-realip.conf
PREV_DIR=/var/lib/birja/nginx-prev
V4_URL=https://www.cloudflare.com/ips-v4
V6_URL=https://www.cloudflare.com/ips-v6
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

curl -fsS --max-time 15 "$V4_URL" > "$TMP/v4" || { echo "fetch failed: $V4_URL" >&2; exit 1; }
curl -fsS --max-time 15 "$V6_URL" > "$TMP/v6" || { echo "fetch failed: $V6_URL" >&2; exit 1; }

check() { # file regex min
    local n=0 line
    while IFS= read -r line || [ -n "$line" ]; do
        [ -z "$line" ] && continue
        [[ "$line" =~ $2 ]] || { echo "invalid CIDR line in $1" >&2; exit 1; }
        n=$((n + 1))
    done < "$1"
    [ "$n" -ge "$3" ] || { echo "too few ranges in $1 ($n < $3)" >&2; exit 1; }
}
check "$TMP/v4" '^([0-9]{1,3}\.){3}[0-9]{1,3}/[0-9]{1,2}$' 10
check "$TMP/v6" '^[0-9a-f:]+/[0-9]{1,3}$' 3

{
    echo "# Cloudflare real-IP ranges, generated $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# Sources: $V4_URL $V6_URL"
    echo "# Manual refresh (D-06, no cron): /srv/birja/deploy/cloudflare-ips.sh"
    grep -v '^$' "$TMP/v4" | sed 's/^/set_real_ip_from /; s/$/;/'
    grep -v '^$' "$TMP/v6" | sed 's/^/set_real_ip_from /; s/$/;/'
    echo "real_ip_header CF-Connecting-IP;"
    echo "real_ip_recursive off;"
} > "$TMP/out"

# Read-only ufw drift report (D-06: ufw is never modified). A range counts as
# present when ufw allows it for both 80 and 443, either as separate
# "80/tcp" + "443/tcp" rules or as one combined "80,443/tcp" rule.
ufw_drift() {
    local out cidr missing=()
    out="$(ufw status 2>/dev/null)" && [ -n "$out" ] || return 0
    has_port() { # cidr port
        awk -v c="$1" -v p="$2" '
            $0 ~ /ALLOW/ {
                src = ""; for (i = 1; i <= NF; i++) if ($i == c) src = c
                if (src == "") next
                n = split($1, a, "/"); if (a[2] != "tcp" && n == 2) next
                m = split(a[1], ports, ",")
                for (j = 1; j <= m; j++) if (ports[j] == p) found = 1
            }
            END { exit found ? 0 : 1 }' <<<"$out"
    }
    while IFS= read -r cidr; do
        [ -z "$cidr" ] && continue
        has_port "$cidr" 80 && has_port "$cidr" 443 || missing+=("$cidr")
    done < <({ cat "$TMP/v4"; echo; cat "$TMP/v6"; echo; })
    if [ "${#missing[@]}" -gt 0 ]; then
        echo "WARNING: Cloudflare ranges missing from ufw (need 80 and 443/tcp):"
        printf '  %s\n' "${missing[@]}"
        echo "Updating ufw is a manual decision. Documented command per range:"
        echo "  ufw allow proto tcp from <cidr> to any port 80,443"
    else
        echo "ufw: all Cloudflare ranges allowed on 80 and 443"
    fi
}

# --check-ufw: only report ufw drift; touch nothing, no reload.
if [ "${1:-}" = "--check-ufw" ]; then
    ufw_drift
    exit 0
fi

# --print: show the generated snippet on stdout, touch nothing (static checks).
if [ "${1:-}" = "--print" ]; then
    cat "$TMP/out"
    exit 0
fi

HAD_OLD=0
mkdir -p "$PREV_DIR"
if [ -f "$TARGET" ]; then
    HAD_OLD=1
    cp -p "$TARGET" "$PREV_DIR/birja-cloudflare-realip.conf.prev"
fi
install -m 644 "$TMP/out" "$TARGET"

if [ "$RELOAD" = 1 ]; then
    if ! nginx -t; then
        if [ "$HAD_OLD" = 1 ]; then
            cp -p "$PREV_DIR/birja-cloudflare-realip.conf.prev" "$TARGET"
        else
            rm -f "$TARGET"
        fi
        echo "nginx -t failed; previous snippet restored" >&2
        exit 1
    fi
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
    fi
fi
echo "wrote $TARGET"

ufw_drift
