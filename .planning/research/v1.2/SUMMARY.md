# Project Research Summary

**Project:** Birja
**Milestone:** v1.2 — Multiple Strategy Portfolios
**Domain:** Independent strategy portfolios in an existing mixed-asset simulator
**Researched:** 2026-11-14
**Confidence:** HIGH for existing coupling and stack fit; MEDIUM for the migration and terminal-lifecycle design pending phase proofs

## Executive Summary

Birja can support ten independently funded portfolios using its existing stack.
The recommended financial root is the existing PostgreSQL account identity:
preserve each original account and its actual balance, permit several portfolio
roots per authenticated user, and give only a genuinely new portfolio its own
once-only $10,000 grant. User/session identity remains independent of finances.
No new package, service, market feed or chart infrastructure is needed.

The work is a financial ownership transition, not just a selector. Cash,
holdings, fills, retry receipts, stock ownership journals, dividend entitlements,
payments, corrections, History and SQL authority currently assume one account
per user. Each must carry the same explicit portfolio target before a second
portfolio can be enabled. Reuse existing exact-money and truthful valuation
rules, and partition browser query keys, local guards and pending attempts by
both owner and portfolio. A stale or deleted target must fail without selecting
another strategy on the user's behalf.

Deletion retains financial records outside normal views and may remove the last
portfolio without ending login. The owner selected **end the experiment and
freeze at deletion** on 2026-11-14: stop future dividend/split activity, preserve
the retained records at closure, and neither fabricate liquidation nor transfer
money. This needs a coherent lifecycle boundary: instrument-global stock
reconciliation must not suspend other portfolios because a frozen holding no
longer advances. Phase 7's six deferred live
outcomes remain unverified in [DEFERRED.md](../../DEFERRED.md); this research does
not activate stocks, exercise providers or authorize deployment.

## Key Findings

### Recommended Stack

Keep current lockfiles and images. Repository pins include Python 3.14,
FastAPI 0.162.0, SQLAlchemy 2.0.55, Alembic 1.20.1 and TanStack Query 5.105.0;
these are inspected project versions, not recommendations to upgrade. PostgreSQL
is the financial authority, SQLAlchemy owns request transactions, Alembic owns
reviewed new revisions, and existing React components and Query own navigation
and server state. Details and pin qualifications are in [STACK.md](STACK.md).

**Core mechanisms:**

- PostgreSQL row locks serialize membership changes and the ten-active cap;
  constraints enforce row, owner and causal-lineage invariants. An unlocked
  count or cross-row `CHECK` cannot safely enforce the cap.
- Existing Decimal arithmetic and string money preserve exact starting grants,
  cash, basis and per-portfolio return inputs.
- Existing shared market collection remains shared. Portfolio count must not
  multiply external polling or grant a new live-data entitlement.
- Query keys, guards, cursor contexts and mutation closures must distinguish
  portfolios; cancellation alone does not make an old confirmation safe.

### Expected Features

The owner confirmed ten active named portfolios per user, $10,000 per new
portfolio, isolated financial activity, a cash/value/return overview, opening a
portfolio to trade, and confirmed deletion including holdings or the last
portfolio. Existing financial state becomes the first portfolio without a reset
or another grant. [FEATURES.md](FEATURES.md) separates those decisions from
proposed refinements such as rename, name validation and stable overview order.

**Must have:**

- Retry-safe creation and funding with an active-only limit enforced under
  actual concurrent requests; deletion frees a slot without reusing identities.
- Explicit portfolio context on trading, previews, receipts, History and detail
  links; owner and active-state checks on every supplied object identity.
- Per-portfolio stock/crypto cash, holdings, cost basis and financial events,
  including two strategies of the same user holding the same instrument.
- Overview statements using each stored starting-cash baseline, dated marks and
  explicit incomplete valuations; no missing holding is silently worth zero.
- Confirmed deletion, ordinary-access refusal afterward, valid signed-in empty
  state, and no automatic portfolio recreation on login or normal reads.
- Exact existing-data migration and exact active/deleted recovery, with unchanged
  restricted-role and financial immutability guarantees.

**Present for requirements approval:** rename and bounded nonblank names,
duplicate-active-name policy, migrated/default first-portfolio label, and
new-user onboarding. These are recommendations, not prior owner approvals.

**Outside this milestone:** historical charts, transfers, resetting an existing
portfolio, cloning, configurable deposits, sharing, restore/trash UI, new asset
classes, provider activation and production rollout. Do not add an account-wide
wealth total that pools independently granted strategies or hidden books.

### Architecture Approach

Retain `accounts.id` as the recommended portfolio root and `users`/sessions as
identity. Add lifecycle and naming metadata, relax one-account-per-user only
when all consumers are safe, and associate financial records with that root.
Keep market evidence global while portfolio effects remain separate.
The recommendation and precise source map are in
[ARCHITECTURE.md](ARCHITECTURE.md).

**Major boundaries:**

1. An owned-active-portfolio resolver binds each financial request to a stable
   target; browser selection never supplies authorization or fallback behavior.
2. Lifecycle creation/deletion serializes membership on a stable owner row;
   money operations lock and recheck their requested financial root using a
   compatible order with existing stock instrument gates and background jobs.
3. Holdings, immutable fills, retry payloads, stock journals, entitlements and
   payments have matching portfolio lineage enforced at the SQL boundary.
4. Profile/authentication works with zero or many portfolios. Legacy `/me` and
   financial endpoints need an explicit tested compatibility contract; an
   unspecified request cannot choose the first active portfolio.
5. Recovery/bootstrap recognizes each new schema revision and exact ownership,
   lifecycle, grants and function/trigger inventories. Older layouts retain
   their historical contracts rather than being silently relabelled.

### Critical Pitfalls

The full prevention and test matrix is in [PITFALLS.md](PITFALLS.md).

1. **User-scoped authority masquerading as portfolio isolation.** Update SQL
   definers, composite lineage and event uniqueness alongside Python queries;
   prove two portfolios of one user cannot share cash, receipts or entitlements.
2. **Extra grants or an eleventh active portfolio.** Creation plus grant is one
   retry-safe transaction. Serialize create/delete membership decisions; preserve
   original current and starting cash during migration and never fund on login.
3. **Wrong-target orders after switching or deletion.** Preserve immutable
   portfolio identity through preview, confirmation and uncertain retry; lifecycle
   checks run under locks, and late responses cannot become another strategy's
   data or actionable order.
4. **Deleted stocks breaking global ownership consistency.** Retained holdings,
   unit epochs, earned entitlements and corrections need the confirmed frozen
   lifecycle semantics. Do not cascade-delete causes, fabricate liquidation or
   redirect cash to a replacement portfolio.
5. **A migration or restore that preserves totals but swaps ownership.** Preserve
   exact row identities, financial payloads, grant state and lineage. Verify fresh
   versus upgraded restricted-TLS behavior and a cold exact restore; a matching
   aggregate total alone is insufficient.

## Implications for Roadmap

These are proposed runnable increments, not approved phases or executable plans.
Numbering continues at **12**. The owner must approve requirements and the actual
roadmap. The confirmed freeze-at-deletion policy is an input to those artifacts.

### Phase 12: Preserve Existing Investing Under Portfolio Authority

**Rationale:** Existing single-portfolio investing must remain usable while its
financial identity becomes explicit. Splitting schema, Python and SQL-authority
work into independently enabled halves would permit cross-strategy corruption.

**Delivers:** Existing users retain their real balances, baseline, holdings and
History in their first portfolio; the same crypto/stock journeys work through
portfolio-aware services and authority. Coordinate reviewed expansion/backfill,
all financial writers, grants and revision-specific recovery support. Additional
portfolio creation stays disabled until every dependent writer is scoped.

**Addresses:** Preservation, owner/portfolio identity, immutable-record
association, explicit legacy API compatibility and the zero/many financial model.
**Avoids:** User-only cash updates, partial lineage, extra migration grants,
old-app ambiguity and an unsupported recovery revision.

### Phase 13: Create, Compare and Trade Independent Strategies

**Rationale:** Enable multiple roots only on the proven financial boundary, and
deliver creation together with a complete investing journey rather than empty
portfolio cards or backend-only endpoints.

**Delivers:** Named independent portfolios, once-only $10,000 grants, ten-active
limit, create/open selection, cash/value/return overview, target-labelled
trading and private per-portfolio History. Two strategies can own the same asset
without shared amounts, basis, retries, dividends or split effects. Include
approved naming/rename refinements and portfolio-aware browser state.

**Addresses:** Independent strategy experiments and comparison using existing
exact valuation. **Avoids:** Double grants, race-created extra slots, shared
cache/attempt state and cross-portfolio event attribution.

### Phase 14: End Strategies Safely

**Rationale:** Deletion is an investing lifecycle change with real concurrent
effects. The owner has selected freezing the experiment and stopping future
dividend/split activity; its user-facing activation follows proven isolation.

**Delivers:** Confirmed deletion even with holdings, last-portfolio empty state,
stale/deleted-tab refusal, slot reuse through a new identity, and retained
financial records frozen at the confirmed terminal boundary. Race
deletion against trades, dividends, splits and corrections; other strategies
continue correctly. Extend exact recovery for the lifecycle state as it ships.

**Addresses:** Ending experiments without fake sales or transferring capital.
**Avoids:** Login-triggered regrant, record leakage, worker poisoning and
inconsistent treatment of already-earned dividends.

### Phase 15: Prove Exact Multi-Portfolio Recovery and Acceptance

**Rationale:** Final operator/user acceptance must qualify the complete retained
schema and journeys; it must not invent ownership repairs that earlier phases
needed to be safe.

**Delivers:** Full isolated PostgreSQL, browser, security and restricted-TLS
acceptance; exact recovery of active/deleted portfolios, same-symbol strategies,
zero-active users and original migrated data; safe post-restore retries and a
documented old-app rollback/refusal boundary. Required coverage/security/image
gates remain enforced. No live-provider or production operation is implied.

### Phase Ordering Rationale

- Identity, SQL authority and all financial writers form one coordinated safety
  boundary before multiple funded portfolios are exposed.
- Each phase retains runnable investing flows and its own migration/recovery
  compatibility. The final campaign integrates earlier proofs rather than
  postponing all testing or recovery support to the end.
- Deletion policy is settled before requirements and schema design even if its
  UI activates later. Do not postpone frozen-stock unit/entitlement consequences
  until Phase 14.
- The proposed four phases are a starting point. Split plan-sized tasks during
  phase planning; do not create layers-only phases or expand into charts/feeds.

### Research Flags

- **Phase 12: deeper research required.** Inventory every financial consumer;
  select immutable metadata backfill versus companion association; prove SQL
  authority, fresh/upgraded grants, compatible locks and old-client behavior.
- **Phase 13: targeted research required.** Validate create/retry identity,
  duplicate-name rules, query/guard isolation, same-user event uniqueness and
  overview batching. Existing UI and valuation patterns are otherwise reusable.
- **Phase 14: deeper research required.** Implement the selected deletion policy
  around cutoff/payable dates, global unit epochs and post-payment corrections.
- **Phase 15: targeted compatibility research.** Extend existing exact recovery
  and authority inventories; establish supported rollback/refusal boundaries.
  Existing test/CI tools need no new framework.

## Confidence Assessment

| Area | Confidence | Notes |
|---|---|---|
| Stack | HIGH | Existing pins and official documented mechanisms suffice; no new package need found |
| Confirmed features | HIGH | Owner explicitly selected funding, ten-active limit, deletion and simple overview |
| Naming/onboarding refinements | MEDIUM | Recommendations awaiting full requirements approval |
| Architecture | MEDIUM/HIGH | Current coupling directly inspected; account-root reuse is a design inference requiring phase proof |
| Pitfalls | HIGH identification; MEDIUM prevention design | Concrete user-keyed SQL/browser/recovery surfaces found; future implementation untested |
| Deleted-portfolio accounting | HIGH policy; MEDIUM design | Owner confirmed freeze at deletion; exact lifecycle/reconstruction proof remains |

**Overall confidence:** HIGH that the scope fits the current stack; MEDIUM that
the proposed migration/lifecycle approach is ready without further phase work.
This is source/documentation research, not a fresh passing runtime campaign.

### Gaps to Address

- **Frozen lifecycle mechanics:** preserve the confirmed closure snapshot and
  stop future economic effects. Specify lifecycle-aware handling of previously
  earned unpaid entitlements, later corrections and split-unit chronology without
  deleting prior records, fabricating liquidation or changing another portfolio.
- **Immutable association migration:** choose a narrow migrator path or companion
  mapping and prove original money/time/cause fields and protections unchanged.
- **Exact API and retry transition:** settle legacy endpoint compatibility and
  key scope. Either retain user-global keys with portfolio-mismatch conflict or
  prove a new scope; neither may replay or execute an order in another portfolio.
- **Authority/lock/recovery revisions:** enumerate every new function, constraint,
  grant and inventory before implementation. Old applications must refuse states
  they cannot represent instead of merging balances or deleting history.
- **Retained growth:** ten active portfolios does not bound lifetime audit rows.
  Reuse bounded requests/rate controls and backup-size safeguards; no automatic
  purge or lifetime creation cap is approved by this research.
- **External deferred work:** STOCK-01/02/03, DATA-01, MKT-01 and SAFE-01 remain
  unchecked in the v1.1 archive and durable register. Local portfolio proof does
  not establish provider rights, live-source freshness or production acceptance.

## Sources

All four reports distinguish inspected repository facts, official mechanism
documentation and Birja-specific design inferences. Official sources were checked
by the researchers on 2026-11-14; this synthesis aggregates those findings without
claiming a second independent source audit or runtime test. Their deletion-policy
fork records the question at research time; the subsequent explicit owner answer
above supersedes that uncertainty. It does not remove the need for phase-specific
frozen-lifecycle accounting and reconstruction proofs.

### Primary documentation and repository evidence

- [PostgreSQL 18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html)
  — composite ownership/uniqueness and cross-row CHECK limitations.
- [PostgreSQL 18 locking](https://www.postgresql.org/docs/18/explicit-locking.html)
  and [isolation](https://www.postgresql.org/docs/18/transaction-iso.html)
  — serialization boundaries, post-wait checks and consistent lock order.
- [PostgreSQL function security](https://www.postgresql.org/docs/18/sql-createfunction.html)
  — safe definer resolution and explicit EXECUTE privilege boundaries.
- [SQLAlchemy composite foreign keys](https://docs.sqlalchemy.org/en/20/core/constraints.html#defining-foreign-keys)
  and [async session concurrency](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncsession-with-concurrent-tasks)
  — lineage tuples and one session per concurrent task.
- [Alembic data migrations](https://alembic.sqlalchemy.org/en/latest/cookbook.html#data-migrations-general-techniques)
  — application-specific backfills and downgrade treatment.
- [Python Decimal](https://docs.python.org/3.14/library/decimal.html)
  — preserve existing exact-money arithmetic.
- [TanStack Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)
  and [cancellation](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)
  — dependency-complete cache identities and consumed AbortSignal.
- [OWASP object authorization](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/)
  and [IDOR prevention](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)
  — authorize every supplied portfolio/object identity.
- [W3C financial/data error prevention](https://www.w3.org/WAI/WCAG22/Understanding/error-prevention-legal-financial-data.html)
  and [alert dialogs](https://www.w3.org/WAI/ARIA/apg/patterns/alertdialog/)
  — named deletion confirmation, cancellation and accessible modal behavior.
- Existing models/services/migrations, frontend hooks, grant/bootstrap and exact
  recovery consumers are mapped with paths in [ARCHITECTURE.md](ARCHITECTURE.md)
  and [PITFALLS.md](PITFALLS.md). Pins are qualified in [STACK.md](STACK.md).
- [TradingView account-manager reference](https://www.tradingview.com/support/solutions/43000786138-what-is-the-account-manager/)
  supports account-context navigation only; it does not establish Birja's quota,
  funding or deletion policy.

---
*Research synthesis complete. Freeze-at-deletion policy confirmed. Ready for
requirements drafting; full requirements and roadmap approval remain pending.*
