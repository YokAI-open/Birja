---
phase: 14-end-strategies-safely
plan: "15"
subsystem: migration-fixtures-and-recovery
tags: [postgresql, tls, authority, migrations, recovery, source-pins]
requires:
  - phase: 14-01
    provides: Finite current migration-owner fixtures
  - phase: 14-04
    provides: Exact0023 bootstrap grants and authority
  - phase: 14-06
    provides: Source-manifest authentication before current regrant
  - phase: 14-10
    provides: Current closure financial integration
provides:
  - Current0023 fixtures distinct from authenticated retained20/17 sources
  - Authenticated initial/runtime20 and exact21/22 resume before Alembic
  - Real fresh/upgraded TLS and complete31-table/24-tail encrypted cold proof
  - Borrowed-stack preservation and bounded current configuration selectors
affects: [14-16, 14-17, 14-18, 14-19, migrations, recovery]
tech-stack:
  added: []
  patterns: [finite-bootstrap-states, exact-source-image-bindings, owned-test-resources]
key-files:
  created: [.planning/phases/14-end-strategies-safely/14-15-TRANSITION-REVIEW.md]
  modified:
    - backend/tests/portfolio_fixtures.py
    - backend/tests/stock_action_fixtures.py
    - backend/app/db/portfolio_bootstrap.py
    - backend/app/db/portfolio_migrate.py
    - deploy/db/bootstrap-roles.sql
    - deploy/tests/portfolio-smoke.py
    - deploy/tests/ops-fixtures.py
    - deploy/tests/test-db-config.sh
    - deploy/tests/test-portfolio-recovery-contracts.py
key-decisions:
  - Preserve immutable20/17 literals and final runtime ACL/defaults; recognize only measured bootstrap states.
  - Authenticate prior20/21/22 catalogue, ACL, defaults and role/configuration before migration child creation.
  - Record broad backend results as partitioned diagnostics; Plan18 still requires an uninterrupted final run.
requirements-completed: []
requirements-progress: [PMGT-04, PMGT-05, PFIN-05, PFIN-06, PSAFE-01]
duration: approximately172min measured first-successful-fixture to implementation-commit interval
completed: 2026-11-19
---

# Phase14 Plan15: Revision-Aware Fixtures and Restricted TLS

**Genuine current and retained fixtures pass isolated checks; an actual granted20
upgrade gap is repaired without loosening final runtime authority.**

## Tasks and commits

1. **Task1 — current versus retained fixtures:** `2522ecc` —32 fixture/test files.
2. **Necessary Task2 upgrade repair:** `352f650` — exact prior authority before
   Alembic, finite bootstrap-only transition, independent SQL parity, coordinated
   current source pins and121-case regressions/provenance.
3. **Task2 — TLS/config/recovery harness:** `1caf086` — six harness files.

Both tasks are implemented and locally verified. Independent review belongs to
the parent workflow. Parent owns STATE/ROADMAP/requirement updates; no complete
requirement, whole phase, UI acceptance or final security run is claimed here.

## Concrete verification

All private logs, PID/start-tick/source-hash receipts and nodeid manifests are
under `/tmp/birja-phase14-plan15/`.

| Proof | Result |
|---|---|
|Required early migration/admission fixture group|81 passed,436.70s; before the additional runtime repair|
|Broad backend fixture diagnostic|3538 distinct scenarios covered by passing partitions, **not one uninterrupted full pass**|
|Final repaired migration/admission modules|121 passed,628.67s;100% statements/branches in both changed runtime modules,119 statements/34 branches, zero misses|
|Current producer/consumer/image contracts|19+9+18 offline tests passed; current source pins verified|
|Deployment compatibility|63 offline control-flow cases passed, including corrupted current migrator-source refusal|
|Borrowed configuration stack|139 passed,31.28s; both caller container IDs preserved;33.60s receipt|
|Fresh owned configuration stack|139 passed;39.81s receipt; zero owned resources afterward|
|Partial borrowed stack|Refused before tests; caller container preserved;4.30s receipt|
|Authenticated retained0017 logical restore|Real marker refusals, reader interpretation and exact restored evidence passed|
|Complete immutable0020 /0017 TLS|22.22s /23.49s; authenticated complete source trees and exact image IDs|
|**Repaired-source fresh /granted20→23 TLS**|**20.70s /15.84s**, exact measured catalogue/object/effective-default ACL parity|
|**Repaired-source encrypted cold recovery**|**55.30s**, source destroyed, complete31/24 before-oracle preserved, original source manifest checked before exact regrant, immutable old20 writer refused before effects|

Repaired-source TLS uses backend commit`352f650` and private archive
`/tmp/birja-backup-test-p14-15-diagnostic-r3/recovery.tar`, SHA256
`58e225255e0e69279be0a7c86c40be4a55aac82aa63c93a4c388bf6fdb6e1ef4`.
The harness commit contains the same tested harness bytes; backend bytes did not
change after352f650. Exact image/source/context records remain beside the archive.

Final unchanged fingerprints: catalogue`59aeeee9428fac73f96143cc8afdd77e3b6a8f81b30ed37b752666579d69a66e`,
object ACL`71896f41a9310ada0af0961b78e78f5364654f1513c11bf9310c250ad545f748`,
effective defaults`4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`.
Scoped mypy/Ruff/format, syntax and diff checks pass. Legacy ops scripts retain
their existing lint findings; the recorded comparison adds zero findings.
Rollback input and retained-installer self-tests pass. No dependencies, image
pins, migration bytes or authority SQL were changed.

### Partition limitation

The3538 diagnostic union is1434+6+1089+41+10+958. Failed/interrupted development
runs are retained and are never described as passing whole-suite runs. Exact
per-run nodeids and hashes are in`partitions.json`/`qualification.json`; ten auth
timestamp labels and one generated UUID label required explicit same-function,
same-order mappings. No tests, financial assertions, gates, markers or coverage
paths were deleted/excluded. The later runtime repair adds34 cases, so final
Phase18 collection is expected3572. **Plan18 must run final source uninterrupted;
the earlier partition results do not replace it.**

## Scope and deviations

**[Rule3 — necessary fixture adaptation, explicitly expanded by parent]**
Current ASGI/service consumers now use genuine0023 grants and public DELETE.
Historical SQL/migration/source consumers retain explicit old revisions. Narrow
rollback-only negative fixtures use real empty/complete closure authority;
three deliberately malformed terminal cases defer only their named root
constraint so the original financial refusal remains exercised. Shared gates
are genuinely acquired for synthetic financial causes; pending announcements
remain independent. History service tests end transactions at simulated request
boundaries, preserving separate same-request fence tests.

The32 Task1 files are inventoried by commit2522ecc. Main groups and reasons:

- `portfolio_fixtures`, `stock_action_fixtures`: complete closure setup and
  actual stock gates; historical authority is not globally promoted to head.
- Creation, funding, identity/API, metadata, overview, routes and scoped History
  tests: genuine current runtime and public deletion; no repeated initial grants.
- Portfolio crypto/API, dividend authority/first-buy, stock authority/ownership/
  trading, strategy-lifecycle and valuation tests: retain money/refusal assertions
  under real closure authority. Stock execution migrations/authority and isolation
  fixtures take the actual instrument gate before financial setup.
- Closure admission/authority/migrations and management/schema admission fixtures:
  restore current schema afterward while keeping explicit retained cases.
- `test_dev_bootstrap`, `test_dividend_authority`, `test_stock_action_migrations`,
  `test_history_service`: explicit current expectations, owned Compose routing,
  genuine gates and request transaction lifetimes.

Minimum conftest/head-owner/grant work was already supplied by Plans01/04;
unnecessary edits to their already-correct files were not manufactured.

**[Rule1 — actual upgrade bug, protected scope explicitly amended by parent]**
Real0020 runtime grants followed by migration23 produced exact catalogue59aeeee…
but bootstrap ACL`f900b495…`, missing only four lifecycle SELECT grants. Existing
tests upgraded an ungranted20 and had missed the real transition. Initial20 and
exact21/22 resume catalogues, object ACLs and effective-default states are now
authenticated before any Alembic child. Python and administrative SQL accept
only the measured transition pair for explicit bootstrap. Ordinary runtime
still requires the unchanged final ACL/private defaults. Every partial/missing
read, extra grant, unsafe default and representative schema drift refuses before
repair/migration. Current producer/consumer/deploy pins now bind the migrator too.
Full states, provenance and exact source hashes are in14-15-TRANSITION-REVIEW.md.

**Harness repairs:** the generated replay checker initially shadowed fresh-operation
imports; distinct aliases and an AST scoping regression fixed it. Each changed
archive generation received a new private path. A hostile-default negative test
needed exact inverse cleanup only after its no-mutation assertion; no runtime
grant reset was introduced to bypass refusal.

## Ownership and integrity

`cleanup.json` confirms zero containers/networks/volumes for`birja-p14-15`,
`birja-p14-15-config`, `birja-p14-15-tls` and its cold project. Borrowed resources
were never adopted for cleanup. Exact diagnostic image bindings remain as proof
artifacts; no unrelated images/resources were removed. The two earlier diagnostic
archives retain SHA52a6794… andde4cb54…. Phase13 archive retains required SHA
`6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92`.
Canonical`/tmp/birja-phase14-proof` remains absent. Untracked`.claude/` is preserved.

No production/dev environment, real data, B2/provider, new dependency/host-package installation,
timer, service deployment, publication, push or merge operation occurred.
Existing issue35 risk/expiry was not broadened. No product stubs or new uncovered
threat surface were introduced; this work enforces planned T-14-15 boundaries.

## Exact Plan16–19 handoff

- **16:** update the runner/CI graph from current0020/V2 to explicit
  payload3/revision23/profile`deploy-recovery-v4`. Use
  `smoke.run(...,revision="0023",fresh_bootstrap=True)`,
  `smoke.run(...,revision="0023",upgraded_bootstrap=True)` and
  `smoke.run(...,revision="0023",cold=True)`; compare all three authority hashes.
  Keep complete fixed20/17 and older7–14 lanes distinct. Every current restored
  context must receive its original source manifest before regrant; compare
  final23 with`quarantined=False`.
- **16 preflight:** retain the real named authority/create/admission selectors
  already added to`test-db-config.sh`; include both repaired runtime modules in
  critical coverage/source hashing. Use stripped child PATH including
  `/usr/sbin`, existing Node24/uv/Python/restic/nginx and no installations.
  Runner archive-path integration needs the explicitly authorized maintained
  `synthetic_path` successor path/prefix; current consumer recognizes backup-test
  prefixes and historical phase12/13 paths, not the canonical phase14 path yet.
- **18:** create its own final archive exclusively after runner integration and
  review; run uninterrupted whole security/coverage and the full seven-stage
  same-archive campaign on final source. These diagnostic archives/results are
  supplemental, never substituted or overwritten.
- **17/19:** browser/regression integration and new owner UI/native200% acceptance
  remain pending. No earlier UI approval is relabelled.

## Self-Check: PASSED

The three implementation commits and review artifact exist; all listed private
passing receipts and integrity/cleanup records were checked. Parent must still
perform independent review and its owned state updates.
