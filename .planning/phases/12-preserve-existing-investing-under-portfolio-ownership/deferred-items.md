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
