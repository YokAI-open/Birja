---
phase: 07-permitted-stock-discovery
reviewed: "2026-11-10 19:51:23 UTC"
depth: standard
diff_base: 6493ecb
files_reviewed: 72
files_reviewed_list:
  - .env.example
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/versions/0009_stock_discovery_schema.py
  - backend/alembic/versions/0010_seed_stock_catalog.py
  - backend/app/api/v1/router.py
  - backend/app/api/v1/stocks.py
  - backend/app/core/config.py
  - backend/app/models/__init__.py
  - backend/app/models/price.py
  - backend/app/models/stock.py
  - backend/app/schemas/stocks.py
  - backend/app/services/alpaca.py
  - backend/app/services/portfolio.py
  - backend/app/services/prices.py
  - backend/app/services/stock_admission.py
  - backend/app/services/stock_quote_rules.py
  - backend/app/services/stock_quotes.py
  - backend/app/services/stock_sessions.py
  - backend/app/services/stocks.py
  - backend/app/services/trading.py
  - backend/app/tasks/scheduler.py
  - backend/app/tasks/stock_scheduler.py
  - backend/pyproject.toml
  - backend/tests/conftest.py
  - backend/tests/test_accounts.py
  - backend/tests/test_alpaca.py
  - backend/tests/test_critical_coverage_config.py
  - backend/tests/test_migrations.py
  - backend/tests/test_scheduler_loop.py
  - backend/tests/test_seed_coins.py
  - backend/tests/test_stock_admission.py
  - backend/tests/test_stock_calendar_runtime.py
  - backend/tests/test_stock_catalog.py
  - backend/tests/test_stock_isolation.py
  - backend/tests/test_stock_migrations.py
  - backend/tests/test_stock_quote_rules.py
  - backend/tests/test_stock_quotes.py
  - backend/tests/test_stock_scheduler.py
  - backend/tests/test_stock_sessions.py
  - backend/tests/test_stocks_api.py
  - deploy/RUNBOOK.md
  - deploy/STOCK-DATA-ADMISSION.md
  - deploy/backup-manifest.sql
  - deploy/backup-snapshot.py
  - deploy/db/bootstrap-roles.sql
  - deploy/recovery-bundle.sh
  - deploy/tests/ops-fixtures.py
  - deploy/tests/test-backup.sh
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-db-operations.sh
  - deploy/tests/test-image-contracts.py
  - deploy/tests/test-restore-safety.sh
  - deploy/tests/test-rollback-db-security.sh
  - deploy/tests/selected-cutover.py
  - deploy/tests/test-stock-recovery-contracts.py
  - deploy/verify-restore.py
  - docker-compose.prod.yml
  - docker-compose.yml
  - frontend/e2e/markets.spec.ts
  - frontend/e2e/helpers.ts
  - frontend/e2e/stocks.spec.ts
  - frontend/src/api/stocks.test.ts
  - frontend/src/api/stocks.ts
  - frontend/src/components/StockAttribution.test.tsx
  - frontend/src/components/StockAttribution.tsx
  - frontend/src/components/StockSection.test.tsx
  - frontend/src/components/StockSection.tsx
  - frontend/src/hooks/useStocks.test.tsx
  - frontend/src/hooks/useStocks.ts
  - frontend/src/pages/MarketsPage.test.tsx
  - frontend/src/pages/MarketsPage.tsx
original_findings:
  critical: 3
  warning: 2
  info: 0
  total: 5
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
re_reviewed: "2026-11-10 19:58:28 UTC"
re_review_commit: 7fb4bedf1826ddc8d5c2b2a69e6cf557690e287b
final_delta_commit: 214560bfb89f59fb74bf12b0d78698eecc3d4123
---

# Phase 7: Code Review Report

## Narrative Findings (AI reviewer)

### Summary

Reviewed the Phase 7 source scope against implementation start `6493ecb`, including working-tree Plan 13 changes. Traced admission boundaries, quote persistence, calendar authority, authenticated response projection, browser lifetime/cancellation, crypto isolation, migration ACLs and successor recovery contracts. Findings below concern new Phase 7 behavior; accepted v1 W01–W08 debt is separate.

Review was read-only apart from this report. No database tests, production reads, provider calls, source edits or commits were performed. Pure local reproductions used existing synthetic admission fixtures and the production helpers. Passing suite/coverage claims were not treated as correctness proof.

Plan 13's removed None guard follows successful strict UTC checks; malformed Decimal exponent conversion is now caught as ArithmeticError and normalized through invalid_json. The image contract preserves the original inventory digest and separately fingerprints the exact eight approved additions.

## Critical Issues

### CR-01 — BLOCKER: Configured account/server scope is lost inside calendar and provider helpers

**File:** `/home/YokaiExchange/backend/app/services/stock_sessions.py:45`

**Related:** `stock_sessions.py:110,202`, `backend/app/services/alpaca.py:43`, `backend/app/services/stocks.py:148`, `backend/app/tasks/stock_scheduler.py:84`.

**Issue:** Settings and the operator import procedure support exact nondefault account/server identifiers. Outer scheduler/API admission checks pass those values, but build_sessions, session_at, persist_sessions and Alpaca _admitted evaluate evidence with the default account/server "birja". Correctly reviewed evidence for any other configured scope consequently cannot build sessions or fetch quotes. The API explicitly rechecks configured scope, then calls a default-scoped session evaluator, leaving valid configured installations permanently unknown.

**Reproduction:** Replace the scope in the existing admitted/evidence fixtures with account="reviewed-account", server="reviewed-server". evaluate_admission(calendar, "calendar", "derived", NOW, **scope) returns True, while build_sessions(NOW, calendar) returns []. The corresponding quotes collection decision returns True, while Alpaca _admitted raises AlpacaError("admission"). Executed as a pure local reproduction.

**Fix:** Pass the trusted configured account/server through every nested calendar and adapter entry point and every reevaluation. Do not infer trusted scope from the evidence being validated. Add nondefault-scope positive end-to-end tests plus mismatched-scope refusal tests, including persisted sessions, API and retry hooks.

### CR-02 — BLOCKER: Stored quote disclosure ignores retention permission and retention duration

**File:** `/home/YokaiExchange/backend/app/services/stocks.py:137`

**Related:** `stocks.py:186`, `backend/app/services/stock_admission.py:217`, `frontend/src/hooks/useStocks.ts:14`, `deploy/STOCK-DATA-ADMISSION.md:187`.

**Issue:** The API permits stored-quote reuse after only display/derived checks. It never checks retention_allowed or quota.retention_seconds. The duration is validated but never consumed anywhere in runtime code. Thus evidence with retention denied can still disclose matching stored quotes, contrary to the documented prohibition on reusing retained values. Even when retention is allowed, a one-second permitted retention period does not prevent indefinite last-quote disclosure during an otherwise valid admission/calendar window; the client receives no per-quote retention deadline and keeps displaying cached values until the much later admission expiry.

A generation increment does not repair the duration defect: a quote written under the current generation simply ages beyond its retention limit without any generation change. Persisted derived sessions and stopped/failed collectors similarly have no retention lifecycle.

**Reproduction:** Pure evaluation of replace(admitted(), retention_allowed=False) yields display=True, derived=True, retention=False; these first two results are precisely the API's permitted predicate. Static tracing of retention_seconds finds only its validator, with no consumer. With quota.retention_seconds=1 and an accepted quote collected two seconds ago, the current disclosure branch still returns the quote and the client retains it.

**Fix:** Define and enforce the reviewed retention horizon at stored-data reuse boundaries, require current retention permission, suppress out-of-horizon values and propagate the earliest applicable deadline to client cache projection. Add retention-denied and exact-expiry API/browser regressions. Define an explicitly reviewed cleanup/activation policy for actual retained storage and backups; do not silently add runtime DELETE privileges or destroy financial evidence.

### CR-03 — BLOCKER: Configured stock cycle budget does not bound the stock cycle

**File:** `/home/YokaiExchange/backend/app/tasks/stock_scheduler.py:218`

**Related:** `stock_scheduler.py:159`, `backend/app/core/config.py:21`, `deploy/STOCK-DATA-ADMISSION.md:209`.

**Issue:** stock_cycle_budget_seconds is documented as the maximum for all work/backoff and restricted to at most 20 seconds. It is used only to cap the HTTP adapter. The enclosing cycle always uses CYCLE_TIMEOUT_S=40, so admission reads, calendar generation, session persistence and post-fetch writes can exceed the operator's configured total budget and still commit successfully.

**Reproduction:** With an enabled synthetic settings object and stock_cycle_budget_seconds=1, substitute a preparatory _refresh that awaits 1.1 seconds and returns success. run_stock_cycle returns status="ok" after 1.1 seconds. Executed locally with only AsyncMock Redis and a patched _refresh; no external services.

**Fix:** Bound the entire owned refresh transaction/cycle by the configured total budget, additionally constrained by the existing lease safety margin. Keep bounded cleanup/token-owned release in finally. Test a hanging pre-fetch read/calendar stage and a hanging post-fetch write using the configured budget rather than only monkeypatching CYCLE_TIMEOUT_S.

## Warnings

### WR-01 — WARNING: Quote database tests expire on a hardcoded calendar date

**File:** `/home/YokaiExchange/backend/tests/test_stock_quotes.py:41`

**Related:** `backend/tests/test_stock_admission.py:12,29`, `backend/app/services/stock_quotes.py:157`.

**Issue:** stock_state inserts admitted() with validity fixed around 2026-11-10, while INSERT SELECT deliberately checks actual PostgreSQL clock_timestamp(). The numerous positive persistence tests therefore start returning zero writes after that admission window, regardless of their injected Python now. The default-clock test also combines actual observed time with this fixed authority. CI success today will become false failures on later dates.

**Fix:** Build database-test admission validity from actual test-stack UTC and use a coherent injected quote clock inside that window. Preserve dedicated expiry tests that deliberately cross the database clock; keep historical pure boundary tests independent of database wall time.

### WR-02 — WARNING: Scheduler fixture assumes every weekday is an open exchange session

**File:** `/home/YokaiExchange/backend/tests/test_stock_scheduler.py:35`

**Issue:** The dynamic fixture skips weekends only. On Thanksgiving, Christmas, Good Friday or another weekday closure, its 15:00 timestamp is a genuine closed session. Positive fetch/persistence tests then make no request, and tests waiting for HTTP entry time out. This is a CI reliability defect in the newly added tests.

**Fix:** Choose a verified open regular-session instant using the calendar fixture/library and ensure admission/review validity also encloses actual DB UTC. Alternatively inject a deterministic reviewed session clock while separately supplying real-clock-compatible storage guards. Add fixture-selection regression cases for a weekday holiday and a weekend.

---

_Reviewer: independent gsd-code-reviewer_
_Depth: standard_

## Focused independent re-review — 2026-11-10 19:58:28 UTC

**Reviewed correction:** `7fb4bedf1826ddc8d5c2b2a69e6cf557690e287b`, including its RED regressions from `70a6791`. Source was frozen during this pass.

**Current result:** all five original findings resolved for the disabled local implementation; zero active BLOCKERs and zero active WARNINGs in the corrected scope. Original findings and reproduction details above are retained as review history. This is a focused correction review, not a claim that the full phase or provider activation is complete.

| Original finding | Disposition and checked evidence |
| --- | --- |
| CR-01 | Resolved. Trusted account/server keywords reach calendar generation, evaluation and persistence; API and scheduler supply their configured scope, and the adapter uses it before every attempt and after receipt. No scope is inferred from untrusted evidence. Pure reproduction now builds 272 scoped rows, returns an open scoped session and admits the scoped adapter; omitting/mismatching scope still produces zero rows. Reviewed nondefault-scope API and real scheduler integration regressions. |
| CR-02 | Resolved for disclosure. Current retention permission is mandatory; collected_at plus the reviewed retention_seconds controls strict suppression, including equality. The response deadline is the earliest of quote permission and every returned quote's retention deadline, which the existing full-RTT client projection spends before caching. Reviewed denied/expired/equality/valid API cases, mixed quote deadlines and the new two-second transport/deadline cache-purge regression. No new runtime DELETE privilege was introduced. Actual storage/recovery-copy lifecycle remains an explicit unsatisfied activation prerequisite, described below. |
| CR-03 | Resolved. The whole owned refresh uses min(CYCLE_TIMEOUT_S, configured total), and token release remains in finally. Repeating the pure one-second budget/1.1-second preparatory-work reproduction now returns source_error at 1.0 seconds and releases the token exactly once. Reviewed pre-fetch cancellation and real post-fetch transaction rollback/lease-release regressions. |
| WR-01 | Resolved. Database quote fixtures anchor their injected observation and admission validity to actual current UTC rather than 2026-11-10. Dedicated expiration tests remain explicit and preserve database wall-clock guards. |
| WR-02 | Resolved. Scheduler fixture selection consults actual XNYS session dates instead of weekday arithmetic. Pure reproductions select Nov 27 after Thanksgiving, Dec 28 after Christmas, and Nov 16 after a weekend. Reviewed the corresponding holiday/weekend regressions. |

### Activation boundary retained

Disclosure suppression does not delete persisted quotes/sessions or encrypted backups and does not establish actual provider storage rights. The operator procedure explicitly requires independently verified rights for the real database/recovery lifetimes **or** a separately approved and verified privileged cleanup process before activation. Stopped collectors do not suspend that obligation. This prerequisite remains pending; this review neither waives it nor authorizes activation, agreements, cleanup, publication or production operations.

### Verification limits

This reviewer inspected the corrected code and regressions and executed only the pure local reproductions described above. No DB tests, browser runs, provider calls or production reads were performed by this reviewer. The executor's full suite/browser/image/role proof results must remain separately recorded with their actual final outcomes; in-progress runs are not treated as passing here.

## Final bounded follow-up — 2026-11-10 20:08:45 UTC

**Reviewed commits:** `670b221d7cd7d5c8d9aac2630d1088808fa4c5c8` and `214560bfb89f59fb74bf12b0d78698eecc3d4123`. Review limited to their source deltas and directly called contracts; source was frozen at 214560b.

**Result:** clean; zero new active BLOCKERs or WARNINGs.

- StockSection restores programmatic focus to its stable, non-tab-order heading after an initiated successful retry. Failed retries retain their existing recovery control. Loading now reserves twenty records; no new stock trading control or networking path was introduced.
- The e2e helper waits for the actual authenticated Markets heading. The unsupported /markets URL assertion was removed; App.tsx mounts Markets as the protected index route at /. This makes subsequent test navigation wait for completed authentication rather than merely the sign-in click.
- The image-transition collation probe lives in transition_fixture, while its explicit collation remains public. Probe ordering/index lookups use the qualified table throughout physical clone, logical restore and original restart assertions.
- The transition canonical reader selects the supported revision before composing schema_guard_sql and manifest_sql. query already strips psql output, so revision selection receives the exact revision. The strict public table/sequence allowlist is unchanged; no unknown object was added to the recovery contract.
- Existing canonical equality, forced-index probes, collation refresh ordering, complete restore verification and preserved-original byte fingerprint checks remain present. No runtime, provider, production or permission change was included.

This pass performed source review only, with no test execution or commits. Actual image-transition and full browser reruns were pending when requested and remain the executor's separate verification obligations. Earlier local proof counts reported by the executor are not independently re-executed or converted to completed results here. All previously recorded activation/storage-rights prerequisites remain pending and unchanged.

## Narrow legacy-fixture follow-up — 2026-11-10 20:13:16 UTC

**Scope:** uncommitted changes after `214560b` in `deploy/tests/test-rollback-db-security.sh` and `deploy/tests/selected-cutover.py` only. The parent explicitly scoped this correction to the legacy0008 rollback lane; successor0010 behavior remains a separate proof.

**Result:** clean; no additional active BLOCKERs or WARNINGs in this delta.

- The rollback fixture still checks immutable v0.3.1 project/lock bytes before and after its actual old-image build. It removes exactly the eight approved calendar additions from the current package inventory, checks their exact versions and independent artifact fingerprint, then requires equality of every remaining original distribution record. The project dependency comparison permits exactly exchange-calendars==4.13.2; it introduces no broad package exception.
- v0.4.0 app/Alembic bytes are extracted from the local release into a private temporary legacy context. Only those private paths replace current app/Alembic mounts for the legacy forward side. The actual repository migrations and the v0.3.1 old-runtime context are untouched; explicit schema0008 and old-image TLS rejection assertions remain.
- selected-cutover applies the same release bytes only after asserting its private clone resides under the fixed /tmp test root. It stages backend/app and backend/alembic in that clone before the existing synthetic fixture commit. Current retained operations/build files remain part of the prepared fixture; original production or repository checkouts are not rewritten.
- The unrelated cutover probe moves to transition_fixture and remains qualified at its final count assertion. Its explicit public collation, selected schema0008 assertion, original-volume fingerprints, retained-tool digests, real old-app checkout and same-installed-archive recovery assertions remain intact. The strict recovery schema allowlist is unchanged.

This review does not claim that the actual rollback rerun succeeded: it was still underway when requested. It also does not represent the fixture's v0.4.0-to-v0.3.1 legacy compatibility as successor0010 rollback compatibility. Separate successor source/schema/roles/TLS/exact-restore evidence must retain its own scope and result. No tests, source edits, commits, private reads or production operations were performed in this review pass.




