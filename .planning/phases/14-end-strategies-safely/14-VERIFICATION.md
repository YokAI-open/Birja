---
phase: 14-end-strategies-safely
verified: 2026-11-22
status: passed
score: 5/5 roadmap outcomes verified
supporting_plan_truths: 38/38
requirements_satisfied: [PMGT-03, PMGT-04, PMGT-05, PFIN-05, PFIN-06, PCTX-03, PSAFE-01]
overrides_applied: 0
verification_scope: local implementation and owner-amended component qualification
---

# Phase 14: End Strategies Safely — Verification

**Goal:** Users can end any strategy without altering other portfolios, losing
retained evidence, receiving later financial effects or losing access to their
user identity.

**Status: passed locally.** Independent goal-backward inspection verifies all
five roadmap outcomes and seven assigned requirements. All19 plan summaries
exist. The owner explicitly accepted the implemented UI and native browser
200% result on2026-11-22. No further human result is outstanding for Phase14.

The verifier inspected actual implementation, test assertions and raw receipts;
it did not treat summaries or SDK artifact existence as behavioral proof.
Plan18's explicit method amendments are the current contract, not unreported
overrides: source-bound component reuse replaces repeated whole-local runs.
Failed whole runs remain failed. No successful whole all-security/browser,
uninterrupted seven-stage recovery, hosted CI, release or deployment is claimed.
Full CI before merge remains required.

## Observable outcomes

| # | Roadmap outcome | Status | Implementation and behavioral evidence |
|---|---|---|---|
| 1 | Named confirmation can be cancelled or confirm any owned portfolio, including holdings; repeated deletion stays on its original target and ordinary views exclude it. | VERIFIED | `PortfolioDeleteForm.tsx` renders the reviewed name, consequences, independent Cancel/Escape and explicit confirmation. `usePortfolioDeletion.ts` persists the original target/key before sending. `api/v2/portfolios.py:151` invokes `close_owned_portfolio`; `0023_portfolio_closure.sql:31` binds permanent intent to owner/target/name/policy and `:142` only sets the terminal timestamp. `list_active_portfolios` filters closed roots. `test_portfolio_closure_authority.py:86,117` and real browser `portfolio-deletion.spec.ts:177` assert original finances unchanged, no DELETE on Cancel and sibling independence. |
| 2 | The committed closure boundary freezes cash, holdings and History; unpaid dividends, corrections and splits cannot advance the experiment or fabricate liquidation/transfers. | VERIFIED | SQL closure derives terminal time after sorted instrument/root locks, records lifecycle and stock boundaries, and leaves financial payloads intact. `portfolio_closure.py` completes the actual ownership proof before commit. `dividends.py:69` resolves the immutable cause and refuses a closed root; `portfolio_lifecycle.py` interprets retained causes read-only. `test_portfolio_closure_events.py:81,102,213,298` asserts exact frozen snapshots for unpaid/corrected events and both real job/closure orders; crypto/stock writers recheck active state under locks. |
| 3 | Same-stock active siblings receive only their own once-only split effects; frozen historical ownership remains reconstructable without poisoning later accounting. | VERIFIED | `corporate_actions.py:572` takes deterministic root locks, rereads only active holdings and excludes frozen roots from later split projections. `stock_ownership.py:_check_closures/_check_units` validates closed sequence/time/unit bounds while retaining history. `0023` terminal-clock triggers prevent backdating across closure. `test_portfolio_closure_stocks.py:31` uses real multi-stock/sold-out books, successive sibling splits, frozen snapshots, conserved basis and original fills; races and clock tests cover both commit orders. |
| 4 | Deleting the last portfolio leaves identity signed in and an explicit Create state; reads/login do not regrant or recreate, and explicit replacement is a new identity within the active limit. | VERIFIED | `accounts.get_or_create_user` initializes a portfolio only for a genuinely inserted user; `get_me` reads identity independently. Overview renders the empty/Create state. Existing management SQL serializes owner creation/deletion and counts only active roots. `test_portfolio_closure_identity.py:163` checks OTP, refresh, identity, zero lists, retained grant counts and new replacement ID; real browser `portfolio-deletion.spec.ts:284` checks reload, Back, sign-in, empty state and explicit $10,000 replacement. |
| 5 | Owner/active authorization protects stale IDs, cursors, references and retries; old tabs cannot retarget orders; trade/job/delete races remain atomic. | VERIFIED | `portfolios.py:27,55` performs explicit owner/active resolution and final shared-lock fences. Valuation, both History services and crypto/stock preview/execute/retry endpoints call final authority after hydration/work. `PortfolioTargetBoundary.tsx` mounts financial children only for a ready owned target; lifecycle broadcasts invalidate identity-scoped caches, while recovery state remains metadata-only. `test_portfolio_closure_privacy.py:115,239,279,359` checks private references and closure during final reads; real race suites prove original-target outcomes without overspend or later mutation. Browser two-tab/lost-response/session-transition cases test revocation and no replacement retry. |

## Supporting plan truths and artifacts

All38 frontmatter truths were checked in their implementation context. The
following19 rows map each plan's pair of truths to substantive artifacts and
the outcome above; the additional infrastructure/recovery truths are included.
SDK `verify.artifacts` passed37/37 declared artifact entries across19 plans.
That existence check supplements the source/wiring inspection below.

| Plan | Both supporting truths | Evidence / mapping | Status |
|---|---|---|---|
| 01 | Preserve migrated finances; retain honest historical closure provenance. | Additive0021 schema and0022 stopped-writer backfill validate existing boundaries without inventing owner confirmation; migration/fixture assertions preserve original financial payloads. | VERIFIED |
| 02 | One terminal boundary across stocks; permanent original intent never retargets. | `0023_portfolio_closure.sql`, actual closure service and authority tests; outcomes1–2. | VERIFIED |
| 03 | Reconstruct frozen sold-out/multi-stock ownership; prohibit backdated stock history. | Complete ownership proof plus already-held-gate terminal-clock triggers and real clock/sibling tests; outcomes2–3. | VERIFIED |
| 04 | Refuse partial schema at startup; restrict closure/financial authority. | `portfolio_bootstrap.py` current0023 catalogue/ACL/default checks and `portfolio_migrate.py` migration-only admission; real fresh/upgraded/cold authority results match. | VERIFIED |
| 05 | Retain all terminal evidence in recovery; use genuine qualified0020 source. | Backup V3 inventories lifecycle/intent tables; immutable retained-source dispatch and actual installed verifier resolve genuine0020; both cold restores pass. | VERIFIED |
| 06 | Validate terminal/private state before restored grants; refuse losing rollback. | `verify-restore.py` V3/quarantine/authority checks and selected deployment contracts; actual cold/rollback logs. | VERIFIED |
| 07 | Authenticated confirmed public closure; delete-last preserves identity without implicit funding. | CSRF/current-user DELETE route → service → SQL; identity/API and browser assertions; outcomes1,4. | VERIFIED |
| 08 | Unpaid/corrected events cannot restart closed books; active siblings continue. | Read-only lifecycle disposition and post-lock financial routines; actual event/scheduler tests; outcomes2–3. | VERIFIED |
| 09 | Closed stock books do not poison siblings; overlaps have an exact commit order. | Real PostgreSQL stocks/races tests use frozen snapshots and actual blockers; outcomes2–5. | VERIFIED |
| 10 | Stale references cannot expose closed finances; final read authority remains owner/active. | Shared final fence wired through valuation, History and trade/retry APIs; outcomes1,5. | VERIFIED |
| 11 | Recover only original deletion; bounded nonfinancial persisted intent never auto-submits/retargets. | Strict `portfolioDeletion.ts` request/result parsing and `portfolioDeletionAttempt.ts` persistence before send; outcome5. | VERIFIED |
| 12 | Recover unknown result outside financial authority; keep siblings usable. | `usePortfolioDeletion.ts` owner/session/operation guards, explicit check and original metadata-only attempt; outcomes1,5. | VERIFIED |
| 13 | Stale tabs/routes hide financial details without redirecting orders; broadcasts cannot grant authority. | Metadata identity invalidation → `usePortfolioTarget` → `PortfolioTargetBoundary`; server final fences remain authoritative; outcome5. | VERIFIED |
| 14 | Accessible named review/Cancel/confirm; signed-in empty/Create after last deletion. | Actual form/page/routes and overview empty state, real browser cases and both owner outcomes; outcomes1,4. | VERIFIED |
| 15 | Real fresh/upgraded restricted TLS; exact current/retained fixture dispatch and ownership. | Revision-aware fixtures, unchanged historical source and raw role/TLS/cold receipts independently inspected. | VERIFIED |
| 16 | Runner can exercise every current/retained gate at one source/archive; durable campaigns cannot silently restart/rebind images. | Actual one-shot claim/status/preflight/source guards and seven-stage runner remain implemented; CI wiring covers critical modules. Plan18 explicitly amends the local qualification method; failed whole runs are not passes. | VERIFIED |
| 17 | Real deletion/last-book/stale-tab journeys; inspectable current rendered packet. | Registered `portfolio-deletion.spec.ts`, actual database oracle assertions and current419-artifact packet independently verified. | VERIFIED |
| 18 | Source-bound component qualification; exact terminal recovery and safe rollback. |28 successful command logs and6 recovery operation logs independently hash-verified; archive/inode unchanged; current source-destroyed restore and authority parity pass under recorded amendments. | VERIFIED |
| 19 | Explicit owner UI approval; separate real native200% result. | Owner response2026-11-22: “i approve ui and 200 zoom”; `14-HUMAN-UAT.md` records both actual outcomes against current verified packet. | VERIFIED |

## Key links and dynamic data flow

| From | To / actual source | Wiring and flow |
|---|---|---|
| Detail layout / App routes | `PortfolioDeleteForm` and separate `PortfolioDeletionPage` | Imported and mounted; metadata-only recovery stays outside unavailable financial target content. |
| Confirmation / Check result | `usePortfolioDeletion` → `deletePortfolio` | Actual explicit callbacks capture immutable owner-scoped intent, persist before network, call TanStack mutation and handle durable success/refusal/unknown outcomes. No automatic new target/key. |
| Browser DELETE | `/api/v2/portfolios/{id}` → `close_owned_portfolio` → `public.close_portfolio` | Authenticated user and CSRF dependencies precede strict payload parsing; bound SQL parameters, actual locked mutation and ownership proof, then commit and exact receipt. |
| Overview / private statements | Active account queries → final owner/active fence → schema response | Real Postgres queries populate values; no static/empty replacement for missing data. Empty portfolio list is a real zero-root result. |
| Lifecycle invalidation | Scoped caches / target boundary → fresh owned-active metadata | Financial children require ready authority. Broadcast is an invalidation hint; it does not manufacture server permission. |
| Split / dividend jobs | Actual holdings/causes → post-lock active checks → immutable journal | Closed books retain original rows but receive no later effect; complete stock proof still includes their frozen history. |
| Backup → restore | V3 schema/source manifest → authenticated installed verifier → quarantine/oracle/role checks | Actual encrypted cold restores and original-intent replay are in operation logs; historical source is selected from the authenticated archive. |

## Requirements coverage

| Requirement | Verified outcomes / implementation | Status |
|---|---|---|
| PMGT-03 |1: named explicit confirmation, Cancel no-op, holdings and original-intent replay | SATISFIED |
| PMGT-04 |2: terminal frozen financial records, omitted future effects, no liquidation/transfer | SATISFIED |
| PMGT-05 |4: zero-root signed-in state and explicit new replacement only | SATISFIED |
| PFIN-05 |3: active-only successive splits with conserved basis and frozen ownership reconstruction | SATISFIED |
| PFIN-06 |2–5: real serialized creation/delete/trade/job races, limits and no duplicate grant/effect | SATISFIED |
| PCTX-03 |1,4,5: stable explicit routes and unavailable stale links without financial disclosure | SATISFIED |
| PSAFE-01 |5: server owner/active checks on ordinary reads, cursors, original references and retries | SATISFIED |

All seven IDs are assigned to Phase14 and declared by its plans; no orphaned
Phase14 requirement was found. Phase15's broader lifecycle acceptance/recovery
requirements remain outside this completion. Phase7 live obligations remain
deferred and stock activation gated. Issue35's existing scope and2026-12-17UTC
expiry are unchanged.

## Independent checks and raw evidence

- Fresh `python3 deploy/tests/portfolio-ui-evidence.py --phase 14 --verify
  /tmp/birja-phase14-ui-review`: exit0, `CURRENT SOURCE AND ARTIFACTS VERIFIED`.
  Current ZIP SHA256 is
  `886805a094fad7495ae53539da7ea80d0ddff6c67b1ce0aa0465899a493d32e0`.
- SDK artifact queries:19 plans,37/37 declared artifacts pass. Actual source
  semantics and links were inspected separately, including concrete real-DB
  assertions for Cancel, financial freeze, sibling effects, final-read races,
  OTP/refresh after last deletion and explicit replacement funding.
- Read-only integrity check independently recomputed every recorded SHA256 for
  all28 successful security-command logs and all6 recovery-component logs;
  all match their receipts and have exit0. This check exited0 in this verifier.
- Independently hashed `/tmp/birja-phase14-proof/recovery.tar.gz`: SHA256
  `1a41c8b9a55986998e46ea6341dfea93dd2b7c8da0e0428af08251d21d6b742f`,
  original inode943123. Cold/upgraded/fresh/rollback authority triples match
  exactly. Actual current cold log records encrypted restore,
  `source_destroyed=true`, independent before-oracle and quarantine checks.
- `git diff 09c70f5 --name-only` over backend, frontend application/public and
  dependency inputs is empty. R2 raw `command.log` records3691 backend passes,
  zero missing critical statements/branches at100%, no Python audit findings
  and1330 frontend passes. The original R2 status remains failed as required.
- Raw receipt roots:
  `/tmp/birja-phase14-campaign-security-plan18-r2/`,
  `/tmp/birja-phase14-campaign-security-tail-plan18-r{1,2}/`,
  `/tmp/birja-phase14-campaign-recovery-components-plan18-r1/`, and
  `/tmp/birja-phase14-campaign-plan18-repair/`. Component ledger, exact log
  hashes, reused input analysis, final authority and cleanup reports were read.
- No explicit `probe-*.sh` path is declared by Phase14 plans/summaries or found
  among project scripts. No mandatory probe was omitted. No application,
  database, browser or scanner was launched during this verification.

## Disconfirmation and limits

The review specifically checked three plausible failures: a successful closure
that changes financial payloads, a job/read selected before closure that acts
after it, and a lost browser response that retargets a replacement. Actual SQL,
post-lock/final-read fences, immutable originals and relevant real-DB/browser
assertions address each. No partial Phase14 requirement or concrete wiring
blocker was found. Reviewed implementation files contain no untracked debt
markers or user-visible placeholder implementations.

The corrected standalone History browser pass did not force its optional order
recovery branch; it is not evidence that this branch ran. The report preserves
that limit rather than claiming extra browser coverage. Closure lost-response
recovery itself has dedicated real browser/DB assertions. Existing complete
component evidence is accepted under the recorded Plan18 amendments; no new
test campaign is implied by this review.

No additional human verification is required for this phase: both actual
owner outcomes are recorded. Browser name/version were not supplied. Immutable
capture-time human flags remain unchanged; later acceptance has separate
provenance. This local completion does not authorize publication or deployment.

**Result:**5/5 roadmap outcomes,38/38 supporting plan truths and7/7 assigned
requirements verified; zero remaining goal blockers or unresolved human items.
Parent may reconcile phase state and requirement checkboxes. Full PR CI remains
a separate prerequisite to merge.
