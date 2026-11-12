#!/usr/bin/env bash
# --backup-restore, --roles, --tls and --all are serial modes. --all performs
# retained0007–0013 backup/restore, restricted roles, then TLS. Calendar
# Both --roles and --all also run the genuine calendar evaluator over persisted
# app-role reads and scheduler writes with verified TLS, in populated and fresh lanes.
# The producer owns
# the complete fixed-project lifecycle in finally; never use a live target.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$ROOT/deploy/tests/ops-fixtures.py" "$@"
