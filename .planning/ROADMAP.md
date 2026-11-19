# Roadmap: Birja

## Milestones

- [x] **v1.0 Birja MVP** — shipped 2026-11-10 as software v0.4.0; [archive](milestones/v1.0-ROADMAP.md).
- [x] **v1.1 US Stock Trading** — closed 2026-11-14 with accepted live gaps: 63/64 plans, 130/132 tasks, 20/26 requirements locally satisfied; [archive](milestones/v1.1-ROADMAP.md).
- [ ] **v1.2 Multiple Strategy Portfolios** — 28 requirements; Phase12 complete locally, Phases13–15 remain.

## Current State

Software [v0.5.0](https://github.com/YokAI-open/Birja/releases/tag/v0.5.0)
is published at main c2c7af1 after all six release checks passed. Corrective
main PR34 and develop back-merge PR33 are merged after six green jobs each;
their final trees match. Last confirmed production remains v0.4.0/schema0008.
Stock activation stays gated; source publication does not establish live rights,
suitability or acceptance. No production inspection or change is part of this roadmap.

The owner approved the original 27 [v1.2 requirements](REQUIREMENTS.md) and
subsequently added optional descriptions (PMGT-06), bringing the total to 28
on 2026-11-14.
The owner approved the four-phase roadmap on 2026-11-14. Numbering continues
at Phase12. Phase12 is complete locally:31plans/62tasks/21waves, independent
goal verification8/8 with one explicit owner-approved advisory override,
all5functional criteria and all7assigned requirements satisfied. Both owner
UI/native200 checks remain accepted. Existing money, explicit target journeys,
private History, restricted verified-TLS authority and exact current/retained
recovery are qualified. See the Phase12 verification and31summary.

Actual complete security1479.850s and fresh seven-stage same-archive
recovery2694.692s pass at4b4320b. Backend3114/critical60at100%, frontend958,
audit12, browser59/1originaldeployed-CSPskip, smoke5 and fiveimage-policy scans
pass. Raw picomatch findings remain visible as accepted risk under issue35,
expiring2026-12-17UTC; this is not a remediation claim. The rejected fork stays
uninstalled. A separate official Python image patch was explicitly approved,
verified and qualified. Prior failed runs and the old archive are retained.
No production/provider/publication action occurred. Phase13 is planned and unimplemented; Phases14–15 remain
unplanned and unimplemented;21v1.2requirements remain pending. Phase7's six
live gaps stay separately deferred, with its manual campaign consumed.

[Research](research/v1.2/SUMMARY.md) supports reusing the existing stack; it does
not authorize new dependencies, providers or implementation.

## Overview

Users will preserve their existing investing history in a first portfolio, then
create and compare up to ten independently funded $10,000 strategies. Each
portfolio owns its cash, holdings, trading, financial events and returns. Deletion
ends an experiment at a retained frozen boundary, even with holdings or when it
is the last portfolio. It never liquidates assets or transfers funds to another
strategy. The phases preserve runnable investing journeys while moving the
financial ownership boundary; they are not separate database/API/UI layers.

## Phases

**Status:** Phases12–13 verified complete locally; Phase14 is executing (7/19plans complete) and Phase15 remains later. The v1.2 milestone remains open.

- [x] **Phase 12: Preserve Existing Investing Under Portfolio Ownership** — keep the existing investing loop and financial evidence intact while every financial operation acquires an explicit portfolio target. (completed 2026-11-17 UTC)
- [x] **Phase 13: Create and Compare Independent Strategies** — create, name, fund, open and compare independent strategies with isolated financial activity. (completed 2026-11-19 UTC)
- [ ] **Phase 14: End Strategies Safely** — confirm terminal deletion, freeze records, support zero active portfolios and refuse stale or unauthorized targets.
- [ ] **Phase 15: Verify Exact Portfolio Recovery and Acceptance** — qualify the complete active/deleted lifecycle through exact recovery, compatibility and protected user journeys.

## Phase Details

### Phase 12: Preserve Existing Investing Under Portfolio Ownership

**Goal**: Existing users can keep investing in their first named portfolio with their actual finances and History preserved, while financial requests and authority are explicitly bound to that portfolio.
**Depends on**: Existing v1.1 local implementation and qualified recovery/CI baseline; Phase 7 live acceptance remains separately deferred and is not a prerequisite for isolated portfolio development.
**Requirements**: PFUND-03, PFIN-02, PFIN-03, PCTX-01, PVIEW-03, PSAFE-02, PSAFE-03
**Success Criteria** (what must be TRUE):

  1. An existing user opens their first named portfolio with exactly the prior cash, stored starting-cash baseline, holdings, basis, fills, event History and retry identities; no migration grant or reset occurs.
  2. The user sees the target portfolio name on tickets, confirmations, receipts and holding details, and can complete the existing crypto/stock preview, fill and original-receipt retry flows under unchanged execution rules; omitted, ambiguous or unavailable targets never select another portfolio.
  3. The user reads only the chosen portfolio's mixed paginated History and original-event details; identities, references and cursors cannot retrieve another portfolio's financial records.
  4. OTP sign-in, session refresh and sign-out work independently of zero, one or many financial portfolios in isolated fixtures; legacy financial requests cannot bypass explicit targeting or choose an ambiguous portfolio.
  5. The same investing journeys work on fresh and populated upgraded databases through restricted verified-TLS roles, with original financial payloads, immutable evidence and matching ownership constraints preserved; ordinary roles cannot gain broader mutation rights.

**Plans**: 31 completed plans (62 tasks, 21 dependency waves;
independent final verification8/8 with the owner-approved issue35 exception)

Plans:
**Wave 1**

- [x] 12-01-PLAN.md — Ownership proof oracles and fixture contracts

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 12-02-PLAN.md — Financial root and core row ownership models

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 12-03-PLAN.md — Stock and dividend ownership lineage models

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 12-04-PLAN.md — Finite immutable legacy association migrations

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 12-05-PLAN.md — Versioned root-aware stock SQL authority
- [x] 12-06-PLAN.md — Versioned root-aware dividend SQL authority

**Wave 6** *(blocked on Wave 5 completion)*

- [x] 12-07-PLAN.md — Final schema closure and explicit revision admission

**Wave 7** *(blocked on Wave 6 completion)*

- [x] 12-08-PLAN.md — Owned-active resolver and identity-only account services

**Wave 8** *(blocked on Wave 7 completion)*

- [x] 12-09-PLAN.md — Versioned identity HTTP and legacy OTP refusal
- [x] 12-10-PLAN.md — Explicit crypto execution and retry ownership
- [x] 12-12-PLAN.md — Root-specific stock journals and terminal split reconstruction

**Wave 9** *(blocked on Wave 8 completion)*

- [x] 12-11-PLAN.md — Explicit stock execution and gated retry ownership
- [x] 12-13-PLAN.md — Portfolio entitlement derivation and dividend worker safety

**Wave 10** *(blocked on Wave 9 completion)*

- [x] 12-14-PLAN.md — Scoped valuation and private mixed History
- [x] 12-16-PLAN.md — Restricted bootstrap and resumable migration-to-final path

**Wave 11** *(blocked on Wave 10 completion)*

- [x] 12-15-PLAN.md — Metadata discovery and final scoped route wiring

**Wave 12** *(blocked on Wave 11 completion)*

- [x] 12-17-PLAN.md — Exact portfolio recovery producer and consumer contracts
- [x] 12-19-PLAN.md — Identity and explicit browser target discovery

**Wave 13** *(blocked on Wave 12 completion)*

- [x] 12-18-PLAN.md — Current and retained isolated recovery lanes
- [x] 12-20-PLAN.md — Explicit scoped financial browser clients

**Wave 14** *(blocked on Wave 13 completion)*

- [x] 12-21-PLAN.md — Trade hook cache and unknown-attempt isolation
- [x] 12-22-PLAN.md — Valuation and History hook isolation
- [x] 12-23-PLAN.md — Scoped navigation and accessible target boundary

**Wave 15** *(blocked on Wave 14 completion)*

- [x] 12-24-PLAN.md — Trade surfaces and original-target receipts
- [x] 12-25-PLAN.md — Scoped holdings and mixed History surfaces

**Wave 16** *(blocked on Wave 15 completion)*

- [x] 12-26-PLAN.md — Browser proof harness and CI security/recovery graph

**Wave 17** *(blocked on Wave 16 completion)*

- [x] 12-27-PLAN.md — Full isolated source-bound security and recovery qualification

**Wave 18** *(blocked on Wave 17 completion)*

- [x] 12-28-PLAN.md — Owner acceptance of changed surfaces and native browser zoom

**Wave 19** *(after Wave 18; owner-approved risk disposition)*

- [x] 12-29-PLAN.md — Record exact owner-approved advisory deferral and follow-up issue35

**Wave 20** *(after successful Plan 29)*

- [x] 12-30-PLAN.md — Shared fail-closed audit exception, targeted tests and independent review

**Wave 21** *(blocked on successful Plan 30)*

- [x] 12-31-PLAN.md — Actual complete security and fresh same-archive recovery qualification

**Cross-cutting constraints (gap plans29–31):** The owner-approved exception
applies only to GHSA-fc5q-39xc-vjpf/current dependency hashes until2026-12-17UTC;
other HIGH/critical and invalid audit evidence remain blocking. Keep full raw
reports and historical failed receipts, with accepted-risk rather than fixed
labels. No dependency substitution/install occurs. Preserve owner UI/native200,
serial isolated DB proofs and Phase7 activation boundaries. Actual full
qualification and independent final goal verification passed; Phase12 is complete.

**UI hint**: yes

**Delivery boundary**: This is a runnable preservation slice across UI, API,
services and SQL authority. All financial writers and readers, including stock
journals, entitlements, payments, corrections and splits, must carry coherent
portfolio lineage before the one-account-per-user assumption is relaxed or
additional funded creation is enabled. Multi-portfolio and closed-lifecycle
fixtures prove that boundary without exposing incomplete management features.
The lifecycle model must already accommodate the approved freeze semantics;
deletion's user-facing activation belongs to Phase 14.

**Continuing obligations**: Owner checks, target-bound state, exact arithmetic,
per-portfolio stock-event effects and compatible lock order are foundational,
even where their full product requirement has a later primary owner. Qualify
each new schema revision's grants, recovery inventory and supported rollback/
refusal behavior in this phase. Do not defer these protections to Phase 15.

### Phase 13: Create and Compare Independent Strategies

**Goal**: Users can create, name, fund, open, trade and compare separate strategies without sharing capital, positions, financial effects or browser state.
**Depends on**: Phase 12
**Requirements**: PMGT-01, PMGT-02, PMGT-06, PFUND-01, PFUND-02, PFIN-01, PFIN-04, PCTX-02, PVIEW-01, PVIEW-02, PSAFE-07
**Success Criteria** (what must be TRUE):

  1. A user can create and rename up to ten active portfolios with approved name validation and owner-local case-insensitive active-name uniqueness, and add, view, edit or clear an optional plain-text description (empty is valid); each genuinely new portfolio, including a new user's “My portfolio,” receives its own $10,000 stored baseline and starting cash once.
  2. Uncertain creation retries, refreshes, sign-ins and renames never repeat a grant or create a second strategy; a retry for a deleted creation identity cannot recreate it, while a genuinely new identity may use a freed slot and name.
  3. Two portfolios of the same user can hold and trade the same crypto or stock with independent cash, quantities and basis; dividend eligibility, credits and corrections follow only each active portfolio's own historical ownership and apply once.
  4. The user compares active strategies in a stable overview showing name, cash, exact total or known value and dollar/percentage return against each stored baseline; detail and overview agree on timestamps and incompleteness, without a pooled wealth total or making other strategies unavailable.
  5. Switching portfolios isolates cached pages, cursors, actionable previews, pending attempts and late responses instead of retargeting them; requests and jobs remain bounded, creation has appropriate resource controls, shared market polling does not multiply, and existing activation/backup-capacity guards remain effective.

**Plans**: 18 checked plans (36 tasks,17 dependency waves; revision1 independent check passed with0blockers/0warnings). All18plans executed; actual full security/recovery, owner acceptance and independent phase-goal verification pass (5/5criteria,11/11requirements).

**Wave 1**

- [x] 13-01-PLAN.md — Expand and backfill canonical metadata and durable provenance

**Wave 2** *(blocked on declared earlier-plan dependencies)*

- [x] 13-02-PLAN.md — Install narrow serialized create, initialization and metadata authority

**Wave 3** *(blocked on declared earlier-plan dependencies)*

- [x] 13-03-PLAN.md — Admit only complete management schema with exact grants

**Wave 4** *(blocked on declared earlier-plan dependencies)*

- [x] 13-04-PLAN.md — Retain immutable source and produce exact successor recovery payload

**Wave 5** *(blocked on declared earlier-plan dependencies)*

- [x] 13-05-PLAN.md — Restore current and retained authority without losing retry evidence

**Wave 6** *(blocked on declared earlier-plan dependencies)*

- [x] 13-06-PLAN.md — Expose strict bounded private creation and metadata APIs

**Wave 7** *(blocked on declared earlier-plan dependencies)*

- [x] 13-07-PLAN.md — Share exact bounded valuation between overview and detail

**Wave 8** *(blocked on declared earlier-plan dependencies)*

- [x] 13-08-PLAN.md — Define strict browser management and overview transport
- [x] 13-14-PLAN.md — Prove newly created books invest and receive active events independently

**Wave 9** *(blocked on declared earlier-plan dependencies)*

- [x] 13-09-PLAN.md — Preserve creation intent and management coherence across refresh

**Wave 10** *(blocked on declared earlier-plan dependencies)*

- [x] 13-10-PLAN.md — Separate target authority from immutable unresolved orders

**Wave 11** *(blocked on declared earlier-plan dependencies)*

- [x] 13-11-PLAN.md — Guard comparison reads and invalidate scoped financial views

**Wave 12** *(blocked on declared earlier-plan dependencies)*

- [x] 13-12-PLAN.md — Build accessible overview and inline creation/metadata forms

**Wave 13** *(blocked on declared earlier-plan dependencies)*

- [x] 13-13-PLAN.md — Route overview and explicit native-select portfolio opening

**Wave 14** *(blocked on declared earlier-plan dependencies)*

- [x] 13-15-PLAN.md — Extend critical gates and revision-aware seven-stage qualification

**Wave 15** *(blocked on declared earlier-plan dependencies)*

- [x] 13-16-PLAN.md — Add real management browser journey and source-bound UI packet

**Wave 16** *(blocked on declared earlier-plan dependencies)*

- [x] 13-17-PLAN.md — Qualify complete frozen-source security and exact recovery

**Wave 17** *(blocked on declared earlier-plan dependencies)*

- [x] 13-18-PLAN.md — Obtain separate implemented UI and genuine native200 acceptance

**Cross-cutting constraints:** All DB-bearing tests, browser stacks and ops proofs use one serial disposable lane; wave8 frontend08 may run alongside DB14 only with disjoint ownership. Retain exact owner/key/payload funding retries, all-existing-user initialization, immutable0018+ migrations, restricted grants/TLS and source-bound current/retained recovery. Preserve original critical60 plus new critical paths at100%, all security/image gates and the exact issue35 scoped exception/expiry. Actual new UI and native200 acceptance remain separate blocking checks after implementation. Keep provider activation, public deletion/freeze and publication outside this planning authorization.

**UI hint**: yes

**Delivery boundary**: Enable additional funded creation only after Phase 12's
financial authority is qualified. Deliver the entire create/open/invest/overview
journey, including validated renaming, optional descriptions that can be left empty or
cleared, and private portfolio-specific links.
Creation tests may use retained closed fixtures to prove slot and retry behavior
before public deletion is available. Phase 14 then verifies the same contracts
through actual deletion and stale-tab journeys.

**Continuing obligations**: Keep Phase 12's isolation, authorization and immutable
retry/History rules effective under multiple portfolios. Implement active split
accounting correctly here even though the complete frozen-versus-active split
requirement is assigned to Phase 14. Extend exact recovery, grants and
compatibility for every newly supported state as it ships.

### Phase 14: End Strategies Safely

**Goal**: Users can end any strategy without altering other portfolios, losing retained evidence, receiving later financial effects or losing access to their user identity.
**Depends on**: Phase 13
**Requirements**: PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06, PCTX-03, PSAFE-01
**Success Criteria** (what must be TRUE):

  1. The user can cancel a named deletion confirmation without changes or confirm deletion of any owned portfolio, including holdings; repeated deletion does not affect another portfolio and deleted records disappear from ordinary financial views.
  2. Deletion has a tested committed boundary: earlier fills or financial jobs remain in the retained state, later cash/holding/History changes are refused, and previously earned unpaid dividends, later corrections and splits never advance the closed experiment or create liquidation/transfer events.
  3. Other active portfolios holding the same stock continue receiving only their own once-only splits with conserved basis and unchanged fills; retained frozen ownership remains reconstructable without poisoning instrument-wide consistency or later dividend/correction processing.
  4. Deleting the last portfolio leaves a signed-in empty overview with a Create portfolio action; login, refresh and ordinary reads do not recreate it, and explicit replacement creation receives a new identity without violating the ten-active limit.
  5. Direct IDs, stale links, cursors, original-event references and retry requests cannot reveal another owner's or deleted portfolio's finances; stale tabs explain unavailability and offer the overview without redirecting an order, while delete/trade/job races cannot overspend, duplicate effects or mutate a closed target.

**Plans**: 19 plans (38 tasks,15 dependency waves), independently checked; ready to execute.

**Wave 1**

- [x] 14-01-PLAN.md — Prepare finite successor test-owner harness, expand lifecycle evidence and backfill provenance

**Wave 2** *(blocked on declared earlier-plan dependencies)*

- [x] 14-02-PLAN.md — Install atomic named closure and permanent intent outcomes

**Wave 3** *(blocked on declared earlier-plan dependencies)*

- [x] 14-03-PLAN.md — Verify closure stock integrity and enforce terminal clock ordering

**Wave 4** *(blocked on declared earlier-plan dependencies)*

- [x] 14-04-PLAN.md — Admit complete closure schema with exact SQL/Python authority parity and repeated test bootstrap

**Wave 5** *(blocked on declared earlier-plan dependencies)*

- [x] 14-05-PLAN.md — Retain qualified0020 and produce complete lifecycle recovery

**Wave 6** *(blocked on declared earlier-plan dependencies)*

- [x] 14-06-PLAN.md — Restore lifecycle evidence before grants and refuse losing rollback

**Wave 7** *(blocked on declared earlier-plan dependencies)*

- [x] 14-07-PLAN.md — Expose strict original-intent private deletion API

**Wave 8** *(blocked on declared earlier-plan dependencies)*

- [ ] 14-08-PLAN.md — Keep unpaid and future financial effects outside frozen strategies
- [ ] 14-11-PLAN.md — Define strict deletion transport and durable browser original

**Wave 9** *(blocked on declared earlier-plan dependencies)*

- [ ] 14-09-PLAN.md — Prove stock continuity and management/trade closure races
- [ ] 14-12-PLAN.md — Keep deletion state outside financial target lifetime

**Wave 10** *(blocked on declared earlier-plan dependencies)*

- [ ] 14-10-PLAN.md — Fence every normal financial read and original retry at closure
- [ ] 14-13-PLAN.md — Revoke closed browser authority across reads, actions and tabs

**Wave 11** *(blocked on declared earlier-plan dependencies)*

- [ ] 14-14-PLAN.md — Build named inline deletion and signed-in recovery routes
- [ ] 14-15-PLAN.md — Adapt revision-aware fixtures and restricted TLS compatibility

**Wave 12** *(blocked on declared earlier-plan dependencies)*

- [ ] 14-16-PLAN.md — Extend critical gates and durable seven-stage qualification runner

**Wave 13** *(blocked on declared earlier-plan dependencies)*

- [ ] 14-17-PLAN.md — Exercise real deletion journeys and package source-bound UI evidence

**Wave 14** *(blocked on declared earlier-plan dependencies)*

- [ ] 14-18-PLAN.md — Qualify frozen-source security and exact lifecycle recovery

**Wave 15** *(blocked on declared earlier-plan dependencies)*

- [ ] 14-19-PLAN.md — Obtain separate owner UI and genuine native200 acceptance

**Cross-cutting constraints:** Dedicated sorted historical-stock gates before root; immutable original intent/policy and terminal freeze; strict owner/active/private reads; existing one-instrument financial guard;31-table/24-sequence successor0023 and immutable qualified0020/0017/older recovery. All DB-bearing tests/browser/ops use one serial disposable lane; disjoint frontend11–14 may overlap backend08–10/15 only. Preserve61critical modules plus new paths at100%, strict security/image gates and unchanged issue35. Source-frozen whole security then fresh seven-stage same-archive recovery; preserve prior qualified archives. Actual new owner UI and native200 outcomes remain separate execution checkpoints. Keep local; Phase7 activation/provider work, new packages, push/merge and production remain outside scope.

**UI hint**: yes

**Delivery boundary**: Complete the confirmed end-the-experiment policy through
the UI, API and financial authority together. Cash, quantities, basis and
financial History freeze at closure; shared market evidence can still evolve.
Preserve causal records and auditable lifecycle dispositions without continuing
hidden economic effects or adding a trash/restore feature.

**Continuing obligations**: Recheck creation/grant replay, portfolio switching,
owner isolation and event lineage against real terminal deletion. Prove active
and closed mixed-stock states under fresh/upgraded restricted TLS and exact
recovery before this lifecycle becomes eligible for release. No automatic
deletion/purge of retained evidence is included.

### Phase 15: Verify Exact Portfolio Recovery and Acceptance

**Goal**: Users and the operator can rely on the full strategy lifecycle after migration, recovery and supported rollback/refusal, with privacy and once-only financial effects preserved.
**Depends on**: Phase 14
**Requirements**: PSAFE-04, PSAFE-05, PSAFE-06
**Success Criteria** (what must be TRUE):

  1. An exact encrypted restore preserves active and frozen deleted portfolio identities, owners, closure state, baselines, cash, holdings, financial lineage and sequences, including migrated original data, same-symbol strategies and users with zero active portfolios; deleted portfolios do not reappear in normal screens.
  2. After restore, retried creation, fills and financial events cannot repeat a starting grant, trade or payment, cross a portfolio boundary or resume economic activity in a frozen portfolio.
  3. The operator can exercise the documented migration and supported rollback/refusal contract; incompatible older schemas or application versions refuse safely without merging strategies, reassigning money or discarding financial evidence.
  4. Full real isolated PostgreSQL concurrency/accounting and protected browser journeys verify create, rename, edit/clear optional descriptions, compare, switch, trade, History, delete and zero-active behavior, with original-data preservation, private access, human UI acceptance and the required coverage/security/image gates satisfied.

**Plans**: TBD
**UI hint**: yes

**Delivery boundary**: This phase supplies final integrated evidence for
protections already qualified in earlier slices. It is not permission to defer
financial ownership, migration/grant integrity, lifecycle consistency or
revision-specific recoverability until the end. Use isolated fixtures and
existing tools; any needed change outside approved package or operational scope
retains its separate review/approval gate.

## Requirement Coverage

Each of the 28 approved requirements has exactly one primary phase owner in the
detail sections and in [REQUIREMENTS.md](REQUIREMENTS.md). Cross-phase obligations
above preserve integrated behavior without duplicating primary ownership.

| Primary phase | Requirements owned | Success criteria |
|---|---|---|
| 12 | 7 | 5 |
| 13 | 11 | 5 |
| 14 | 7 | 5 |
| 15 | 3 | 4 |
| **Total** | **28/28** | **19** |

Mapping alone completes no requirement. Eighteen requirements are verified complete
(seven Phase12 and eleven Phase13); ten Phase14–15 requirements remain pending.
The phase structure was approved on2026-11-14. Phase14 planning is independently
checked; no Phase14 implementation or completion is claimed.

## Progress

**Approved execution order:** 12 → 13 → 14 → 15, with separate phase planning.
Phase12 execution, independent reviews and goal verification are complete.
The owner-approved unresolved picomatch advisory stays tracked in issue35;
actual complete security and fresh recovery pass under its scoped exception.
Phase13 is verified complete locally:18plans,11requirements, both owner checks and complete security/recovery pass. Phase14 is planned and ready to execute; Phase15 follows it.

| Phase | Milestone | Plans Complete | Status | Completed |
|---|---|---|---|---|
| 12. Preserve Existing Investing Under Portfolio Ownership | v1.2 | 31/31 | Complete locally; owner-accepted advisory in issue35 | 2026-11-17 UTC |
| 13. Create and Compare Independent Strategies | v1.2 | 18/18 | Complete locally; independent verification passed | 2026-11-19 UTC |
| 14. End Strategies Safely | v1.2 | 7/19 | Executing; Plan08 then11 next | - |
| 15. Verify Exact Portfolio Recovery and Acceptance | v1.2 | 0/TBD | Not started | - |

## Deferred Follow-up

The durable [carryover register](DEFERRED.md) stays separate from v1.2 scope.

- Phase 7 STOCK-01/02/03, DATA-01, MKT-01, SAFE-01: actual permitted live-data
  verification and acceptance remain unchecked/unverified; [audit](milestones/v1.1-MILESTONE-AUDIT.md).

- Applicable live action/status/retention prerequisites remain necessary before stock activation.
- The existing approved manual November 16 campaign remains bounded, with no automatic schedule;
  [original scope](phases/07-permitted-stock-discovery/07-LIVE-VERIFICATION-PROPOSAL.md).

- W09 metadata discipline and the previously accepted v1.0 W01–W08/four validation-record gaps remain in the [v1.1 audit](milestones/v1.1-MILESTONE-AUDIT.md) and [v1.0 audit](milestones/v1.0-MILESTONE-AUDIT.md).

Phase 07–11 directories, historical research and original manual-campaign links
remain in place. These six carried outcomes are not included in v1.2's 28
requirements and are not silently completed or reassigned. Local portfolio
acceptance never authorizes live provider calls or stock activation.

## Approval Boundary

**Roadmap status:** APPROVED by the owner on 2026-11-14.
Milestone setup is complete and the planning record may be committed locally.
Phases12–13 are complete locally. Phase14 planning is checked (19plans,38tasks,
15waves). Next: `$gsd-execute-phase 14`. This planning approval does not
itself start implementation, install dependencies, authorize push/merge,
operate providers, activate stocks or deploy production.
