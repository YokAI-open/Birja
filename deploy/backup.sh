#!/usr/bin/env bash
# Operator entrypoint; importing definitions has no operational side effects.
backup_main() { python3 "$(dirname "${BASH_SOURCE[0]}")/backup-snapshot.py" backup "$@"; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  backup_main "$@"
fi
