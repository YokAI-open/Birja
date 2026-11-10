#!/usr/bin/env bash
# --backup-restore, --roles, --tls and --all are serial modes. --all performs
# backup/restore, restricted roles, then production-shaped TLS. The producer owns
# the complete fixed-project lifecycle in finally; never use a live target.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$ROOT/deploy/tests/ops-fixtures.py" "$@"
