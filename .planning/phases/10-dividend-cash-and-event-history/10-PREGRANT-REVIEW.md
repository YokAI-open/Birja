---
phase: 10-dividend-cash-and-event-history
reviewed: 2026-11-13
depth: standard
scope: Plan10-06 fresh-cluster pregrant repair before replacement retained archive
reviewed_head: 64f77951f99b6a1dfb90af8f9872a421fc676fb4
regression_commit: 50eff38e4e90cedc6ac9d56ce5b037df43134b99
files_reviewed: 2
files_reviewed_list:
  - deploy/verify-restore.py
  - deploy/tests/test-stock-recovery-contracts.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase10 fresh-cluster pregrant repair review

## Narrative Findings (AI reviewer)

**Targeted independent review: clean at64f7795.** No remaining material issue
was identified in this bounded repair and its fresh-cluster regression. Earlier
04 recovery-owner and02 financial-authority review histories remain separate.

### Failure and repair boundary

The actual retained0014 restore on a genuinely fresh server encountered a
name-based lookup for the absent `birja_action_operator` role. Calling full
`canonical()` inside the dividend pregrant check queried resolution permissions
before the independently authenticated resolution helper could create that
fixed role. A clone on the source server already had the role and masked the
ordering problem. The reported old retained archive and its failed0014 run
remain historical evidence, not a successful replacement-archive proof.

The new `dividend_pregrant_structure()` uses only the trusted0014 producer
query. It requires exactly one occurrence of the exact trusted resolution
authority fragment before replacing that value with SQL NULL. Zero or multiple
occurrences refuse before a SQL call. The same UTC setting and complete public
table/sequence schema guard remain. Its output contains only complete schema
metadata and execution-trigger definitions; the partial authority object is
not exposed as a canonical manifest or accepted by `verify()`.

Traced the full call chain and confirmed:

- Exact dividend declarations, independently pinned bodies/owners, no-ACL
  function state and safe canonical role flags/memberships are authenticated
  before this structure query and before any runtime grant reconstruction.
- Schema and trigger metadata still must match the independently pinned0014
  hashes. The new helper does not substitute caller-supplied hashes, choose
  arbitrary query fragments or repair corrupted definitions into acceptance.
- Reconstruction order remains dividend quarantine, execution authority,
  then independently authenticated resolution authority. Full `canonical()`
  and `verify()` remain unchanged, with complete resolution, execution,
  dividend and role identity verification after reconstruction.
- Default PUBLIC execution is still revoked; app/scheduler receive no dividend
  payout execution. The repair adds no authority or role/grant bypass.

### Independent actual verification

Ran from the repository root against only the owned disposable stacks:

```
python3 deploy/tests/test-stock-recovery-contracts.py --postgres \
  RevisionContracts.test_dividend_pregrant_structure_refuses_ambiguous_query \
  PostgreSQLContracts.test_zzzz_dividend_restore_on_genuinely_fresh_cluster
```

**Result: 2passed,0skipped,30.884s.** Log:
`/tmp/birja-phase10-pregrant-review-recheck.log`.

The fresh-cluster test performs an actual custom-format dump and actual
`pg_restore`, starting each destination with only its fixed bootstrap role.
The positive path completes real `restored()` entry, full canonical0014
validation and actual SQLSTATE42501 refusals for both runtime payout callers.
Negative paths tamper function metadata or schema after actual restoration and
before pregrant authentication, or preprovision an unsafe runtime role. They
refuse without reconstructing missing runtime/operator roles, and the unsafe
pre-existing role is not silently repaired. Query-fragment zero/multiple
occurrence cases separately refuse before SQL execution.

No source, tracked tests, state or production files were modified during this
review. Only this report was written; no commit was made. The focused processes
finished, and the fresh test servers were removed by the test's cleanup path.

## Limits and next gate

This independently verifies the repair and real fresh-cluster path. It does
not claim a new retained recovery archive has been built, signed off or replayed,
nor repeat the executor's full23-case SQL suite. The replacement archive must
contain these reviewed bytes and pass the mandatory complete same-archive
retained/role/TLS gates before financial consumers. No provider, production,
installed-tool, B2, timer, publication or deployment action is authorized by
this review.

_Reviewer: independent gsd-code-reviewer sub-agent._
