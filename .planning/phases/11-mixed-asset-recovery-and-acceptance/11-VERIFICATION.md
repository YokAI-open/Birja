---
phase: 11-mixed-asset-recovery-and-acceptance
verified: 2026-11-13T19:55:04Z
status: passed
score: 3/3 must-haves verified
overrides_applied: 0
reviewer: /root/phase11_execute04/goal_verify
source_head: 32acccea038ee59bdeae0a712fc721d4a9827aa7
executable_source: a7f965fe27bf3da6172f3110245ff31c3627fa12
---

# Phase 11: Mixed-Asset Recovery and Acceptance Verification Report

**Phase Goal:** Operator can restore the full mixed-asset financial state exactly, and complete user stock journeys are proven without weakening protections.
**Verified:** 2026-11-13T19:55:04Z
**Status:** passed
**Re-verification:** No — initial verification; no previous Phase11 VERIFICATION existed.
**Reviewer:** Independent delegated goal verifier, distinct from implementation and code/security/UI reviewers. Only this report was authored; no commit or canonical state change.

## Goal Achievement

### Observable Truths

The SDK `roadmap.get-phase 11 --raw` independently returned the following three non-MVP success criteria. Plan-specific truths are checked beneath their corresponding criterion rather than counted as extra roadmap outcomes.

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Operator can restore an exact encrypted backup of holdings/cash, announcement revisions, entitlements, dividends, actions and History with matching totals and duplicate-prevention state, using compatible retained tools, schema and restricted-role grants. Replay cannot repeat fills, payments, corrections or splits. (SAFE-02) | VERIFIED | Real encrypted repository roundtrips and retained0007–0014 canonical/schema/authority/sequence checks; actual roles and both TLS lanes; current0014 selected cutover, twice owner-clone replay with runtime42501 quarantine, intended old-source refusal and tested-source failed-attempt recovery. Independent archive/source/raw equality checks below. |
| 2 | Real isolated PostgreSQL tests prove stock/crypto contention, post-lock expiry, closed-market replay, dividend cutoff/revision/concurrency, split ordering and uncertain-action suspension with exact-money assertions. (SAFE-03) | VERIFIED | Actual patched full backend log:2557 passed/310.53s,99.87%;47 critical modules4565statements/1462branches100%. Real independent-client concurrency, DB-clock waits, immutable receipt and dividend lineage assertions exist in executable tests, not mocked economic success. |
| 3 | Browser journeys prove discovery, preview/confirmation, open/closed trading, combined portfolio, dividends, splits, corrections, stale/unknown states and crypto coexistence; applicable coverage, dependency/image security and required CI gates remain enforced. (SAFE-03) | VERIFIED | Source-bound actual49browser passes/326.1s;697frontend tests; complete required CI/audit/strict-five-image graph remains wired. Accepted owner UI/native200% scope is preserved by source/build/response continuity and the independent24/24 UI review. Sole deployed-CSP skip remains explicitly outside local proof. |

**Score:** 3/3 roadmap truths verified. No failed or uncertain local must-have; no override used.

### Complete Requirement and Plan-Truth Coverage

| Clause / acceptance rows | Concrete trigger, executable path and independent oracle | Status |
|---|---|---|
| SAFE-02 mixed holdings/cash; announcement revisions; entitlement/payment/action/event state; consistent totals (R01–R02) | `ops-fixtures.py` roundtrip/successor fixtures exercise encrypted backup and restore; `verify-restore.py` canonical checks include full row hashes/counts/totals, schema constraints/indexes/function authority and dumped sequence last_value/is_called. Corruption and unavailable-repository controls must reject while originals remain unchanged. | VERIFIED |
| SAFE-02 duplicate-prevention including fills, splits, dividends/corrections (R03) | Actual `stock-runtime-fixture.py` and `dividend-execution-fixture.py` replay saved IDs through services; receipt/dividend digests and complete canonical/identity equality reject repeated cash, quantity, basis or History effects. Original and held/reconciled successor lineage remain distinct. | VERIFIED |
| SAFE-02 schema, restricted grants and retained tools before rollout (R04–R07; Plan01) | Authenticated retained manifest supplies tested SHA; `deploy.sh:admit_application_source` runs before pending/checkout/build/start in deploy and rollback. At0014 only that SHA passes. Actual installed synthetic launcher starts restricted verified-TLS current0014 services, preserves originals, refuses old runtime with the exact diagnostic and recovers failed attempt to tested source. Separate0008 lane proves actual historical downgrade. | VERIFIED |
| SAFE-03 contention/proceeds and once-only keys (F01) | `test_stock_trading_concurrency.py:test_stock_crypto_competing_spends_and_keys`, parallel first holdings/sells and immediately reusable proceeds use independent clients, actual transactions and literal Decimal balances/effect counts. | VERIFIED |
| SAFE-03 post-lock expiry and closed replay (F02–F03) | `test_stock_trading_waits.py` advances actual clock during lock waits and checks refusal without effects; service/API replay tests resolve original receipt/key after close without another fill or current-market permission fabrication. | VERIFIED |
| SAFE-03 dividend cutoff/revision/concurrency (F04–F06) | Dividend payment/wait/correction/concurrency suites assert historical eligibility, immutable original, A→B→A corrections, duplicate workers, spend races, lost-commit-response retries, holds and funded reconciliation. Example independent oracle: eight workers yield one payment and cash101, with starting_cash10000 unchanged. | VERIFIED |
| SAFE-03 split ordering and uncertain suspension (F07–F09) | Stock wait/action/ownership suites exercise actual fill→forward split and ordering; uncertainty denies execution and complete valuation. Event History tests independently check owner filtering, deterministic cross-kind ordering and immutable lineage. | VERIFIED |
| SAFE-03 browser stock journeys and crypto coexistence (B01–B05) | Real browser authenticated requests cover catalogue, ask/bid fills, explicit reprice confirmation, closed drafts, original-key lost-response recovery, combined portfolio, split/history, dividends/held/reconciled corrections and late former-owner responses. Expected values include buy2×102→cash9796 and actual split quantity2→3; successful financial POSTs use real services. Synthetic read/provider inputs establish presentation and deterministic conditions only. | VERIFIED |
| SAFE-03 coverage/security/CI; protected acceptance (B06/G01–G05; Plan02–04) | Backend80%/critical100%, frontend80%, unrestricted pip audit, npm high gate, strict images and required backend/frontend/image/e2e/ops aggregate remain enforced. Same archive is forwarded through both selected lanes; missing/reordered stages and swallowed failures are mutation-tested. Separate code0blocker/0warning, security14/14closed, UI24/24 reviews clear required scope. | VERIFIED |

Both SAFE-02 and SAFE-03 are satisfied **locally** in full. All plans declare these two IDs; REQUIREMENTS maps no additional Phase11 requirement, so none is orphaned. Pending requirement/Plan04/sign-off labels in coordinator-owned artifacts describe pre-verdict workflow state and are not contradictory implementation evidence. Coordinator should reconcile them after this verdict.

## Required Artifacts and Key Links

| Artifact | Substantive implementation / wiring verified | Status |
|---|---|---|
| `deploy/deploy.sh` | Immutable40hex SHA and authenticated revision admission;0014 equality to retained tested source; both deploy and rollback invoke before mutation. Unknown/malformed targets refuse. | VERIFIED |
| `deploy/tests/selected-cutover.py` | Separate legacy/current dispatch; actual installed recovery archive, real current service fixtures, financial/sequence/original-volume checks, replay, refusal snapshot, failed-attempt rollback and finally-owned cleanup. | VERIFIED |
| `deploy/tests/test-rollback-db-security.sh` | Calls legacy integration, selected legacy, then current0014 with the same `args.recovery_bundle`; retained self-test asserts intended admission failure and zero mutation. | VERIFIED |
| `.github/workflows/ci.yml`, `deploy/tests/test-ci-ops.py` | Archive checksum/CORE checks through serial stages, rollback `--recovery-bundle` wiring, both selected lanes and failure-propagation contracts; required aggregate retains coverage/audit/image/e2e/ops obligations. | VERIFIED |
| Compatibility/selected contract tests | Actual shell control-flow refusal checks; JSON row/key ordering accepted while changed image fields and row multiplicity fail. Seven selected tests independently rerun here. | VERIFIED |
| `11-ACCEPTANCE.md`, `11-LOCAL-PROOF.md` | R01–R07/F01–F09/B01–B06/G01–G05 map concrete oracles and private source-bound receipts. Historical/pre-verdict wording requires coordinator reconciliation; actual raw evidence, not those labels, determined this report. | VERIFIED |

### Data-Flow Trace (Level 4)

| Consumer | Data source and wiring | Status |
|---|---|---|
| HistoryPage / event details | `useEventHistory` → `fetchEventHistory` → authenticated event-history route → `event_history.py` actual SQL union of owner-filtered trades, split movements, payments and decisions, deterministic keyset ordering. Owner/epoch checks discard late data. | FLOWING |
| Stock ticket / combined Portfolio | Existing authenticated API/services, actual PostgreSQL balances/receipts and quote/session/action authority; actual browser fills and subsequent portfolio/history assertions verify returned values reach rendering. | FLOWING |
| Selected recovery oracle | Actual restored DB canonical/identity state → source-service receipt/payment replay → whole-state comparison; complete runtime CLI records retained and independently parsed. | FLOWING |

No hardcoded-empty dynamic consumer was identified in the changed scope.

## Independent Evidence Integrity and Source Qualification

Independently recomputed all389current executable/config source hashes,23final linked artifact hashes and113Task1 artifact hashes: zero mismatches. Independently read the recovery tar and checked all11retained CORE/unit members against both current source and recorded digest. Archive size152320000bytes; SHA256 `1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`.

| Receipt / raw evidence | Independently checked SHA256 |
|---|---|
| `/tmp/birja-phase11-gates/final-receipt.json` | `bb90d570e6b2313f7b1fd3fc5d53cf2a6ebe558831b7f0e57a4760d16255f5af` |
| `/tmp/birja-phase11-gates/task1-receipt.json` | `a9ae4672b48c9d848ab8b9e613b59f8d327c99246d89eb68915e8a2aa90608d9` |
| `/tmp/birja-phase11-gates/current0014-only.log` | `8b57f962b7cd13db8e8952b3938ccd8b285b97d362fb5bcd446acb3bb21d85d4` |
| `/tmp/birja-phase11-gates/current0014-only-report.json` | `d6ad5c0973260385dfbaeffb5d365f14e27f92d501cb690bd48da394bcf8c770` |
| `/tmp/birja-phase11-04-offline/receipt.json` | `d6c27240f771c0234b0e9ff6fc6d595908559792da97b8dec6503fcdfb6233c4` |

Current0014 raw log contains actual cutover, **two** owner-clone replay/quarantine markers, exact unsupported rollback refusal, tested-source failed-attempt rollback and cleanup. Synthetic fixture git SHA54618e52… identifies the tested copied application inside that host; campaign sourcea7f965f identifies the harness executing it. These are different identities and are not conflated.

Private `/tmp/birja-backup-test-selected0014-evidence-p487c9dv` before/after full snapshots independently compare equal (SHA256 `b5c4d146f2af9b56f8ce8b25079ad834cda01a53ea9824f46e28ea76f50490be`). Independently parsed raw image records with a Counter of full canonical JSON rows: **every field and duplicate-row multiplicity equal**. Raw byte hashes differ solely in ordering in this retained fresh pair; no field projection or row deduplication was used. Historical failed payload was not retained, so its cause remains unproven. It is not evidence for diagnosing that historical failure.

Five actual recovery stages ran atfb926d8: image transition39.639s, roundtrip452.729s, roles178.205s, populatedTLS145.445s and freshTLS145.753s. Legacy old-image/selected0008 ran at22c44d6 (100.375/276.057s); fresh complete current0014 ran ata7f965f (342.673s). Direct source comparison finds exactly three changed executable harness paths: selected-cutover.py, test-selected-cutover-contracts.py and test-rollback-db-security.sh. Reviewed deltas strengthen intended refusal, exact approved package fingerprint and order-independent complete runtime equality. Producer/restore/authority/CORE, application/Alembic, build recipes and runtime images do not change between these campaign stages; all386other mapped sources match. Affected lanes/contracts were actually rerun. This supports the qualified same-archive proof without an irrelevant full repeat.

The original full serial report remains `ok:false` (SHA256 `98e7dd2559b2fb73257bb2ac32e6985127e545c0ea3877dc39f4e0479f990122`); final current0014 report is `ok:true`. **No fresh successful complete CI block at final source, hosted CI success or production rollout is claimed.**

Runtime `sha256:2c91676c9d4408bb7ab7458a6dfef353157aef44dca18a77a9a60fe97dbfb80b`, builder `sha256:ec7544f9813f558889bb725513b524b12ee3608b93073f1f2811755b9f185856`, Node `sha256:f2e7cc228ec174d5df1bca0e61050f39b8c3685aa36095459df1b28583971feb` are receipt-bound. Patched raw pip audit reports no known vulnerabilities. Independently parsed all five patched raw Trivy reports: zero HIGH/CRITICAL including unfixed. Npm retains2low/15moderate; the high gate passes, not zero total vulnerabilities. Exact owner-approved OpenTelemetry1.45.2 repair and disclosed absent wheel signature/attestation remain in DEPENDENCY-REVIEW; no new package approval is inferred.

### Behavioral Spot-Checks and Probes

| Check | Result | Status |
|---|---|---|
| `python3 deploy/tests/test-selected-cutover-contracts.py` independently invoked | 7tests,0.023s,exit0 | PASS |
| `bash -n deploy/deploy.sh`; `git diff --check` | exit0 each | PASS |
| Independent Python read-only source/artifact/archive/full-snapshot/runtime-Counter checks |389sources/23final/113Task1 artifacts,11tar members, exact three harness deltas and full preservation equality pass | PASS |
| Plan04 short-check receipt/log authentication |17deploy/7selected/16CI checks,1.247s,all exit0; all four logs hash-match | PASS |
| Raw actual patched application results |2557backend,47critical100%,697frontend,49browser plus sole deployed-CSP skip; native/dev/build proofs retained | PASS |

No `scripts/*/tests/probe-*.sh` exists or is declared by this phase. Mandatory runnable acceptance is the explicit recovery/selected/CI suite, authenticated above; no substituted probe pass is claimed. No servers, services, installations or full campaigns were started during this verification. Recorded cleanup contains empty containers/networks/volumes for all six owned projects; no new live resource inspection is claimed here.

### Adversarial Checks and Anti-Patterns

Disconfirmation targets were: legacy0008 falsely substituting for0014 compatibility; projected image records hiding changes; passing an arbitrary refusal; and a failed full report being relabelled green. Direct current0014 source/raw checks, full-row multiplicity comparison, exact diagnostic plus preservation assertions and explicit retained failed report reject those shortcuts. Failed patched connection-attempt logs are retained alongside the actual successful `backend-full-patched-final.log`; the earlier failure is not counted as the2557pass run.

Focused scan of all seven changed deployment/CI implementation/test paths found no TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers. No BLOCKER or WARNING remains in required local scope. Read-only browser fixtures and supplementary CSS reflow are deliberately limited evidence: neither establishes live provider rights, successful economic mutation nor native-menu zoom. No unsupported missing local behavior was hidden by those fixtures.

### Human Verification Required

None outstanding for this phase's unchanged local contract. Direct `git diff 48d970c HEAD` of frontend, design system, backend application/Alembic/build recipe and relevant served configuration shows no relevant presentation/financial-response delta. Patched runtime API/accounting/browser/native/dev/build evidence and the independent UI review support continued acceptance. Phase10 HUMAN-UAT records actual owner “Reviewed: accept the new UI” and “Checked native 200%: passes” for48d970c and ZIP `cf4e4817bdae885c2feea4c5fe9e6368ef834394a83f618e6bddddaa5fb9845d`. Browser name/window size were not supplied. That native answer applies to its specified History/held-correction/error pages; earlier accepted discovery/action/ticket/Portfolio scopes are preserved separately. No fresh human answer or automated native200% measurement is invented.

### Gaps Summary and Boundaries

No actionable Phase11 local gap remains; no later-phase deferral is used to excuse a required truth. SAFE-01/Phase7 live provider identity, rights/access/coverage/freshness and activation remain deferred and unverified. Production, B2 custody/upload, installed host tools, timers, publication/push/merge and accepted W01–W08 debt remain outside this local verdict. Local compatibility is proven before rollout; rollout itself is not performed or authorized by this report.

Recommend coordinator canonical completion of Phase11/SAFE-02/SAFE-03 only after recording this verdict and reconciling ACCEPTANCE/VALIDATION/Plan04 summary. This reviewer has not edited STATE, REQUIREMENTS or ROADMAP.

---
_Verified: 2026-11-13T19:55:04Z_
_Verifier: independent goal-verifier `/root/phase11_execute04/goal_verify`_
