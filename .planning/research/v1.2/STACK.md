# Stack Research

**Domain:** Adding independent strategy portfolios to Birja's existing mixed-asset simulator
**Milestone:** v1.2 — Multiple Strategy Portfolios
**Researched:** 2026-11-14
**Confidence:** HIGH for stack suitability; MEDIUM for exact migration/cutover design pending phase research

## Recommendation

Keep the current stack and lockfiles. This milestone needs a new portfolio
ownership boundary across existing services, not another database, broker,
ORM, state manager or financial-math package. Ten active portfolios per user
fits relational queries and the existing React data layer. No new third-party
dependency is recommended by this research; no package was installed or changed.

Use PostgreSQL as the sole financial authority, SQLAlchemy transactions for
portfolio lifecycle and money mutations, Alembic for reviewed schema changes,
and TanStack Query keys containing the selected portfolio identity. Preserve
the existing Decimal/string-money contract and financial service rules.

## Recommended Stack

### Core Technologies

Versions below are repository pins, **not claims about the newest upstream
release or approvals to upgrade**. Exact Python/Node versions come from the
Dockerfiles; Python packages come from `backend/uv.lock`; frontend versions come
from `frontend/package-lock.json`. PostgreSQL version is documented in the
retained deployment runbook; its actual image reference is digest-pinned in
Compose. No production runtime was inspected.

| Technology | Repository version | Purpose | Why recommended |
|---|---|---|---|
| Python | 3.14.10, Wolfi package `3.14.10_git20261104-r0` | Exact-money services | Existing runtime and stdlib Decimal already support the required arithmetic |
| FastAPI / Pydantic | 0.162.0 / 2.14.1 | Authenticated portfolio APIs and validated payloads | Reuse current dependency-based auth, CSRF and response schemas |
| SQLAlchemy / asyncpg | 2.0.55 / 0.32.0 | Portfolio-owned queries and transactional writes | Current async PostgreSQL path supports explicit transactions and row locks |
| PostgreSQL | 18.7 documented; existing Chainguard digest | Ownership, cash, holdings, immutable records | Current constraints, indexes and transactions support the new relational boundary |
| Alembic | 1.20.1 | Schema evolution and migration verification | Already owns immutable reviewed revisions; keep schema and financial data backfill separately reviewable |
| React / React DOM | 19.3.1 | Portfolio overview and selected-portfolio screens | Existing component tree and accepted design system remain reusable |
| TanStack React Query | 5.105.0 | Server-state caching and invalidation | Native variable-based keys and cancellation fit portfolio switches/deletion |
| React Router | 8.5.1 | Explicit portfolio navigation | Existing routing dependency can carry portfolio identity without a new state package |
| Node / Vite / TypeScript | 24.22.3-r0 / 8.3.5 / 6.0.3 | Existing frontend build | No new build capability is required |

### Supporting Libraries and Infrastructure

| Existing component | Version/evidence | Use in this milestone |
|---|---|---|
| Python `decimal` | Python 3.14 stdlib | Per-portfolio grants, cash, basis and return inputs; explicit `ROUND_HALF_EVEN` at existing boundaries |
| Redis client / Redis service | Client 8.1.0; keep existing digest-pinned service | Existing auth, rate limits and disposable cache only; no authoritative portfolio registry or money |
| Radix / Tailwind | 1.8.1 / 4.3.3 | Existing accessible controls, confirmation dialog and responsive overview; implementation follows existing design-system contracts |
| Existing scheduler | Current dedicated container | Continue shared market-data collection; portfolio count must not multiply external quote polling |
| Existing restic/recovery tooling | Retained reviewed tooling; no change authorized here | Extend exact snapshot/restore coverage when schema changes are implemented |

### Development Tools

| Tool | Repository version | Required use |
|---|---|---|
| pytest / pytest-asyncio | 9.1.1 / 1.4.1 | Actual isolated PostgreSQL races, owner isolation, grants and migration parity |
| Vitest / React Testing Library | 5.0.5 / 16.3.3 | Portfolio switching, late responses, deletion and empty states |
| Playwright | 1.64.1 | Two-portfolio/two-user journeys and true selected-portfolio behavior |
| Existing recovery/TLS/strict scan gates | Current repository workflows | New ownership columns and lifecycle records must survive exact recovery and restricted-role execution |

## How to Use This Stack

These are implementation recommendations inferred from inspected code and the
official capabilities cited below, not an already implemented schema or an
approved phase plan.

1. **Persist portfolio identity explicitly.** Existing `Account.user_id` is
   unique; `Holding` is unique by user/instrument; trade idempotency and History
   are currently user-scoped. A collection screen alone cannot provide isolated
   strategies. Financial queries and durable records need the selected
   portfolio boundary while user ownership remains authenticated server-side.
2. **Serialize lifecycle changes in PostgreSQL.** Lock a stable owner row while
   counting/creating/deleting active portfolios, then create the portfolio and
   its once-only grant atomically. A row `CHECK` is not a safe aggregate-count
   enforcement mechanism. DB uniqueness/FKs and real concurrent tests must
   complement the service lock protocol. The exact lifecycle SQL/trigger design
   belongs in phase planning, including restricted-role behavior.
3. **Make deletion an explicit durable state.** Use an application-owned
   lifecycle field and predicates rather than an ORM soft-delete plugin.
   Preserve financial rows and identifiers; deny normal reads/new writes for
   deleted portfolios. Recheck active state inside the money transaction after
   locking. Whether retained deleted portfolios receive later event processing
   needs an explicit domain policy before implementation; deletion must never
   redirect cash/entitlements to another portfolio.
4. **Reuse exact portfolio math.** `portfolio_math.calculate_portfolio()` already
   accepts cash, starting cash and positions. Feed it one portfolio's inputs;
   preserve unavailable/incomplete valuation behavior in overview cards. Existing
   Decimal computations, JSON strings and frontend exact parsers avoid adding
   another numerical library.
5. **Scope both Query keys and local guards.** Query keys must distinguish owner
   and portfolio for holdings, previews, fills, History and valuation. The current
   portfolio hook also has per-QueryClient guard state, so adding a key alone is
   insufficient: portfolio changes must isolate/reset the corresponding guard
   lifecycle. Pass AbortSignal through existing fetch helpers and remove deleted
   portfolio queries so late responses cannot resurrect a removed strategy.
6. **Use bounded SQL for the overview.** At most ten active portfolios can be
   loaded in one bounded owner query with batched holdings/price joins; avoid
   concurrent queries sharing one AsyncSession. Public instrument prices may
   remain shared, while private financial snapshots are portfolio-scoped.

## Migration and Compatibility

Use the existing Alembic/SQLAlchemy toolchain. Plan an expand/backfill/validate/
enforce sequence and a precisely bounded writer transition rather than rewriting
old migrations. Preserve each user's current cash, original starting cash,
holding basis, trade IDs and immutable event evidence in their first portfolio.
This is not a new $10,000 grant. The new grant applies only to actually new
strategy portfolios. Existing login/account bootstrap and zero-active-portfolio
behavior must be redesigned together so login cannot silently recreate a
deleted strategy or issue another initial grant.

Alembic documents distinct approaches to data migrations and warns that data
downgrades need application-specific treatment. Thus retain the project's
schema/data separation and recovery-first review. A downgrade must not collapse
ten funded portfolios into one account, delete financial history, or invent
merge semantics. Exact downgrade/refusal and legacy rollback boundaries remain
phase-specific work. [Alembic data migration guidance](https://alembic.sqlalchemy.org/en/latest/cookbook.html#data-migrations-general-techniques)

## Installation

**No installation or lockfile change is required for the recommended stack.**
Future implementation should use the project's existing locked `uv`/npm and
owned Docker test environments. A later security/dependency issue would need
its own reviewed scope; this report grants no package or image upgrade approval.

## Alternatives Considered

| Recommended | Alternative | Assessment for this scope |
|---|---|---|
| Shared PostgreSQL tables with explicit portfolio ownership | Database/schema per portfolio | Adds routing, roles and restore complexity for ten strategies; no measured need |
| Existing owner checks plus DB constraints | New tenancy framework or ORM soft-delete plugin | Domain ownership and retained financial records need explicit rules; another implicit filter layer would not prove isolation |
| Existing SQL transactions and stable row locks | Redis lock or in-process mutex for funding/limit | Financial and lifecycle authority must survive process/cache failures and cross-worker races |
| Existing TanStack Query and route identity | Redux/Zustand or persisted browser-selected account authority | No new state-manager need established; selected UI state is never backend authorization |
| On-demand current valuation overview | Charting/time-series database or snapshot jobs | Owner chose cash/value/return overview and deferred historical charts |
| Existing dedicated scheduler | New task broker/worker per portfolio | No new job-transport requirement; shared data collection should remain shared |

## What NOT to Add

- Automatic `create_all()` or ORM schema mutation at startup; retain Alembic.
- A default “first portfolio” fallback that can send a stale request to another
  strategy, or login-triggered grants after all portfolios were deleted.
- A generic cascade delete of trades, dividend revisions, receipts or holdings
  just to hide a portfolio from its owner-facing screens.
- New packages based solely on the latest documentation version. Retrieved
  SQLAlchemy docs currently describe 2.0.57 while Birja locks 2.0.55; the cited
  transaction/session capabilities are existing 2.0-series features, not a
  recommendation to upgrade.
- Provider calls, activation flags, production changes or the bounded Phase 7
  campaign as part of this research. Six Phase 7 outcomes remain deferred.

## Version Compatibility and Open Validation

| Area | Assessment |
|---|---|
| Existing Python/PostgreSQL/asyncpg/SQLAlchemy pins | Locally evidenced configuration; reuse the previously tested runtime, then run affected/full gates after implementation |
| SQLAlchemy async overview | One session per concurrent task; prefer one batched statement over unsafe gather on a shared session |
| Alembic finance backfill | Suitable toolchain; exact immutable financial guards and migration authority require Phase 12+ research |
| Browser cache | Query supports keys/cancellation, but current guard state and all private hooks need an explicit portfolio audit |
| Fresh versus upgraded schemas | Must prove equivalent constraints, grants, starting-cash state and event ownership using actual PostgreSQL |
| Runtime security | This report performs no fresh scan and makes no new clean-image/security claim |
| Live stocks | Unchanged external prerequisites; stack suitability does not establish feed rights, freshness or live acceptance |

## Sources and Confidence

All external sources are official documentation, retrieved 2026-11-14. No
Context7 connector was available; no CLI/package download was attempted.

- **HIGH — local pins:** `backend/pyproject.toml`, `backend/uv.lock`,
  `frontend/package.json`, `frontend/package-lock.json`, `frontend/.nvmrc`,
  both Dockerfiles, Compose digest references, `deploy/RUNBOOK.md`.
- **HIGH — local integration evidence:** `backend/app/models/user.py`,
  `backend/app/models/trade.py`, `backend/app/services/accounts.py`,
  `backend/app/services/portfolio.py`, `backend/app/services/portfolio_math.py`,
  `frontend/src/api/portfolio.ts`, `frontend/src/hooks/usePortfolio.ts` and private
  query hooks. Findings describe inspected code, not a full implementation audit.
- [SQLAlchemy 2.0 transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
  — explicit transaction boundaries and context-managed commit/rollback.
- [SQLAlchemy async concurrent tasks](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncsession-with-concurrent-tasks)
  — AsyncSession is stateful and must not be shared across concurrent tasks.
- [PostgreSQL 18 locks](https://www.postgresql.org/docs/18/explicit-locking.html)
  — row locking and consistent lock acquisition; supports the proposed protocol,
  but does not itself validate Birja's future lifecycle implementation.
- [PostgreSQL 18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)
  — per-row CHECK limitations, foreign keys and uniqueness.
- [Alembic data migration techniques](https://alembic.sqlalchemy.org/en/latest/cookbook.html#data-migrations-general-techniques)
  — schema/data separation and application-specific backfill/downgrade design.
- [TanStack Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)
  — include changing query variables in independently cached keys.
- [TanStack Query cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)
  — AbortSignal must be consumed for underlying fetch cancellation.
- [Python 3.14 Decimal](https://docs.python.org/3.14/library/decimal.html)
  — decimal representation and explicit arithmetic/rounding controls.

**Remaining uncertainty:** Exact portfolio schema, retained-event processing for
deleted strategies, grant/idempotency enforcement, immutable-record backfill and
cutover compatibility need phase-specific decisions and proofs. No uncertainty
currently requires an additional dependency or service.
