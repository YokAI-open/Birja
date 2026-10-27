#!/usr/bin/env bash
# One-time creation of /etc/birja/prod.env with generated secrets.
# Never prints secret values. Undo: rm /etc/birja/prod.env (only while the
# prod stack is down; the Postgres volume keeps the old password).
set -Eeuo pipefail

ENV_DIR=/etc/birja
ENV_FILE=$ENV_DIR/prod.env

if [ "$(id -u)" -ne 0 ]; then
  echo "must run as root" >&2
  exit 1
fi
if [ -e "$ENV_FILE" ]; then
  echo "$ENV_FILE exists, not overwriting" >&2
  exit 1
fi

umask 077
install -d -m 700 "$ENV_DIR"
tmp=$(mktemp "$ENV_DIR/prod.env.XXXXXX")

pg=$(openssl rand -hex 32)
redis=$(openssl rand -hex 32)
otp=$(openssl rand -hex 32)
jwt=$(openssl rand -hex 32)

{
  printf '%s\n' '# Birja production env. Root-only (600). Never commit, print or paste this file.'
  printf '%s\n' '# Undo: rm /etc/birja/prod.env (only while the prod stack is down; the Postgres volume keeps the old password).'
  printf 'POSTGRES_USER=birja\n'
  printf 'POSTGRES_DB=birja\n'
  printf 'POSTGRES_PASSWORD=%s\n' "$pg"
  printf 'REDIS_PASSWORD=%s\n' "$redis"
  printf 'OTP_HMAC_SECRET=%s\n' "$otp"
  printf 'JWT_SECRET=%s\n' "$jwt"
  printf 'EMAIL_FROM="Birja <birja@nist.one>"\n'
  printf '%s\n' '# Paste the Resend API key here yourself (nano /etc/birja/prod.env). Never paste it into chat.'
  printf 'RESEND_API_KEY=\n'
} > "$tmp"
unset pg redis otp jwt

chown root:root "$tmp"
chmod 600 "$tmp"
mv "$tmp" "$ENV_FILE"

echo "Created $ENV_FILE (mode $(stat -c '%a' "$ENV_FILE"))"
empty=$(grep -E '^[A-Z_]+=$' "$ENV_FILE" | cut -d= -f1 | tr '\n' ' ' || true)
if [ -n "$empty" ]; then
  echo "Still empty, fill in: $empty"
fi
exit 0
