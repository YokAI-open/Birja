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
- [ ] **Phase 8: Corporate-Action-Safe Ownership** — Protect ownership with event monitoring, historical dividend eligibility, ordinary forward splits and visible uncertainty suspensions.
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

- [ ] 07-02-PLAN.md — Preserve crypto routes and refuse stock execution.

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 07-03-PLAN.md — Version exact recovery contracts with the schema.

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 07-04-PLAN.md — Prove restricted-role TLS upgrade and exact restore.

**Wave 5** *(blocked on Wave 4 completion)*

- [ ] 07-05-PLAN.md — Implement product-specific fail-closed admission.

**Wave 6** *(blocked on Wave 5 completion)*

- [ ] 07-06-PLAN.md — Validate exact IEX quotes and monotonic persistence.
- [ ] 07-07-PLAN.md — Review calendar dependency before installation.

**Wave 7** *(blocked on Wave 6 completion)*

- [ ] 07-08-PLAN.md — Implement verified regular-session calendars.

**Wave 8** *(blocked on Wave 7 completion)*

- [ ] 07-09-PLAN.md — Collect stocks independently inside the single scheduler.

**Wave 9** *(blocked on Wave 8 completion)*

- [ ] 07-10-PLAN.md — Expose authenticated catalogue-first stock discovery.

**Wave 10** *(blocked on Wave 9 completion)*

- [ ] 07-11-PLAN.md — Validate and isolate stock client state.

**Wave 11** *(blocked on Wave 10 completion)*

- [ ] 07-12-PLAN.md — Deliver responsive read-only stocks beside crypto.

**Wave 12** *(blocked on Wave 11 completion)*

- [ ] 07-13-PLAN.md — Close local coverage, image and recovery gates.

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

**Plans**: TBD
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

**Plans**: TBD
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

**Approved execution order:** 7 → 8 → 9 → 10 → 11. Phase7 execution is underway:
07-01schema/catalogue complete;07-02crypto-boundary preservation is next.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 7. Permitted Stock Discovery | v1.1 | 1/14 | In Progress | - |
| 8. Corporate-Action-Safe Ownership | v1.1 | 0/TBD | Not started | - |
| 9. Whole-Share Trading and Combined Portfolio | v1.1 | 0/TBD | Not started | - |
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
