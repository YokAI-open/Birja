---
phase: 08-corporate-action-safe-ownership
verified: 2026-11-11T18:05:50Z
status: passed
score: 28/28 must-haves verified
roadmap_score: 5/5
plan_truths_checked: 38/38
overrides_applied: 0
verification_scope: approved isolated local Phase 8 boundary
source_head: 507196d
runtime_gate_source: 0026053
live_activation: deferred-by-owner-disabled-unverified
stock_execution: disabled
deferred:
  - truth: Actual stock fills, timely halt/status authority and combined portfolio consume these safeguards from the first fill.
    addressed_in: Phase 9
    evidence: Roadmap Phase 9 dependency and success criteria 2, 3 and 5 require entitlement/action ordering, current eligibility and incomplete uncertain valuations.
  - truth: Dividend cash, once-only payments, post-payment corrections and public mixed-event History are delivered.
    addressed_in: Phase 10
    evidence: Roadmap Phase 10 success criteria 1–4 own DIV-03, DIV-04, DIV-05 and HIST-03.
  - truth: Complete stock-trading/payment journeys and the resulting final mixed-asset ledger receive rollout acceptance.
    addressed_in: Phase 11
    evidence: Roadmap Phase 11 success criteria 1–3 own final SAFE-02/SAFE-03 acceptance; feature-local Phase 8 restore and concurrency proof already exists.
---

# Phase 8: Corporate-Action-Safe Ownership Verification Report

**Phase Goal:** Stock owners' units, basis and dividend eligibility remain explainable through ordinary events, and uncertain events prevent unsafe trading or valuation.
**Verified:** 2026-11-11T18:05:50Z
**Status:** passed — approved isolated local boundary
**Re-verification:** No — initial verification; no previous `*-VERIFICATION.md` existed.

The local phase goal is achieved. This verdict does **not** establish live action-product permission, operational suitability, current production monitoring, stock execution or deployment readiness. The roadmap explicitly requires Phase 8 ownership behavior to be demonstrated on isolated seeded historical holdings while stock execution remains disabled. Plan 13 permits owner deferral of distinct live gates. The actual owner accepted the new UI and selected “Defer live activation; continue locally (Recommended).” Neither answer substitutes for implementation evidence.

Verification started from the five roadmap success criteria returned by `gsd-sdk query roadmap.get-phase 8 --raw`, then checked all 38 PLAN truth declarations. Repeated claims were merged into the 28 observable obligations below: the five roadmap contracts retain their wording; additional rows capture distinct technical/acceptance obligations. The plan inventory below accounts for every original declaration. No verification override was needed or applied. The phase is not in MVP mode.

## Goal Achievement

### Observable Truths

All statuses in this table are **VERIFIED** within the stated local boundary. A failed truth would be a BLOCKER; an uncertain current-phase truth would be a WARNING requiring a decision. Neither classification remains open.

| # | Truth | Status | Actual evidence |
| --- | --- | --- | --- |
| 1 | Operator can inspect retained ordinary USD dividend announcement identities, dates, rates and revisions; regular rechecks detect changes, while conflicting, incomplete or cancelled information stays pending instead of producing guessed entitlements. (DIV-01) | VERIFIED | Nine durable models retain source IDs, immutable revision terms and observations. `corporate_actions.py:274` fingerprints terms, preserves source/economic/observed instants, appends ordinals, records missing IDs and holds conflicts. `stock_actions.py` discovers inclusive process-date segments and separately rechecks retained IDs. Operator SELECT grants cover retained evidence; private inspection is deliberately sanitized. Real revision/recheck/held-entitlement assertions in `test_corporate_actions.py:352,414,886,904,945` and `test_stock_action_monitoring.py:349`. |
| 2 | Given a verified cutoff and historical holdings, the user earns only the eligible quantity: buying afterward does not qualify and selling afterward does not erase it. Processed splits are accounted for and eligibility remains reconstructible; Phase 9 must preserve this history from its first fill. (DIV-02) | VERIFIED | `stock_ownership.py:548` reconstructs strict economic `< cutoff`, explicit split epochs and boundary units after complete journal validation; `corporate_actions.py:822` includes journal users, prior entitlement users and current holders. Actual late-buyer/departed-seller assertions at `test_corporate_actions.py:736`; exact-cutoff/sold-out/split reconstruction at `test_stock_ownership.py:252,263,293`; five split/dividend order cases at `test_corporate_actions.py:555`. Phase 9 integration remains an explicit future dependency. |
| 3 | A verified straightforward forward split adjusts supported whole-share holdings once, conserves total basis, changes unit basis correctly and leaves original fills unchanged. Fractional or ambiguous entitlements do not use this automatic path. (ACT-01, ACT-03) | VERIFIED | `plan_forward_split` uses exact Fraction arithmetic, validates every owner and returns unchanged total basis. `apply_due_actions` validates all owners before one application, journal and unit transition; it never assigns Trade or cash. `append_stock_movement` only changes quantity for a split and checks basis equality. Real 4:1/integral 3:2/zero-owner/fractional/overflow, replay and all-owner rollback assertions at `test_corporate_actions.py:1030–1160`. Unit basis follows exact total basis/adjusted quantity; no rounded unit basis overwrites total basis. |
| 4 | User sees affected stocks suspended and uncertain valuations unavailable for unsupported/disputed actions or insufficient monitoring; only verified auditable reconciliation restores availability, without guessed liquidation or cash-in-lieu. Other eligible instruments and crypto remain independent. (ACT-02, ACT-03) | VERIFIED | Immutable unresolved historical revisions/missing observations feed shared `action_hold_queries`; source recovery cannot remove them. `stocks.py` final committed action projection suppresses quotes and timestamps while preserving catalogue identities. `StockSection` renders fixed suspension/valuation copy independently of stock status/session and crypto. Narrow resolution advances epoch and requires fresh monitoring/quote authority afterward. Actual API, client, RTL and browser assertions, plus accepted owner presentation; no liquidation or cash-in-lieu code path. |
| 5 | Event replay or recovery cannot repeat a split or reorder it across trades and dividend eligibility. Defined monitoring-loss/recovery behavior is demonstrable on isolated seeded holdings before stock execution is enabled. (ACT-03, DIV-02) | VERIFIED | Shared transaction advisory gate, causal/trade/application/sequence uniqueness and complete unit checks serialize effects. Inclusive mutation replay returns its original revision without rewinding current state. Real concurrent processor/causal races, rollback, cutoff and freeze races assert results. Retained encrypted restore replays real split and operator services twice; unchanged application/resolution identities and counts asserted by `RECOVERY_REPLAY_SCENARIO`, `ops-fixtures.py:2035`. Final operations receipt records successful six-revision roundtrip and actual TLS consumers. |
| 6 | Existing balances, starting cash, identities, holdings/basis and crypto fills survive additive migrations. | VERIFIED | 0011 adds accounting without rewriting legacy financial data; populated downgrade refuses before alteration. Actual populated/fresh role/TLS and exact predecessor recovery fixtures compare original financial rows, schema and identities. Existing trading remains crypto-scoped and full backend/browser receipts include crypto buy/sell/portfolio/history. |
| 7 | Runtime cannot grant provider permission, mint operator approval or rewrite immutable accounting; scheduler quantity access cannot change basis/cash/fills. | VERIFIED | 0011/bootstrap grant append/state/current-pointer access and `UPDATE(quantity)` only on holdings; six immutable trade columns are SELECT-only. 0012 revokes PUBLIC function execution and grants only a separate NOLOGIN operator. Actual SQLSTATE42501 tests and final populated/fresh TLS consumers exercise denials; runtime has no operator membership. |
| 8 | Quote-unit schema compatibility preserves epoch-zero writes and only the completed gate-bound writer admits nonzero units. | VERIFIED | `stock_quotes.py` explicitly maps provider fields plus local unit epoch; no blind ORM/asdict mapping. Final insert proof requires current gated units and authentic applied boundary. Original zero/nonzero guard regressions remain, and Plan 09 legitimately replaces the temporary nonzero refusal with substantive provenance checks. |
| 9 | Every supported 0007–0012 schema restores exactly, including identities, financial duplicate state and 0012 function authority; predecessor contracts do not drift. | VERIFIED | Producer explicit six-revision dispatch, complete accounting columns/schema and archive-derived sequence states; consumer imports producer and checks exact canonical state. Independently pinned function definition/ACL/role checks prevent self-reported authority acceptance. Own-process offline contracts passed seven active cases; retained explicit real-SQL receipt executes all ten. Actual encrypted roundtrip, authority corruption refusals and replay receipt checked; archive SHA independently matches. |
| 10 | Collection/replay is bounded and unrelated received symbols are discarded before persistence. | VERIFIED | `ActionBudget` bounds actual attempts/pages/response/cumulative bytes/time/frames/mutations. Fixed distinct HTTPS REST/stream origins, no redirect/encoding acceptance, finite historical terminal contract, bounded continuation/retries. `_normalize` validates then filters curated mappings; replay all-US ingress requires separate admission. HTTP-boundary adversarial tests assert actual body/attempt limits. |
| 11 | Source deletion and missing known records remain distinguishable. | VERIFIED | Known-ID absence emits `missing_or_uncertain` coverage/observation and preserves prior revision. Replay delete is a distinct mutation/cancelled fact; no absent page/ID synthesizes deletion. `test_ingest_known_missing_preserves_revision_and_audits` and retained-ID monitor recovery test check persistent uncertainty. |
| 12 | Quote permission cannot authorize retained action accounting. | VERIFIED | `stock_admission.py:225` separately requires actions feed, REST/replay capability, exact twenty symbols, all-US ingress where applicable and explicit durable accounting/backup retention rights. Every collector/accounting entry point re-evaluates its own purposes/scope/generation. Original IEX-only admission is refused by regression. |
| 13 | Split/fill-like/freeze/quote/resolution operations share instrument-first ordering and fresh post-wait economic time. | VERIFIED | `acquire_stock_gate` uses fixed `birja.stock.instrument:` hash namespace, READ COMMITTED and bounded timeouts; movements lock account then sorted holdings and use DB `clock_timestamp` after waits. SQL resolution uses exactly the same lock expression. Actual PostgreSQL lock witnesses test both freeze/fill and quote/split orders. |
| 14 | Missing historical coverage or inconsistent causal/unit history holds rather than substituting current quantity. | VERIFIED | `assert_ownership_consistent` validates baseline, contiguous global sequence, immutable fill economics, all owners including departed/zero owners, full split transitions and current holdings sums. Reconstruction rejects future/missing coverage and ambiguous units. Tests deliberately corrupt baseline/sequence/causes/units/holdings. |
| 15 | Late/conflicting/cancelled/reappearing revisions retain immutable history and cannot inverse or reapply financial effects. | VERIFIED | `persist_action_batch` holds suspected aliases, late effective events, changed applied revisions and reappearing old facts; current pointer/observations retain audit. Applied economic-event UNIQUE and hold checks prevent another split. Historical mutation A after B returns A's stored result without changing B; divergent reuse fails. |
| 16 | Entitlement revisions are immutable, lineage-linked and cannot expose an obsolete eligible snapshot as current. | VERIFIED | `derive_dividend_entitlements` appends `version`/`supersedes_id`, retains cutoff rule, units/sequence and historical quantity; `latest_verified_entitlements` selects newest per owner matching current revision and excludes held/cancelled replacement. Actual revision/sale/monitor-loss-recovery assertions at `test_corporate_actions.py:736–830`. No cash or History publication. |
| 17 | Disabled stock actions need no client/credentials and cannot block the independent crypto scheduler. | VERIFIED | Config defaults actions false and requires reviewed baseline/keys when enabled; existing `scheduler.amain` independently builds crypto, quote and action callbacks in TaskGroup, with separate leases/cadences and bounded failures/cancellation. Shared actual account quota reservations include failures/retries. Config/scheduler/concurrent quota/cancellation assertions and current full receipts support wiring. |
| 18 | A verified supported dispute can be reconciled through evidence-bound limited authority without blanket unfreeze. | VERIFIED | Protected typed CLI→Python service→0012 fixed SECURITY DEFINER function binds exact validated action/calendar snapshots, event/revision/generation/epoch/ledger/unit/history/observation/security facts. Allowed prospective decisions append audit, do not alter financial rows, and set reconciling/null validity. Stale/arbitrary evidence, changed applied events, actual unsupported repair and runtime invocation refuse. |
| 19 | Current responses use final committed action, permission and reconciliation facts. | VERIFIED | `stocks.py:262` uses bounded final READ COMMITTED core projections and fresh UTC after final await, then synchronous response construction. Missing/malformed/denied/generation-mismatched action/calendar authority becomes generic epoch0/null time, without stale ORM promotion. Same-request committed-change tests assert the whole authority envelope. |
| 20 | Post-split prices come from genuine new-unit source observations, not arithmetic adjustment or fetch-time relabelling. | VERIFIED | `stock_quotes._unit_authority` requires exact applied/current revision boundary and source event strictly after it; equality/old events refuse. API compares local stored/current unit epochs and exact boundary. Real quote/split races, revocation/age-crossing waits and actual apply→new quote→API integration assertions exist. |
| 21 | Delayed, equal-time, lower-generation or lower-epoch client responses cannot undo a newer suspension. | VERIFIED | Strict parser precedes TanStack cache insertion. QueryClient/auth-lifecycle guard retains raw per-instrument epoch/exact-time, approved admission generation and monotonic clock separately from sanitized public cache. Late generic denial may reduce authority but cannot restore independent metadata or erase raw high-waters. Actual client regression assertions cover cache removal/remount and auth change. |
| 22 | Known safety deadlines remove cached and displayed numbers at equality without waiting for polling. | VERIFIED | `nextDeadline`, `purgeExpired` and `projectStocks` use nearest deadline timeout, monotonic elapsed plus full measured RTT, conservative submillisecond rounding and focus/visibility catch-up. Source 120s, action, calendar/session and disclosure expiry purge numbers; original transport/source anchors survive repeated projection. Exact millisecond fake-clock and real browser boundary assertions exist. |
| 23 | Client clocks only remove server authority and never establish safety. | VERIFIED | Projection requires approved server admission, reviewed session and current action; upper bound can only expire facts. Unknown/held states are never promoted locally. No browser wall-clock recovery or adjusted stock price exists. Parser requires execution false and coherent amounts/source/session/action facts. |
| 24 | Action health, unknown halt status and phase-disabled trading remain independent visible facts. | VERIFIED | Backend schema uses fixed unknown StockStatus and `execution_enabled: Literal[False]`; trading service only resolves crypto. Component separately renders Corporate actions, Stock status unverified and Trading coming later, with no stock Buy/Sell/Resolve control. Unsafe numbers and source times are absent. |
| 25 | Mobile/desktop warnings and retry flows remain readable and accessible within the existing design system. | VERIFIED | Semantic checked/source times, wrapping warnings/badges, one contextual polite atomic live region and retained manual retry focus; no background focus movement. Actual 320/375/768/1280 and CSS200%/640CSS reflow evidence with cell overflow assertions; inspected mobile capture shows readable fixed warning/Unavailable. Existing UI review 24/24 and explicit owner approval are already recorded. |
| 26 | Local accounting/authority behavior has real isolated proof under unchanged CI, coverage and security gates. | VERIFIED | Inspected guard, real SQL assertion bodies and raw full receipts: backend 1551/99.82%; exact 29 critical modules 2972 statements/978 branches 100%; frontend 429; browser 31 plus expected CSP skip; native 77; strict five-image scans all zero HIGH/CRITICAL including unfixed. CI/CLAUDE/test exact critical mirror is substantive and reviewed. |
| 27 | Owner reviews concrete new safety presentation after automated proof. | VERIFIED | Actual screenshot links and source hash in `08-HUMAN-UAT.md`, owner response “Approve the Phase 8 UI.” at 01ab6d3; browser source receipt matches current relevant runtime hashes. This is presentation acceptance, not a claim of repeated manual financial testing. |
| 28 | Deferred live prerequisites remain visible and disabled while authorized isolated work continues. | VERIFIED | `08-ACTIVATION.md` records actual owner deferral at 80a2567, separately lists REST/replay/durable derived/DB/backup/display/quota/history/deletion/latency prerequisites and no call-ready campaign. Default disabled config, action authority checks and permanently disabled stock execution enforce the boundary. No external permission inferred. |

**Score: 28/28 merged must-haves; all 5/5 roadmap criteria and all 38/38 original plan truth declarations checked.**

### Complete PLAN Truth Inventory

Original declarations are abbreviated only for legibility; plan number and position identify the exact frontmatter text. Repeated declarations map to the already-scored obligations above and do not inflate the score.

| Plan/truth | Declaration | Status | Evidence rows |
| --- | --- | --- | --- |
| 01.1 | Legacy balances/IDs/fills unchanged | VERIFIED | 6 |
| 01.2 | Economic split/ownership causes cannot duplicate | VERIFIED | 3, 5, 13 |
| 01.3 | Runtime cannot grant permission/operator resolution | VERIFIED | 7, 12, 18 |
| 01.4 | Epoch-zero compatibility; nonzero closed until gated writer | VERIFIED | 8, 20; temporary guard superseded by completed Plan 09 |
| 02.1 | Restored actions/ownership preserve duplicate state | VERIFIED | 5, 9 |
| 02.2 | Old revisions recover without contract drift | VERIFIED | 9 |
| 03.1 | Unknown currency/conflicting dates cannot earn guessed dividend | VERIFIED | 1, 2, 12, 16 |
| 03.2 | Only exact supported forward ratios apply | VERIFIED | 3 |
| 03.3 | Quote permission cannot authorize retained actions | VERIFIED | 12 |
| 04.1 | Incomplete pages cannot renew health | VERIFIED | 4, 10, 17 |
| 04.2 | Deletions distinguishable from missing records | VERIFIED | 11 |
| 04.3 | No unbounded polling/stream/unrelated retention | VERIFIED | 10 |
| 05.1 | Cutoff purchases/sales use historical ownership | VERIFIED | 2 |
| 05.2 | Split/fill/freeze share lock order | VERIFIED | 13 |
| 05.3 | Missing history held, never today's quantity | VERIFIED | 14 |
| 06.1 | One immutable economic application and exact basis | VERIFIED | 3, 5 |
| 06.2 | Entitlements survive sales/revisions | VERIFIED | 2, 16 |
| 06.3 | Late/conflicting changes create persistent holds | VERIFIED | 15 |
| 07.1 | Monitoring loss makes valuation unavailable | VERIFIED | 4, 19, 22 |
| 07.2 | Catch-up cannot erase event hold | VERIFIED | 4, 15, 18 |
| 07.3 | Independent default-disabled collection preserves crypto | VERIFIED | 17 |
| 08.1 | Supported dispute reconciles without blanket unfreeze | VERIFIED | 18 |
| 08.2 | Runtime/source success cannot mint approval | VERIFIED | 7, 18 |
| 08.3 | Resolution authority/audit survive exact restore | VERIFIED | 9 |
| 09.1 | Unsafe prices disappear; catalogue/crypto remain | VERIFIED | 4, 19, 24 |
| 09.2 | Holds/resolutions affect final authority boundary | VERIFIED | 19 |
| 09.3 | Post-split prices use real new-unit observations | VERIFIED | 20 |
| 10.1 | Delayed response cannot undo suspension | VERIFIED | 21 |
| 10.2 | Deadlines remove numbers immediately | VERIFIED | 22 |
| 10.3 | Client clocks only reduce safety | VERIFIED | 23 |
| 11.1 | Affected stock unavailable; crypto usable | VERIFIED | 4, 24 |
| 11.2 | Action state neither advertises trading nor hides halt uncertainty | VERIFIED | 24 |
| 11.3 | Mobile/desktop readable and accessible | VERIFIED | 25 |
| 12.1 | Real isolated proof under existing gates | VERIFIED | 26 |
| 12.2 | All six revisions preserve financial/duplicate state | VERIFIED | 9 |
| 12.3 | Concrete acceptance evidence and accurate activation gates | VERIFIED | 27, 28 |
| 13.1 | Owner reviews concrete states after proof | VERIFIED | 27 |
| 13.2 | Deferred live gates visible; authorized local work continues | VERIFIED | 28 |

## Required Artifacts

`gsd-sdk query verify.artifacts` was run for **every one of the 13 plans**: **30/30 artifact declarations passed** existence/substantive heuristics. The following manual checks verify actual behavior and consumers; file existence alone was not accepted. Repeated proof/UAT declarations are grouped.

| Artifact | Expected | Status | Substantive implementation and wiring |
| --- | --- | --- | --- |
| `backend/alembic/versions/0011_stock_action_accounting.py` | Additive constrained accounting | VERIFIED | Nine concrete tables, composite causal FKs, exact uniqueness, safe money/units, guarded populated downgrade and narrow grants; actual migration/role tests. |
| `backend/app/models/corporate_action.py` | Nine typed durable models | VERIFIED | Concrete SQLAlchemy columns/constraints; registered in models/__init__, imported by ownership/actions/monitor/API/reconciliation. |
| `deploy/backup-snapshot.py` | Exact revision producer | VERIFIED | Explicit 0007–0012 columns/schema/function/identity contracts; used by retained backup and restore consumer. |
| `deploy/verify-restore.py` | Compatible exact restore consumer | VERIFIED | Imports canonical producer, checks manifest/state/authority, quarantined fixed-role restoration; actual encrypted/SQL corruption/replay proof. |
| `deploy/tests/test-db-operations.sh` | Real operation driver | VERIFIED | Calls actual ops fixture lanes, not a narration-only probe. Existing retained wrapper invokes identical bundle/roundtrip/roles/TLS functions; final receipt and archive checked. |
| `backend/app/services/corporate_action_rules.py` | Pure exact economics | VERIFIED | Implemented classification, genuine calendar cutoff, Fraction all-owner split plan; called by actions and reconciliation. Own-process behavior passed. |
| `backend/app/services/stock_action_rules.py` | Fail-closed safety decision | VERIFIED | Concrete persistent-hold precedence, health/coverage/deadline/units checks; called by final API. |
| `backend/app/services/alpaca_actions.py` | Bounded REST/known-ID/replay | VERIFIED | Actual fixed HTTP endpoints, strict parsing, shared budgets, verified finite termination and discarded unrelated records; called by monitor. |
| `backend/tests/test_alpaca_actions.py` | HTTP adversarial proof | VERIFIED | Actual HTTP-boundary fixtures/assertions for pages, missing IDs, mutations, limits and permission changes; executed in final backend suite. |
| `backend/app/services/stock_ownership.py` | Serialized historical journal | VERIFIED | Matched causal inserts, exact historical replay, consistency/unit/transaction epoch checks; called by actions/quote/monitor; future fill contract documented. |
| `backend/tests/stock_action_fixtures.py` | Synthetic historical ownership | VERIFIED | Explicit test-only baseline/fill/split helpers; test consumers use real isolated PostgreSQL; not imported by runtime. |
| `backend/app/services/corporate_actions.py` | Durable revisions/splits/entitlements | VERIFIED | Full transactional implementation, final SQL authority guard and immutable resolution predicate; monitor and API consume it. |
| `backend/tests/test_corporate_actions.py` | Real races/rollback/accounting | VERIFIED | Assertions inspect real quantities/basis/markers/lineage, not just code coverage; final full receipt covers suite. |
| `backend/app/tasks/stock_actions.py` | Durable complete catch-up | VERIFIED | Fixed-target segmented progress, retained IDs, replay frontiers, atomic twenty-state health, scoped action consumers; scheduler imports/calls. |
| `backend/app/core/config.py` | Disabled bounded action settings | VERIFIED | Scheduler-only false default, finite budgets/coverage/key checks; Compose passes settings to existing scheduler only. |
| `backend/alembic/versions/0012_stock_action_resolution.py` | Narrow SQL authority | VERIFIED | Concrete fixed SECURITY DEFINER function, evidence guards, no dynamic SQL/financial repair, PUBLIC revoke/operator grant; Python invokes exact signature. |
| `scripts/stock-actions.py` | Private inspect/reconcile | VERIFIED | Real argparse modes, protected config/CA/evidence, verified TLS dedicated role and receipt only after commit; own-process help succeeds. |
| `backend/tests/test_stock_action_resolutions.py` | Real role/stale decisions | VERIFIED | Real SQL privilege/stale snapshot/history/alias/cancellation and commit/failure assertions; actual TLS operator consumers separately proven. |
| `backend/app/schemas/stocks.py` | Additive strict safe envelope | VERIFIED | Frozen literal execution/status, action enums/UTC/safe epochs and valuation reasons; authenticated route response model. |
| `backend/app/services/stocks.py` | Final committed projection | VERIFIED | Bounded SQL hold/resolution/unit facts and final fresh synchronous response; existing `/stocks` route calls it. |
| `backend/app/services/stock_quotes.py` | Gate-bound local units | VERIFIED | Actual current-unit SQL proof and monotonic upsert; scheduler partitions one instrument per transaction after I/O. |
| `frontend/src/api/stocks.ts` | Strict action envelope validator | VERIFIED | Exact keys/types/UTC/Decimal-string/coherence, measured full transport and no-store fetch; hook consumes validated response. |
| `frontend/src/hooks/useStocks.ts` | Auth-scoped epochs/deadlines | VERIFIED | Actual TanStack query, raw high-waters, sanitized cache and nearest timers; StockSection calls hook. |
| `frontend/src/components/StockActionState.tsx` | Fixed accessible state renderer | VERIFIED | Real fixed enum copy, semantic time and unavailable valuation; both desktop/mobile StockSection render it. |
| `frontend/e2e/stock-actions.spec.ts` | Isolated safety stories | VERIFIED | Real browser assertions for presentation/time/crypto links and recovery; stock routes are deterministic UI fixtures, not financial proof. |
| `08-LOCAL-PROOF.md` | Accurate local receipts | VERIFIED | Raw logs/source identities independently checked below; existing full runs not rerun without changed source. |
| `08-HUMAN-UAT.md` | Actual owner disposition | VERIFIED | Concrete capture links/current source hash and actual approval, not inferred from test results. |
| `08-ACTIVATION.md` | Honest external gate disposition | VERIFIED | Actual owner deferral, disabled status and distinct unverified action rights/suitability; no invented campaign authorization. |

## Key Link Verification

The SDK literal-path checker returned “Target not referenced in source” for all **27** declared links. It looks for target path text, which is not how Python module imports, reverse consumers, SQL function bindings, matching grant contracts or document evidence work. These were **manually resolved with actual imports/calls/queries/contracts**, not waived. Several declarations point from producer to consumer although the import correctly runs consumer→producer.

| Plan | Declared links | Status | Actual wiring evidence |
| --- | --- | --- | --- |
| 01 | Migration↔bootstrap grants; model→registration | WIRED, 2/2 | Matching explicit 0011 runtime/NOLOGIN grants in migration/bootstrap; models/__init__ imports/exports all nine types and metadata/migration tests use them. |
| 02 | Producer→restore; fixtures→shell driver | WIRED, 2/2 | `verify-restore.recovery_contract()` imports selected producer; shell executes ops fixture, which seeds accounting and calls real backup/restore/role/TLS lanes. |
| 03 | Admission→rules authority; rules→calendar | WIRED, 2/2 | Independent evaluator checks are used alongside classification in real accounting consumers; rules imports ProductAdmission and `build_sessions`, and `dividend_cutoff` actually calls it. No reverse circular import is necessary. |
| 04 | Adapter→admission; adapter→normalized rules | WIRED, 2/2 | `_Context.guard` re-evaluates independent action authority around attempts/I/O; `_normalize` builds concrete NormalizedAction values consumed downstream. |
| 05 | Ownership→accounting model; ownership→immutable trade cause | WIRED, 2/2 | Actual SELECT/INSERT movements/applications plus matched Trade id/user/instrument/quantity/cost basis and current-transaction cause checks. |
| 06 | Actions→ownership; actions→exact rules | WIRED, 2/2 | Calls acquire gate/assert consistency/append/reconstruct and classify/cutoff/split-plan; no orphan exported service. |
| 07 | Scheduler→monitor; monitor→actions | WIRED, 2/2 | `amain` imports/calls run_stock_action_cycle independently; monitor partitions batches and calls persist/apply/derive in caller-owned transactions. |
| 08 | CLI→service; service→SQL function; producer→0012 restore | WIRED, 3/3 | CLI imports inspect/reconcile/protected input; reconcile executes `public.apply_stock_action_resolution`; migration creates exact signature; restore authenticates independent pinned function and fixed ACL contract. |
| 09 | Projection→safety; quotes→ownership gate | WIRED, 2/2 | `_action_projection` calls evaluate_action_state using final SQL facts; quote writer calls acquire_stock_gate before current-unit assignment and final insert. |
| 10 | API→hook; hook→component | WIRED, 2/2 | Hook imports/calls fetchStocks and measured TimedStocks; component imports/calls useStocks and renders conservative items. Actual data direction is producer→consumer. |
| 11 | Component→hook; state renderer→UI contract | WIRED, 2/2 | Both responsive layouts render StockActionState from validated items; fixed-copy helper and wrapping/semantic/live-region structure match approved contract, confirmed by browser/accepted captures. |
| 12 | CI↔CLAUDE critical list; proof→operations driver | WIRED, 2/2 | Exact 29-module mirror contract test asserts both lists; raw final critical report covers all 29. Proof names actual operations wrapper and identical fixture lane functions/receipts. |
| 13 | Proof→UAT; activation→roadmap boundary | WIRED, 2/2 | Same current screenshot/runtime hashes and concrete receipt links support owner packet; activation preserves explicit roadmap local/live boundary and actual owner decision. |

**Manual result: 27/27 semantic links WIRED.** No missing import/call, orphan artifact or unwired current-phase consumer found.

## Data-Flow Trace (Level 4)

| Artifact | Rendered/durable variable | Actual source and transformation | Produces real data | Status |
| --- | --- | --- | --- | --- |
| StockSection desktop/mobile | `data.items`, `item.action`, `item.quote` | useStocks→strict fetchStocks→authenticated `/api/v1/stocks`→list_stocks SQL catalogue/quotes/final admissions/actions | Real SQL-derived values; null quote is a deliberate denied/held/missing result, not an empty prop stub | FLOWING |
| StockActionState | action state/reason/checked time, valuationAvailable | Each real item passes action and conservative numeric availability; enum helper supplies safe copy only | Uses the backend-derived item, no hardcoded healthy default; missing action renders unavailable | FLOWING |
| useStocks cache/render projection | authenticated TimedStocks | Actual TanStack query/fetch result, full transport timing, exact deadlines/high-waters; timers only redact | Network response used; authenticated lifecycle cleans state; no hand-rolled fetching | FLOWING |
| Stock API | per-stock action/valuation availability | Final bounded SQL action state + unresolved immutable revisions/resolutions + current permission/calendar + stored quote units | Real PostgreSQL reads; no provider request/static successful response | FLOWING |
| Durable action/ownership state | revisions, movements, split marker, entitlements, health/frontiers | Bounded HTTP observations→per-instrument persistence; complete historical journal→exact split/cutoff effects; complete source segments→atomic monitor health | Actual persistence/mutations, tested with real isolated rows and HTTP-boundary source mocks | FLOWING locally; live activation OFF |

The HTTP adapter intentionally leaves unavailable economic verification facts unknown (for example absent date/due-bill/ordinary verification). Such real observations remain held; test-supplied verified normalized event evidence proves the automatic supported path under the roadmap's seeded local boundary. Fixtures do not prove a real product supplies adequate facts, and no blanket verified-date/ordinary assumption was found in the adapter. That suitability question remains an explicit activation prerequisite.

## Behavioral Spot-Checks Run by This Verifier

No server/service was started, database mutated, dependency installed or provider called. Each check completed in under ten seconds.

| Behavior | Command | Actual result | Status |
| --- | --- | --- | --- |
| Exact forward split, basis conservation, fractional refusal, persistent hold and equality expiry | `PYTHONPATH=backend backend/.venv/bin/python -c ...` importing actual rules and asserting 2×3/2=3, unchanged 100.01 basis, 3×3/2 held, recovered-health unsupported hold and `now == valid_until` denial | exit0, `PASS exact 3:2/basis; fractional refusal; persistent hold; deadline equality`, 1.26s | PASS |
| Private real CLI modes exist without connecting | `backend/.venv/bin/python scripts/stock-actions.py --help` | exit0; actual inspect/reconcile modes and protected connection help, 1.53s | PASS |
| Current predecessor/accounting recovery contract | `python3 deploy/tests/test-stock-recovery-contracts.py` | exit0; seven active cases pass, three real-PG cases explicitly skipped, 0.20s process time | PASS for offline scope only |

The offline command's skipped real-PG cases are **not** counted as new database proof. Its separately retained explicit `--postgres` receipt has ten executed tests, no skips, 55.831s and exact equality/invariant/identity outputs. That receipt and its assertion bodies were inspected. Broad existing green suites were not rerun after documentation-only changes.

### Probe Execution

No `scripts/*/tests/probe-*.sh` exists and no Phase 8 PLAN/SUMMARY declares a `probe-*.sh` path. No documented probe was missing. Step 7c conventional probe execution is therefore not applicable. The actual runnable recovery contract was independently executed above; retained operation PASS markers were additionally traced to genuine assertions and source, not treated as sufficient proof alone.

## Evidence Integrity and Existing Full Gates

Verified current HEAD 507196d. `git diff 0026053..HEAD --stat` contains only planning/acceptance/review documentation, with no runtime/test/CI source changes. Current relevant runtime hashes match the retained browser source receipt; recovery verifier and fixture hashes match the final operations packet. The retained archive was actually rehashed to:

`db27d99ba3085c6b93fa4fe4a6ea6bd9be5ea38a89f9e5f3620005de9681b874`

at `/tmp/birja-backup-test-phase08-plan12/recovery.tar`.

| Existing executed gate | Independently inspected receipt | Result |
| --- | --- | --- |
| Full isolated backend | `/tmp/birja-phase08-final-backend.log` | 1551 passed, 73 existing warnings, 163.92s; 99.82% overall |
| Exact critical coverage | `/tmp/birja-phase08-final-critical.log` | 29 modules, 2972 statements/978 branches; zero misses/partial branches, 100% |
| Frontend | `/tmp/birja-phase08-wave9-frontend.log` | 429 tests; 98.87% statements/97.29% branches/99.61% functions/99.66% lines; documented full static/build receipts current |
| Actual Chromium | `/tmp/birja-phase08-plan12-browser-rw1fffy4/browser-final.log` and `source-receipt.json` | 31 passed, one expected production-CSP skip, retries0; wrapper130.4s; source hashes match; owned resource inventories empty |
| Explicit real-SQL recovery | `/tmp/birja-phase08-final-recovery-postgres-contracts.log` | Ten executed tests, no skips, 55.831s; exact predecessor/accounting/function authority checks |
| Same retained encrypted six-revision roundtrip and roles/TLS | `/tmp/birja-phase08-plan12-ops.log`, actual ops-fixture scenarios | Recovery315.978s, roles160.138s, populatedTLS111.679s, freshTLS108.760s; final_all_lanes=true; actual runtime consumers/replays and bad CA/hostname/plaintext denials |
| Strict image scans | `/tmp/birja-phase08-final-scans/status.json` | All five targets exit0, zero qualifying HIGH/CRITICAL including unfixed; distinct engine/config identities, report hashes and DB timestamps retained |

Retained native77/runtime smoke, audits/static and independent source/security/UI reviews are supporting evidence in LOCAL-PROOF. This verifier did not rerun those expensive operations or claim to have done so. Source and behavioral assertion checks, rather than SUMMARY completion percentages, determine this verdict.

## Requirements Coverage

Exactly **five primary Phase 8 owners** appear in REQUIREMENTS traceability. All five occur in plan frontmatter. No orphaned or additional primary owner was found. All other milestone IDs retain their approved owners.

| Requirement | Source plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| DIV-01 | 01–04,06–08,12–13 | Retained structured ordinary USD announcements/revisions and regular rechecks, uncertain/cancelled events held | SATISFIED locally | Truths1,10–12,15,17–19; real revisions/known-ID/replay tests and SQL evidence; live source suitability remains deferred |
| DIV-02 | 01–03,05–06,08,12–13 | Historical cutoff entitlement accounting for trades/splits, excluding late buys and preserving later sellers | SATISFIED locally | Truths2,5,13–16; real cutoff/sold-out/split-unit/lineage tests and protected future-first-fill contract |
| ACT-01 | 01–03,05–06,09,12–13 | Exact supported once-only forward splits, conserved total basis, immutable fills | SATISFIED locally | Truths3,5,8,13–15,20; exact all-owner math and real atomic/replay/concurrency assertions |
| ACT-02 | 01,03–04,06–13 | Unsupported/uncertain events suspend affected stock and valuation until audited verified resolution | SATISFIED locally | Truths4,7,11–12,15,18–25; current SQL hold projection, private authority, cache/UI and acceptance; actual stock fill integration remains Phase9 |
| ACT-03 | 01–13 | Duplicate/recovery safety, ordered ownership/actions/eligibility, monitoring suspension/recovery | SATISFIED locally | Truths3–5,9–10,13–23,26; genuine database contention/fault/replay and retained exact restore evidence |

Requirement checkboxes/state transitions remain the orchestrator's responsibility. This report changes neither REQUIREMENTS nor ROADMAP nor STATE.

## Anti-Patterns and Adversarial Checks

| File/scope | Pattern or limitation | Classification | Assessment |
| --- | --- | --- | --- |
| All changed non-planning source/test/config/tool files since baseline949db3a | Unreferenced TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER, coming-soon/not-implemented stubs, console-only handlers | None found | Actual search produced no matches. Empty collections/nulls inspected in service/client paths are validated defaults, held/missing data, query initialization or bounded empty-source results populated by real code. |
| `stock_ownership.py:58` | New causal journaling refuses full cluster XID≥2**32 | INFO — explicit fail-closed capacity limit | Typed `transaction_epoch_unverified` prevents guessed xmin ownership; pre-wrap actual causal/savepoint/race behavior and pure boundary tests exist. No actual wraparound support claimed. Replay/reconstruction remain readable. |
| `stock_actions.py` | Known-ID/dividend capacity1000, replay density minimum, bounded segment catch-up | INFO — explicit safety caps | Overflow/incomplete segments refuse and remain reconciling; no silent truncation or renewed healthy lease. Actual provider capacity/suitability must be verified before activation. |
| `08-VALIDATION.md` / older STATE paragraphs | Historical pending Plan13 wording/false sign-off flags | INFO — bookkeeping pending this verifier | Newer STATE top/Plan13 records actual dispositions; no runtime impact. Orchestrator should finalize validation/state after this verdict, preserving historical receipts. |
| ROADMAP future phase sections | Existing `Plans: TBD` for unplanned Phases9–11 | INFO — explicitly later scope | These are future planning placeholders present before Phase8 execution, not unresolved Phase8 implementation debt; clear later-phase contracts above. |
| Browser suite | Production CSP case skips without E2E_PROD_URL | INFO — accepted scope | Explicit one-case skip, no production access or complete production-CSP claim. Local UI/action/crypto behavior has actual browser assertions. |

The inversion pass checked three concrete ways the goal could be false: substituting current holdings for historical entitlement, duplicate revised/restored splits, and green source responses clearing a hold or stale client prices. Actual journal reconstruction, economic-key/transaction proofs, immutable hold predicates, final API projection and client raw high-waters falsify those failure hypotheses locally.

The disconfirmation pass also checked evidence limits: (1) real provider event completeness is only partially established globally and remains explicitly unverified/deferred; (2) an empty mocked snapshot/replay monitor test proves local publication mechanics, **not** live deletion continuity or delivery latency, so it was not used for that claim; (3) Python hook defensive/unreachable branches and production CSP are not fully exercised by their respective frontend/local browser lanes, as honestly reported. No uncovered required local error path or misleading test was found that invalidates a must-have. Source real-failure assertions include permission loss after awaits, final SQL expiry, cancellation rollback, malformed/partial replay, immutable changed application and stale operator snapshots.

## Human Verification Required

**None outstanding for the approved local Phase8 boundary.** Plan13's two human-check blocks were harvested and both already have actual owner dispositions: UI approved and external activation deferred. The owner is not asked to repeat them. Visual acceptance is supported by actual screenshots and the recorded response; dynamic accounting/browser behavior is supported by automation rather than presumed manual repetition.

External access, long-lived action-derived/database/backup rights, real replay history/deletion continuity, quota/latency suitability and Phase7 live acceptance remain **OWNER-DEFERRED / UNVERIFIED**, with action activation and stock execution disabled. These are future activation blockers, not verified truths or human items silently waived by this local pass. Fresh status/halts authority remains a separate Phase9 prerequisite. No new private provider, production, B2, installed-tool, publication or campaign operation was performed or authorized.

## Deferred Items and Gaps Summary

Full milestone roadmap was inspected using `roadmap.analyze` and actual Phase9–11 criteria. Actual fills/combined valuation/status integration belong specifically to Phase9; cash payments/corrections/public History to Phase10; final complete mixed-ledger/rollout acceptance to Phase11. They were not used to defer any missing Phase8 artifact, local recovery duty or financial test. The approved roadmap already leaves execution disabled and permits seeded local ownership proof.

**No local BLOCKER, open WARNING, missing/stub artifact, orphan consumer or actionable Phase8 gap found.** The phase is ready for local bookkeeping and dependency-ordered isolated continuation. All deferred external gates remain enforced and unpassed. This report is not permission to activate live data, enable fills, publish, push, merge or deploy.

---

_Verified: 2026-11-11T18:05:50Z_
_Verifier: independent gsd-verifier agent; report only, no runtime edits or commits._
