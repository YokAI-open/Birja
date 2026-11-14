#!/usr/bin/env bash
# Producer, canonical SQL and restore consumer are one checksummed payload.
# Successor inventory records supported schemas; old immutable bundles remain readable.
recovery_bundle_main() { python3 "$(dirname "${BASH_SOURCE[0]}")/verify-restore.py" bundle "$@"; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  recovery_bundle_main "$@"
fi
