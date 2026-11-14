---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "12"
subsystem: portfolio-ui
requires: [09-09]
provides: [strict mixed snapshot parser, protected private cache, combined holdings UI]
affects: [09-11, 09-13, 09-14]
tech-stack:
  added: []
requirements-completed: []
requirements-supported: [PORT-06, PORT-07]
completed: 2026-11-12
---

# Plan09-12: Protected combined portfolio

Task1 observed REDb820e81 and parser GREEN3e32c91 reject contradictory completeness,
counts, asset identities, nullable classes, percentages, source rights and unsafe
unit-derived figures. Money stays bounded38-integer/9-fraction strings with exact
BigInt relationship checks. Actual positive raw value rounded to zero may retain
server allocation; no denominator is invented from rounded dollars.

Hook RED96a1560/GREEN0550c25 implement private email/query-owner/lifecycle guards,
monotonic original authority/epochs/hash/continuity and full-RTT display bounds.
Historical closed/halted prices do not expire merely at120seconds. Exact deadline
timers, focus and cache changes redact prices and dependent summaries in cache
and view. Known subtotal becomes unavailable after client suppression; no JS
financial subtotal is calculated. Independently safe cash/crypto may remain.

Task2 RED176d4ad exercises missing stock labels/basis/three-class/incomplete UI.
Implementation uses exactly seven semantic columns at1024px and labelled mobile
cards below, stable ticker/identity ordering, direct figures and Stock/Crypto
labels. Cash/Stocks/Crypto bars use server percentages only; all fills disappear
when incomplete. IEX midpoint attribution and dated closed/halted labels remain
visible. Uncertain unit average cost/quantity/valuation are unavailable, with
stored basis retained. Starting cash and future dividend cash stay server-owned.

Separate inline review found late older restrictive snapshots were ignored:
RED340b394; correction preserves newer cash and suppresses affected stock marks.
Review also caught clock metadata cache writes clearing background error state;
clock stays in the guard, safety-only cache changes preserve request status.
Original auth-switch App regression now asserts private-cache removal and the
additional real useMe observer. No auth expectation was removed.

## Verification

Final four files:59tests passed (see/tmp/birja-phase09-12-client.log for duration).
TypeScript, scoped ESLint/Prettier and diff checks pass. Tests cover exact125ms
cache expiry, original retention equality, slow RTT, delayed split/permission
hashes, auth pending replies, retry focus, duplicate refresh, seven fields,
complete/incomplete/zero/raw-rounded-zero, crypto route/quantity, huge values,
long escaped company names and actual rendered historical labels. Browser
breakpoints/zoom and full critical coverage remain13–14; owner acceptance15.
Review provenance is inline, not independent. No provider/production/publication.
