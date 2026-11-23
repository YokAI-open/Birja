---
status: resolved
trigger: Released deployment preflight flags healthy built-in C collation as drift
created: 2026-11-22
updated: 2026-11-22
---

## Symptoms and evidence

Production0023 remains paused; original financial data preserved. All six0.6.1CI
checks passed and software0.6.1 is published, but an operator dry run retained the
separate COLLATION_PREFLIGHT and found collation_blocked. Read-only metadata:
database stored/actual versions both2.44; zero invalid/unready public indexes;
indexedpg_catalog.C providerlibc stored/actual versions bothNULL, as expected.
The new portfolio name-key index deliberately uses this deterministic collation.
No role/bootstrap/data mutation occurred during that refused dry run.

## Current focus

hypothesis: configure-db.sh incorrectly treats every NULL collation version as
unknown drift, including documented stable built-in bytewise C/POSIX.
next_action: parent reviews local verification and controls production confirmation;
  original production symptom is not declared resolved by these isolated tests.

## Primary sources

https://www.postgresql.org/docs/18/collation.html explains C/POSIX bytewise
ordering is stable across versions for a given encoding.
https://www.postgresql.org/docs/18/sql-altercollation.html explains versioned
collation mismatch handling. No data/index repair is indicated for healthyC.

## Reproduction evidence

- timestamp: 2026-11-22
  checked: exact COLLATION_PREFLIGHT AST-literal extracted from configure-db.sh,
    passed unmodified to psql stdin on disposable birja-test after genuine0023 migrations
  found: database stored/actual2.44/2.44; indexedpg_catalog.C providerlibc stored/actual
    NULL/NULL; all public indexes valid/ready. Probe returns collation_blocked,
    failing expectedcollation_ok in3.84s. Full index/collation/database metadata
    compares unchanged after probe. No version refresh/index repair performed.
  implication: unconditional NULL rejection mistakes documented bytewiseC for drift.

## Boundaries

Only isolated local tests and reviewed source fix. No production/provider access,
package changes, financial/schema changes, catalogue version refresh or index
repair. Parent owns configure-db.sh and publication; investigator owns newtest
and this debug report. Preserve existing gates and publishedtags.

## Resolution

root_cause: COLLATION_PREFLIGHT rejects every indexed libc collation with NULL
  stored/actual versions, including documented stable pg_catalog.C used by0023's
  portfolio name-key index; healthy database/index checks cannot override that clause.
fix: parent narrows exemption to deterministic libc pg_catalog C/POSIX with matching
  locale/ctype identity and BOTHNULL versions; database version, invalid/unready index,
  genuine version mismatch and unknown unversioned checks remain. Investigator owns
  only backend/tests/test_deploy_collation.py and this report.
verification: genuine pre-fixRED1failed3.84s, post-fixGREEN6passed2.54s;
  exact deployment SQL extracted as AST literal and executed unchanged via psql stdin.
files_changed: backend/tests/test_deploy_collation.py and this report.

## Local GREEN evidence

- timestamp: 2026-11-22
  checked: six genuine PostgreSQL18 cases, current0023 plus owned benign fixtures
  found: current indexedpg_catalog.C accepted; explicit indexedpg_catalog.POSIX accepted;
    versioned pg_catalog.en_AU.utf8 accepted with stored/actual2.44/2.44. Unknown custom
    unversioned copy ofC refused. Custom libc collation created through supported
    CREATE COLLATION VERSION test-stale-version refused. Duplicate synthetic rows
    cause real CREATE UNIQUE INDEX CONCURRENTLY failure, leaving an invalid index
    which the probe refuses. No pg_catalog tampering, version refresh or index repair.
  implication: exemption handles healthy built-ins and preserves genuine drift gates.
- timestamp: 2026-11-22
  checked: before/after database/collation/index projections and financial snapshots
  found: metadata and financial rows unchanged after every probe; synthetic duplicate
    fixture rows retained exactly. Only test-owned table/index/custom collation dropped
    after assertions. Full test run6passed2.54s. Ruff check and format pass.
  implication: bounded readonly preflight neither normalizes nor repairs refused state.

Reproducible command, run from /tmp/birja-hotfix-0.6.2-worktree/backend:

```bash
UV_PROJECT_ENVIRONMENT=/home/YokaiExchange/backend/.venv UV_CACHE_DIR=/tmp/birja-uv-cache uv run --no-sync pytest tests/test_deploy_collation.py -x -s --tb=short
```

Same command before source fix ran the original single current0023 test and failed
with expectedcollation_ok/actualcollation_blocked. Local test socket/Docker execution
used authorized sandbox escalation. No whole campaign or production result claimed.

## Bounded review

Session manager reviewed the parent's source diff and regression inline:
0 blockers, 0 warnings. This was not a fresh third-party review. Only the
deterministic libc pg_catalog C/POSIX definitions with exact matching locale
fields and BOTHNULL versions are exempt. IS NOT TRUE retains refusal for
unknown definitions; database version, invalid-index and versioned mismatch
predicates are unchanged. PostgreSQL18 primary documentation was independently
checked. First-party0.6.2 metadata changes no dependency graph; frontend audit
bindings match actual bytes and retain advisory scope/expiry. git diff --check
passes. No database operations or new campaigns were run during review.

## Actual production confirmation

All six hosted checks passed run45069245874 at1a9f9e8;3,703backend tests and
criticalcoverage100%. PR39published main7d236e4/v0.6.2. Exact qualified source
probe and full canonical bootstrap passed, original finances remained unchanged,
and actual deployment completed. Pre-start and post-rollout exact isolated B2
restores, current-API origin41/41, public9/9 and verified encrypted custody export
pass. See[production receipt](../releases/0.6.2/PRODUCTION.md). Earlier isolated-only
scope and paused-production statements above describe the investigation history.
