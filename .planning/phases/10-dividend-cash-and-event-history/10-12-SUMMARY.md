---
phase: 10-dividend-cash-and-event-history
plan: "12"
subsystem: frontend-api
tags: [history, exact-decimal, dividends, lineage, wire-validation]
requires:
  - phase: 10-planning
    provides: C05/C06 mixed-event and privacy contracts
provides:
  - Exported strict EventHistoryItem/EventHistoryPage union and read-only fetchEventHistory
  - Whole-page rejection of malformed cash, dates, IDs, cursors and original lineage
  - Exact nullable uncertainty and immutable offpage original details
affects: [10-10, 10-13, 10-14, 10-15, 10-16]
tech-stack:
  added: []
  patterns: [discriminated-wire-union, bounded-bigint-validation, owner-bound-linked-summary]
key-files:
  created:
    - frontend/src/api/eventHistory.ts
    - frontend/src/api/eventHistory.test.ts
  modified: []
key-decisions:
  - Public identities and references are kind:canonical-source-bigint; original references include a full bounded immutable dividend summary.
  - Uncertain current terms are explicit null with null desired/proposed amounts and zero applied cash, never verified zeros.
  - Exact wire validation uses bounded BigInt arithmetic; no Number or parseFloat conversion of money, rates or IDs.
requirements-completed: []
requirements-supported: [HIST-03, DIV-03, DIV-05]
duration: approximately12min
completed: 2026-11-12
---

# Phase 10 Plan 12: Strict Mixed History Client Summary

**A strict tagged History parser preserves exact financial strings, validates immutable dividend lineage and refuses entire inconsistent pages before read-only display.**

## Accomplishments

- Exported EventTrade, DividendTerms, EventDividend, EventSplit,
  EventDividendCorrection, EventHistoryItem and EventHistoryPage. Existing
  `api/history.ts` and legacy `/api/v1/trades` remain untouched.
- All events require bounded saved identity, canonical public kind:source-ID,
  UTC recorded timestamp and exact signed cent cash change. Source IDs retain
  full PostgreSQL bigint precision and distinct entity kinds may reuse IDs.
- Trades retain original side, quantity, price, fee and fill timestamp. Crypto
  admits fractional quantities; stocks require whole quantities, zero fee and
  retained Alpaca/IEX source and quote timestamp. A projection from the existing
  immutable stock receipt fixture passes without current quote reconstruction.
- Dividend targets validate exact eight-place rates, whole eligible quantities,
  original reference, optional source dates, payable date, cutoff and actual
  credit timestamp. Bounded integer HALF_EVEN checks reject cash mismatches;
  exact .005/.015/.025 ties and a verified zero remain distinct from unknown.
- Forward splits conserve saved basis and verify ratio against before/after
  shares, with no cash effect. Corrections retain target, cumulative actually
  applied amount, proposed/applied deltas and an embedded immutable original
  even outside loaded pages. Applied, held uncertain, held unaffordable and
  verified no-change enforce their fixed outcome/reason and cash semantics.
  Broken references, future originals, invented uncertain targets and nonzero
  held cash fail the whole page. Display rights/ownership are still enforced
  server-side; the parser does not claim to authenticate an owner from amounts.
- `fetchEventHistory({cursor,limit}, signal)` uses existing apiFetch only,
  authenticated refresh/401 behavior, no-store and cancellation. Requests and
  returned pages are bounded. Cursorv2 JSON/base64url, exact fields, integer
  ranks, UTC microseconds and canonical bigint are validated; duplicate JSON
  keys/noncanonical bytes are rejected. No client resort or cash mutation.

## Exact Wire Details Frozen for Consumers

C05 is normative; these minimal field names resolve its semantic descriptions:

- Every ID is the public `kind:source_id`; `payment_reference` is
  `dividend:<payment_id>` and `decision_reference` equals the correction ID.
- Trade source fields are `source`, `feed`, `quote_at`, all explicit null for
  unavailable crypto attribution; stock requires `alpaca`, `iex`, UTC instant.
- DividendTerms contains `eligible_quantity`, `rate`, `cutoff`, nullable
  `ex_date`/`record_date`, and required `payable_date`. Dividend uses those flat
  fields plus `payment_reference`, `credited_amount`, `credited_at`.
- Split adds `ratio_new`, `ratio_old`, `quantity_before`, `quantity_after`,
  `cost_basis_before`, `cost_basis_after`, `effective_at`.
- Correction adds C05 amount/outcome/reason fields, `terms:DividendTerms|null`
  and `original:EventDividend` (full bounded owner-filtered original summary).
  Unknown terms require null terms/target/proposal; no fabricated entitlement.

Parent received this exact interface before later backend/UI consumers; no
extra route or provider contract was introduced. Implementations must not infer
ownership from public identity alone; every backend projection remains scoped.

## Task Commits and Actual TDD Evidence

1. Task1 RED `9b09403`: exported types/guard existed; actual tests had six
   behavioral failures and26passes, not import errors. Initial32tests1.67s.
2. Task1 GREEN `f9c214f`: strict parser and isolated transport;32tests passed
   1.31s, scoped ESLint and TypeScript passed after correcting a control-regex
   lint issue without disabling its rule.
3. Task2 RED `35786f9`: explicit oversized requested-page test failed against
   actual existing transport;32passed/1failed1.37s.
4. Task2 GREEN `3343813`: requested-limit guard and expanded meaningful boundary
   tests; final62tests passed1.84s. Every parser statement, branch, function and
   line covered (95statements/230branches/22functions/88lines, all100%).

Verification used existing locked frontend tools, no installation:

```
npm run test -- src/api/eventHistory.test.ts --coverage --coverage.include=src/api/eventHistory.ts
./node_modules/.bin/eslint src/api/eventHistory.ts src/api/eventHistory.test.ts
npm run typecheck
./node_modules/.bin/prettier --check src/api/eventHistory.ts src/api/eventHistory.test.ts
git diff --check
```

Final scoped static/type/format/whitespace checks passed8.84s. One interim
TypeScript check correctly rejected indexing the zero-argument mock's inferred
tuple; it was replaced with the proper observable `toHaveBeenCalledWith`
assertion and the complete static gate passed. Full frontend integration,
backend, actual financial browser, recovery/TLS/image gates remain parent's
later wave/phase checks; no browser financial success is claimed from unit
wire fixtures. No new version-specific library API or documentation dependency
was needed; transport and validation follow the existing inspected analogues.

## Deviations and Boundary Checks

- **[Rule2 — Missing critical validation]** Requested page size is also enforced
  on the response, preventing a response from bypassing the caller's bound.
  Behavioral RED/GREEN above proves it.
- Public contract's semantic fields required minimal exact naming; exported
  types are documented above for backend/hook/UI consumers, with no new feature.
- No authentication gate, package/image/lockfile change, provider/secret access,
  production/B2/timer/installed-tool action, publication or deployment occurred.
- Parent owns canonical STATE/ROADMAP/REQUIREMENTS and final review/gates; none
  was staged by this executor. Other workers' changes and `.claude/` preserved.

## Threat Results and Stub Scan

- T-10-12-01: exact discriminator, range, date, amount/outcome and lineage
  rejection tested; no client authority or financial mutation introduced.
- T-10-12-02: full retained original in each correction, exact references and
  original chronology checked. Server-side owner filtering remains required
  in10-10; wire validation cannot replace authentication or that privacy proof.
- T-10-12-03: maximum100items,512cursor characters, bounded text/IDs/NUMERIC,
  one bounded read request and abort propagation; no page scan or retry loop.
- T-10-12-SC: no dependency additions, installs or lock changes.
- No unplanned endpoint, auth bypass, file access or schema trust boundary.
- No temporary parser stub/TODO remains. Explicit nullable terms/source dates
  represent planned unavailable facts, not unimplemented success paths.

## Self-Check: PASSED

Both new source/test files exist and all four recorded task commits exist.
No task commit deletes tracked files. Final62focused tests and scoped static
checks passed; only the two owned API files and this summary are committed.
Requirements are supported here, not marked wholly complete ahead of the
backend projection, full gates and actual owner acceptance.
