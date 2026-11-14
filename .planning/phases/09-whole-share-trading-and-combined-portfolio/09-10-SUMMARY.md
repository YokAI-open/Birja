---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "10"
subsystem: stock-client
requires: [09-08]
provides: [exact stock contracts, protected memory-only attempt lifecycle]
affects: [09-11, 09-12, 09-13, 09-14]
tech-stack:
  added: []
key-files:
  created: [frontend/src/api/stockTrades.ts, frontend/src/hooks/useStockTrade.ts]
  modified: [frontend/src/api/stocks.ts, frontend/src/hooks/useStocks.ts]
requirements-completed: []
requirements-supported: [STKTR-01, STKTR-03, STKTR-05, MKT-02]
completed: 2026-11-12
---

# Plan09-10: Exact stock client and protected attempts

Task1 REDbbf1726/cd16fce and GREENebcc939 implement exact bounded contracts,
BigInt financial relationship validation, strict original receipt timestamps,
source/status authority and conservative full transport RTT including refresh
and body parsing. Malformed execution success remains UNKNOWN. Explicit errors
never publish keys, raw errors or private response contents. Discovery accepts
independent normal status only when all other server evidence permits it.

Task2 REDa12cb13 and GREENc24b54e expire independent status in discovery cache.
Controller RED1d6484c, GREENd16f761 and review correction11bad97 implement
owner-scoped memory-only draft/preview/submitting/unknown/filled states. Explicit
result checks reuse the frozen original body and key after closure; no automatic
execution retries, optimistic money or new-key abandonment. Pending/unknown
freezes editing. Success preserves original receipt and invalidates shared
queries. Repricing requires another explicit confirmation. Timers, focus and
cache events purge forbidden previews immediately while retaining typed quantity.

Full RTT, monotonic authority/epochs/status continuity, query ownership and auth
lifecycle prevent late responses from restoring earlier data. Same-email logout
and login are separate lifecycles. Unknown attempts survive component unmount
within the authenticated QueryClient; no browser persistent storage is used.
Review RED4332c45 exposed a stuck loading state after context replacement and
an old executable preview surviving changed provider identity.11bad97 fixes both;
a changed mapping needs strictly newer safety/time evidence before positivity.

## Verification

Final four focused files: **247 passed in5.24s**; TypeScript and scoped ESLint/
Prettier pass. Includes81 stock API,96 discovery API,50 discovery lifecycle and
20 attempt lifecycle tests. Actual backend execution is proven in06–08; these
frontend fixtures prove client behavior only. Full critical coverage, actual
browser/UI and security/recovery gates remain13–14, owner UI acceptance15.
Separate inline review is09-10-REVIEW.md; independence is not claimed.
No provider, production, backup, installed-tool or publication action occurred.
