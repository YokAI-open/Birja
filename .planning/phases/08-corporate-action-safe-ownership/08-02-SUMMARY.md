---
phase: 08-corporate-action-safe-ownership
plan: "02"
subsystem: recovery
tags: [postgresql, accounting, restic, tls, privileges]
requires:
  - phase: 08-01
    provides: "Reviewed additive0011 accounting schema and restricted runtime grants"
provides:
  - "Exact0011 rows, causal schema and actual-dump identity recovery contract"
  - "Same retained tooling proves encrypted recovery0007 through0011"
  - "Actual populated0010 restricted-TLS upgrade and fresh0011 ACL parity"
affects: [08-04, 08-05, 08-06, 08-08, 08-09, 11]
tech-stack:
  added: []
  patterns: [archive-bound-sequence-state, explicit-revision-dispatch, exact-accounting-schema]
key-files:
  created: []
  modified:
    - deploy/backup-snapshot.py
    - deploy/backup-manifest.sql
    - deploy/verify-restore.py
    - deploy/tests/test-stock-recovery-contracts.py
    - deploy/tests/test-restore-safety.sh
    - deploy/tests/ops-fixtures.py
key-decisions:
  - "Identity values for0011 come from actual retained SEQUENCE SET entries, since PostgreSQL sequences are not MVCC."
  - "Keep predecessor SQL byte-identical and enforce an independent exact0011 schema fingerprint."
  - "No requirement is completed by infrastructure alone; activation and later financial services remain gated."
requirements-completed: []
requirements-addressed: [DIV-01, DIV-02, ACT-01, ACT-03]
duration: 27 min
completed: 2026-11-11
---

# Phase 8 Plan 02: Exact Accounting Recovery Summary

**Revision0011 retains all action identities, aliases, movements, entitlements, epochs, cursors and resolutions, with exact archive-bound identity values and proven restricted-TLS grants.**

## Performance

- Approximately27minutes,2026-11-11, completed11:30UTC.
- Tasks:2/2; six source/test/SQL artifacts changed.
- Existing dependencies/images only; no private provider, production or B2 access.

## Accomplishments

- Producer/consumer explicitly support0007/0008/0009/0010/0011. All nine accounting tables and every selected column are hashed, including observations.event_id, applications.coin_id and quote.unit_epoch. Canonical timestamp text preserves microseconds; monetary values stay exact text. The independent0011 schema fingerprint includes exact columns/defaults/types,40 validated foreign keys, checks, identities, sequence configuration and complete indexes, including uq_trades_id_coin_user. Unknown future revisions, missing/extra schema and corrupt identity state are refused.
- All17 identity last_value/is_called states are compared exactly to restored state, while next-ID safety remains checked without consuming values. The authoritative manifest values are parsed from the actual pg_dump archive, not a pre-dump live sample. PostgreSQL18 pg_restore selects the17 allowlisted sequences, with a64KiB child output bound, cumulative deadline/invocation limits and a strict missing/duplicate/unknown/value parser. No extracted SQL executes.
- One immutable recovery-tool archive performed real pg_dump, local encrypted-restic backup, retrieval and isolated pg_restore for all five revisions. Each revision has its own actual dump/snapshot; this is not one database dump claimed to represent five schemas. Installed launchers execute with the feature checkout denied by Landlock. The0011 fixture preserves verified aliases sharing a revision, opening/split movements, split markers, held/cancelled superseding entitlements, unknown monitoring, epochs, cursor/continuation and immutable resolution evidence. Nothing is normalized to healthy.
- Actual independent nextval advances users_id_seq after snapshot-manifest capture and before pg_dump. The same retained0011 dump restores successfully with its actual archived identities. Nine accounting-table corruption classes, all17 identity-state corruptions and duplicate economic application replay are refused. Source financial rows/schema and controlled identities remain unchanged except this deliberate sequence advance; the post-writer source identity is explicitly compared to the archived/restored value.
- Actual verified-TLS app/scheduler connections survive populated0010→0011 under NOCREATEROLE migrator credentials, with the operator role preprovisioned by privileged bootstrap and no post-upgrade grant repair. Allowed append/identity/quantity operations and immutable/audit/financial/admission denials execute as real roles. Fresh0011 has the identical table/sequence/column privilege matrix. The operator remains NOLOGIN with no runtime membership. Genuine persisted calendar consumers and all existing CA/hostname/plaintext, renewal and mount-isolation checks pass in both lanes.

## Task Commits and TDD Gates

1. Task08-02-01 RED `a81a34d`: the real behavior assertion failed because0011 was unsupported, rather than an import failure.
2. Task08-02-01 GREEN `7e9403b`: explicit canonical contract, full schema/identity validation and real accounting fixture/corruption tests. Predecessor and0011 SQL proofs passed; backup25tests and restore-safety6tests passed.
3. Task08-02-02 RED `edd7c5a`: actual isolated TLS probe rejected its older predecessor because the required populated0010 catalogue was absent.
4. Task08-02-02 regression/fixture extension `fe52f2a`: real nextval race reproduced failure of the retained0011 restore; actual accounting/ACL/TLS fixtures added. The initial immutable archive SHA5999d2599d470f2edf4b37a6f9018252456f4cd606ec3324c1cbb2c26e6f4d38 was rejected by its restore guard after the deliberate sequence advance.
5. Correction GREEN `df2d4b4`: archive-derived sequence state; actual retained0011 race passes, followed by the complete serial five-revision/roles/TLS gate.

Both tasks have observed behavioral RED before their successful completion. Independent review identified the sequence-race blocker after the initial Task1 implementation; its correction and the complete operations fixture are independently re-reviewed clean in08-02-REVIEW.md. That review inspected source; executed results below are separately attributed to this executor.

## Verification Executed

- `bash deploy/tests/test-db-operations.sh --all`: **exit0**, all lanes serial. Retained recovery263.968s; roles150.169s; populated0010 TLS99.296s; fresh0011 TLS93.225s. Existing63 legacy financial/DDL denials remain, alongside new accounting denials. Log:`/tmp/phase08-02-all.log`.
- `python3 deploy/tests/test-stock-recovery-contracts.py --postgres`: **7passed47.652s**, no skipped real cases. Actual SQL for every selected revision; accounting rows/identities and complete schema corruption rejection. Log:`/tmp/phase08-02-postgres-final.log`.
- `bash deploy/tests/test-backup.sh`: **25passed53.239s**, including actual approved local-restic encryption/rotation and zero-network accounting. Log:`/tmp/phase08-02-backup-final.log`.
- `bash deploy/tests/test-restore-safety.sh`: **6passed1.318s**. Log:`/tmp/phase08-02-restore-final.log`.
- `python3 deploy/tests/test-stock-recovery-contracts.py`: **5offline cases pass0.025s;2real cases explicitly skipped** in this quick invocation only; the separate --postgres run above executes both.
- `uv run pytest tests/test_stock_action_migrations.py -k populated_accounting_downgrade_refuses_before_alter -q -x`: **1passed/53deselected0.44s**. The durable event and quote-unit column survive refused downgrade; isolated fixture cleans up. No backend source changed, so the already-passing Wave1 full backend gate was not unnecessarily repeated.
- Scoped Ruff E9/F/I over all four changed Python files, py_compile, shell syntax and git whitespace checks pass. No tracked-file deletion, dependency/lock change or security-gate weakening.

The actual PostgreSQL18 selective extraction behavior was checked against the [official pg_restore documentation](https://www.postgresql.org/docs/current/app-pgrestore.html) and a private synthetic dump experiment. The experiment file was removed.

## Exact Identities and Cleanup

Final retained recovery-tool archive:

- SHA256:`eb271dfc8fe524230b12c698586298ad29ecdf74aacb66d4555c646aaecea690`.
- Size:152,176,640bytes; profile deploy-recovery-v2.
- Recovery engine image ID:`sha256:4401cf2919e749cd77b634a72e4a677c1a1afc12baddb21faf28df326162472e`; verified config digest:`sha256:91c89cf7f1f18cc4d96fcb5b9e2438108569c1dfcd5aa7286f9cad7d75742ed4`, linux/amd64, pull never.
- Existing hardened backend fixture image ID:`sha256:1189c36f9e278b23e2455be753c696a9aa563bdda4b584f086b59f674748a574`.
- Existing approved restic0.19.1 SHA256:`20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639`; pinned binary and provenance were verified before reuse, with no download/install.
- Reviewed0011 migration SHA256 unchanged:`57b4f279a969b3e7da55c87742414138eeefe493fd82309fb1b268b71ac6e161`.
- Final producer SHA256:`196b459ec86c75d778eb1f7bc81b14cb1b8f987b4737c2d3a4ce92261917311a`; ops fixture:`1dad3de515408d289b227bf7b88a94c1eb51c4990d16c20c0918223d5b4d0d13`.

Predecessor selected SQL SHA256 stays byte-compatible:0007/0008=`52753d97387ec491c6494d327a6037d847cdc323bafb571c2dac6bdb0d28b5a5`;0009/0010=`30b3ab0789afa3187fdda383241dfdb115fd102471604a8bb43bf91c21e9d8c1`. The raw SQL file retains the legacy/static-fragment convention; successor callers use manifest_sql/schema_guard_sql or canonical.

Every owned operations fixture tears down in finally. Explicit final Docker label queries found **zero birja-ops-test containers, networks and volumes**. Private temporary recovery hosts, dumps and repositories were context-cleaned; no live tool installation was changed. Existing isolated birja-test PostgreSQL/Redis stay available for later plans; final canonical/downgrade fixtures are cleaned.

## Deviations and Issues

**[Rule1 — Correctness] Bind sequence equality to the actual archive.** Independent review found that pre-dump live sequence capture is not protected by MVCC and invalidates a correct concurrent backup. The actual failing encrypted restore regression precedes the bounded archive-extraction correction. Exact equality/next-value safeguards remain; no writer pause or new production lock is introduced. Resolved and independently re-reviewed clean.

**[Rule3 — Fixture compatibility] Extend retained inventory test.** The restore-safety fixture's exact supported-revision list now includes0011. Predecessor inventory readability and payload corruption rejection remain.

One initial test-seed attempt used a non-UUID economic key; it was corrected to a fixed synthetic UUID. Repeatable user setup was made idempotent. A draft TLS predecessor assertion attempted runtime access to alembic_version, correctly denied; the behavioral RED instead uses the permitted35-row curated catalogue assertion. No runtime privilege was widened to satisfy a test.

## Stubs, Threats and Remaining Gates

No required stub, TODO/FIXME, new endpoint, credential route or unplanned service is introduced. Static allowlists, exact schema/row/archive identity checks and actual restricted-TLS denials implement T-08-02-01/02; existing dependencies/configuration remain unchanged for T-08-02-SC.

Ready for dependency-ordered later plans after parent review/integration. This infrastructure does not implement new stock fills, dividend cash or public event History, and no end-to-end requirement is checked complete. Stock execution stays OFF. Phase7's separately deferred live verification and frozen one-shot process are untouched. No production paths/configuration/services, B2, timers, private keys/provider calls, publication or deployment were accessed. Unrelated .claude/ work and the parent's review artifact are preserved.

## Self-Check: PASSED

All six changed artifacts and the five listed task commits exist. Real final operations/canonical/downgrade gates and scoped static checks actually passed. Reviewed hashes and predecessor bytes match. No requirement/phase-completion claim exceeds this plan's infrastructure evidence.
