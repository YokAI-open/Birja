#!/usr/bin/env bash
recovery_bundle_main() { python3 "$(dirname "${BASH_SOURCE[0]}")/verify-restore.py" bundle "$@"; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  recovery_bundle_main "$@"
fi
