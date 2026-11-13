# Phase11 acceptance inventory

Prepared2026-11-13 at source `96834e9f566530dbff377cf1d09de8123d4b74b0`.
SAFE-02 and SAFE-03 remain **PENDING**. This is an inspected oracle inventory,
not a financial, browser, compatibility or rollout pass. Roadmap criterion1 is
R01–R07, criterion2 is F01–F09, criterion3 is B01–B06/G01–G05.

Identity/result references below are normalized to keep the matrix readable.
Every row inherits its referenced source/image/archive, time, private log/hash,
reviewer and blocker record; PENDING fields must be replaced with actual receipts
in Plan03 and assessed in Plan04. No historical count is a current execution.

## Commands and evidence identities

- **C-OPS:** exact runnable command in `11-VALIDATION.md`, section
  “Task11-03-2 exact integration command”. It runs
  `sudo -- python3 deploy/tests/test-stock-recovery-contracts.py --postgres`,
  then extracts/compiles/executes the uniquely marked current CI serial block,
  changing only its archive to a fresh `/tmp/birja-backup-test-phase11-final/recovery.tar`.
  Original/executed block hashes are recorded. Required order is
  image_transition → roundtrip(archive) → roles → populated/fresh TLS parity →
  rollback runner: retained self-test → legacy rollback integration → selected
  legacy0008 → selected current0014. Every outer stage checks archive and current
  CORE/unit bytes; installed-recovery contexts independently retain bytes.
- **C-DB(files):** `cd backend && uv run pytest` followed by the exact
  `tests/<file>.py` arguments named in the row. Requires the owned isolated
  `docker compose -f docker-compose.test.yml up -d --wait`; teardown is
  `docker compose -f docker-compose.test.yml down -v`. No dev database.
- **C-BROWSER:** `python3 deploy/tests/run-stock-browser.py` (all specs, one
  worker, zero retries; owns its disposable stack). Individual row test names
  locate assertions; they do not replace the complete suite.
- **C-FULL:** `cd backend && uv run pytest --cov=app --cov-branch --cov-fail-under=80`;
  exact47-module `uv run coverage report --include=... --fail-under=100` in
  `CLAUDE.md` and `.github/workflows/ci.yml` (identical fixed inventory in
  `backend/tests/test_critical_coverage_config.py`). The ellipsis here denotes
  that referenced full command, never a runnable shortened module list.
- **C-STATIC:** backend `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy app`; frontend `npm run lint`, `npm run typecheck`,
  `npx prettier --check .`, `npm run build`, each in its respective directory.
  No package acquisition is authorized by this inventory.
- **N:** final Phase11 source/file hashes, runtime/builder/Node image IDs and
  inventories, immutable datastore/scanner refs, archive SHA/size/profile/tested
  source, exact command/block SHA, private log path/SHA and duration all
  **PENDING Plan03**. Reviewer **PENDING Plan04**. Safe summary: unexecuted on
  final source. Blocker: source-frozen real campaign and review required.
- **O:** actual offline source `96834e9f566530dbff377cf1d09de8123d4b74b0`;
  no image/archive execution. Private receipt
  `/tmp/birja-phase11-02-offline-1xneg7zh/receipt.json`, SHA256
  `033d8133833cc5b0c8dc2e3a1b684fb663889cf3c7b0afa57554f477f5787bb9`,
  contains five exact source hashes and three logs. CI15tests/0.601s,
  selected4tests/0.189s, deploy17cases/0.560s, exit0 each; total1.350s.
  Logs `0.log`, `1.log`, `2.log` under that directory, respectively SHA256
  `db07abe7bd9d6939388f36c648e6736568e1527c5c0a3c161f5bfacdb4cd94be`,
  `9d654695c0a90577e252109954dd749137ace81d33f39cf1a31990e7f48cf31d`,
  `a5bb4bb47c28b12fa0404b738383f68f27b07d1f98ce500d953cea13717e4456`.
  Reviewer: executor self-check; independent review pending04. Safe summary:
  dispatch/contracts pass, no real service claim. Blocker: N still required.
- **H-RECOVERY:** historical Phase10 source7196d5f, six stages1391.017s,
  original command `python3 /tmp/birja-phase10-16-final-gate.py` (different
  historical order, not the new CI execution). Archive
  `/tmp/birja-backup-test-phase10-final/recovery.tar`,152320000bytes,SHA256
  `1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`.
  Report `/tmp/birja-backup-test-phase10-final/gate-report.json`,SHA256
  `0114bbd04e61756afd47fda9246eb333102d059af799c2e1db0efeadd471f972`;
  private log `/tmp/birja-phase10-16-final-same-archive.log`,SHA256
  `a06b495303d4a23c93aadcda97f89d688d72c0185d3b84e445f55413622dd344`.
  Original runtime/builder/Node IDs in `10-LOCAL-PROOF.md`:045aab29…a946,
  2eeaaf47…f405,7344f1b0…a4db (full values there). Historical independent
  review: `10-VERIFICATION.md`; safe summary: exact retained0014 recovery and
  legacy0008 selected rollback, **no selected0014 proof**. N remains blocker.
- **H-APP:** historical Phase10 reviewed source48d970c. `10-VERIFICATION.md`
  records2557backend/324.80s/99.87%overall,47critical4565statements/1462branches
  at100%;697frontend/16.42s/98.37%statements/94.82%branches;49browser passes
  plus one expected deployed-CSPskip/317.3s. Private logs
  `/tmp/birja-phase10-17-backend-full.log`, `...-critical.log`,
  `...-frontend-full.log`, `/tmp/birja-phase09-browser-5bjhfgb1/browser-all.log`;
  original hash/inventory receipts are `10-UI-SOURCE-HASHES.json`,
  `/tmp/birja-phase10-17-final-integrity.json` and
  `/tmp/birja-phase10-17-image-native-inventory.json`. Consult originals for
  exact log/image SHA; they were not freshly authenticated by this inventory.
  Reviewer: historical independent Phase10 verifier. Safe summary: historical
  passes attributed to their source; final N outcomes/log hashes PENDING.
- **H-UI:** `10-HUMAN-UAT.md` records owner “Reviewed: accept the new UI” and
  “Checked native 200%: passes”,2026-11-13T16:33:06Z, source
  `48d970c262c7f52bb5692d38db0748e5169cf389`, ZIP15497014bytes,SHA256
  `cf4e4817bdae885c2feea4c5fe9e6368ef834394a83f618e6bddddaa5fb9845d`.
  Private packet `/tmp/birja-phase10-ui-review.zip`; source/capture hashes in
  `10-UI-SOURCE-HASHES.json`. Browser/window dimensions not supplied.

## SAFE-02 — exact recovery and compatibility (criterion1)

| ID / behavior | Existing test/fixture | Independent expected oracle | Exact command | Source/image/archive | Result/time | Private log/hash | Safe summary | Reviewer | Blocker |
|---|---|---|---|---|---|---|---|---|
| R01 full0007–0014 holdings/cash, revisions, entitlement versions, payments/decisions, action and History | `ops-fixtures.py:roundtrip/successor_roundtrips`; producer/restore canonical contracts | All table row counts/hashes and financial totals equal exported snapshot; schema constraints/indexes and exact dumped sequence last_value/is_called match; next ID exceeds stored max. No sample-only/max-ID substitute | C-OPS | N; H-RECOVERY separately | PENDING; historical retained458.785s | N; H-RECOVERY | Exact encrypted local repository, not B2 proof | Pending04 | N |
| R02 corruption/unavailable repository, source preservation | `roundtrip/negative_controls`; real PGContracts in `test-stock-recovery-contracts.py` | Wrong cash/checksum, truncated dump, missing FK/index/sequence/calendar/authority refuse; unavailable encrypted repo fails; original canonical/identities/config/credentials/containers/mounts unchanged, deliberate0007 concurrent writer separately observed | C-OPS | N; H-RECOVERY | PENDING | N | Rejection must be intended failure, never arbitrary green exit | Pending04 | N |
| R03 immutable stock/crypto fills, splits, original payments/corrections/held/reconciled lineage and event replay | `stock-runtime-fixture.py`; `dividend-execution-fixture.py`;0014 successor callback | Persisted original receipt unchanged; saved dividend digest and full canonical state before/after equal; no second cash/count/quantity/basis effect on replay; current mixed History/Portfolio reads original account cash | C-OPS | N; H-RECOVERY | PENDING | N | Actual source services; owner clone replay distinct from runtime authority | Pending04 | N |
| R04 restricted grants/schema/tools and quarantine | `roles`, both `tls` lanes, restore pregrant/authentication; fixture runtime denials | Actual app/scheduler financial calls deny SQLSTATE42501; owner verifies exact definitions/owners/ACLs; populated/fresh authority results equal; actual consumers use verify-full; plaintext/wrong-host/CA refused | C-OPS | N; H-RECOVERY | PENDING; historical roles183.898s/TLS147.413+160.010s | N | No financial EXEC added to unblock replay | Pending04 | N |
| R05 current0014 selected startup/cutover and supported failed-attempt rollback | `selected-cutover.py:integration_current0014/current0014_checks` | Real restricted services start; revision0014; current tested SHA; canonical/identities/original volumes/retained bytes unchanged; owner replay twice and quarantined runtime denials; pending marker removed after rollback to tested source | C-OPS | N; offline O | **PENDING actual0014** | N | Only tested-source failed-attempt recovery supported; no downgrade | Pending04 | Actual service proof N |
| R06 unsupported old-runtime/schema preservation | `refused_rollback`, actual deploy admission; offline compatibility/contracts | Exact `application_schema_incompatible=true`; no checkout/build/start/log/pending/web/image/container/financial/identity/original-volume changes | C-OPS; `bash deploy/tests/test-deploy-compatibility.sh`; `python3 deploy/tests/test-selected-cutover-contracts.py` | N; O | Actual PENDING; offline O pass | N; O | Old runtime refuses before mutation, no claim it runs0014 | Pending04 | N |
| R07 separate legacy0008 downgrade rollback and source integrity | Runner `integration`; `selected.integration`; image transition | Actual v0.4.0/0008→v0.3.1 verified TLS and selected rollback;0008 retained; original volume fingerprints unchanged; archive/CORE/unit checks after each stage and owned cleanup even on failure | C-OPS | N; H-RECOVERY | PENDING; historical selected395.051s/image39.011s | N; H-RECOVERY | Legacy evidence cannot satisfy R05 | Pending04 | N |

## SAFE-03 — real PostgreSQL money/concurrency (criterion2)

Below are literal expected assertions or independently stated relationships
inspected in the named tests, not amounts calculated by the service under test.
Calendar/status/admission inputs are synthetic; locks/transactions and financial
service effects are real. Ownership helper tests explicitly use synthetic causes;
actual stock-fill and dividend service suites supply the financial integration.

| ID / behavior | Existing test/fixture | Independent expected oracle | Exact command | Source/image/archive | Result/time | Private log/hash | Safe summary | Reviewer | Blocker |
|---|---|---|---|---|---|---|---|---|---|
| F01 shared stock/crypto cash, no double fill/oversell, proceeds | `test_stock_trading_concurrency.py`: parallel_first_holdings, concurrent_sells, stock_crypto_competing_spends_and_keys, stock_sale_cash_is_immediately_reusable | Cash510 at ask102:5fills/5cash refusals/cash0; same key10results/1effect/cash408; sells3success/5refusals/cash9994; cross-asset102 admits1 and leaves0, same key conflicts; sale200 permits stock cash98 or crypto0 | C-DB(test_stock_trading_concurrency) | N; H-APP | PENDING | N | Independent sessions and DB books | Pending04 | N |
| F02 post-lock eligibility/expiry and price recheck | `test_stock_trading_waits.py`: adversarial_change_at_actual_wait_boundary; opposite_side_quote_after_staging_needs_no_reconfirmation | Observed pg_blocking_pids at instrument/account/holding/helper/constraints/final guard; rights, age120, halt/continuity/status expiry/action/cutoff/units/close/epoch changes refuse with exact unchanged snapshot; opposite bid101/ask102 allowed, cash9796/held2 in staging case | C-DB(test_stock_trading_waits) | N; H-APP | PENDING | N | Real advancing authority/clock; synchronization is test-only | Pending04 | N |
| F03 immutable replay incl closed market and uncertain response | `test_stock_trading_service.py:test_receipt_replays_after_sale_rename_and_permission_revocation`; stock browser lost-response test B02 | Saved original receipt equal, created=false, original cash9796/held2 despite later sale/rename/revocation; financial snapshot unchanged; actual closed replay B02 returns200 same key after201 | C-DB(test_stock_trading_service); C-BROWSER | N; H-APP | PENDING | N | Changed payload conflicts; no second effect | Pending04 | N |
| F04 exclusive cutoff and sold-after eligibility | `test_stock_ownership.py`: reconstruction_exclusive_cutoff/sold_out_retains_past_entitlement; `test_corporate_actions.py`: entitlement_late_buyer_and_departed_seller | At cutoff offsets−1/0/+1 quantities2/0/0; sold-out holding0 retains historical2; late buy0/departed seller2 | C-DB(test_stock_ownership,test_corporate_actions) | N; H-APP | PENDING | N | Economic time, not ingestion time | Pending04 | N |
| F05 revision/split ordering and exact basis/once-only | `test_corporate_actions.py`: entitlement_verified_split_unit_order, entitlement_rate_revision_appends_linked_replacement, split_exact_quantity_and_basis_once; `test_stock_ownership.py`: reconstruction_split_units_and_immutable_replay | Pre/post same boundary2/8; unknown held; earlier/later split8/2; revised entitlement version2→version1, quantity2 unchanged; split holding8/basis20; ownership2→4/basis20, replay sequence2 unchanged, ambiguous units held | C-DB(test_corporate_actions,test_stock_ownership) | N; H-APP | PENDING | N | Existing exact-or-none multi-owner/rollback/concurrent split cases retained | Pending04 | N |
| F06 duplicate/revised dividend money and response/transaction loss | `test_dividend_concurrency.py`: duplicate_workers_credit_once, duplicate_corrections_a_b_a_keep_original, rollback_after_actual_sql_before_commit, commit_response_loss_retry_does_not_repeat_cash | Eight workers one payment/cash101/start10000; rates.75→.5 yield101.50→101 with2linked corrections/original unchanged; precommit failure books unchanged; lost-response retry identical saved books/cash101 or101.5 | C-DB(test_dividend_concurrency) | N; H-APP | PENDING | N | Actual restricted scheduler financial SQL | Pending04 | N |
| F07 stock/crypto spend vs credit/debit and affordability | Same file: spend_races_credit_or_debit_exactly, duplicate_deficit_then_funded_success_once | One original; nonnegative cash; credit case cash0 if spend succeeds else102; debit correction is−.80 if no spend (cash101.20) or held0 after102spend(cash0). At cash.79 hold; funded.80→0 exactly once, linked successor | C-DB(test_dividend_concurrency) | N; H-APP | PENDING | N | Enumerated economics independent of implementation formula | Pending04 | N |
| F08 dividend waits/clock/cancellation/uncertainty, suspension | `test_dividend_waits.py`; concurrency duplicate_uncertain_holds_then_reviewed_successor; `test_corporate_actions.py`: split_persistent_hold_survives_healthy_monitor; stock F02 | Invalid postwait authority refuses unchanged books; current same-generation hash/calendar accepted only before constraints (cash101), never stale authority; expiration/cancel rolls back. Uncertain6workers one0delta/null-target hold then reviewed successor cash101.5, original unchanged. Healthy monitor does not clear persistent action hold | C-DB(test_dividend_waits,test_dividend_concurrency,test_corporate_actions,test_stock_trading_waits) | N; H-APP | PENDING | N | Deferred-constraint trigger is owned test synchronization, not a production trigger claim | Pending04 | N |
| F09 atomic History/private deterministic paging and closed dividend payment | `test_dividend_concurrency.py`: uncommitted_cash_and_history_are_both_invisible; `test_event_history.py`; `test_dividend_waits.py`: due_does_not_require_open_market_or_fresh_quote | Before commit cash100/noevent; after101/exact1 dividend ID. Full timestamp/kind-rank/source-ID cursor, collisions distinct, cross-owner/offpage originals protected; corrections applied.5 or held0; closed/halted/3day quote does not block due quantity0/2 dividend cash100/101 | C-DB(test_event_history,test_dividend_concurrency,test_dividend_waits) | N; H-APP | PENDING | N | Portfolio counts account cash once; no client-side dividend sum | Pending04 | N |

## SAFE-03 — browser and preserved gates (criterion3)

| ID / behavior | Existing test/fixture | Independent expected oracle | Exact command | Source/image/archive | Result/time | Private log/hash | Safe summary | Reviewer | Blocker |
|---|---|---|---|---|---|---|---|---|---|
| B01 discovery/open/closed/stale/unknown and independent crypto | `stocks.spec.ts`, `stock-actions.spec.ts` named errors/admission/expiry/calendar/monitor/hold/deadline cases | Exactly20 stock identities plus15crypto;120s boundary removes executable values; permission and source/calendar/status independent; refresh cannot clear persistent hold; crypto still navigable/usable | C-BROWSER | N; H-APP | PENDING | N | Many discovery/error states are read-only route presentation fixtures; not successful financial effects or live rights | Pending04 | N |
| B02 preview/reprice→confirm→receipt→combined Portfolio; retry after close | `stock-trades.spec.ts`: actual ask buy and bid sale; changed ask; committed lost response; malformed success; closed drafts | Buy2×102→cash9796, held2, midpoint total9998; sell2×100→9996; crypto100 then stock102→9794/start10000. Reprice103: no fill/cash10000 until renewed confirm→9794. Lost actual201 response replays200 same receipt/key after close, cash9796/held2. Closed draft never queues | C-BROWSER | N; H-APP | PENDING | N | POST success goes through actual services; interception only loses/corrupts response after genuine commit | Pending04 | N |
| B03 valuations/splits/stale/unknown/hold and crypto history | `stock-trades.spec.ts`: real historical closed/halted marks; keyboard stale deadlines; `stock-actions.spec.ts`: post-split mark; `portfolio-history.spec.ts`: buy→portfolio→history→sell | Dated closed/halted marks remain labelled; uncertain stock makes known value9796 incomplete and hides allocation; stale deadline disables order; stock/crypto holdings and actual receipt/History retained; no silent zero valuation | C-BROWSER | N; H-APP | PENDING | N | Read-only mark states separate from actual fill/financial tests | Pending04 | N |
| B04 real dividend/correction/hold/reconciliation and funded cross-asset use | `dividends-history.spec.ts`: real restricted worker credits once | Original10000 credit:10000→20000; stock50×102→14900; crypto10000→4900; verified+2→4902;−10001hold unchanged; actual crypto sale then debit10001; uncertainty0; reviewed+10003; repeated cycles exact equal and original unchanged | C-BROWSER | N; H-APP | PENDING | N | Actual fixture/services, no successful financial response fulfillment | Pending04 | N |
| B05 mixed History/splits/private pages/responsive/focus | Same spec: actual mixed pages; pre-anchor uncertainty; empty |28originals; first25/all31unique mixed IDs; split3:2 quantity2→3; widths320/375/768/1024/1440 one accessible layout/no overflow; original/back focus and44px target/nav clearance; errors retain rows; final completion focused onscreen; preanchor no dividend/cash10000; new owner empty after late response | C-BROWSER | N; H-APP | PENDING | N | Tied-time route fulfillment is presentation only (SQL F09); CSS200% is supplementary, not native zoom | Pending04 | N |
| B06 existing design/owner/native200% scope | `11-UI-SPEC.md`, `11-UI-SPEC-REVIEW.md`; H-UI | Contract6/6 approved independently; actual owner packet UI/native-menu200% answers bind48d970c only; final relevant continuity must hold | Continuity command below; owner evidence H-UI | N; H-UI | Historical owner pass; final reuse PENDING04 | H-UI; N | No new owner answer inferred from contract approval | Pending04 | Final continuity assessment |
| G01 overall80% and all47critical100% statements+branches | CI backend/frontend; critical inventory test; mutation policy | Full suites green, no critical missing/partial branches; frontend configured80%; every fixed critical module retained | C-FULL; `cd frontend && npm run test -- --coverage`; C-STATIC | N; H-APP | PENDING | N | Historical2557/697 not promoted | Pending04 | N |
| G02 dependency audits/five strict actual images | CI dependency steps/image; `deploy/scan-images.py` | Locked pip audit and npm audit high gate; runtime/builder/Postgres/Redis/Node including-unfixed0HIGH/CRITICAL, fail-open flags absent; exact image inventory bound | `cd backend && uv run pip-audit`; `cd frontend && npm audit --audit-level=high`; exact five-image scan command in CI “Scan all five actual images” | N; H-APP | PENDING | N | Historical npm2low/15moderate means not zero vulnerabilities; no waiver/new install | Pending04 | N |
| G03 native runtime/dev startup | `test-dev-bootstrap.py`; native gates from `10-LOCAL-PROOF.md`/Plan03 | UID1001/networknone native XNYS/dividend/worker/History imports/target; fresh/upgraded0014 real financial service effects and unsafe-role refusal; original owner safe | `python3 deploy/tests/test-dev-bootstrap.py --image birja-backend-test:phase05-07`; Plan03 native exact invocation/receipt | N; H-APP | PENDING | N | Existing installed dependencies only; no production access | Pending04 | N |
| G04 mandatory serial dispatch/unchanged archive | Actual runner AST execution with failure fakes; `test-ci-ops.py`; selected/deploy offline contracts | Omit either selected lane, swap order, change either archive argument, swallow either failure all rejected; integrity omissions,47-module omissions, audits/scans/aggregate dependency failures rejected; actual CI Python block compiles | `python3 deploy/tests/test-ci-ops.py`; `python3 deploy/tests/test-selected-cutover-contracts.py`; `bash deploy/tests/test-deploy-compatibility.sh` | O | PASS15+4+17/1.350s | O | Offline graph proof only; current0014 integration still N | Self-check; review04 pending | N |
| G05 required jobs/cleanup/skip boundary | CI `ci-pass`, image policy and ops always-cleanup; owned browser runner | backend/frontend/image/e2e/ops all required; failure/cancel/skip rejects success; fixed owned resources only; retain precisely deployed-CSP W07 skip, never skip financial/0014 proof | `python3 deploy/tests/test-ci-ops.py`; C-OPS/C-BROWSER actual receipts | O plus N | Offline PASS; actual PENDING | O; N | Existing45min ops timeout unchanged; extra0014 runtime unmeasured, assess measured total in03 | Pending04 | N |

## UI continuity, exclusions and disposition

At this inventory source, `git diff --name-only 48d970c -- . ':(exclude).planning'`
lists only CI, deploy admission, selected/rollback harnesses and their offline
tests. There is no delta in frontend source/config/design-system, package locks,
Dockerfiles, backend application/Alembic, normal dev Compose, nginx or served
application response code. Thus no identified material change invalidates the
existing History packet owner/native200% scope. Deploy admission only constrains
operator source selection. This is source continuity, not a fresh build/runtime
or served-response measurement; final relevant build/dependency/runtime/response
assessment remains Plan04 after N. If that reveals a material UI change, affected
owner and genuine desktop browser-menu200% results become pending. Do not extend
the History packet to unreviewed screens or invent dimensions/browser identity.

No actual uncovered financial/browser requirement was identified in this source
inventory: existing seams above provide explicit oracles. The concrete selected0014
execution gap is implemented by Plan01 and wired here, but remains unproven until
Plan03. Exact current0014 service/refusal/recovery failure blocks SAFE-02 and
rollout; neither writing this table nor legacy0008/historical recovery closes it.
SAFE-03 also awaits final actual suites/security and review. No requirement checkbox
is changed here. Only the existing deployed-CSP W07 test may remain skipped;
W01–W08 remain accepted follow-ups, not new passes.

SAFE-01 remains primarily Phase7 and pending; live quote/action/status permission,
access/coverage/freshness/quota campaigns remain deferred. Synthetic admission,
calendar and provider evidence establishes local safeguards only. Production,
provider contact/agreements, B2, private.env, installed host tools, timers,
publication/push/PR/merge/deployment and package installation are excluded.
