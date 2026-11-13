---
phase: 10-dividend-cash-and-event-history
reviewed: 2026-11-13T16:07:41Z
depth: deep
diff_base: 5925b52
reviewed_head: 48d970c262c7f52bb5692d38db0748e5169cf389
files_reviewed: 73
files_reviewed_list:
  - .github/workflows/ci.yml
  - CLAUDE.md
  - backend/alembic/versions/0014_dividend_accounting.py
  - backend/app/api/v1/event_history.py
  - backend/app/api/v1/router.py
  - backend/app/db/dev_bootstrap.py
  - backend/app/models/__init__.py
  - backend/app/models/corporate_action.py
  - backend/app/models/dividend.py
  - backend/app/schemas/event_history.py
  - backend/app/services/dividend_rules.py
  - backend/app/services/dividends.py
  - backend/app/services/event_history.py
  - backend/app/tasks/dividends.py
  - backend/app/tasks/scheduler.py
  - backend/tests/conftest.py
  - backend/tests/dividend_fixtures.py
  - backend/tests/test_accounts.py
  - backend/tests/test_critical_coverage_config.py
  - backend/tests/test_dev_bootstrap.py
  - backend/tests/test_dividend_authority.py
  - backend/tests/test_dividend_concurrency.py
  - backend/tests/test_dividend_corrections.py
  - backend/tests/test_dividend_payments.py
  - backend/tests/test_dividend_rules.py
  - backend/tests/test_dividend_scheduler.py
  - backend/tests/test_dividend_schema.py
  - backend/tests/test_dividend_waits.py
  - backend/tests/test_event_history.py
  - backend/tests/test_event_history_api.py
  - backend/tests/test_event_history_cursor.py
  - backend/tests/test_history_api.py
  - backend/tests/test_history_service.py
  - backend/tests/test_migrations.py
  - backend/tests/test_portfolio_snapshot.py
  - backend/tests/test_scheduler.py
  - backend/tests/test_scheduler_loop.py
  - backend/tests/test_stock_action_migrations.py
  - backend/tests/test_stock_execution_migrations.py
  - backend/tests/test_stock_migrations.py
  - deploy/backup-manifest.sql
  - deploy/backup-snapshot.py
  - deploy/configure-db.sh
  - deploy/db/bootstrap-roles.sql
  - deploy/tests/dividend-execution-fixture.py
  - deploy/tests/ops-fixtures.py
  - deploy/tests/run-stock-browser.py
  - deploy/tests/stock-runtime-fixture.py
  - deploy/tests/test-ci-ops.py
  - deploy/tests/test-db-operations.sh
  - deploy/tests/test-deploy-prerequisites.py
  - deploy/tests/test-dev-bootstrap.py
  - deploy/tests/test-image-contracts.py
  - deploy/tests/test-restore-safety.sh
  - deploy/tests/test-stock-recovery-contracts.py
  - deploy/verify-restore.py
  - docker-compose.override.yml
  - docker-compose.yml
  - frontend/Dockerfile
  - frontend/e2e/dividends-history.spec.ts
  - frontend/e2e/portfolio-history.spec.ts
  - frontend/e2e/stock-actions.spec.ts
  - frontend/src/App.test.tsx
  - frontend/src/api/eventHistory.test.ts
  - frontend/src/api/eventHistory.ts
  - frontend/src/components/HistoryEventDetails.test.tsx
  - frontend/src/components/HistoryEventDetails.tsx
  - frontend/src/hooks/useEventHistory.test.tsx
  - frontend/src/hooks/useEventHistory.ts
  - frontend/src/hooks/useStockTrade.ts
  - frontend/src/hooks/useTrade.ts
  - frontend/src/pages/HistoryPage.test.tsx
  - frontend/src/pages/HistoryPage.tsx
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
resolved_findings:
  critical: 1
  warning: 0
---

# Phase 10: Independent Code Review Report

**Depth:** deep  
**Initial source:** `5925b52..a60a027` (application/image repair `6d95d19`, operational consumer repair `7196d5f`).  
**Affected re-reviews:** `a60a027..f47af65` (persistent RED `dd2ba3a`, fix `f47af65`); `f47af65..48d970c` (UI RED `db19cf5`, fix `48d970c`).  
**Status:** clean — CR-01 resolved; zero active blockers or warnings in the reviewed source.

## Narrative Findings (AI reviewer)

This is an independent reviewer-agent pass. Runtime implementation, migration
SQL, model constraints, worker discovery, private projection, client parser/auth
handling and recovery boundaries were inspected directly; changed tests and
operational fixtures were assessed for their behavioral assertions and setup
differences. The exact cumulative 73-file diff scope is retained above. Planning artifacts
are context, not counted as source files. No fallow structural pre-pass was
provided.

No tests, database stacks, provider calls or financial writes were executed by
this reviewer. Existing final gate results are evidence supplied by Plan 16,
not newly executed or independently reproduced test results. No behavioral RED
is claimed for this review-only work. No source file, branch or commit was
changed; the report is the only owned artifact.

### Affected re-review — CR-01 resolved

This same independent reviewer inspected all seven files in
`a60a027..f47af65`: the helper, its unit tests, both Compose commands, CI,
the CI policy test and the new actual ordinary-dev financial regression.
No additional source defect was proved. This is code-review closure of CR-01,
not completion of the phase's remaining full-suite/image/human gates.

The explicit `--after-migrations` mode in
`backend/app/db/dev_bootstrap.py:77` retains the shared dev-only URL/admin,
safe NOLOGIN/NOINHERIT role, all-seven-flags, bidirectional membership and
transaction/advisory checks. A missing post-migration owner refuses instead
of inventing one. `_authorize_dividends` at line 11 checks current database
and effective public-schema ownership, exactly one 0014 revision, all 15
fixed tables and two owned identity sequences, their identity dependencies,
and the four fixed function signatures/owners/security modes before the
first GRANT at line 56. Grants are confined to required SELECT, two INSERTs,
two sequence USAGE rights, Account UPDATE(cash) and schema USAGE for the
safe definer owner. No runtime role receives cash/table writes; no role
membership, production bootstrap, function body or migration is changed.

Both Compose startup commands now order prerequisite → migration → explicit
post-migration authorization → server. CI builds the actual repository
test-builder image before invoking `deploy/tests/test-dev-bootstrap.py`;
`deploy/tests/test-ci-ops.py:88` checks the presence and order of those stages.

Coordinator execution evidence was directly read, not rerun by this reviewer:

- `/tmp/birja-phase10-17-dev-repro.log` observes both ordinary fresh and
  0013-upgrade lanes with tables owned by `birja`, missing definer SELECT,
  and actual SQLSTATE 42501 at `stock_action_events`. Cash/rows remain
  unchanged and owned resources are cleaned. This confirms the initial
  source-traced diagnosis below.
- Persistent RED `dd2ba3a`,
  `/tmp/birja-phase10-17-dev-financial-red.log`, fails at the first expected
  original through the actual service with `DividendRefused`, before the
  fix introduced the post-migration CLI flag. It is a financial behavior
  failure, not a missing-option or fixture-import failure.
- GREEN `f47af65`,
  `/tmp/birja-phase10-17-dev-financial-green.log`, records fresh 19.287s and
  upgrade 21.117s. The actual regression uses the ordinary `birja` database
  connection without auxiliary migrator fixture grants, runs original,
  correction, uncertain hold, deduplication, reconciliation, worker,
  private History and immutable replay, and asserts cash 10004,
  starting cash 10000, one unchanged original and three decisions.
  Deliberately unsafe CREATEROLE, membership and foreign object owner states
  fail without being repaired; their expected refusal tracebacks in the
  GREEN log are followed by passing assertions and final resource cleanup.

The coordinator reports 29 focused cases, helper 44 statements/20 branches
at 100%, full backend static checks and 13 CI contracts passing. Those
counts are attributed to the coordinator. At this re-review boundary,
full backend and actual-recipe image/native/strict-scan runs were still
in progress; this report does not claim their completion. No long gates
were repeated by this reviewer.

### Resolved historical Critical Issue

#### CR-01 — BLOCKER, RESOLVED in f47af65: Ordinary dev startup provisions an unusable dividend definer owner

The following original finding describes `a60a027`, before the fix. Its
initial source-only provenance is preserved; actual RED/GREEN confirmation
and independent affected closure are recorded immediately above.

**File:** `/home/YokaiExchange/backend/app/db/dev_bootstrap.py:42-46`  
**Related:** `/home/YokaiExchange/docker-compose.yml:57`,
`/home/YokaiExchange/docker-compose.yml:76`,
`/home/YokaiExchange/docker-compose.override.yml:18`,
`/home/YokaiExchange/backend/alembic/versions/0014_dividend_accounting.py:374-393`,
`/home/YokaiExchange/backend/alembic/versions/0014_dividend_accounting.py:534-544`,
`/home/YokaiExchange/backend/tests/dividend_fixtures.py:53-90`.

**Issue:** The newly added ordinary dev startup sequence connects as the
`birja` PostgreSQL administrator, creates `birja_migrator` with NOLOGIN,
NOINHERIT and no object privileges, then runs Alembic using that same
`birja` connection. The tables and identity sequences consequently remain
owned by `birja`. Migration 0014 explicitly transfers the payout entry
points and private helpers to `birja_migrator`, but transfers neither the
underlying tables nor their required privileges.

`apply_stock_dividend` is SECURITY DEFINER: its first statement reading
`stock_action_events` and `stock_dividend_entitlements` therefore executes as
the empty `birja_migrator` role, even when the calling scheduler is the
`birja` superuser. A fresh ordinary dev installation cannot process an
otherwise valid locally prepared payout. The hold entry point has the same
problem when it first reads `stock_dividend_payments`.

**Expected/actual:** After the advertised local startup, a locally prepared
verified due entitlement should reach the retained financial authority and
publish once; the source-defined privilege state instead yields PostgreSQL
permission denial (42501), mapped by the service to
`financial_unavailable`, before authority evaluation. This is a
source-traced PostgreSQL permission conclusion, **not an observed execution
or a claimed reproduced RED**.

Default dev has corporate actions disabled, so disabled health/startup can
pass without exercising this defect. This finding does not allege that those
health checks failed, authorize activation or invent provider permissions.
The restricted production/ops path runs migrations with genuine migrator
ownership and is not shown defective. The financial tests explicitly add the
missing grants in their fixture, so their successful calls do not establish
the ordinary Compose path's permissions.

**Fix:** Complete the guarded local-only setup after migrations, or migrate
under a properly provisioned local owner. Keep the fixed definer owner,
NOLOGIN/NOINHERIT attributes, runtime cash restrictions and frozen 0014 SQL
unchanged. For the grant-based option, validate the same local administrator,
database, safe role and expected object ownership, then grant only:

- SELECT on `stock_action_events`, `stock_action_revisions`,
  `stock_action_observations`, `stock_action_resolutions`,
  `stock_action_state`, `stock_instruments`, `coins`,
  `stock_data_admissions`, `stock_sessions`,
  `stock_ownership_movements`, `stock_split_applications`,
  `stock_dividend_entitlements`, `stock_dividend_payments`,
  `stock_dividend_decisions` and `accounts` to the safe definer owner;
- INSERT on the two payout tables, USAGE on their two identity sequences,
  required schema USAGE, and UPDATE(cash) on `accounts` to that owner.

Do not grant scheduler direct cash/table writes, make the owner a superuser,
add role memberships, or silently repair unsafe existing roles. A regression
must exercise the actual fresh and populated ordinary dev startup and an
actual synthetic due payout/hold without the test fixture's auxiliary
migrator grants. Assert exact cash/row counts, repeat-call idempotency and
unsafe-owner refusal. The coordinator controls any stack reproduction and
source ownership expansion.

### Other reviewed boundaries

No additional defect was proved in these boundaries. These are trace notes,
not substitutes for the separate broader acceptance gates.

| Boundary | Direct source/evidence reviewed |
| --- | --- |
| Exact financial target | `backend/app/services/dividend_rules.py:60` and migration `0014_dividend_accounting.py:411` compute exact quantity × rate, explicit half-even cents and target minus original plus applied deltas. Unknown terms have no fabricated amount; held proposals are excluded from cumulative cash. |
| Immutable accounting and replay | Migration `:396`, `:448`, `:500`, `:989` and `backend/app/models/dividend.py`: original and successful-target replay precede current authority; composite owner/event/revision/entitlement FKs, immutable triggers, applied-target and NULL-safe held-status indexes preserve lineage. Empty-only downgrade refuses populated state before destructive DDL. |
| SQL privilege boundary | Migration `:134`, `:374`, `:493`, `:534`; `deploy/db/bootstrap-roles.sql:50`: fixed signatures, static schema-qualified statements, pinned search path, revoked PUBLIC EXECUTE, scheduler-only entry-point EXECUTE and exact input/output/body metadata checks. CR-01 concerns the separate ordinary dev owner's missing underlying rights. |
| Waits and transaction ownership | Migration `:392`, `:473`, `:523`; `backend/app/services/dividends.py:45`: instrument gate → Account lock, SET CONSTRAINTS → final full retained-row/rights check using advancing clock → return/commit. `test_dividend_waits.py:143` uses observed actual blockers; the deferred test trigger is explicitly synthetic synchronization. |
| Uncertainty and corrections | Migration `:493`, `backend/app/tasks/dividends.py:48`, `test_dividend_corrections.py:30`: paid anchors are independently discoverable with no current eligible target; no-anchor uncertainty creates no Dividend; uncertainty carries zero applied effect, deduplicates and can link a later verified successor. |
| Worker bounds and fairness | `backend/app/tasks/dividends.py:20`, `:72`, `:93`: two independent retained keysets, 50 candidates each, common 100-candidate/40-second cycle, interleaving, advance before attempt and independent wrap. Actual wait/cancellation and 105-owner assertions are in `test_dividend_scheduler.py`. |
| Owner privacy and pagination | `backend/app/services/event_history.py:150`, `:274`; `backend/app/api/v1/event_history.py:26`: all UNION branches filter owner before seek/lookahead, the complete time/rank/BIGINT tuple orders pages, and offpage originals are joined with the owner. No client-supplied owner enters the service. Legacy history/cursor v1 remains separate. |
| Exact wire compatibility | `backend/app/schemas/event_history.py`, `backend/app/services/event_history.py:239`, `frontend/src/api/eventHistory.ts`, `backend/tests/test_event_history.py:164`: exact decimal/string identities, correction lineage and nullability; Fraction reduction emits retained 1.5:1 as 3:2, with an actual DB-page → installed TS-parser assertion. Existing supported ratio components are bounded in `corporate_action_rules.py:175`. |
| Auth lifecycle and authoritative cash refresh | `frontend/src/hooks/useEventHistory.ts:15`, `:58`, `:82`; trade hooks: owner/epoch and query-object guards discard late data, synchronous auth subscription removes old pages, cancel precedes authoritative invalidation, and no optimistic cash is derived from History. Hook tests cover same-owner relogin, old-owner 401 and cancellation settlement. |
| Focus and displayed cash | `frontend/src/pages/HistoryPage.tsx:53`, `:89`; `frontend/src/components/HistoryEventDetails.tsx:47`, `:194`: applied versus proposed cash is explicit; loaded original focus and bounded inline original/back behavior; native disabled-button blur intent is preserved. UI source checks do not establish native 200% owner acceptance. |
| Recovery producer/consumer | `deploy/backup-snapshot.py:124`, `:202`, `:241`, `:514`; `deploy/verify-restore.py:931`, `:951`, `:1038`: exact declarations/bodies/owners/ACLs/role flags/membership/schema/trigger identity precede fixed reconstruction, restore quarantines payout EXECUTE, and sequence/row identities cover both new ledgers. Earlier revision SQL has explicit byte-compatibility assertions. |
| CI and proof scope | `.github/workflows/ci.yml:47`, `:297`, `backend/tests/test_critical_coverage_config.py`, `deploy/tests/test-ci-ops.py`: branch coverage and all 47 critical modules are mirrored; final ops uses one checksum-pinned archive and checks current CORE/unit bytes between stages. Current 0014 retained/current-service recovery is distinct from actual selected cutover/old-app rollback at 0008. |

### Evidence and limits

The coordinator supplied the already completed final gates: backend 2550,
critical statements/branches 100%, frontend 697, browser 49 plus one explicitly
expected CSP skip, SQL contracts 23, and six same-archive operational stages.
Their logs and scope are recorded in `10-16-SUMMARY.md` and
`10-LOCAL-PROOF.md`; this review did not rerun them. They do not test away the
different ordinary dev ownership state originally identified in CR-01.
The later dedicated actual-dev regression addresses that distinction as
recorded in the affected re-review above.

Read context included AGENTS/CLAUDE/adapter/reviewer/selected review workflow,
project/requirements/roadmap/state, Plan 17, C01–C06 including C03a/C05a,
PATTERNS, Plan 16 summary and local proof. Relevant predecessor ownership,
corporate-action classification and replay contracts were cross-referenced.
W01–W08 accepted debt and Phase 7/8 live/publication deferrals were not reopened.

Native 200% browser zoom, owner acceptance of the new mixed History and future
live activation remain separate pending outcomes. No assertion here completes
those requirements or authorizes production/publication work.

_Reviewer: independent gsd-code-reviewer agent_  
_Initial review: 2026-11-13T15:33:46Z; affected re-review: 2026-11-13T15:48:32Z_

## Coordinator reproduction — after the independent review

The parent authorized guarded ordinary-dev reproduction. Both **fresh** and
**0013→0014** ordinary Compose lanes actually constructed a synthetic verified
due entitlement through the existing retained fixture/producer, without its
auxiliary migrator grants, then called the real payout function as ordinary
Compose user`birja`. Both observed`42501: permission denied for table
stock_action_events`; table owner was`birja` and definer SELECT was false.
Cash, starting_cash10000 and zero payout/decision row counts were unchanged.
This confirms CR-01; it does not downgrade the original independent finding.

Command:`python3 /tmp/birja-phase10-17-dev-repro.py`; actual evidence
`/tmp/birja-phase10-17-dev-repro.log:39–44,123–128`. The harness exits0 because
it asserts the defect, **not** because the financial path passed. The initial
sandbox Docker refusal ran no stack; authorized escalation executed the two
lanes. All owned fresh/upgrade containers/networks/volumes were removed and
checked absent. No provider, production, real environment or financial authority
change occurred. This historical reproduction preceded the approved dev-only
repair and affected independent re-review recorded above. CR-01 is now resolved
in f47af65; the original failure and actual execution provenance remain preserved.

## Independent affected UI re-review — 2026-11-13T16:07:41Z

**Source:** all three changed files in `f47af65..48d970c`:
`frontend/e2e/dividends-history.spec.ts`,
`frontend/src/pages/HistoryPage.tsx` and
`frontend/src/components/HistoryEventDetails.tsx`. These files were already
in the cumulative 73-file scope above. **Result: zero new blockers/warnings.**

The final-completion focus change at `HistoryPage.tsx:293` permits native
scrolling only inside the existing recorded append-intent, same-owner and
same-session-epoch checks. The active element must still be the initiating
button or the body after native disabled-control blur. Moving focus to another
control prevents completion focus transfer; a background refresh supplies no
append intent. Intent is cleared after evaluation. Retry and non-final append
focus logic remains unchanged. The source therefore fixes the offscreen final
focus without widening owner/session access or introducing unconditional focus
stealing. Existing tests explicitly cover native blur, background refresh,
focus moved elsewhere and immediate logout removal of inline originals.

The four `gap-3` → `gap-4` changes and cash `font-medium` change alter spacing
and emphasis only. No event parsing, financial value, auth guard, query key,
server authority or dependency changes occur in this diff.

Directly inspected coordinator browser evidence:

- RED `db19cf5`,
  `/tmp/birja-phase09-browser-nnh4g3e4/browser-dividends.log`, fails the actual
  focused element's bottom bound: 3616 versus viewport height 900. This is
  real offscreen focus, not merely DOM focus or a missing test import.
- GREEN `48d970c`,
  `/tmp/birja-phase09-browser-sp2l4ank/browser-dividends.log`, passes the one
  targeted mixed-page browser journey. Runner
  `/tmp/birja-phase10-17-ui-focus-green.log` reports 40.2s for that stage and
  successful owned-resource cleanup. The regression checks x/y/right/bottom
  bounds and mobile fixed-nav clearance, including retry at desktop and
  repeated genuine append completion at 320, 375, 768, 1024 and 1440 widths;
  the narrower repeat loop also checks no horizontal page overflow.

The coordinator reports 29 component/page tests, full 697 frontend tests,
98.37% statements/94.82% branches, static checks and build passing. This
reviewer did not rerun those commands. At this review boundary the newly
frozen full browser run was still running; no completion is claimed here.
The later full UI re-audit, refreshed evidence packet and owner/native 200%
acceptance remain separate. Original CR-01 and its resolved RED/GREEN history
remain preserved above. No source, test, stack or commit was modified by
this reviewer; only this report changed.

