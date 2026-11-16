---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "24"
subsystem: ui
tags: [portfolio, trading, receipts, recovery, authorization, accessibility]
requires:
  - phase: 12-21
    provides: target-first trade hooks and immutable original-attempt recovery
  - phase: 12-23
    provides: verified Outlet target context and safe financial-route boundary
provides:
  - Explicit crypto/stock ticket, preview and original-receipt portfolio context
  - Owned crypto cash projection and unchanged original-attempt retries
  - Scoped receipt destinations and unavailable-target financial suppression
  - Privacy-safe unresolved-order notice for the original owner/root/session only
affects: [12-25, 12-26, 12-27, 12-28]
tech-stack:
  added: []
  patterns: [captured display context, original-root receipt links, unresolved boolean notice]
key-files:
  created: []
  modified:
    - frontend/src/pages/TradePage.tsx
    - frontend/src/pages/TradePage.test.tsx
    - frontend/src/pages/StockTradePage.tsx
    - frontend/src/pages/StockTradePage.test.tsx
    - frontend/src/components/StockTradeReceipt.tsx
    - frontend/src/components/StockTradeReceipt.test.tsx
    - frontend/src/hooks/useTrade.ts
    - frontend/src/components/PortfolioTargetBoundary.tsx
    - frontend/src/components/PortfolioTargetBoundary.test.tsx
key-decisions:
  - Financial pages consume verified Outlet targets; crypto cash comes from usePortfolio(target), never identity
  - Unknown crypto recovery repeats frozen order, expected mid and key even after quote refresh and cannot be edited/reset
  - Render captured portfolio display context and validate original receipt root before publication or focus
  - Unavailable-target notice reads only an unresolved boolean in the current owner/root/session cache, without financial access
requirements-completed: []
requirements-addressed: [PCTX-01, PFIN-03]
duration: 21 min
completed: 2026-11-16
---

# Phase 12 Plan 24: Trade Surfaces and Original-Target Receipts

**Verified portfolio context now follows crypto and stock tickets through confirmation, original receipt and safe recovery without borrowing identity cash or another strategy's result.**

## Performance

- Started: 2026-11-16T15:27Z
- Final focused verification: 2026-11-16T15:48Z
- Tasks: 2/2
- Files modified: 9
- Packages, backend authority, providers and production resources changed: none

## Accomplishments

- Both pages consume useOutletContext<PortfolioTarget>() and pass that target
  to financial hooks. Root/owner/session/symbol page lifetimes cannot relabel an
  earlier fill or carry an old draft into a sibling ticket. Crypto cash comes
  from the selected portfolio's validated statement; Me has no cash fallback.
- PortfolioContext uses the approved neutral, escaped full-name text on the
  page/ticket and preview/receipt regions. Crypto heading/context precedes its
  financial card grid. Long60-character names retain wrapping styles without
  ellipsis, selector, added badge or invented identity values.
- Crypto unknown outcomes freeze edits and expose Check order result. Recovery
  repeats attempt.order, expected_mid and idempotency_key rather than current
  inputs or a refreshed quote. Invalid repricing responses remain unknown;
  valid repricing still requires renewed confirmation and a new key.
- Stock bid/ask, whole-share shortcuts, old/new repricing, second confirmation,
  source timestamps, IEX disclosure, draft-only closure and recorded balances
  retain their existing behavior. Matching original active receipts recover
  after market closure; unavailable portfolios never expose receipts or retry.
- Receipt Portfolio links identify the actual original portfolio. Trade again
  starts a fresh same-root draft; successful receipts focus their headings
  once per receipt rather than stealing focus on metadata refresh.
- A root lost during confirmation suppresses all financial children. The fixed
  unresolved-order sentence is driven only by an existing boolean for the
  current authenticated owner/session and original route root. It exposes no
  order values, quantities or original owner/name, performs no financial fetch,
  and disappears after logout/owner changes. Guessed sibling, foreign-owner and
  previous-session cache entries cannot produce it.

## Task Commits

| Task | Commit | Result |
|---|---|---|
| 12-24-01 | d0bd19a | Scoped crypto cash/context and frozen original-attempt recovery |
| 12-24-02 | 20adfed | Scoped stock ticket/receipt, safe unavailable-order notice and final integration |

## Verification

- Assigned crypto page gate:29 cases pass, including exact existing economics,
  definitive refusal edits, lost-result frozen retry, changed quote/original
  mid, unavailable-root suppression, long escaped names, receipt focus/links
  and late original fill after sibling navigation.
- Assigned stock page gate:18 cases pass, including explicit confirmation,
  zero-fee disclosure, closure drafts, old/new repricing, original retry after
  market closure, long names, root loss during fill, conflict privacy, scoped
  receipt links and no sibling receipt relabeling.
- Boundary:19 cases pass, including exact unresolved notice, no financial
  disclosure, owner switch/logout clearing and foreign/sibling/prior-session
  exclusion. Direct receipt:2 cases pass, including mismatched/unavailable root
  suppression and unchanged recorded fill facts.
- Final seven-file page/boundary/receipt/trade-hook/App regression passes128
  cases on final source. Fetch is intercepted at the HTTP boundary; these are
  real page/hook/client interactions, not provider or production requests.
- All nine changed files pass ESLint, Prettier and git diff checks.
- Full frontend typecheck still reports50 errors across14 downstream page/
  retained-fixture files; none are in this plan's changed files. PortfolioPage
  and HistoryPage target consumers belong25; remaining legacy fixtures belong27.
  Whole frontend typing/build/coverage success is not claimed.
- Unit tests prove semantics, text escaping, wrapping styles and focus, not
  actual layout at320px or native200% browser zoom. Browser/reflow/keyboard
  qualification and owner acceptance remain26–28.

## Deviations from Plan

1. **[Rule1 — definitive crypto refusals]** useTrade's earlier terminal set
   omitted the backend's below_minimum, insufficient_quantity, order_too_large
   and stale_price codes. Without alignment a definitively refused order became
   an uneditable unknown result. Added only those existing codes; unknown
   transport/malformed receipt/reprice responses stay frozen. Existing page
   refusal tests and hook regression verify the distinction. Commitd0bd19a.
2. **[Rule2 — unavailable original-order notice]** Added the exact UI-SPEC
   sentence to PortfolioTargetBoundary with a privacy-safe scoped cache boolean
   and dedicated refusal/logout/owner tests. Financial children stay absent;
   no new query, fallback root, execution authority or broad store was added.
   Commit20adfed.
3. **[Rule3 — direct receipt consumer]** Updated the existing direct receipt
   test for its required verified target and captured name; added a wrong-root/
   unavailable negative. Commit20adfed.

## Issues Encountered

- Retained test responses initially echoed input100 for orders changed to20/50;
  strict request/response matching correctly refused them. Fixtures now echo
  their actual request without relaxing parsers.
- A long-name test initially exceeded60 characters and was correctly refused;
  its fixture now exercises exactly60 escaped characters.
- Stock context's nested market quote does not carry a portfolio field; an
  adapted fixture initially added one and was correctly rejected. Only actual
  outer context and trade quote/receipt identities are scoped.
- Synthetic unknown-cache tests initially used immediate collection instead of
  the actual trade-state Infinity lifetime. Their fixture lifetime now matches
  production hook behavior; privacy/session filters remain unchanged.
- Final lint rejected render-time ref reads for captured display names. Event-
  captured state replaces those refs without lint suppression or retargeting.

## Known Stubs / External Setup

None. No management feature, mock financial source, package or external setup
was introduced into the product. Tests use synthetic HTTP fixtures only.

## Handoff

- Plan25 must consume the same verified Outlet target in portfolio/History
  pages and preserve target-bound holding/original-reference navigation.
- Plans26/27 still own full frontend fixture integration, exact critical
  coverage, real browser multi-width/reflow/keyboard and security gates.
- Plan28 still requires distinct owner UI and genuine native200% outcomes.
- All whole requirements remain unchecked pending full phase verification;
  six Phase7 live outcomes and all stock activation guards remain unchanged.

## Self-Check: PASSED

Both task commits exist; all changed files exist. Assigned page gates and final
128-case regression pass with changed-file lint/format/type checks. Remaining
downstream typing and actual browser/native-zoom gates are recorded explicitly.
