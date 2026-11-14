---
phase: 10-dividend-cash-and-event-history
plan: "15"
subsystem: actual-browser-evidence
tags: [restricted-sql, dividend-spending, responsive-history, keyboard-focus, offline-review]
requires:
  - phase: 10-09
    provides: Bounded real retained dividend worker
  - phase: 10-14
    provides: Typed responsive mixed History
provides:
  - Real dividend-funded stock/crypto and held/reconciled browser journeys
  - Complete50-case browser gate with49passes and one expected CSP skip
  - Source-hashed offline DOM/CSS/font review ZIP and screenshots
affects: [10-16, 10-17, 10-18]
tech-stack:
  added: []
  patterns: [guarded-disposable-financial-fixture, frozen-source-browser-proof, session-bound-focus-intent]
key-files:
  created:
    - frontend/e2e/dividends-history.spec.ts
    - .planning/phases/10-dividend-cash-and-event-history/10-BROWSER.md
    - .planning/phases/10-dividend-cash-and-event-history/10-UI-SOURCE-HASHES.json
  modified:
    - deploy/tests/dividend-execution-fixture.py
    - deploy/tests/run-stock-browser.py
    - frontend/e2e/portfolio-history.spec.ts
    - frontend/e2e/stock-actions.spec.ts
    - frontend/src/pages/HistoryPage.tsx
    - frontend/src/pages/HistoryPage.test.tsx
key-decisions:
  - Prove purchases exceed the original grant so dividend funds are actually required.
  - Capture append focus intent before native disabled blur and restore post-render only for the same owner lifecycle.
  - Separate synthetic tied-read presentation from actual financial effects and SQL tie proof.
requirements-completed: []
requirements-supported: [DIV-03, DIV-04, DIV-05, HIST-03]
duration: multi-pass local browser execution; final full browser314.1s
completed: 2026-11-13
---

# Phase10 Plan15: Actual dividend cash and private browser History

**Real restricted worker/SQL income funds stock and crypto purchases, immutable
adjustments and holds match cash, and final-source keyboard/responsive evidence
is packaged without claiming owner acceptance.**

## Tasks and commits

1. `ababfd5`: guarded browser extension, actual financial/mixed History spec,
   runner dividends/optional bounded grep, exact legacy wire/layout adaptation
   and synchronized existing stock retry test. All earlier operations PROGRAM
   bytes remain unchanged; no authority/schema/recovery source changed.
2. Evidence files and source/hash manifest accompany this summary. Actual final
   full browser49passed/1expectedCSPskip,314.1s runner (5.2m Playwright).

Parent-approved source fixes are separate atomic commits:
`944cb7f` captures native-blur focus intent; `7aa29fe` restores the retry control
after React enables it. Same owner/epoch and body/original-control checks preserve
non-stealing focus. Actual browser failures, two regressions and existing focus/
auth tests establish the fix; no speculative UI expansion or financial change.

## Actual verification

| Gate | Final result |
|---|---|
| New financial/responsive/owner suite |4passed/1.5m before final retry refinement |
| Final actual focus/responsive selector |1passed/31.3s |
| Stock retry synchronization selector |1passed/3.8s |
| Complete frozen browser suite |49passed/1expectedskip/5.2m; runner314.1s |
| Final complete frontend coverage |697passed/36files/18.04s |
| Final frontend coverage percentages |98.37statements;94.82branches;98.95functions;99.10lines |
| Focus component/page gate |29passed/3.67s |
| Full ESLint/TypeScript/Prettier |Pass |
| Python compile/scoped RuffF/format/whitespace |Pass |
| Frozen source and browser cleanup |112hashes unchanged; owned containers/networks/volumes0 |
| Review ZIP/source/hash integrity |Pass;16HTML/32PNG,50ZIP entries |

Exact commands/logs and failure provenance are in10-BROWSER. Final log
`/tmp/birja-phase10-15-browser-all-final2.log`, detailed evidence
`/tmp/birja-phase09-browser-b1d258g4`. Frontend log
`/tmp/birja-phase10-15-frontend-final.log`. Installed tools only; no sync/install.

Cash10000→20000 original, real stock−5100 and crypto−10000→4900 proves dividend
funds are used. Verified+2, unaffordable−10001hold/repeat, actual sale funding and
one−10001successor, uncertain no-cash hold/repeat and reviewed+10003successor
match exact stored/API values. Starting cash stays10000. Synthetic historical
opening journal/evidence is explicitly input, not a claimed prior executed fill.
No Account.cash UPDATE or mocked financial-success mutation creates these effects.

Actual31-record mixed pages include owner split3:2 (stored1.5:1), trade, dividend
and correction, offpage original and 320/375/768/1024/1440 focus/reflow. Errors
retain accepted pages; delayed actual reads cannot restore an old owner's trade.
Pre-anchor uncertainty publishes no Dividend. Read-only tied presentation uses a
labelled synthetic timestamp and never modifies DB cash/immutable timestamps;
actual SQL tie/privacy proof remains predecessor10. Root-font enlargement is
supplementary; native200% and new UI owner acceptance remain pending Plan18.

## Deviations, threats and remaining gates

Parent approved narrowly necessary existing portfolio-history wire/locator and
stock-actions retry synchronization updates, plus the two-file real focus fix.
Fresh browser startup lacked the safe0014owner; runner-only preprovisioning fixes
the owned stack. Fresh ordinary dev startup still needs Plan16 follow-up, with
exact evidence in10-BROWSER; no dev/prod environment was read or touched.

Own fixture import/required-date/retained-opening timing errors were corrected;
earlier failed runs and interrupted full diagnostics remain separate. First
complete frozen run48passes/one expectedskip/one retry-race failure was superseded
by49passes. StockSection application source stayed unchanged.

T-10-15-01/02: actual auth/private reads and restricted financial effects, immutable
lineage/once-only/no-cash assertions pass. T-10-15-03: bounded fixture ops, test
timeouts, disabled external data and verified owned cleanup. T-10-15-SC: no new
dependency/image/lock changes or install. Browser bootstrap is explicitly guarded
test-only and introduces no app endpoint/backdoor. No known stubs remain.

Review: `/tmp/birja-phase10-ui-review.zip`,15536733bytes, SHA256
`4f5d316ae29a6a2d9f9b7173b58715f6bee996191c5387effa7d51193ea49c7d`;
index `/tmp/birja-phase10-ui-review/index.html`. No scripts/forms/network URLs,
traces/env/OTP/session material; all data synthetic.106source hashes and all
review artifact hashes are tracked in10-UI-SOURCE-HASHES.json. Final viewport
images were visually inspected for wrapping, truthful cash and nav clearance.

No provider/real.env/production/B2/timer/installed-tool/push/deployment action.
Parent owns state/requirements and full final gates16, independent reviews17,
owner acceptance18. Whole requirements are not marked complete by this plan.

## Self-Check: PASSED

All owned/approved source files, browser evidence, manifest and summary exist.
Task1 and both scoped fix hashes exist without tracked deletions. Actual final
browser/frontend/static/ZIP/hash/cleanup gates pass. Only unrelated.claude remains
untracked. The parent's birja-test stack is untouched; browser ownership released.
