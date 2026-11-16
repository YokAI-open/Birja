# Roadmap: Birja

## Milestones

- [x] **v1.0 Birja MVP** — shipped 2026-11-10 as software v0.4.0; [archive](milestones/v1.0-ROADMAP.md).
- [x] **v1.1 US Stock Trading** — closed 2026-11-14 with accepted live gaps: 63/64 plans, 130/132 tasks, 20/26 requirements locally satisfied; [archive](milestones/v1.1-ROADMAP.md).
- [ ] **v1.2 Multiple Strategy Portfolios** — 28 requirements and four-phase roadmap approved 2026-11-14; Phase 12 execution in progress locally.

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
at Phase 12. Phase 12 has 28 approved plans; fifteen plans are complete locally.
Plan07 installs actual0017 with passing restricted-role SQL, preservation/inventory
and schema-admission checks. Plan08 adds explicit root/identity service contracts;
Plan09 adds versioned identity HTTP/legacy refusal and Plan10 explicit crypto
transactions/HTTP. Plan12 adds owned journals, legacy/current digests and active
split effects with frozen siblings. Plans11/13/14 add scoped stock execution,
dividend workers and private valuation/History. Plan16 qualifies restricted final
bootstrap and authenticated fresh/retained/staged migration-to-final; production v2
composition, retained TLS/recovery and complete phase verification remain pending.
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

**Status:** APPROVED (2026-11-14). Phase 12 planning passed independent review; Phases 13–15 await planning.

- [ ] **Phase 12: Preserve Existing Investing Under Portfolio Ownership** — keep the existing investing loop and financial evidence intact while every financial operation acquires an explicit portfolio target.
- [ ] **Phase 13: Create and Compare Independent Strategies** — create, name, fund, open and compare independent strategies with isolated financial activity.
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

**Plans**: 28 plans (56 tasks, 18 dependency waves; independent planning verification passed)

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

- [ ] 12-15-PLAN.md — Metadata discovery and final scoped route wiring

**Wave 12** *(blocked on Wave 11 completion)*

- [ ] 12-17-PLAN.md — Exact portfolio recovery producer and consumer contracts
- [ ] 12-19-PLAN.md — Identity and explicit browser target discovery

**Wave 13** *(blocked on Wave 12 completion)*

- [ ] 12-18-PLAN.md — Current and retained isolated recovery lanes
- [ ] 12-20-PLAN.md — Explicit scoped financial browser clients

**Wave 14** *(blocked on Wave 13 completion)*

- [ ] 12-21-PLAN.md — Trade hook cache and unknown-attempt isolation
- [ ] 12-22-PLAN.md — Valuation and History hook isolation
- [ ] 12-23-PLAN.md — Scoped navigation and accessible target boundary

**Wave 15** *(blocked on Wave 14 completion)*

- [ ] 12-24-PLAN.md — Trade surfaces and original-target receipts
- [ ] 12-25-PLAN.md — Scoped holdings and mixed History surfaces

**Wave 16** *(blocked on Wave 15 completion)*

- [ ] 12-26-PLAN.md — Browser proof harness and CI security/recovery graph

**Wave 17** *(blocked on Wave 16 completion)*

- [ ] 12-27-PLAN.md — Full isolated source-bound security and recovery qualification

**Wave 18** *(blocked on Wave 17 completion)*

- [ ] 12-28-PLAN.md — Owner acceptance of changed surfaces and native browser zoom

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

**Plans**: TBD
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

**Plans**: TBD
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

No requirement is complete by mapping it. All 28 remain unchecked and pending;
the phase structure itself is approved on 2026-11-14; no implementation is complete.

## Progress

**Approved execution order:** 12 → 13 → 14 → 15, with separate phase planning.
No implementation has started.

| Phase | Milestone | Plans Complete | Status | Completed |
|---|---|---|---|---|
| 12. Preserve Existing Investing Under Portfolio Ownership | v1.2 | 15/28 | In progress; next12-15 by wave order | - |
| 13. Create and Compare Independent Strategies | v1.2 | 0/TBD | Not started | - |
| 14. End Strategies Safely | v1.2 | 0/TBD | Not started | - |
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
Next: `$gsd-discuss-phase 12` or `$gsd-plan-phase 12`. This approval does not
itself start implementation, install dependencies, authorize push/merge,
operate providers, activate stocks or deploy production.
