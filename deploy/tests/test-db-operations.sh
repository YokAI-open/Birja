#!/usr/bin/env bash
# --backup-restore, --dividend-sql, --roles, --tls, --tls-pair and --all are serial modes.
# --dividend-sql is a focused genuine scheduler SQL plus quarantined clone proof.
# --all performs retained0007–0014 backup/restore, restricted roles, then TLS.
# Both --roles and --all also run the genuine calendar evaluator over persisted
# app-role reads and scheduler writes with verified TLS, in populated and fresh lanes.
# The producer owns
# the complete fixed-project lifecycle in finally; never use a live target.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$ROOT/deploy/tests/ops-fixtures.py" "$@"
