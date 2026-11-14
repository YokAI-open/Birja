#09-03 integration corrections

Recorded2026-11-11 after parent full-backend run at `e5f122a`:
**7failed/1777passed165.64s,99.67%overall**. That run was not green; the
earlier124-test09-03 scoped proof did not cover these older integration fixtures.

## Corrected compatibility

- `test_migrations.py`: actual-head expectations now0013. Its original crypto
  financial-constraint comparison excludes only the separately verified successor
  `stock_fill_integrity` constraint trigger, while preserving legacy CHECK/FK
  assertions and financial row snapshots.
- `test_stock_action_migrations.py`: exactly three assertions following actual
  `upgrade head` now expect0013. Failed restricted-upgrade retry was reproduced:
  retry returned0 and produced0013; failure was solely stale0012 expectation.
  Cancelled concurrent-index test was separately reproduced: genuine57014,
  invalid-index observation and rebuild succeeded; final assertion alone expected
  stale0012. Historical0010/0011/0012 test targets were not blanket-replaced.
- `test_stock_isolation.py`: crypto replay denial now starts from a complete
  persisted stock Trade/facts/movement plus corresponding cash/holding snapshot.
  The asserted outcome remains `unknown_coin` with unchanged financial rows.
  Test cleanup uses the existing privileged, test-only named-trigger maintenance
  helper. Behavior under test keeps immutable financial triggers enabled; no
  incomplete stock fill is committed and no runtime authority is bypassed.

Compatibility commit: **`b2d9f80`**.

## Critical pure-rule coverage

`test_stock_trading_rules.py` adds assertions for incomplete/inverted/mismatched
session intervals, unpermitted retained marks, missing quote sides and stale
open-session marks without a closed-session fallback. One explicit validator
fault-injection test verifies projection still refuses a missing source side;
it does not mock database accounting or invent a value. Parent fix `e5f122a`
and its malformed-session-state regressions are preserved unchanged.

Coverage commit: **`96e780b`**. No application or migration file changed.

## Targeted final evidence

All commands used existing locked interpreter through
`uv run --no-sync --no-cache` and guarded test resources only:

| Selector / command | Actual outcome |
| --- | --- |
| pytest test_migrations.py test_stock_action_migrations.py test_stock_isolation.py -q -x |71passed10.67s |
| pytest test_stock_trading_rules.py --cov=app.services.stock_trading_rules --cov-report=term-missing --cov-fail-under=100 -q |79passed0.60s;173statements/50branches100%;0partialbranches |
| Ruff check/format on four changed test files |PASS |
| git diff --check |PASS |

No full backend rerun was performed in this correction lane. Parent owns the
single subsequent full-wave run and canonical recovery/verified-TLS proof.
STATE/ROADMAP changes and unrelated untracked review/proof/.claude files were
preserved. No packages, provider/private/production access, push or deployment.
