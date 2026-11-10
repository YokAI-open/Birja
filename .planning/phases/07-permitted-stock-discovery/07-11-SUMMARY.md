---
phase: 07-permitted-stock-discovery
plan: "11"
subsystem: ui
tags: [stocks, react, tanstack-query, admission, decimal, attribution]
requires:
  - phase: 07-10
    provides: Authenticated twenty-item stock discovery response and authoritative deadlines
provides:
  - Strict stock payload validation with exact decimal-string comparison
  - Auth-scoped stock queries with monotonic full-transport deadline accounting
  - Visible reusable IEX and simulated-execution attribution
affects: [07-12, 07-13, 07-14]
tech-stack:
  added: []
  patterns: [Conservative server-time interval, Query-owned cancellation, React-escaped attribution]
key-files:
  created:
    - frontend/src/api/stocks.ts
    - frontend/src/api/stocks.test.ts
    - frontend/src/hooks/useStocks.ts
    - frontend/src/hooks/useStocks.test.tsx
    - frontend/src/components/StockAttribution.tsx
    - frontend/src/components/StockAttribution.test.tsx
  modified: []
key-decisions:
  - "The complete apiFetch duration includes shared authentication refresh/retry and validation; no clock budget restarts on receipt."
  - "Display projection preserves original source times and original ages; cache purging never compounds RTT into already projected ages."
  - "Existing private-query cancellation/removal handles logout; stock queries additionally bind their identity and query object and cancel superseded generations."
requirements-completed: []
requirements-addressed: [STOCK-01, STOCK-02, STOCK-03, DATA-01]
duration: 10min
completed: 2026-11-10
---

# Phase 7 Plan 11: Stock client validation and attribution Summary

**Validated twenty-stock client data now uses exact decimal strings, session-isolated queries and conservative monotonic permission/session deadlines, with visible reusable IEX disclosure.**

## Performance

- Approximately 10 minutes, 2026-11-10T19:08Z–19:18Z; two tasks, six owned source/test files.
- Local implementation is complete. Whole-phase requirements and permitted live discovery remain pending.

## Accomplishments

- `fetchStocks(signal)` uses the existing authenticated `apiFetch` transport and validates the actual Plan10 response. It requires exactly twenty unique safe positive identities and unique ticker symbols, known listing/currency/feed/reason/status enums, timezone-aware valid civil timestamps, bounded positive decimal strings and bid ≤ mid ≤ ask. Money comparison uses fixed-scale BigInt units rather than Number arithmetic. Malformed arrays fail atomically.
- Transport timing starts before `apiFetch` and ends after response validation, including shared authentication refresh/retry and JSON work. Full nonnegative RTT is retained with its original monotonic receipt anchor.
- `useStocks()` returns TanStack query state with a projected `StocksResponse` in `data`. Its key is `["stocks", identity.email]`; absent identity disables reads. Networking uses TanStack Query, AbortSignal, 30-second reads and focus refetch, with no useEffect networking. The one-second effect is a display/cache-expiry timer only.
- Admission and calendar deadlines use server_now plus monotonic elapsed and full RTT. Open is advertised only when the entire conservative interval lies within supplied reviewed session bounds. Source age includes full RTT and subsequent elapsed once. Local projection never opens a server-closed/unknown session or enables execution. Slow responses are already classified/redacted before first successful display.
- Permitted historical quotes retain original source/collection timestamps; stale or closed classifications remain independent from execution. Background errors retain data only within permission/review bounds. Initial expired data is purged before caching; the display timer removes expired numbers and timestamps from the private cache without initiating network work.
- Logout/unmount cancellation, identity/query-object binding, generation comparison and cache-event cancellation reject late results. Installed denial/newer generation aborts old requests immediately. Final 401 hides stock data, clears stock cache and invalidates account identity. Crypto cache is unaffected by stock failures/revocation.
- `StockAttribution` supports listing, preview and valuation contexts, always showing exact UI-SPEC “IEX prices” and the full single-exchange/virtual-money/simulated-execution explanation. Optional `required_text` is additive escaped React text. Typography and semantic tokens follow the existing design system; no package or logo was added.

## Task Commits

1. **07-11-01 RED** — `41c370f`: Specify strict stock client safety.
2. **07-11-01 GREEN** — `892f019`: Guard stock client authority and timing.
3. **07-11-02 RED** — `698b5f5`: Require visible IEX simulation disclosure.
4. **07-11-02 GREEN** — `448c8f5`: Show reusable IEX source attribution.

Both RED gates used intentionally inert callable/components and observed behavioral assertion failures rather than missing-import failures. Task1 initially observed nine failures; Task2 observed all four disclosure assertions fail. Supplemental adverse tests were added before the corresponding GREEN commit.

## Verification

- Exact Task1 slice `npm run test -- src/api/stocks.test.ts src/hooks/useStocks.test.tsx` — **34 passed**, final run 3.33 seconds including environment/setup. Cases include malformed payloads, exact eight-decimal price ordering, actual shared refresh/retry timing, permission expiry, source age120, close and before-open uncertainty, browser clock skew, missing quotes, historical time retention, background failure, cache expiry, newer-generation/revocation cancellation, logout/unmount, auth identity switching and final401.
- Exact Task2 slice `npm run test -- src/components/StockAttribution.test.tsx` — **4 passed**, 1.56 seconds including environment/setup. All three contexts require visible disclosure; malicious supplemental markup remains text with no image/script element.
- `npm run typecheck` passes. Scoped ESLint on all six files and scoped Prettier check pass; `git diff --check` passes. No tracked file deletion, dependency change or generated task file remains.
- Targeted UI skill searches found readable-font/contrast guidance and React derived-state guidance. The explicit approved UI-SPEC typography and MASTER tokens were preserved. Official TanStack Query cancellation/QueryCache documentation was consulted; no Context7 tool or ctx7 CLI was available.

## Deviations from Plan

None. No backend contract, dependency, public route or future stock-trading/portfolio screen was changed. Existing auth private-query cleanup is reused without broadening its behavior.

## Known Stubs

None in the completed local client boundary. Nullable quotes, unknown status and execution-disabled fields are real required Phase7 states. The listing consumer belongs to Plan12; preview/valuation are tested reusable contexts, not claims that future stock screens exist. Fixtures do not establish live provider rights.

## Next Plan Readiness

Ready for Plan12 read-only discovery UI. Import `useStocks` from `hooks/useStocks` and `StockAttribution` from `components/StockAttribution`. Hook `data` is the authoritative projected `StocksResponse`; it already owns a monotonic display tick and all permission/session redaction. Read `admission.state`, per-item `quote_reason`/`session_reason`, nullable quote/session bounds and execution-disabled fields independently. Preserve original event_at/collected_at for last-quote display. Attribution props are `context="listing"` and additive `required_text={data.attribution.required_text}`.

Full phase checks, restricted-TLS consumer proof and provider/live/human acceptance remain Plans13–14. No private environment, production resource/service, B2 storage, provider request/contact, publication or deployment was accessed or changed.

## Self-Check: PASSED

All six declared files exist. All four task commits above exist on the current branch. Exact task slices and scoped static checks passed. No task-generated untracked file remains; unrelated `.claude/` is preserved. Whole-phase requirements intentionally remain pending.
