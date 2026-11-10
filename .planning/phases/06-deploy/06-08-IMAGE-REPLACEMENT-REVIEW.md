---
phase: 06-deploy
plan: "08"
reviewed: 2026-11-08T08:15:00Z
depth: deep
source_base: e728855
source_head: e40f688
files_reviewed: 22
files_reviewed_list:
  - .github/workflows/ci.yml
  - backend/Dockerfile
  - backend/pyproject.toml
  - backend/uv.lock
  - deploy/RUNBOOK.md
  - deploy/backup-snapshot.py
  - deploy/configure-db.sh
  - deploy/db-security.compose.yml
  - deploy/deploy-entrypoint.sh
  - deploy/deploy.sh
  - deploy/provision-db-tls.sh
  - deploy/tests/ops-fixtures.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-deploy-prerequisites.py
  - deploy/tests/test-image-contracts.py
  - deploy/tests/test-rollback-db-security.sh
  - deploy/verify-restore.py
  - docker-compose.ops-test.yml
  - docker-compose.prod.yml
  - docker-compose.test.yml
  - docker-compose.yml
  - frontend/Dockerfile
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 06-08: Independent replacement-image code and security review

**Result:** zero confirmed source BLOCKERs or WARNINGs in the bounded
`e728855..e40f688` replacement change. This is source review of T3A/T3B;
it does not complete T3C, Plan 08, the strict image gate or live acceptance.

## Narrative Findings (AI reviewer)

No confirmed finding requiring a source correction was identified. Review
covered the changed lines in all 22 source/documentation paths and the called
consumers needed to assess their behavior. The two changed planning evidence
documents were context rather than additional source files. No structural
pre-pass was supplied.

The review used AGENTS.md, the full shared CLAUDE.md rules, the GSD adapter
and code-review skill, current STATE, Plan 08, the checked image-replacement
contract, T3A/T3B evidence and the original 06/15 review history. Historical
resolved findings were checked for regression at affected boundaries; this
was not a repeat of their original full-phase reviews.

### Build, dependency and retained-release boundaries

The Python builder and runtime derive from the same pinned Wolfi Python
stage. APK uses the base's configured trusted repository/keys and exact
Python/base and Node package versions. No untrusted-repository option or
selective vendor/package-metadata deletion was introduced. Existing uv
paths remain consistent with `/opt/venv`; runtime1001 and frontend1000
permissions, HOME, executable paths and npm symlinks are coherent with their
consumers. Complete npm archive integrity and streamed timeout/size bounds
remain present.

The audit dependency is moved as a complete group, while default host
selection includes both dev and audit. The CI backend still executes
`uv sync --locked` and `uv run pip-audit`, and backend remains required by
ci-pass. Image stages explicitly select production-only or non-audit dev
dependencies. Lock changes affect only project group metadata; the focused
contract authenticates unchanged non-project distribution/artifact records.
Actual installed inventories and successful native execution are supplied
T3A evidence, not independently repeated image inspections in this review.

Retained deployment explicitly supplies the verified retained backend
Dockerfile for backend, scheduler and migrator while retaining the selected
application source context. The retained inventory already includes that
Dockerfile. The production frontend still selects the retained complete
toolchain and its built engine ID. Direct development paths continue to use
their local Dockerfiles. The old-release fixture checks archived lock and
project bytes against immutable v0.3.1, compares resolved dependency records
and builds that source with the reviewed Dockerfile; it does not rewrite old
locks to match the regrouped current metadata.

### Datastore and privileged-operation boundaries

All changed live datastore consumers and CI references select the exact
replacement index pins. PostgreSQL runs explicitly as70:70 with PGDATA
`/var/lib/postgresql/18/docker` beneath the existing volume mount; root
entrypoint ownership conversion is therefore unavailable during normal
startup. Test tmpfs ownership matches70 or65532. Redis commands pass flags
to the image entrypoint and preserve authentication, noeviction, AOF where
previously configured and internal data networks. Server TLS directory/key
group70 preserves0750/0640 modes; app/migrator consumers remain CA-only.

The role helper resolves Compose beside its retained release rather than
the mutable application checkout. Fixed config/target validation and the
existing kernel-checked shared lock precede the added bounded read-only
collation/index query. Failed queries, missing/mismatching versions,
invalid indexes and unexpected output prevent subsequent role SQL. Retained
deployment invokes inspection before source/build/service progression. No
automatic production chown, REINDEX or catalog-version refresh was added.
Retained orchestration prevents application rollback from selecting the
old datastore definitions or undoing TLS/role/UID/data-path controls.

The new physical-transition fixture uses only fixed synthetic project and
volume names, rejects existing resources before entering owned cleanup,
uses absolute Compose paths and `/dev/null` environment input, publishes no
ports and bounds subprocesses. Original volumes are stopped and fingerprinted;
copy/ownership conversion affects selected clones. PostgreSQL REINDEX
precedes version refresh; canonical data, indexed locale behavior, existing
invariant verification, fresh logical restore and untouched-original abort
are checked. Redis checks authenticated cloned AOF reload/restart and the
untouched original. Actual observed glibc drift, roles/TLS denial counts and
timings remain supplied execution evidence from T3B, not rerun integrations.

### Registry, archive and recovery boundaries

The anonymous token request and both manifest requests have fixed CGR
origins; redirects are rejected and bearer authorization is attached only
to the fixed manifest requests. Exact index/platform bytes are hashed.
The unchanged verifier authenticates index-to-platform-to-config links,
layers and only the permitted optional attestation graph, including unknown,
duplicate, size, subject and blob rejection.

Registry acquisition may expose the exact authenticated index engine ID;
that allowance is restricted to REGISTRY_REF inspection. Cold import still
selects only authenticated config/platform identities, binds the fixed
verified-config alias and starts with pull-never behavior. No registry or
RepoDigest fallback was added to imported execution. All three Compose
hash allowlists match the finalized recovery Compose bytes.

These are phase-specific ASVS 5 Level 1/STRIDE checks of trusted-build,
registry/archive, retained privileged installer and datastore transition
boundaries. They assume the existing trusted host/root/Docker boundary;
they are not whole-application certification.

### Independent verification and remaining acceptance

Focused offline checks independently passed:

- Image contracts:13 tests,0.382s, including redirect rejection,
  preflight failures, graph tampering, imported identities and CI handoff.
- CI operational contracts:4 tests,0.002s.
- Shared-lock/deployment prerequisites:15 tests,7.498s.
- Restore safety:4 tests,1.248s.

An initial invocation used the nonexistent Python spelling of the shell
restore-safety producer; the correct shell producer above subsequently
passed. No result is inferred from that failed invocation. No Docker build,
scan, integration, full application suite, CVE research or external/private
operation was performed by this reviewer.

T3C must still produce fresh raw five-target0HIGH/0CRITICAL reports without
VEX/ignores/exceptions, the affected full local/native/browser/audit gates,
and one unchanged final supplied recovery artifact across recovery and
actual-v0.3.1 rollback with serial roles/TLS checks, copy reverification and
resource cleanup. Earlier scans and historical archive bytes cannot satisfy
that acceptance. Any subsequent source correction requires relevant review
and proof renewal.

Only this new review artifact was written. No source, STATE, historical
review, unrelated `.claude/`, commit or publication change was made.
