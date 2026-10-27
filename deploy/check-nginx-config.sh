#!/usr/bin/env bash
# Offline `nginx -t` of the repo config in a throwaway prefix. Changes nothing
# under /etc. Needs root because nginx -t opens /var/log/nginx.
set -Eeuo pipefail

SRC="$(dirname "$(readlink -f "$0")")/nginx"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/snippets" "$TMP/conf.d" "$TMP/certs" "$TMP/sites"
cp "$SRC/snippets/"*.conf "$TMP/snippets/"
cp "$SRC/conf.d/"*.conf "$TMP/conf.d/"
sed -e "s#/etc/nginx/snippets/#$TMP/snippets/#g" \
    -e "s#/etc/nginx/certs/nist.one/#$TMP/certs/#g" \
    -e "s#/etc/nginx/conf.d/#$TMP/conf.d/#g" \
    "$SRC/birja.nist.one.conf" > "$TMP/sites/birja.nist.one"
# Snippets include each other by absolute path too.
sed -i -e "s#/etc/nginx/snippets/#$TMP/snippets/#g" "$TMP/snippets/"*.conf

openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 1 \
    -subj /CN=birja.nist.one -keyout "$TMP/certs/key.pem" \
    -out "$TMP/certs/fullchain.pem" 2>/dev/null

printf 'set_real_ip_from 192.0.2.0/24;\nreal_ip_header CF-Connecting-IP;\n' \
    > "$TMP/snippets/birja-cloudflare-realip.conf"

cat > "$TMP/nginx.conf" <<CONF
pid $TMP/nginx.pid;
error_log stderr;
events {}
http {
    include /etc/nginx/mime.types;
    include $TMP/conf.d/*.conf;
    include $TMP/sites/birja.nist.one;
}
CONF

nginx -t -p "$TMP" -c "$TMP/nginx.conf"
