---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T16:55:16Z
depth: deep
diff_base: 949db3a
review_head: 0cea8b56ab0967ba4e24661b872e593a700e555b
review_scope: runtime_and_configuration
files_reviewed: 33
files_reviewed_list:
  - .env.example
  - backend/alembic/versions/0011_stock_action_accounting.py
  - backend/alembic/versions/0012_stock_action_resolution.py
  - backend/app/core/config.py
  - backend/app/models/__init__.py
  - backend/app/models/corporate_action.py
  - backend/app/models/stock.py
  - backend/app/models/trade.py
  - backend/app/schemas/stocks.py
  - backend/app/services/alpaca_actions.py
  - backend/app/services/corporate_action_rules.py
  - backend/app/services/corporate_actions.py
  - backend/app/services/stock_action_reconciliation.py
  - backend/app/services/stock_action_rules.py
  - backend/app/services/stock_admission.py
  - backend/app/services/stock_ownership.py
  - backend/app/services/stock_quotes.py
  - backend/app/services/stocks.py
  - backend/app/tasks/scheduler.py
  - backend/app/tasks/stock_actions.py
  - backend/app/tasks/stock_scheduler.py
  - deploy/backup-manifest.sql
  - deploy/backup-snapshot.py
  - deploy/db/bootstrap-roles.sql
  - deploy/verify-restore.py
  - docker-compose.prod.yml
  - docker-compose.yml
  - frontend/src/api/stocks.ts
  - frontend/src/components/StockActionState.tsx
  - frontend/src/components/StockSection.tsx
  - frontend/src/hooks/useStocks.ts
  - frontend/src/lib/stockActionCopy.ts
  - scripts/stock-actions.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
followup_required: Plan12_CI_coverage_contract_changes
---

# Phase 8: Final Runtime Code Review

**Reviewed:** 2026-11-11T16:55:16Z  
**Depth:** deep  
**Files reviewed:** 33 runtime/configuration sources  
**Status:** clean for the recorded source scope

## Narrative Findings (AI reviewer)

No active **BLOCKER** or **WARNING** findings were identified in the reviewed
runtime/configuration source. Earlier resolved findings remain historical in
08-01 through 08-10-REVIEW.md; this report does not reopen them or infer correctness
from their reported test counts.

The explicit scope is the 33 changed runtime/configuration files listed above,
selected from baseline `949db3a`. Supporting regression source and prior reviews
were consulted for reachability and earlier dispositions; this is not a claim
that every changed test or operations fixture received a new complete review.
Backend/accounting/recovery sources still match the frozen `f6e9d0a` tree.
The client guard is the reviewed `7473df3` implementation. The final recorded
StockSection hash matches committed `0cea8b5`, including all three final
Side/quote-badge/timestamp intrinsic-size and wrapping corrections.

### Cross-module traces

- **Accounting and ownership:** Traced scheduler ingestion through immutable
  event/source/revision/observation identities, shared instrument gates, pending
  immutable causes, whole-instrument history checks, exact forward-split planning,
  quantity-only holding updates and journal append. Fractional/late earlier
  boundaries stop later effects. Existing basis, cash and fills are preserved.
  Exclusive dividend cutoff reconstruction retains departed owners and explicit
  pre/post-split denomination. Applicable final action/calendar/monitor checks
  abort the caller-owned transaction on changed or expired authority.
- **Monitoring and persistence:** Traced finite REST/known-ID/replay results,
  inclusive immutable mutation replay, policy-bound durable continuation,
  fixed-target completeness, all-twenty publication guards and actual-attempt
  account quota hooks. A healthy source cycle does not erase an independent
  economic hold. Uncertain multi-security identity cannot silently remap the
  globally unique provider event; unverifiable complete coverage remains held.
- **Operator and recovery:** Traced protected evidence/CA reads, configured scope,
  admission/calendar row-and-digest snapshot binding and the narrow 0012 function
  through expected revision/history/ledger/unit/epoch checks. Reviewed grants,
  immutability, guarded downgrade, exact revision dispatch, archive-derived
  sequence state, independently pinned function authority and quarantined fixed
  allowlist restoration. No caller-supplied SQL or unrestricted healthy override
  enters these paths.
- **API and quote units:** Traced gate-bound local unit assignment, strict
  post-boundary source observations, source-time monotonic persistence and
  unchanged-unit refusal. Final READ COMMITTED API authority precedes the fresh
  projection clock, with no subsequent await. Persistent holds, changed applied
  revisions, pending canonical boundaries and current generation/calendar rights
  suppress unsafe quote values and source times. Denied derived authority uses
  generic epoch-zero/null-time action metadata.
- **Client and UI source:** Traced strict whole-envelope parsing into auth-scoped
  query state, raw epoch/generation/server-time maxima, conservative monotonic
  upper-clock retention, reduction-only late responses, sanitized retained
  snapshots, remounts and exact deadline projection. Reviewed fixed action copy,
  independent status/session/trading text, number/time suppression and explicit
  retry error/focus behavior. Final Side block/minimum-width/wrapping,
  quote-badge automatic-height/wrapping and StockTime intrinsic-size bounds were
  re-read against the existing Badge composition; they introduce no additional
  source finding and change no authority, parsing or request behavior.

### Verification and acceptance limits

This reviewer performed source inspection and read-only git/hash operations.
No tests, browser sessions, database/Docker operations, provider requests,
credential/private configuration reads, production operations, installations or
source edits were performed. Executor proof in 08-LOCAL-PROOF.md and plan summaries
remains separately attributed; no passing runtime result is claimed here.

This report makes no screenshot, contrast, overflow, zoom, browser-matrix or
owner-acceptance claim. The independent UI auditor owns those conclusions in
08-UI-REVIEW.md. Actual CSS 200% zoom and a 640-CSS-pixel reflow viewport remain
distinct evidence and must not be described as interchangeable native zoom.

Plan 12's pending exact critical-module CI/CLAUDE/test mirror and scheduler-test
reliability corrections require a focused follow-up after their source freeze.
They are not included in this 33-file result. A changed runtime source likewise
requires affected-scope re-review; later documentation/test-only commits do not
silently change the frozen runtime identities below.

Stock execution remains false. Phase 9 fills, Phase 10 cash/public History,
unsupported financial repairs, provider rights/live verification, ongoing
activation, publication and deployment remain outside this source review.
The documented full-XID >=2**32 refusal remains an explicit operational limit,
not claimed wraparound support.

### Frozen source identities

| Source | SHA-256 |
| --- | --- |
| backend/alembic/versions/0011_stock_action_accounting.py | `ba07623bca2cff4e709971e2157364e417d877b085ff5e4f24dfa3e96fb72af3` |
| backend/alembic/versions/0012_stock_action_resolution.py | `439a36e6c10c67600d0388c5d1ee11be6425fb4b2c3b71523d6c430928bd8ce0` |
| backend/app/services/stock_ownership.py | `08c6d75bac572d2c3a62d15d65efb28a6e9166129668e6bf8e17095de2c064e9` |
| backend/app/services/corporate_actions.py | `6be8f49158009d9b1e9c927ec8d88813770085ff51f25d1a43d8ab5f0fdccfc3` |
| backend/app/services/stocks.py | `12c2bf3dfe16fa5446342adebe4b5ccae9f858b8a4260258c38b418f973e3fdc` |
| backend/app/services/stock_quotes.py | `0aeee6f1982802c1960c9cc7a83c5181507e9e4950c544c15ba74904f0f2d7e6` |
| backend/app/services/stock_action_reconciliation.py | `3633a7a83febea3bb629c64888ced272080b0eb017a8b228e8274bdd9fe8def9` |
| backend/app/services/alpaca_actions.py | `e8cb2eb9c5b79eb35918b02327107662f0a9e7a9a52b7eb128082e6caecf3a16` |
| backend/app/tasks/stock_actions.py | `465be3c19d01be2254f3fbd073c2a9b4aeb3e2dbe2986fa261e7c7acf5813399` |
| backend/app/tasks/stock_scheduler.py | `5c9b255122f4b85ec7c15c5d1f42a458aba8882d2f6bdbe5e53be99dc7b194e2` |
| backend/app/tasks/scheduler.py | `b9f6be7cf4834aeb2627d35efc3ad64cbaa3be76a0600091803e871c2e3fba31` |
| frontend/src/api/stocks.ts | `3ec74a0f69a7b1cac338954fa18e2efc0dddc29d7a3127b4e902609a618d5e53` |
| frontend/src/hooks/useStocks.ts | `7befec3b3df07084226d8278def3236a3077965feee2f0d44d04a8f8d6c9143d` |
| frontend/src/components/StockSection.tsx | `aee6a806a4588c1af653fe84f2e40cecae286a2fa59101369f3c4cb98ef2516d` |
| frontend/src/components/StockActionState.tsx | `3c0d4ef7af80cbe291f95a82d02929b17114fac3f128dc4b6cbd7dc7ea6bb726` |
| frontend/src/lib/stockActionCopy.ts | `f4c78027395273fed3976c9e40a46f4ab1fc141a1b7ad690a3e28a19b62e1f5a` |
| deploy/backup-snapshot.py | `9e24a224718c3aab9c5252185da64a6e44ee6c26c320f2cbcb8b4b12246cf2d4` |
| deploy/verify-restore.py | `1aa4337745716237f228e468da6a09202907fffbdd9621e9913a8a8272c08bf6` |
| scripts/stock-actions.py | `fb493fcbd19192ae3a6fadab3df61e1d92e560d552c50efa18faa149263c93db` |

---

_Reviewer: independent gsd-code-reviewer; source-only deep review._
