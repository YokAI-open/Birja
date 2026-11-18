---
phase: 13-create-and-compare-independent-strategies
reviewed: 2026-11-18T14:58:14Z
depth: standard
diff_base: 7125fec
reviewed_head: 6bfb447
files_reviewed: 64
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
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  - CR-01
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

## Review Scope and Limits

Initial explicit runtime/config/tool scope: 61 paths, changes relative to
`7125fec`, at `255c4a0` (runtime bytes last changed at `8cdd175`). This is a
standard change-oriented integration review using source/diffs and surrounding
callers, not a fresh requalification of all historical unchanged implementation.
The two initially unchanged trade-page consumers were followed to establish CR-01;
the follow-up explicitly reviewed their repair plus the new routed regression
file at `6bfb447`, bringing the exact listed cumulative scope to 64 files.
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
