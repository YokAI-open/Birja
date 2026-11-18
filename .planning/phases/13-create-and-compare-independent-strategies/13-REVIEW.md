---
phase: 13-create-and-compare-independent-strategies
reviewed: 2026-11-18T16:32:06Z
depth: standard
diff_base: 7125fec
reviewed_head: 99166d9
files_reviewed: 66
files_reviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/sql/0019_portfolio_metadata.sql
  - backend/alembic/sql/0020_portfolio_management.sql
  - backend/alembic/versions/0018_portfolio_management_expansion.py
  - backend/alembic/versions/0019_portfolio_management_backfill.py
  - backend/alembic/versions/0020_portfolio_management_authority.py
  - backend/app/api/v2/portfolio_management.py
  - backend/app/api/v2/portfolios.py
  - backend/app/core/config.py
  - backend/app/db/dev_bootstrap.py
  - backend/app/db/portfolio_bootstrap.py
  - backend/app/db/portfolio_migrate.py
  - backend/app/db/schema_contract.py
  - backend/app/models/__init__.py
  - backend/app/models/portfolio_creation.py
  - backend/app/models/user.py
  - backend/app/schemas/portfolios.py
  - backend/app/services/accounts.py
  - backend/app/services/portfolio.py
  - backend/app/services/portfolios.py
  - deploy/backup-snapshot.py
  - deploy/db/bootstrap-roles.sql
  - deploy/recovery-bundle.sh
  - deploy/tests/fixtures/portfolio-recovery-0020.json
  - deploy/tests/ops-fixtures.py
  - deploy/tests/portfolio-execution-fixture.py
  - deploy/tests/portfolio-management-recovery-fixture.py
  - deploy/tests/portfolio-retained-sources.json
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/portfolio-sources.py
  - deploy/tests/portfolio-ui-evidence.py
  - deploy/tests/run-portfolio-validation.py
  - deploy/tests/run-stock-browser.py
  - deploy/tests/test-db-operations.sh
  - deploy/tests/test-dev-bootstrap.py
  - deploy/tests/test-rollback-db-security.sh
  - deploy/verify-restore.py
  - frontend/e2e/portfolio-browser-fixture.py
  - frontend/src/App.tsx
  - frontend/src/api/portfolio.ts
  - frontend/src/api/portfolioManagement.ts
  - frontend/src/api/portfolioOverview.ts
  - frontend/src/api/portfolios.ts
  - frontend/src/components/PortfolioCreateForm.tsx
  - frontend/src/components/PortfolioMetadataForm.tsx
  - frontend/src/components/PortfolioSwitcher.tsx
  - frontend/src/components/PortfolioTargetBoundary.tsx
  - frontend/src/hooks/useEventHistory.ts
  - frontend/src/hooks/useHistory.ts
  - frontend/src/hooks/usePortfolio.ts
  - frontend/src/hooks/usePortfolioManagement.ts
  - frontend/src/hooks/usePortfolioOverview.ts
  - frontend/src/hooks/usePortfolioTarget.ts
  - frontend/src/hooks/useStockTrade.ts
  - frontend/src/hooks/useTrade.ts
  - frontend/src/lib/portfolioCreationAttempt.ts
  - frontend/src/lib/portfolioMetadataEvents.ts
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/PortfolioPage.tsx
  - frontend/src/pages/PortfoliosPage.tsx
  - frontend/src/pages/TradePage.tsx
  - frontend/src/pages/StockTradePage.tsx
  - frontend/src/pages/TradeRenameRecovery.test.tsx
  - backend/tests/test_portfolio_management_grants.py
  - backend/tests/test_portfolio_strategy_events.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  - CR-01
  - CR-02
status: clean
---

# Phase 13: Integrated Code Review

## Narrative Findings (AI reviewer)

### CR-01: Retained trade names are not wired into the actual ticket and receipt UI

**Original classification:** BLOCKER — incorrect original-attempt presentation after rename/remount.
**Disposition:** RESOLVED in `6bfb447`, independently re-reviewed after RED `bc4298c`.

**Files:** `frontend/src/hooks/useTrade.ts:175`,
`frontend/src/hooks/useStockTrade.ts:39`; integration callers
`frontend/src/pages/TradePage.tsx:102`, `:254`, `:300` and
`frontend/src/pages/StockTradePage.tsx:45`, `:269`, `:275`.

**Issue:** Both hooks correctly retain the original attempt name, but their actual
page components still render independently stored component-local labels.
`TradePage` initializes `attemptName` from `target.name`; `StockTradePage`
initializes `originalName` the same way. Neither page reads the retained hook
field. Those local values do not survive the real metadata-renewal boundary:
`PortfolioTargetBoundary` removes its financial Outlet while discovery is
invalidated/loading and then mounts it again with the renamed target.

Concrete sequence: submit an order in **Original**, lose or defer its response,
rename that portfolio to **Renamed** in another tab, and let authenticated
metadata renewal complete. The original request remains in the hook cache with
its original ID/key/payload/name, but the remounted page initializes its local
label as **Renamed**. Both the unresolved original attempt and its subsequent
explicit-replay receipt therefore show the new name. A previously filled
cached receipt has the same remount problem. This defeats the planned distinction
between the current page label and the frozen original-attempt label. It does
not demonstrate cash duplication, cross-owner disclosure or request retargeting;
the defect is the incorrect financial-context label.

**Fix:** Use `trade.originalName` for crypto pending/unknown/filled presentation,
and `t.originalName` (or the attempt's frozen `portfolioName`) for stock original
attempts and receipts. Retain the current/local preview name only for an
unsubmitted preview. The page header can continue showing the current
authenticated name; clear the original label only through the existing explicit
new-order transition. Do not rewrite the original request or weaken target guards.

**Required regression:** A routed component/browser test for each asset should
submit a pending/lost original, perform a real rename/discovery invalidation
that removes and remounts the financial Outlet, assert a current **Renamed**
page context alongside an **Original** unresolved-attempt context, then check
the original result with byte-identical ID/key/payload and assert an **Original**
receipt. Include revisiting an already filled receipt after rename. Existing
`portfolioCrypto.test.tsx` / `portfolioStock.test.tsx` hook tests assert the
retained name but do not render these page-local consumers, so they cannot
detect this integration failure.

**Resolution review:** The crypto consumer now takes its unresolved-attempt and
receipt labels from `trade.originalName`; the stock consumer uses
`t.originalName` for an original attempt/receipt and keeps separate local
`previewName` only for an unsubmitted quote. Both current page contexts remain
bound to the newly authenticated name. The existing hook state retains the
original name through late-result recovery and filled receipts, then its
explicit new-order transition clears it. No request payload, target guard,
idempotency key, money calculation or authority check changed.

`TradeRenameRecovery.test.tsx` renders the actual pages under the actual
`PortfolioTargetBoundary`, rather than mocking their hook-returned name. Its
six cases cover crypto/stock crossed with lost, pending and already-filled
outcomes. Each forces discovery loading, asserts removal/remount of the
financial page, checks the current renamed context and frozen original context,
checks byte-identical replay requests where applicable, checks the receipt's
portfolio link, and verifies Trade again clears the original name and quantity.
The case structure and assertions address the failure described above. The
executor reports all six failed before the consumer repair and passed after it;
138 affected cases, typecheck and lint also passed. This reviewer inspected the
actual diff, test and hook/caller lifecycle; it did not rerun those commands.
No remaining or newly introduced defect was demonstrated in this repair.

### CR-02: Management owner locks invert the dividend user foreign-key lock

**Original classification:** BLOCKER — concurrent metadata/creation replay and
dividend processing can deadlock or encounter a lock-timeout refusal.
**Disposition:** RESOLVED in `99166d9`, independently reviewed after deterministic
RED `203815f`. Original trace and fixture review are preserved in
`13-17-FIXTURE-REVIEW.md`.

**Runtime source:** `backend/alembic/sql/0020_portfolio_management.sql:16`,
`:63`, `:96`. All three owner-row locks now use `FOR NO KEY UPDATE`, retaining
mutual serialization among management operations while allowing the dividend
ledger FK's `KEY SHARE`. The account lock, authenticated owner predicate,
canonicalization, cap/quota ordering, permanent owner/key binding, grant amount,
transactions, timeout and row checks are unchanged. The fix does not alter
retained0017 dividend SQL or historical0015–17/0019 migrations.

**Binding review:** Independently compared all1172 measured catalogue records
before/after: reversing only the exact `WHERE u.id=p_user FOR NO KEY UPDATE;`
line in the three routine definitions makes the entire record multiset equal.
The measured ACL is unchanged at
`041a948470f9692628da43b35263a47bf58f4815310a0793d5eec099fa64c87e`.
The current catalogue becomes
`535cacb140a3a1753b5cf27e2eadcb80bc272a9b12772defd3936a3edc6c2209`.
The producer, production bootstrap, migration runner, restore source guards and
current recovery fixture all bind the corresponding current hashes; no matching
predicate, source guard, historical literal or privilege check was removed.
The stored0020 specimen's only JSON changes are that catalogue hash and the
same three function definitions; finances, table digests, identity tails,
constraints, owners and ACLs remain exact.

Recomputed the current authority hash from the specimen as
`0192d3a7222af2a91930d34b7089ef93371e849bc32f911cacc8383fd5ac5ebf`;
independently projecting the six quarantined financial/management routine ACL
revocations yields
`d6486b31f5609a6fdbeadaf4eeb7d9f0b4eaabe1de0566e646d85080a939fa26`;
projecting no-ACL tables/columns/sequences and default PUBLIC function EXECUTE
yields `e88cb1971126447232f872c3b93fe18454ef58094becdcecd4d9066af44e3cfe`.
These match the repaired constants; schema and ACL fingerprints stay unchanged.
This validates the intended new definition, not an arbitrary repin of a failing
financial or permission oracle.

**Regression review:** The observed-blocking-PID case now covers metadata and
original creation replay, requiring both successful200, the same root ID,
cash10000.50 and exactly two original creation records. Restricted-grant tests
also exercise initialize/create/rename after reapplying the unchanged ACL
profile. Existing cap, canonical intent and replay tests remain in scope.
Inspected the receipt and verified its committed source and log hashes:
70 focused tests passed363.48s, the two overlap cases passed12.71s, and four
offline contract groups passed8+11+8+6. No new issue was demonstrated. These
commands were run by the executor, not rerun by this reviewer. They do not
replace final full-suite/image/browser/TLS/encrypted-recovery qualification.

## Review Scope and Limits

Initial explicit runtime/config/tool scope: 61 paths, changes relative to
`7125fec`, at `255c4a0` (runtime bytes last changed at `8cdd175`). This is a
standard change-oriented integration review using source/diffs and surrounding
callers, not a fresh requalification of all historical unchanged implementation.
The two initially unchanged trade-page consumers were followed to establish CR-01;
the follow-up explicitly reviewed their repair plus the new routed regression
file at `6bfb447`. CR-02 follow-up reviewed the eleven-file delta
`203815f..99166d9`, including two strengthened test files added to this cumulative
list, bringing its exact scope to66. The separate35-file fixture review is
retained in `13-17-FIXTURE-REVIEW.md`; those paths are not silently claimed as
another full runtime review here.
The separate 51 changed test paths have per-plan review records; this report
does not claim another comprehensive review of every test. Fallow was disabled
and no structural substrate was supplied.

The pass traced SQL canonical intent and permanent owner/key replay ordering,
onboarding latches and fixed grants, service-bound ownership/CSRF/body bounds,
metadata route leases and unknown-result handling, target/session cache guards,
detail/overview proof sharing, retained/current source and schema binding,
versioned recovery inventory completeness and quarantine, and final security/
same-archive campaign guards. No additional demonstrated issue is reported in
those paths. Prior clean per-plan reviews are evidence of their narrower passes,
not a reason to disregard the combined consumer defect above.

This review ran no database/browser/security/recovery campaign and changed no
source or tests. Plan17 actual final-source qualification remains mandatory.
The previously owner-accepted issue35 picomatch advisory, its narrow checks and
2026-12-17 expiry are retained; no remediation or expanded exception is claimed.
Owner UI/native200 acceptance is a separate human result; the source repair and
its regression evidence resolve CR-01. Changed render inputs require refreshed
source-bound evidence before final qualification. No provider, production,
dependency or publication operation occurred.

_Reviewer: independent gsd-code-reviewer; no commit created._
