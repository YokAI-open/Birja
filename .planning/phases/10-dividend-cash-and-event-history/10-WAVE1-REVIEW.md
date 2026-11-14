---
phase: 10-dividend-cash-and-event-history
reviewed: 2026-11-12T19:24:49Z
depth: standard
diff_base: 5925b52
reviewed_head: c90f5f3
rechecked_head: 90cef7aeff7358eca8c66e9190156343d4737bca
files_reviewed: 12
files_reviewed_list:
  - backend/app/models/dividend.py
  - backend/app/models/corporate_action.py
  - backend/app/models/__init__.py
  - backend/alembic/versions/0014_dividend_accounting.py
  - backend/tests/test_dividend_schema.py
  - backend/tests/test_migrations.py
  - backend/tests/test_stock_action_migrations.py
  - backend/tests/test_stock_execution_migrations.py
  - backend/app/services/dividend_rules.py
  - backend/tests/test_dividend_rules.py
  - frontend/src/api/eventHistory.ts
  - frontend/src/api/eventHistory.test.ts
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase10 Wave1 Code Review

## Narrative Findings (AI reviewer)

No active BLOCKER or WARNING findings remain in this bounded Wave1 review.

### Resolved WR-01 — WARNING: Correction rejection tests started from invalid terms

**File:** `frontend/src/api/eventHistory.test.ts:41-42`, consumed at `325-335`.

**Original issue:** The exported original correction fixture had rate `0.000000005`,
which has nine fractional places. `fixed()` explicitly accepts at most eight.
Consequently the unchanged fixture already fails `isEventHistoryPage` before
any tested corruption. Eight negative lineage, cash, discriminator and reason
cases mutate this invalid baseline. In particular, removing the
`decision_reference !== id` or `cash_delta !== applied_delta` rejection would
leave their negative cases passing because the independent invalid rate still
rejects the page. The same invalid baseline weakens the chronology assertion.
This makes purported regression coverage for financial/lineage checks unreliable.

**Fix:** Make the shared correction valid: use eligible quantity `50000000`
and rate `0.00000001`, preserving the exact desired total `0.50` and correction
`-0.50`. Assert that this unmodified fixture is accepted before the negative
mutation table. Retain a dedicated explicit nine-place-rate rejection test.
For each negative case, change only its intended property from a known-valid
baseline; add the separate correct no-cash baseline for held outcomes as needed.

**Resolution:** Closed by focused source recheck at
`90cef7aeff7358eca8c66e9190156343d4737bca`, following reported behavioral RED
`f0bf398`. The shared correction now uses `50000000 × 0.00000001 = 0.50`;
the original remains `100000000 × 0.00000001 = 1.00`. Its unchanged baseline
has an explicit acceptance assertion. All existing lineage/cash mutations now
start from valid terms. The verified-no-change fixture explicitly supplies its
own100million quantity, retaining desired1.00 rather than inheriting0.50.
Seven additional individual term mutations each assert baseline acceptance
before rejection, preventing another independent bad term from masking their
target guard. Parent reports actual70focused passes and100%parser coverage;
this reviewer verified the source correction without rerunning tests or DB work.

## Scope and limits

This is the bounded pre-authority Wave1 source review, not full-phase completion.
It inspects the new schema, immutable composite links and successful/held identity
indexes; migration retries, grants and empty downgrade; Decimal range/precision
and once-rounded corrections; strict wire parsing and existing authenticated
transport. Historical test changes were checked against their predecessor intent.
No proven material runtime defect was found in those reviewed changes.

Plan02 payout functions, Plan04 recovery and Plan10 backend projection do not
exist yet by design and are not treated as missing implementation findings.
Their retained/TLS/restricted-role and final advancing authority proofs remain
mandatory before consumers. No tests, DB operations, provider calls or source
mutations were performed during this read-only review; the parent owns the
currently running full backend/frontend gates.

One consumer compatibility point was checked rather than reported as a current
defect: retained forward split rates can be decimal (e.g. `1.5:1`), while the new
wire accepts integral ratio components. An exact reduced `3:2` wire representation
is compatible with the saved economic ratio and does not mutate retained facts.
The future backend projection must honor that wire representation or explicitly
align both sides, and test the supported decimal-source case. C05a now explicitly
freezes this exact rational normalization and requires that regression before
consumer completion. There is no backend projection yet to prove a present
mismatch.

No structural findings block was supplied. No app, migration, test, canonical
state or unrelated files were edited by this reviewer; this artifact is the only
write. Publication and all live/production boundaries remain unchanged.
