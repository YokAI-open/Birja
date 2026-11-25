# Phase 21 pattern map

Mapped 2026-11-25 against the Phase 20 handoff and local `d688092`.

## File and flow map

| Likely surface | Role and flow | Closest reusable pattern |
|---|---|---|
| `.github/workflows/ci.yml`, `deploy/tests/run-portfolio-validation.py`, `deploy/tests/ops-fixtures.py` | Workflow and serial release qualification | One archive selected, verified through every stage, then uploaded only on success. |
| `deploy/tests/portfolio-{sources,smoke}.py`, `deploy/tests/test-rollback-db-security.sh` | Synthetic runtime/image binding and guarded rehearsal | Finite source families, exact OCI and archive checks, restored TLS smoke and predecessor refusal. |
| `deploy/backup-snapshot.py`, `deploy/verify-restore.py`, `deploy/tests/test-stock-catalog-finance-recovery.sh` | File I/O and ledger round trip | Existing payload 6/0026 producer and v7 consumer plus Phase 20 real restored replay. |
| `backend/app/tasks/stock_catalog_import.py`, `deploy/STOCK-DATA-ADMISSION.md` | Restricted operator input and transactional writes | Guarded catalog importer for connection and revision checks. Legacy packet import for review, exact scope and explicit apply. |
| `backend/app/tasks/stock_catalog_inventory.py`, `backend/app/services/stock_catalog_{publish,promotion}.py` | Bounded acquisition, publication and renewal | Existing rights-before-acquisition, compare-and-swap publication and stable financial binding. |
| `docker-compose.prod.yml`, `backend/app/{main.py,core/deps.py,tasks/scheduler.py,tasks/stock_catalog_quotes.py,api/v2/stock_catalog.py}` | Conditional cache configuration, service lifecycle and quota | Existing private Redis wiring, catalog quote request lifecycle and common account reservoir. |
| `deploy/deploy.sh`, `deploy/RUNBOOK.md`, `frontend/e2e/stock-catalog.spec.ts` | Cutover control, operational receipts and browser | Retained lock, protected bindings, source/revision guard, the existing browser journey and exact release acceptance precedent. |

## One tested recovery bundle

- The production-capable packaging boundary already exists in
  `deploy/backup-snapshot.py:2452`–`2476`. `bundle_package_v6(...)` calls
  `_bundle_package(..., payload_version=6)`. `deploy/verify-restore.py:494`
  validates the exact SHA before reading the inventory and checks the
  profile, allowed members and pinned retained sources. Keep the current
  consumer as the authority for v7/payload 6/0026.
- The hosted graph is a distinct integration. `deploy/tests/ops-fixtures.py:35`
  currently calls `bundle_package_v4`, and `archive_profile` at line 43
  accepts only v3, v4 and v5. `deploy/tests/run-portfolio-validation.py:353`
  authenticates current CORE, units and `PORTFOLIO_PAYLOAD_V4` bytes and
  authenticated image bindings. Its `execute_stages` at line 386 uses a
  `finally: guard()` per stage and checks the cold/upgraded/fresh authority
  triple. `execute_recovery` at line 458 claims an exclusive directory and
  records success only after the last guard. Carry those properties to the
  successor and preserve retained families. Review the separate fixed
  selectors in `deploy/tests/portfolio-sources.py:73`,
  `deploy/tests/portfolio-smoke.py:86` and `617`, and
  `deploy/tests/test-rollback-db-security.sh:31`.
- `.github/workflows/ci.yml:335`–`366` binds serial runner, staged archive,
  verified checksum and successful upload. `ci-pass` at line 374 requires
  every job result. Guard tests in `deploy/tests/test-ci-ops.py:77` and
  `deploy/tests/test-portfolio-validation-contracts.py:241` pin the existing
  graph. Extend the contracts with the chosen successor selection. Bind the
  deployment artifact to its recorded main SHA/run and actual tested image.
- `deploy/tests/test-stock-catalog-finance-recovery.sh:99` captures and
  restores exact restic dump/manifest bytes, checks Redis canary exclusion,
  then replays a cold 0026 restore and rejects downgrade. Its retained
  input is a reconstructed 0025 path. Use the schema, accounting and replay
  assertions in the same-archive release graph. The last recorded production
  app is `07d3aa5` at 0023, so verify the real predecessor during authorized
  preflight and rehearse a populated upgrade starting there.

## Reviewed catalog records and refresh

- `backend/app/tasks/stock_catalog_import.py:41`–`77` verifies the
  `BIRJA_CATALOG_DATABASE_URL` restricted migrator via
  `database_connect_args(..., migration=True)` and `require_migrator`; fixture
  mode has a bounded local test identity. At lines 113–158 the only operator
  commands are `publish`, `stage-assets` and `promote-instrument`. The legacy
  `deploy/STOCK-DATA-ADMISSION.md:99`–`167` packet uses role-specific verified
  TLS, exact fields, locked revision checks and rollback by default. Apply
  those operator properties to the independent `StockCatalogAdmission`
  model in `backend/app/models/stock_catalog.py:78`. Its input uses
  `artifact`, `reference`, time window, bounded `fields` and `scope`, and
  fixture isolation. The legacy packet writes a different table. Keep
  runtime roles read-only on admissions as set by
  `backend/app/db/portfolio_bootstrap.py:699`–`702`.
- `backend/app/tasks/stock_catalog_inventory.py:120` and `170` check
  dated field/purpose rights and exact coverage; lines 579–619 serialize
  private cursor acquisition and resume. `publish_catalog` in
  `backend/app/services/stock_catalog_publish.py:335`–`436` locks the
  catalog, checks independent rights, replays identical manifest digests,
  compares the expected generation and publishes new listing IDs under
  preserved issue IDs. Stage-assets at
  `backend/app/tasks/stock_catalog_import.py:192`–`263` consumes the
  one-shot claim before HTTP and rechecks exact listing/claims per attempt.
  `backend/app/services/stock_catalog_promotion.py:295`–`357` updates a
  matched existing binding under the same catalog lock and retains its
  coin ID. Rehearse source renewal and fresh exact-listing admissions
  followed by reattachment without changing original holdings/history.
  Publication contention and exact version tests are in
  `backend/tests/test_stock_catalog_publish.py:153` and `372`.

## Conditional cache retention

- `docker-compose.prod.yml:63`–`80` currently sets `--appendonly yes`
  with the persisted `redisdata` binding. Runtime acquires/disposes the
  existing private pool in `backend/app/main.py:30`–`49` and retrieves it
  from `backend/app/core/deps.py:35`–`37`. Scheduler wiring is at
  `backend/app/tasks/scheduler.py:281` and `344`–`362` with lifecycle
  cleanup near line 435. Existing flags default false in Compose.
- If active quote rights only permit a volatile cache, the catalog API
  (`backend/app/api/v2/stock_catalog.py:240`, `300`, `319`) and catalog
  scheduler (`backend/app/tasks/stock_catalog_quotes.py:217`–`407`) need
  the same private volatile path. The `_COMPLETE` operation at
  `backend/app/services/stock_catalog_quote_demand.py:65` and its call at
  `195`–`229` update queue, matched pending token, outcome and display
  bytes atomically on one Redis instance. Keep that whole key family
  together. Keep `reserve_account_attempt` on the shared account counter
  in `backend/app/tasks/stock_scheduler.py:50`–`78`. The limit is a
  minimum across review and config limits and the key is scoped by the
  provider account. `backend/app/tasks/stock_actions.py:885` uses that
  same reservoir, so the cache option must not split attempt budgets.
  Durable marks and receipts have their own admission and PostgreSQL
  policies. A dump comparison alone cannot establish Redis AOF behavior.

## Cutover, recovery and acceptance

- `deploy/deploy.sh:174` verifies the exact candidate source/revision
  before mutation, `recovery_gate` at line 309 binds the actual running
  revision and snapshot to the installed bundle under the operation lock,
  and `do_deploy` at line 569 builds before stopping writers and puts
  migration before backend/TLS health and frontend swap.
  `deploy/RUNBOOK.md:418`–`474` binds original/candidate volumes to
  measured identities, retains writer fencing and requires isolated
  restore before proceeding. Keep the pre-write recovery choice distinct
  from post-write recovery on the 0026 ledger. `do_rollback` at line 639
  selects from the deploy log and checks admission first. The default
  previous-version choice can be incompatible. The rehearsal at
  `deploy/tests/test-deploy-compatibility.sh:234`–`265` checks acceptance
  under the tested 0026 source and refuses incompatible rollback. Widening
  the rollback target or passing an earlier-schema refusal does not prove
  a safe post-write operational route.
- `frontend/e2e/stock-catalog.spec.ts:115`, `217`, `262`, `381`,
  `445` covers accessible selection, crypto independence, repricing and
  original-order lookup, closed marks without cached quotes, and private
  dividends/holdings. Use `deploy/tests/run-stock-browser.py --suite catalog`
  for affected paths and the workflow's complete browser scope for release.
  [Phase 18 live receipt](../18-make-simulated-stock-trades-work/18-LIVE-RECEIPT.md)
  is the pattern for sanitized venue, source time, exact ask/bid/cash and
  existing crypto check. [Phase 20 verification](../20-trade-and-value-stocks-from-search/20-VERIFICATION.md)
  shows how to record fixture scope and explicit zoom limitations.

## Missing direct analogs

- A validated catalog-specific admissions writer still needs a bounded
  operator step.
- There is no current two-client topology that routes the catalog's atomic
  key family separately from the shared provider budget. Add one only if
  actual retention scope needs it.
- There is no passing published v7 same-archive evidence for the recorded
  0023 predecessor, and the generic rollback command lacks a proven target
  after 0026 writes. Preserve rollout as an explicit gate until the plan
  produces compatible evidence.
