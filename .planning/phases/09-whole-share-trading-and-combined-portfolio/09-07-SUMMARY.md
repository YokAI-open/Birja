---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "07"
subsystem: trading
tags: [concurrency, postgresql, corporate-actions, deadlines]
requires:
  - phase: 09-06
    provides: atomic stock execution and original receipts
provides:
  - Real mixed-asset and multi-instrument shared-cash contention proof
  - Post-wait authority/quote/clock refusal and exact rollback proof
  - Bounded rollback/rebuild for current opposite-side quote facts
  - Actual first-fill versus corporate-action gate ordering and historical units
affects: [09-08, 09-09, 09-14]
tech-stack:
  added: []
  patterns: [observable PostgreSQL blockers, bounded metadata rebuild]
key-files:
  created:
    - backend/tests/test_stock_trading_concurrency.py
    - backend/tests/test_stock_trading_waits.py
  modified:
    - backend/tests/stock_trade_fixtures.py
    - backend/app/services/stock_trading.py
requirements-completed: []
requirements-supported: [MKT-02, STKTR-03, STKTR-04, STKTR-05, STKTR-06]
duration: 15min
completed: 2026-11-12
---

# Plan09-07: Actual financial contention and post-wait authority

## Task evidence

Task1 b8a3b1c:9real concurrency tests pass7.02s without a runtime change.
The existing06 implementation already satisfied these assertions; no fabricated
failing test is claimed. Actual separate sessions prove absent holdings,
competing stock/crypto and two-stock spends, duplicate global keys, overselling,
multi-user/multi-stock holder contention and immediately reusable sale cash.

Task2 RED050bfa0: independently committed opposite-side quote during an observed
helper lock wait still refused. The runtime refinement rolls back ALL tentative
immutable rows and permits exactly one fresh metadata rebuild. It never retries
timeout, deadlock, cancellation, ownership, integrity or permission failure.
A changed selected price still requires a fresh preview/confirmation. Repeated
metadata movement refuses safely; no immutable row is rewritten.

Final serial gate `/tmp/birja-phase09-07-services.log`: **248passed63.39s**.
New execution174statements/40branches and global keys11statements/2branches:
**100%**, no partial branches. Scoped Ruff/format/Mypy pass. It includes all
new service/key/crypto/ownership and concurrency/wait files.

## Adversarial boundaries

Observed actual PostgreSQL waits at instrument, Account, sorted existing holding,
helper flush, before deferred constraints and immediately before final guard.
Helper/final boundary instrumentation adds a real test-only advisory barrier;
it does not replace SQL, clocks, services, authorities or financial operations.
These are NOT claimed as relation waits inside the final function. A discarded
harness attempted an impossible relation-lock upgrade across the writer's
existing read locks; it was corrected, not treated as a runtime deadlock.

Committed quote changes/staleness, permission revocation, halt, continuity loss,
status expiry, monitor/due-cutoff/units and closure are tested at every boundary.
Additional late same-generation attribution, safety epoch and status sequence
changes refuse. Real elapsed DB wall time expires status, quote120s, admission
and monitor while final work waits. Every refused order leaves exact pre-state
cash, holdings, basis, Trade/facts/journal. Actual cancellation releases locks.
Final guard is LAST business SQL with runtime ordering and source assertions;
statement-snapshot linearization does not predict later changes/commit delay.

Real first fills preserve exclusive dividend cutoffs at -1/0/+1microsecond and
sold-out history. A matched synthetic split's actual causal journal and later
stock sale preserve old/new units, basis and original receipt. Separately the
ACTUAL corporate-action ingest/apply processor waits for a first fill gate and
then applies a4:1split to8shares with204basis. Original receipt remains unchanged.
The XID wrap test injects the guard input only; actual PostgreSQL wrap is not
claimed. Existing ownership timeout and unit/cause tests remain in this gate.

Fixture teardown was extended for action observations; after one teardown
failure the owned tmpfs birja-test stack alone was reset. Final gate passes
with complete cleanup. No dev/prod data, provider, B2, installed tool or timer
was touched. API/UI/recovered actual-service gates remain08–15; live activation
is deferred and whole requirements are pending.
