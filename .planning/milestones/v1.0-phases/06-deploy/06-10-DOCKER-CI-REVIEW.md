---
phase: 06-deploy
reviewed: 2026-11-09T12:28:37Z
depth: standard
diff_base: 1bbaa69
review_head: f5ad5cc
files_reviewed: 2
files_reviewed_list:
  - .github/workflows/ci.yml
  - deploy/tests/test-ci-ops.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 06-10: Docker CI Capability Review

## Narrative Findings (AI reviewer)

No BLOCKER or WARNING findings in the bounded two-file diff
`1bbaa69..f5ad5cc`.

The new setup (`.github/workflows/ci.yml:220`) runs only in the disposable
Ubuntu 24.04 ops job. It uses the official HTTPS Docker repository, a
repository-specific readable `signed-by` keyring and exact matching
`docker-ce`/`docker-ce-cli` versions. Normal apt signature verification stays
enabled; no downloaded script is executed. Package installation uses `--yes`
and remains within the existing 30-minute job timeout.

The exact runner image's [Docker installation script](https://raw.githubusercontent.com/actions/runner-images/ubuntu24/20261101.360/images/ubuntu/scripts/build/install-docker.sh)
already installs official Docker components and removes its temporary apt
source/key afterward. The change therefore restores that source for a CE
upgrade rather than mixing distro Docker packages. Existing separately
installed Compose/Buildx plugins are retained. The package pinning and keyring
pattern follow [Docker's Ubuntu installation instructions](https://docs.docker.com/engine/install/ubuntu/);
both 29.2.1 packages are present in the [official Noble amd64 archive](https://download.docker.com/linux/ubuntu/dists/noble/pool/stable/amd64/).

Docker restarts before any fixture containers are built or started. The
following preflight requires both installed client and running daemon to be
29.2.1, pulls the existing immutable recovery image reference, then tests
platform-aware inspection using `/usr/bin/docker` with the same clean root
environment as recovery. Inspect failure propagates before fixture execution.
The unchanged verifier still checks authenticated identity and linux/amd64;
no fallback, tag substitution or identity relaxation was added.

The new contract (`deploy/tests/test-ci-ops.py:61`) checks setup/preflight
ordering, repository/keyring, package pins, daemon restart, clean-environment
inspection and absence of unauthenticated apt or remote Docker overrides.
All required producers, aggregate gates, privilege boundaries and fixed
synthetic cleanup remain unchanged.

## Validation and limits

- Independently reran `python3 deploy/tests/test-ci-ops.py`: 6 passed.
- Scoped `git diff --check 1bbaa69..f5ad5cc`: passed.
- Read both changed files and traced the existing recovery image inspection.
- Verified package-family/repository compatibility against the exact runner
  installation source and official Docker documentation above.

The parent supplied actual run `42616168904`'s API-capability failure and the
executor's read-only local API rejection/success proof. This review did not
install packages, restart Docker, rerun databases/application/scanners, or
claim successful hosted installation. Actual corrective-head GitHub ops and
aggregate success remain pending.

Only this review artifact was written. No source, VDS/runtime, recovery,
image pin, production or remote state was changed; unrelated `.claude/` was
preserved. No merge or deployment authority is implied.
