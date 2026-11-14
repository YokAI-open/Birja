---
phase: 10-dividend-cash-and-event-history
plan: "10"
subsystem: event-history
tags: [owner-scope, keyset, immutable-facts, exact-wire, dividends]
requires:
  - phase: 10-01
    provides: Constrained immutable originals, decisions and frozen query indexes
  - phase: 10-06
    provides: Passed retained0007–0014 recovery and restricted-role/TLS prerequisite
  - phase: 10-07
    provides: Actual payment and hold transaction services
  - phase: 10-12
    provides: Frozen exact C05a client wire and parser
provides:
  - Strict C05a event schemas and canonical mixed cursorv2
  - Owner-first UNION paging and bounded immutable original lineage
  - Actual PostgreSQL mixed History and backend-to-TypeScript compatibility proof
affects: [10-09, 10-11, 10-13, 10-14, 10-15, 10-16]
tech-stack:
  added: []
  patterns: [owner-first-union, full-tuple-seek, bounded-saved-details, discriminated-wire]
key-files:
  created:
    - backend/app/schemas/event_history.py
    - backend/app/services/event_history.py
    - backend/tests/test_event_history_cursor.py
    - backend/tests/test_event_history.py
  modified: []
key-decisions:
  - Restrict each UNION source to the owner before seek and lookahead; detail/original reads repeat owner restriction.
  - Split ratios use exact Fraction reduction; absent historical company names use the retained symbol rather than mutable catalog labels.
  - Preserve legacy cursorv1 and endpoint implementation unchanged; expose the new service separately.
requirements-completed: []
requirements-supported: [HIST-03, DIV-03, DIV-05]
duration: approximately20min including contextual reads; task commit interval11m50s
completed: 2026-11-13
---

# Phase10 Plan10: Private immutable mixed History

**Owner-filtered source UNION and complete publication-tuple cursors project
saved trades, Dividend originals, owner splits and linked correction outcomes
without recreating or mutating their financial effects.**

## Accomplishments

- Exact frozen EventTrade, DividendTerms, EventDividend, EventSplit,
  EventDividendCorrection and EventHistoryPage schemas match C05a. Strict
  strings preserve BIGINT and Decimal precision; discriminators, fixed reasons,
  canonical UTC microseconds/dates, bounded plain labels, cent cash, whole
  shares, source attribution, original references and correction equations are
  validated. Nullable uncertain terms/target/proposal remain unknown, with
  actual cash0. Every outcome and malformed category has behavioral assertions.
- `list_event_history(db,*,user_id,limit=25,cursor=None)` restricts every source
  inside UNION ALL before outer seek/order/limit+1. Full tuple is
  `(recorded_at,kind_rank,source_id)` DESC, ranks4/3/2/1. Cursor rejects duplicate
  or extra JSON keys, wrong types/ranks, legacyv1, invalid calendar instants,
  noncanonical encoding/IDs/JSON and oversized data before any query. Owner and
  limits are also bounded before SQL; legacy History files remain unchanged.
- After the bounded key page, at most four bounded bulk detail queries fetch
  selected sources; no N+1 or unbounded original lookup. Owner restrictions
  repeat in every detail query and original-payment join. Correction includes
  the full immutable owner-bound original even outside this page. Zero-change
  checkpoints and holds remain correction events, never duplicate credits.
- Stock fills use retained StockFillFacts, including company/symbol and actual
  IEX quote time; crypto uses its existing stored fill values/established labels.
  Owner split movement supplies actual before/after shares, basis and economic
  time, joined to its retained application and revision. Decimal stored1.5:1
  reduces exactly to3:2. No float, current quote or financial recomputation.
- Existing split storage has no historical company name. As directed by parent,
  use the retained revision symbol for both symbol and display name instead of
  inventing a company name or joining a mutable catalog label. Actual catalog
  rename leaves stock fills, dividends and splits byte-stable. This truthful
  historical-label limitation requires no new schema or metadata backfill.
- Actual original/apply/hold services produce payment, verified correction,
  uncertain/cancelled and unaffordable outcomes for projection tests. Replay and
  held dedup do not add rows. Separate read-only retained-record fixtures test
  all-four-kind timestamp ties and colliding trade/payment IDs; those fixtures
  do not claim to execute or simulate successful cash effects. Existing SQL
  integrity constraints stay enabled and are explicitly flushed for coherent
  stock receipt/journal fixtures. An incomplete uncommitted stock receipt is
  refused and rolled back, never persisted by relaxing a constraint.

## Task commits and actual RED/GREEN

1. Task1 RED233c948: callable cursor scaffold refused a valid full-tuple
   roundtrip; actual expected behavior failed, not an import/collection error.
   Log `/tmp/birja-phase10-10-task1-red.log`:1failed0.52s.
2. Task1 GREENedb7eac: exact schemas/canonical cursor plus126tests1.01s.
   Log `/tmp/birja-phase10-10-task1-green.log`.
3. Task2 REDc8898d0: real SQL dividend credited its original, but the staged
   callable History returned0items instead of the expected1;1failed1.21s.
   Log `/tmp/birja-phase10-10-task2-red.log`.
4. Task2 GREENd0a2174: owner-first projection and complete scoped proof below.

Both temporary staged seams are removed; four commits exist, with no tracked
deletions. Source task interval11:16:26–11:28:16UTC on2026-11-13, excluding reads.

## Verification actually executed

Existing locked `uv run --no-sync --no-cache` only. Owned isolated `birja-test`
was inherited at0014; no provider, development or production service was used.

| Gate | Result |
|---|---|
| Final new cursor/schema/SQL files |149passed2.92s |
| New schema coverage |132statements/66branches,0missing/partial,100% |
| New service coverage |115statements/52branches,0missing/partial,100% |
| Legacy History/API plus actual dividend/action regressions |235passed21.68s;8existing pandas deprecation warnings |
| Scoped Ruff and format |All4owned source/test files PASS |
| Scoped Mypy |Both new source modules PASS |
| Whitespace and stub/deletion scan |PASS; no staged seams, TODO/FIXME or tracked deletion |
| DB handoff |0014; originals0,decisions0,entitlements0; no pending process |

Final coverage command:
`COVERAGE_FILE=/tmp/birja-phase10-10.coverage uv run --no-sync --no-cache pytest tests/test_event_history.py tests/test_event_history_cursor.py --cov=app.services.event_history --cov=app.schemas.event_history --cov-branch --cov-report=term-missing -q`.
Log `/tmp/birja-phase10-10-final.log`. Affected log
`/tmp/birja-phase10-10-affected.log`. Final tests are a superset of both plan
focused selectors. Full financial-wave suite/critical gate remains parent-owned.

Meaningful assertions include page sizes1/2/3/25/100, tied all-four-kind seeks,
same numeric ID in distinct kinds, exact lookahead/end cursor, foreign owner
and forged boundary isolation, newly inserted records visible after refresh,
immutable rename/replay, explicit no-cash uncertainty and offpage originals.
There is no cross-request frozen-snapshot promise.

### Actual backend-to-client compatibility

The real mixed PostgreSQL page, containing retained decimal1.5:1 split reduced
to3:2, passed the installed current `isEventHistoryPage` TypeScript parser.
Test `test_mixed_tied_time_whole_tuple_owner_paging_and_rename[25]` writes
pytest-owned temporary JSON and a copy of the actual parser; only its unused
transport import is replaced with a throwing stub. Every parsing guard remains
the current source, not a reimplementation. Test executes resolved Node24.22.1:
`node --input-type=module -e <fixed script> <temporary parser file URI> <temporary JSON path>`.
No network, package install or successful financial transport is mocked.

**Plan16 prerequisite:** backend CI must explicitly select the already approved
Node24 runtime before this cross-language test. Existing backend job currently
does not pin Node; parent accepted recording this for its CI-owned Plan16.
No workflow or package file was edited here. Backend tests use no npm install.

Context7 MCP/ctx7 CLI were unavailable. Consulted official
[SQLAlchemy2.0 UNION/select documentation](https://docs.sqlalchemy.org/en/20/core/selectable.html#sqlalchemy.sql.expression.union_all)
and [Pydantic discriminated unions](https://pydantic.dev/docs/validation/latest/concepts/unions/).
No dependency upgrade was inferred from documentation versions.

## Deviations and fixture corrections

- Historical split-label handling is a parent-directed truthful fallback for
  absent retained company-name facts; financial facts and frozen wire unchanged.
- Initial local non-escalated test hit sandbox socket denial before collection;
  rerun with authorized isolated-stack access produced the genuine RED above.
- Corrected own Coin `asset_class` field reference, deferred fixture timing after
  payout's constraint flush, and exact stock midpoint/held-after facts. No
  invariant was disabled. Scoped test harness uses asyncio.to_thread for file/
  Node work, resolved executable, fixed script and private pytest temporary paths.
- No architecture, schema, index, authority, recovery or grant change. Parent
  owns canonical STATE/ROADMAP/requirements updates; no full requirement is
  marked completed by this bounded projection plan.

## Threat results and remaining gates

- T-10-10-01 CLOSED for this service: owner predicate per UNION/detail source,
  immutable owner-bound originals, strict full-tuple cursor and actual foreign
  owner/forged boundary tests. No input amount/owner override or financial write.
- T-10-10-02 CLOSED: saved source identities/values, stable public kind:ID,
  original lineage, explicit unknown/no-cash semantics and real parser proof.
- T-10-10-03 CLOSED: limit1..100, cursor≤512, ≤101keyrows and at most100selected
  details across four bulk queries; no provider I/O, lock or unbounded scan loop.
- T-10-10-SC CLOSED: no package/image/lockfile change or installation.
- No unplanned endpoint/auth/file/schema trust surface and no known stubs. API,
  scheduler integration, browser/UI, final full recovery/security and actual
  owner UI/nativezoom acceptance remain later declared plans. Provider/live,
  production/B2/timer/installed-tool and publication scope remains deferred.

## Self-Check: PASSED

All4owned implementation/test files and this summary exist. Four task commits
exist, no tracked deletion;149new/235affected tests and100%statement/branch
coverage plus static checks pass. SQL authority/recovery unchanged. Owned empty
0014 test stack remains running; DB ownership is released to parent. Unrelated
`.claude/` and canonical project state are preserved.

## Full-wave fixture collision and verified correction

Parent's first complete financial-wave run failed6tests/2428 in299.35s:
the five mixed tied-time variants and legacy stored-BIGINT case collided on
fixed trade ID9007199254740993. The earlier affected legacy run had committed
that test record; existing new_user fixtures intentionally retain their rows,
whereas mixed records roll back. Initial scoped passes therefore did not prove
repeatability against committed legacy records. This failure is not a passing
full-wave gate. Evidence: `/tmp/birja-phase10-wave6-backend.log`.

Parent extended ownership solely to the existing legacy History test file.
Actual regression REDf1e312e adds two distinct-owner high-ID records; it fails
with the existing duplicate PK before repair,1failed1.12s. Fix6f9af5c binds
high ID9007199254740993+test-owner-ID in both helpers, preserving values beyond
JavaScript's exact-integer range and using returned IDs in all assertions.
No production source, schema, sequence, existing row or invariant was changed
or deleted. Canonical parent STATE/ROADMAP edits remain untouched.

On the same owned database, with no cleanup/reset between runs:

| Order | Actual result |
|---|---|
| Legacy History service → mixed History |74passed3.76s |
| Mixed History → legacy History service |74passed3.10s |
| Repeat legacy → mixed |74passed3.08s |

Logs: `/tmp/birja-phase10-10-fixture-{red,order1,order2,repeat}.log`.
Ruff/format on both changed tests and whitespace checks pass. New runtime
modules are unchanged from their100%statement/branch proof. Parent must rerun
the full financial wave; no full-suite pass is claimed here. No process remains;
DB ownership is released, test stack still0014. Legacy test-owned rows remain
under their existing fixture policy, with collision-free owner identities.
