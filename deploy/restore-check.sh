#!/usr/bin/env bash
restore_main() { python3 "$(dirname "${BASH_SOURCE[0]}")/verify-restore.py" restore "$@"; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  restore_main "$@"
fi
