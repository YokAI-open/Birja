---
phase: 13-create-and-compare-independent-strategies
plan: "04"
reviewed: 2026-11-18T09:13:48Z
initial_reviewed: 2026-11-18T09:10:57Z
depth: standard
diff_base: 01c360d
diff_head: aba75aa
initial_diff_head: 12cc45a
repair_diff_base: 12cc45a
files_reviewed: 9
files_reviewed_list:
  - deploy/tests/portfolio-sources.py
  - deploy/tests/portfolio-retained-sources.json
  - deploy/tests/portfolio-execution-fixture.py
  - deploy/tests/test-portfolio-fixture-contracts.py
  - deploy/backup-snapshot.py
  - deploy/recovery-bundle.sh
  - deploy/tests/fixtures/portfolio-recovery-0020.json
  - deploy/tests/portfolio-management-recovery-fixture.py
  - deploy/tests/test-portfolio-management-recovery.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  critical: 1
  total: 1
status: clean
---

# Phase 13 Plan 04: Code Review Report

**Reviewed:** 2026-11-18T09:13:48Z  
**Depth:** standard  
**Files Reviewed:** 9  
**Status:** clean — initial blocker resolved

## Summary

Initial review covered the nine-file producer/source-profile change in `01c360d..12cc45a` and established one blocker. Independent re-review of the full repair range `12cc45a..aba75aa` finds it resolved, with no remaining BLOCKER or WARNING. The initial finding is retained below as resolved history. Restore consumer V2 admission and later encrypted/TLS/cold campaign work remain outside this review.

## Narrative Findings (AI reviewer)

## Repair Disposition

**CR-01 — Resolved by `9a54623`.** The 0020-only unsafe aggregate now counts `birja_action_operator` with `rolcanlogin`, so the existing requirement for `unsafe == 0` rejects the changed role state. The repair leaves the frozen 0017 projection and all existing schema/catalogue/authority/quarantine/noACL constants unchanged.

The real PostgreSQL regression added in RED `c26ba5b` first validates the actual normal manifest, enables operator LOGIN, independently asserts that LOGIN took effect, regenerates the manifest through `producer.manifest_sql('0020')`, and requires validation refusal. Its `finally` block rolls back and explicitly restores/commits NOLOGIN, including on assertion failure, then checks the restored flag. The same path retains normal/quarantine/noACL producer fingerprints, authenticated creation replay, closed/conflicting replay refusals and before/after table/sequence equality.

The implementation addendum records the actual failing RED and passing final `--postgres-operator-login` command, plus repeated 8/6/10 affected offline contracts. These execution receipts and the regression source were inspected independently, without rerunning them. No additional unresolved defect was established in the focused repair diff.

## Initial Critical Issue — Resolved History

### CR-01: BLOCKER — V2 producer accepts a LOGIN-enabled action operator

**Disposition:** Resolved by `9a54623`; original severity and initial-source evidence retained below.

**File:** `/home/YokaiExchange/deploy/backup-snapshot.py:954-965`  
**Related projection:** `/home/YokaiExchange/deploy/backup-snapshot.py:803-805`  
**Validator:** `/home/YokaiExchange/deploy/backup-snapshot.py:969-978`

**Issue:** The new producer authenticates the reviewed bootstrap source but incorporates only its catalogue and ACL SQL, not the complete preflight's role checks. The reused `portfolio_authority_sql()` projects role inheritance/superuser/creation/replication/RLS attributes but omits `rolcanlogin`. The new `management_contract.unsafe` aggregate checks rewrite rules, effective runtime CREATE and database/schema ownership, but also omits the action operator's LOGIN state.

Consequently, on an otherwise valid 0020 database:

```sql
ALTER ROLE birja_action_operator LOGIN;
```

leaves the entire generated manifest unchanged: neither pinned catalogue/ACL hash includes this role flag; the separately hashed `portfolio_authority.roles` omits it; and `unsafe` stays zero. `validate_management_manifest()` therefore accepts the state and `Job` proceeds to dump/package it. This contradicts the current source's explicit NOLOGIN boundary for the privileged action-resolution operator. Shared runtime and production preflight already reject this exact drift, but the producer does not execute those preflights, so their protection does not cover this backup path.

**Fix:** Add a 0020-only unsafe count for `birja_action_operator` with `rolcanlogin`, or add an independently pinned management-role projection that includes the flag. Keep the original 0017 authority projection and historical hash meanings unchanged. Add a real disposable PostgreSQL negative that toggles operator LOGIN, generates the actual 0020 manifest and proves producer validation refuses it; restore NOLOGIN in cleanup and retain the positive normal/quarantine profiles. An offline mutation of an already-generated manifest alone cannot detect this omission because the current SQL never emits the changed flag.

## Review Limits

Both reviews were read-only source reviews: no tests, database operations, provider calls, dependency changes, source edits or commits were performed; only this report was written. `git diff --check` passed for the repair range. The executor's actual LOGIN regression and repeated offline/PostgreSQL receipts were inspected as source and recorded evidence, not rerun. Package assembly's mocked external image/registry transport remains correctly distinguished from actual provenance/encryption qualification. Pending Plan 05 consumer work and Plan 17 complete recovery qualification are not qualified by this report.

---

_Reviewer: gsd-code-reviewer_  
_Depth: standard_
