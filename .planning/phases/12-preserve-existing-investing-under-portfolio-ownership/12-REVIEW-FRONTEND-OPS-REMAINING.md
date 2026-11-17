---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17
depth: standard
diff_base: e14fa20753a008bab52afbe04c8f735faf5f9fd2
reviewed_head: 05426f76640f0d15ca27551b723dd07d766b3bb6
files_requested: 64
files_reviewed: 63
coverage: partial
files_reviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - deploy/backup-manifest.sql
  - deploy/db/bootstrap-roles.sql
  - deploy/tests/dividend-execution-fixture.py
  - deploy/tests/ops-fixtures.py
  - deploy/tests/portfolio-execution-fixture.py
  - deploy/tests/portfolio-retained-sources.json
  - deploy/tests/portfolio-smoke.py
  - deploy/tests/run-stock-browser.py
  - deploy/tests/selected-cutover.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-dev-bootstrap.py
  - deploy/tests/test-portfolio-fixture-contracts.py
  - deploy/tests/test-portfolio-migration-runner.py
  - deploy/tests/test-portfolio-recovery-contracts.py
  - deploy/tests/test-selected-cutover-contracts.py
  - deploy/verify-restore.py
  - frontend/e2e/auth.spec.ts
  - frontend/e2e/dividends-history.spec.ts
  - frontend/e2e/helpers.ts
  - frontend/e2e/markets.spec.ts
  - frontend/e2e/portfolio-browser-fixture.py
  - frontend/e2e/portfolio-history.spec.ts
  - frontend/e2e/portfolio-ownership.spec.ts
  - frontend/e2e/stock-trade-fixture.py
  - frontend/e2e/stock-trades.spec.ts
  - frontend/e2e/trade.spec.ts
  - frontend/src/App.test.tsx
  - frontend/src/api/auth.test.ts
  - frontend/src/api/eventHistory.test.ts
  - frontend/src/api/history.test.ts
  - frontend/src/api/portfolio.test.ts
  - frontend/src/api/portfolioReads.test.ts
  - frontend/src/api/portfolioTrades.test.ts
  - frontend/src/api/stockTrades.test.ts
  - frontend/src/api/trades.test.ts
  - frontend/src/components/HistoryEventDetails.test.tsx
  - frontend/src/components/PortfolioTargetBoundary.test.tsx
  - frontend/src/components/StockSection.test.tsx
  - frontend/src/components/StockTradeReceipt.test.tsx
  - frontend/src/hooks/portfolioCrypto.test.tsx
  - frontend/src/hooks/portfolioHistory.test.tsx
  - frontend/src/hooks/portfolioStock.test.tsx
  - frontend/src/hooks/portfolioValuation.test.tsx
  - frontend/src/hooks/useAuthMutations.test.tsx
  - frontend/src/hooks/useEventHistory.test.tsx
  - frontend/src/hooks/useHistory.test.tsx
  - frontend/src/hooks/usePortfolio.test.tsx
  - frontend/src/hooks/usePortfolioTarget.test.tsx
  - frontend/src/hooks/useStockTrade.test.tsx
  - frontend/src/hooks/useTrade.test.tsx
  - frontend/src/pages/AccountPage.tsx
  - frontend/src/pages/HistoryPage.test.tsx
  - frontend/src/pages/HistoryPage.tsx
  - frontend/src/pages/PortfolioPage.test.tsx
  - frontend/src/pages/PortfolioPage.tsx
  - frontend/src/pages/SignInPage.test.tsx
  - frontend/src/pages/StockTradePage.test.tsx
  - frontend/src/pages/TradePage.test.tsx
  - frontend/src/test/portfolioFixtures.ts
  - frontend/src/test/portfolioTargetFixture.ts
  - frontend/src/test/stockTradeFixtures.ts
files_partially_reviewed:
  - deploy/tests/fixtures/portfolio-recovery-0017.json
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 12: Remaining frontend and operations code review

## Summary

Read all 63 executable/source/test files listed above at standard depth, including the actual Account, Portfolio and History pages, browser fixtures, retained deployment control, restore verifier, and CI contracts. This report does not claim complete coverage of the requested 64 files: the 283,436-byte single-line generated recovery catalogue received structural review of every top-level section, financial/table/identity projections and function metadata, but not full reading of every embedded SQL definition and ACL row. Its remaining content requires review before aggregate coverage is complete.

Review was offline and read-only. No tests, Docker processes, providers, production operations, source edits or commits were performed. Prior successful automated runs were context only. The separately reported backend CR-01 is outside this finding and is not duplicated.

## Narrative Findings (AI reviewer)

### CR-02 — BLOCKER: Mandatory cold recovery relies on an unavailable workstation image

**File:** `deploy/tests/portfolio-smoke.py:52`  
**Related:** `deploy/tests/portfolio-smoke.py:58`, `deploy/tests/portfolio-smoke.py:71`, `.github/workflows/ci.yml:283`, `.github/workflows/ci.yml:315`, `deploy/tests/run-portfolio-validation.py:150`

**Issue:** The mandatory current0017 cold stage directly runs the hardcoded local Docker image ID `sha256:e5c153f11416842a3cbd7f34c1fe9c7d3f4dec35df8478fd22fbf023d1737aec`, then builds a smoke image FROM that ID. Nothing in this ops job or either preceding serial recovery stage builds, pulls or loads that content ID. The ops CI job builds only the current `test-builder` target; the runtime target built by the image job belongs to a separate runner. Preceding retained builds use independently qualified historical source/image bindings, not this workstation runtime.

**Trigger and consequence:** On a clean GitHub runner, the required recovery command reaches current0017-cold and fails at the first `docker run` because the local-only ID is absent. Docker cannot obtain this local content ID as a registry reference. Local success with a warm workstation cache therefore does not establish portability of the mandatory CI gate.

There is also a provenance mismatch with the intended current-runtime proof: checking installed Python versions and copying current app/Alembic files onto an old cached runtime does not prove recovery using the current declared runtime image. The subsequent source label and binding describe the overlay image without independently establishing the cached base's relationship to the declared Dockerfile.

**Fix:** Build the current declared Dockerfile `runtime` target from the exact frozen, authenticated source context (or pass an explicitly built, authenticated immutable runtime binding into this stage). Record and verify its immutable image/config/layer/source identity before each execution. Use that identity for both seeding and cold restore/read checks, with no fallback to arbitrary local cache images. Preserve all same-archive, restricted TLS, dependency, schema and money assertions. Add a command/provenance regression proving acquisition precedes invocation, and rerun current0017 cold recovery with an independently obtained declared runtime on an otherwise clean image namespace.

## Coverage notes

Reviewed behavior includes explicit owner/root/session partitioning, stale response cancellation, hidden original unknown attempts, same-key receipt recovery, renewed confirmation after repricing, original-reference History state, qualified retained image identities, independent recovery money oracles, protected marker/ACL restoration, exact legacy deployment control and unchanged strict CI security/coverage gates. No additional concrete defect was established in those reviewed paths.

Remaining standard-depth coverage: complete embedded definitions and catalogue rows in `deploy/tests/fixtures/portfolio-recovery-0017.json`. Its zero-row data projections are catalogue fixtures, not claimed populated financial proof; the separate execution fixture supplies actual retained money expectations.

