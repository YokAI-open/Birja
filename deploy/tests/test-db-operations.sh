#!/usr/bin/env bash
# --backup-restore, --dividend-sql, --roles, --tls, --tls-pair and --all are serial modes.
# --dividend-sql is a focused genuine scheduler SQL plus quarantined clone proof.
# --all is a retained0007–0014 diagnostic, with current V3 recovery tools.
# Current0023 plus complete immutable0020/0017 qualification uses the
# run-portfolio-validation.py seven-stage graph and a new Phase14 archive.
# Both --roles and --all also run the genuine calendar evaluator over persisted
# app-role reads and scheduler writes with verified TLS, in populated and fresh lanes.
# The producer owns
# the complete fixed-project lifecycle in finally; never use a live target.
set -Eeuo pipefail
umask 077
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$ROOT/deploy/tests/ops-fixtures.py" "$@"
