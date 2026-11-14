---
phase: 10-dividend-cash-and-event-history
reviewed: 2026-11-13
depth: standard
reviewed_head: 0c6f11d2fa21dce5e80bb56780645e534b646968
original_review_head: d825cb5
diff_base: 0c6efa3
files_reviewed: 4
files_reviewed_list:
  - deploy/backup-snapshot.py
  - deploy/verify-restore.py
  - deploy/backup-manifest.sql
  - deploy/tests/test-stock-recovery-contracts.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  critical: 1
  warning: 0
status: clean
---

# Plan10-04 recovery contract review

## Narrative Findings (AI reviewer)

**Independent recheck: clean at0c6f11d.** The original BLOCKER below is resolved
by03f912d, after behavioral RED evidence inff10840. No remaining finding was
identified in this targeted recheck. The historical finding and its evidence
are preserved below rather than erased.

### Resolution and independent recheck

- Newly absent recovery migrators are now explicitly created with NOINHERIT
  and NOBYPASSRLS as well as the other safe flags. The immediate existing-role
  check also refuses rolinherit=true before database creation; it does not
  silently ALTER an unsafe pre-existing role.
- Independently inspected the two-line verifier change and both new entry-path
  tests. They call the actual restored() context manager and capture its exact
  role-creation and validation SQL. That SQL is executed against PostgreSQL
  using a rollback-owned alias, not replaced with a guessed role definition.
  The resulting flags reach the real0014 role-boundary validator. The unsafe
  pre-existing role case must fail before any CREATE DATABASE call.
- Independently ran:

  `python3 deploy/tests/test-stock-recovery-contracts.py --postgres
  PostgreSQLContracts.test_zz_fresh_restored_owner_reaches_0014_pregrant
  PostgreSQLContracts.test_zz_existing_unsafe_restored_owner_refused_before_database`

  Result: **2passed,0skipped,2.433s**;
  `/tmp/birja-phase10-recovery-review-recheck.log`.
- Archive transport, database creation and the non-role restoration helpers are
  adapted in this focused regression. It proves the real entry SQL and role
  checks, not a complete dump/restoration. Full retained-archive/TLS acceptance
  remains mandatory in Plans05/06. The executor's21/21 full SQL contract results
  are separate evidence and were not repeated by this reviewer.
- No application, source, tracked test, canonical state or production edits or
  commits were made during recheck. Only this report was updated.

Independent bounded review of the changed producer/verifier contract and its
actual restoration entry path follows.

### CR-01 — BLOCKER, resolved: Fresh restoration creates an owner rejected by its own new guard

**File:** `deploy/verify-restore.py:981`

**Related:** `deploy/verify-restore.py:943`,
`deploy/backup-snapshot.py:212`,
`deploy/tests/test-stock-recovery-contracts.py:700`.

**Issue:** `restored()` preprovisions an absent `birja_migrator` with
`CREATE ROLE ... LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION`,
omitting `NOINHERIT`. PostgreSQL therefore creates it with `rolinherit=true`.
The existing immediate role check does not test inheritance. After restoring
schema0014, the new `restore_dividend_authority()` calls
`validate_dividend_role_boundary(..., allow_missing_runtime=True)`, which
requires all six security flags, including `rolinherit`, to be false. The
valid fresh restore consequently fails its own newly added pre-grant check.

The fresh isolated recovery Compose starts only `birja_ops_bootstrap`; it does
not preprovision the migrator. Thus this is the real `--isolated-clone` /
approved fresh recovery path, not an unsupported arbitrary role configuration.
The current0014 consumer test first applies administrative source bootstrap
and invokes `restore_dividend_authority()` directly, so it starts with an
already safe NOINHERIT owner and misses the mismatch in `restored()`.

The app and scheduler creation statements already include `NOINHERIT`; the
missing option is specific to the migrator creation at line981.

**Independent reproduction:** On the guarded disposable `birja-test` database,
ran a rollback-only role probe using exactly the creation options from the
entry path, with a temporary review role name. PostgreSQL returned:

```
birja_phase10_review_default|t|f|f|f|f|f
```

The columns are role name, inheritance, superuser, database creation, role
creation, replication and bypass-RLS. Supplying those actual flags under the
canonical owner name to the real new validator with `allow_missing_runtime=True`
raised `ValueError`, as expected. The probe ended in ROLLBACK; the temporary
role was not retained. No production or provider access occurred.

**Fix:** Provision a newly created recovery migrator with explicit `NOINHERIT`
and all other required safe flags, including `NOBYPASSRLS`. Do not silently
alter a pre-existing unsafe role into acceptance. Add a regression exercising
the actual `restored()` absent-owner entry path, rather than only the
post-bootstrap direct consumer helper. Verify the newly created owner reaches
the0014 pre-grant checks with the exact safe role boundary; preserve refusal
of unsafe pre-existing flags/memberships. Keep the full retained-archive/TLS
gates mandatory after this focused correction.

## Reviewed boundaries and limits

- Traced explicit0014 tables/sequences, full function declarations/body pins,
  role flags/membership checks, no-ACL-to-quarantine transformation and
  source-versus-clone manifest comparison. Earlier authority review remains
  separate; its closed findings are not reopened here.
- Independently inspected the actual fresh server definition and
  `restore()` → `restored()` → `restore_dividend_authority()` call chain.
- The executor's19/19 SQL contract results and byte-preservation evidence are
  recorded in04-SUMMARY; this review does not claim to have repeated them.
- Only the small rollback-only role-default probe and offline real-validator
  refusal were run independently. No application, source, test, canonical
  state or production files were modified. Only this review report was written;
  no commit was made.

_Reviewer: independent gsd-code-reviewer sub-agent._
