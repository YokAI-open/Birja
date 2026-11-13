---
phase: 10-dividend-cash-and-event-history
verified: 2026-11-13T16:20:13Z
status: human_needed
score: 4/4 roadmap must-haves verified
overrides_applied: 0
review_source: 48d970c262c7f52bb5692d38db0748e5169cf389
human_verification:
  - test: Accept the new mixed History, Dividend, correction/held and original-reference interface at the recorded source.
    expected: Explicit owner acceptance or concrete defects recorded in 10-HUMAN-UAT.md.
    why_human: Automated financial/browser proof and independent UI review cannot supply the owner's acceptance.
  - test: Inspect the extracted review HTML in a desktop browser whose own Zoom menu visibly reads 200%.
    expected: Readable text, reachable controls/details, no obscuring overlap and no horizontal page overflow.
    why_human: Viewport tests, root-font enlargement and earlier Phase9 acceptance do not establish genuine current-phase native zoom.
---

# Phase 10: Dividend Cash and Event History Verification Report

**Phase Goal:** Users receive verified dividend cash once and trace all mixed-asset trades, income, splits and corrections in History.

**Status:** human_needed. **Re-verification:** No — no previous report existed. All four roadmap implementation truths are VERIFIED; two additional Plan18 acceptance truths are UNCERTAIN (WARNING, owner decision required). No implementation blocker or override found. This report does not complete Phase10 or check off its requirements.

## Goal Achievement

### Observable Truths

| # | Roadmap contract | Status | Actual evidence |
|---|---|---|---|
| 1 | On or after payable date, a verified ordinary USD dividend credits gross cash using retained eligible quantity, without tax or reinvestment. Its separate Dividend event shows stock, relevant dates, eligible shares, per-share rate and credit, including entitlements captured before this phase. (DIV-03) | VERIFIED | `0014_dividend_accounting.py:124–372,374–477` derives authority/owner/quantity/rate from retained state, checks New York payable date, reconstructs historical quantity and applies explicit half-even cents. `dividends.py:63` invokes that function in one transaction. `test_dividend_payments.py`, `test_dividend_schema.py`, `test_dividend_authority.py:307` and `test_dividend_scheduler.py:332` assert old entitlement preservation, literal rounding, due dates and credit after an actual sale. `event_history.py:121` projects saved original dates/terms/cash; UI renders gross/no-tax/no-reinvestment copy. |
| 2 | Concurrent runs, retries, announcement revisions and recovery cannot credit one dividend twice or expose History cash without its matching atomic credit. (DIV-04) | VERIFIED | Immutable unique event/owner anchor, target identity and composite FKs in `models/dividend.py`/0014; instrument gate → Account lock → final full authority guard after immediate constraints → service commit. `test_dividend_concurrency.py:32,48,117,139,213` asserts duplicate workers, A→B→A, real rollback, lost response/replay and simultaneous invisibility of uncommitted cash/History. Actual retained0014 replay/quarantine evidence described below preserves rows, sequences and exact function authority. |
| 3 | A verified post-payment correction produces a separate linked adjustment, preserving the original. Repetition cannot duplicate its delta; uncertain or unaffordable negative adjustments stay visibly held for reconciliation without negative cash. (DIV-05) | VERIFIED | 0014 computes rounded desired total minus original + applied deltas; holds apply0 and retain immutable predecessors. `test_dividend_corrections.py`, concurrency tests and `test_dividend_scheduler.py:59` exercise paidA→held/cancelledB with **empty** latest-verified helper, repeated cycle dedup, private held History and one reviewed applied successor; original unchanged. The independent paid-anchor keyset reaches no-target uncertainty. `deploy/tests/dividend-execution-fixture.py:301–385` proves the real restricted worker/services/History and retained replay/42501 quarantine chains. |
| 4 | User privately pages through deterministic newest-first crypto/stock fills, Dividend credits, forward splits and corrections with event-specific details and preserved crypto history. Portfolio return includes dividend cash exactly once. (HIST-03; consumes PORT-06) | VERIFIED | `event_history.py:139–313` owner-filters every UNION branch and every projector/original join, seeks the complete `(recorded_at,kind_rank,source_id)` tuple and uses bounded limit+1. Strict authenticated no-store API is registered in `api/v1/router.py`. Exact Fraction reduction emits1.5:1 as3:2. Cursor/service/API and legacy `/trades` tests assert privacy, tied pages, offpage originals and compatibility. `test_portfolio_snapshot.py:182–221` asserts cash100→101→101.50, unchanged starting_cash10000 and no held balance change. Real browser assertions prove dividend-funded stock+crypto purchases and mixed pages. |

**Score:** 4/4 roadmap truths verified in local code and automated evidence. The roadmap wording is retained; plan refinements below add checks rather than reduce that contract.

### Plan Must-Have Refinements

All PLAN frontmatter was examined. Related implementation refinements are grouped beneath their roadmap truth; both truths per plan resolve as follows. The score above counts the four deduplicated roadmap outcomes, not human acceptance as an automated pass.

| Plan | Additional truths checked | Status / evidence |
|---|---|---|
| 01 | Preserved0013 entitlement, relational/immutability rejection; verified zero and safe downgrade | VERIFIED — schema migration/tests include composite identities, zero original and populated downgrade refusal. |
| 02 | Narrow scheduler-only derived cash/hold authority; app/PUBLIC/shadow denials and role parity | VERIFIED — 0014 fixed signatures/path/owner/revocation, authority tests, actual fresh/upgraded roles/TLS. |
| 03 | HALF_EVEN ties/zero; target-minus-applied A→B→A and held debit | VERIFIED — independent literal TARGET_VECTORS and SQL parity, correction/concurrency assertions; fresh verifier spot-check. |
| 04 | Exact0014 data/identity/authority retention; authenticate before clone ACL reconstruction/quarantine | VERIFIED — revision-specific producer/consumer definitions and actual corruption/restore tests; retained run. |
| 05–06 | Actual sold-eligibility/corrections/reconciliation; fresh/upgraded restricted TLS; same archive0007–0014 and preconsumer proof | VERIFIED — actual SQL fixture, preconsumer proof and final same-archive logs. No current0014 compatibility requirement is deferred. |
| 07–08 | Gross due once-only shared cash; paid→uncertain→reconciled lineage; cross-asset races and actual wait rechecks | VERIFIED — services, independent-connection concurrency/wait tests and actual financial fixture. |
| 09 | Independent uncertain paid-anchor discovery; dedup/reconciliation without blocking crypto | VERIFIED — separate VERIFIED/ANCHORS bounded keysets; scheduler tests and actual cycle→SQL→History. |
| 10–11 | Strict cursor/tied private pages/offpage original; authenticated exact no-store API, legacy preservation and once-only portfolio | VERIFIED — full-tuple SQL and owner joins; actual DB service/API/portfolio assertions. |
| 12–13 | Whole-page strict exact parser; owner/epoch late-response isolation and retained errors; authoritative cash refresh | VERIFIED — parser/hook source and malformed/late401/same-owner-relogin/cancel-before-invalidate tests. |
| 14–15 | Actual versus proposed cash, reachable original; responsive focus/errors; genuine financial browser and source-bound captures | VERIFIED — renderer/page, real SQL/API browser assertions and current packet hashes; native zoom expressly pending. |
| 16 | Complete critical CI contract; actual suites/audits/scans and final retained/TLS/current-service replay/rollback | VERIFIED — 47-module CI/docs/test list and measured gates. Same-archive proof retains its original source/image scope, detailed below. |
| 17 | Current code/security/UI reviews have no unresolved blocker; four requirements mapped honestly | VERIFIED — `10-REVIEW.md`, `10-SECURITY.md`, `10-UI-REVIEW.md` and this report. Coordinator-owned final ledger/summary reconciliation follows this review; its timing is not a missing product artifact. |
| 18, truth1 | Explicit owner acceptance of the new mixed History/held/correction/original UI | UNCERTAIN — WARNING: owner decision required; `10-HUMAN-UAT.md` records PENDING. |
| 18, truth2 | Genuine desktop native200% usability with no overlap/horizontal overflow | UNCERTAIN — WARNING: owner observation required; no result invented. |

### Required Artifacts and Critical Links

All below exist, are substantive and wired; dynamic data is traced separately below.

| Artifact / link | Status | Evidence |
|---|---|---|
| `backend/app/models/dividend.py` ↔ `backend/alembic/versions/0014_dividend_accounting.py` | VERIFIED / WIRED | Registered models, immutable triggers, finite/cents/state/lineage checks, unique original/target/held identities, real owner/time/ID indexes; migration adds no backfill. |
| `services/dividend_rules.py` → literal rules tests → actual SQL parity | VERIFIED / WIRED |64-digit Decimal context; no intermediate rate rounding, no held proposal in applied sum; SQL tie logic uses trunc/mod rather than PostgreSQL round. |
| scheduler → `tasks/dividends.py` → `services/dividends.py` → two SQL entry points | VERIFIED / WIRED | Dedicated supervised loop; two durable keysets interleave at most100 candidates/40s with fair wrap. One owner transaction per attempt; failure/cancellation cleanup tested. SQL derives owner/amount and keeps scheduler direct cash writes denied. |
| SQL gate → Account → deferred constraints → final authority → commit | VERIFIED / WIRED | `apply_stock_dividend:392–475`, hold equivalent; final helper re-reads full retained rows/rights/calendar/monitoring and advancing clock; no later business query/await in transaction service. Real gate/account/constraint waits test stale revision/entitlement/rights/expiry refusal and rollback. |
|0014 authority → `deploy/db/bootstrap-roles.sql` / `configure-db.sh` → exact restore validator | VERIFIED / WIRED | Fixed bodies/signatures/owners/security/path/volatility/ACLs authenticated before restoration. Actual altered authority and unsafe roles refused; clone app/scheduler denied42501. |
| Ordinary Compose migration → guarded `app/db/dev_bootstrap.py --after-migrations` | VERIFIED / WIRED | Explicit ENV/host/database/admin/safe-NOLOGIN/membership/effective schema0014/object/identity/function-owner checks precede minimal object grants. Permanent `deploy/tests/test-dev-bootstrap.py` CI financial regression covers fresh and0013 upgrade. |
| `services/event_history.py` → `schemas/event_history.py` → authenticated `/api/v1/history` | VERIFIED / WIRED | Exact C05a union, owner predicate in every branch, full cursor seek, saved stock fill facts, owner split movements and owner-bound original. Legacy `/trades` remains registered separately. |
| `frontend/src/api/eventHistory.ts` → `useEventHistory.ts` → routed `HistoryPage.tsx` / `HistoryEventDetails.tsx` | VERIFIED / WIRED | Strict tagged exact-string parser; owner+epoch query keys, abort/late-result guards, no optimistic cash; typed live query rows render table/cards and original/proposal/held fields. Trade completion invalidations reach History. |

### Data-Flow Trace (Level4)

| Rendered artifact / variable | Real source | Status |
|---|---|---|
| HistoryPage `data.pages[].items` | TanStack infinite query → `fetchEventHistory` → CurrentUser `/history` → owner-filtered SQL UNION of Trade/Payment/Movement/Decision | FLOWING — real rows; accepted pages survive read failures. No hardcoded empty prop supplies the production renderer. |
| HistoryEventDetails `item`, `item.original`, terms/applied/proposed | Strict C05a projection; correction original joined with both owner predicates, even offpage | FLOWING — immutable saved financial terms; null uncertainty stays unknown, held cash stays0. No unbounded original scan. |
| Shared cash/portfolio after new events | Hook cancels pending pre-event views then invalidates `/me`/portfolio/stock context; backend reads Account.cash once | FLOWING — no client dividend sum or second starting grant. Independent before/after portfolio assertions and real browser purchases verify effect. |

### Behavioral Spot-Checks and Execution Evidence

This independent verifier read source, changed-file scope (`5925b52..HEAD`), actual assertions and logs; it did not start a database/browser/service, rerun long suites, change source or commit. Source build is48d970c; report-only HEAD7af5011 adds no product change.

| Check | Command / evidence | Result |
|---|---|---|
| Fresh half-even and held debit | `cd backend && uv run --locked --no-sync --no-cache python -c ...` importing actual rules; literal1×.005→.00,1×.015→.02; target.20 minus1 applied with cash.79 | PASS; held applied0 and unchanged.79. Under1s. |
| Fresh cursor roundtrip | Same read-only process; actual encode/decode with UTC timestamp/rank4/bigint9223372036854775807 | PASS; exact full cursor roundtrip. |
| Fresh current source/packet integrity | Python hashlib/zipfile: frozen385source map +107UI hashes, exact ZIP SHA/size and CRC | PASS;385/385 +107/107;50ZIP members,15,497,014bytes, no mismatch/CRC failure. |
| Fresh changed-source debt/whitespace |73 changed source files scanned for unreferenced TBD/FIXME/XXX; `git diff --check` | PASS; zero debt markers/whitespace errors. |
| Full affected backend / critical | `/tmp/birja-phase10-17-backend-full.log`, `...-critical.log` |2557passed324.80s,99.87%;47critical modules4565statements/1462branches100%, no missing/partial. |
| Actual ordinary dev financial regression | `/tmp/birja-phase10-17-dev-financial-green.log` | Fresh19.287s/upgrade21.117s: real original/hold/correction/dedup/reconciliation/worker/History/replay; cash10004/start10000, original unchanged; unsafe state refused unchanged. |
| Current frontend/browser | `/tmp/birja-phase10-17-frontend-full.log`; `/tmp/birja-phase09-browser-5bjhfgb1/browser-all.log`; runner `...-browser-all-final.log` |697frontend/36files16.42s,98.37%statements94.82%branches; actual browser49passed/one expected deployed-CSPskip317.3s.385before/after/current source hashes match. |
| Static/native/images/audits | `10-LOCAL-PROOF.md`, `10-VALIDATION.md`; `/tmp/birja-phase10-17-image-native-inventory.json`, `...-image-reports/status.json` | Ruff/190format/Mypy88 and frontend static/build pass; repository recipe builds, inventory parity, UID1001/networknone native financial imports/checks pass. Five strict fresh scans0HIGH/CRITICAL incl unfixed. Locked pip audit clean; npm configured high gate passes with2low/15moderate, not zero vulnerabilities. |

### Probe Execution and Recovery Scope

No declared or conventional `scripts/*/tests/probe-*.sh` was discovered; no missing documented probe. Named operational tests are real financial probes; their already executed commands/logs were inspected, not rerun or replaced with a dry-run claim.

`/tmp/birja-backup-test-phase10-final/gate-report.json` records **six actual passes /1391.017s** from source7196d5f: retained0007–0014, restricted roles, populated TLS, fresh TLS, image transition, selected cutover/recreate/old-app rollback. Actual command was `python3 /tmp/birja-phase10-16-final-gate.py`, not literal CLI `--all`. One archive `/tmp/birja-backup-test-phase10-final/recovery.tar` is checksum-pinned: `1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`,152320000bytes. Report SHA256 `0114bbd04e61756afd47fda9246eb333102d059af799c2e1db0efeadd471f972`.

The **selected cutover/old-app rollback fixture is0008**. This is not proof of an old runtime on0014 or a selected0014 candidate cutover. Current0014 has genuine retained encrypted restore, exact financial/lineage/identity/authority comparisons, current-service immutable original/correction/nochange/held/reconciled replay, mixed History/Portfolio, worker paidA→heldB→dedup→reconciled publication and app/scheduler42501 quarantine. See `deploy/tests/dividend-execution-fixture.py`, `test-stock-recovery-contracts.py`, producer/consumer validators and `/tmp/birja-phase10-16-final-same-archive.log:93–105,121–138`. Those address DIV-04/05 and C04's required0014 compatibility; no absent0014 proof is silently deferred. Phase11's broader SAFE-02/03 full mixed-asset recovery/acceptance and rollout boundary remain distinct.

`/tmp/birja-phase10-17-retained-source-integrity.json` records all12 sealed prior artifacts and all11 retained CORE/current/tar bytes unchanged; authority, migrations, production bootstrap and backend financial services/workers/History are byte-identical. Its current comparison is375/384 unchanged, with nine approved dev/CI/Compose/UI deltas plus the new dev regression. Parent approved affected checks; those and the fresh complete browser run passed. The1391.017s proof remains the **Plan16 execution at its original source/images**; it was not rerun at48d970c or the rebuilt Plan17 images.

### Requirements Coverage

| Requirement | Source plans | Status / evidence |
|---|---|---|
| DIV-03 — verified gross ordinary USD due cash and detailed Dividend |01–03,05,07–09,11–12,14–18 | Implementation SATISFIED — roadmap truth1, real sold-after-cutoff credit and C05a fields; owner new UI/nativezoom pending. |
| DIV-04 — atomic once-only cash/History across retries, concurrency, revisions and recovery |01–02,04–09,13,15–17 | Implementation SATISFIED — truth2; actual transactional/concurrent/retained replay proof. |
| DIV-05 — linked immutable correction, duplicate protection and visible uncertainty/affordability hold |01–05,07–12,14–18 | Implementation SATISFIED — truth3; real worker→restricted SQL→History paidA/heldB/dedup/reconciled successor and exact held authority recovery. Owner new UI/nativezoom pending. |
| HIST-03 — private deterministic mixed event paging/details, preserved crypto fills |10–18 | Implementation SATISFIED — truth4; actual owner-filtered SQL/API/browser, full tuple cursor and bounded original. Owner new UI/nativezoom pending. |

All four IDs assigned by REQUIREMENTS are claimed by plans; no orphaned requirement. Requirements remain unchecked until actual Plan18 acceptance and normal orchestrator closure. PORT-06 is consumed/protected, not claimed as a new Phase10 assignment.

### Anti-Patterns and Test Quality

No current missing/stub/orphaned/hollow artifact or unresolved implementation BLOCKER found. Runtime empty lists/nulls are bounded empty results, unknown terms or cleared state; production data paths populate them. No unreferenced TBD/FIXME/XXX in73 changed source files. Error/delay/presentation fixtures are not mislabeled successful financial mocks.

Disconfirmation checks targeted duplicate-cash races, disappearing paid-anchor uncertainty and cross-owner/tied-page leakage. Tests assert independent literal cash values, row counts, original row equality, predecessor IDs, denied SQLSTATEs and actual independent DB waits. SQL half-even parity consumes literal expected vectors rather than using the implementation to calculate its own oracle. The full47-module critical list is actually mirrored in CI/docs/test assertions; coverage alone was not taken as proof.

Two potentially misleading green checks were explicitly limited: (1) the historical dev reproduction exits0 because it **asserts the42501 defect**, not financial success; real expected-success REDdd2ba3a then GREENf47af65 and permanent ordinary-dev CI regression close CR-01; (2) tied-time browser route fulfillment is a **read-only presentation fixture**, not proof of SQL tie ordering or financial mutation. Actual SQL paging tests and independent real browser financial flow supply those proofs. Failure/timeout monkeypatches exercise cleanup around real financial behavior; they do not replace successful financial writes. No disabled Phase10 financial requirement proof was found. The sole expected deployed-CSP skip is old accepted W07, not the sole evidence for a new requirement.

The initial UI21/24 finding UX-01 was a real readiness defect despite its WARNING label: actual REDdb19cf5 measured focused completion bottom3616>viewport900. GREEN48d970c retains owner/epoch/append-intent/nonsteal guards and permits native focus scrolling; actual end/retry rectangle/navigation checks pass at320/375/768/1024/1440. Cash medium weight and four16px gaps now match the contract. Independent current UI24/24/code0active/security70fully verified+2pending human are consistent with inspected source and evidence. This does not mean72 threats closed or owner acceptance received.

### Human Verification Required

1. **New Phase10 UI acceptance — UNCERTAIN / WARNING.** Follow `10-HUMAN-UAT.md`: download/extract `/tmp/birja-phase10-ui-review.zip`, open local `index.html` in a desktop browser, inspect mixed desktop/mobile, original, unaffordable/uncertain/reconciled and loading/empty/error/end pages. Expected: clear actual versus proposed cash, truthful no-cash holds, traceable originals and acceptable new UI. Record the owner's explicit answer bound to48d970c. Offline exported controls are presentation only; browser/service tests prove interactions.
2. **Genuine native200% — UNCERTAIN / WARNING.** In that desktop browser select Zoom200% in its own menu and confirm the displayed setting. Inspect mixed/held/append-error pages top to bottom. Expected: readable text, reachable controls/details, no obscuring overlap or horizontal page scrolling. Record browser/setting/result and any affected page. Smaller viewports, CSS/root-font/device scaling and Phase9 approval cannot answer this.

The packet SHA256 is `cf4e4817bdae885c2feea4c5fe9e6368ef834394a83f618e6bddddaa5fb9845d`;16HTML/32PNG plus index/manifest,385current capture hashes and107UI hashes verified. Neither owner answer is present. These are planned Plan18 human gates, not a circular Plan17 implementation blocker.

### Gaps and Deferred Boundary

No actionable implementation gap found, so no fabricated `gaps` entry or override. Overall status remains **human_needed**, never `passed` while the two owner outcomes are pending. Later Phase11 scope was checked against ROADMAP; no failed Phase10 truth was moved there. Existing Phase7/8 live access/rights/activation, publication and accepted v1 W01–W08 deferrals are preserved. Synthetic admission/provider fixtures prove local safeguards and cannot establish live permission, freshness or rollout acceptance.

---

_Verified: 2026-11-13T16:20:13Z_  
_Verifier: independent gsd-verifier agent; only this report written, no commits._
