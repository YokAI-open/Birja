---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T11:20:15Z
depth: deep
diff_base: a81a34d
review_head: 7e9403b
re_review_producer_sha256: 196b459ec86c75d778eb1f7bc81b14cb1b8f987b4737c2d3a4ce92261917311a
ops_review_head: fe52f2a
ops_fixture_sha256: 1dad3de515408d289b227bf7b88a94c1eb51c4990d16c20c0918223d5b4d0d13
files_reviewed: 7
files_reviewed_list:
  - deploy/backup-snapshot.py
  - deploy/backup-manifest.sql
  - deploy/verify-restore.py
  - deploy/tests/test-stock-recovery-contracts.py
  - deploy/tests/test-restore-safety.sh
  - deploy/tests/ops-fixtures.py
  - deploy/tests/test-db-operations.sh
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 08-02: Focused Recovery Contract Review

Reviewed frozen Task 1 recovery changes through `7e9403b` and the stable 0011
schema contract. Task 2's concurrently changing operations fixtures were
excluded. No tests, database/provider calls, source edits or runtime operations
were performed. Executor-reported tests are separate evidence.

## Narrative Findings (AI reviewer)

### Task 2 fixture review at `fe52f2a`

**Zero additional BLOCKER/WARNING findings.** Verified the frozen operations
fixture SHA256 above. Source inspection follows actual populated 0010 creation,
privileged role preparation before the restricted upgrade, verified-TLS
app/scheduler sessions, migration through the migrator route, and allowed/42501
operations without post-upgrade grant repair. The separate fresh lane compares
the same action privilege matrix. No new migrator administrative capability or
operator runtime membership is introduced by the fixture.

The retained-tool session spans real dump/encrypted backup/retrieval/restore
lanes for 0007 through 0011. Legacy seeds use their historical release models.
The 0011 lane advances an actual sequence between manifest capture and pg_dump,
compares archive-bound identities after restoration, corrupts each accounting
table and all 17 identity states, and checks duplicate application refusal.
Negative controls target only disposable restored clones; fixed test-project
cleanup remains in finally blocks. The full serial proof was still running at
review time, so these are inspected assertions and isolation boundaries, not a
claim that the entire command has passed. No tests or runtime operations were
performed by this reviewer.

### Targeted re-review of frozen producer correction

**Zero active BLOCKER/WARNING findings in the reviewed correction.** CR-01 is
resolved in the frozen producer with SHA256 recorded above, based on `7e9403b`.
The reviewed correction was uncommitted; this report does not claim a later
commit or completion of the still-running full serial operations proof.

The producer selects exactly the 17 allowlisted sequence objects from the actual
retained archive using `pg_restore --data-only --file=-`. It parses fixed full-line
`pg_catalog.setval` statements without executing SQL, rejects duplicate/unknown/
missing identities and invalid values, replaces the earlier live sequence sample
and validates the manifest before publication. Extraction retains the cumulative
job deadline/invocation bound and adds a 64 KiB child output file limit; parsing
independently checks the same byte bound. Exact restored identity equality and
safe next-value checks remain enforced. Legacy selected SQL changes are absent;
the separate `verified_cutoff` formatting correction applies only to 0011 rows.
No source edits, tests or runtime operations were performed in this re-review.

### CR-01 — BLOCKER, RESOLVED: Sequence capture can disagree with the same retained dump

**File:** `/home/YokaiExchange/deploy/backup-snapshot.py:193`

**Also affected:** `/home/YokaiExchange/deploy/backup-snapshot.py:1038` and
`/home/YokaiExchange/deploy/verify-restore.py:805`.

**Issue:** The new 0011 manifest captures all sequence `last_value/is_called`
states before invoking `pg_dump`. Restore verification now requires exact
equality with those earlier values. PostgreSQL sequence state is not protected
by the exported MVCC snapshot: a normal `nextval` after the manifest query and
before pg_dump captures its SEQUENCE SET entry changes the dump's sequence state
without changing the snapshot's table rows. Consequently an otherwise correct
nightly backup created while users/scheduler write may fail its own retained
restore proof. The archive can be published successfully because the producer
does not compare its sequence values with the retained dump. The existing
consumer's adjacent identity-progression comment already recognizes this MVCC
limitation; the new equality requirement introduces the regression.

**Fix:** Preserve exact identity-state verification by deriving the manifest's
authoritative sequence values from the actual retained archive, using a bounded
and strictly validated SEQUENCE SET extraction or another reviewed capture
mechanism. Keep table hashes tied to the exported snapshot, all 17 identities
explicit, and safe future identity progression enforced. Do not simply remove
the exact equality check or assume the read-only transaction pauses writers.
Add an actual PostgreSQL regression that advances a sequence between manifest
capture and pg_dump, restores that same archive and proves exact archive-bound
sequence equality and safe next identities.

The reviewed static dispatch preserves predecessor selected SQL and includes
all nine accounting tables, observation event identity, split instrument identity,
quote units and 17 identity states. The independent fixed schema fingerprint
includes full constraint/index definitions rather than trusting a source manifest
alone. No separate concrete defect was identified in those scoped changes.
