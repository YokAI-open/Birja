---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T11:02:22Z
depth: deep
diff_base: a0ba4eb
review_head: 32bff2b
files_reviewed: 13
files_reviewed_list:
  - backend/alembic/versions/0011_stock_action_accounting.py
  - backend/app/models/__init__.py
  - backend/app/models/corporate_action.py
  - backend/app/models/stock.py
  - backend/app/models/trade.py
  - backend/app/services/stock_quotes.py
  - backend/app/services/stocks.py
  - backend/tests/test_migrations.py
  - backend/tests/test_stock_action_migrations.py
  - backend/tests/test_stock_quotes.py
  - backend/tests/test_stocks_api.py
  - backend/tests/test_stock_catalog.py
  - deploy/db/bootstrap-roles.sql
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 08-01: Focused Schema Review

Scope is the frozen Plan 01 source through `6282251`, including its tests and
stable planning contracts. This is an early schema review, not the final phase
audit. No source edits, provider calls, database operations or production access
were performed. Existing reported test passes were not treated as proof of the
missing constraints below.

## Narrative Findings (AI reviewer)

### Scoped integration correction at `32bff2b`

**Zero active BLOCKER/WARNING findings.** Inspected only the explicit provider
projection correction and its stock API/seed-guard regressions. The projected
field names match `ValidatedStockQuote` exactly and no longer pass local
`unit_epoch` to its constructor. Nonzero stored unit epochs suppress both recent
and historical quote disclosure until the later current-unit gate exists. The
new API regression covers zero/nonzero epochs with recent/dated quotes; the seed
downgrade regression now explicitly starts at its original 0010 revision and
restores head after cleanup. Prior CR-01/02/03 corrections are unchanged. No
tests, source edits or runtime operations were performed in this scoped review.

### Final targeted re-review at `b389ce1`

**Zero active BLOCKER/WARNING findings.** CR-01, CR-02 and CR-03 are resolved.
Migration SHA256 verified as
`57b4f279a969b3e7da55c87742414138eeefe493fd82309fb1b268b71ac6e161`.

The new index helper validates the exact standalone public/trades unique btree
definition, matching table/current migrator ownership, live state and absence of
an attached constraint. It reuses only a matching valid/ready index, rebuilds an
exact invalid build concurrently, and refuses incompatible objects. Thus the
committed-index/post-transaction-failure retry path no longer unconditionally
recreates the index. The regression source covers restricted prerequisite
failure/provision/retry, untouched incompatible-name refusal, and actual
cancelled-build recovery. Earlier alias and causal composite FK corrections
remain intact. No source edits, tests or runtime operations were performed in
this re-review; the executor's 91-test result remains separately attributed.

### Re-review at `5d0353a`

CR-01 and CR-02 below are retained as historical findings and are **resolved** in
the reviewed correction. Observations now reference source/event and
revision/event composite keys; movements bind fills to the same instrument/user
and split applications to the same instrument/resulting unit epoch. Split
applications themselves bind their instrument to the economic event. The
matching ORM/migration definitions and focused regression source were inspected;
no additional runtime privileges, trigger or function were introduced. The
executor's reported 88 passing tests were not rerun by this reviewer.

At that review one new BLOCKER remained, subsequently resolved at `b389ce1`:

### CR-03 — BLOCKER, RESOLVED: Failed upgrade leaves an index that prevents safe retry

**File:** `/home/YokaiExchange/backend/alembic/versions/0011_stock_action_accounting.py:26`

**Issue:** `CREATE UNIQUE INDEX CONCURRENTLY uq_trades_id_coin_user` executes in
an autocommit block before the transactional migration, with no reuse or recovery
path. A restricted upgrade without the preprovisioned operator role intentionally
raises its prerequisite exception later in this migration. PostgreSQL then rolls
back the new tables, constraint attachment and revision advancement, but the
already committed standalone index remains. Provisioning the operator and
retrying the unchanged migration immediately fails because the named index
already exists. Any later transactional failure has the same retry failure;
an interrupted concurrent build can also leave an invalid index.

**Fix:** Make this exact concurrent-index preparation safely restartable.
Independently verify the existing object's relation, ownership, columns/order,
uniqueness, validity/readiness and absence of incompatible expressions/predicates
before reusing it. Reject incompatible objects rather than silently trusting
`IF NOT EXISTS`. Handle an invalid index through an explicitly safe exact-object
repair path. Move known prerequisite checks ahead of autocommit preparation as
well, but retain retry safety for other failures. Add a real PostgreSQL regression
that causes a post-index migration failure, confirms predecessor revision remains,
removes the failure condition and successfully retries without manual grant or
index repair.

## Historical Findings

### CR-01 — BLOCKER, RESOLVED: Verified aliases cannot observe an existing economic revision

**File:** `/home/YokaiExchange/backend/app/models/corporate_action.py:144`

**Also affected:**
`/home/YokaiExchange/backend/alembic/versions/0011_stock_action_accounting.py:271`

**Issue:** An observation's `(revision_id, source_id)` must match the revision's
original source exactly. Consider event E with source S1 and revision R for
fingerprint F. After a second verified source S2 is linked to the same economic
event, an identical observation from S2 cannot reference R: the composite FK
rejects it. Creating another revision with S2 and F also fails the existing
`UNIQUE(event_id, fingerprint)` constraint. Thus the schema cannot represent the
planned verified-alias observation without fabricating different economic terms,
losing source provenance, or rewriting immutable records. Plan 08-08 explicitly
requires verified aliases with equal economic terms; the shared schema contract
requires repeated identical observations without a second economic revision.

**Fix:** Make observation source/revision consistency operate at the economic
event boundary. For example, add observation `event_id` and composite FKs
`(source_id,event_id)` to sources and `(revision_id,event_id)` to revisions.
Preserve the revision's originating source and scoped mutation uniqueness.
Regression: two sources for one event can observe the same revision, while a
source belonging to a different event is rejected by PostgreSQL.

### CR-02 — BLOCKER, RESOLVED: Ownership causes can refer to another instrument or owner

**File:** `/home/YokaiExchange/backend/app/models/corporate_action.py:338`

**Also affected:**
`/home/YokaiExchange/backend/alembic/versions/0011_stock_action_accounting.py:651`

**Issue:** Ownership movements check that `trade_id` or `application_id` exists,
but never connect that cause to the movement's instrument or owner. All current
checks permit an AAPL movement for user U to cite a BTC trade for user V, or an
AAPL split movement to cite a MSFT split application. The movement's unit epoch
is also independent of the cited split application's resulting epoch. The
before/after arithmetic can be internally valid while the economic cause is
false. Existing uniqueness constraints then consume that trade/application cause
and cannot establish a correct ownership journal or dividend eligibility. This
violates the durable causal-accounting boundary before downstream services rely
on it.

**Fix:** Enforce causal correspondence in PostgreSQL. Use composite keys/FKs for
trade identity plus coin/user, and add a constrained instrument identity to split
applications with a composite FK tying it to the application's event. Tie split
movement coin and resulting unit epoch to that application, or use a narrowly
scoped insert trigger that validates these immutable facts without granting
runtime mutation authority. Regression tests must reject cross-user/cross-coin
fill references and cross-coin/wrong-epoch split references while accepting the
matching cause.
