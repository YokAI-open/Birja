#!/usr/bin/env bash
# Operator entrypoint; importing definitions has no operational side effects.
# The source-owned producer admits exact0017 or retained0007–0014; its
# revision/schema guard refuses0015/16 as migration_only before pg_dump/upload.
backup_main() { python3 "$(dirname "${BASH_SOURCE[0]}")/backup-snapshot.py" backup "$@"; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  backup_main "$@"
fi
