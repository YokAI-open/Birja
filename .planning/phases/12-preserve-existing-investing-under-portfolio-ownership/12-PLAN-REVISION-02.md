# Phase12 — Planner revision2

**Input:** preserved12-PLAN-CHECK-02.md: four BLOCKER, zero WARNING.
**Iteration:**2 of maximum3. **Status:** revised; fresh independent recheck pending.
**Scope:**28 plans,56 tasks,18 waves; seven primary requirement IDs unchanged.

| Issue | Concrete correction | Contract/proof owners |
|---|---|---|
| P12-C02 | Changed every05/06 completion surface: truths, acceptance, done and success now require static asset-contract success plus collected final_sql scenarios. No precursor claims actual restricted-role economic/forgery/freeze success. |05/06 static source/collection;07-01 actual Alembic0017 plus all final_sql assertions. VALIDATION/COVERAGE distinguish these outcomes. |
| P12-C06 | StockSplitApplication remains instrument-global: no user/root column, root association, owner equality or OLD.user_id predicate. Preserve unique economic_event_id and global application/coin/unit cause FK. Movements own portfolio_id with unique(application_id,portfolio_id). | RESEARCH R1/R2 and stage table;03 metadata;04 owned-only backfill;05/07 SQL;12 journal/writer;16–18 inventories/oracle/restore.01/04 seed one genuine legacy split spanning two users;12 later applies one global split to two same-user sibling portfolios. Original application IDs/digest bytes stay exact. |
| P12-C07 | Selected real nullable SMALLINT stock_split_applications.owner_digest_version, no default: existingNULL means legacyv1, new explicit2 required. No nonexistent application JSON payload. Legacy rows/digest bytes are never rewritten. |03 model/check;0015 expansion;05 static check_stock_split_digest_version BEFORE INSERT guard;07 installs/qualifies shape/trigger/owner/search_path/ACL/body and immutable UPDATE/DELETE;12 explicit writer/persisted reader;16 authority inventory;17 exact projection/hash/restore;18 mixed-version oracle/real smoke;27 cold proof. Unsupported versions, new missing marker, altered defaults/checks/guards/ACLs and legacy marker mutation refuse. |
| P12-C08 | Assigned actual test bootstrap before04: reconcile conftest's unconditional prerequisite and test_migrations's NOLOGIN rejection to guarded restricted LOGIN migration identity, using per-session in-memory disposable credentials. Shared fresh-child run_test_migration passes only child DATABASE_URL, producing real authenticated session_user; parent app Settings/identity remain ordinary. Existing online migration callers including test_stock_migrations use the helper; offline rendering stays unchanged. |01-01 owns conftest.py,test_migrations.py,test_stock_migrations.py and migration fixture tests. Exact test-stack/admin/object inventory guards precede provisioning; production setup is untouched.01 proves connection/unsafe-role/endpoint/parent isolation on existing0014;04 proves real association, ordinary/SET ROLE refusal and interrupted authenticated resume;07 proves fresh/populated final head before running_app. Staged tests use explicit-revision fixtures, never intermediate app startup. |

The0015/16 caller predicate remains authenticated session_user='birja_migrator'.
No GUC, SET ROLE shortcut, weakened production guard, manually fabricated final
schema, metadata.create_all or skipped SQL proof was introduced. The nullable
digest marker is unrelated to required owned-root associations; global
applications never enter that association allowlist. Qualified restore loads
existing mixedNULL/2 rows before installing guards, then proves exact interpretation
and fresh-insert refusal with the final restricted authority installed.

## Static verification

PASS using installed gsd-sdk1.42.3:

- All28 frontmatter.validate schema checks and28 verify.plan-structure checks.
- All28 frontmatter.get typed artifact/link assertions (block YAML objects).
- All56 task field/file-bound/command/threat-map checks; every command matches
  VALIDATION and its named threat proof. Each task touches at most five files.
- Acyclic dependencies,18 waves, same-wave disjoint outputs, transitive ordering
  for shared files, new-file ownership and per-file analog/input references.
- Seven primary requirements, verbatim context constraints, coverage owners,
  unchanged deferred/live/future-management boundaries and both false flags.
- Both independent check reports remain byte-identical to their committed inputs.
- Targeted assertions cover all four revised contracts. git diff --check passes.

Static check command: python3 /tmp/phase12-revision2-static.py. This temporary
checker inspects planning files and invokes the installed SDK only; it creates
no application, database or runtime evidence.

Counts and waves are unchanged.01-01 owns five files for its fixture/prerequisite
contract; its plan additionally owns the existing two authorization-matrix
outputs. All new prerequisites precede04 through the existing01→02→03→04 graph.
No additional plan or dependency was needed.

Prior fixes remain: typed objects, concrete functional links/per-file analogs
and threats, actual pre15 router compositions, pinned current/retained
source-schema-image-program matrix, independent mutated-input oracle and real
isolated smoke, serial one-archive current/retained proof, strict coverage/audit/
five-image gates and two blocking owner UI/native200% checkpoints.

No implementation, service/runtime/Docker/provider/production operation,
secret inspection, package operation, branch switch, push or publication was
performed. Only authorized planning files are committed locally. Reports01/02
are preserved; this revision does not self-approve the plans.
nyquist_compliant and wave_0_complete remain false. Six Phase7 IDs remain
deferred/unverified and live-gated; public create/rename/description/overview
stay Phase13 and delete stays Phase14. Fresh independent recheck is next.
