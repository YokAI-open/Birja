#!/usr/bin/env bash
# The source-owned consumer validates revision/source/manifest before clone
# writes;0015/16 are explicitly migration_only, not runnable recovery points.
restore_main() { python3 "$(dirname "${BASH_SOURCE[0]}")/verify-restore.py" restore "$@"; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  restore_main "$@"
fi
