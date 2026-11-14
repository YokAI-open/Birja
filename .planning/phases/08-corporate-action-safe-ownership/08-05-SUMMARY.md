---
phase: 08-corporate-action-safe-ownership
plan: "05"
subsystem: accounting
tags: [postgresql, ownership, advisory-locks, cutoff, split-units, least-privilege]
requires:
  - phase: 08-02
    provides: Exact0011 retained recovery and restricted-TLS upgrade/fresh proof
  - phase: 08-03
    provides: Frozen exact action and genuine-calendar cutoff contracts
provides:
  - Instrument-first caller-owned ownership transactions and immutable causal replay
  - Exact exclusive-cutoff snapshots with explicit pre/post-split unit epochs
  - Whole-instrument journal, immutable-fill and holdings/basis consistency checks
affects: [08-06, 08-07, 08-08, 08-09, 09-stock-trading]
tech-stack:
  added: []
  patterns: [native-transaction-advisory-gate, post-lock-database-wall-clock, explicit-unit-boundaries]
key-files:
  created: [backend/app/services/stock_ownership.py, backend/tests/test_stock_ownership.py, backend/tests/stock_action_fixtures.py]
  modified: [backend/alembic/versions/0011_stock_action_accounting.py, backend/tests/test_stock_action_migrations.py, deploy/db/bootstrap-roles.sql, deploy/tests/ops-fixtures.py]
key-decisions:
  - App allocates journal sequence from the serialized tail without updating scheduler-owned state authority.
  - All owners, zero holdings and departed owners remain part of history consistency.
  - A split sequence boundary is the journal tail before its first per-owner delta; old-unit movements at or after its cutoff are held.
  - Atomic cause validation explicitly refuses full transaction IDs at or beyond2**32 rather than guessing tuple xmin epochs.
  - Scheduler receives only six immutable trade columns required to audit orphan fills; financial mutation and other columns remain denied.
requirements-completed: []
requirements-addressed: [DIV-02, ACT-01, ACT-03]
duration: 32min
completed: 2026-11-11
---

# Phase 8 Plan 05: Historical Stock Ownership Summary

**Instrument-serialized causal movements atomically update whole-share holdings and reconstruct exclusive-cutoff entitlement inputs in verified split units, while incomplete or ambiguous history remains held.**

## Accomplishments and interfaces

`acquire_stock_gate(db, coin_id)` uses the fixed SQL namespace
`pg_advisory_xact_lock(hashtextextended('birja.stock.instrument:' || CAST(:coin AS text),0))`.
SQL/operator consumers must use the same expression. Hash collisions only add
serialization. One instrument is allowed per transaction. READ COMMITTED is
required; lock/statement/idle-transaction timeouts are5/10/30seconds. Caller
transaction contexts own commit/rollback and cancellation cleanup.

`append_stock_movement(db, StockMovementInput)` matches a real immutable fill or
split application and changes its holding plus journal atomically. No production
opening operation, order endpoint or cash service exists. Fill integration order
is instrument→account→holdings sorted(user_id,id)→immutable cause. Fresh
`clock_timestamp()` is captured after blocking locks/authority reads; caller
backdating and `Trade.created_at` never determine a new fill's economic instant.
Same causal payload returns the original stored movement; changed payload,
duplicate cause, orphan committed fill/application and cross-transaction pending
cause are refused. Basis must match exact existing fill accounting; splits
preserve it unchanged.

The app derives sequence from the complete serialized journal tail. It never
updates `stock_action_state.sequence`, health or epoch; those remain scheduler
authority. `assert_ownership_consistent` checks contiguous global sequences,
economic order, causal fills, every affected owner's before/after quantities and
basis, all current holdings, absent/zero holdings, split linkage and complete unit
transitions. A pending current cause can be excluded only during its atomic
append. Public reconstruction never accepts partial split applications.

`reconstruct_stock_quantity(db,user_id,coin_id,cutoff:CutoffEvidence,units:int)`
returns frozen `StockQuantitySnapshot(quantity,unit_epoch,last_movement_sequence,
cutoff)`. Cutoff retains rule/calendar generation/version. Strict economic
`<cutoff` excludes exact/late buys; later sales and zero current holdings do not
erase prior eligibility. Integer `units` explicitly selects prior/new denomination
at an exact split boundary; away from that boundary only its effective epoch is
accepted. A split's sequence boundary is the tail BEFORE all per-owner deltas.
An old-unit movement at/after that cutoff is held, not guessed into another unit.
Missing baseline, sequence gap, late/backdated fill, orphan cause, unjournaled
holding or inconsistent units blocks automatic processing across all owners.

### Explicit transaction epoch limitation

`require_supported_transaction_epoch(full_xid)` raises typed
`OwnershipHeld(reason="transaction_epoch_unverified")` for full IDs>=2**32
before any32-bit xmin/`pg_xact_status` interpretation. New fill/split journaling
then remains held until a separately verified own-row proof replaces this guard;
stored replay and read-only reconstruction remain available. This is enforced
fail-closed behavior, not claimed wraparound support. Actual current/pre-wrap
pending, committed, another transaction's invisible pending cause and completed
savepoint behavior are tested. Synthetic pure boundary tests cover2**32-1,
2**32 and2**33; no actual cluster wrap was performed. A real PostgreSQL probe
showed native own-subtransaction locks disappear after savepoint release, so
that shortcut was not used as a false proof. Independent focused re-review
accepted the conservative explicit limitation with0active findings.

## TDD and task commits

1. Task08-05-01 RED `004108a`: an importable fail-closed scaffold failed the real
   atomic holding/replay behavioral assertion. GREEN `43bcb9a`:32actual PostgreSQL
   cases passed, including observed lock waits, expiry, replay and cancellation.
2. Task08-05-02 RED `ac00361`: exclusive-cutoff ownership failed behaviorally,
   rather than from a missing file/import. GREEN `cf637f0`: complete history,
   exact units, adversarial real database fixtures and minimum scheduler reads.

Additional independently found bugs have observed failing regressions before
correction: both exact-boundary buy/sale cases previously failed to hold
(`/tmp/phase08-05-boundary-red.log`), and three wrapped full-XID boundaries were
not refused (`/tmp/phase08-05-epoch-red.log`). Final GREEN includes both fixes.

## Actual verification

- `uv run pytest tests/test_stock_ownership.py tests/test_stock_action_migrations.py tests/test_trading_service.py tests/test_trading_concurrency.py tests/test_trades_api.py --cov=app.services.stock_ownership --cov-branch --cov-report=term-missing --cov-fail-under=100 -q -x`:
  **207passed19.41s**, no warnings; ownership **203statements/94branches100%**.
  Includes84ownership cases and unchanged crypto service/API/concurrency checks.
  Receipt:`/tmp/phase08-05-backend-final.log`.
- Five changed backend files: Ruff check/format pass; ownership mypy passes.
  Operations fixture E9/F/I, py_compile, shell syntax and whitespace checks pass.
- Actual waiting transactions are observed through `pg_blocking_pids`, not
  inferred from sleep. First-commit duplicate-cause race makes one movement;
  concurrent committed gaps and authority-expiry changes are detected after
  waiting. Actual five-second lock timeout and cancellation release safely.
- `bash deploy/tests/test-db-operations.sh --roles`: exit0. Role transition and
  fresh parity **155.530s**, including63legacy denials; actual populated0010→0011
  verified-TLS **102.727s**, fresh0011 verified-TLS **99.435s**. Both execute actual
  app append/replay/reconstruction and scheduler consistency services, exact
  six-column reads and retained denials. Receipt:`/tmp/phase08-05-roles.log`.
- After independent review corrections, final frozen-source
  `bash deploy/tests/test-db-operations.sh --tls`: exit0, **100.850s**. Actual
  populated upgrade, final app/scheduler ownership consumers, genuine calendar,
  CA/hostname/plaintext refusals, credential isolation and renewal pass.
  Receipt:`/tmp/phase08-05-tls-final.log`.
- Independent focused re-review of `cf637f0`: **0active findings**. Parent full
  Wave3 integration remains a separate next gate; it is not claimed here.

## Privilege correction and recovery boundary

**[Rule2—critical correctness]** The first actual scheduler consumer failed42501
because the new orphan-fill audit needs immutable trade facts. Parent explicitly
assigned the minimum correction: identical0011/bootstrap
`SELECT(id,coin_id,user_id,side,quantity,cash_delta)` and matching downgrade
REVOKE, with explicit six-column service projection. No table-wide SELECT,
other-column read, trade mutation, account access, basis update or state authority
was granted. Actual SQL allows precisely those columns while SELECT*,cash_after,
INSERT/UPDATE/DELETEtrades and existing cash/basis/admission/operator escalation
remain42501. App append/replay/reconstruction passes with existing app grants;
app state health UPDATE remains42501.

0011 remains unmerged. Its new SHA256 is
`ba07623bca2cff4e709971e2157364e417d877b085ff5e4f24dfa3e96fb72af3`.
Only ACL SQL changed; no table/column/constraint/index/row/identity or canonical
producer/restore contract changed. Existing Plan02 exact five-revision encrypted
archive proof remains historical evidence, not a claimed rerun. The affected
current upgrade/fresh grants and actual services were separately re-proved above.
Producer SHA256 remains
`196b459ec86c75d778eb1f7bc81b14cb1b8f987b4737c2d3a4ce92261917311a`.
Final ownership source SHA256:
`08c6d75bac572d2c3a62d15d65efb28a6e9166129668e6bf8e17095de2c064e9`.

## Deviations, threats and remaining scope

**[Rule1—correctness]** Independently reviewed equal-boundary denomination and
xmin epoch bugs were reproduced and corrected as described above. An old role
test's denied-ID-read expectation was updated to an allowed ID read plus denied
cash_after read; existing denial gates were not removed. A draft savepoint
permission assertion caught its exception inside the context and attempted to
release an aborted savepoint; corrected exception nesting preserves actual42501
proof. No dependency installation or version change occurred.

The only new privilege surface is the reviewed six-column immutable scheduler
read above; T-08-05-01/02/03 are covered by exact causal/unit/cutoff constraints,
real bounded-lock races and post-wait wall-clock evidence. No new endpoint,
secret route, provider call or infrastructure service was introduced. No required
stub/TODO/FIXME remains. Test-only openings are explicit synthetic fixtures,
never imported by application code.

Phase7 live verification remains owner-deferred; its process and files are
untouched. Stock execution remains OFF, real fills integrate in Phase9 and
payments/public event History remain Phase10. No provider/env/key access,
production, B2, timer, installation, publication or deployment occurred.
All operated resources are isolated fixtures; final cleanup is checked below.

## Self-Check: PASSED

All seven source/test artifacts and four listed task commits exist. Actual
focused/backend/role/TLS results above passed; independent re-review is clean.
No requirement is marked complete solely from this foundation. Metadata updates
preserve prior Phase7 deferral and Plan02's historical recovery evidence.
