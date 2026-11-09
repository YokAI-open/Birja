#!/usr/bin/env bash
# One-time creation of /etc/birja/prod.env with generated secrets.
# Never prints secret values. Undo: rm /etc/birja/prod.env (only while the
# prod stack is down; the Postgres volume keeps the old password).
set -Eeuo pipefail

ENV_DIR=/etc/birja
if [ "$#" -ne 0 ]; then
  if [ "$#" -ne 2 ] || [ "$1" != --synthetic ]; then
    echo 'invalid init target' >&2
    exit 1
  fi
  ENV_DIR=$2
  if [[ ! "$ENV_DIR" =~ ^/tmp/birja-backup-test-[A-Za-z0-9_-]+$ ]] ||
     [ "$(realpath -e -- "$ENV_DIR")" != "$ENV_DIR" ] ||
     [ "$(stat -c '%u:%a' "$ENV_DIR")" != 0:700 ]; then
    echo 'invalid init target' >&2
    exit 1
  fi
fi
ENV_FILE=$ENV_DIR/prod.env

if [ "$(id -u)" -ne 0 ]; then
  echo "must run as root" >&2
  exit 1
fi
if [ -e "$ENV_FILE" ] || [ -L "$ENV_FILE" ] || [ -L "$ENV_DIR" ]; then
  echo "$ENV_FILE exists, not overwriting" >&2
  exit 1
fi

umask 077
install -d -m 700 "$ENV_DIR"
tmp=$(mktemp "$ENV_DIR/prod.env.XXXXXX")
trap 'rm -f -- "$tmp"' EXIT

pg=$(openssl rand -hex 32)
app_pg=$(openssl rand -hex 32)
scheduler_pg=$(openssl rand -hex 32)
migrator_pg=$(openssl rand -hex 32)
redis=$(openssl rand -hex 32)
otp=$(openssl rand -hex 32)
jwt=$(openssl rand -hex 32)

{
  printf '%s\n' '# Birja production env. Root-only (600). Never commit, print or paste this file.'
  printf '%s\n' '# Undo: rm /etc/birja/prod.env (only while the prod stack is down; the Postgres volume keeps the old password).'
  printf 'POSTGRES_USER=birja\n'
  printf 'POSTGRES_DB=birja\n'
  printf 'POSTGRES_PASSWORD=%s\n' "$pg"
  printf '%s\n' '# New install only: provision restricted roles before starting runtime.'
  printf '%s\n' '# Populated installs: configure-db after verified recovery; never regenerate this file.'
  printf 'APP_DATABASE_URL=postgresql+asyncpg://birja_app:%s@postgres:5432/birja\n' "$app_pg"
  printf 'SCHEDULER_DATABASE_URL=postgresql+asyncpg://birja_scheduler:%s@postgres:5432/birja\n' "$scheduler_pg"
  printf 'MIGRATOR_DATABASE_URL=postgresql+asyncpg://birja_migrator:%s@postgres:5432/birja\n' "$migrator_pg"
  printf 'REDIS_PASSWORD=%s\n' "$redis"
  printf 'OTP_HMAC_SECRET=%s\n' "$otp"
  printf 'JWT_SECRET=%s\n' "$jwt"
  printf 'EMAIL_FROM="Birja <birja@nist.one>"\n'
  printf '%s\n' '# Paste the Resend API key here yourself (nano /etc/birja/prod.env). Never paste it into chat.'
  printf 'RESEND_API_KEY=\n'
} > "$tmp"
unset pg app_pg scheduler_pg migrator_pg redis otp jwt

chown root:root "$tmp"
chmod 600 "$tmp"
# Atomic no-clobber publication, including concurrent invocations.
ln "$tmp" "$ENV_FILE"

echo "Created $ENV_FILE (mode $(stat -c '%a' "$ENV_FILE"))"
empty=$(grep -E '^[A-Z_]+=$' "$ENV_FILE" | cut -d= -f1 | tr '\n' ' ' || true)
if [ -n "$empty" ]; then
  echo "Still empty, fill in: $empty"
fi
exit 0
