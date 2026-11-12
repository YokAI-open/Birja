# Roadmap: Birja

## Milestones

- [x] **v1.0 Birja MVP** — 7 phases / 69 plans, shipped 2026-11-10 as software v0.4.0; [full roadmap](milestones/v1.0-ROADMAP.md).
- [ ] **v1.1 US Stock Trading** — Phases 7–11; requirements and roadmap approved 2026-11-10.

## Overview

Extend the working crypto simulator with twenty curated NYSE/Nasdaq stocks,
labelled IEX quotes, whole-share regular-session trading, shared USD and combined
portfolio/history. Establish permitted data and corporate-action safeguards before
stock execution, then complete dividend payments and prove exact mixed-asset
recovery. Keep crypto usable at every phase. This planning milestone does not
authorize a software release or deployment.

## Phases

- [ ] **Phase 7: Permitted Stock Discovery** — Browse twenty stocks with truthful IEX prices, freshness and regular-session availability while preserving existing accounts.
- [x] **Phase 8: Corporate-Action-Safe Ownership** — Protect ownership with event monitoring, historical dividend eligibility, ordinary forward splits and visible uncertainty suspensions. (completed 2026-11-11)
- [ ] **Phase 9: Whole-Share Trading and Combined Portfolio** — Trade stocks against shared cash with safe previews/retries and honest mixed-asset valuations.
- [ ] **Phase 10: Dividend Cash and Event History** — Receive dividends and auditable corrections in shared cash and complete paginated History.
- [ ] **Phase 11: Mixed-Asset Recovery and Acceptance** — Restore the complete ledger exactly and prove full user journeys under existing CI gates.

## Activation and compatibility boundaries

- **Data gate:** Verify Birja's quote, corporate-action and status product access,
  display/derived-data/retention rights, attribution, quotas, symbol coverage and
  observed source freshness before exposing the relevant live data. Unverified
  rights or unavailable inputs leave stock activation disabled; crypto works.
  Research is dated evidence, not permission. No provider contact, signup,
  agreement, payment or production access is authorized by this roadmap.

- **Staged execution:** Phases 7–8 leave stock execution disabled. Phase 8's
  ownership/action behaviors are verifiable with isolated seeded holdings and
  historical trades and visible affected-stock states. Phase 9 may enable stock
  execution only after the Phase 8 monitor, suspension rules, ordered action
  processing and historical eligibility capture are integrated with its first
  fill. No interval of trading without entitlement history is permitted.
  Phase 10 adds dividend cash publication; earlier entitlements survive until
  payment and are processed without a gap or duplicate.

- **Schema safety travels with features:** SAFE-01 and SAFE-02 each have one
  primary owner, but every schema-changing phase preserves identities, balances
  and history, reviews migrations, exercises restricted-role verified-TLS access
  and evolves backup/manifest/validation contracts for its new state. Final
  Phase 11 recovery acceptance does not defer these obligations. Public rollout
  waits for exact mixed-asset restore proof and retained-tool/grant compatibility;
  installed-tool replacement and deployment need separate approval.

- **Tests travel with features:** Each phase ships meaningful isolated database,
  HTTP-boundary and applicable browser tests. Phase 11 proves integrated journeys;
  it does not defer feature tests, critical-path coverage or security gates.

- **UI continuity:** Frontend phases use GSD UI contracts and the existing
  design-system/birja/MASTER.md, Tailwind/shadcn and TanStack Query. No replacement
  visual system, additional queue or generic provider framework is implied.

## Phase Details

### Phase 7: Permitted Stock Discovery

**Goal**: Users can discover curated stocks with honest permitted quote and session information while their existing crypto accounts remain intact.
**Depends on**: Completed v1.0 milestone (Phase 6).
**Requirements**: STOCK-01, STOCK-02, STOCK-03, DATA-01, MKT-01, SAFE-01
**Success Criteria** (what must be TRUE):

  1. User can browse exactly twenty NYSE/Nasdaq USD common stocks alongside crypto, distinguish stable company/symbol/listing identities, and see “IEX prices” with the single-venue simulated-execution explanation. Shared attribution components also serve later previews and valuations. (STOCK-01, STOCK-02)
  2. User sees bid/ask quotes and source-event times refreshed about every minute; quotes aged 120 seconds or more, invalid quotes and prior-session quotes at reopening are ineligible for execution. Fetch time cannot make old quotes fresh. (STOCK-03)
  3. User receives relevant live data only when verified access, display/derived-data rights, quotas and attribution cover quote, action and eligibility inputs; otherwise stocks remain disabled and crypto works. (DATA-01)
  4. User sees regular-session availability derived server-side from the applicable calendar, including holidays, early closes and America/New_York daylight saving; outside that session no stock is advertised as executable. Phase 9 applies this same guard to actual fill attempts. (MKT-01)
  5. Existing users retain original starting cash, balances, identities, holdings and immutable crypto fills after reviewed migrations; existing and new services work with restricted verified-TLS roles. Later phases retain this contract. (SAFE-01)

**Plans**: 14 plans

Plans:
**Wave 1**

- [x] 07-01-PLAN.md — Expand stable instrument and discovery storage.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 07-02-PLAN.md — Preserve crypto routes and refuse stock execution.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 07-03-PLAN.md — Version exact recovery contracts with the schema.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 07-04-PLAN.md — Prove restricted-role TLS upgrade and exact restore.

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 07-05-PLAN.md — Implement product-specific fail-closed admission.

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 07-06-PLAN.md — Validate exact IEX quotes and monotonic persistence.
- [x] 07-07-PLAN.md — Review calendar dependency before installation.

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 07-08-PLAN.md — Implement verified regular-session calendars.

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 07-09-PLAN.md — Collect stocks independently inside the single scheduler.

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 07-10-PLAN.md — Expose authenticated catalogue-first stock discovery.

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 07-11-PLAN.md — Validate and isolate stock client state.

**Wave 11** *(blocked on Wave 10 completion)*

- [x] 07-12-PLAN.md — Deliver responsive read-only stocks beside crypto.

**Wave 12** *(blocked on Wave 11 completion)*

- [x] 07-13-PLAN.md — Close local coverage, image and recovery gates.

**Wave 13** *(blocked on Wave 12 completion)*

- [ ] 07-14-PLAN.md — Verify external admission and final discovery acceptance.

**UI hint**: yes

### Phase 8: Corporate-Action-Safe Ownership

**Goal**: Stock owners' units, basis and dividend eligibility remain explainable through ordinary events, and uncertain events prevent unsafe trading or valuation.
**Depends on**: Phase 7
**Requirements**: DIV-01, DIV-02, ACT-01, ACT-02, ACT-03
**Success Criteria** (what must be TRUE):

  1. Operator can inspect retained ordinary USD dividend announcement identities, dates, rates and revisions; regular rechecks detect changes, while conflicting, incomplete or cancelled information stays pending instead of producing guessed entitlements. (DIV-01)
  2. Given a verified cutoff and historical holdings, the user earns only the eligible quantity: buying afterward does not qualify and selling afterward does not erase it. Processed splits are accounted for and eligibility remains reconstructible; Phase 9 must preserve this history from its first fill. (DIV-02)
  3. A verified straightforward forward split adjusts supported whole-share holdings once, conserves total basis, changes unit basis correctly and leaves original fills unchanged. Fractional or ambiguous entitlements do not use this automatic path. (ACT-01, ACT-03)
  4. User sees affected stocks suspended and uncertain valuations unavailable for unsupported/disputed actions or insufficient monitoring; only verified auditable reconciliation restores availability, without guessed liquidation or cash-in-lieu. Other eligible instruments and crypto remain independent. (ACT-02, ACT-03)
  5. Event replay or recovery cannot repeat a split or reorder it across trades and dividend eligibility. Defined monitoring-loss/recovery behavior is demonstrable on isolated seeded holdings before stock execution is enabled. (ACT-03, DIV-02)

**Plans**: 13 plans (29 tasks, 11 waves)

Plans:
**Wave 1**

- [x] 08-01-PLAN.md — Add durable action and ownership schema with narrow grants. (Wave 1)
- [x] 08-03-PLAN.md — Define independent action permission, exact terms and safety rules. (Wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-02-PLAN.md — Prove exact0011 recovery and restricted TLS compatibility. (Wave 2)
- [x] 08-04-PLAN.md — Collect bounded current REST/known-ID/mutation observations. (Wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 08-05-PLAN.md — Journal historical ownership with post-lock economic ordering. (Wave 3)

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 08-06-PLAN.md — Persist revisions, atomic forward splits and dividend entitlements. (Wave 4)

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 08-07-PLAN.md — Monitor complete catch-up independently in the existing scheduler. (Wave 5)

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 08-08-PLAN.md — Add audited narrow reconciliation and exact0012 recovery. (Wave 6)

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 08-09-PLAN.md — Expose current action safety and compatible quote units. (Wave 7)

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 08-10-PLAN.md — Enforce strict client epochs and exact boundary expiry. (Wave 8)

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 08-11-PLAN.md — Render accessible responsive suspension states and browser proof. (Wave 9)

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 08-12-PLAN.md — Close local critical coverage, security and recovery gates. (Wave 10)

**Wave 11** *(blocked on Wave 10 completion)*

- [x] 08-13-PLAN.md — Record new UI acceptance and separate external activation disposition. (Wave 11)

**Execution boundary**: Owner-deferred Phase 7 live evidence remains pending.
Isolated Phase 8 development may proceed without enabling stock execution or
new provider access. Distinct action-product/retained-accounting/backup rights,
actual continuity/quotas/latency and Phase 7 live acceptance stay activation
gates. All local proof precedes the final external checkpoint. Migration/recovery
compatibility for each successor revision precedes its runtime consumers;
no production or installed-tool change is authorized by these plans.
**UI hint**: yes

### Phase 9: Whole-Share Trading and Combined Portfolio

**Goal**: Users can safely buy and sell whole stocks using existing cash and see truthful combined holdings without compromising crypto or corporate-action accounting.
**Depends on**: Phases 7 and 8; eligibility capture and action safeguards integrated before the first stock fill.
**Requirements**: MKT-02, STKTR-01, STKTR-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06, PORT-06, PORT-07
**Success Criteria** (what must be TRUE):

  1. User can submit positive whole-share stock quantities only, preview an eligible IEX ask buy or bid sell at zero commission/added spread, and inspect the persisted fill; relevant price changes require renewed confirmation. IEX/simulation and omitted-regulatory-fee disclosures are visible; fractional and dollar-input crypto behavior is preserved. (STKTR-01, STKTR-02, STKTR-03)
  2. Concurrent stock and crypto orders use the same original USD account without a second grant or negative cash/holdings. Stock-sale proceeds immediately fund either asset with the settlement simplification disclosed; each fill preserves Phase 8 entitlement/action ordering. (STKTR-04, STKTR-06)
  3. User receives clear refusal for closed, halted, frozen, unknown or stale eligibility; requests blocked on database locks recheck current eligibility and quote age before new fills. Crypto remains independently available. (MKT-02)
  4. Retrying an uncertain order returns its original stored fill exactly once even after closing time; changing its payload under the same key conflicts. (STKTR-05)
  5. User sees combined cash, crypto and midpoint-valued stocks, allocation and return against original starting cash, with IEX attribution. Closed marks show actual dates; missing/action-uncertain marks make totals explicitly incomplete. Dividend cash is counted once when Phase 10 enables credits. (PORT-06, PORT-07)

**Plans**: 15 plans in13 execution waves

Plans:
**Wave 1**

- [x] 09-01-PLAN.md — Freeze stock financial and authority contracts

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 09-02-PLAN.md — Implement exact whole-share plans and conservative shortcuts

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 09-03-PLAN.md — Add successor stock facts and independent status integrity

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 09-04-PLAN.md — Prove exact0013 recovery and least-privilege TLS parity

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 09-05-PLAN.md — Implement bounded independent status and stock eligibility

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 09-06-PLAN.md — Implement atomic stock execution and global idempotency

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 09-07-PLAN.md — Prove shared-cash, action-order and final-wait concurrency

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 09-08-PLAN.md — Expose authenticated stock preview, context and fill APIs
- [x] 09-09-PLAN.md — Compute honest mixed portfolio from one financial snapshot

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 09-10-PLAN.md — Implement strict stock client and protected order-attempt lifecycle
- [ ] 09-12-PLAN.md — Present protected combined portfolio and three allocation classes

**Wave 10** *(blocked on Wave 9 completion)*

- [ ] 09-11-PLAN.md — Deliver the reachable whole-share ticket and immutable receipt

**Wave 11** *(blocked on Wave 10 completion)*

- [ ] 09-13-PLAN.md — Exercise actual isolated browser journeys and accessibility

**Wave 12** *(blocked on Wave 11 completion)*

- [ ] 09-14-PLAN.md — Close strict local financial, recovery and independent review gates

**Wave 13** *(blocked on Wave 12 completion)*

- [ ] 09-15-PLAN.md — Obtain owner acceptance of the new Phase9 interface

**Cross-cutting constraints:**

- D-01: User edits only positive whole-share stock quantity; Buy max/Sell all populate drafts requiring preview and confirmation.
- D-03: Relevant stock price changes show old-to-new execution price and cash-total difference and require renewed confirmation.
- D-04: User remains on original persisted receipt with historical cash/share-after and Portfolio/Trade again actions.
- D-09: Incomplete portfolio shows Known value and unvalued count, with unavailable total returns and all allocation percentages.
- D-14: New fills require current regular session, normal independent status and action/permission safety plus quote age strictly below120seconds after all waits.
- D-15: Mixed orders share original cash without new grant/overspend; same-key original receipt replays even after close and payload changes conflict.
- D-16: Stocks use midpoint/dated closed marks; unknown actions make valuation unavailable, and future dividend cash is counted once from Account.cash.
- D-02: User sees IEX bid/ask, buys at ask or sells at bid with zero stock fee/spread; crypto inputs/fees remain unchanged.
- D-13: Stock journey discloses IEX single venue, simulated execution, omitted regulatory fees and immediately reusable virtual proceeds.
- D-10: Verified halt retains permitted compatible dated last midpoint with Halted label; action uncertainty suppresses it.
- D-11: Unavailable stock ticket allows quantity drafting but disables confirmation and unsafe estimates; no order is queued.
- D-12: Interrupted review retains quantity, invalidates preview and requires fresh preview plus confirmation without autoexecution.
- D-05: User sees one shared cash balance and combined labelled Stock/Crypto holdings list.
- D-06: Holdings remain alphabetical by ticker with stable identity tie-break as prices refresh.
- D-07: Quantity, average cost, basis, value, gain/loss and allocation appear directly in desktop table/mobile cards.
- D-08: Allocation displays Cash/Stocks/Crypto class bars and individual holding percentages only when complete.

**UI hint**: yes

### Phase 10: Dividend Cash and Event History

**Goal**: Users receive verified dividend cash once and trace all mixed-asset trades, income, splits and corrections in History.
**Depends on**: Phases 8 and 9
**Requirements**: DIV-03, DIV-04, DIV-05, HIST-03
**Success Criteria** (what must be TRUE):

  1. On or after payable date, a verified ordinary USD dividend credits gross cash using retained eligible quantity, without tax or reinvestment. Its separate Dividend event shows stock, relevant dates, eligible shares, per-share rate and credit, including entitlements captured before this phase. (DIV-03)
  2. Concurrent runs, retries, announcement revisions and recovery cannot credit one dividend twice or expose History cash without its matching atomic credit. (DIV-04)
  3. A verified post-payment correction produces a separate linked adjustment, preserving the original. Repetition cannot duplicate its delta; uncertain or unaffordable negative adjustments stay visibly held for reconciliation without negative cash. (DIV-05)
  4. User privately pages through deterministic newest-first crypto/stock fills, Dividend credits, forward splits and corrections with event-specific details and preserved crypto history. Portfolio return includes dividend cash exactly once. (HIST-03; consumes PORT-06)

**Plans**: TBD
**UI hint**: yes

### Phase 11: Mixed-Asset Recovery and Acceptance

**Goal**: Operator can restore the full mixed-asset financial state exactly, and complete user stock journeys are proven without weakening protections.
**Depends on**: Phases 7–10
**Requirements**: SAFE-02, SAFE-03
**Success Criteria** (what must be TRUE):

  1. Operator can restore an exact encrypted backup of holdings/cash, announcement revisions, entitlements, dividends, actions and History with matching totals and duplicate-prevention state, using compatible retained tools, schema and restricted-role grants. Replay cannot repeat fills, payments, corrections or splits. (SAFE-02)
  2. Real isolated PostgreSQL tests prove stock/crypto contention, post-lock expiry, closed-market replay, dividend cutoff/revision/concurrency, split ordering and uncertain-action suspension with exact-money assertions. (SAFE-03)
  3. Browser journeys prove discovery, preview/confirmation, open/closed trading, combined portfolio, dividends, splits, corrections, stale/unknown states and crypto coexistence; applicable coverage, dependency/image security and required CI gates remain enforced. (SAFE-03)

**Plans**: TBD
**UI hint**: yes

## Progress

**Approved execution order:** 7 → 8 → 9 → 10 → 11. Phase 7 Plans 01–13 are
complete, including calendar dependency review, genuine calendar consumers,
responsive discovery and local coverage/security/recovery gates. Plan 14 remains
open: owner-attested permission and bounded verification are authorized, with
one campaign waiting for the 2026-11-11 regular-session opening. Actual provider
identity/freshness results are explicitly deferred by the owner while local
closeout continues; they remain pending, not waived. Owner UI acceptance was received on
2026-11-11 and recorded in `07-HUMAN-UAT.md`; waiting and test fixtures
do not establish live acceptance or phase completion.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 7. Permitted Stock Discovery | v1.1 | 13/14 | Local work complete; live acceptance deferred |  |
| 8. Corporate-Action-Safe Ownership | v1.1 | 13/13 | Complete    | 2026-11-11 |
| 9. Whole-Share Trading and Combined Portfolio | v1.1 | 10/15 | In Progress|  |
| 10. Dividend Cash and Event History | v1.1 | 0/TBD | Not started | - |
| 11. Mixed-Asset Recovery and Acceptance | v1.1 | 0/TBD | Not started | - |

**Coverage:** 26/26 approved requirements have exactly one primary owner:
6 in Phase 7, 5 in Phase 8, 9 in Phase 9, 4 in Phase 10 and 2 in Phase 11.
Integration/compatibility obligations do not create duplicate primary owners.

## Follow-up debt

Owner-approved W01–W08 and four historical validation-record gaps remain in the
[milestone audit](milestones/v1.0-MILESTONE-AUDIT.md) and
[integration audit](milestones/v1.0-INTEGRATION-AUDIT.md). They are not silently
resolved or added to this milestone. Prior phase history remains in
milestones/v1.0-phases/. Daily backup/certificate checks continue under
deploy/RUNBOOK.md.
