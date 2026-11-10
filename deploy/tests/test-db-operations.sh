#!/usr/bin/env bash
# --backup-restore, --roles, --tls and --all are serial modes. --all performs
# retained0007/0008/0009/0010 backup/restore, restricted roles, then TLS. Calendar
# SQL authority is proven here; genuine evaluator semantics follow in07-08/13.
# The producer owns
# the complete fixed-project lifecycle in finally; never use a live target.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$ROOT/deploy/tests/ops-fixtures.py" "$@"
