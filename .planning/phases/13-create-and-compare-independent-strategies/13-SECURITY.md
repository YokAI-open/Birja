---
phase: 13-create-and-compare-independent-strategies
audited: 2026-11-19
reviewed_runtime_head: 9527e358bc6953cec7580043703324db194ba396
register_authored_at_plan_time: true
status: secured
asvs_level: 1
threats_total: 58
threats_closed: 58
threats_open: 0
implementation_gaps: 0
qualification_pending: 0
current_packet_binding: verified
unregistered_flags: 0
---

# Phase 13 security mitigation verification

Final independent declared-threat verification at tested source
`9527e358bc6953cec7580043703324db194ba396`: **58/58 CLOSED, zero OPEN**.
All18authored plan registers remain individually represented below:40mitigation
rows (36implementation,2actual whole-campaign evidence,2actual human-response
records) and18references to the same existing accepted risk. Final raw command,
coverage, audit/image, source/archive and UAT evidence has been independently
checked. This is local Phase13 threat verification; global phase completion
still requires the separate goal verifier. No production or provider activation
is implied, and no new risk exception was accepted.

## Initial audit scope and method (historical)

Read AGENTS.md, full CLAUDE.md, Codex adapter/secure-phase workflow and role,
PROJECT/REQUIREMENTS/ROADMAP/STATE/config, all18plan threat registers,
01–16summary threat-flag sections, current clean integrated code review
(including CR-01 resolved at6bfb447 and CR-02 at99166d9), UI review and UI evidence, Phase12accepted
risk, then followed the named implementation/control call sites and corresponding
negative regressions. The summaries contain no `## Threat Flags` headings;
that absence was not treated as proof of no attack surface. Source-boundary
coverage below follows the authored register rather than blind discovery.

No tests or browser/security/recovery campaigns ran in this audit. Regression
citations establish implemented assertions; prior executor receipts remain
separate evidence. No dependency, source, environment, provider, production,
publication or git mutation occurred. Only this report was written. Concurrent
capture work owns UI-EVIDENCE/SUMMARY16; no screenshot or acceptance receipt was
rewritten by this auditor. Nominal ASVS level1 comes from the default workflow;
this is threat-register verification, not a comprehensive ASVS certification.

## Threat register

| Threat ID | Category | Disposition | Status | Concrete evidence |
|---|---|---|---|---|
| T-13-01-01 | Tampering | mitigate | CLOSED — implementation verified | `backend/alembic/versions/0019_portfolio_management_backfill.py:38` — Rejects noncanonical/duplicate legacy active names before bounded backfill; metadata-only closed-root exception compares every non-key column. Regression: `backend/tests/test_portfolio_management_migrations.py:209`. |
| T-13-01-02 | Elevation of privilege | mitigate | CLOSED — implementation verified | `backend/alembic/versions/0019_portfolio_management_backfill.py:62` — Every legacy user, including zero-book users, receives a legacy latch; initializer returns the existing latch instead of granting. Regression: `backend/tests/test_portfolio_funding.py:134`. |
| T-13-01-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-02-01 | Elevation of privilege | mitigate | CLOSED — implementation verified | `backend/alembic/sql/0020_portfolio_management.sql:4` — Only fixed10000 cash/baseline and paired immutable journal are inserted; app accounts INSERT/sequence authority revoked. initialize has once-only latch. Regression: `backend/tests/test_portfolio_management_authority.py:269`. |
| T-13-02-02 | Tampering | mitigate | CLOSED — implementation verified | `backend/alembic/sql/0020_portfolio_management.sql:20` — Owner/key payload replay precedes cap/name/quota; closed original refuses rather than creating. Regression: `backend/tests/test_portfolio_management_authority.py:144`. |
| T-13-02-03 | Denial of service | mitigate | CLOSED — implementation verified | `backend/alembic/sql/0020_portfolio_management.sql:7` — Owner FOR NO KEY UPDATE precedes account; ten-active check under mutual owner serialization;2s lock timeout. Non-key lock permits dividend FK KEY SHARE and avoids the demonstrated owner/root inversion; see CR-02 refresh below. Regression: `backend/tests/test_portfolio_management_authority.py:168`. |
| T-13-02-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-03-01 | Elevation of privilege | mitigate | CLOSED — implementation verified | `backend/app/db/schema_contract.py:13` — Current admits0020 only with exact preflight/catalogue/ACL; actual retained0017 consumer refuses successor. Regression: `backend/tests/test_portfolio_management_admission.py:30`. |
| T-13-03-02 | Elevation of privilege | mitigate | CLOSED — implementation verified | `deploy/db/bootstrap-roles.sql:225` — Fixed catalogue/ACL admission refuses public rewrite rules, unsafe schema/database ownership, effective CREATE and private helper EXECUTE; app funding writes restricted. Regression: `backend/tests/test_portfolio_management_grants.py:335`. |
| T-13-03-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-04-01 | Tampering | mitigate | CLOSED — implementation verified | `deploy/tests/portfolio-sources.py:212` — Retained0017 uses complete fixed4b4320b source archive; exact archive/source/image Config/RootFS binding precedes imports. Regression: `deploy/tests/test-portfolio-fixture-contracts.py:54`. |
| T-13-04-02 | Tampering | mitigate | CLOSED — implementation verified | `deploy/tests/portfolio-management-recovery-fixture.py:89` — 0020 projection requires exact table/identity/state shape and independent pre-backup snapshot; closed journal, zero latch and sequences retained. Regression: `deploy/tests/test-portfolio-management-recovery.py:552`. |
| T-13-04-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-05-01 | Tampering | mitigate | CLOSED — implementation verified | `deploy/verify-restore.py:1177` — No-ACL catalogue/schema/management state authenticated before transactional fixed17-routine revocation/grants; creator and payout EXECUTE remain quarantined. V2 package/source inventory exact. Regression: `deploy/tests/test-portfolio-management-recovery.py:330`. |
| T-13-05-02 | Elevation of privilege | mitigate | CLOSED — implementation verified | `backend/app/db/portfolio_migrate.py:62` — Finite authenticated migration/source lane; retained consumer rejects successor before writes; destructive authority downgrade explicitly refused. Regression: `deploy/tests/test-portfolio-migration-runner.py:90`. |
| T-13-05-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-06-01 | Spoofing/Elevation of privilege | mitigate | CLOSED — implementation verified | `backend/app/api/v2/portfolios.py:97` — CurrentUserDep/CsrfDep precede body parsing; services bind user.id, never client owner/cash; SQL metadata owner+active checks. Regression: `backend/tests/test_portfolio_creation.py:187`. |
| T-13-06-02 | Denial of service | mitigate | CLOSED — implementation verified | `backend/app/api/v2/portfolio_management.py:25` — Streaming length independently bounded8192; duplicate JSON fields rejected; owner/IP attempts bounded with TTL, durable SQL100successful grants/UTCday, replays exempt only grant quota. Regression: `backend/tests/test_portfolio_creation.py:246`. |
| T-13-06-03 | Tampering | mitigate | CLOSED — implementation verified | `backend/app/services/portfolios.py:80` — Bound SQL call commits paired root/journal or rolls back; same original UUID/canonical payload returns existing root; response failure remains private recoverable unknown. Regression: `backend/tests/test_portfolio_creation.py:259`. |
| T-13-06-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-07-01 | Information disclosure | mitigate | CLOSED — implementation verified | `backend/app/services/portfolio.py:72` — Owner/active predicates and paired root/user joins; original stock proof scoped root/user/coin/generation; final locked membership recheck. Regression: `backend/tests/test_portfolio_overview.py:334`. |
| T-13-07-02 | Tampering | mitigate | CLOSED — implementation verified | `backend/app/services/portfolio.py:194` — Shared captured valuation instant and common assembler, stored per-book baselines, original/current authority intersection; incomplete totals remain unavailable. Regression: `backend/tests/test_portfolio_overview.py:217`. |
| T-13-07-03 | Denial of service | mitigate | CLOSED — implementation verified | `backend/app/services/portfolio.py:106` — Root limit11 detects corrupt over-cap; loader uses one financial plus one authority/membership query; no per-root provider polling. Regression: `backend/tests/test_portfolio_overview.py:101`. |
| T-13-07-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-08-01 | Tampering | mitigate | CLOSED — implementation verified | `frontend/src/api/portfolioManagement.ts:34` — Exact three-key metadata, canonical string ID/name/description; POST snapshots raw key/body before auth await, malformed/5xx remains unknown. Regression: `frontend/src/api/portfolioManagement.test.ts:81`. |
| T-13-08-02 | Tampering | mitigate | CLOSED — implementation verified | `frontend/src/api/portfolioOverview.ts:12` — Exact19keys <=10 ordered roots; reuse strict monetary detail parser, common valued_at and exact oldest source timestamps; no numeric coercion. Regression: `frontend/src/api/portfolioOverview.test.ts:169`. |
| T-13-08-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-09-01 | Tampering | mitigate | CLOSED — implementation verified | `frontend/src/lib/portfolioCreationAttempt.ts:62` — One bounded validated metadata-only sessionStorage envelope, nonce/opaque owner binding; persist/readback before POST; unknown retains exact key/payload and explicit retry. Regression: `frontend/src/hooks/usePortfolioManagement.test.tsx:185`. |
| T-13-09-02 | Information disclosure | mitigate | CLOSED — implementation verified | `frontend/src/hooks/usePortfolioManagement.ts:391` — Owner/session/operation guards before publication, persistence resolution, invalidation and receipt navigation; abort cleanup cannot transfer authority. Regression: `frontend/src/hooks/usePortfolioManagement.test.tsx:310`. |
| T-13-09-03 | Tampering | mitigate | CLOSED — implementation verified | `frontend/src/lib/portfolioMetadataEvents.ts:9` — Broadcast only strict opaque emitter/root identity; server GET supplies authority. Editor revision/operation lease preserves dirty draft and requires review. Regression: `frontend/src/hooks/usePortfolioManagement.test.tsx:326`. |
| T-13-09-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-10-01 | Tampering | mitigate | CLOSED — implementation verified | `frontend/src/hooks/useTrade.ts:80` — Unknown state retains frozen original key/payload/root/name; strict target guards for previews, narrow original identity solely recovery/revocation. Actual pages now consume retained name across remount. Regression: `frontend/src/pages/TradeRenameRecovery.test.tsx:53`. |
| T-13-10-02 | Tampering/Information disclosure | mitigate | CLOSED — implementation verified | `frontend/src/hooks/useStockTrade.ts:630` — Stock attempt captures root/owner/session, side/quantity/key/quote/name; delayed effects guarded and cannot publish or retarget sibling; receipt consumer repaired. Regression: `frontend/src/hooks/portfolioStock.test.tsx:457`. |
| T-13-10-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-11-01 | Information disclosure/Tampering | mitigate | CLOSED — implementation verified | `frontend/src/hooks/usePortfolioOverview.ts:31` — Owner/session overview key, captured query identity guards, shared per-root detail/overview safety proof+clock and expiry projection; no source-time renewal. Regression: `frontend/src/hooks/usePortfolioOverview.test.tsx:163`. |
| T-13-11-02 | Tampering | mitigate | CLOSED — implementation verified | `frontend/src/hooks/useEventHistory.ts:50` — Owner/root/session cursors/seen sets; post-await current checks before scoped cancellation/invalidation; comparison invalidation once for attributable new events. Regression: `frontend/src/hooks/portfolioHistory.test.tsx:378`. |
| T-13-11-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-12-01 | Information disclosure/Tampering | mitigate | CLOSED — implementation verified | `frontend/src/pages/PortfoliosPage.tsx:228` — Plain JSX-escaped names/descriptions, reused exact-money formatter; incomplete values explicitly unavailable per strategy, no pooled total. Regression: `frontend/src/pages/PortfoliosPage.test.tsx:1`. |
| T-13-12-02 | Tampering | mitigate | CLOSED — implementation verified | `frontend/src/components/PortfolioCreateForm.tsx:209` — Submitted original fields frozen/read-only, explicit retry/close, guarded receipt; metadata save disabled for pending/invalid/stale-review and guarded operation/revision. Regression: `frontend/src/hooks/usePortfolioManagement.test.tsx:519`. |
| T-13-12-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-13-01 | Tampering | mitigate | CLOSED — implementation verified | `frontend/src/components/PortfolioSwitcher.tsx:40` — Native selection changes local draft only; explicit Open requires current verified target; owner/session/path key resets stale draft; creation receipt checks isCurrent before navigation. Regression: `frontend/src/components/PortfolioSwitcher.test.tsx:1`. |
| T-13-13-02 | I/E | mitigate | CLOSED — implementation verified | `frontend/src/components/PortfolioTargetBoundary.tsx:57` — Only ready verified target mounts financial Outlet. Empty/ambiguous/unavailable provide choices without fallback or grant; unresolved unavailable notice only boolean and no finance. Regression: `frontend/src/components/PortfolioTargetBoundary.test.tsx:1`. |
| T-13-13-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-14-01 | Tampering | mitigate | CLOSED — implementation verified | `backend/app/services/trading.py:211` — Crypto and stock lock owned active root and paired holdings; transaction debits only selected cash; per-root immutable receipts/history and stored baselines. Regression: `backend/tests/test_portfolio_strategy_lifecycle.py:229`. |
| T-13-14-02 | Tampering/Repudiation | mitigate | CLOSED — implementation verified | `backend/app/services/dividends.py:64` — Dividend original/payment/root+user checks and SQL idempotency; splits/reconciliation select active roots; duplicate worker/history attribution tests cover independently created siblings. Regression: `backend/tests/test_portfolio_strategy_events.py:106`. |
| T-13-14-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-15-01 | Tampering | mitigate | CLOSED — implementation verified | `deploy/tests/run-stock-browser.py:25` — Explicit12-spec default inventory and61critical module command, omission/symlink contracts; no discovery silently skipping management coverage. Regression: `backend/tests/test_critical_coverage_config.py:71`. |
| T-13-15-02 | Tampering/Elevation of privilege | mitigate | CLOSED — implementation verified | `deploy/tests/run-portfolio-validation.py:127` — Seven exact stages/current0020 and fixed retained0017; authenticate archive/currentCORE/units/payload/image bytes before/after every stage including failure; TLS parity equality. Regression: `deploy/tests/test-portfolio-validation-contracts.py:22`. |
| T-13-15-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-16-01 | Tampering/Information disclosure | mitigate | CLOSED — implementation verified | `frontend/e2e/portfolio-strategies.spec.ts:159` — Real protected HTTP writes then lost transport, reload/same-key/rename/cap/cross-tab/sibling/owner/late callback scenarios and exact-text before-oracle; no mocked core successes. Regression: `frontend/e2e/portfolio-strategies.spec.ts:510`. |
| T-13-16-02 | Repudiation | mitigate | CLOSED — implementation verified | `deploy/tests/portfolio-ui-evidence.py:74` — Complete source-owned72-state265-artifact matrix with exact source/browser/state/path/HTML/trace correspondences; flagsfalse disallow inferred native/owner approval; drift/coherent omissions refused. Regression: `deploy/tests/test-portfolio-ui-evidence.py:112`. |
| T-13-16-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-17-01 | Tampering/Repudiation | mitigate | CLOSED — actual whole qualification verified | `deploy/tests/run-portfolio-validation.py:87` retains source guards and the full CI command inventory. Final campaign6 actual all-security exits0 at9527e35 in3373.046s, with3343backend tests, all61critical modules100%,1194frontend tests,79browser passes/one existing deployed-CSPskip and all5immutable-image policies. Raw log SHA9ee807da… and exact command/result/coverage/image receipts independently verified; see final audit below. |
| T-13-17-02 | Tampering/Elevation of privilege | mitigate | CLOSED — actual whole qualification verified | `deploy/tests/run-portfolio-validation.py:127` authenticates archive/currentCORE/units/payload/source/image records before and after every stage, including failure; :156 compares TLS authority. Final campaign6 recovery exits0 in2792.054s at the SAME9527e35, all7passed-authenticated and same_archive_final_ci=true. Fresh canonical archiveSHA6fb79a45… is independently measured, with distinct producer-created inode, source-destroyed0017/0020 cold oracles, exact authority parity, supported rollback/refusal and empty21resource checks. |
| T-13-17-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |
| T-13-18-01 | Repudiation | mitigate | CLOSED — human response verified | `13-UAT.md` records the actual separate “Accept the Phase 13 UI” response against preserved approved SHAeac08181… packet and the unchanged management inputs after CR-01. Later repairs do not alter those management surfaces; final source-map comparison and packet verification at9527e35 reconcile the current340-input SHA724607… packet without rewriting capture-time flags. |
| T-13-18-02 | Repudiation | mitigate | CLOSED — human response verified | `13-UAT.md` records the separate actual “Native 200% zoom passes” response, not emulation or inherited Phase12 approval. Browser/version was not supplied and is not invented. Automated captureflags remain false; final source-bound packet SHA724607… and actual campaign6 verification now match the unchanged management inputs. |
| T-13-18-SC | Tampering | accept | CLOSED — accepted risk | Exact common accepted-risk entry AR-01 below; no package-wide exception. |

## Accepted risks

### AR-01 — existing issue35, no expanded exception

Owner acceptance is recorded in
`.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-ACCEPTED-RISK.md`:
“can you create an issue in gh for the future about this and continue without fixing it?”
Follow-up: https://github.com/YokAI-open/Birja/issues/35.
Only GHSA-fc5q-39xc-vjpf / CVE-2026-112366 is accepted until
**2026-12-17T00:00:00Z**. Current locked picomatch4.0.7/nested2.3.2 and Node
npm-bundled4.0.4 at the exact tinyglobby path remain unresolved. This is accepted
risk, not remediation, a new package approval or proof of non-exploitability.

ManifestSHA256 `73cd4f25fb329d7d0711321ee56dd9f07b25426eb9ddb69f3491396c2ccbdb59`;
lockSHA256 `1461d4f89e875a5b915278e9d39ba413608fa4ff816fab6be6b21e280db5475b`.
`deploy/audit-frontend.mjs` and `deploy/scan-images.py`/their accepted-risk helper
retain raw reporting and exact advisory/target/path/version/hash/expiry bounds.
Other HIGH/CRITICAL, changed source/locks, expired approval and malformed/network
failure remain blocking. The18SCrows reference this one accepted scope; they are
not18independent exceptions. Plan17 must still measure fresh raw audit/image
results against this policy; the prior Phase12campaign cannot supply those passes.

## Qualification disposition — final

- **T-13-17-01 CLOSED:** actual complete all-security at9527e35 passed; raw log,
  exact literal command and exit0,61critical statement/branch records, full current
  browser inventory, raw dependency audits and all five immutable-image policies
  are independently checked. Earlier failures remain failed history.
- **T-13-17-02 CLOSED:** actual uninterrupted seven-stage recovery followed that
  security pass at the same source, using a newly producer-created exclusive
  canonical archive. Every post-stage source/archive/image guard passed; exact
  fresh/upgraded TLS authority and owned cleanup are verified.
- **T-13-18-01/02 CLOSED:**13-UAT.md and13-18-SUMMARY.md preserve the two explicit
  owner responses and final unchanged-management source association. Current
  packet SHA724607… matches all340render inputs in the final campaign receipt.
  Browser/version was not supplied and is not invented; automated manifest
  owner/native flags remain false rather than being relabeled human outcomes.

No unresolved qualification or implementation threat remains. This does not
close separate Phase7live work, issue35, or the milestone's future public deletion
and whole-lifecycle phases. It adds no risk waiver and authorizes no publication,
production change or provider operation.

### Earlier qualification disposition (historical, superseded)

- **T-13-17-01:** produce complete current-source all-security receipt with actual
 61critical statement/branch coverage, raw dependency audit, full current browser
 command and five immutable-image policies. No composite partial pass.
- **T-13-17-02:** produce new full seven-stage same-archive receipt, independent
 before-backup exact oracle, current0020 and fixed retained0017/earlier profiles,
 source destruction/cold restore, restricted verified-TLS fresh/upgraded parity,
 authenticated rollback/refusal and exact-owned cleanup.
- **T-13-18-01/02 — human-response evidence CLOSED:** both explicit replies are
 persisted in13-UAT.md, preserving their approved packet association. No repeated
 owner confirmation is needed for the backend-only CR-02 repair. Current packet
 recapture at99166d9 is separately pending and must be reconciled by the parent
 with UI-EVIDENCE/UAT and final17source receipts before global completion. It is
 not another missing owner response or a newly accepted security risk. Capture-time
 automatedfalseflags remain false; browser/version is not invented.

These two OPEN records are planned unfinished campaign evidence, **not two
newly identified vulnerabilities**. No additional owner waiver is requested. Refresh
this report from actual final receipts and durable UAT before asserting
`threats_open: 0` or allowing phase completion.

## Audit trail

2026-11-18: first independent pre-qualification pass at runtime6bfb447.
58registered threats;54closed (36implemented mitigations,18same-scope accepted
risk references);4qualification gates pending;0demonstrated implementation gaps;
0unregistered summary flags. Integrated CR-01 is resolved by retained hook-name
consumers and six real routed lost/pending/filled rename/remount/replay tests.
Final campaign and owner source-association outcomes are intentionally not inferred.

## CR-02 mitigation refresh at99166d9

The earlier implementation verification missed a real lock inversion, later
reproduced by the deterministic restricted-role dividend/HTTP management overlap
regression. This update records the defect and reviewed repair rather than
rewriting the initial pass into a claim that no defect ever existed. It maps to
**T-13-02-03** (owner/action lock coexistence) and **T-13-14-02** (accounting
worker/action ordering), with source-authentication propagation covered by
T-13-03-01/02, T-13-04-01 and T-13-05-01.

Inspected actual203815f..99166d9diff: all three management user-row locks in
`backend/alembic/sql/0020_portfolio_management.sql:16`, `:63`, `:96` now use
`FOR NO KEY UPDATE`. That lock still conflicts with another such owner lock,
serializing cap/name/grant/replay/metadata decisions, but permits ledger user-FK
`KEY SHARE` while management waits on an account held by the scheduler. Account
`FOR UPDATE`, owner predicates, immutable request binding, fixed10000grant,
canonical payload, quota/cap ordering and transactional boundaries remain.
Retained0017dividend SQL and historical0015–17/0019 are unchanged.

Read independently clean13-REVIEW and13-17-FIXTURE-REVIEW resolution. The
1172-record measured catalogue differs only in the three function definitions;
ACLs remain `041a948470f9692628da43b35263a47bf58f4815310a0793d5eec099fa64c87e`.
The new catalogue is
`535cacb140a3a1753b5cf27e2eadcb80bc272a9b12772defd3936a3edc6c2209`.
Source/migration/bootstrap/producer/restore/current-fixture pins bind the new
definitions; normal/quarantined/no-ACL authority fingerprints are updated without
removing equality checks or repinning financial/privilege oracles. Reviewed the
actual source changes and current-fingerprint-delta receipt. Verified all11file
SHA256values and four raw-log hashes from
`/tmp/birja-p13-cr02-repair-receipt.json` against disk; no test was rerun here.

The regression at `backend/tests/test_portfolio_strategy_events.py:410` covers
metadata and original creation replay, waits for actual PostgreSQL blocking PID
state before the dividend FK insertion, and requires successful200, same root,
cash10000.50 and exactly two original creation records. It does not accept503
or skip the overlap. Separate restricted-role checks execute initialization,
creation and rename under unchanged grants. The verified executor receipt reports
70focused cases passing363.48s, two direct overlap cases12.71s and33offline
contracts (8+11+8+6), with owned resources empty. These remain affected-source
proof, **not** final complete security or encrypted recovery qualification.

Refresh totals:58registered,56CLOSED (36implementation +2human-response
mitigations +18same-scope accepted-risk references),2OPEN planned complete
campaigns,0open implementation gaps,0unregistered summary flags. Current packet
binding remains explicitly recapture_pending until the capture worker supplies
its99166d9receipt. Only this SECURITY.md changed; no tests/DB/browser/source/git/
provider/production operations or new acceptance occurred in this refresh.


### Parent source-association update after capture

Capture worker completed current99166d9 proof inb20bdf1:20browser cases,12strict
contracts and120offline layouts pass. Current packet SHA724607e83592bd1bda5e86a0b92217478aba93b53127b7cdf5f2d04f0142c361
and340-input digeste082f97d9aaa758fa17a6060877328ed6f6dd39c31f2d66942c00bb7dba47a47
are recorded in13-UI-EVIDENCE and13-UAT. Exact four-backend-input delta, zero
frontend changes; owner UI/native200 association is preserved. The prior
recapture_pending note is resolved by this actual receipt. Only the two actual
Plan17 whole-campaign records remain OPEN; no final qualification is inferred.


### Reviewed deployment-source and fixture follow-up

Campaign3 was stopped by real source admission in the compatibility fixture.
Genuine immutable source revealed CR-03: deploy.sh pinned an obsolete0017marker.
The one-line74ee5ea repair now matches both the unchanged current migration and
fixed retained4b4320b object (`92cff0699a40b0b8f5f4d66bc56a39a2ef88e3184860d86d6957607a3413f32b`).
Independent13-REVIEW records the measured source check and preserved47-case
legacy/current/corrupt/missing-source refusal matrix. This resolves a source-binding
implementation defect mapped to existing retained/current-source threats, without
editing0017/schema/financial/authority profiles or accepting a new risk.

Test-only follow-ups531cf48/fa28d8e preserve strict refusal messages and isolate
historical0007–0014 probes; borrowed-stack ownership now preserves the funded
current database. Independent review is clean. Actual final15ordered diagnostics
atfa28d8e all pass, including five immutable image policies with zero blocking
findings; only the already accepted issue35Node finding is present. The before/
after funded0020plain dump SHA matches
`2c16a2492129a3e50164cf1064d8d893fa230aef0b40b129a361eb22d6cb49bc`,
borrowed container identities match, all12owned resource-label checks are empty.
Full source/log/image receipts live at
`/tmp/birja-p13-security-tail-repair-receipt.json`.

These are diagnostic/review records, not a substitute for complete security or
seven-stage same-archive recovery. The same two campaign-evidence threats stay
OPEN until actual whole commands succeed at the final frozen revision. No new
risk waiver, dependency/image upgrade, provider or production operation occurred.
No UI render input changed, so source-bound packet724607 and owner acceptance
remain valid; frontend/backend application render source stays99166d9.


### CR-04 strict image binding repair and diagnostic follow-up

Complete all-security at535a5b7 passed3374.206s, including3343backend tests,
61critical modules100% (5287statements/1668branches),1194frontend tests,
79browser passes/one retained deployed-CSP skip, full infra tail and five image
policies. This is measured history for535a5b7, not qualification of later helpers.

The following whole recovery correctly failed its exact image-ID guard after
retained0017/current0020cold operations returned: repeating a deterministic build
tag replaced an OCI index ID. CR-04 was repaired by RED5693083/GREEN312d8c9:
private first-use campaign records are reused only after archive/source/context
and exact ID/config/RootFS validation; missing/changed IDs refuse without rebuild.
New aliases are campaign-scoped. The guard and comparison equality are unchanged.
Independent code review is clean;17image methods/26related contracts and actual
separate-process Docker first-build/zero-build-reuse/missing-IDrefusal proofs pass.
Receipt:`/tmp/birja-p13-image-binding-repair-receipt.json`.

Remaining-stage diagnostics used a separate219289600byte archiveSHA
6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92.
Roles and both TLS stages passed authenticated; user interruption stopped selected
rollback without a completion receipt. Exact-owned orphaned synthetic resources
were inventoried and removed; source, private records and archives were preserved.
A resumable one-shot reran only that diagnostic stage, passing950.7065s with all
six image-record hashes unchanged, fresh/upgraded authority equal and all21owned
resource checks empty. It retains explicit false fullsecurity/sevenstage flags:
`/tmp/birja-backup-test-phase13-rollback-resume-312d8c9-20261118/receipt.json`.

This diagnostic composite is not an uninterrupted seven-stage pass. Final new
all-security and seven-stage recovery remain required at the same frozen source;
the same two evidence threats remain OPEN. Failed archiveSHA2d182e0b91488138cf4a9bbe96b2a43e35f3f99e785dfb45543f3c76e0318375
is preserved under`/tmp/birja-phase13-proof-campaign4-failed-535a5b7/` for the
new canonical campaign directory to be created exclusively. No new waiver,
provider/production operation or UI render change occurred.


## Final Security Audit — 2026-11-19

**Result: SECURED.**58registered rows,58CLOSED,0OPEN,0implementation gaps,
0qualification pending and0unregistered summary flags. All18plan-time threat
models were cross-checked against the individual register; no row was dropped.
Read current implementation enforcement points and their named negative tests;
followed the final runner and exact-ID reuse path in source rather than treating
summary assertions as execution evidence. Plans17/18, actual UAT, clean code/
fixture review,24/24UI review and final source-map associations were reconciled.
Plan17's local/recovery records were available during final verification; their
raw underlying receipts, not document existence, support the closures.

### Independently checked actual whole results

- Frozen tested HEAD:`9527e358bc6953cec7580043703324db194ba396`.
- Actual literal all-security command exit0,3373.046358s. Raw log SHA256:
  `9ee807da3bcc03f8d062a2da9c46b80df5cf8b84fa4becafc61d9e085a3e56bb`.
- Actual literal recovery command exit0,2792.053910s, launched only after the
  complete security command's successful exit at that same source. Raw log SHA256:
  `1d08f0b14d96e4e2bb8d9fdca6d1afa863653665961a298b40dc8054b327a896`.
- Supervisor receipt SHA256:
  `09909cf5b6874c2304b34d6908db90db3408a3778e53612e17b52b1850e8c9b1`;
  reports ok=true, source/HEAD/preserved archives unchanged and all21owned
  container/network/volume checks empty. Both result JSONs' exact argv, source,
  return codes, timestamps and raw-log hashes were read and checked.
-3343backend tests pass; exported overall combined coverage99.8599767%. The
  actual CI include list contains exactly61critical modules, and each exported
  coverage record has zero missing statements and branches:5287statements and
 1668branches at100%.1194frontend tests and79actual browser passes plus one
  existing deployed-CSPskip are recorded in the same full command. All12explicit
  browser specifications and20new management cases remain required.
- Python audit clean; raw npm audit retains14moderate findings and0HIGH/CRITICAL.
  All five final immutable-image targets report0qualifying,0accepted and0blocking
  findings under the final database metadata. Every raw image-report file and
  six campaign image-binding-record hashes were independently recomputed.
  Accepted-risk count0 is not a dependency fix or closure of issue35: package,
  lock and narrow expiry-bound exception remain unchanged and tracked.

Actual files live under
`/tmp/birja-phase13-plan17-campaign6-20261118-9527e35/`:
`receipt.json`, `all-security-result.json`, `recovery-result.json`, raw logs,
`backend-coverage.json`, `image-reports/`, `fresh-archive-identity.json` and
`ui-final-source-verify.json`. No new tests or database/image operations were
performed by this auditor; these are independently checked executor receipts.

### Exact archive/source and image evidence

The new canonical archive is219289600bytes, SHA256
`6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92`.
Independent hashing matches both actual command receipts and the final
same_archive_final_ci line. `fresh-archive-identity.json` proves the canonical
path was absent before producer execution and the actual producer created a
new inode700678, distinct from diagnostic867057. Deterministic matching content
is not copying or reusing an earlier proof. Previous failed and diagnostic
archives remain preserved; none is substituted for final qualification.

All seven statuses are passed-authenticated: image-transition, retained-roundtrip,
current0020-cold, roles, tls-upgraded, tls-fresh and selected-rollback. Raw log
lines116/124 independently record genuine0017/current0020 encrypted cold restore,
source_destroyed=true, immutable_before_oracle=true and quarantine=true. TLS
transport negatives, restricted authority, exact fresh/upgraded parity and
supported rollback or explicit refusal are present in the same actual log.
The authenticated tooling archive itself is strict USTAR; actual database
backup/restore uses encrypted restic snapshots within these operations. Those
artifact roles are not conflated into a claim that the tooling tar is encrypted.

Read `authenticate` and `execute_stages`: exact archive/currentCORE/unit/source/
fixed-retained/image bytes are checked before/after every stage including failure,
then authority objects must compare equal. CR04's private first-use image binding
reuses only exact IDs with matching source commit, app tree, context, config and
RootFS; absent/mutated recorded IDs refuse without build. No equivalence waiver
or record replacement is used to clear the earlier failed image guard. Current
runtime/config/test bytes independently match the frozen source snapshot; later
commits are planning records only. Retained0017 source/profile is unchanged.

### Human/source association and preserved boundaries

The final manifest's340source entries exactly equal the campaign's render map,
render digest `e082f97d9aaa758fa17a6060877328ed6f6dd39c31f2d66942c00bb7dba47a47`,
ZIP SHA256 `724607e83592bd1bda5e86a0b92217478aba93b53127b7cdf5f2d04f0142c361`.
Actual final packet verification exits0. Compared with the original owner-approved
packeteac081…, the only seven changed render-map entries are the two trade
consumers/their regression and four backend authority inputs; no management
surface input changed. The accepted overview/create/edit/switch UI and separate
actual native200% response remain valid under the recorded association.

Existing AR01 remains one narrow owner-accepted issue35 scope repeated by18SCrows,
with current manifest/lock hashes independently matching the approved values and
expiry2026-12-17T00:00:00Z unchanged. No new acceptance, package/image pin change,
provider call, production access, implementation edit or commit was made here.
Global requirement checkboxes and phase completion belong to the parent after
separate goal verification; this audit does not modify them.
