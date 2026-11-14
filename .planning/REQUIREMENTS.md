# Requirements: Birja

**Milestone:** v1.2 — Multiple Strategy Portfolios
**Defined:** 2026-11-14
**Status:** 28 requirements and four-phase roadmap approved, including the owner's optional-description amendment (2026-11-14); implementation not started
**Core value:** Make a trade at a real, recent market price and see what it is worth now, correct to the cent.

## v1.2 Requirements

Confirmed scope: ten active portfolios per user, independent $10,000 starting
cash per new portfolio, isolated strategy activity, a simple overview and
confirmed deletion even with holdings or the last portfolio. The owner also
confirmed that deletion ends the experiment and freezes it. The naming,
renaming and first-portfolio defaults below were approved as part of the full
27-requirement draft on 2026-11-14.
The owner subsequently added optional portfolio descriptions, bringing the
approved total to 28 without changing the four-phase structure.

### Portfolio management

- [ ] **PMGT-01**: User can create a named private portfolio while fewer than ten owned portfolios are active; deleted portfolios free a slot, and a replacement has a new permanent identity.
- [ ] **PMGT-02**: User can name and rename an active portfolio using a trimmed nonblank name of 1–60 characters without control characters; active names are unique for that owner under a documented case-insensitive normalization rule, and renaming changes no money or history.
- [ ] **PMGT-03**: User can delete any owned portfolio, including one with holdings, only after a confirmation identifies the portfolio and explains the effect; cancellation changes nothing and repeated deletion cannot affect another portfolio.
- [ ] **PMGT-04**: Deletion freezes that portfolio's committed cash, holdings and financial History, stops future dividend/split/correction effects on it, and preserves its financial records outside normal screens without creating liquidation trades or moving funds elsewhere.
- [ ] **PMGT-05**: User can delete their last portfolio and remain signed in with an empty overview and Create portfolio action; subsequent reads, refreshes and sign-ins do not silently create or fund another portfolio.
- [ ] **PMGT-06**: User can add, view, edit and clear an optional plain-text description for an active owned portfolio; an empty description is valid, existing/initial portfolios start with an empty description, and description changes do not change finances or History.

### Starting funds and preservation

- [ ] **PFUND-01**: Each genuinely new portfolio receives exactly $10,000 virtual cash and its own stored starting-cash baseline once; a brand-new user's initial portfolio is named “My portfolio” and receives that same single grant.
- [ ] **PFUND-02**: Retrying an uncertain creation cannot create another portfolio or repeat its starting grant, including after the originally created portfolio has been deleted; opening, renaming, refreshing or signing in grants no additional funds.
- [ ] **PFUND-03**: Existing users receive their first named portfolio with their actual prior cash, original starting-cash baseline, holdings, basis, immutable fills, event History and retry identities preserved; migration grants no new money and resets nothing.

### Independent financial activity

- [ ] **PFIN-01**: User has independent cash, holdings, quantities and cost basis in each portfolio, including when several portfolios own the same asset; crypto and stocks share cash only within their portfolio.
- [ ] **PFIN-02**: User can preview and execute existing crypto and stock orders in an explicitly targeted active portfolio with unchanged fee, quantity, quote freshness, eligibility and stock-activation rules; no unspecified or unavailable target silently selects another portfolio.
- [ ] **PFIN-03**: User retries an uncertain order only against its original portfolio and payload without duplicate execution or another portfolio's receipt; an original active-portfolio fill remains replayable under existing safe-retry rules.
- [ ] **PFIN-04**: Each active portfolio's dividend eligibility, credits and corrections use its own historical ownership and cash, apply once, and remain attributable to that portfolio when the same user holds the stock in other portfolios.
- [ ] **PFIN-05**: Each active portfolio receives only its own verified split effects with preserved total basis and unchanged historical fills; frozen deleted portfolios remain consistent at closure and cannot disrupt another portfolio's later stock accounting.
- [ ] **PFIN-06**: Concurrent creation, deletion, trades and financial jobs cannot exceed ten active portfolios, duplicate grants/events, overspend a portfolio, mutate a portfolio after its deletion boundary or move an operation into a different strategy.

### Portfolio context and navigation

- [ ] **PCTX-01**: User sees the target portfolio's name on trade tickets, confirmations, receipts, holding details and History so each action's strategy is clear.
- [ ] **PCTX-02**: Switching portfolios or deleting one invalidates its actionable previews and isolates cached pages, cursors, late responses and pending attempts; an old tab or unresolved request never becomes an order or financial display for the newly selected portfolio.
- [ ] **PCTX-03**: User can open an active portfolio from the overview and navigate its holdings, trading and History through stable portfolio-specific links; a stale/deleted link explains unavailability and offers the overview without exposing retained financial records.

### Strategy overview and statements

- [ ] **PVIEW-01**: User sees every active portfolio's name, cash, total or known value, and dollar/percentage return against its own stored starting cash in a stable overview order; deleted portfolios are excluded and no pooled cross-portfolio wealth total is introduced.
- [ ] **PVIEW-02**: Portfolio detail and overview use the same exact valuation rules, source times and completeness semantics; missing or uncertain prices produce explicit incomplete values and unavailable overall returns for that portfolio without making other portfolios unavailable.
- [ ] **PVIEW-03**: User sees only the chosen active portfolio's private, deterministically paginated crypto/stock/dividend/split/correction History and original-event details; cursors and references cannot cross portfolios.

### Privacy, compatibility and acceptance

- [ ] **PSAFE-01**: Every portfolio operation and financial object lookup enforces owner and active-state authorization on the server, including guessed IDs, old references, cursors and direct trade/retry requests; other owners' and deleted portfolios' finances remain unavailable through normal APIs.
- [ ] **PSAFE-02**: User identity, OTP sign-in, session refresh and sign-out work independently of having zero, one or many portfolios; legacy financial requests cannot choose an ambiguous portfolio or bypass explicit targeting.
- [ ] **PSAFE-03**: Fresh and migrated portfolio services retain restricted PostgreSQL roles, verified TLS, immutable financial evidence and matching ownership constraints; migration preserves existing financial payloads and does not broaden ordinary mutation privileges.
- [ ] **PSAFE-04**: Operator can exactly restore active and frozen deleted portfolios, ownership/lifecycle state, baselines, grants, financial lineage and retry protections from an encrypted backup without resurrecting a deleted strategy or repeating grants, fills or payments.
- [ ] **PSAFE-05**: Operator has a tested migration and rollback/refusal contract for supported retained schemas and application versions; incompatible older applications cannot silently merge strategies, reassign money or discard financial history.
- [ ] **PSAFE-06**: Real isolated PostgreSQL concurrency/accounting tests and browser journeys verify the full multi-portfolio loop, deletion races, original-data preservation and private access; required coverage, security, image and human UI acceptance gates remain enforced.
- [ ] **PSAFE-07**: Portfolio requests and financial jobs remain bounded, portfolio creation reuses appropriate rate/resource controls, and portfolio count does not multiply shared market-data polling or bypass existing backup-capacity and stock-activation safeguards.

## Acceptance interpretations

- All grants, balances, quantities, basis and returns retain existing Decimal /
  NUMERIC precision and string JSON transport; returns use the stored baseline,
  including a migrated baseline that differs from $10,000.
- New-user onboarding creates only the initial portfolio. An existing user who
  intentionally deleted all portfolios stays at zero until explicitly creating
  a new one. The default migrated/initial label is “My portfolio,” and may be renamed.
- Ten is an active-count limit, not a lifetime creation limit. Reusing a deleted
  name is allowed for a newly created identity; another user may use the same name.
- Confirmed deletion is terminal in the normal app: no restore/trash UI. A fill
  or financial job committed before closure remains in the frozen state; later
  effects, including previously earned but unpaid dividends and later negative
  corrections, do not change the closed experiment. Preserve their causal
  records and lifecycle disposition without redirecting value to an active book.
- Read access to deleted financial records remains blocked even for a prior
  retry or original-reference URL. An old request cannot recreate the strategy
  or spend a replacement portfolio's starting cash. Internal retained evidence
  still supports exact recovery and integrity checks.
- Shared market evidence can continue updating globally; the deleted portfolio's
  cash, quantities, basis and financial History do not advance. Lifecycle-aware
  reconstruction must distinguish its closure state from active stock unit epochs.
- Overview return is since that portfolio began, not annualized or a ranking of
  strategies with different start dates. Incomplete portfolios show known value
  and a clear unavailable return rather than zero or a misleading complete total.
- Each runnable implementation phase must qualify its own new schema, financial
  authority and recovery compatibility. The final integrated proof supplements
  earlier phase checks; it does not defer safety until release.

## Carried deferred work — outside v1.2 committed scope

STOCK-01/02/03, DATA-01, MKT-01 and SAFE-01 remain unchecked and unverified from
v1.1. Their original primary phase remains Phase 7; they are not counted as new
v1.2 requirements or silently reassigned to a new phase. See
[DEFERRED.md](DEFERRED.md), [archived requirements](milestones/v1.1-REQUIREMENTS.md)
and the [v1.1 audit](milestones/v1.1-MILESTONE-AUDIT.md).

Live stock collection/execution admissions remain gated. The existing bounded
November 16 manual campaign stays at its original path and authorization; no
provider calls, new schedule or repeat campaign follows from this milestone.
Production rollout remains separate. Last confirmed production is v0.4.0/schema0008;
milestone planning has not inspected or changed it.

## Future requirements

- Historical performance charts and time-normalized strategy comparison.
- Portfolio cloning/templates or configurable starting capital, if later selected.
- Separate follow-up on accepted v1.0 W01–W08, v1.1 W09 and historical validation debt.

## Out of scope

| Feature | Reason |
|---|---|
| Transfers between portfolios | Owner chose independently funded strategies; transfers need additional cash-flow and return policy |
| Resetting an existing portfolio or editable deposits | Create a new strategy identity; retain the prior experiment's records |
| Pooled wealth total, leaderboard or sharing | This milestone compares private independent strategies, not a combined capital pool |
| Forced liquidation or physical ledger deletion | Deletion freezes retained records and does not manufacture financial events |
| Continuing hidden dividends/splits/corrections after deletion | Owner explicitly chose to end the experiment and freeze at deletion |
| Deleted-portfolio restore/trash/export features | Not selected; retained evidence serves integrity/recovery rather than normal access |
| New market-data providers, packages or asset classes | Existing stack/capabilities suffice; any needed package change requires its own review |
| Live stock activation, provider operations or production deployment | Deferred prerequisites and explicit operational approvals remain separate |

## Traceability

Requirements and four-phase roadmap approved on 2026-11-14.
Numbering continues at Phase 12. Each of these 28 requirements has exactly one
approved primary phase owner; cross-phase obligations remain explicit in the
roadmap. No mapping is an implementation or completion claim.

| Requirement | Primary phase | Status |
|---|---|---|
| PMGT-01 | Phase 13 | Pending |
| PMGT-02 | Phase 13 | Pending |
| PMGT-03 | Phase 14 | Pending |
| PMGT-04 | Phase 14 | Pending |
| PMGT-05 | Phase 14 | Pending |
| PMGT-06 | Phase 13 | Pending |
| PFUND-01 | Phase 13 | Pending |
| PFUND-02 | Phase 13 | Pending |
| PFUND-03 | Phase 12 | Pending |
| PFIN-01 | Phase 13 | Pending |
| PFIN-02 | Phase 12 | Pending |
| PFIN-03 | Phase 12 | Pending |
| PFIN-04 | Phase 13 | Pending |
| PFIN-05 | Phase 14 | Pending |
| PFIN-06 | Phase 14 | Pending |
| PCTX-01 | Phase 12 | Pending |
| PCTX-02 | Phase 13 | Pending |
| PCTX-03 | Phase 14 | Pending |
| PVIEW-01 | Phase 13 | Pending |
| PVIEW-02 | Phase 13 | Pending |
| PVIEW-03 | Phase 12 | Pending |
| PSAFE-01 | Phase 14 | Pending |
| PSAFE-02 | Phase 12 | Pending |
| PSAFE-03 | Phase 12 | Pending |
| PSAFE-04 | Phase 15 | Pending |
| PSAFE-05 | Phase 15 | Pending |
| PSAFE-06 | Phase 15 | Pending |
| PSAFE-07 | Phase 13 | Pending |

**Coverage:** 28/28 approved requirements mapped exactly once to approved Phases
12–15; zero orphaned or duplicate primary owners. All remain unchecked/pending.
Six carried Phase 7 requirements remain separately deferred, not completion claims.

## Research and decision evidence

- [v1.2 research summary](research/v1.2/SUMMARY.md), with four detailed reports
  and official documentation/source references; historical v1.1 research stays intact.
- Owner confirmed the v1.2 milestone scope, Phase 12 numbering and research first.
- Owner confirmed $10,000 per portfolio, ten active portfolios, deletion with
  holdings/last portfolio, simple cash/value/return overview, and freeze at deletion.
- Name/rename validation, distinct active names and first-portfolio onboarding
  defaults were explicitly approved with the full requirements draft on 2026-11-14.
- Owner subsequently requested portfolio naming and optional descriptions on
  2026-11-14. Naming remains covered by PMGT-02; PMGT-06 adds editable/clearable
  descriptions to Phase 13, with empty descriptions explicitly allowed.
- No requirement is completed by drafting this document. Requirements approval
  does not authorize implementation, dependency changes, pushing, provider
  operations, protected merges or deployment.

---
*Last updated: 2026-11-14 after research synthesis and confirmed deletion policy;
all 28 requirements and the four-phase roadmap approved, including optional descriptions; implementation not started.*
