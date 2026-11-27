---
phase: 25-finish-the-trading-flows-and-verify-the-integrated-app
plan: "01"
subsystem: trading
tags: [react, trades, quote, receipt, vitest]
requires:
  - phase: 25-03
    provides: Signed-in navigation and mobile shell
  - phase: 20
    provides: Exact catalog trade routes and server preview, confirm and receipt
provides:
  - Shared trade workspace and one route-owned portfolio chooser
  - Actual cash, positions, quotes and receipts across the three trade routes
affects: [25-05]
tech-stack:
  added: []
  patterns: [Scoped workspace CSS, Existing portfolio and order authority]
key-files:
  created: [frontend/src/pages/tradeWorkspace.css]
  modified: [frontend/src/App.tsx, frontend/src/App.test.tsx, frontend/src/pages/TradePage.tsx, frontend/src/pages/TradePage.test.tsx, frontend/src/pages/StockTradePage.tsx, frontend/src/pages/StockTradePage.test.tsx, frontend/src/pages/StockCatalogTradePage.tsx, frontend/src/pages/StockCatalogTradePage.test.tsx]
key-decisions:
  - Keep executable prices, fees, cash changes and filled quantities tied to the accepted server response
  - Use current order context for stock cash and shares and the scoped portfolio cash when curated context cannot load
  - Preserve exact listing and portfolio identifiers when checking an original catalog order
requirements-completed: [FLOW-01]
duration: 13min
completed: 2026-11-26
---

# Phase 25 Plan 01 — Shared trade workspace

Crypto, curated stock and catalog stock now use the approved ticket and
preview layout with current balances and the existing order lifecycle.

## Delivery

- Trade routes have a single 220px portfolio chooser and an asset heading.
  Cash and holdings are visible for both sides when present in the
  scoped responses. Crypto retains dollar and quantity buys, quantity
  sells and automatic preview.
- Both stock tickets show whole-share controls, bid and ask when
  usable, and server preview. Closed sessions show the next opening
  countdown and last permitted mark when supplied. An original order
  can still be checked after the session closes.
- Repricing keeps explicit confirmation and the existing server
  comparisons. Successful orders focus the receipt with actual
  execution and cash values, the scoped portfolio link and Trade again.
  Catalog stock keeps the exact listing through selection, preview,
  replacement and original-receipt requests.

| Task | Commit | Verification |
|---|---|---|
| 25-01-01 · Crypto and trade chooser | `c758103` | 110 App, crypto ticket, attempt and rename tests passed. |
| 25-01-02 · Curated stock | `8e0cc33` | 69 curated ticket, attempt and receipt tests passed. |
| 25-01-03 · Exact catalog and shared controls | `ed8ebad` | 79 combined ticket and rename tests passed with project TypeScript. The final eight-suite run passed 198 tests. |

Scoped ESLint, Prettier, project TypeScript, whitespace checks and the
production Vite build passed. Vite reported its chunk-size warning.

## Local visual measurements

Chromium rendered the production bundle with intercepted responses for
an owned BTC trade. Every other request origin was blocked. Recorded
coordinates are in CSS pixels.

| Viewport | Chooser x, y and size | Ticket x, y and width | Preview x, y and width |
|---|---|---|---|
| 1440 × 1000 | 40, 127, 220 × 44 | 40, 289.7, 752.6 | 808.6, 289.7, 591.4 |
| 390 × 1000 | 16, 89, 220 × 44 | 16, 233.4, 358 | 16, 637.2, 358 |
| 320 × 1000 | 16, 89, 220 × 44 | 16, 233.4, 288 | 16, 673.2, 288 |

The approved prototype starts the ticket at y289.2 and y232.9 for
1440px and 390px. The live desktop gap is 16px and the prototype gap
is 18px. The live money input is 52px high at all measured widths.
The 320, 390, 740, 741, 1024 and 1440px views had no horizontal
overflow. The ticket stacked before the preview at 740px and appeared
beside it at 741px.

The prototype uses a decorative asset stamp and illustrative buy/sell
figures and controls. The crypto implementation uses the route's asset
heading, its current market price, its amount/quantity interaction and
the actual automatic preview and confirmation. These controls change the
panel heights. Plan 25-05 supplies integrated route and browser evidence.

## Self-Check: PASSED

All three scoped commits and their files exist. The source diff passes
whitespace checks. The signed-in shell, owned trade hooks and server
protocols are covered by the focused tests above.
