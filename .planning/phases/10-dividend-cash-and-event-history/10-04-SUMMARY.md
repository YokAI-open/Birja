---
phase: 10-dividend-cash-and-event-history
plan: "04"
subsystem: recovery
tags: [postgresql, retained-recovery, dividend, authority, quarantine]
requires:
  - phase: 10-02
    provides: Reviewed0014 schema, narrow SQL definers and exact bootstrap identities
provides:
  - Exact0014 original/decision columns, sequences, schema and financial authority inventory
  - Independent full-function declaration and safe-role authentication before clone grant reconstruction
  - Quarantined runtime SELECT with all dividend execution and write capabilities withheld
  - Actual legacy SQL compatibility and0014 data/schema/authority corruption proof
affects: [10-05, 10-06, 10-07, 10-10, 10-16]
tech-stack:
  added: []
  patterns: [independently-pinned-authority, source-role-isolation, no-acl-to-quarantine]
key-files:
  created: []
  modified:
    - deploy/backup-snapshot.py
    - deploy/verify-restore.py
    - deploy/backup-manifest.sql
    - deploy/tests/test-stock-recovery-contracts.py
key-decisions:
  - Authenticate exact declarations, bodies, owners, role flags and memberships before any clone grant changes; never normalize corrupted source authority into acceptance.
  - Restore runtime SELECT only and explicitly revoke PUBLIC/app/scheduler execution of all four dividend functions, including default PUBLIC privileges from no-ACL restoration.
  - LOGIN intentionally differs across production, test and clone roles; six security flags and canonical role isolation remain invariant.
requirements-completed: []
requirements-supported: [DIV-04, DIV-05]
duration: interrupted multi-session execution; measured test timings below
completed: 2026-11-13
---

# Phase 10 Plan 04: Exact Dividend Recovery Contracts Summary

**Retained0014 manifests preserve immutable dividend lineage and independently
authenticate SQL/role authority before reconstructing a quarantined read-only
financial runtime.**

## Performance and continuation

- Tasks2/2 complete across the original session and a continuation after interruption.
- Four implementation/test files modified; no dependency or image changes.
- Final SQL-enabled suite:19executed,19passed,0skipped,91.580seconds.
- Final offline suite:19discovered,15executed/passed,4explicit SQL skips,
  0.374seconds. Offline skips do not constitute SQL evidence.
- No trustworthy total active duration was recorded across the interruption;
  individual actual test durations are retained instead of an invented total.

## Accomplishments

### Task1 — producer dispatch and exact retained state

- Added0014 explicit dispatch with26tables and19identity sequences. Both new
  financial tables retain every saved original/decision field, zero original,
  NULL uncertain terms, predecessor/application references and stable hold identity.
- Pinned complete schema and55validated foreign keys, indexes, constraints,
  sequence structure and all enabled triggers. Schema SHA256 is
  `691aaca6ec9c3e386910b55849091cdaa989345bb16f177f92dc478ccee2e247`;
  execution/dividend trigger SHA256 is
  `94a79eff11bd9d0db43a2d2ad38c69cda7a6a012e42f1f8a6e9291dca72c2aef`.
- Independently pin all four0014 functions: both definer entry points, private
  invoker authority helper and immutable trigger helper. Validation covers body
  SHA256, complete input/output types/names/modes, owner, path, language, security
  mode, set-returning behavior, volatility and other execution attributes/ACLs.
  A supplied manifest cannot select its own trusted body or declaration.
-0014 additionally records the canonical app/scheduler/migrator security flags
  and role memberships. Privileged or inheriting roles and any membership edge
  into/out of those roles are refused; this also excludes transitive SET ROLE
  escape paths. LOGIN is deliberately excluded from this invariant.
- All generated0007–0013 manifest and schema-guard SQL remain byte-equal to
  planning baseline5925b52, independently compared in this continuation. Existing
  raw SQL gains documentation comments only; its generated legacy queries retain
  their exact contracts. Hash log:
  `/tmp/birja-phase10-04-legacy-query-hashes.log`.

### Task2 — authenticate before narrowly reconstructing clone permissions

- Source manifest validation occurs before consuming its retained dump. Clone
  restoration authenticates the known no-ACL function state, exact owner/schema/
  triggers and isolated safe roles before changing any grants.
- Expected pg_restore PUBLIC EXECUTE defaults are explicitly revoked from all
  four functions. Neither app nor scheduler receives payout/hold/helper execution,
  direct financial-table writes or sequence privileges; fixed SELECT only is
  reconstructed. Final quarantine identity is checked again.
- Unexpected source declarations, bodies, owners, ACLs, security role flags or
  memberships cannot be repaired into validity. New runtime roles may be created
  with the fixed safe clone attributes only after independent authentication.
- Existing0012/0013 authority paths remain revision-selected.0014 verification
  compares all data hashes, financial totals, complete schema and next identities,
  with only the deliberate function-ACL quarantine transformation permitted.

## Commits and observed RED/GREEN

1. Task1 RED `9feca5b`: actual dispatch assertion refused absent0014 support;
   `/tmp/birja-phase10-04-red.log`.
2. Task1 GREEN `b6184e3`: explicit dividend producer/state/authority contracts.
   Original offline run discovered15cases:12passed and3SQLskipped0.044s;
   actual catalogue probing is superseded by the final SQL-enabled suite below.
3. Task2 RED `23973ad`: clone-authentication assertion failed before the consumer
   existed; `/tmp/birja-phase10-04-clone-red.log`.
4. Additional concrete security RED `1ba1300`: a NOINHERIT app member could SET ROLE
   to the definer owner and the consumer failed to refuse it. Actual rollback-only
   proof:1failed30.808s, `/tmp/birja-phase10-04-membership-red.log`.
5. Task2 GREEN `68882db`: authenticated/quarantined consumer, shared source/clone
   role isolation, explicit fixed grants and actual corruption/denial tests.

Continuation verified the existing commits/partial files and resumed Task2 rather
than restarting Task1. Parent owns canonical STATE/ROADMAP/REQUIREMENTS updates;
no whole-phase requirement was marked complete by this infrastructure plan.

## Actual verification

| Gate | Result/evidence |
|---|---|
| Final legacy+0014 SQL contracts |19passed,0skipped91.580s; `/tmp/birja-phase10-04-final-global-roles.log` |
| Final offline contracts |15passed,4explicit SQL skips0.374s; `/tmp/birja-phase10-04-role-offline.log` |
| Initial resumed0014 SQL probe |1passed31.265s; `/tmp/birja-phase10-04-resume-postgres.log` |
| Clone membership behavioral RED |1failed30.808s; `/tmp/birja-phase10-04-membership-red.log` |
| Initial membership guard GREEN |1passed29.984s; `/tmp/birja-phase10-04-membership-green.log`; superseded by final source+clone suite |
| Legacy query bytes vs5925b52 |All7revision manifest/schema-guard pairs equal; independent generated-query hash log above |
| Python syntax |py_compile passes for producer, consumer and test script |
| Scoped lint |Existing standalone deploy convention: Ruff F checks pass for all3Python files |
| Whitespace/deletion review |git diff --check passes; no tracked deletion |

The realSQL suite changes original amounts, historical cash, decision status/
lineage, next sequences, nullable columns, FK/unique-index/trigger definitions,
table/column/sequence privileges and all four function owner/body/path/security/
volatility/ACL/declaration identities. It proves strict producer refusal and
consumer refusal before grant repair where applicable, and exact-data mismatch
refusal against the retained expected state.

Storage fixtures deliberately represent a zero original, NULL-terms hold and
separate applied successor. They exercise retained rows/hashes, not provider
authorization or economic payout proof (Plan02/05 own real entry-point calls).
The live consumer probe executes its actual statements on a persistent rollback-
owned PostgreSQL connection; only the subprocess transport is adapted. Both
runtime roles encounter insufficient_privilege for both public entry points,
the private helper, direct cash UPDATE and both financial-table INSERTs:
12real denials. Direct app/scheduler membership and an intermediate-role chain
are independently shown SET-capable and refused before clone grant changes.

All SQL targets only guarded `docker-compose.test.yml` project `birja-test`.
No dev/prod database, provider key, .env, private provider/B2 call, package install,
timer, installed recovery tool, deployment or publication was accessed/changed.

## Deviations and issues

1. **[Rule3 — Interrupted test transport]** The persistent psql test adapter needed
   a final statement terminator before its completion sentinel. The interrupted
   session left that fix in the partial test; continuation verified it with the
   actual0014 and full suites. This was a harness issue, not a claimed financial
   application failure.
2. **[Rule2 — Missing critical role isolation]** Final inspection found that
   NOINHERIT alone does not disable SET ROLE. Parent authorized a bounded actual
   reproduction and source/clone boundary extension. Shared0014-only role metadata
   now enforces canonical bootstrap isolation before grants; tests cover direct
   and transitive escapes plus source role-flag/membership corruption. No unsafe
   membership is silently removed. PostgreSQL18 GRANT documentation confirms
   that membership SET and INHERIT options are distinct:
   https://www.postgresql.org/docs/18/sql-grant.html.
3. A temporary standalone legacy-byte comparison initially used a copied module
   without its adjacent SQL template; it was corrected to load both baseline
   files. A syntax-check invocation initially used root-relative paths from
   backend; the corrected root invocation passed. Neither tooling invocation is
   counted as a successful test or application failure.

## Threat results and readiness

- T-10-04-01: CLOSED for this plan by independently pinned source/clone function,
  schema, grant and role identities, corruption refusal and12actual runtime denials.
- T-10-04-02: CLOSED for retained state by complete saved rows, lineage and
  identity preservation; synthetic storage fixtures are explicitly labelled.
- T-10-04-03: CLOSED for this scope by fixed catalogue/function inventories,
  existing bounded tooling, statement timeouts and rollback-owned cleanup.
- T-10-04-SC: CLOSED; no dependency, image, installation or lockfile change.
- No TODO/stub or fake financial success was introduced. Deliberate unknown
  retained terms remain NULL under the frozen contract, not placeholder data.

Ready for Plan05 actual restricted SQL/TLS fixtures and Plan06 exact retained
encrypted archive proof. Those gates have NOT run in this plan and remain
blocking before financial runtime consumers07/10. Final current-service recovery,
same-archive replay/rollback, browser/full-phase reviews and owner acceptance
remain later plans. Existing live provider/production/publication deferrals stay.

## Self-Check: PASSED

All four source/test paths and all listed RED/GREEN commits exist. Final19/19
SQL contracts and scoped checks pass. No tracked file deletion, package install,
canonical-state update or unrelated `.claude/` modification occurred. Parent
should independently review this recovery boundary before advancing consumers.

## Independent review correction — fresh owner CR-01

The independent recovery-contract review found one BLOCKER in the actual
`restored()` entry path: creating a missing migrator omitted NOINHERIT, so
PostgreSQL supplied inheritance=true and the new0014 pre-grant role validator
correctly rejected the otherwise valid fresh restore. The earlier consumer
probe began after safe source bootstrap and therefore did not cover this entry
condition. The original19/19 results above remain historical evidence, not proof
that this fresh-owner path was correct.

- Behavioral RED `ff10840`: two regressions invoke real `restored()`, capture
  its emitted role-creation and role-check statements, and execute those exact
  statements on fresh rollback-only test aliases. The actual created flags are
  passed to the real0014 pre-grant validator. A valid fresh entry failed there,
  and an unsafe pre-existing alias reached database creation before refusal:
  one failure/one error2.202s, `/tmp/birja-phase10-04-fresh-owner-red.log`.
- GREEN `03f912d` makes new migrator creation explicitly LOGIN NOINHERIT,
  NOSUPERUSER, NOCREATEDB, NOCREATEROLE, NOREPLICATION and NOBYPASSRLS. Its immediate
  existing-owner guard now includes inheritance. No ALTER ROLE or unsafe-owner
  repair is introduced; an unsafe existing owner is refused before CREATE DATABASE.
- Focused actual-entry SQL GREEN:2passed2.345s,
  `/tmp/birja-phase10-04-fresh-owner-green.log`.
- Final affected SQL suite:21executed/21passed/0skipped91.538s,
  `/tmp/birja-phase10-04-fresh-owner-all-sql.log`.
- Final offline suite:21discovered/15executed passed/6explicit SQL skips0.039s,
  `/tmp/birja-phase10-04-fresh-owner-offline.log`.
- Python syntax, scoped Ruff F and whitespace checks pass. Only the verifier,
  recovery-contract tests and this summary changed for the review correction.

The role probes replace only the fixed canonical role name with a test alias;
they never drop/alter the existing canonical owner. Alias creation and flags are
actual PostgreSQL behavior in owned `birja-test`. Archive operations and clone
database creation are transport-adapted in this focused test, so this is not a
claim of full retained-archive/TLS restoration. Plans05/06 remain mandatory.
No producer query or0007–0013 manifest/schema-guard bytes changed. Independent
recheck of this correction remains the parent's gate before advancing Plan05.
