---
phase: 13-create-and-compare-independent-strategies
plan: "05"
reviewed: 2026-11-18T09:34:44Z
initial_reviewed: 2026-11-18T09:30:30Z
depth: standard
diff_base: 7864d3d
diff_head: 668d769
initial_diff_head: b0bd7c1
repair_diff_base: b0bd7c1
files_reviewed: 6
files_reviewed_list:
  - deploy/verify-restore.py
  - deploy/tests/test-portfolio-recovery-contracts.py
  - deploy/tests/test-portfolio-management-recovery.py
  - deploy/tests/test-portfolio-migration-runner.py
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/test-portfolio-smoke-image.py
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

# Phase 13 Plan 05: Code Review Report

**Reviewed:** 2026-11-18T09:34:44Z  
**Depth:** standard  
**Files Reviewed:** 6  
**Status:** clean — initial blocker resolved

## Summary

Initial review covered the six-file consumer/quarantine/smoke change in `7864d3d..b0bd7c1` and established one blocker. Independent re-review of the complete repair range `b0bd7c1..668d769` finds it resolved, with no remaining BLOCKER or WARNING. The original finding below remains as resolved history. No additional concrete defect was established in this focused repair review.

## Narrative Findings (AI reviewer)

## Repair Disposition

**CR-01 — Resolved by `2c2efae`.** Immediately after reading a V2 inventory, `bundle_verify` now requires both declarations, the exact four retained archive names/hashes, the exact schema-contract fields, the fixed finite revision array and the exact source-hash key inventory. These guards precede construction of the permitted member set, saved-image verification and runtime admission. Existing later validation still matches each declared source-hash value against its authenticated archive member; V2 cannot coherently remove either declaration or its associated archives.

The regression builds three coherent V2 omissions separately and together, recalculating member lists, inventory bytes, all checksum entries and the supplied archive digest. It requires all three to fail and asserts that saved-image verification/runtime were never invoked. Four V1 positive controls use original CORE/unit/V1 bytes from the complete fixed `4b4320b` release with the optional declarations present, individually absent and jointly absent. This preserves the historical absence semantics rather than extending the V2 requirements backward.

The summary records actual failing RED `0677561`, GREEN `2c2efae`, 42 repeated focused tests and a repeated actual 0020 logical roundtrip/refusal/oracle proof. Test source and recorded receipts were inspected independently without rerunning them. Existing source-profile/hash meanings and pending full qualification limits remain unchanged.

## Initial Critical Issue — Resolved History

### CR-01: BLOCKER — Coherent omission of mandatory V2 recovery metadata is accepted

**Disposition:** Resolved by `2c2efae`; original severity and initial-source evidence retained below.

**File:** `/home/YokaiExchange/deploy/verify-restore.py:445-456`  
**Also affected:** `/home/YokaiExchange/deploy/verify-restore.py:523-541`

**Issue:** V2 requires a complete fixed retained 0017 source release and an explicit current schema/source contract, but both `retained_source_payloads` and `schema_contract` remain optional in the verifier. The new version branch checks their contents only when the keys happen to exist. The required-profile check at the end verifies the V2/profile association without requiring either missing field.

A self-consistent damaged V2 archive can therefore:

1. Remove `retained_source_payloads` from `INVENTORY.json` and remove every `sources/*.tar` member.
2. Update `INVENTORY.files`, `SHA256SUMS` and the supplied archive digest to match the remaining members.
3. Keep the valid V2 payload and `deploy-recovery-v3` profile unchanged.

`allowed` then never includes any retained source archive, so the exact-member comparison succeeds. The remaining checks do not require the fixed 0017 archive or any of the earlier retained source releases. The result is accepted as a complete V2 recovery artifact even though it cannot execute its promised retained-source recovery lanes.

Independently, removing `schema_contract` and updating the inventory checksum also succeeds: `verify_contract_inventory()` returns without validating the explicit revision/source-hash contract, while `verify_portfolio_inventory()` validates only `portfolio_payload`. Both omissions can be combined. An external archive checksum establishes byte integrity for the supplied artifact; it cannot supply the omitted structural requirements.

The new missing-member regression removes archive members while preserving their inventory declarations, which correctly fails but does not exercise these coherent metadata omissions.

**Fix:** For V2, require `schema_contract` and `retained_source_payloads` before constructing the allowed member set or importing runtime tools, and validate their complete exact current/fixed-retained values. Preserve legacy/V1 absence semantics explicitly rather than inheriting them into V2. Add tests that coherently strip each mandatory metadata field separately and together; for retained sources also strip all source archives, update member lists/checksums and compute the new archive digest. All such artifacts must fail `bundle_verify(..., required_profile='deploy-recovery-v3')`, while genuine V2 and retained V1 controls remain accepted.

## Review Limits

Both reviews were read-only independent source reviews: no tests, database operations, provider calls, dependency changes, source edits or commits were performed; only this report was written. `git diff --check` passed for the repair range. The executor reproduced the initial finding and supplied the coherent-omission negatives, fixed-source V1 positive controls and actual roundtrip evidence; those sources/receipts were inspected rather than rerun. Complete encrypted/TLS/image qualification remains Plan 17 work; the documented old deployment gate's explicit 0020 refusal remains outside this plan's implementation scope.

---

_Reviewer: gsd-code-reviewer_  
_Depth: standard_
