---
phase: 22
slug: adopt-the-market-workspace
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-26
---

# Phase 22 — Validation strategy

All tests run in the existing Vitest or isolated Playwright infrastructure.
Record commands, code identity, counts and outcomes during execution.
`nyquist_compliant` records planned coverage, not a test result.

| Task | Requirement | Defensive behavior | Feedback |
|---|---|---|---|
| 22-01-01 | WS-01 | Keyboard reachability and working sign-out retry | Vitest `App.test.tsx`, lint, typecheck |
| 22-01-02 | WS-02, WS-03 | Bounded discovery and stale search/selection fencing | Vitest `MarketsPage.test.tsx`, `useStocks.test.tsx` |
| 22-01-03 | WS-02 | Existing browser journeys use explicit asset-class context | Playwright discovery for six named specs and the final owned run |
| 22-02-01 | WS-01, WS-03 | Only a ready explicitly owned target opens scoped trade | Vitest `App.test.tsx`, `PortfolioSwitcher.test.tsx`, `MarketsPage.test.tsx` |
| 22-02-02 | WS-04 | Verified mark lifetime and no timer-based order authority | Vitest `MarketsPage.test.tsx`, `useStocks.test.tsx`, `StockTradePage.test.tsx`, `StockCatalogTradePage.test.tsx` |
| 22-03-01 | WS-01–04 | Mobile/keyboard and exact paths in the installed app | `python3 deploy/tests/run-stock-browser.py --suite all` |
| 22-03-02 | WS-01–04 | Scope and fixture behavior confirmed from source | Frontend lint, typecheck, full Vitest and passing browser receipt check |

Run the focused Vitest selector after each task and phase-relevant frontend
tests at each wave. Use the existing locked Node 24 toolchain. Close the phase
with one full disposable browser run because shared header and default-tab
changes affect multiple existing suites. Browser configuration and test
fixtures remain in their established paths. No separate Wave 0 setup is
needed. Recovery tooling and backend sources stay outside the phase.

## Evidence

Retain measured non-overflow and focus assertions at 320px, 390px, 768px and
1440px, plus 640px reflow as an enlarged-text baseline. Capture desktop open
and closed Markets and the mobile selected detail from the real app. Review
them against the accepted prototype. The automated narrow viewport evidence
does not represent a human's native browser zoom check. Record any separate
human feedback only if received.
