---
phase: 5
slug: portfolio-and-history
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-10-29
---

# Phase5 — Validation Strategy

Planning coverage is complete; no implementation tests/services ran during planning. `nyquist_compliant:true` describes the planned feedback/producer coverage, not execution. `wave_0_complete:false` remains until new tests exist and run. No passed test or human approval is claimed.

Existing pytest/pytest-asyncio/httpx and isolated PostgreSQL/Redis from docker-compose.test.yml; existing Vitest/RTL/QueryClient; Playwright only ephemeral fake-price/console-email CI. Focused commands target<60s after services ready; measure and shard focused selections if necessary. Full suites are intentionally longer. Backend/frontend total coverage≥80%; critical paths100%, identical CI/CLAUDE list adds portfolio_math.py,portfolio.py,history.py. No install or new framework needed.

## Per-Task Feedback and Producers

Commands run independently from repo root. Run each RED command separately; behavioral failure is expected before Task2, not fixture failure. GREEN commands use && to preserve failure and repo-root subshells when changing directories. In-task RED sections are the logical Wave0 producers, avoiding a horizontal setup phase.

|Task|Wave|Requirements|Threat suffixes|Producer/dependency|Command or explicit checkpoint|Status|
|---|---|---|---|---|---|---|
|05-01-1|1|PORT-01..05|AUTH,MATH,UI|Creates portfolio math/service/API,frontend guard/page tests,e2e before01-2|`(cd backend && uv run pytest tests/test_portfolio_math.py tests/test_portfolio_service.py tests/test_portfolio_api.py -x -q)`<br>`(cd frontend && npm run test -- --run src/api/portfolio.test.ts src/pages/PortfolioPage.test.tsx)`; independently expected RED|planned|
|05-01-2|1|PORT-01..05|AUTH,MATH,UI|01-1+existing accounts/App|`(cd backend && uv run pytest tests/test_portfolio_math.py tests/test_portfolio_service.py tests/test_portfolio_api.py tests/test_accounts.py -x -q) && (cd frontend && npm run test -- --run src/api/portfolio.test.ts src/pages/PortfolioPage.test.tsx src/App.test.tsx)`|planned|
|05-02-1|2|PORT-01..03|UI,MATH|Creates financialDisplay.test;extends page tests before code;depends01|`cd frontend && npm run test -- --run src/lib/financialDisplay.test.ts src/pages/PortfolioPage.test.tsx && npm run typecheck`|planned|
|05-02-2|2|PORT-01..04|UI,MATH|Extends math/page tests before code;depends02-1|`(cd backend && uv run pytest tests/test_portfolio_math.py -x -q) && (cd frontend && npm run test -- --run src/lib/financialDisplay.test.ts src/pages/PortfolioPage.test.tsx)`|planned|
|05-03-1|3|PORT-01..05|TIME,UI|Extends page timer/state assertions before code;depends02|`cd frontend && npm run test -- --run src/pages/PortfolioPage.test.tsx src/components/FreshnessBadge.test.tsx src/lib/age.test.ts`|planned|
|05-03-2|3|PORT-01..05|MATH,AUTH,TIME|Creates snapshot test;extends service/API;real independent sessions/events|`cd backend && uv run pytest tests/test_portfolio_snapshot.py tests/test_portfolio_service.py tests/test_portfolio_api.py -x -q`|planned|
|05-04-1|4|HIST-01..02|AUTH,CURSOR,HISTORY|Creates history service/API/guard/page;extends allow-list/e2e;depends03|`(cd backend && uv run pytest tests/test_history_service.py tests/test_history_api.py -x -q)`<br>`(cd frontend && npm run test -- --run src/api/history.test.ts src/pages/HistoryPage.test.tsx)`; independently expected RED|planned|
|05-04-2|4|HIST-01..02|AUTH,CURSOR,HISTORY|04-1+existing accounts/App|`(cd backend && uv run pytest tests/test_history_service.py tests/test_history_api.py tests/test_accounts.py -x -q) && (cd frontend && npm run test -- --run src/api/history.test.ts src/pages/HistoryPage.test.tsx src/App.test.tsx)`|planned|
|05-05-1|5|HIST-01..02|CURSOR,HISTORY|Creates useHistory.test;extends page tests before code;depends04|`cd frontend && npm run test -- --run src/hooks/useHistory.test.tsx src/pages/HistoryPage.test.tsx`|planned|
|05-05-2|5|HIST-02|INDEX,CURSOR|Extends existing migration tests before schema;serial isolated DB;after04|`(cd backend && uv run pytest tests/test_migrations.py -x -q && uv run ruff check app/models/trade.py alembic/env.py alembic/versions/0008_trade_history_index.py tests/test_migrations.py)`|planned|
|05-06-1|6|All7|REFRESH|Creates useTrade.test before hook edit;depends03+05|`cd frontend && npm run test -- --run src/hooks/useTrade.test.tsx src/pages/TradePage.test.tsx`|planned|
|05-06-2|6|All7|CACHE|Creates privateQueries/auth mutation tests;extends client/App before code|`cd frontend && npm run test -- --run src/lib/privateQueries.test.ts src/hooks/useAuthMutations.test.tsx src/api/client.test.ts src/App.test.tsx`|planned|
|05-07-1|7|All7|AUTH,UI|Extends App/e2e before responsive shell;depends06|`cd frontend && npm run test -- --run src/App.test.tsx src/pages/PortfolioPage.test.tsx src/pages/HistoryPage.test.tsx && npm run typecheck`|planned|
|05-07-2|7|All7|TEST,SC,MATH|Existing/new suites;01-1/04-1 e2e extended|`(cd frontend && npm run e2e -- --list) && (cd backend && uv run pytest tests/test_portfolio_math.py tests/test_portfolio_service.py tests/test_portfolio_api.py tests/test_history_service.py tests/test_history_api.py -x -q)`; actual e2e only CI|planned|
|05-07-3|7|All7|All|All earlier test producers|`(cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest --cov=app --cov-fail-under=80 -q && uv run coverage report --include=app/services/otp.py,app/services/auth.py,app/services/accounts.py,app/services/ratelimit.py,app/services/email.py,app/core/security.py,app/core/deps.py,app/services/price_rules.py,app/services/prices.py,app/services/trade_math.py,app/services/trading.py,app/services/portfolio_math.py,app/services/portfolio.py,app/services/history.py --fail-under=100 && uv run pip-audit) && (cd frontend && npm run lint && npm run typecheck && npx prettier --check . && npm run test -- --coverage && npm run build && npm audit --audit-level=high)`; image/offline/review gates per07-3|planned|
|05-08-1|8|All7|TEST|07 concrete result|Explicit fresh dev-rebuild choice;after approval service health/alembic0008 only|human pending|
|05-08-2|8|All7|UI,TEST|Approved rebuild+07 evidence|Fresh human real-price/browser UAT at375/768/1024/1440,200%zoom/keyboard/reduced-motion|human pending|
|05-08-3|8|All7|RELEASE|UAT/reviews/local evidence/git summary|Scoped push/PR/not-yet;separate fresh release intent or skipped;green CI before separately approved merge|human pending|

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
- [ ] Actual RED/GREEN/full-suite/review evidence recorded.
- [ ] Fresh human UAT approved.
- [ ] CI/e2e green before merge, or honestly pending with not-yet.

**Approval:** Planning finalized; implementation, review outcomes, CI and human checks pending.
