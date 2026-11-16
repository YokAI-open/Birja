#!/usr/bin/env bash
# Producer, canonical SQL and restore consumer are one checksummed payload.
# Versioned portfolio_payload v1 pins migration SQL/bootstrap/proof sources.
# Older immutable bundles without that field retain their original inventory.
recovery_bundle_main() { python3 "$(dirname "${BASH_SOURCE[0]}")/verify-restore.py" bundle "$@"; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  recovery_bundle_main "$@"
fi
