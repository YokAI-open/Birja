---
phase: 22
slug: adopt-the-market-workspace
status: executed
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-26
---

# Phase 22 — Validation strategy

All tests run in the existing Vitest or isolated Playwright infrastructure.
Record commands, code identity, counts and outcomes during execution.
`nyquist_compliant` records planned coverage, not a test result.

| Task | Requirement | Defensive behavior | Feedback | Result |
|---|---|---|---|---|
| 22-01-01 | WS-01 | Keyboard reachability and working sign-out retry | Vitest `App.test.tsx`, lint, typecheck | Passed. App tests and Chromium reflow. |
| 22-01-02 | WS-02, WS-03 | Bounded discovery and stale search/selection fencing | Vitest `MarketsPage.test.tsx`, `useStocks.test.tsx` | Passed. Market and stock-hook tests plus Chromium discovery and fallback. |
| 22-01-03 | WS-02 | Existing browser journeys use explicit asset-class context | Playwright discovery for six named specs and the final owned run | Passed. Eight affected specs discovered and exercised in the full run. |
| 22-02-01 | WS-01, WS-03 | Only a ready explicitly owned target opens scoped trade | Vitest `App.test.tsx`, `PortfolioSwitcher.test.tsx`, `MarketsPage.test.tsx` | Passed. Portfolio and route tests plus the selected catalog ticket in Chromium. |
| 22-02-02 | WS-04 | Verified mark lifetime and no timer-based order authority | Vitest `MarketsPage.test.tsx`, `useStocks.test.tsx`, `StockTradePage.test.tsx`, `StockCatalogTradePage.test.tsx` | Passed. Session tests and browser holiday, early-close and closed-ticket coverage. |
| 22-03-01 | WS-01–04 | Mobile/keyboard and exact paths in the installed app | `python3 deploy/tests/run-stock-browser.py --suite all` | Passed. 105 tests with one optional deployed-site CSP skip. |
| 22-03-02 | WS-01–04 | Scope and fixture behavior confirmed from source | Frontend lint, typecheck, full Vitest and passing browser receipt check | Passed. 1,376 Vitest tests, lint, typecheck, scoped format and production build. |

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

[Executed browser receipt](22-BROWSER-RECEIPT.md).
