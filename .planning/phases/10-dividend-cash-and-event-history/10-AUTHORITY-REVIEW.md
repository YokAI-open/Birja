---
phase: 10-dividend-cash-and-event-history
reviewed: 2026-11-12
depth: deep
scope: Plan10-02 narrow financial SQL boundary before retained recovery consumers
reviewed_head: 6f60ce48165a9613e471f67d03414540c6a95b24
original_review_head: 576b667
files_reviewed: 8
files_reviewed_list:
  - backend/alembic/versions/0014_dividend_accounting.py
  - backend/tests/test_dividend_authority.py
  - backend/tests/conftest.py
  - backend/tests/test_stock_migrations.py
  - backend/tests/test_migrations.py
  - backend/tests/test_stock_action_migrations.py
  - deploy/db/bootstrap-roles.sql
  - deploy/configure-db.sh
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  critical: 1
  warning: 1
status: clean
---

# Phase10 Plan02 financial authority review

## Narrative Findings (AI reviewer)

**Independent recheck: clean at6f60ce4.** Both originally reproduced findings
below are resolved by4de3977, with behavioral RED evidence inedc0af8. No
remaining finding was identified in this bounded authority recheck. Historical
reproduction and original severity are preserved below rather than erased.

### Resolution and independent recheck evidence

- **CR-01 resolved:** The same private guard called initially and after all
  constraint waits now requires ex-date within current calendar coverage and
  applies the matching authoritative exchange/date override. Closed overrides
  and either opening or closing contradiction refuse without a financial
  effect. A correctly matching shortened session remains accepted. These
  checks do not add an open-current-market or live-quote requirement.
- **WR-01 resolved:** Before any role/ownership/grant change, bootstrap now
  pins full `proallargtypes`, `proargmodes` and `proargnames` for all four
  functions. The private-helper body pin matches its updated guard. Input
  names and TABLE output names/types/modes are authenticated; unchanged-prosrc
  substitutions of OUT type, name and mode are refused.
- Independently read the source/bootstrap/test diff through6f60ce4 and the
  Plan02 summary correction appendix. Then ran actual tracked cases on owned
  disposable `birja-test`: `uv run --no-sync --no-cache pytest
  tests/test_dividend_authority.py -q -k 'current_admitted_calendar or
  altered_out_declaration or acl_bootstrap_accepts_exact'` from `backend`.
- Actual result: **9passed,40deselected,8existing pandas warnings,2.45s**;
  `/tmp/birja-phase10-authority-review-recheck.log`. Includes four legitimate
  admitted-calendar refusal cases, matching shortened-session success,
  three changed-OUT-declaration refusals and the real exact-bootstrap positive.
- No source, tracked test, state or production edits and no commit were made
  during recheck. Broader191-test executor evidence is retained separately;
  this independent recheck does not claim to have repeated it. Planned
  recovery/restricted-role/TLS gates remain required before consumers.

Independent bounded cross-file review of the new SQL apply/hold/helper boundary,
its bootstrap identity guard, and changed migration test fixtures. Existing
ownership reconstruction, dividend entitlement producer, admission/calendar
rules and C01–C04 contracts were traced as context. Prior Plan01 review remains
separate. Planned worker, retained recovery and TLS work is not reported as
missing implementation.

Two findings were reproduced using actual PostgreSQL and scheduler-role calls
on the guarded disposable `birja-test` stack. External evidence is synthetic;
successful financial calls are real. All test changes and DDL/data mutations
were inside rollback-only fixtures/savepoints. Only the temporary probe file
`/tmp/test_phase10_authority_review.py` and this report were written; no source,
tracked test, canonical state or production file was edited. No production,
provider, B2, timer, deployment or publication action occurred.

## Resolved Critical Issues — historical reproduction

### CR-01 — BLOCKER, resolved: Current calendar closure does not invalidate the retained cutoff

**File:** `backend/alembic/versions/0014_dividend_accounting.py:283`

**Related:** same file lines309–318;
`backend/app/services/corporate_action_rules.py:195`;
`backend/app/services/stock_sessions.py:72`.

**Issue:** The authority checks calendar override JSON shape, then accepts an
eligible entitlement when its cutoff matches the cached `stock_sessions`
opening and generation. It never applies the current authoritative overrides
to that opening. A valid reviewed calendar payload can close the dividend's
ex-date while the old derived session and retained eligible snapshot remain.
If the payload changes without incrementing generation, both the first and
final SQL guards accept the already-closed date and credit cash. Comparing full
rows only between those two guards cannot reject a contradiction already
present before the call.

This is not a need for the current market to be open: the historical ex-date
cutoff itself no longer has current calendar authority. The actual calendar
producer applies the override and produces `opens_at=None`, and
`dividend_cutoff` would therefore return no verified cutoff. The SQL boundary
must independently refuse that stale retained target before an append/cash
effect, without depending on the worker first regenerating entitlements.

**Observed reproduction:** Keep all original admission fields and scope intact;
replace the calendar's overrides with one official-source `XNAS`/ex-date
`state=closed` override, preserving generation. The normal
`evaluate_admission(...,"calendar","derived",now)` accepts the complete
payload. Actual `build_sessions` returns `opens_at=None` for that date. Yet
the scheduler's real `apply_stock_dividend` returns `original` and changes
cash from100 to101.

**Fix:** In the authoritative SQL guard, resolve the current calendar override
for the instrument exchange/ex-date and require the retained cutoff/session to
agree with its actual economic meaning; explicitly reject a closed date and
inconsistent shortened-session opening. Also enforce relevant horizon/date
provenance rather than treating derived generation equality as calendar
authority. Retain final full-identity/advancing-time validation. Add actual SQL
negatives for valid same-generation closure and changed calendar coverage,
including no original/decision/cash effect. Keep the producer comparison to
demonstrate the payload is legitimate and the disagreement is real.

## Resolved Warnings — historical reproduction

### WR-01 — WARNING, resolved: Exact function preflight omits the returned tuple identity

**File:** `deploy/db/bootstrap-roles.sql:63`

**Issue:** `to_regprocedure` authenticates input argument types, while the
return check only requires generic PostgreSQL `record`. The body hash does not
include the CREATE FUNCTION declaration. Consequently altered TABLE/OUT
types, names or modes can pass the advertised exact four-function identity
preflight. This admits a substituted runtime contract before role/grant
application even though the financial call is unusable. The role's own
privileges remain restricted; this is an identity-validation/availability gap,
not an observed privilege escalation or committed cash corruption.

**Observed reproduction:** Drop/recreate APPLY in a rollback-only savepoint,
with its exact original `prosrc`, owner, security mode, path, volatility and
ACL, changing only `RETURNS TABLE(payment_id bigint,...)` to
`RETURNS TABLE(payment_id text,...)`. The real `DO $dividend_identity$` block
passes. A fresh distinct prepared scheduler call then fails with SQLSTATE42804
(`structure of query does not match function result type`); no payment/cash
effect survives.

**Fix:** Pin and compare `proallargtypes`, `proargmodes` and `proargnames`,
including all TABLE output columns, plus the expected input parameter names
where body references rely on them. Keep these checks before any ownership or
grant changes and carry the same exact tuple into forthcoming retained
producer/consumer identity validation. Add altered OUT type/name/mode negatives;
the existing body/security/owner/path tests do not cover this declaration.

## Verification and limits

- Final command: `uv run --no-sync --no-cache pytest -c pyproject.toml -p
  tests.conftest /tmp/test_phase10_authority_review.py -q -s`, from `backend`.
- Final result: **2passed,4existing pandas warnings,1.57s**.
- Log: `/tmp/birja-phase10-authority-review-repro.log`.
- An initial OUT-tamper probe reused an asyncpg prepared statement and reached
  its schema-cache invalidation error first. The final probe uses a distinct
  statement and observes the actual42804 function result mismatch. No
  application retry behavior was changed.
- No additional demonstrated cash replay, half-even, lock-order, private-helper
  invocation, mutable caller JSON, schema-shadowing or fixture-owned-role
  deletion defect was identified in this bounded pass. This does not replace
  the planned fresh/upgraded restricted-role, TLS, exact retained recovery,
  final concurrency or whole-phase security gates.
- Original result `outcome=original` with a null decision reference is the
  documented SQL contract; it requires explicit mapping in later typed service
  consumers and is not itself a review finding.

_Reviewer: independent gsd-code-reviewer sub-agent; no commit created._
