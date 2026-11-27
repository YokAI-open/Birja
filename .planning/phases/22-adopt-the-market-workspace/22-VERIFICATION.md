---
phase: 22-adopt-the-market-workspace
verified: 2026-11-26T10:23:17Z
status: passed
score: "4/4 must-haves verified"
overrides_applied: 0
runtime: 519199143fb8e1ae6793825569c794dab428c96a
browser_assertions: 23b1e5bfc1c5a51a565448e95c79621c26b1c19e
---

# Phase 22 — Markets workspace verification

The approved Markets layout supports browsing and selecting stocks and crypto through the existing market and trade APIs. All three roadmap criteria and all four Phase 22 requirements passed. This is verification of the app in the isolated stack with deterministic market fixtures.

## Observable truths

| Requirement | Result | Evidence |
|---|---|---|
| WS-01 | Verified | The shared header keeps the Birja branding, three navigation links and 44px account control. Chromium measured one row and no page overflow at 320, 390, 640, 768 and 1440px. Enlarged-text Portfolio and History checks passed after the wrap fix. The app renders one labeled trading-portfolio chooser, and keyboard selection moves focus to the mobile detail and back to the result. |
| WS-02 | Verified | The signed-in app starts on US stocks and shows the original 20 on entry and after clearing the query. The eligible catalog resolves names, ticker, aliases and classes. Search failure retains curated discovery. Crypto has its own list, price feed and executed buy/sell scenario. |
| WS-03 | Verified | The selected instrument has a quote and appropriate action in a panel alongside the desktop list and below it on mobile. The catalog requests a quote only for the selected ID and version. Changing the portfolio in place preserves the query and instrument, changes the scoped route and leaves the quote request count unchanged. Chromium followed the route to the selected portfolio and instrument. Component tests verify revoked or pending authority keeps the quote visible and suspends trading. |
| WS-04 | Verified | Ordinary closure, holiday and early-close cases preserve the permitted price and exact timestamp and count down to the server-provided opening. The SQL-backed catalog case works with an empty cache and hides expired marks. Closed stock views expose details and refuse preview, while independent crypto trading remains available. |

## Source and wiring

- [App shell and portfolio routing](../../../frontend/src/App.tsx) mounts Markets for the signed-in identity and validates the selected portfolio through [usePortfolioTarget](../../../frontend/src/hooks/usePortfolioTarget.ts). The [portfolio switcher](../../../frontend/src/components/PortfolioSwitcher.tsx) reads the owned list and changes the selection in place. Stock, catalog and crypto links use the existing portfolio route boundary.
- [Markets](../../../frontend/src/pages/MarketsPage.tsx) consumes the existing curated stock and crypto queries plus authenticated [catalog search and selected-quote hooks](../../../frontend/src/hooks/useStockCatalog.ts). Query results supply rows, prices and timestamps. The [CSS](../../../frontend/src/pages/markets.css) sets the 42:58 wide layout, mobile stacking and visible focus. Focus recovery uses the same breakpoint and preserves the result or search destination.
- The selected curated or catalog session supplies `next_open_at` to [MarketOpening](../../../frontend/src/components/MarketOpening.tsx). The component renders the exact datetime, a visible relative countdown and the local time for assistive technology. Session, permission, mark validity and order authority remain governed by the existing stock services and ticket routes.
- The [isolated runner](../../../deploy/tests/run-stock-browser.py) executes the [Markets](../../../frontend/e2e/markets.spec.ts) and [catalog](../../../frontend/e2e/stock-catalog.spec.ts) specs as part of all-suite mode. The verifier traced these links directly through the alias imports, route and rendered browser behavior. All eight declared artifacts exist and are substantive. The integration evidence confirms the key links that the SDK path-string matcher could not resolve.

## Executed evidence

| Check | Result |
|---|---|
| Full isolated Chromium suite | 105 passed across 14 specs, zero failures and one optional deployed-site CSP skip. No owned containers, networks or volumes remained. |
| Full frontend Vitest suite | 1,376 passed in 61 files. |
| Frontend lint, typecheck, scoped format and production build | Passed, with a build bundle-size advisory. |
| Source binding | The runtime and test commit resolve, with only two E2E specs changing between them. Their diff independently hashes to `e4b791d7c37a31df0ab70f841fafdb02011c37f3549036f25f731d7acc86f392`. |
| Rendered evidence | Inspected 1440px open and holiday-closed desktop captures and a 390px selected-detail capture. The images show the expected layout, calendar state and keyboard focus. Hashes match the receipt. |

[Raw browser log](/tmp/birja-phase09-browser-bsctkx__/browser-all.log) · [Raw Vitest log](/tmp/birja-phase22-vitest-final.log) · [Source-bound browser receipt and screenshots](22-BROWSER-RECEIPT.md) · [Executed validation map](22-VALIDATION.md) · [Code review](22-REVIEW.md)

The browser evidence covers Chromium geometry, keyboard interaction and automated reflow. The captures use deterministic fixtures. There is no separate human checkpoint in the approved phase plan. Historical charts and period changes remain Phase 23 scope.
