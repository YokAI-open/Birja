#!/usr/bin/env bash
# Install the Birja nginx config. Writes only birja-* paths; never edits the
# nist.one, lib.nist.one or default sites. Restores backups if nginx -t fails.
# Run from the dev tree or /srv/birja.
# Undo: rm /etc/nginx/sites-enabled/birja.nist.one /etc/nginx/sites-available/birja.nist.one /etc/nginx/snippets/birja-*.conf /etc/nginx/conf.d/birja-zones.conf /etc/nginx/conf.d/birja-default-tls.conf && nginx -t && systemctl reload nginx
# To also stop serving nist.one again: systemctl disable --now nginx
set -Eeuo pipefail

[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }
HERE="$(dirname "$(readlink -f "$0")")"
SRC="$HERE/nginx"
CERT_DIR=/etc/nginx/certs/nist.one
BACKUP=/var/lib/birja/nginx-prev

for f in fullchain.pem key.pem; do
    [ -f "$CERT_DIR/$f" ] || { echo "missing $CERT_DIR/$f; run renew-cert.sh first" >&2; exit 1; }
done

if [ ! -f /etc/nginx/snippets/birja-cloudflare-realip.conf ]; then
    "$HERE/cloudflare-ips.sh" --no-reload
fi

SRCS=(
    "$SRC/birja.nist.one.conf"
    "$SRC/snippets/birja-security-headers.conf"
    "$SRC/snippets/birja-proxy.conf"
    "$SRC/conf.d/birja-zones.conf"
    "$SRC/conf.d/birja-default-tls.conf"
)
TARGETS=(
    /etc/nginx/sites-available/birja.nist.one
    /etc/nginx/snippets/birja-security-headers.conf
    /etc/nginx/snippets/birja-proxy.conf
    /etc/nginx/conf.d/birja-zones.conf
    /etc/nginx/conf.d/birja-default-tls.conf
)
LINK=/etc/nginx/sites-enabled/birja.nist.one

mkdir -p "$BACKUP"
EXISTED=()
for i in "${!TARGETS[@]}"; do
    t="${TARGETS[$i]}"
    if [ -f "$t" ]; then
        EXISTED[i]=1
        cp -p "$t" "$BACKUP/$(basename "$t")"
    else
        EXISTED[i]=0
    fi
done

CHANGED=()
for i in "${!TARGETS[@]}"; do
    if [ ! -f "${TARGETS[$i]}" ] || ! cmp -s "${SRCS[$i]}" "${TARGETS[$i]}"; then
        CHANGED+=("${TARGETS[$i]}")
    fi
    install -m 644 "${SRCS[$i]}" "${TARGETS[$i]}"
done

MADE_LINK=0
if [ ! -e "$LINK" ] && [ ! -L "$LINK" ]; then
    ln -s ../sites-available/birja.nist.one "$LINK"
    MADE_LINK=1
    CHANGED+=("$LINK")
fi

if ! nginx -t; then
    for i in "${!TARGETS[@]}"; do
        t="${TARGETS[$i]}"
        if [ "${EXISTED[$i]}" = 1 ]; then
            cp -p "$BACKUP/$(basename "$t")" "$t"
        else
            rm -f "$t"
        fi
    done
    if [ "$MADE_LINK" = 1 ]; then rm -f "$LINK"; fi
    echo "nginx -t failed; previous state restored" >&2
    exit 1
fi

systemctl enable nginx
systemctl reload-or-restart nginx

echo "Changed files:"
if [ "${#CHANGED[@]}" -eq 0 ]; then echo "  (none)"; else printf '  %s\n' "${CHANGED[@]}"; fi
