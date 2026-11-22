# Phase 12 Deferred Integration Items

## Retained trading-schema fixture association — Plan27

Discovered during Plan12-10's optional retained regression run:
backend/tests/test_trading_schema.py has16 failures because its synthetic
holdings/trades omit portfolio_id required since0017. The combined run had91
passing cases, including all44 assigned crypto service/API cases and47 unchanged
trade_math cases. These retained fixture failures are not a passing full suite.

Plan27 must give each fixture its explicit owned root while preserving its
original positive/negative economic and uniqueness assertions. Do not relax
NOT NULL, paired ownership, immutable evidence or authorization guards. Old
user-only service/API fixture callers likewise require their planned explicit
root/v2 composition updates; legacy v1 finance refusal belongs15.


## Retained mixed-History API cursor/fixture integration — Plan27

Plan15's actual production four-API gate and259 affected API/auth/onboarding
cases pass. The older test_event_history_api.py still fails collection at its
static HistoryCursor(created_at=STAMP,id=1) without required portfolio_id. Its
retained dividend fixture also assumes temporary ownership of older role setup.
Adapt those cursor/owned fixture contracts and actual scoped URLs in27; do not
weaken immutable ledgers, paired FKs, role inventories or cursor rejection.
A new real correction/original HTTP test proves scoped private originals in15;
this does not claim the older mixed fixture suite passed.

Plan15 resolves the old production v1 stock/read followed-import type failures:
complete mypy app now passes101 source files. Legacy routes are explicit409;
new production readers/execution are reachable only through scoped v2 paths.
