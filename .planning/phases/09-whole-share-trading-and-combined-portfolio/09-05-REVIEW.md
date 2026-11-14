# Plan09-05 review —2026-11-12

Separate sequential inline review under AGENTS/GSD fallback: the attempted
agents lacked filesystem/shell tools. No independent agent review is claimed.
Scope: finite normalization, real persistence and scheduler entry, shared
authority SQL/projection, discovery schemas and synthetic fixtures.

## Resolved findings

- R05-01: enforce raw source-reference length, total UTF8 envelope size before
  partitioning, at most20 instruments/1000 events, safe integer generations and
  explicit complete/contiguous/end markers. A whitespace-prefixed oversized
  source reference failed a behavioral regression before its correction.
- R05-02: fresh quote/status data could outlive its permitted data-use period.
  Actual PostgreSQL RED showed an executable quote beyond retention. Expired
  data now denies permission; future data deadlines conservatively narrow
  session_valid_until, which the final invoker guard already checks. Raw
  admission dates and status records remain exact for its equality checks.
- R05-03: current display/collection rights do not authorize permanent financial
  receipts and recovery copies. Execution approval requires each product's
  explicit durable_accounting/backup_restore/retention_mode scope, alongside
  all existing semantic checks. Current independent status display remains
  separate. These fixture scopes establish no real provider agreement.
- R05-04: terminal continuity generation cannot wrap, but loss must still clear
  authority. The terminal row remains at MAX_SAFE with unknown state, cleared
  verification/continuity and no deadline; no supported later baseline can
  advance it. Actual PostgreSQL tests cover this behavior.
- R05-05: shared fixtures now replace only the external calendar dataset, clear
  its immutable cache even on setup failure, and execute real calendar
  construction/validation plus the advancing database clock. They do not mock
  the database or bypass eligibility to permit off-hours tests.

## Boundary checks

One materialized bounded SQL snapshot precedes DB time sampling. Numeric quote
JSON fields are text before decoding; bigint/epoch values remain Python ints.
Fresh scalar reads bypass ORM identity caches and deny repeatable-read authority.
After gated status writes/flush, a second real statement compares full admission
row hashes and mapping identity, rechecks semantic permissions and advances time.
Real row-lock barriers prove rollback after same-generation edits, mapping edits,
permission expiry and status lease expiry, with unchanged financial snapshots.

No quote/heartbeat/poll health can create normal status. None/startup invalidates
persisted continuity. Only finite test injection is available; production rejects
it before collection. No transport, credential path, dependency or outbound
attempt was added. Future real transport still requires verified suitability,
rights and the existing shared attempt quota. Default collector failure is bounded,
logs only exception classes and attempts conservative invalidation.

Independent halt/freeze, session and action information stays separate. A known
halt does not override action uncertainty. Compatible post-split quotes may stay
visible while an unrefreshed cached action boundary blocks execution, matching
the existing final SQL guard. No schema/function/role-grant change was made.

## Outcome and remaining work

No open blocker/high finding. Settled backend proof:1889passed/77warnings202.08s,
99.85%overall; all35 critical modules3534statements/1154branches100%. Full Ruff
and formatting pass158files; Mypy passes76sources. Six affected critical modules
separately pass593statements/182branches100%; see09-05-SUMMARY.md for selectors.

This plan does not implement new stock fills, global key handling, mixed valuation
or new UI acceptance. The planned frontend parser integration is Plan10; actual
trade API/service and final-wait races are06–08, portfolio09 and full gates14.
Phase7/8 live activation remains owner-deferred. No provider/production/B2/timer/
push/merge/deployment action occurred.
