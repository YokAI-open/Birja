---
phase: 13-create-and-compare-independent-strategies
plan: "08"
subsystem: api
tags: [typescript, portfolios, metadata, unicode, idempotency, valuation]
requires:
  - phase: 13-06
    provides: Actual private creation, metadata and PATCH contracts
  - phase: 13-07
    provides: Exact bounded 19-field overview and shared valuation semantics
provides:
  - Strict browser creation and metadata transport preserving original request identity
  - Shared Unicode display and description validation without browser uniqueness authority
  - Bounded overview identity adaptation through the existing financial parser
affects: [13-09, 13-10, 13-11, 13-12, 13-13, 13-15, 13-17]
tech-stack:
  added: []
  patterns: [immutable transport snapshot, strict identity adaptation, private classified errors]
key-files:
  created:
    - frontend/src/api/portfolioManagement.ts
    - frontend/src/api/portfolioManagement.test.ts
    - frontend/src/api/portfolioOverview.ts
    - frontend/src/api/portfolioOverview.test.ts
  modified:
    - frontend/src/api/portfolios.ts
    - frontend/src/api/portfolio.ts
key-decisions:
  - "Validate exact overview keys before mapping id to the existing portfolio_id financial guard; detail identity/stock validation is retained."
  - "Preserve original raw validated creation strings and UUID in a synchronous transport snapshot across session recovery."
  - "Known service_unavailable codes retain status and Retry-After but remain unknown mutation outcomes."
requirements-completed: [PMGT-02, PMGT-06, PFUND-02, PVIEW-01, PVIEW-02]
duration: 7min
completed: 2026-11-18
---

# Phase 13 Plan 08: Strict Browser Portfolio Contracts Summary

**Private management clients preserve original creation intent, and bounded overview parsing retains exact per-book money and stock evidence through the existing statement guard.**

## Performance and Task Commits

- Started approximately10:21UTC; completed10:28UTC on2026-11-18.
- Two of two tasks complete; six source/test files, plus this summary.
- Task1 RED `7ce0fc9`: management suite fails resolving the absent management client before implementation.
- Task1 GREEN `2d9eb54`: strict management/Unicode transport;34 management cases and52 retained target cases pass.
- Task2 RED `de4cc8a`: overview suite fails resolving the absent overview client;41 retained scoped-read cases still pass.
- Task2 GREEN `6ac87e5`: strict19-field overview and shared detail parser;82 overview/scoped-read cases pass.
- Final error-classification refinement `013104c`: retain known service failure code/timing while outcome remains unknown. Final six-suite regression passes205 cases.

Both tasks have committed RED before GREEN. No tracked file was deleted. Parent owns STATE/ROADMAP/REQUIREMENTS and independent review; this executor did not edit or stage them. The requirement IDs above record this plan's contribution, not whole-requirement acceptance.

## Delivered Management Contract and Plan09 Handoff

`portfolioManagement.ts` exports `PortfolioMetadata`, `PortfolioCreation`, `PortfolioMetadataPatch`, `parsePortfolioMetadata(value, requestedId?)`, `fetchPortfolioMetadata(id, signal?)`, `createPortfolio({key,name,description?}, signal?)`, `updatePortfolioMetadata(id, patch, signal?)`, `PortfolioManagementError`, `portfolioNameDisplay(value)` and `normalizePortfolioDescription(value)`.

Metadata responses contain exactly canonical string `id`, canonical `name` and plain-text `description`. Read/PATCH responses must match the requested ID; extra owner/financial fields, numeric/overflow/noncanonical IDs, invalid names, nulls and overlong descriptions refuse. Existing discovery remains exactly two keys `{id,name}`; the shared canonical name validator preserves that transport shape.

Name validation rejects raw C0/C1 and unpaired surrogate values before trimming the explicit server Unicode White_Space set and NFC normalization. Bounds count Unicode code points, including astral characters, rather than UTF-16 units. Display normalization does not decide casefold equivalence: distinct `Straße` and `STRASSE` remain independent browser input values pending SQL authority. The explicit trim set preserves BOM, which JS trim would otherwise remove. Description validation normalizes CRLF/CR to LF for validation/counters, allows TAB/LF, preserves whitespace and markup-looking text, rejects unsupported controls/surrogates and enforces1000 normalized code points. Callers can use `[...normalizePortfolioDescription(value)].length` after successful validation for counters.

Creation requires a canonical lowercase UUIDv4. It snapshots the original raw validated name/description and key before any CSRF/session await. The shared client's existing401 recovery resends the exact same serialized payload/key; this client generates no key and performs no separate retry. Omitted creation description becomes empty. PATCH omission preserves fields and explicit empty description clears; empty patches, unknown keys and nulls refuse before transport. All new requests use no-store, same-origin credentials and the supplied AbortSignal; writes use existing shared CSRF headers. Abort errors remain abort errors so captured owner/session lifecycle hooks can suppress late work.

`PortfolioManagementError` exposes only `outcome: refused|unknown`, safe allowlisted `code`, `status` and bounded `retryAfter`. Recognized management input/name/key/cap/unavailable/quota/attempt refusals remain definitive. Authentication/CSRF status remains definitive without retaining arbitrary authentication detail. Response loss, malformed success, arbitrary error codes and ambiguous5xx remain unknown. Known500/503 `service_unavailable` keeps its stable code and wait while remaining unknown; no error promises that no grant occurred. Arbitrary server messages, detail objects and financial/owner fields are discarded. Plan09 still owns frozen owner/session attempts, persistence-before-POST, explicit retry policy and stale callbacks.

## Exact Overview Contract and Plan11 Handoff

`portfolioOverview.ts` exports `PortfolioOverview`, `parsePortfolioOverview(value)` and `fetchPortfolioOverview(signal?)`. The static private URL is `/api/v2/portfolios/overview`. Unknown/malformed/error responses never become an empty success. Valid zero-book responses remain empty. At most ten unique canonical string IDs must appear in ascending numeric bigint order.

Each record has exactly these19 fields:

```text
id, name, description, cash, starting_cash, total_value, total_pl,
total_pl_percent, cash_allocation_percent, valuation_complete, known_value,
unvalued_holding_count, class_values, class_allocation_percent, valued_at,
prices_as_of, fresh_seconds, stale_seconds, holdings
```

Exact keys and metadata are checked before adapting `id` to `portfolio_id` for existing `isPortfolio`. This prevents duplicate-root injection without weakening detail's identity, holding, financial/completeness or stock-authority validation. Detail retains its original transport shape. All records must share one valuation instant. Each book's `prices_as_of` must equal its oldest available holding source instant, or null when none is available. Invalid/future source times, malformed times, extra/missing fields, noncanonical or numeric money, null/infinite/negative safety fields, duplicate holdings/roots, unsorted/over-cap rows and inconsistent financial/completeness/stock evidence refuse.

Monetary strings and custom/zero starting baselines remain exactly as returned; no Number money conversion, pooled value, return calculator or projected total is added. Complete and incomplete books remain independent. Existing dated/expired stock proof, original source times, mark modes, unsafe-unit flags and unavailable basis stay intact. Parsing does not renew proof or claim it is currently displayable. Plan11 must apply the existing permission/expiry projection semantics before exposing retained values, and own owner/session cache guards and stale-response suppression.

## Verification Evidence

Existing Node24/frontend dependencies only; no DB resource, backend test, provider or production operation ran.

```text
cd frontend
npm run test -- src/api/portfolioManagement.test.ts
  Initial GREEN:34 cases pass
npm run test -- src/api/portfolioOverview.test.ts src/api/portfolioReads.test.ts
  Initial GREEN:82 cases pass
./node_modules/.bin/eslint <all six changed TypeScript files>
  PASS
npm run typecheck
  PASS (whole frontend tsc -b)
npm run test -- src/api/portfolioManagement.test.ts src/api/portfolioOverview.test.ts \
  src/api/portfolioReads.test.ts src/api/portfolio.test.ts \
  src/hooks/usePortfolioTarget.test.tsx src/api/client.test.ts
  Final:6 files,205 tests pass; Vitest duration2.53s
git diff --check
  PASS
```

Changed files were formatted with the installed local Prettier. Focused cases independently assert original transport bytes through auth recovery, CSRF/method/header/credentials/abort semantics, strict canonical metadata, root mismatches, unknown outcomes and safe Retry-After, exact19-field shape, stored7654/zero baselines, incomplete values, dated stock proof and malformed authority/source/money negatives. Retained financial/detail/target/client families pass with the new validators.

## Deviations from Plan

None requiring scope or architecture changes. The plan explicitly permits safe identity adaptation instead of extraction; this retains the existing financial parser in place. Final review corrected known service-code preservation in `013104c`, with a regression assertion, while keeping ambiguous results unknown.

## Issues Encountered

The sandbox initially refused Git index writes as read-only; authorized Git escalation succeeded. No authentication gate or package install occurred. Routine implementation corrections replaced control-character regular expressions with explicit code-point checks for the existing ESLint rule and used explicit error fields to satisfy TypeScript erasableSyntaxOnly. Final lint/type/tests pass.

## Limits and Next Work

No UI rendering, storage, management hooks, cache lifecycle, cross-tab events or browser acceptance is claimed by these transport clients. Plans09–13 supply those consumers. Full critical coverage/security/recovery campaigns and implemented UI/native200 owner acceptance remain15–18. No new test/coverage gate waiver is introduced.

No packages, manifests, lockfiles, image/Python pins, provider admission, private environment, production, push or merge changed. Issue35's existing exact hash/path/version/target accepted risk, expiry2026-12-17T00:00:00Z and Python20261111 pin remain unchanged. Unrelated `.claude/` is preserved. Stub scan found no TODO/FIXME/placeholder or unfinished product stub; intentional empty metadata values represent valid omission/clear semantics. All API surfaces used here are already modeled in this plan; no additional trust-boundary surface was introduced.

## Self-Check: PASSED

All six source/test paths exist and all five task/refinement commit hashes resolve. RED precedes GREEN for both tasks. The205-case affected regression, whole frontend typing, changed-file lint/format and diff checks pass. Only unrelated `.claude/` remains untracked before summary creation.
