---
phase: 07-permitted-stock-discovery
plan: "12"
subsystem: frontend
tags: [react, accessibility, stocks, playwright, permission]
requires:
  - phase: 07-11
    provides: Validated projected stock query and visible IEX attribution
provides:
  - Independent read-only stock discovery beside existing crypto Markets
  - Responsive semantic catalogue with truthful quote/session/status facts
  - Authenticated Chromium refusal, expiry, recovery and coexistence evidence
affects: [07-13, 07-14, stock-trading]
tech-stack:
  added: []
  patterns: [Hook-owned monotonic deadlines, single categorical stock status region, responsive table and labelled records]
key-files:
  created:
    - frontend/src/components/StockSection.tsx
    - frontend/src/components/StockSection.test.tsx
    - frontend/e2e/stocks.spec.ts
  modified:
    - frontend/src/pages/MarketsPage.tsx
    - frontend/src/pages/MarketsPage.test.tsx
    - frontend/e2e/markets.spec.ts
key-decisions:
  - Stock presentation consumes useStocks projections without duplicating clocks or networking.
  - Calendar open, source recency and unknown stock status remain separate from disabled execution.
  - Browser fixtures intercept the stock discovery HTTP response while real isolated auth and crypto services run.
patterns-established:
  - CSS breakpoint exposes exactly one semantic stock table/list; stock records have no controls or links.
  - One categorical live region omits changing source ages and preserves focus during updates.
duration: 16min
completed: 2026-11-10
---

# Phase 7 Plan 12: Read-only Stock Markets Summary

**Markets now keeps crypto trading independent while twenty informational stock records show IEX attribution, dated bid/ask quotes and separate session/status facts.**

## Performance

- Duration: approximately16minutes including fresh isolated image builds and browser proof.
- Tasks:2/2; six owned frontend files.
- Source baseline:c250319; final implementation:ecb1344.

## Accomplishments

- Existing Markets shell now has Crypto followed by US stocks ·20; oldest-age summary explicitly belongs to crypto. All fifteen crypto Trade links remain executable.
- StockSection consumes the existing validated projected useStocks data. It introduces no provider call, independent permission authority, duplicated expiry clock or money arithmetic.
- Source label and simulation explanation are always visible. Provider-required credit is rendered through StockAttribution. Stocks have stable identities, separate company/symbol/listing exchange, exact string-formatted sides, semantic source times with local zone, exchange-zone regular session bounds and unknown status copy.
- Initial stock loading/error/retry is independent. Denial keeps catalogue identities and redacts quote values; original permitted updates remain dated after refresh failure, with keyboard retry. Missing/stale/previous-session/closed/unknown states remain distinct from trading capability.
- At1024px and above a semantic table is exposed; smaller views expose labelled records. Existing tokens/four-size typography subset/two weights are retained. One categorical status region omits changing ages.

## Task Commits

1. **07-12-01 Render approved discovery UI:** RED392708a → GREENab90f91.
2. **07-12-02 Authenticated responsive browser proof:** RED88c0ef4 → GREENecb1344.

## Verification

- Exact required component slice: `npm run test -- src/components/StockSection.test.tsx src/pages/MarketsPage.test.tsx` —16passed. Together with existing StockAttribution tests:20passed.
- Exact required browser slice: `playwright test e2e/markets.spec.ts e2e/stocks.spec.ts --workers=1 --retries=0` —11passed in approximately66seconds, no retries.
- Actual browser stories: real console-OTP authentication and fake-source crypto via isolated five-service Compose; fifteen crypto links/Trade navigation; twenty stock identities; source/provider attribution;320/375/768/1280px;640px effective viewport for200%reflow; no document overflow; single accessible table/list; keyboard retry/focus; unavailable→approved→revoked generations; local admission expiry plus expired late response; conservative119.999-second first response and119→120-second tick; categorical announcement changes only at boundary; missing/previous-session/unknown calendar; server-provided winter/summer bounds and early close; independent refresh failure.
- Existing Markets story also proves real denied stock API catalogue coexistence, crypto polling/account navigation and anonymous rejection.
- Changed-file ESLint, project TypeScript and changed-file Prettier checks pass; `git diff --check` passes.
- Behavioral RED evidence: five missing-presentation assertions failed before Task1 implementation. Actual authenticated Chromium then failed specifically because background recovery lacked the required retry button; Task2 GREEN provides it.
- Stub/threat scan found no unimplemented feature stub, new endpoint, secret storage, file trust boundary or dependency. Stock execution being disabled and stock status remaining unverified are intentional approved phase boundaries.

### Isolated execution evidence

Temporary harness/evidence: `/tmp/birja-phase07-e2e-vnwyv5ep/`:

- Rendered configuration verified dedicated `birja-phase07-e2e-test` project, synthetic environment only, fake crypto, console email, stock source disabled, no bound source/private paths, tmpfs datastores, and only random loopback frontend port.
- Fresh backend/scheduler/frontend images built from current workspace; identities saved in `image-identities.json`; final frontend build log and exact browser output retained.
- Responsive screenshots copied to `screenshots/stocks-{320,375,768,1280}.png`. Desktop screenshot inspected; automated screenshots are not final owner UI acceptance.
- This test project was brought down with its own exact configuration. Container/network/volume label inventory is empty in `remaining-resources.json`. Existing birja-test resources were preserved for07-13. Production/development services, data, timers and private credentials were not accessed.

## Deviations from Plan

1. **[Rule1—Bug] Background outage recovery needed a visible retry.** The browser RED assertion found that initial-error retry existed but retained-data failure had no keyboard recovery. Added the same secondary recovery control to the owned StockSection during Task2; preserved original quote timestamps and hook authority. Proven by the real authenticated outage/Enter-key story. Commit:ecb1344.
2. **[Rule3—Local proof harness] Nonroot Redis tmpfs ownership.** Existing hardened Redis UID65532 could not create its append-only directory on a root-owned disposable tmpfs. Set UID/GID only on the temporary test mount. No tracked Compose/image/runtime changes.
3. **Test-fixture correction.** Initial expiry fixture counted React StrictMode’s repeated initial request as the deliberate late response. Switched fixture mode only after a visible admitted quote; reran the failed case and final exact slice successfully. No product bypass or security gate change.

## Decisions Made

- Reuse existing attribution/query ownership and design system. Stock rows remain informational through Phase8.
- Browser stock-response fixtures prove presentation and client expiry behavior; they do not establish provider access or live display rights. Backend/provider/committed-generation semantics have their separate earlier proofs.

## Remaining Gates / Next Plan Readiness

07-13 can run complete local phase gates, restricted-TLS consumer and security/image regressions against this implementation.07-14 still owns actual provider permission/access/coverage/freshness evidence and owner UI acceptance. No requirement checkbox or whole-phase success criterion is completed merely by this fixture-backed UI plan. No push, publication, deployment or provider activation occurred.

## Self-Check: PASSED

- Six owned files exist; all four task commits are present in local history.
- Required component/browser slices pass; screenshots and sanitized local proof records exist.
- Exact isolated e2e resource cleanup verified empty; unrelated untracked `.claude/` preserved.
