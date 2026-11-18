---
phase: 13-create-and-compare-independent-strategies
plan: "03"
reviewed: 2026-11-18T08:48:37Z
initial_reviewed: 2026-11-18T08:39:05Z
depth: standard
diff_base: 00d787d
diff_head: aa25d81
initial_diff_head: 7295c52
repair_diff_base: 7295c52
files_reviewed: 8
files_reviewed_list:
  - backend/app/db/schema_contract.py
  - backend/app/db/portfolio_migrate.py
  - backend/app/db/dev_bootstrap.py
  - backend/app/db/portfolio_bootstrap.py
  - deploy/db/bootstrap-roles.sql
  - backend/tests/test_portfolio_management_admission.py
  - backend/tests/test_portfolio_management_grants.py
  - backend/tests/portfolio_fixtures.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  critical: 2
  total: 2
status: clean
---

# Phase 13 Plan 03: Code Review Report

**Reviewed:** 2026-11-18T08:48:37Z  
**Depth:** standard  
**Files Reviewed:** 8  
**Status:** clean — both initial blockers resolved

## Summary

Initial review covered all eight changed source/test files in `00d787d..7295c52` and established two blockers. Independent re-review of the complete repair range `7295c52..aa25d81` finds both resolved, with no remaining BLOCKER or WARNING. The original findings below are retained as historical evidence and are not active findings.

## Narrative Findings (AI reviewer)

## Repair Dispositions

- **CR-01 — Resolved:** Shared preflight now rejects every rewrite rule attached to a public relation (`portfolio_bootstrap.py:279-281`); production preflight carries the same refusal (`bootstrap-roles.sql:240-242`). The check does not depend on rule name, event or enabled state, so both enabled and disabled versions of the reported rule refuse before authorization or write dispatch. The added real PostgreSQL test exercises authenticated app admission, shared preflight and actual production psql bootstrap, then asserts unchanged account counts/cash and an empty creation journal.
- **CR-02 — Resolved:** Shared preflight explicitly rejects app/scheduler/migrator/operator ownership of the current database or public schema and checks effective public CREATE for app and scheduler (`portfolio_bootstrap.py:282-295`). Production mirrors those checks (`bootstrap-roles.sql:243-256`). Tests prove implicit effective CREATE for both runtime database owners, require authenticated runtime/shared/production refusal, restore ownership in `finally`, and retain positive cases for administrative and `pg_database_owner` schema ownership.

The repair only adds preflight guards; frozen 0017 contract literals, migration sources and both existing catalogue/ACL hash constants are unchanged by the repair diff. The implementation summary records RED `d026a71` (eight reproduced failing cases), GREEN `5f5d087`, 12 focused passing cases and 90 affected regression passes. These are implementation execution receipts, independently inspected here as test code and recorded evidence rather than rerun. No additional unresolved defect was established in this focused repair review.

## Initial Critical Issues — Resolved History

### CR-01: BLOCKER — Rewrite rules can alter grants without changing either pinned fingerprint

**Disposition:** Resolved by `5f5d087`; original severity and initial-source evidence retained below.

**File:** `/home/YokaiExchange/backend/app/db/portfolio_bootstrap.py:193-231`  
**Also affected:** `/home/YokaiExchange/deploy/db/bootstrap-roles.sql:245-283`

**Issue:** `CATALOGUE_SQL` enumerates relations, columns, constraints, indexes, triggers, routines and sequences, but never includes `pg_rewrite` or rejects unexpected table rewrite rules. `ACL_SQL` does not cover them either. Consequently an owner-installed rule can change the financial meaning of the authenticated source while the catalogue and ACL hashes remain exactly equal to their expected values. Both runtime admission and the production bootstrap accept that state.

A concrete drift is:

```sql
CREATE RULE unexpected_grant AS
ON INSERT TO public.portfolio_creations
DO ALSO UPDATE public.accounts
SET cash = cash + NEW.amount
WHERE id = NEW.portfolio_id;
```

`create_portfolio` first inserts the fixed-10000 account and then inserts the fixed-10000 journal. The added rule makes that second statement credit another 10000 to the account. Existing canonical/baseline triggers permit cash updates, and the immutable journal still records only the original 10000 grant. No field selected by either fingerprint changes when this rule is installed. PostgreSQL documents that rules add commands to the original operation and execute rule-referenced relation access with the rule owner's privileges. [CREATE RULE](https://www.postgresql.org/docs/18/sql-createrule.html), [Rules and Privileges](https://www.postgresql.org/docs/18/rules-privileges.html).

**Fix:** Since the approved public table inventory needs no rewrite rules, explicitly reject any `pg_rewrite` row attached to an application table before grants or runtime admission. Alternatively include the exact complete rule definition, target, event and enabled state in the pinned projection. Apply the same contract to shared and production preflight, leaving frozen 0017 literals untouched. Add a real PostgreSQL negative that installs the rule above as the owner and proves admission/bootstrap refuse before any creation or grant mutation.

### CR-02: BLOCKER — Runtime admission misses implicit database-owner schema privileges

**Disposition:** Resolved by `5f5d087`; original severity and initial-source evidence retained below.

**File:** `/home/YokaiExchange/backend/app/db/portfolio_bootstrap.py:269-283`  
**Caller:** `/home/YokaiExchange/backend/app/db/schema_contract.py:46-51`

**Issue:** The new shared preflight checks explicit `pg_auth_members` rows and schema ACL grantees named PUBLIC/app/scheduler, but does not check database ownership or effective schema privileges. With the standard `public` schema owned by `pg_database_owner`, changing the current database owner to `birja_app` or `birja_scheduler` leaves every selected catalogue/ACL field unchanged. The schema CREATE ACL still names `pg_database_owner`, and its database-owner membership is implicit rather than a `pg_auth_members` row. Thus `require_schema` accepts a runtime role that now controls the public schema, including destructive DDL, contrary to the admission guarantee that unsafe schema CREATE refuses before financial dispatch. PostgreSQL explicitly documents this implicit membership and ownership of `public`. [Predefined Roles](https://www.postgresql.org/docs/18/predefined-roles.html).

The production script's earlier administrative preflight already rejects runtime database ownership (`deploy/db/bootstrap-roles.sql:43-51`), but that protection is absent from the shared preflight used by startup, every write request and dev authorization. A prior successful production bootstrap does not make the new ongoing runtime drift check complete.

**Fix:** Add explicit current-database/schema ownership validation to shared preflight and check effective `has_schema_privilege(role, 'public', 'CREATE')` for app and scheduler rather than relying only on ACL grantee names. Keep administrative and runtime rules aligned without changing frozen 0017 contracts. Add a disposable PostgreSQL negative with `public` owned by `pg_database_owner` and the database temporarily owned by a runtime role; assert effective CREATE is true and `require_schema` refuses before writes, then restore ownership in cleanup.

## Review Limits

No tests, database operations, provider calls, dependency changes, source edits or commits were performed during either review; only this review artifact was written. Initial findings were source-traced failure paths supported by official PostgreSQL semantics. The executor subsequently reproduced both and added real regression tests, whose source and reported results were inspected during re-review. `git diff --check` passed for the repair range. Full migration-fixture inventory, TLS, encrypted recovery and later phase work remain outside this report's scope.

---

_Reviewer: gsd-code-reviewer_  
_Depth: standard_
