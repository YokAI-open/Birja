---
phase: 10-dividend-cash-and-event-history
plan: "02"
subsystem: database-authority
tags: [postgresql, security-definer, dividends, half-even, restricted-roles]
requires:
  - phase: 10-01
    provides: Immutable0014 dividend originals/decisions and retained composite identities
  - phase: 10-03
    provides: Literal cross-language HALF_EVEN target vectors
provides:
  - Narrow retained-row dividend apply and no-cash uncertainty SQL authorities
  - Private current-authority helper and final post-constraint advancing guard
  - Exact0014 function identity preflight and minimal bootstrap grants
affects: [10-04, 10-05, 10-06, 10-07, 10-08, 10-09]
tech-stack:
  added: []
  patterns: [scheduler-execute-only, gate-before-account, full-row-authority-snapshot, immutable-corrections]
key-files:
  created:
    - backend/tests/test_dividend_authority.py
  modified:
    - backend/alembic/versions/0014_dividend_accounting.py
    - deploy/db/bootstrap-roles.sql
    - deploy/configure-db.sh
    - backend/tests/conftest.py
    - backend/tests/test_migrations.py
    - backend/tests/test_stock_migrations.py
    - backend/tests/test_stock_action_migrations.py
key-decisions:
  - Existing canonical birja_migrator owns both definers and private helpers; migration fails before DDL if that safe owner is absent or privileged.
  - Historical eligibility is checked against the retained ownership journal and current retained calendar session, without requiring an open market, quote or normal trading status.
  - Original and successful-target replay returns immutable references without another cash effect even after current authority is revoked.
  - Test-only canonical NOLOGIN owner provisioning is explicit and guarded outside application migrations; historical fixture cleanup preserves pre-existing owners.
requirements-completed: []
requirements-supported: [DIV-03, DIV-04, DIV-05]
duration: approximately26min
completed: 2026-11-12
---

# Phase 10 Plan 02: Narrow Dividend SQL Authority Summary

**Scheduler-only SQL derives exact dividend targets from retained owner evidence, atomically appends credits/corrections, and records uncertain successors without cash authority.**

## Performance

- Tasks2/2;8implementation/test/bootstrap files plus this summary.
- Observed first behavioral RED commit19:31:55UTC through final source/fixture
  commits approximately19:57UTC,2026-11-12; approximately26minutes, excluding
  initial contextual reads. No publication, provider/secret, production, B2,
  timer, installed-tool, deployment or dependency action occurred.
- Final affected suite:183passed,4existing pandas calendar warnings,23.01s.
  New authority suite contains41tests. Root owns full-wave/backend/critical
  coverage and independent review; neither is claimed from this scoped gate.

## Accomplishments

- Exact `public.apply_stock_dividend(bigint,bigint,text,text)` derives event,
  owner, revision, entitlement, quantity, rate and cash internally. No caller
  amount, owner, clock or JSON authority is accepted. Fixed static qualified
  SQL takes the shared instrument advisory gate before Account FOR UPDATE.
- Private invoker helper
  `public.stock_dividend_authority(bigint,bigint,text,text,boolean,jsonb)`
  reloads complete retained event/revision/entitlement/action/instrument/coin,
  independent admissions and historical cutoff/session facts. Full JSON row
  equality includes all admission fields and generations after waits; advancing
  clock checks independently enforce current rights/monitor/coverage/payable
  New York calendar date. The helper is not executable by app/scheduler/PUBLIC.
- Current verified target requires the latest version/ID entitlement tied to
  the current revision, exact fingerprint, exclusive calendar opening, matching
  calendar generation, retained denomination and independently reconstructed
  historical quantity/sequence. Unsupported persistent events require existing
  reviewed reconciliation. Current holdings, fresh quotes, open sessions and
  normal live trading status are not payout prerequisites.
- Admission checks enforce retained collection/display/derived/storage rights,
  durable-accounting/backup scope, finite bounded quota/field shape, reviewed
  action capabilities and curated symbols, calendar provenance, review/horizon
  and override shape. No runtime observation supplies its own permission.
- SQL explicitly implements HALF_EVEN on the once-computed exact product, with
  all10literal Python vectors passing actual PostgreSQL, including tie/zero/
  large-boundary cases. Correction is desired target minus original plus actual
  applied decisions. Zero originals, A→B→A and verified no-change remain valid;
  held proposals do not enter cumulative applied cash.
- Insufficient-cash corrections append stable deduplicated no-cash decisions;
  the exact target can later append a separate successful linked application.
  Original replay and successful target replay return their saved references
  without relying on current permission or changing money again.
- `public.record_stock_dividend_hold(bigint,text)` requires an existing payment,
  derives owner/current observed revision/optional entitlement, and appends or
  deduplicates held_uncertain with unknown target/proposal and applied0. It does
  not require healthy eligible terms or update Account.cash. Actual paidA→
  cancelled/uncertainB without a current eligible snapshot, repeated dedup and
  reviewed supported successor preserve original/hold rows and exact cash.
- Both functions flush all deferred constraints before their final authority
  read and advancing check; only in-memory result references follow the guard.
  Definers and all helpers are owned by existing safe `birja_migrator`, fixed
  `search_path=pg_catalog,public,pg_temp`, PUBLIC revoked transactionally, and
  scheduler has EXECUTE only on the two entry points. App/scheduler may SELECT
  payout rows but have no INSERT/UPDATE/DELETE or payout sequence privileges;
  scheduler Account.cash UPDATE remains denied.
- Bootstrap supports0014 while preserving prior0007–0013 dispatch. Before any
  role/ownership/grant change, exact four-function signatures, SHA256 bodies,
  owner, language, security mode, volatility, return mode/type, path and allowed
  ACL identity are checked. Trusted schema CREATE is refused. configure-db
  uses this same guard during inspection and application, so changed authority
  is refused rather than silently repaired. The existing immutability helper
  remains registered and is included in this exact identity manifest.

## Task Commits and TDD

1. Task1 RED `00fea31`: actual PostgreSQL has neither required narrow function;
   behavior assertion fails,1failed0.62s, not an import/collection failure.
2. Task1 GREEN `a68b853`: both authorities, private guard, actual producer
   integration and guarded isolated ownership fixture;31passed3.45s and scoped
   Ruff passed. No mocked successful financial mutation.
3. Task2 RED `96eecdf`: real rollback-only administrative bootstrap rejects
   current0014 as unsupported;1failed1.69s.
4. Task2 GREEN `6abeb69`: exact identity/bootstrap policy, stronger current
   semantic guards and direct-SQL tests;183affected tests passed23.19s,
   Ruff/format passed, Mypy82source files passed.
5. Fixture safeguard `84a69bf`: explicitly track historical fixture role
   creation and preserve an already provisioned canonical owner. Final183tests
   passed23.01s; no authority body changed after the green source commit.

Both tasks have observed RED followed by GREEN commits. No successful payment
or financial SQL result is stubbed. External source/calendar/review evidence in
tests is explicitly synthetic; one regression calls the actual existing
`derive_dividend_entitlements` producer and then the restricted SQL function.

## Verification Executed

All tests used existing `uv run --no-sync --no-cache`, the guarded owned tmpfs
test stack `birja-test` at55432/56379 and test-only identities. Test ledger and
role grants roll back. Administrative bootstrap proof runs inside one explicit
ROLLBACK, never installed production tooling.

| Gate | Actual result / evidence |
|---|---|
| Initial authority RED |1failed0.62s; `/tmp/birja-phase10-02-red.log` |
| Task1 actual SQL/producer GREEN |31passed3.45s; `/tmp/birja-phase10-02-task1.log` |
| Task2 bootstrap RED |1failed1.69s; `/tmp/birja-phase10-02-task2-red.log` |
| Initial corrected bootstrap |1passed1.49s; `/tmp/birja-phase10-02-task2-green.log` |
| Semantic authority/identity suite |40passed3.58s before final reconciliation test; `/tmp/birja-phase10-02-task2-all.log` |
| Final authority/schema/all affected migrations |183passed23.01s; `/tmp/birja-phase10-02-affected.log` |
| Real restricted SQL matrix |27app/scheduler/PUBLIC refusal operations;42501, plus exact bootstrap policy assertions |
| Exact identity tamper negatives |Security mode, PUBLIC grant, path, owner, volatility and altered body all refused |
| Scoped Ruff/format |PASS, all6changed Python files |
| Backend Mypy |PASS,82source files |
| Configure syntax / whitespace |`bash -n deploy/configure-db.sh`, `git diff --check`: PASS |

Version-specific primary references consulted: PostgreSQL18
[CREATE FUNCTION](https://www.postgresql.org/docs/18/sql-createfunction.html),
[numeric functions](https://www.postgresql.org/docs/18/functions-math.html) and
[advancing/timezone clocks](https://www.postgresql.org/docs/18/functions-datetime.html).
Context7/ctx7 were unavailable; no fallback package was installed.

## Deviations and Issues

- **[Rule2 — Explicit isolated migration prerequisite]** Parent extended test
  ownership to conftest and relevant migration fixtures. Ordinary test schemas
  are owned by the guarded test administrator, while production uses the real
  canonical migrator. A separate guarded test bootstrap preprovisions only
  the canonical nonprivileged NOLOGIN owner; migration never creates a role,
  grants membership or leaves a superuser definer. New financial tests grant
  that owner only required table reads, payout inserts/sequences and cash-column
  update inside their rollback transaction. Real restricted fresh/upgraded/TLS
  ownership proof remains plans05/06. Historical fixture teardown preserves any
  canonical owner it did not create.
- **[Rule1 — Producer compatibility]** Actual dividend revisions carry NULL
  verified_cutoff (that field is populated for splits); eligible snapshots
  carry `unit_epoch:N`. The new guard uses real retained calendar opening and
  historical journal semantics instead of incorrectly requiring a split field
  or inventing a fixed clock time. Actual producer→function regression passes.
- **[Rule3 — Historical moving-head fixture]** The restricted concurrent-index
  retry proof intentionally uses noncanonical `birja_action_retry_migrator`.
  Its moving head correctly failed0014's required canonical ownership. It now
  explicitly proves its original0013 boundary and restores head afterward;
  original refusal/retry/index assertions remain. Final183tests pass.
- Intermediate literal compilation errors (SQLAlchemy interpreting adjacent
  colon literals as binds), catalog `char` byte decoding and test setup errors
  were fixed before final verification. One added reconciliation test initially
  displaced an original replay assertion; it was restored to its own test and
  the entire affected suite rerun. No unresolved failure or authentication gate.
- Full requirements remain supported, not marked complete from infrastructure
  alone. Root owns canonical STATE/ROADMAP/REQUIREMENTS and later full-wave,
  independent review, retained archive/TLS, runtime services and owner gates.

## Threat Results and Stub Scan

- T-10-02-01 CLOSED for this scoped authority boundary: exact retained owner and
  historical quantity/terms, numeric vectors, append-only linked decisions,
  direct42501denials, shadow-object isolation and exact function tamper refusal.
- T-10-02-02 CLOSED for this plan: immutable original references, exact target
  identity/lineage, no-cash nullable uncertainty, stable dedup and replay without
  renewed credit. Retained recovery authentication follows04–06.
- T-10-02-03 CLOSED for this plan: one instrument then one Account transaction,
  fixed static queries with existing concrete indexes, no source I/O or retry
  loop under locks; owned tests rollback. Worker cycle limits are plan09.
- T-10-02-SC CLOSED: no package/image/lockfile/install change.
- The private helper is part of the planned C03 boundary, not an extra public
  endpoint; all four functions must enter exact producer/consumer identity proof
  in04. No unregistered API/auth/file-access surface was added.
- No TODO/FIXME, placeholder or payment success stub remains. Unknown fields in
  held decisions are intentional required uncertainty. Services, workers and
  mixed History consumers remain later plans, not claimed implemented here.

## Self-Check: PASSED

All8owned source/test/bootstrap files and this summary exist; all five listed
task commit hashes exist. Final183tests and scoped static checks actually pass.
No task commit deletes tracked files. Only scoped files are committed; unrelated
`.claude/`, canonical planning state and production remain untouched.

## Independent Authority Review Corrections

Independent review at576b667 found one blocker and one warning, reproduced
against actual PostgreSQL. The phase correctly stopped before Plan04. The
original review is retained in10-AUTHORITY-REVIEW.md; no clean re-review is
claimed by this executor. The following corrections supersede the initial
authority completeness claim until independent recheck accepts them.

- **CR-01 / Rule1 — Current calendar economic meaning.** Valid same-generation
  current calendar closure/coverage changes could contradict the stale derived
  session and eligible entitlement before both SQL guards. Full row equality
  between those guards did not reject a contradiction already present at entry.
  The private authoritative guard now requires the actual ex-date inside current
  admitted coverage and applies the matching exchange/date override: closed
  dates and either opening or closing mismatch refuse. Both initial and final
  post-constraint calls execute those same semantics; no cash/publication
  survives refusal. A matching legitimate shortened session can still pay.
  Tests explicitly call evaluate_admission and real build_sessions to establish
  that the reviewed payloads are legitimate and to compare their economic
  meaning. Current market opening/quotes/status are still not prerequisites.
- **WR-01 / Rule2 — Exact returned tuple identity.** Identical prosrc with a
  substituted TABLE output type/name/mode passed generic record-return checks.
  Bootstrap now pins proallargtypes, proargmodes and proargnames for all four
  functions, including each input name and every TABLE output column. These
  checks precede ownership/grant changes. Actual drop/recreate of APPLY with
  unchanged body and altered OUT type, name or mode is refused. Upcoming exact
  recovery proof must carry these full identities too.

Additional commits:

1. RED `edc0af8`: tracked current-calendar and returned-declaration regressions.
   Initial run6failed2.31s: closure/coverage and all three OUT substitutions
   reached actual missing-refusal assertions. The first shortened override
   fixture used a non-UTC serialized timestamp and failed admission setup; that
   failure is not counted as behavioral RED evidence. It was corrected to a
   legitimate UTC override before final verification. Additional valid cases
   cover changed opening, same-opening changed close, and matching shortened
   session success.
2. GREEN `4de3977`: both authority fixes and updated exact private-helper body
   hash. Final191affected tests passed24.25s,8existing pandas warnings; all49
   authority tests are included. Scoped Ruff/format, configure syntax and diff
   checks pass. No app module/dependency changed; prior Mypy82source pass applies.

Evidence: `/tmp/birja-phase10-02-review-red.log`,
`/tmp/birja-phase10-02-review-green.log` (7focused cases passed2.05s before the
matching shortened positive was added), and final
`/tmp/birja-phase10-02-review-affected.log`. Only the owned empty0014 disposable
schema was refreshed through Alembic. No production/provider/retained-tool/
publication action occurred. Root owns canonical state and independent recheck.

Review correction work took approximately8minutes after the new assignment;
the initial26minute plan evidence above remains historical rather than replaced.

### Review Correction Self-Check: PASSED

Both new commit IDs exist; the three corrected source/test/bootstrap files
and this updated summary exist. Final191test evidence and exact body/tuple
validation are actual runs; no tracked deletion was introduced. Independent
review report and unrelated `.claude/` are preserved and not staged here.
