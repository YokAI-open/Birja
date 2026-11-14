# Pitfalls Research: Multiple Strategy Portfolios

**Domain:** Adding independently funded, deletable portfolios to Birja's existing mixed-asset simulator
**Researched:** 2026-11-14
**Confidence:** HIGH for observed code and documented database/security mechanisms; MEDIUM for proposed lifecycle design pending requirements approval

## Scope and evidence boundary

Confirmed scope is up to ten active named portfolios per user, one $10,000 grant
per new portfolio, isolated finances and History, a cash/value/return overview,
and confirmed deletion including holdings or the last portfolio. Existing actual
balances and history become the first portfolio without a new grant. Retained
records remain outside normal portfolio screens. This is research, not a claim
that these changes exist or that production/provider access was exercised.

Phase 7's six deferred requirements remain unverified in
[DEFERRED.md](../../DEFERRED.md). Existing stock admission/rights/calendar/status
gates remain applicable to every portfolio; creating a strategy does not activate
stocks. New phases start at 12; the phase topics below are recommendations, not
an approved numbered roadmap.

## Critical Pitfalls

### 1. Adding a portfolio selector while financial authority still means user

**What goes wrong:** Two strategies display separate names but share cash,
holdings, fill receipts, dividend cash or History. Checking only the signed-in
user prevents cross-user leaks while still allowing cross-strategy corruption.

**Why it happens:** `Account.user_id` is unique in `backend/app/models/user.py`;
`Holding` is unique on `(user_id,coin_id)` in `models/trade.py`. Existing route
handlers pass `user.id` directly to portfolio, trading and History services.
`services/portfolio.py:get_portfolio` joins holdings to accounts by user ID.

**How to avoid:** Establish a stable financial portfolio identity and an explicit
owner-plus-portfolio authorization boundary before exposing a selector. Carry
that identity through every read/write and stored causal reference. Do not
reinterpret a portfolio ID as an authentication user ID or duplicate users for
strategies. Enforce owner/portfolio/asset lineage with suitable keys and FKs.
OWASP requires object authorization even when the caller supplies an ID; knowing
or hiding an identifier is not permission. [OWASP IDOR guidance](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)

**Warning signs / required assertions:** Buy the same asset in two portfolios
with different costs; one portfolio's buy/sell must leave the other unchanged.
User B must fail all reads, mutations, receipt/detail and deletion requests for
user A's portfolio. Test direct API IDs, not only navigation.

**Phase to address:** Ownership/schema foundation, then every financial/API integration.

### 2. Regranting money on login, retry, deletion or migration

**What goes wrong:** A retried create grants twice; migration resets actual cash
to $10,000; a user who deletes their last portfolio gets a replacement on next
login. Alternatively, a lost create response leaves an invisible funded strategy
and a retry consumes another slot.

**Why it happens:** `services/accounts.py:get_or_create_user` currently creates
the single financial account only when its unique email insert wins. `get_me`
expects exactly one account. Multiplicity and zero-active portfolios invalidate
those assumptions even if authentication itself is unchanged.

**How to avoid:** Separate user authentication from explicit portfolio creation.
Make create and its initial grant one atomic, retry-safe operation; decide the
create-request identity during phase design. Preserve stored `cash`,
`starting_cash`, holdings/basis, trade IDs and original timestamps when assigning
legacy rows. Zero active portfolios is a valid state and cannot trigger an
implicit grant. Deleted IDs and original create identities must never be reused
to fund an existing experiment again.

**Warning signs / required assertions:** Repeat the same create request, race
two copies, lose its response, log in repeatedly, migrate twice where supported,
and delete-all then log in. Show one grant per created identity and no mutation
of migrated financial amounts. A genuinely new portfolio after deletion is
allowed by the owner-approved policy; it is not a reset of the deleted ID.

**Phase to address:** Lifecycle creation and legacy migration, before multi-portfolio UI.

### 3. Counting ten portfolios without a serialization boundary

**What goes wrong:** Two requests both observe nine active portfolios and create
an eleventh. Counting deleted rows prevents an approved replacement; counting
only in the browser is bypassable.

**Why it happens:** An ordinary count followed by insert is not an atomic limit.
PostgreSQL Read Committed gives a statement snapshot rather than serializing
the whole transaction. A `CHECK` constraint is unsuitable for counting other
rows. [PostgreSQL isolation](https://www.postgresql.org/docs/18/transaction-iso.html),
[constraint restrictions](https://www.postgresql.org/docs/18/ddl-constraints.html)

**How to avoid:** Serialize active create/delete lifecycle decisions on a stable
owner row or an equivalently enforced transaction boundary, then count active
portfolios and insert/grant before releasing it. Keep ordinary per-portfolio
financial locks scoped appropriately. Use DB constraints for row/key invariants;
do not rely on a custom cross-row `CHECK`.

**Warning signs / required assertions:** With nine active rows, simultaneous
creates result in at most ten. Race create against delete and duplicate delete;
count and grant outcomes must match committed active rows. A deleted portfolio
frees a slot without erasing retained history.

**Phase to address:** Lifecycle foundation and real PostgreSQL concurrency tests.

### 4. Deletion racing an in-flight trade or silently choosing another portfolio

**What goes wrong:** A tab previews in A, another tab deletes A, then confirmation
executes in B because B is now selected/default. An endpoint checks A as active
before waiting for a lock and writes after deletion committed.

**Why it happens:** Existing crypto execution locks the account then the holding;
stock execution first takes an instrument advisory gate, then the account.
The new lifecycle rule must participate in these transactions, not only routing.

**How to avoid:** Bind request, preview, receipt and idempotency identity to the
explicit portfolio. Recheck owner/activity under the relevant financial lock
before new writes. Deletion and execution must have a defined committed order:
either the completed trade is retained before deletion, or the new trade is
refused. Never move a failed/deleted-target request to another portfolio. Design
one compatible lock order across lifecycle, stock gate, cash, holdings and jobs;
PostgreSQL recommends consistent acquisition order to avoid deadlocks.
[PostgreSQL locking](https://www.postgresql.org/docs/18/explicit-locking.html)

**Warning signs / required assertions:** Use barriers to hold a trade behind a
deletion and vice versa; assert no fill after the chosen deletion boundary, no
cross-portfolio effects, no negative cash and a clear stale/deleted-target error.
Retain price/eligibility checks after blocking waits. Do not add a general retry
loop that can obscure an uncertain fill or reorder confirmed lifecycle intent.

**Phase to address:** Transactional deletion plus trading integration.

### 5. Keeping old idempotency rules that forget the portfolio

**What goes wrong:** Reusing an order key in B returns A's receipt, or executes a
second order after a switch/deletion because the retry identity changed. An
original reference opens another strategy's event.

**Why it happens:** `services/trade_idempotency.py` looks up `(user_id,key)` and
`require_same_order` checks instrument/side/kind/value, with no portfolio field.
`models/trade.py` enforces the same user-global unique key. Stock replay also
joins immutable facts with `user_id`; History source unions use that scope.

**How to avoid:** Make the portfolio part of immutable economic request identity
and the receipt's lineage. Choose a coherent key policy: portfolio-scoped keys,
or retained user-global keys with a different-portfolio conflict. Either must
preserve old original receipts and never treat A's key as B's valid request.
Public activity/deletion authorization must still apply; internal recovery
replay is not permission to expose deleted records through normal endpoints.

**Warning signs / required assertions:** Same key and same payload across A/B;
same key with changed portfolio after a timeout; replay after close/deletion;
cross-portfolio original-reference fetch and cursor reuse. Assert no duplicate
cash/holding effects, no receipt leakage, and no dependency on today's quote for
authorized replay of an existing fill.

**Phase to address:** Trading/History contract migration and retry verification.

### 6. Treating deletion as a UI filter while global stock accounting continues

**What goes wrong:** Hard-deleting holdings or movements breaks audit lineage.
Skipping a closed holding in one job but retaining its journal in another causes
an instrument-wide ownership mismatch and can suspend other users/strategies.
An earned dividend is redirected to a replacement portfolio or is guessed away.

**Why it happens:** `stock_ownership.py:assert_ownership_consistent` reconstructs
totals by user across the instrument and compares them with all holdings.
`corporate_actions.py:apply_due_splits` iterates all instrument holders and moves
a shared unit epoch. Entitlement reconstruction combines historical movements,
prior entitlements and present holders. `0014_dividend_accounting.py` selects
and credits an account by entitlement user ID inside a SQL definer.

**How to avoid:** Resolve the deleted-portfolio policy explicitly before plans
promise acceptance. Two possible policies are under owner discussion: freeze
the experiment at deletion with no future dividend/split processing, or retain
hidden bookkeeping. Neither permits liquidating at a guessed price, moving
funds, deleting causes, or exposing retained rows in normal views. If frozen,
persist an auditable closure boundary and make journal/unit-epoch reconstruction
lifecycle-aware so later splits of active owners do not require fictional closed
movements. If hidden processing continues, scope it strictly to the same closed
identity, with no resurrection, transfer or additional starting grant.

**Warning signs / required assertions:** A and B own the same stock, A deletes,
then a split, earned payable dividend, changed dividend, negative correction and
worker replay occur. B remains correct/available; A follows the approved closed
lifecycle; immutable lineage remains reconstructable. Delete the last portfolio
and repeat jobs/recovery. Test once-only entitlements separately for two active
portfolios of the same user.

**Phase to address:** Lifecycle policy before schema finalization; corporate-action integration before feature completion.

### 7. Updating Python while leaving SQL authority and grants user-global

**What goes wrong:** UI/service reads appear isolated while a definer credits
the wrong account, rejects multiple rows, or allows forged portfolio attribution.
A permission shortcut gives the app/scheduler direct ledger mutation rights.

**Why it happens:** `0014_dividend_accounting.py:APPLY` derives user ownership,
locks `accounts WHERE user_id=uid`, applies cash there and authenticates exact
payment/entitlement/decision lineage. Models and migrations contain composite
owner/event/revision FKs and immutable triggers. Merely adding a Python argument
does not change that authority contract.

**How to avoid:** Audit every SQL function, FK, unique constraint, immutable
trigger and restricted-role grant affected by the chosen financial identity.
Write new migrations; do not edit merged ones. Keep definer ownership,
search-path and narrow EXECUTE permissions explicit. PostgreSQL warns that new
functions default to PUBLIC EXECUTE and that writable schemas can subvert a
definer's object resolution. [Definer security](https://www.postgresql.org/docs/18/sql-createfunction.html)

**Warning signs / required assertions:** Execute the real service through app,
scheduler and migrator roles over verified TLS on fresh and upgraded schemas.
Forge a mismatched portfolio/user/cause tuple and prove refusal with no writes.
Prove direct mutation and unauthorized EXECUTE remain denied; grant parity and
financial outcomes must agree, not merely schema creation.

**Phase to address:** Financial-authority migration and integration proof.

### 8. Safe schema migration but unsafe compatibility or rollback

**What goes wrong:** Adding `portfolio_id` works on empty tables but leaves
legacy rows unowned, invalidates immutable fingerprints, or allows an old app to
choose arbitrary rows once accounts are no longer unique per user. Downgrade
silently combines portfolios and loses financial provenance.

**How to avoid:** Map every existing financial row to its original account in a
reviewed, exact backfill. Preserve authentication IDs and financial payloads;
validate FKs and required columns only after backfill. Explicitly define the
compatibility boundary for the old single-account app, including safe refusal
once multiple portfolios exist. Do not claim an automatic lossless downgrade
that would need to merge distinct balances/history or rewrite immutable rows.

**Warning signs / required assertions:** Start with populated mixed-asset
schema0014, old grants and identities; compare pre/post amounts, fills, sequence
states, receipts and entitlements exactly. Test interrupted/replayed migration
and the approved rollback/refusal boundary. Fresh bootstrap alone is insufficient.

**Phase to address:** Foundation migration; end-to-end recovery/cutover acceptance.

### 9. Isolated API data but shared browser cache, preview or late response

**What goes wrong:** Switching A to B shows A's value, pending confirmation,
receipt or History page under B's heading. A slow response for A overwrites B.
Deleting A leaves its data reachable through browser Back or another tab.

**Why it happens:** `usePortfolio.ts` caches `["portfolio",email]` and guards
local freshness maps by email. `useEventHistory.ts` holds an email/epoch/seen
guard. `useStockTrade.ts` has email-scoped trade state and symbol contexts.
Their current session-isolation protections do not distinguish two portfolios
within the same login.

**How to avoid:** Add portfolio identity to all dependent query keys, guards,
cursors, drafts, receipts and mutation inputs. Clear or detach incompatible
previews on switch/deletion, reject late responses by owner/portfolio/lifecycle
identity, and preserve existing sign-out/account-switch protection. TanStack
requires changing query dependencies to be represented in their cache keys.
[Query key guidance](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)
Market quotes can remain globally shared where independent of finances; cash,
holdings and order state cannot.

**Warning signs / required assertions:** Slow A response after switch to B;
switch during preview/repricing/uncertain fill; delete current A in another tab;
reuse History cursor/reference; sign out then another user signs in. Nothing
from A may become an actionable B order or an apparent B financial result.

**Phase to address:** Portfolio-aware client/API contracts and browser UAT.

### 10. Backing up the new schema without proving exact portfolio recovery

**What goes wrong:** Restores lose portfolio ownership/deletion boundaries,
merge grants, resurrect deleted rows in normal views, or accept changed SQL
authority. Legacy bundles are relabelled as supporting the new schema.

**Why it happens:** `deploy/backup-snapshot.py` uses revision-specific explicit
columns, identity allowlists and pinned SQL-authority declarations.
`backup-manifest.sql` and `verify-restore.py` authenticate known layouts and
retained tooling. New tables/columns/functions need a new reviewed contract.

**How to avoid:** Extend current recovery inventories and exact authority checks
for portfolio ownership, lifecycle, financial lineage and identities, retaining
older revision behavior. Use one checksum-pinned archive for final recovery/
roles/TLS/rollback qualification. Restore deleted and active portfolios together;
keep recovery quarantine and activation denials intact.

**Warning signs / required assertions:** Exact restored rows/constraints/indexes/
sequences/grants match; two strategies retain distinct cash/basis/entitlements;
deleted rows stay hidden; replay cannot repeat creation grants, fills or dividend
effects. A financial total alone cannot detect swapped portfolio ownership.

**Phase to address:** Recovery tooling integration before release acceptance.

## Technical Debt Patterns

| Shortcut | Immediate appeal | Long-term failure | Acceptable? |
|---|---|---|---|
| Treat `user_id` as whichever portfolio is selected | Fewer query changes | Authentication and financial identity become ambiguous | Never |
| Cascade-delete records or zero holdings on deletion | Easy UI disappearance | Destroys causes, split consistency and exact recovery | Never |
| Permit unscoped legacy writes to the first active portfolio | Old clients keep working | Stale requests silently target another strategy | Only an explicitly bounded compatibility design that cannot misroute |
| Reset all accounts to a new $10k baseline in backfill | Simple seed | Erases gains/losses and grants money again | Never |
| Add a database/service/plugin per portfolio | Isolation by duplication | Excess deployment, authorization and recovery work for ten bounded rows | No evidence of need |
| Change historical migrations/recovery fixtures in place | Faster green test | Old archive compatibility and provenance become unverifiable | Never |

## Integration and Performance Gotchas

| Area | Mistake | Required approach |
|---|---|---|
| Prices/provider jobs | Poll feeds once per portfolio | Reuse existing instrument collection; portfolio multiplicity does not increase feed polling |
| Overview | Ten sequential detail requests or fake zero for incomplete marks | Bounded owner-scoped aggregation/batching; reuse current valuation rules and explicit unavailable results |
| Financial totals | One all-portfolio return based on $10k | Compute each portfolio against its own stored starting cash; no cross-strategy cash or grant pooling |
| Retained history | Assume ten active means ten lifetime rows | Preserve exact audit data and measure retained growth; reuse bounded requests/rate controls, no invented retention cap or automatic purge |
| Names | Use display names as persistent foreign keys | Stable IDs for requests/causes; bounded validated names are display metadata |
| Signup/current-user response | Continue joining exactly one account | Auth identity and zero/many-portfolio responses need explicit semantics |

## Security and UX Pitfalls

| Pitfall | User impact | Better boundary |
|---|---|---|
| Delete dialog omits portfolio identity | Wrong strategy deleted | Confirm the specific named target and its permanent removal from normal views |
| Broad `DELETE` or `UPDATE` by supplied ID alone | Another owner's portfolio affected | Owner plus immutable portfolio target; activity checked transactionally |
| Last deletion automatically creates a default | Unexpected new money and unwanted portfolio | Valid empty state with explicit create action |
| Retained deleted details accessible via old URL/reference | Deletion promise broken | Apply lifecycle scope to detail, History, preview, receipt and original-reference APIs |
| UI says every stock strategy is live | Confuses known deferred capability | Keep existing stock activation/status restrictions and truthful unavailable marks |

## "Looks Done But Isn't" Checklist

- [ ] **Creation:** retry/cancel/lost-response/concurrent creation cannot double-grant or exceed ten active rows.
- [ ] **Migration:** populated legacy cash, basis, history, entitlements and identity states remain exact in the first portfolio.
- [ ] **Isolation:** same asset, same order key and same user in two portfolios still produce independent financial outcomes.
- [ ] **Deletion:** holdings and last-portfolio deletion work with no liquidation, transfer, regrant or normal-screen record leakage.
- [ ] **Closed stock lifecycle:** delete then split/dividend/correction/replay leaves other portfolios correct and preserves lineage under the approved policy.
- [ ] **Concurrency:** lifecycle, crypto, stock, payout and split interleavings have a documented compatible lock order and tested refusal behavior.
- [ ] **Browser:** cache/guard/draft/receipt/cursor isolation survives switch, delayed response, deletion, Back and sign-out.
- [ ] **Authority:** real restricted TLS roles have fresh/upgraded parity and reject forged ownership/lineage or direct ledger mutations.
- [ ] **Recovery:** one exact archive restores active/deleted identities, grant state and once-only effects; old layouts retain supported boundaries.
- [ ] **Scope honesty:** Phase 7 deferred requirements remain unchecked and stock activation is not inferred from portfolio work.

## Pitfall-to-Phase Mapping

| Proposed phase topic | Pitfalls to prevent | Observable verification |
|---|---|---|
| Portfolio identity, migration and lifecycle foundation | 1–4, 8 | Legacy amounts exact; ten-active race; zero-active login; own/delete authorization |
| Portfolio financial and corporate-action integration | 1, 4–7 | Independent same-stock strategies, scoped retries, deleted-target races, correct closed lifecycle |
| Overview, selection and private History UI | 1, 5, 9 | Same exact detail/overview values; stale response and deleted-tab refusal; no cross-portfolio record leak |
| Exact recovery and complete journeys | 7, 8, 10 | Fresh/upgraded restricted TLS parity; exact archive roundtrip; once-only grant/fill/payment replay |

Do not postpone ownership or deleted-stock lifecycle until a final test phase:
they determine schema and financial contracts. The final phase verifies those
earlier decisions rather than inventing data repair to make them pass.

## Open Policy / Phase-Specific Research

The owner has been asked to select frozen-at-deletion versus hidden continuing
corporate-action bookkeeping. Research cannot decide this product policy. Plans
must express what happens to earned unpaid dividends and already-paid correction
lineage, including deletion around cutoff/payable dates. Either choice must keep
other active portfolios independent and retained records auditable. No guessed
sale, cash-in-lieu, transfer, restoration feature or retention purge is authorized.

Exact immutable-row backfill, financial identifier choice, compatible lock order,
SQL signatures and safe old-app refusal need phase-specific design and real
PostgreSQL proof. The established stack is adequate; no new package is required
by the risks identified here.

## Sources and Confidence

**Repository evidence (HIGH):** observed current files, not claims of runtime testing:
`backend/app/models/user.py`, `models/trade.py`, `models/dividend.py`,
`services/accounts.py`, `trading.py`, `stock_trading.py`, `trade_idempotency.py`,
`stock_ownership.py`, `corporate_actions.py`, `dividends.py`, `event_history.py`,
`portfolio.py`, `backend/alembic/versions/0011_stock_action_accounting.py`,
`0014_dividend_accounting.py`, `frontend/src/hooks/usePortfolio.ts`,
`useStockTrade.ts`, `useEventHistory.ts`, `deploy/backup-snapshot.py`,
`backup-manifest.sql`, and `verify-restore.py`.

**Official documentation (HIGH for stated mechanisms; checked 2026-11-14):**

- [PostgreSQL 18 explicit locking](https://www.postgresql.org/docs/18/explicit-locking.html): row/advisory locks and consistent acquisition order.
- [PostgreSQL 18 isolation](https://www.postgresql.org/docs/18/transaction-iso.html): Read Committed snapshots and concurrent behavior.
- [PostgreSQL 18 constraints](https://www.postgresql.org/docs/18/ddl-constraints.html): cross-row CHECK limitations and relational constraints.
- [PostgreSQL CREATE FUNCTION security](https://www.postgresql.org/docs/18/sql-createfunction.html): definer resolution and EXECUTE privileges.
- [OWASP IDOR prevention](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html): authorize every supplied object identity.
- [TanStack Query v5 query keys](https://tanstack.com/query/v5/docs/framework/react/guides/query-keys): dependency-complete resource identities; official link redirects to v5 latest documentation.

These sources inform prevention. Recommended product semantics and the proposed
phase grouping are Birja-specific inferences requiring requirements/roadmap
approval; no source establishes the owner's deletion policy for them.
