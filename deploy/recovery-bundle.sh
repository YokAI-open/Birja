#!/usr/bin/env bash
# Producer, canonical SQL and restore consumer are one checksummed payload.
# Versioned portfolio_payload v2 adds0020 provenance/source; v1 stays immutable.
# Older immutable bundles without that field retain their original inventory.
recovery_bundle_main() {
  if [[ "${1:-}" == package ]]; then
    shift
    python3 "$(dirname "${BASH_SOURCE[0]}")/backup-snapshot.py" bundle-v2 "$@"
  else
    python3 "$(dirname "${BASH_SOURCE[0]}")/verify-restore.py" bundle "$@"
  fi
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  set -Eeuo pipefail
  umask 077
  recovery_bundle_main "$@"
fi
