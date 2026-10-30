---
phase: 5
slug: portfolio-and-history
status: all-gates-passed
nyquist_compliant: true
wave_0_complete: true
created: 2026-10-29
---

# Phase5 — Validation Strategy

Planning coverage and all local implementation gates are complete as of 2026-10-30. New tests exist and have executed; evidence is recorded below and in summaries 05-01 through 05-07. Remote CI/browser execution and fresh human UAT have passed; see the final checkpoint closeout below. `nyquist_compliant:true` describes feedback coverage, not human approval or completed phase acceptance.

Existing pytest/pytest-asyncio/httpx and isolated PostgreSQL/Redis from docker-compose.test.yml; existing Vitest/RTL/QueryClient; Playwright only ephemeral fake-price/console-email CI. Focused commands target<60s after services ready; measure and shard focused selections if necessary. Full suites are intentionally longer. Backend/frontend total coverage≥80%; critical paths100%, identical CI/CLAUDE list adds portfolio_math.py,portfolio.py,history.py. No install or new framework needed.

## Per-Task Feedback and Producers

Commands run independently from repo root. Run each RED command separately; behavioral failure is expected before Task2, not fixture failure. GREEN commands use && to preserve failure and repo-root subshells when changing directories. In-task RED sections are the logical Wave0 producers, avoiding a horizontal setup phase.

|Task|Wave|Requirements|Threat suffixes|Producer/dependency|Command or explicit checkpoint|Status|
|---|---|---|---|---|---|---|
|05-01-1|1|PORT-01..05|AUTH,MATH,UI|Creates portfolio math/service/API,frontend guard/page tests,e2e before01-2|`(cd backend && uv run pytest tests/test_portfolio_math.py tests/test_portfolio_service.py tests/test_portfolio_api.py -x -q)`<br>`(cd frontend && npm run test -- --run src/api/portfolio.test.ts src/pages/PortfolioPage.test.tsx)`; independently expected RED|passed; 05-01 summary/local evidence|
|05-01-2|1|PORT-01..05|AUTH,MATH,UI|01-1+existing accounts/App|`(cd backend && uv run pytest tests/test_portfolio_math.py tests/test_portfolio_service.py tests/test_portfolio_api.py tests/test_accounts.py -x -q) && (cd frontend && npm run test -- --run src/api/portfolio.test.ts src/pages/PortfolioPage.test.tsx src/App.test.tsx)`|passed; 05-01 summary/local evidence|
|05-02-1|2|PORT-01..03|UI,MATH|Creates financialDisplay.test;extends page tests before code;depends01|`cd frontend && npm run test -- --run src/lib/financialDisplay.test.ts src/pages/PortfolioPage.test.tsx && npm run typecheck`|passed; 05-02 summary/local evidence|
|05-02-2|2|PORT-01..04|UI,MATH|Extends math/page tests before code;depends02-1|`(cd backend && uv run pytest tests/test_portfolio_math.py -x -q) && (cd frontend && npm run test -- --run src/lib/financialDisplay.test.ts src/pages/PortfolioPage.test.tsx)`|passed; 05-02 summary/local evidence|
|05-03-1|3|PORT-01..05|TIME,UI|Extends page timer/state assertions before code;depends02|`cd frontend && npm run test -- --run src/pages/PortfolioPage.test.tsx src/components/FreshnessBadge.test.tsx src/lib/age.test.ts`|passed; 05-03 summary/local evidence|
|05-03-2|3|PORT-01..05|MATH,AUTH,TIME|Creates snapshot test;extends service/API;real independent sessions/events|`cd backend && uv run pytest tests/test_portfolio_snapshot.py tests/test_portfolio_service.py tests/test_portfolio_api.py -x -q`|passed; 05-03 summary/local evidence|
|05-04-1|4|HIST-01..02|AUTH,CURSOR,HISTORY|Creates history service/API/guard/page;extends allow-list/e2e;depends03|`(cd backend && uv run pytest tests/test_history_service.py tests/test_history_api.py -x -q)`<br>`(cd frontend && npm run test -- --run src/api/history.test.ts src/pages/HistoryPage.test.tsx)`; independently expected RED|passed; 05-04 summary/local evidence|
|05-04-2|4|HIST-01..02|AUTH,CURSOR,HISTORY|04-1+existing accounts/App|`(cd backend && uv run pytest tests/test_history_service.py tests/test_history_api.py tests/test_accounts.py -x -q) && (cd frontend && npm run test -- --run src/api/history.test.ts src/pages/HistoryPage.test.tsx src/App.test.tsx)`|passed; 05-04 summary/local evidence|
|05-05-1|5|HIST-01..02|CURSOR,HISTORY|Creates useHistory.test;extends page tests before code;depends04|`cd frontend && npm run test -- --run src/hooks/useHistory.test.tsx src/pages/HistoryPage.test.tsx`|passed; 05-05 summary/local evidence|
|05-05-2|5|HIST-02|INDEX,CURSOR|Extends existing migration tests before schema;serial isolated DB;after04|`(cd backend && uv run pytest tests/test_migrations.py -x -q && uv run ruff check app/models/trade.py alembic/env.py alembic/versions/0008_trade_history_index.py tests/test_migrations.py)`|passed; 05-05 summary/local evidence|
|05-06-1|6|All7|REFRESH|Creates useTrade.test before hook edit;depends03+05|`cd frontend && npm run test -- --run src/hooks/useTrade.test.tsx src/pages/TradePage.test.tsx`|passed; 05-06 summary/local evidence|
|05-06-2|6|All7|CACHE|Creates privateQueries/auth mutation tests;extends client/App before code|`cd frontend && npm run test -- --run src/lib/privateQueries.test.ts src/hooks/useAuthMutations.test.tsx src/api/client.test.ts src/App.test.tsx`|passed; 05-06 summary/local evidence|
|05-07-1|7|All7|AUTH,UI|Extends App/e2e before responsive shell;depends06|`cd frontend && npm run test -- --run src/App.test.tsx src/pages/PortfolioPage.test.tsx src/pages/HistoryPage.test.tsx && npm run typecheck`|passed; 05-07 summary/local evidence|
|05-07-2|7|All7|TEST,SC,MATH|Existing/new suites;01-1/04-1 e2e extended|`(cd frontend && npm run e2e -- --list) && (cd backend && uv run pytest tests/test_portfolio_math.py tests/test_portfolio_service.py tests/test_portfolio_api.py tests/test_history_service.py tests/test_history_api.py -x -q)`; actual e2e only CI|passed; 05-07 summary/local evidence|
|05-07-3|7|All7|All|All earlier test producers|`(cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest --cov=app --cov-fail-under=80 -q && uv run coverage report --include=app/services/otp.py,app/services/auth.py,app/services/accounts.py,app/services/ratelimit.py,app/services/email.py,app/core/security.py,app/core/deps.py,app/services/price_rules.py,app/services/prices.py,app/services/trade_math.py,app/services/trading.py,app/services/portfolio_math.py,app/services/portfolio.py,app/services/history.py,app/api/v1/history.py --fail-under=100 && uv run pip-audit) && (cd frontend && npm run lint && npm run typecheck && npx prettier --check . && npm run test -- --coverage && npm run build && npm audit --audit-level=high)`; image/offline/review gates per07-3|passed; 05-07 summary/local evidence|
|05-08-1|8|All7|TEST|07 concrete result|Explicit fresh dev-rebuild choice;after approval service health/alembic0008 only|passed; explicit user response and 05-08 evidence|
|05-08-2|8|All7|UI,TEST|Approved rebuild+07 evidence|Fresh human real-price/browser UAT at375/768/1024/1440,200%zoom/keyboard/reduced-motion|passed; explicit user response and 05-08 evidence|
|05-08-3|8|All7|RELEASE|UAT/reviews/local evidence/git summary|Scoped push/PR/not-yet;separate fresh release intent or skipped;green CI before separately approved merge|passed; explicit user response and 05-08 evidence|

## Threat and Behavioral Map

Every suffix above has prefix `T-05-`; per-plan threat models name dispositions. ASVS5 L1/high-severity-blocking applies, not certification. No new cryptography; cursor is a seek boundary, not authority.

|Threat|STRIDE / ASVS5 categories|Required evidence|
|---|---|---|
|AUTH|I/E;V4 API and Web Service,V6 Authentication,V8 Authorization,V14 Data Protection|GET401/no-store/read-only,fixed user predicates,two users/foreign boundary,exact two-GET allow-list addition|
|MATH|T;V2 Validation and Business Logic|One nonlocking financial projection,real-PG complete-before/after,Decimal50/raw/HALF_EVEN,zero basis/start/total,dust/huge/tiny/weighted buys+partial sells,completed return|
|TIME|T;V2,V4|119/120/300/301/configured rules,future skew,late clock,oldest/worst,missing/inactive,last-known vs incomplete,failed-refresh aging|
|UI|T/I;V1 Encoding and Sanitization,V2|Explicit fresh/aging/stale/unpriced schema/guard/fixture assertions;strict plain-string/null guards,React escaping,no financial Number math,all mobile fields/one representation,neutral signs,N/A vs unavailable,validated bar widths,local+UTC times,focus/reduced motion|
|CURSOR|T/D;V1,V2,V4|≤512 strict stdlib schema/version/types/UTF8/JSON/microseconds/bigint;422;1..100/default25/limit+1/last-returned cursor,bound tuple,ties/inserts/isolation|
|HISTORY|T/R;V2,V4|Stored cash_delta/fee/execution values,inactive/dust0,stable string IDs,append/retry/end/focus/retained pages/sequential refresh|
|INDEX|D/T;V2,V14|0008 concurrent autocommit/per-migration boundaries,populated downgrade/re-upgrade,index validity/definition/key order,parity/full roundtrip,preserve0007 guard,recovery docs|
|CACHE|I/E;V4,V7 Session Management,V8,V14|Cached/in-flight A→expired→B,await cancel/remove before me publish,logout/late response/refresh-retry signal,preserve observed me|
|REFRESH|T;V2|Buy/sell/replay await all five key invalidations,no optimistic money/duplicate fill|
|TEST|I/T;V14|Isolated synthetic PG/Redis,fake/console CI only,discovery≠pass,human-only real-email UAT,no secrets/balances output|
|RELEASE|T/E;V8|Existing branch/upstream preflight,scoped push/PR,green CI+separate merge approval,fresh release choice or skipped|
|SC|T;supply chain|No install/new dependency,pip-audit/npm audit high,critical list parity|

## Sampling and Boundaries

Each implementation task runs its focused feedback before commit; no three consecutive implementation tasks lack feedback. At wave end run relevant regression suites.07 is the full final gate; repeat broader suites only after new failures/changes. All eight waves are serial:01→02→03→04→05→06→07→08;06 retains03+05 dependencies. Fixed PostgreSQL/Redis resources cannot overlap: autouse auth cleanup deletes OTP/rate-limit keys and migration roundtrips downgrade birja_test to base. Wait for each plan and teardown before the next, even with parallelization enabled; isolated stack tears down with down-v in finally. Never inspect .env/prod.env/secrets/individual balances or authenticate/trade on real dev/prod.

E2e execution remains pending until permitted ephemeral fake-price/console-email CI exists; no real-email fallback.08 push/PR choice can enable CI. Not-yet leaves remote checks explicitly pending; required CI must pass before any merge. New test files all have producers above and existing frameworks/fixtures; no MISSING scaffold remains unassigned.

08 human review covers the four roadmap outcomes,375/768/1024/1440px,200% zoom,keyboard/safe-area/end focus/reduced motion. Synthetic unavailable/zero/cursor/refusal branches are automated fixtures, never written to real data. Rebuild approval, browser approval, push, merge and release authority stay distinct.

## Sign-Off

- [x] All18 tasks mapped to automated feedback or explicit human checkpoints.
- [x] Every test has an earlier/in-task RED producer; no watch flags/new framework.
- [x] Eight serial waves enforce shared PostgreSQL/Redis fixture isolation and disjoint ownership.
- [x] Exact threat-linked assertions planned; high findings block.
- [x] Actual RED/GREEN/full-suite/inline-review evidence recorded below and in plan summaries.
- [ ] Fresh human UAT approved.
- [x] CI/e2e green at 0595c89; merge remains separately gated.

**Approval:** Local gates, independent review, remote CI/e2e and 05-08 human checks passed. Merge requires separate approval. Earlier execution notes below retain the evidence available at that time.

## Actual Local Execution — 05-07

Executed 2026-10-30, beginning 07:47 UTC. Existing locked tools/dependencies were reused; no install, upgrade, real account, real-email flow, dev/prod rebuild, deployment or remote write was performed. All database suites ran serially against guarded synthetic localhost PostgreSQL/Redis. Every stack lifecycle used `docker compose --env-file /dev/null -f /home/YokaiExchange/docker-compose.test.yml` and Python `finally` executed absolute-path `down -v`. The final isolated network and containers were removed.

| Gate | Actual result |
|---|---|
| Navigation RED | Two behavioral failures: four primary links instead of three, and missing heading focus; 14 old tests passed. |
| Navigation GREEN | App/PortfolioPage/HistoryPage: 49 passed; TypeScript and ESLint passed. |
| Critical-list RED/GREEN | Initial pytest invocation lacked the isolated Redis fixture and errored; direct invocation then failed on the missing financial modules. After updates, direct assertion and isolated pytest passed. Lists are byte-identical; regression also requires the history route's independent limit validation. |
| Focused financial/API/parity | 79 passed in 2.30s; stack startup/test/teardown 7.48s. |
| Backend static | `uv run ruff check .`, `uv run ruff format --check .`: 99 files; `uv run mypy app`: 49 modules passed. Final changed tests also pass lint/format. |
| Initial full backend | 566 passed in 23.13s; 99.59% overall. The new critical gate correctly failed history at 94%, identifying three missing branches. |
| Final full backend | `uv run pytest --cov=app --cov-fail-under=80 -q`: 573 passed in 14.95s; 99.90% total, including branch coverage. The seven added cases prove noncanonical base64 rejection, naive-time rejection, and five invalid internal page sizes before any SQL statement. No exclusion or production branch was removed. |
| Final critical gate | Exact current CI/CLAUDE include list: 797 statements/160 branches, zero misses/partial branches, 100%. Includes portfolio_math, portfolio, history and history API alongside all previous critical modules. |
| Python audit | `uv run pip-audit`: no known vulnerabilities. Final backend coverage/audit/in-image smoke lifecycle: 26.15s. |
| Frontend static | `npm run lint`, `npm run typecheck`, `npx prettier --check .` passed. |
| Final full frontend | `npm run test -- --coverage`: 257 passed in 24 files, 15.48s; statements 99.05%, branches 97.53%, functions 100%, lines 99.82%. New private-read final-401 and direct-entry regressions cover both new routes. |
| Final focused frontend | After exact retry-copy assertion and browser focus checks: App/HistoryPage 30 passed in 2.96s; types and Playwright listing passed. |
| Frontend build | `npm run build` passed; Vite built 2199 modules, JS 381.26 kB / 119.31 kB gzip, CSS 25.72 kB / 6.39 kB gzip. |
| npm audit | `npm audit --audit-level=high` exited 0: three low advisories in existing deepmerge/shadcn chain; no high or critical finding. No dependency changes; tracked separately in deferred-items.md. |
| Image builds | `docker build --target test-builder -t birja-backend-test:phase05-07 backend` and runtime target `birja-backend-runtime:phase05-07` passed. No deployment/real service restart. |
| In-image smoke | `docker run --rm --network host birja-backend-test:phase05-07 pytest tests/test_smoke.py -q`: 5 passed in 0.78s on isolated fixtures. |
| Runtime smoke | Runtime image with `--network none`, ENV=test and test-only dummy settings: UID 1001, app import and new GET route presence passed. No resource connection attempted. |
| Offline deploy checks | `bash -n` passed all 12 deploy/test shell scripts. All five actual `deploy/tests/*.sh` ran with their offline stubs: app-services 8/8, reexec 14/14, rollback-target 18/18, smoke-ports 11/11, smoke-trading 7/7; 58/58. |
| CI browser discovery | `npm run e2e -- --list`: 11 tests in six files. Four responsive fixture tests at 375/768/1024/1440, cash-only flow and captured actual buy→portfolio→history→sell story are discovered by existing testDir ./e2e and unfiltered CI `npx playwright test`. Discovery is not a browser pass. Existing deployed-only CSP test is skipped without E2E_PROD_URL. |
| Change hygiene | `git diff --check` passed; no tracked deletions, package/lock changes, new dependency or blocking stub. Unrelated pre-existing .claude files preserved. |

### Separate Inline Review Passes

These were performed sequentially by the executor, not by independent reviewers. The orchestrator retains independent phase review.

1. **Code:** traced private routes through hooks/API guards to session-scoped scalar services and Decimal output, mutation invalidation, cancellation/identity publication, strict cursor lookahead and concurrent index migration. Full API/real-PG snapshot/populated migration regressions passed. No blocking correctness finding remains. Added history branch tests after the enforced coverage failure, with behavioral assertions and no coverage exclusions.
2. **Security:** checked T-05-AUTH/UI/TEST/SC against auth/no-store/read-only/isolation tests, bounded cursor and page sizes, bound ORM predicates, unchanged CSRF/session behavior, React escaping and plain-string formatting, private-cache cancellation and CI console/fake placeholders. No new logging/crypto/token storage/trust-boundary surface. No high finding remains; pip audit clean and npm has only the three recorded low advisories.
3. **UI contract:** traced routes and complete holdings/history fields, complementary CSS table/card visibility, signed/null outcomes, timestamps, retained retry/end-focus states and design tokens. One responsive primary nav with separate Account, 44px targets, decorative Lucide icons, 56px mobile tabs/safe area, 80px content inset and focused-element scroll clearance is implemented. Route heading focus is separate from data refresh. Corrected retained-pagination error copy to the exact contract and asserted it. Actual media-query rendering, zoom and subjective appearance remain pending browser/human checks.

### Source Audit Closure Map

Every row of 05-SOURCE-AUDIT.md was compared with actual implementation/tests; its original COVERED planning labels are preserved as history.

| Source rows | Implementation/evidence and remaining boundary |
|---|---|
| GOAL Story/SC1..4; REQ PORT-01..05/HIST-01..02 | Reachable App routes, portfolio/history pages and private APIs; full backend/frontend suites. CI full-story and fresh human acceptance pending. |
| R1..R2 | Single scalar nonlocking account/positive-holding/all-coin/optional-price SELECT; real-PG before/after and split-reader negative control, cash-only/missing-account/read-only assertions. |
| R3..R5 | portfolio_math exact worked/raw-rounding/half-even/zero/dust/wide-value tests and page null/fee-basis/allocation assertions. |
| R6..R7 | Freshness boundary/configured/late-clock/oldest/missing/inactive tests; full schema/guard/API strings/timestamps/401/no-store/isolation assertions. |
| R8..R10 | Strict bounded cursor codec and history route/service/API matrices; ties, lookahead, bigint, signed persisted values, foreign boundaries and continuation. Final critical gate 100%. |
| R11 | Populated 0007→0008→0007→head and base migration tests, index definition/readiness/validity/keys/data invariants, offline DDL and RUNBOOK recovery; old migrations unchanged. |
| R12..R14 | Real query hooks/infinite-chain tests, five awaited invalidations including replay, deferred identity cancellation/late A→B App regressions; no optimistic money. |
| R15..R17 | Exact API route allow-list and auth/markets/trade/account regressions; identical extended critical list; audits and separate inline threat review above. |
| R18..R19 | CI fake/console configuration, existing Playwright discovery; local isolated fixtures only. Dev rebuild, browser approval and remote push/merge/release gates stay with 05-08. |
| U1..U2 | Existing tokens/Inter and local typography overrides; 8+4/2-column/mobile layout classes, wrapping and semantic component assertions. Browser layout pending. |
| U3..U4 | Single responsive nav, separate Account and all five route families; heading focus, direct gated links and Back tests; complete semantic desktop/mobile fields and labelled scroll regions. Browser target execution pending. |
| U5..U7 | Financial display, allocation and freshness component/calculator tests cover signs/rounded zero/null/zero basis/cash denominator/time/incomplete precedence/liquidation. |
| U8..U9 | Initial/loading/error/empty/retained-refresh and three-page append/retry/end/sequential-refetch tests; exact retained copy and focus assertions. |
| U10 | Local class/semantic/focus/reduced-motion checks plus authored four-width CI targets, large values/timestamps, card-only keyboard scrolling and enlarged-rem checks. Real browser 200% zoom, safe-area and appearance approval remain pending 05-08. |
| CONTEXT None | Existing requirements/research/UI-SPEC followed; no invented context or scope decision. |

### Remaining Gates

- Independent code/security/UI phase review by the orchestrator.
- Actual ephemeral fake-price/console-email CI Playwright run and green remote CI before merge; no browser test was run locally and no real-email fallback was used.
- 05-08 explicit fresh dev rebuild choice and human real-price/browser UAT at all four widths, real 200% zoom, keyboard/safe-area/end focus and reduced motion.
- Scoped push/PR choice, separately approved merge and fresh release decision. No Phase 5 remote action is authorized or completed by this evidence.

## Final checkpoint and CI closeout — 2026-10-30

User approved the rebuilt development app (five healthy services, Alembic
0008), the supplied real-price/responsive browser checklist, and push-pr.
PR #25 targets develop. Independent code review is clean, including the
identity race, exact selector, expression and native-disabled focus fixes.
Final frontend suite: 264 passed; lint/types/format/build passed.
Backend source is unchanged since 573 passed/99.90% overall/100% critical.

Actual remote [CI run 41066672894](https://github.com/YokAI-open/Birja/actions/runs/41066672894)
passed all five jobs including ci-pass at 0595c89. Playwright executed:
10 passed, one production-only CSP test intentionally skipped, zero failed.
The full financial flow and all four responsive widths passed. Earlier
CI failures and focused correction evidence are retained in REVIEW and
REFRESH-FOCUS-FIX. Earlier pending entries describe their execution time;
this closeout supersedes them for the final status. Merge requires separate
approval; release/deployment is skipped.
