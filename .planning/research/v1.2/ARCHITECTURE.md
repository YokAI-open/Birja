# Architecture Research

**Domain:** Multiple independently funded strategy portfolios in Birja's existing mixed-asset simulator
**Milestone:** v1.2 — Multiple Strategy Portfolios
**Researched:** 2026-11-14
**Confidence:** HIGH for current coupling and required boundaries; MEDIUM for the proposed migration/deleted-corporate-action design until phase-specific PostgreSQL proofs

## Recommendation

Use the existing PostgreSQL financial account as the portfolio aggregate: preserve
`accounts.id`, make one user own multiple account rows, and expose them to users
as portfolios. Add names and explicit lifecycle metadata rather than creating a
second independently mutable cash wallet. Keep `users`/`auth_sessions` as login
identity. Every financial operation receives an explicit portfolio identity and
proves that its authenticated user owns it.

This is a recommended internal design, not a requirement already implemented.
It retains existing account identities and balances while avoiding account-to-
portfolio cash synchronization. The table may remain named `accounts`; a physical
rename is unnecessary for the user-facing concept. Distinguish `user_id` and
`portfolio_id` in service signatures even if the latter references `accounts.id`.
Do not reinterpret existing `user_id` values as portfolio IDs.

The change is deeper than a portfolio selector. Financial ownership, SQL
authorities, immutable lineage and restore inventories are currently user-scoped.
They must move together before two portfolios can safely trade the same symbol.

## Standard Architecture

### System overview

```text
Authenticated user/session
        |
        v
Owned active portfolio resolver (explicit portfolio_id)
        |
        +-- lifecycle: create once / name / confirm deletion
        +-- crypto and stock trade services --> same portfolio cash lock
        +-- portfolio statement / private mixed History
        +-- overview of <=10 active portfolio statements
        |
        v
PostgreSQL: accounts as portfolio roots
        +-- holdings, trades, immutable receipts/journal, dividend lineage
        +-- retained lifecycle/deletion metadata and idempotent grant identity

Shared market catalogue/quotes/calendar/action observations remain global
        |
        v
Single scheduler --> portfolio-scoped corporate-action effects

Retained recovery tooling --> exact active AND deleted financial records
```

### Component responsibilities and existing integration map

| Component | Current evidence | v1.2 responsibility |
|---|---|---|
| Login identity | `backend/app/models/user.py:19`; `models/auth.py`; `core/deps.py:82` | Remain user/session scoped; login is valid with zero active portfolios |
| Financial aggregate | `models/user.py:33` has unique `Account.user_id`, cash and starting cash | Preserve account ID; allow multiple portfolio roots with immutable owner, name/lifecycle and independently stored starting baseline |
| Signup/profile | `services/accounts.py:13–39` creates the only account on first signup and inner-joins one cash row in `get_me` | Separate identity/profile from selected portfolio finances; never create another portfolio because normal reads find zero active rows |
| Holdings/fills | `models/trade.py:23–88` uses `(user_id,coin_id)` holding uniqueness and `(user_id,idempotency_key)` trade uniqueness | Add explicit financial root ownership, scoped holdings and bound order identity; preserve original monetary fields and recorded fills |
| Crypto execution | `services/trading.py:235–342` locks one user account, then holding | Lock and recheck the requested owned active portfolio; update only its cash/holding/fill |
| Stock execution | `services/stock_trading.py:242–410` replays before current market checks, then instrument gate/account and SQL final authority | Bind replay, financial reads, movement, fill facts and final authority to the same portfolio; retain existing quote/session/action safeguards |
| Stock ownership | `models/corporate_action.py:282–447`; `services/stock_ownership.py:150–215,361–455,532+` | Per-portfolio reconstruction and totals, retaining global instrument sequence/unit chronology |
| Splits/entitlements | `services/corporate_actions.py:553–669,798–892` identifies owners by user and iterates all instrument holdings | One source event; distinct effects and entitlement versions per portfolio, including lifecycle-aware retained history |
| Dividend cash/corrections | `models/dividend.py:38–169`; migration `0014_dividend_accounting.py:374–517` | Payment uniqueness, correction chain and affordability against the entitled portfolio, never another portfolio of the same user |
| History | `services/history.py:85+`; `services/event_history.py:142–193` | Portfolio filter before every union/seek, hydration join and original-reference lookup; preserve deterministic keyset ordering |
| Valuation | `services/portfolio.py:45–95`; `portfolio_math.py`; `stock_valuation.py` | Scoped financial positions with shared market evidence; overview reuses the same valuation rules and incomplete/dated states |
| Frontend request state | `hooks/useHolding.ts`, `useQuote.ts`, `useTrade.ts`, `usePortfolio.ts`, `useStockTrade.ts`, `useEventHistory.ts`; API modules | Include authenticated owner and portfolio in all financial query/mutation identities; switching/deletion must not relabel pending responses |
| Privilege/bootstrap | `deploy/db/bootstrap-roles.sql:14–17,49+,156–161,224–272`; `deploy/configure-db.sh` | Recognize new revisions and exact new authority/column grants on both fresh and upgraded restricted-TLS databases |
| Recovery | `deploy/backup-snapshot.py:83–140,380–425,501+`; `backup-manifest.sql`; `verify-restore.py` | Exact portfolio metadata, links, active/deleted rows, sequences, constraints/functions/triggers and grants; fail closed for unsupported revisions |

## Recommended Project Structure

Keep the existing router → service → SQLAlchemy model organization. Add one
portfolio lifecycle/ownership service and schemas/routes for the resource; extend
existing financial services rather than copying crypto/stock/accounting code
into parallel per-portfolio implementations. Existing task and retained deploy
directories remain their established boundaries. No new queue, datastore,
microservice, provider product or library is implied by this design.

## Architectural Patterns

### 1. A portfolio is a financial boundary, a user is an authorization boundary

Recommended aggregate invariants:

- Account/portfolio ID and `user_id` do not change after creation. A composite
  `(portfolio_id,user_id)` reference can enforce that denormalized owners match.
- Holdings are unique by `(portfolio_id,coin_id)`. Existing financial checks on
  cash, quantity, cent precision and basis remain unchanged.
- Trades, stock fill facts, journal movements, entitlements, payments and
  corrections carry the same portfolio lineage; existing composite owner/cause
  constraints must include that identity, not merely acquire a loose new FK.
- Initial grant and portfolio creation are one transaction with an idempotent
  creation identity. A retry cannot create another portfolio or another grant.
  Existing users retain their original `cash` AND `starting_cash`; migration
  must not substitute the current $10,000 default for either.
- Authentication remains valid after deleting the last portfolio. Signup or
  `/me` must not recreate one on every login or treat zero active portfolios as
  a missing user/account corruption condition.

Composite FKs enforce matching tuples, rather than separately valid references.
Use SQLAlchemy `ForeignKeyConstraint` to describe paired columns; preserve named
constraints so migration/recovery code can verify them.
[PostgreSQL constraints](https://www.postgresql.org/docs/18/ddl-constraints.html),
[SQLAlchemy composite foreign keys](https://docs.sqlalchemy.org/en/20/core/constraints.html#defining-foreign-keys).

### 2. Explicit request context and immutable order binding

Prefer additive resource routes such as
`/api/v1/portfolios/{portfolio_id}/...` for financial operations. The path is a
resource selector, not proof of ownership: the server resolves it with the
authenticated user. A browser-wide mutable “current portfolio” is not transaction
authority and must not silently redirect a stale tab's order.

Retain user-wide trade-key uniqueness initially and include portfolio identity in
`require_same_order`: reusing a key for another portfolio conflicts rather than
moving or replaying the order into it. This preserves existing cross-asset key
behavior and avoids needlessly rewriting legacy keys. Portfolio-scoped key
uniqueness is possible but would be a separate justified compatibility decision;
in either design the original request stores its target portfolio and retries
can never acquire a new one.

Check owner/lifecycle before returning an old receipt through normal portfolio
endpoints. Historical replay remains independent of *current market* availability,
but deletion does not permit an old tab to bypass the removed-portfolio boundary.
Define a deterministic unavailable/deleted result without executing again.

Changing `/me` from one non-null cash balance to ambiguous/null/many cash values
is a compatibility issue (`services/accounts.py:32`, `schemas/auth.py`,
`frontend/src/api/auth.ts`, `AccountPage.tsx` and trade pages). Keep identity and
selected finances separate in new clients. Phase planning must choose a tested
legacy-endpoint transition or version an actually breaking contract; never make
an unspecified old financial request operate on whichever portfolio is now first.

### 3. One lock protocol across lifecycle, trading and background effects

For creation/deletion membership changes, serialize on a stable user row, then
lock the affected portfolio if any. Count active portfolios and grant/insert in
that transaction. Creation and deletion both participate, so parallel requests
cannot exceed ten. A plain `CHECK(count(*) <= 10)` is not a valid PostgreSQL
cross-row invariant; use a reviewed serialized command/authority (and, if needed,
an explicit DB guard for all write paths).

For normal financial mutations, preserve stock instrument gate → portfolio cash
root → holdings in deterministic order. Crypto needs portfolio → its holding.
Recheck active lifecycle, spendable cash, ownership and the existing source-age/
eligibility rules after waits. Never acquire an instrument gate after locking a
portfolio that other stock operations lock in the reverse order.

A simple deletion can take user → portfolio and set a tombstone without taking
instrument/holding locks; all user-facing financial writers must take and
recheck that same portfolio row. It either follows a completed fill or wins
first and makes the later fill refuse. If deletion also mutates stock journals,
it no longer fits this protocol and needs a separately verified lock design.
Do not add synthetic liquidation merely to make deletion fit existing journals.
Current split code locks instrument holdings without account rows; its lifecycle
interaction must be reviewed rather than assumed covered by the trade lock.

PostgreSQL row locks serialize conflicting writers, and a waiting `FOR UPDATE`
under READ COMMITTED returns the updated version. Consistent lock order limits
deadlocks. An `AsyncSession` is transaction state, not a cross-task concurrency
primitive; overview batching should use set-based queries or separate sessions,
not concurrent operations on a shared session.
[PostgreSQL locking](https://www.postgresql.org/docs/18/explicit-locking.html),
[SQLAlchemy session concurrency](https://docs.sqlalchemy.org/en/20/orm/session_basics.html#is-the-session-thread-safe-is-asyncsession-safe-to-share-in-concurrent-tasks).

### 4. Deletion is a durable lifecycle transition, not row removal

Use a tombstone/time on the portfolio root, preserving account cash, holdings,
fills, receipts, entitlements and corrections. Normal list/detail/History/order
routes filter both owner and active lifecycle; internal audit/recovery tools must
still see retained rows. Repeated deletion should be safe and must not create
cash, sell assets, transfer money or reset another portfolio.

**Policy requiring explicit definition before implementation:** what happens to
future corporate actions and already-earned dividends after deletion? Current
stock consistency/reconstruction is instrument-global and user-keyed. Silently
excluding deleted holdings from one query while retaining their journal in
another can hold the instrument for everyone or assign the wrong unit epoch.

Recommended acceptance boundary: deletion closes new user activity and cannot
change any other portfolio; past lineage remains exact. The implementation must
explicitly specify whether retained deleted portfolios continue internal economic
roll-forward, or freeze at a terminal lifecycle cutoff with lifecycle-aware
split/entitlement reconstruction. Retain already-earned/revised payment lineage
in its original portfolio in either case. Both alternatives keep it hidden; do
not choose an unaudited mix or credit a replacement portfolio. This research does
not silently approve one of these economic policies.

### 5. Portfolio statements reuse truthful valuation

The overview must calculate each portfolio from its own stored starting cash,
cash and holdings, using shared allowed market marks. Preserve existing known-
value/incomplete and dated-market behavior; do not present missing positions as
zero or sum independent grants into one user's apparent investment profit.
At ten active portfolios, a bounded set-based statement query is sufficient;
there is no requirement for time-series snapshots, charts or a new cache.

All financial query keys, cursor contexts, idempotency payloads and mutation
closures include portfolio identity. Cancel/remove deleted-context queries and
ignore late results after selection changes. A fill response must retain its
original target label even if another portfolio is now open. The current
`["holding",symbol]`, global crypto quote/history keys and user-only portfolio/
stock/event keys are a concrete migration surface, not an adequate multi-
portfolio cache partition.

## Data Flow

1. **Create:** authenticated user → serialize membership → check active count
   and creation key → create root with one grant/baseline → commit → overview.
2. **Trade:** explicit portfolio → resolve owner/active → execute under the
   existing asset authority and portfolio lock → persist matched fill/holding/
   cash/journal atomically → receipt bound to original portfolio.
3. **Corporate action:** shared provider/source revision → instrument authority →
   reconstruct separate portfolio ownership at cutoff → once-only portfolio
   effects with matching entitlement/payment/correction lineage.
4. **Delete:** confirmed owned portfolio → serialized lifecycle transition →
   normal reads/mutations refuse it → retain all financial data and apply the
   explicitly selected post-deletion accounting policy.
5. **Recover:** archive current schema and all active/deleted portfolio records →
   restore exact rows/identities/authorities → replay without new grants,
   duplicate fills, dividend payments or resurrection.

## Migration, Privilege and Recovery Boundaries

### Existing users: metadata association, never financial reset

Preserve existing `accounts.id`, owner, current/starting cash, created times,
holdings/bases and immutable fill IDs/values. Associate all old financial records
with the original root. Add new association columns/constraints as an expansion,
backfill with a narrowly scoped reviewed migration, verify completeness and only
then require them and remove one-account/user uniqueness. New schema and data
backfills should be distinct migration steps per `CLAUDE.md`; existing 0001–0014
remain immutable.

Append-only stock triggers currently reject UPDATE/DELETE, including a naive
new-column backfill (`0013_stock_execution.py:379–386`,
`0014_dividend_accounting.py:92–107,991+`). Phase research must choose and prove a
finite migrator-only metadata association path, or immutable companion mappings.
Neither path may allow app/scheduler financial rewrites, leave protection off, or
change original monetary/price/time/cause fields. Additive ownership metadata
is not permission to regenerate historical fills or economic timestamps.

Alembic explicitly treats data migrations as application-specific; separate
schema expansion, backfill and final constraints rather than trusting
autogeneration to understand lineage or downgrade semantics.
[Alembic data migration guidance](https://alembic.sqlalchemy.org/en/latest/cookbook.html#data-migrations-general-techniques).

Old applications assume exactly one account per user. Do not enable creation of
second portfolios while an old backend/scheduler can write that schema. Local
upgrade proof must cover populated 0014 and the actual production-origin 0008
upgrade chain; production rollout itself remains separately approved. A
downgrade that cannot represent multiple portfolios must refuse rather than
merge balances/drop retained histories. Recovery to a compatible current image
is safer than claiming old-image rollback after new portfolio activity.

### SQL authority and role parity

Dividend SQL currently locks/updates `accounts WHERE user_id=uid` and enforces
payment uniqueness by `(event_id,user_id)`. With multiple rows this could update
every portfolio or reject a valid second entitlement. Extend the *new revision's*
functions and composite lineage to derive/validate portfolio ownership; enforce
the same target for payment, correction affordability and `cash_after`.

Update exact bootstrap inventories, definer ownership/search paths, execute
grants, immutable triggers and scheduler column reads as a coordinated authority
change. Keep scheduler cash mutation behind its reviewed dividend definer;
do not grant broad account UPDATE to solve a new column permission failure.
Prove fresh and upgraded app/scheduler/migrator/operator roles produce the same
allowed/denied operations over verified TLS.

### Exact recovery cannot be deferred until release

`backup-snapshot.py` currently accepts revisions 0007–0014 only, enumerates exact
columns and identity sequences, and validates schema/function/trigger hashes.
The role bootstrap also rejects unknown revisions. New lifecycle columns,
ownership links, grant/create idempotency records and new SQL authority must get
revision-specific producer/verifier inventories. Do not “fix” this by relaxing
hash/table/column allowlists or making historical revision contracts mutable.

Every schema-expansion phase needs compatible recovery support before its
result can be a usable deployment candidate. Final proof includes two active
portfolios with the same symbol, a deleted portfolio retaining holdings and
lineage, a user with zero active portfolios, post-migration original balances,
and retries after restore. Test malformed cross-portfolio lineage and unsupported
old tooling fail closed. The ten-*active* limit does not bound archived storage;
retained deletion history must be included in the existing bounded backup-size
checks and lightweight create/delete request limits, without inventing a purge.

## Recommended Ordering for the Roadmap

These are dependency groups, not approved plans or a fixed phase count:

1. **Phase 12 foundation:** portfolio identity/lifecycle and exact original-owner
   migration, grants/recovery compatibility and zero-active authentication.
   Keep extra portfolio creation disabled until every writer is scoped.
2. **Financial isolation:** crypto/stock execution and replay, holdings/journal,
   dividend/split/correction authority and lifecycle concurrency; test two
   strategies holding the same instrument under restricted roles.
3. **Portfolio journeys:** create/name/select/overview/confirmed delete, scoped
   browser cache/history/receipt behavior and empty/deleted-tab handling, on top
   of the proven financial boundary.
4. **Integrated acceptance:** exact active/deleted recovery and retained-tool
   compatibility, migration/rollback refusal, full database/browser/security
   proof. No chart, transfers or new market-data activation is required.

Do not ship a phase that enables multiple accounts while leaving existing
user-only cash UPDATEs, `scalar_one()` assumptions or user-only corporate-action
uniqueness active. Small deployable steps may use a lifecycle gate to keep the
new capability unavailable until its dependent writers are correct.

## Scaling and Anti-Patterns

For the existing friends-scale app, keep the monolith and shared market fetch.
Batch up to ten portfolio statements, index actual owner/lifecycle and portfolio/
instrument/history lookups, and measure before adding caches. Market polling
must not multiply by portfolios. Existing stock instrument gates intentionally
serialize that instrument across strategies; remove only with a separate proof.

Avoid one database/schema per portfolio, storing selected authority only in a
cookie, interpreting user ID as portfolio ID, enforcing ten with an unlocked
count, allocating a new grant during migration/login, hiding only the overview,
or cascading deletion into financial rows. Do not alter original Phase 7 evidence
or infer live provider suitability from multi-portfolio synthetic tests.

## Confidence and Open Questions

| Area | Confidence | Remaining phase-specific work |
|---|---|---|
| User-to-financial coupling | HIGH | All named current paths inspected; implementation must inventory every SQL/query consumer |
| Existing-account-as-portfolio root | MEDIUM/HIGH | Recommended smallest aggregate; validate against grant/backfill/legacy API constraints |
| Concurrency protocol | MEDIUM | Real PostgreSQL delete/trade/split/dividend and create-limit race proofs |
| Historical metadata backfill | MEDIUM | Select constrained migrator path vs companion associations while retaining immutable economics |
| Post-deletion corporate actions | OPEN POLICY | Choose coherent hidden roll-forward or terminal-cutoff semantics before code |
| Role/recovery changes | HIGH need, MEDIUM design | Exact new revision inventories and fresh/upgraded/cold-restore proofs |
| Live stock readiness | UNVERIFIED | Unchanged deferred Phase 7 requirements; outside v1.2 acceptance scope |

## Sources

Official documentation checked 2026-11-14; pages document PostgreSQL 18 and
SQLAlchemy 2.0 behavior, not an instruction to upgrade dependencies:

- [PostgreSQL 18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)
- [PostgreSQL 18 locking](https://www.postgresql.org/docs/18/explicit-locking.html)
- [SQLAlchemy 2.0 composite foreign keys](https://docs.sqlalchemy.org/en/20/core/constraints.html#defining-foreign-keys)
- [SQLAlchemy session basics/concurrency](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [Alembic cookbook: data migrations](https://alembic.sqlalchemy.org/en/latest/cookbook.html#data-migrations-general-techniques)

The code integration map above is direct repository evidence. Concrete design
recommendations and ordering are inferences from that evidence; they are not
claims that an external source specifies Birja's product policies.
