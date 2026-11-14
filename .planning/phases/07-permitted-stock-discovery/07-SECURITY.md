---
phase: 7
slug: permitted-stock-discovery
status: verified_local_mitigations
scope: implemented-local-plans-01-through-13
register_authored_at_plan_time: true
threats_total: 47
threat_obligations: 49
threats_closed: 47
threats_open: 0
asvs_level: 1
block_on: open
created: 2026-11-10
---

# Phase 7 — Security verification

Independent declared-mitigation audit of local Plans01–13. **Current source re-review at7fb4bed: both original gaps are corrected;47/47 unique declared local mitigation IDs are CLOSED.** Final refreshed execution gates and Plan14 remain separately pending. The following initial audit snapshot preserves the original two blockers and their evidence. This is not whole-phase approval or provider activation. All47 unique threat IDs/49 plan obligations were classified by declared disposition; every disposition is mitigate, none accept/transfer. T-07-SC appears in three plans and all three obligations are retained below. ASVS1 uses the repository template default (no explicit ASVS override configured); this is not an independent full ASVS certification. Open threats block advancement; no waivers were requested or created.

## Trust boundaries

| Boundary | Verified enforcement |
|---|---|
| External package/provider/operator evidence → trusted state | Reviewed exact dependency approval; bounded Decimal adapter; product/purpose/scope/generation evidence. Retention consumer gap remains open. |
| Browser/runtime → persisted authority and money | Authenticated read-only stock API, crypto-only financial paths, migrator-owned admission/calendar evidence and runtime SQL denials. |
| Derived sessions/quotes → displayed facts | Current committed authority and fresh UTC; exact generations; client full-RTT monotonic reduction. Retention deadline omission remains open. |
| Fixture source → operations artifacts | Fixed synthetic projects/roles, old-host source isolation, complete revisioned equality and original read-only fingerprints. |

## Initial audit snapshot — threat register and implementation evidence

Line references are repository-relative. Tests corroborate the identified implementation; summary prose alone was not treated as mitigation evidence. No tests were launched by this auditor.

| Plan | Threat ID | Category | Disposition | Status | Actual evidence / gap |
|---|---|---|---|---|---|
| 07-01 | T-07-01 | Tampering | mitigate | CLOSED | backend/alembic/versions/0009_stock_discovery_schema.py:69,187,228,239; backend/tests/test_stock_migrations.py:74,182,219 — CHECK/FK/discriminator enforcement plus exact populated financial comparison. |
| 07-01 | T-07-02 | Elevation | mitigate | CLOSED | backend/alembic/versions/0009_stock_discovery_schema.py:264; deploy/tests/ops-fixtures.py:1151,1580,2087 — conditional explicit grants, real existing-TLS-connection upgrade without repair and exact privilege matrix. |
| 07-01 | T-07-03 | Denial | mitigate | CLOSED | backend/alembic/versions/0009_stock_discovery_schema.py:292; backend/alembic/versions/0010_seed_stock_catalog.py:65; backend/tests/test_stock_migrations.py:324 — table locks and refusal before financial-reference deletion. |
| 07-01 | T-07-01-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-02 | T-07-04 | Elevation | mitigate | CLOSED | backend/app/services/trading.py:103,117,150,205; backend/tests/test_stock_isolation.py:276 — crypto-only preview/fill/holding/replay paths and unchanged-account assertions. |
| 07-02 | T-07-05 | Tampering | mitigate | CLOSED | backend/app/services/prices.py:48,80,104; backend/app/services/portfolio.py:51,60; backend/tests/test_stock_isolation.py — explicit crypto selectors and unsupported unpriced holdings. |
| 07-02 | T-07-02-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-03 | T-07-06 | Tampering | mitigate | CLOSED | deploy/backup-snapshot.py:83,103,154,185; deploy/backup-manifest.sql:45; deploy/verify-restore.py:783 — exact revision dispatch, every stock/admission/calendar field hash and schema equality. |
| 07-03 | T-07-07 | Information disclosure | mitigate | CLOSED | deploy/tests/ops-fixtures.py:33,79,120; deploy/verify-restore.py:70 — synthetic service seed, restricted child source access and private artifact mode checks; logs print bounded results rather than real rows. |
| 07-03 | T-07-08 | Elevation | mitigate | CLOSED | deploy/verify-restore.py:657,939; deploy/tests/ops-fixtures.py:1022 — fixed synthetic projects/targets and read-only original fingerprints; no live install invoked by these test paths. |
| 07-03 | T-07-03-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-04 | T-07-09 | Elevation | mitigate | CLOSED | deploy/db/bootstrap-roles.sql; backend/alembic/versions/0009_stock_discovery_schema.py:264; deploy/tests/ops-fixtures.py:958,1151,1557,1604 — SQLSTATE42501 assertions, no admission/catalogue/DDL/SET ROLE authority. |
| 07-04 | T-07-10 | Spoofing | mitigate | CLOSED | deploy/tests/ops-fixtures.py:2126,2150,2196; backend/app/db/session.py — genuine verified-TLS clients with untrusted CA/hostname/plaintext refusal. |
| 07-04 | T-07-11 | Tampering | mitigate | CLOSED | deploy/verify-restore.py:783,797,839; deploy/tests/ops-fixtures.py:535,558,581,1022 — complete equality, mutation detection, sequence progression and unchanged source fingerprints. |
| 07-04 | T-07-04-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-05 | T-07-12 | Spoofing | mitigate | CLOSED | backend/app/services/stock_admission.py:145,169,191,217; backend/tests/test_stock_admission.py — explicit product/purpose/scope/terms/version/expiry/quota validation; credentials absent from approval decision. Retention consumer gap is separately OPEN T-07-25. |
| 07-05 | T-07-13 | Information disclosure | mitigate | CLOSED | backend/app/core/config.py:249; backend/app/tasks/stock_scheduler.py:250; docker-compose.yml:132; docker-compose.prod.yml:165 — SchedulerSettings-only SecretStr, type-only errors and scheduler-only key injection. |
| 07-05 | T-07-14 | Elevation | mitigate | CLOSED | backend/alembic/versions/0009_stock_discovery_schema.py:264; deploy/STOCK-DATA-ADMISSION.md:104; backend/app/api/v1/stocks.py:13; deploy/tests/ops-fixtures.py:1557 — migrator import procedure, read-only public route and actual runtime authority denials. |
| 07-05 | T-07-05-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-06 | T-07-15 | Tampering | mitigate | CLOSED | backend/app/services/alpaca.py:42,59,76,121; backend/app/services/stock_quote_rules.py:104; backend/tests/test_alpaca.py:95,138,150 — bounded raw Decimal decoding, duplicate/depth and exact mapping/feed/conditions/side/time rejection. |
| 07-06 | T-07-16 | Denial | mitigate | CLOSED | backend/app/services/alpaca.py:182,207; backend/app/tasks/stock_scheduler.py:26,160,250; backend/tests/test_alpaca.py:195,220 — byte/count/depth/attempt/time limits and bounded backoff. |
| 07-06 | T-07-17 | Repudiation | mitigate | CLOSED | backend/app/services/stock_quote_rules.py:80,154; backend/app/services/stock_quotes.py:126; deploy/backup-manifest.sql:46 — exact source/feed/event/collection/session/generation persisted and recovered. |
| 07-06 | T-07-18 | Tampering | mitigate | CLOSED | backend/app/services/stock_quotes.py:149,179; backend/tests/test_stock_quotes.py:108,212,231,258 — INSERT SELECT current snapshot/DB clock and strictly newer source-time conflict update. |
| 07-06 | T-07-06-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-07 | T-07-SC | Supply-chain tampering | mitigate | CLOSED | Plans07/08/13 combined obligations: 07-PACKAGE-REVIEW.md:170 owner approval; backend/pyproject.toml and uv.lock exact reviewed eight packages; backend/tests/test_stock_calendar_runtime.py; deploy/scan-images.py:181,218; /tmp/birja-phase07-plan13-scans/status.json actual five-image pass (details below). |
| 07-07 | T-07-07-ASSUMED | Elevation of privilege | mitigate | CLOSED | 07-PACKAGE-REVIEW.md:22,30,170; 07-07-SUMMARY.md; 07-08-SUMMARY.md — reviewed exact registry/tag/wheel packet and explicit owner approval before locked install. Unsigned source/no attestation/unverified legitimacy protocol remain disclosed limitations. |
| 07-08 | T-07-19 | Spoofing | mitigate | CLOSED | backend/app/services/stock_admission.py:43; backend/app/services/stock_sessions.py:40,98; backend/tests/test_stock_calendar_runtime.py:25; backend/tests/test_stock_sessions.py:82,116 — independent official-date fixtures, review maximum24h, current evidence and fail-closed mismatch. |
| 07-08 | T-07-20 | Tampering | mitigate | CLOSED | backend/app/services/stock_sessions.py:98,185,211; backend/app/services/stock_quote_rules.py:168; deploy/tests/ops-fixtures.py:1502 — exact boundaries, fresh authority generation, migrator-only override authority and genuine cross-role evaluator. |
| 07-08 | T-07-SC | Supply-chain | mitigate | CLOSED | Plans07/08/13 combined obligations: 07-PACKAGE-REVIEW.md:170 owner approval; backend/pyproject.toml and uv.lock exact reviewed eight packages; backend/tests/test_stock_calendar_runtime.py; deploy/scan-images.py:181,218; /tmp/birja-phase07-plan13-scans/status.json actual five-image pass (details below). |
| 07-09 | T-07-21 | Denial | mitigate | CLOSED | backend/app/tasks/stock_scheduler.py:26,89,250; backend/app/tasks/scheduler.py:322; backend/tests/test_stock_scheduler.py:458,490 — independent leases/cadence/budgets, thread-isolated cold calendar, concurrent loops and hanging-source/stop proofs. |
| 07-09 | T-07-22 | Information disclosure | mitigate | CLOSED | backend/app/core/config.py:249; backend/app/tasks/scheduler.py:312; backend/app/tasks/stock_scheduler.py:250; docker-compose.prod.yml:165 — separate keyed HTTP client, scheduler-only keys, no raw provider exception/body logging. |
| 07-09 | T-07-23 | Tampering | mitigate | CLOSED | backend/app/tasks/stock_scheduler.py:117,146,192,213; backend/app/services/stock_quotes.py:149; backend/tests/test_stock_scheduler.py:322,433 — fresh committed per-attempt and post-I/O authority/lease checks plus guarded write and precommit rollback. |
| 07-09 | T-07-09-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-10 | T-07-24 | Spoofing/Elevation | mitigate | CLOSED | backend/app/api/v1/stocks.py:23; backend/app/api/v1/router.py; backend/tests/test_stocks_api.py:122 — CurrentUserDep mandatory; only GET stock discovery, no admin/provider proxy. |
| 07-10 | T-07-25 | Information disclosure | mitigate | OPEN (BLOCKER) | OPEN: backend/app/services/stocks.py:137–140 only checks display and derived; :181–195 exposes permitted dated historical rows without retention_allowed or collected_at+retention_seconds cutoff. The envelope :218 does not bound display lifetime to retained-quote rights. deploy/STOCK-DATA-ADMISSION.md:20,25,187 and Plan05 require separate retained-data permission decisions. |
| 07-10 | T-07-26 | Tampering | mitigate | CLOSED | backend/app/services/stocks.py:83,95; backend/app/schemas/stocks.py; backend/tests/test_stocks_api.py:87,382 — bounded catalogue-first left join, typed immutable response and exact Decimal JSON string assertions. |
| 07-10 | T-07-10-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-11 | T-07-27 | Information disclosure | mitigate | OPEN (BLOCKER) | OPEN: frontend/src/hooks/useStocks.ts:13,28,50,72 enforces supplied admission/calendar deadlines and rejects superseded/session-invalid responses, but API supplies no retained-quote cutoff. A cached historic quote can remain past reviewed retention_seconds; frontend cannot derive the omitted authority. Other generation/logout/RTT protections are present. |
| 07-11 | T-07-28 | Tampering | mitigate | CLOSED | frontend/src/api/stocks.ts:81,102,160 — exact BigInt decimal comparison, known enums, civil timestamps, twenty unique positive identities and whole-response validation; corresponding stocks.test.ts adverse cases. |
| 07-11 | T-07-29 | Injection | mitigate | CLOSED | frontend/src/components/StockAttribution.tsx:17; frontend/src/components/StockAttribution.test.tsx — required attribution is ordinary React text; malicious markup assertion finds no executable element. |
| 07-11 | T-07-11-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-12 | T-07-30 | Spoofing | mitigate | CLOSED | backend/app/schemas/stocks.py; frontend/src/components/StockSection.tsx:220,256; frontend/src/components/StockAttribution.tsx:22 — explicit phase-disabled capability, unverified status and separate calendar/recent facts; no stock Trade control. |
| 07-12 | T-07-31 | Information disclosure | mitigate | CLOSED | frontend/e2e/stocks.spec.ts; frontend/src/hooks/useStocks.test.tsx:133,170,187,322 — real browser revocation/local-deadline/delayed-response tests and cache purge. These cover supplied admission/calendar deadlines; missing retention deadline is OPEN T-07-27, not claimed covered. |
| 07-12 | T-07-32 | Denial | mitigate | CLOSED | frontend/src/pages/MarketsPage.tsx; frontend/src/components/StockSection.tsx; frontend/e2e/markets.spec.ts; frontend/e2e/stocks.spec.ts — independent stock errors/retry/data projection leave fifteen crypto links and navigation intact. |
| 07-12 | T-07-12-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |
| 07-13 | T-07-33 | Tampering | mitigate | CLOSED | .github/workflows/ci.yml:44,47,72,73,126,302; backend/tests/test_critical_coverage_config.py; deploy/tests/test-ci-ops.py; deploy/scan-images.py:181,218 — original80/100 coverage and unfixed-inclusive strict HIGH/CRITICAL gates retained; actual local passing scans inspected. |
| 07-13 | T-07-34 | Elevation | mitigate | CLOSED | backend/tests/conftest.py:21; backend/tests/guard.py; deploy/verify-restore.py:657,939; deploy/tests/ops-fixtures.py:79 — guard before app import, exact isolated identities, private temporary fixture and source-restricted recovery subprocesses. |
| 07-13 | T-07-SC | Supply-chain | mitigate | CLOSED | Plans07/08/13 combined obligations: 07-PACKAGE-REVIEW.md:170 owner approval; backend/pyproject.toml and uv.lock exact reviewed eight packages; backend/tests/test_stock_calendar_runtime.py; deploy/scan-images.py:181,218; /tmp/birja-phase07-plan13-scans/status.json actual five-image pass (details below). |
| 07-13 | T-07-13-SC | Supply-chain tampering | mitigate | CLOSED | No dependency additions in this plan; source/lock delta from6493ecb places calendar/native changes solely in approved Plan08. frontend/package.json and package-lock.json unchanged; backend/uv.lock pinned and audited. Shared approval/runtime/image evidence is T-07-SC. |

## Open threat details

1. **T-07-25 — retained quote disclosure.** A quote admission with display_allowed/derived_allowed true but retention_allowed false still authorizes historical persisted quote display. With retention_allowed true, retention_seconds is only checked as a bounded integer in the evidence validator, not applied at the disclosure boundary. Denied retention must not permit reuse from stored quote rows; an expired retention window must remove the retained values/timestamps even while the broader admission/calendar lifetime remains valid. Searched stock_admission.py, stocks.py, stock_quotes.py, stock_scheduler.py, and client admission/projection code. No enforcement call at API display was found.
2. **T-07-27 — omitted downstream retention deadline.** The client correctly enforces the supplied admission and calendar lifetimes, including full request/refresh RTT. The server does not convey a retention-derived per-quote/envelope lifetime, so those otherwise-correct protections cannot purge cached historical values at their true retention cutoff. Fix the producer/consumer contract coherently and verify delayed initial response, retained background data and timer purge at the exact boundary. Do not weaken existing generation/current-clock checks.

The independently reported configured nondefault account/server path also fails because inner calendar/adapter admission defaults remain birja. That is a functional availability defect requiring code-review resolution; it fails closed and is not misreported here as an authorization bypass. Re-review any scope-propagation fix against T-07-12/19/20/23/25.

## Actual scan evidence inspected

`/tmp/birja-phase07-plan13-scans/status.json`: ok=true; runtime, builder, postgres, redis and node each exit_code0 and qualifying_findings0. Actual scanner is pinned Trivy0.76.1, database UpdatedAt2026-11-10T19:01:23Z / NextUpdate2026-11-11T19:01:23Z. Source scan code explicitly requests HIGH,CRITICAL and never ignores unfixed findings. These are executed image scans, not static contract-test substitutes.

| Lane | Actual engine image SHA256 |
|---|---|
| runtime | 06f776b631669033e41f858e68998f4cccf0e7240c140a011de0e02e4993d885 |
| builder | 90c1d23a41fe7f2771255494105bd8ced94ae890c77b61cd98e9936cb9e266af |
| node | e44078913d853de420bdd91a255281140c0265c93c18f5675e5088416d6ff16e |
| postgres | f131db66371391e404c80cef7dd40f31b1b54eb264a6cb032925d9a3859f93f4 |
| redis | 26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48 |

The current restricted-role fixture log `/tmp/birja-phase07-plan13-roles-final.log` already records65 SQL denials, exact stock ACLs and the genuine populated0008_no_grant_repair calendar evaluator. Final current-source fresh-TLS/remaining full operations completion belongs to the executor; this audit does not invent that unfinished run's result. Earlier source-backed role/restore assertions remain present and reviewed.

## Unregistered flags

None. Summaries01–12 contain no dedicated `## Threat Flags` entries; their known-stub/threat/boundary sections were inspected as well as changed implementation paths. Implemented migrations, quote/session authority, private provider boundary, read-only endpoint, client caching and native dependencies are all mapped to the register above. Unknown status/actions and disabled execution are explicit phase boundaries, not hidden unfinished mitigations.

## Accepted risks log

No accepted risks. Exact calendar package installation was explicitly approved after disclosure of unsigned source, missing wheel attestation and unverified installed legitimacy protocol. That approval establishes the declared pre-install checkpoint only; registry hashes/security scans do not constitute proof of authentic authorship or live market-data rights. No accept/transfer threat disposition was invented from the approval.

## Pending external scope

Plan14 has not executed. Its separate T-07-35/36/37/38 and T-07-14-SC are **not audited/closed** by this local audit and are not included in47 implemented threat IDs. Actual provider product/display/derived/retention permission, authorized bounded private verification and owner UI acceptance remain blocking external checkpoints. No fixture, package approval or credential establishes those rights. No provider/private API, production/B2, service, deployment or publication action was taken by the auditor.

## Audit trail

| Date | Scope | Unique threats | Closed | Open | Auditor |
|---|---|---|---|---|---|
| 2026-11-10 | Plans01–13 local source and declared mitigations | 47 | 45 | 2 | Independent gsd-security-auditor |

Implementation files were read-only. Only07-SECURITY.md was created; no tests/commits/waivers were made. Re-audit the scoped fixes before setting threats_open0/statusverified.


## Focused independent re-review — current source7fb4bed

**Current declared source mitigation status: SECURED,47/47 unique IDs closed,0 open.** The original49-obligation register and two OPEN findings above are retained as audit history, not current findings. No accept/waiver was used. This re-review inspected the actual committed source delta and regression assertions; the auditor did not modify implementation or run tests.

| Threat | Current disposition | Verified corrective evidence |
|---|---|---|
| T-07-25 | CLOSED / mitigate | backend/app/services/stocks.py:137–141 requires current display, derived **and retention** purposes using exact configured scope; :174–177 calculates immutable collected_at+quota.retention_seconds and refuses equality/expiry; :191–196 only discloses matched permitted rows and tightens the envelope to the earliest disclosed deadline; :228 returns that deadline. backend/tests/test_stocks_api.py:87 checks denied, valid, expired and exact-boundary retention. :133 mixed-window test asserts earliest deadline and redacts the first expired quote while preserving a separately eligible row. |
| T-07-27 | CLOSED / mitigate | stocks.py:196,228 exposes the conservative earliest retained-value lifetime through the existing admission.valid_until. frontend/src/hooks/useStocks.ts:9–15 spends full monotonic RTT/elapsed before authority; :50 removes quote values without authority; its query function calls purgeExpired before caching and display timer purges cache. frontend/src/hooks/useStocks.test.tsx:340 simulates a2-second initial transport against a2-second shortened retention deadline and asserts both visible and cached quotes are null. Existing :112 and :322 cases cover retained background data and timed private-cache purge. |
| T-07-12/19/20/23 | CLOSED / mitigate retained | backend/app/services/stock_sessions.py:40,104,196 now accepts trusted account/server keywords and passes them to every nested evaluate_admission/build_sessions call. stock_scheduler.py:88 builds scope from settings and propagates it to build/persist/open and adapter; alpaca.py:42,200,212,234,262 uses exact supplied scope on initial/per-attempt/post-I/O admission. API stocks.py:148 uses the same scope in session_at. No evidence-derived substitution or permissive bypass was added. Nondefault-scope API/scheduler regression assertions are present. |
| T-07-16/21 | CLOSED / mitigate retained | backend/app/tasks/stock_scheduler.py:229 wraps the entire refresh with asyncio.timeout(min(CYCLE_TIMEOUT_S, settings.stock_cycle_budget_seconds)); existing per-source timeout,45-second token lease, cadence key and token-owned final release remain. Configured-budget hanging source/DB regressions exercise the whole-cycle refusal. |

The current response-time final committed evidence read/fresh UTC, SQL guards, generation checks, auth/no-store boundary, Decimal adapter and client session/generation cancellation remain intact. Scope propagation fixes a previously fail-closed functional refusal; it adds no runtime admission administration, financial mutation, provider route or DELETE grant.

### Storage-rights boundary remains an external activation gate

Actual source redaction is not physical deletion of a persisted/encrypted backup copy. deploy/STOCK-DATA-ADMISSION.md:200 now explicitly keeps activation disabled until verified rights cover the actual database/recovery lifetimes **or** an independently approved and verified privileged cleanup process meets every storage deadline, including stopped/failed collectors. This correction does not claim cleanup exists, does not invent provider retention permission and does not expand runtime grants. These live terms/activation obligations remain under unexecuted Plan14 and cannot be closed by local tests or this report.

### Execution evidence after the correction

The earlier five-image pass recorded above remains historical pre-correction evidence. Fresh final-source images/scans and full serial operations are being rerun by the executor and **are not claimed passed here until their actual results are recorded**. The inspected `/tmp/birja-phase07-plan13-roles-final.log` now additionally contains both genuine calendar consumer lanes (populated0008_no_grant_repair and fresh_bootstrap), TLS CA/hostname/plaintext denials and65 SQL privilege denials. This corroborates those already-reviewed source controls without replacing the final full-operations gate.

| Date | Scope | Unique threats | Closed | Open | Auditor |
|---|---|---|---|---|---|
| 2026-11-10 | Focused independent source re-review at7fb4bed | 47 | 47 | 0 | Independent gsd-security-auditor |

No implementation changes, test runs, commits, provider/private/prod operations, accepted risks or waivers were made by the auditor. Final phase sign-off remains pending the executor's actual refreshed gates and explicit Plan14 authorization/evidence/acceptance.
