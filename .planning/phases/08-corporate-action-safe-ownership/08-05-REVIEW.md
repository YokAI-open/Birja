---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T12:24:23Z
depth: deep
review_head: cf637f009026709944c075095ad8bbc274f32140
ownership_source_sha256: 08c6d75bac572d2c3a62d15d65efb28a6e9166129668e6bf8e17095de2c064e9
files_reviewed: 7
files_reviewed_list:
  - backend/app/services/stock_ownership.py
  - backend/tests/test_stock_ownership.py
  - backend/tests/stock_action_fixtures.py
  - backend/alembic/versions/0011_stock_action_accounting.py
  - deploy/db/bootstrap-roles.sql
  - deploy/tests/ops-fixtures.py
  - backend/tests/test_stock_action_migrations.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 08-05: Focused Ownership Review

Reviewed the stable ownership service, fixtures, causal schema and scoped ACL
delta while executor role/TLS proofs were running separately. No tests, database
operations, provider requests, credentials, source edits or commits occurred.
The necessary scheduler six-column immutable-trade projection was treated as the
explicitly reviewed minimum-read design, not an escalation finding by itself.

## Narrative Findings (AI reviewer)

### Targeted re-review at `cf637f0`

**Zero active BLOCKER/WARNING findings in the reviewed corrections.** Both
historical findings below are resolved with explicit conservative limits.
Verified the source SHA256 recorded above; no tests or database operations were
performed. Executor-reported 207-test/coverage results and pending final TLS
proof remain separately attributed.

CR-01: rows on or before a split sequence boundary now require economic time
strictly before its cutoff. The added buy/sell boundary-tie fixtures require a
held outcome, preventing the previously mixed-unit eligibility quantity.

CR-02: before querying xmin transaction status, both new fill and split paths
read the full current transaction ID and reject unsupported epochs with the
typed `transaction_epoch_unverified` reason. The implementation deliberately
does not claim general wrapped-XID operation or guess an epoch. Existing causal
replay precedes this guard, and historical reconstruction does not invoke it.
Root/savepoint and committed/other-transaction orphan cases remain covered in
the regression source.

**Operational limitation:** automatic new stock fill/split journal append is
unsupported once the full transaction ID reaches 2**32; a separately verified
same-current-transaction proof is required to lift that limit. This fail-closed
restriction is documented directly in the service. It is a retained capability
limit, not evidence that arbitrary XID epochs are supported. No authority,
financial matching or committed-orphan checks were relaxed.

## Historical Findings

### CR-01 — BLOCKER, RESOLVED: Exact-cutoff fills contaminate post-split exclusive snapshots

**File:** `/home/YokaiExchange/backend/app/services/stock_ownership.py:533`

**Also affected:** `_check_units` owner reconstruction near line 442.

**Issue:** The journal validator permits a fill with economic time exactly equal
to a split cutoff on or before `sequence_boundary`; the split delta is calculated
from the resulting holding. Historical reconstruction excludes that exact-cutoff
fill but includes its share of the split delta when post-split units are selected.
For example: opening quantity 10, an old-unit buy of 5 exactly at the cutoff,
then a 2:1 split with delta 15. The accepted post-split exclusive snapshot is
`10 + 15 = 25`, even though the strict pre-cutoff ownership is 10 old shares,
equivalent to 20 new shares. A same-boundary sell creates the inverse error.
This is a financial eligibility error, not merely a display issue.

**Fix:** Either reject/hold ambiguous exact-cutoff fills before the split boundary
or reconstruct the selected pre-cutoff ownership through the verified exact unit
transformations instead of summing deltas that include excluded fills. Keep the
strict exclusion of cutoff-time purchases/sales and explicit pre/post unit choice.
Add a real PostgreSQL buy and sell boundary-tie regression; require an exact
result or an explicit held outcome, never the mixed-unit quantity.

### CR-02 — BLOCKER, RESOLVED: Pending-cause transaction check loses the XID epoch

**File:** `/home/YokaiExchange/backend/app/services/stock_ownership.py:185`

**Also affected:** identical split-application check at line 198.

**Issue:** Tuple `xmin` is a 32-bit transaction ID. Casting its decimal text to
`xid8` treats it as an epoch-zero full transaction ID, rather than reconstructing
the actual current epoch. After the cluster's first transaction-ID wrap, a genuine
new fill or split application in the current transaction therefore queries an
old transaction's status and is rejected, or raises an unavailable-status error.
The service does not document or enforce an epoch-zero deployment limitation.
The nested-transaction check must retain its existing same-transaction protection
without this epoch assumption. PostgreSQL distinguishes these transaction-ID
representations in its [transaction information documentation](https://www.postgresql.org/docs/18/functions-info.html#FUNCTIONS-PG-SNAPSHOT).

**Fix:** Resolve the tuple XID against the current full transaction epoch using
the proper wrap-aware boundary semantics before status lookup, or use another
reviewed same-current-transaction ownership test that handles subtransactions.
Keep committed orphan-fill rejection. Test wrap conversion boundaries explicitly
alongside actual root/savepoint transaction and committed-orphan regressions;
do not relax this to accepting any visible committed cause.
