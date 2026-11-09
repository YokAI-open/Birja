#!/usr/bin/env bash
# 0 fresh success; 1 missing/stale/failed; 2 invalid configuration.
backup_status_main() { python3 "$(dirname "${BASH_SOURCE[0]}")/backup-snapshot.py" status "$@"; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  backup_status_main "$@"
fi
