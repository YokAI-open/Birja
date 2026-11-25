# Phase 21 research

**Research date** 2026-11-25

**Confidence** High for repository contracts and documented endpoint behavior. Expanded account rights, source coverage and usable live limits require evidence during execution.

<user_constraints>

## User Constraints

- **D-01:** Use the approved simulator rules and existing interface. Keep the
  <120-second original IEX quote age, regular sessions, reported-halt
  checks and their coverage limitation, whole shares, zero stock commission,
  re-confirmation on price change and original-receipt recovery. Keep the
  last permitted mark and local countdown at close.
- **D-02:** Use the existing free products and public documentation without
  provider outreach. Treat Phase 7's owner attestation and Phase 18's
  original-20 receipt as evidence for their stated scope. Establish
  expanded field, purpose, retention and backup scope, exact live directory
  reconciliation and bounded selected/held quote and action proof before
  activating those paths.
- **D-03:** Reuse browser and recovery evidence whose inputs still match.
  Qualify the exact release candidate under the existing coverage, CI,
  image, migration, recovery and rollback gates. Limit fixes and new tests
  to release-blocking defects and behavior changed in this milestone.
- **D-04:** Use the repository's feature and release PRs, then the protected
  production runbook. Carry the exact tested main SHA, recovery bundle,
  schema, live source admissions and approved rollback route into execution.
  Preserve the separate authorization checkpoints for publishing and
  production actions.
- **D-05:** Final acceptance uses a designated synthetic production portfolio
  and one eligible out-of-list issue during a regular session. Reconcile
  both fills, final cash, zero position, immutable History and crypto
  smoke with an identity-bound, sanitized receipt. A blocked live check
  stays open in the requirement records.

</user_constraints>

## Summary

Advance release qualification while separately establishing source eligibility. The Phase 20 browser and financial-core evidence is reusable when its inputs match. The CI recovery path still packages an exact 0024 bundle and runs a historical seven-stage 0023 campaign. Phase 21 needs a current 0026 artifact through the actual production-compatible producer, consumer, image and rollback lanes before that artifact can be installed. [VERIFIED: `20-09-SUMMARY.md`, `.github/workflows/ci.yml`, `deploy/tests/run-portfolio-validation.py`, `deploy/tests/ops-fixtures.py`]

The live path needs approved scope, complete classified directory coverage, a repeatable renewal procedure, and a bounded out-of-original-universe sample. Work from private existing agreements and dated public terms. If evidence is missing for the current source, leave that source disabled and identify the exact blocker. A passing API response, report sample, or owner attestation for the original 20 supplies evidence for that scope. [VERIFIED: `21-CONTEXT.md`, `18-SOURCE-DECISION.md`, `19-SOURCE-DECISION.md`, `20-VERIFICATION.md`]

## Architectural Responsibility Map

| Capability | Owner | Boundary |
|---|---|---|
| Source permissions, catalog publication, promotions | Restricted operator and PostgreSQL | Review exact scope and expiry. Reuse the guarded inventory/import and existing operator roles. |
| Bounded quotes, reports and corporate actions | Dedicated scheduler | Read current authorities and rate limits before collection. Keep credentials within the private scheduler/operator lane. |
| Accounting, replay and ownership | Owned API and transactional PostgreSQL ledger | Require a fresh, admitted IEX quote, active portfolio, exact listing, units and action coverage before a fill. |
| Search and acceptance | Existing browser and owned APIs | Show actual server state, scoped price, accessible selection, closed countdown and matching private History. |
| Release and recovery | Hosted CI, restricted deploy tool, encrypted backup | Bind proofs and tooling to the tested source, schema, image and snapshot. |

[VERIFIED: `stock_catalog_import.py`, `scheduler.py`, `stock_catalog_trading.py`, `frontend/e2e/stock-catalog.spec.ts`, `deploy/RUNBOOK.md`]

<phase_requirements>

## Phase Requirements

| ID | Required outcome | Evidence |
|---|---|---|
| SV-01 | Accessible browser search, out-of-list trade and exact owned cash, holdings and History, including closure, halt, stale data and crypto | Final-source guarded Playwright evidence. Record native 200% browser evidence only if exercised. |
| SV-02 | Existing ledgers and identities survive the upgrade. Review, automated checks and applicable recovery and rollback pass. | Actual 0023 predecessor and preserved 0025 fixture, exact 0026 production bundle, role/TLS and cold replay, compatible recovery or rollback. |
| SV-03 | Required CI and approved production rollout, followed by an out-of-list live IEX round trip | Successful main run and artifact, source and rollout receipt, final production smoke and exact reviewable acceptance totals. |
| SC-01, SC-03 | Open Phase 19 production prerequisites | Complete admitted discovery receipt and visible live out-of-list quote or exact reason, with one eligible selection used for the round trip. Preserve the Phase 19 assignment. |

[VERIFIED: `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`]

</phase_requirements>

## Standard Stack and Environment

Reuse the lockfiles, Python 3.14/FastAPI, PostgreSQL 18 under verified TLS, Redis, Node 24/Playwright, restic 0.19.1, Docker and GitHub Actions. Installed local tools include Python 3.14.9 in the previously used workspace venv, Node 24.22.1, uv 0.13.5, gh 2.102.0 and Docker client 29.2.1. The local Compose binary reports 5.0.0. Hosted recovery expressly pins Docker client/server 29.2.1 and Compose 5.7.0 and verifies their platform support. Qualify the full graph on that supported runner. No package installation or live account check took place in research. [VERIFIED: local version commands, `backend/pyproject.toml`, `frontend/.nvmrc`, `.github/workflows/ci.yml`]

## Live Data Sources

| Source | What the current documentation supports | Evidence needed for Birja |
|---|---|---|
| Nasdaq Trader directories | Separate Nasdaq and other-listing field tables and terminal file times. Symbol Lookup names Nasdaq Listed in its licensing exception. The other-listed export is not named in that exception. | Exact application of terms to `nasdaqlisted.txt` and `otherlisted.txt`, including the NYSE subset and actual normalized fields, class/alias derivation, display, storage and backups. Document per-artifact scope. [CITED: [directory definitions](https://www.nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs), [Symbol Lookup notice](https://www.nasdaqtrader.com/trader.aspx?comb=Enter+Name%2C+Symbol+or+MPID&id=symbollookup&mth=contains&typ=All_Issues), [Nasdaq terms](https://www.nasdaq.com/legal)] |
| OpenFIGI and SEC corroboration | The OpenFIGI grant covers FIGI identifiers. Descriptions are identified separately. Anonymous mapping is 25 requests per minute, 10 jobs each. SEC provides reusable public information, and its lookup files lack guaranteed scope or accuracy. | Establish the actual classification/evidence and alias field rights. Use issuer filings for exact reviewed security/exchange/class exceptions. A CIK or ticker association alone cannot prove share class or complete market coverage. [CITED: [OpenFIGI terms](https://www.openfigi.com/docs/terms-of-service), [API](https://www.openfigi.com/api/documentation), [SEC reuse](https://www.sec.gov/about/privacy-information#website), [SEC lookup FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions)] |
| Alpaca Basic, Assets and IEX | Basic documents free single-venue real-time IEX, 200 historical requests/minute, and a separate streaming limit. The quote endpoint uses rate-limit headers and permits explicit `feed=iex`. Asset GET returns provider identity and listing metadata. | Confirm the applicable current agreement and private account's actual read products, exact source fields and terms for friends-facing display, normalized storage, execution and encrypted backup. The publicly listed securities customer agreement has restrictions on redistributing market data. Its applicability to this account and any separate grant must be checked privately. Record request header cap/reset, batch and observed quote freshness before widening. [CITED: [market data plans](https://docs.alpaca.markets/us/docs/about-market-data-api), [latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1), [asset lookup](https://docs.alpaca.markets/us/reference/get-v2-assets-symbol_or_asset_id), [published agreements](https://alpaca.markets/disclosures), [customer agreement](https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf)] |
| Corporate actions | REST uses page tokens and supports including incomplete early events. The provider disclaims guaranteed creation time. The event stream documents historical replay and insert/update/delete mutations. | Verify admitted process-date windows, known-ID refresh, all-US bounded mutation replay ingress, corrections/unsupported routing, latency, completeness and durable storage/backup. Keep continuous or unbounded collection outside the smoke. The prior bounded access receipt lacks full history/latency proof. [CITED: [REST](https://docs.alpaca.markets/us/reference/corporateactions-1), [SSE](https://docs.alpaca.markets/us/reference/subscribetocorporateactionseventssse)] [VERIFIED: `stock_catalog_actions.py`, `alpaca_actions.py`, November 24 quick receipt] |
| Nasdaq reported halts and exchange calendars | Nasdaq documents its published halt report and at-most-once-per-minute polling. NYSE and Nasdaq close November 26 and end their November 27 regular session at 13:00 ET. | Review current schedule and closures again before any appointed window, in Eastern time and UTC. Require current report, actual report/retention scope, and no applicable reported halt. Keep the owner-approved coverage limitation and the expiry behavior. [CITED: [Nasdaq halt RSS](https://www.nasdaqtrader.com/Trader.aspx?id=TradeHaltRSS), [NYSE calendar](https://www.nyse.com/trade/hours-calendars), [Nasdaq calendar](https://nasdaqtrader.com/Trader.aspx?id=Calendar), [Nasdaq Thanksgiving alert](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2026-69)] [VERIFIED: `18-SOURCE-DECISION.md`] |

## Implementation and Operational Patterns

### Directory completeness and continued eligibility

Use `python -m app.tasks.stock_catalog_inventory --output <private-manifest> live --rights <private-rights> --cursor <private-cursor>` with optional root-level `--exceptions` before the subcommand. The application checks explicit dated fields/purposes before source access and before mapping attempts. Directory freshness is four days and pair skew is at most one hour. The importer limits enrichment to 10 jobs per request, 20 attempts per rolling minute and 100 per invocation, including retries. Serialize resumes using the same private cursor and rebind unchanged evidence on directory updates. At the earlier candidate count of about 7,100 listings, mapping all would need roughly 710 successful batches before exclusions, reuse or retries. This is an order-of-magnitude budget estimate and cannot be counted as a live classification result. [VERIFIED: `stock_catalog_inventory.py`, `stock_catalog_sources.py`, `19-SOURCE-DECISION.md`]

Capture pair timestamps/hashes, coverage totals and exclusions, duplicates and unresolved per venue. Exit 0, positive included on both required venues, reconciled totals and zero unresolved provide the publishable record. Exit 2 preserves incomplete work for authorized resume. Verify complete final generation, active-listing counts, search by ticker and name and distinct classes. Make sure candidate output remains private. [VERIFIED: `stock_catalog_inventory.py`, `stock_catalog_publish.py`, `19-VERIFICATION.md`]

The existing catalog CLI exposes `publish <manifest> --expect-generation <positive-id-or-empty>`, `stage-assets --admission-id <id>` and `promote-instrument --catalog-id <id> --listing-id <id> --admission-id <id>`. It uses the verified TLS `BIRJA_CATALOG_DATABASE_URL` restricted migrator path. The existing operator document's legacy packet writes `stock_data_admissions`, while catalog tools read `stock_catalog_admissions` and lack a catalog admission constructor CLI. A narrow reviewed, default-review-only packet/import step or validated runbook is needed to provision exact catalog records before using the CLI. Keep the directory, OpenFIGI/issuer exceptions, `alpaca_assets`, `alpaca_iex_quotes`, `catalog_execution`, `catalog_mark`, `catalog_halt` and `catalog_actions` grants distinct. The runtime app/scheduler lack write authority over admissions. [VERIFIED: `stock_catalog_import.py`, `stock_catalog_publish.py`, `stock_catalog_quotes.py`, `stock_catalog_promotion.py`, `deploy/STOCK-DATA-ADMISSION.md`, `deploy/db/bootstrap-roles.sql`]

An asset stage is single-use and claims the allowance before request. Its scope accepts at most two exact targets and requires distinct exchanges for the two. Select a small approved cohort and document that catalog search coverage and trading eligibility have separate measures. Subsequent publications give active listings new version IDs under their stable issue ID. Prepare an owned refresh and rebind procedure for mapped/traded/held issues and for expiring calendar/action authority. Test it through one refresh on owned fixtures before broad activation. Do not renew evidence by copying stale IDs or dropping a hold. [VERIFIED: `stock_catalog_import.py`, `stock_catalog_provider.py`, `stock_catalog_publish.py`, `stock_catalog_promotion.py`, `stock_sessions.py`]

### Retention, attempts and actual proof

The production Compose uses append-only Redis with a persistent volume. Redis AOF logs writes even when the key will expire. Logical DB numbers share that instance-wide persistence. First verify that exact AOF retention for the display-cache fields is already covered, including log rewrite/backup behavior. If the evidence permits only transient cache, use a reviewed volatile Redis lane for catalog demand, outcomes and display quote values with `appendonly no` and snapshots disabled, without a persistent volume, and verify no quote canary is written to disk. That is conditional infrastructure work. Keep Redis account quota reservation shared with legacy quotes/actions. Keep the catalog demand, outcome and quote keys on the same instance for atomic store-and-complete. Confirm held quotes, immutable fills, actions and marks independently have PostgreSQL/backup rights. A database dump that omits Redis cannot settle AOF permission. [CITED: [Redis persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)] [VERIFIED: `docker-compose.prod.yml`, `stock_catalog_quote_demand.py`, `stock_catalog_quotes.py`, `stock_scheduler.py`, `20-09-SUMMARY.md`]

Use existing `STOCK_DATA_ENABLED` and `STOCK_ACTIONS_ENABLED` gates plus valid exact admissions on every live path. Compose keeps Alpaca keys exclusively in the scheduler context. Public source documentation is technical evidence. Actual account allowances, response bytes, provider timestamps, attempt count, 429/partial outcomes, quote age and cohort readiness need a bounded approved measurement. Preserve the shared configured cap (default 20 attempts/min, inclusive of quote and action attempts) and per-scope cap, regular session, valid two-sided quote, original event age below 120 seconds at fill, report validity and actions completeness. Display cache, action history, and terminal immutable receipt retention require their particular admitted fields. [VERIFIED: `backend/app/core/config.py`, `stock_scheduler.py`, `stock_catalog_quotes.py`, `stock_catalog_actions.py`, `stock_catalog_trading.py`, `docker-compose.prod.yml`]

### CI release artifact and actual predecessor

The ops job currently calls `run-portfolio-validation.py --suite recovery`, runs the historical seven stages with `current0023-cold` and 0023 TLS parity, and uploads `/tmp/birja-phase14-proof/recovery.tar.gz`. The driver and `ops-fixtures.py` expect `deploy-recovery-v5`/payload 4/0024 and have exact assertions in CI contract tests. The current producer supports `python3 deploy/backup-snapshot.py bundle-v6 --output <archive>` for `deploy-recovery-v7`/payload 6/0026. The existing `recovery-bundle.sh package` shortcut invokes the retained v2 packager. Current bytes fail the old exact-source package contract. Plan an explicit 0026 campaign selection and bind the required hosted artifact to `bundle_verify(..., required_profile="deploy-recovery-v7")`, exact bundle members, verified runtime image and tested source. Keep the historical 0007–0025 lanes and contract assertions intact with their own pinned sources; extend fixture verifiers to support the successor intentionally. The guarded Phase 20 paired restic test supplies a feasible 0025/0026 fixture pattern. It does not exercise the release bundle end to end. [VERIFIED: `.github/workflows/ci.yml`, `run-portfolio-validation.py`, `ops-fixtures.py`, `test-ci-ops.py`, `backup-snapshot.py`, `verify-restore.py`, `recovery-bundle.sh`, `test-stock-catalog-finance-recovery.sh`]

The last recorded production SHA is `07d3aa5`, the cached `origin/main` tip during planning. That source ends at schema 0023, while the Phase 20 paired test migrates retained 0025 to 0026. Refresh actual live SHA/schema, database and Redis bindings, migration/role/TLS status, installed manifest, recovery headroom and active writers in the authorized preflight. Rehearse the actual predecessor-to-candidate chain on synthetic volumes with prior ledger/identity data and a mandatory restoration receipt. Fetch exact successful main run artifact by run ID, check the supplied SHA, profile, inventory, tested source and image before installation, then retain all custody data required by current runbook. PR checks can attach to a test merge commit. Reconcile source/tree/resulting main ref and require the actual main-run proof as deployment authority. [VERIFIED: November 24 production receipt, cached Git migrations, `deploy/RUNBOOK.md`, `deploy.sh`, `.github/workflows/ci.yml`] [CITED: [required check commit behavior](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks), [artifact download](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)]

The protected deploy path checks compatibility before live mutation, builds/tests while the current app is still serving, acquires the shared backup/deploy lock, stops writers, migrates under the restricted role, and switches frontend only after backend health. Use exact snapshot recovery before cutover and verify an approved fresh encrypted snapshot/clone afterward, subject to provider and operational rights. The older 0023 runtime cannot run on candidate 0026, and populated 0026 cannot downgrade. The generic rollback selector can pick an incompatible older source and must refuse. Rehearse a supported pre-write rollback with retained/pre-upgrade volumes where the runbook allows it, and a compatible 0026 roll-forward or same-schema release recovery after any candidate write, preserving that current ledger. A prechange restore after a successful candidate writer loses later data. If no scoped compatible recovery route is demonstrated, keep production rollout blocked while release checks proceed. [VERIFIED: `deploy/RUNBOOK.md`, `deploy.sh`, `test-deploy-compatibility.sh`, `0026_stock_catalog_finance.py`, `20-09-SUMMARY.md`]

### Final browser and operational outcome

Use guarded local Chromium for search, keyboard/focus, exact out-of-list fill/reprice/recover, History, closed countdown, stale/halt refusal and crypto availability. Earlier seven-journey exact-source evidence includes 390px and 640px equivalent reflow. Native zoom is separately observable. Schedule final live browser acceptance only after main CI, approved rollout and actual live readiness. Use normal app sign-in and one whole share under selected portfolio and exact live catalog listing in a currently verified regular session, confirm buy at ask and sell at bid, reconcile authoritative request receipts and cash/position/history, and include the crypto smoke. Retain only permitted sanitized results, release SHA, schema, generation/issue, timestamps/age, report/approval disposition and rollback reference. No livestream, request from tests, external brokerage order, raw provider logs or account data is needed. [VERIFIED: `21-CONTEXT.md`, `20-VERIFICATION.md`, `frontend/e2e/stock-catalog.spec.ts`, `deploy/RUNBOOK.md`]

## Runtime State Inventory

| Category | Observed state and action |
|---|---|
| Stored data | PostgreSQL owns money, legacy stock/crypto and catalog authorities. Upgrade a reviewed populated predecessor, compare retained ledgers and sequences, and allow current records only under the matched 0026 runtime. Preserve both approved prechange and current encrypted snapshot evidence. |
| Live service config | Record exact production compose project, volume routing, current flag/admission state, CORS/TLS smoke and Redis persistence after access approval. The stock flags default false in production definitions. |
| OS-registered state | The runbook uses retained release-specific launchers and nightly backup timer. Preserve timer and protected configuration through reviewed tooling installation and any required custody/inventory rotation. |
| Secrets/env | Keep prior company/portfolio/customer data and protected credentials private. Host or tool changes require separate explicit authorization. Review key access in private by endpoint and keep the API/frontend credential-free. |
| Artifacts | Source-bound runtime and frontend assets, exact v7 archive/profile and checkout, retained v4/5/6 inputs as distinct families, documented compatible recovery route and guarded current backup/restore receipts. |

[VERIFIED: `deploy/RUNBOOK.md`, `docker-compose.prod.yml`, `stock_catalog_promotion.py`, `verify-restore.py`, `20-VERIFICATION.md`]

## Validation Architecture

| Checks | Existing command or observable evidence | Cadence |
|---|---|---|
| SV-01 | `python3 deploy/tests/run-stock-browser.py --suite catalog` for affected catalog changes. Default runner executes all E2E scopes in required CI. UI case matrix references Phase 20. | Targeted change and required candidate CI. |
| SV-02 | `python3 deploy/tests/test-ci-ops.py`, `python3 deploy/tests/test-portfolio-recovery-contracts.py`, `bash deploy/tests/test-deploy-compatibility.sh`; selected changed backend tests; guarded current recovery driver exercises exact v7 on populated upgrade and isolated restored TLS roles with archive/image/source binding. | Fast local after affected change; full serial ops release gate. |
| Coverage and image gates | Backend whole-suite branch coverage `--cov-fail-under=80`, the explicit critical list with `--fail-under=100`, frontend coverage, dependency audits, strict five-image-policy scans and successful `ci-pass`. The test and `CLAUDE.md` mirror the workflow's module list. Identify Phase 20 financial paths that now need critical coverage and add behavioral tests where required. | Targeted while fixing; whole release runs on the appropriate PR and exact main candidate. |
| SC-01/SC-03 | Existing inventory/quote/trade-context suites with synthetic input. In approved live qualification record a paired complete manifest, provider/account limits and visible outside-20 venue/quote/readiness with current eligibility. | Per relevant source or generation change. Live verification is separately admitted. |
| SV-03 | Record all six GitHub jobs and matching main SHA/run ID/archive. With authorized live access, record isolated pre/post-restore result and one normal production buy/sell with exact reconciled receipts and History. | Release candidate, protected cutover, admitted regular session. |

The Phase 20 five-suite slice passed 63 tests and reported 55.17% whole-app coverage. This scoped sampling did not clear the inherited 80% threshold. The availability of that focused evidence allows targeted repairs while retaining both whole-suite gates. No new test platform or package is required. Wave 0 execution preparation is a source-bound evidence matrix and explicit successor harness binding. [VERIFIED: `20-09-SUMMARY.md`, `.github/workflows/ci.yml`, `backend/tests/test_critical_coverage_config.py`, `deploy/tests/run-stock-browser.py`]

## Project Constraints and Defensive Controls

Read the shared rules, keep live credentials and real rows outside logs/repo, and honor explicit push/merge and operational approvals. Preserve scoped ownership/session checks, parameterized exact-decimal accounting, authenticated evidence and finite replay, current restricted TLS roles and package pin verification. Test benign refusals for unsupported sources/revisions and affirm a secret-free receipt. These controls use the existing authenticated application and recovery pathways. [VERIFIED: `AGENTS.md`, `CLAUDE.md`, `deploy/RUNBOOK.md`, `deploy/STOCK-DATA-ADMISSION.md`]

## Open Evidence

- Expanded NYSE/Nasdaq source and normalized mapping rights, complete live classified coverage, and the applicable Alpaca products/terms and measured account quotas remain open. Existing admissions automatically refuse absent, expired or incompatible scope. If the documented products and existing private terms leave a missing right, preserve that blocker without outreach or unauthorized widening. [VERIFIED: `19-SOURCE-DECISION.md`, `stock_catalog_inventory.py`, `stock_catalog_quotes.py`, `21-CONTEXT.md`]
- Source-clock availability, report freshness and expanded action replay completeness must be observed for the chosen cohort, including readiness after listing refresh. Record production acceptance at the appointed regular session only when all prior gates pass. [VERIFIED: `18-LIVE-RECEIPT.md`, `20-VERIFICATION.md`, `21-CONTEXT.md`]
- The exact live predecessor, compatible 0026 rollout/rollback target and release version should be selected from verified host and release state during execution. The cached repository ref and Phase 20 fixture are evidence of different environments. [VERIFIED: `deploy/RUNBOOK.md`, November 24 production receipt, cached Git source]
