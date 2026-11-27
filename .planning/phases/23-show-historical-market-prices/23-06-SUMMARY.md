---
phase: 23-show-historical-market-prices
plan: "06"
subsystem: markets-ui
tags: [react, tradingview, coin-metrics, charts, csp, accessibility]
requires:
  - phase: 23-04
    provides: "Independent history, quote, and trade behavior with browser regression coverage"
provides:
  - "Hosted, attributed stock charts bound to exact selected NYSE and Nasdaq listings"
  - "Native Coin Metrics charts with UTC interval and license attribution"
affects: [23-07]
tech-stack:
  added: []
  patterns: [hosted-frame, native-crypto-chart]
key-files:
  created:
    - frontend/src/components/StockHistoryChart.tsx
    - frontend/src/components/StockHistoryChart.test.tsx
  modified:
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/components/MarketHistoryChart.tsx
    - frontend/src/api/marketHistory.ts
    - frontend/src/api/marketHistory.test.ts
    - frontend/e2e/markets.spec.ts
    - frontend/e2e/stock-catalog.spec.ts
    - frontend/e2e/market-history-fixtures.ts
    - frontend/playwright.config.ts
    - deploy/nginx/snippets/birja-security-headers.conf
key-decisions:
  - "The stock chart uses TradingView's delayed, branded Symbol Overview widget in an origin-restricted iframe."
  - "The browser requests historical crypto prices through Birja's authenticated API and shows Coin Metrics attribution and its applicable license."
requirements-addressed: [CHART-01, CHART-02, CHART-03, CHART-04]
requirements-completed: []
completed: 2026-11-27
---

# Phase 23 Plan 06 Summary

Markets shows a TradingView chart for the selected stock and a native Coin Metrics chart for crypto. The current quote, reopening countdown, and trade action remain available independently of the history panel.

## Implementation

- Featured and catalog stocks bind the frame to the selected exchange and ticker. The panel defaults to 1W and offers 1D and 1M with keyboard-accessible controls. It labels the prices as delayed and links out to the same instrument on TradingView if the chart fails to load.
- The app opens the [official TradingView widget](https://www.tradingview.com/widget-docs/widgets/charts/symbol-overview/) in a sandboxed frame. The production `frame-src` permits `https://www.tradingview-widget.com` only. The browser sends the public instrument selector and range to the frame without the Birja referrer. The widget supplies its branding and history data inside the frame.
- The crypto panel decodes the Coin Metrics series at five-minute, hourly, and daily intervals for 1D, 1W, and 1M. Its caption links to the source and license and identifies daily closes and UTC. Crypto retains its accessible price table. Stock history and historical percent changes are displayed by the provider widget.

## Verification

- All 1,444 Vitest tests passed across 67 files. Line coverage was 96.62% and branch coverage was 92.29%.
- ESLint, TypeScript, scoped Prettier checks, and the production frontend build passed.
- Four Chromium scenarios passed with the isolated application and PostgreSQL fixture. They cover holiday reopening and the last verified price, AAPL ranges and fallback with the current ask, BTC ranges with the trade link, and catalog symbol binding and preview with the current ask. The committed browser tests use local widget fixtures or suppress the widget request.
- Separate headless Chromium checks rendered hosted NASDAQ:AAPL 1D and 1W charts and a NYSE:ORCL 1M chart under the proposed parent frame policy. The frame displayed TradingView branding on desktop and mobile.

## Deviations from the plan

TradingView loaded the widget frame with a seven-day range but left the chart spinning. Birja's 1W button now selects the verified five-trading-day view and labels it accordingly.

## Activation

The integrated provider and production verification are recorded under Plan 23-07.

## Self-Check: PASSED
