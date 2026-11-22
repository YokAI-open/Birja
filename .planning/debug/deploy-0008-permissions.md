---
status: verifying
trigger: Production portfolio deployment refused its final permission gate
created: 2026-11-22
updated: 2026-11-22
---

## Symptoms

Expected: released0008→0023 migration and restricted-role bootstrap succeed.
Actual: database reaches0023; portfolio_migrate final preflight refuses
"unexpected closure privileges"; backend/scheduler remain stopped.
Production original finances and owner associations compare unchanged.
Both source PRs passed all six CI jobs; v0.6.0 is already published.
Before migration two fresh encrypted B2 backups and exact isolated restores passed.
No rollback to old code or manual privilege repair is permitted.

## Current Focus

hypothesis: the finite0023 bootstrap allowlist omits permissions inherited from
an authentic configured0008 runtime, although that source revision is admitted.
test: real0008 schema plus the runtime-grant/default statements from released
46d24c8 bootstrap, followed by untouched reviewed migrations to0023.
expecting: current catalogue and private defaults match; inherited ACL differs
from the finite final preflight allowlist while financial rows remain unchanged.
next_action: parent reviews locally verified hotfix and controls actual deployment;
  no production verification is asserted by this isolated synthetic investigation.

## Evidence

- Live read-only released PREFLIGHT_0023_SQL refuses unexpected closure privileges.
- Original cash/holdings/trades are unchanged and portfolio associations valid.
- Existing tests cover0014/0020 migration permission states, not configured0008.
- timestamp: 2026-11-22
  checked: released46d24c8 deploy/db/bootstrap-roles.sql and current migration tests
  found: bootstrap grants runtime access at0008 and revokes PUBLIC function defaults;
    existing legacy14 setup drops runtime roles before migration and so omits those grants.
  implication: the existing legacy14 post-migration ACL does not model configured0008.

## Boundaries

Isolated synthetic local diagnosis and narrowly tested fix only. Preserve all
strict guards, historical pins and already published tags. No production writes,
provider calls, dependency installation or publication by the debugging agent.
The parent controls deployment. No exploit demonstrations or attack payloads.

## Resolution

root_cause: admitted configured0008 runtime grants evolve through unchanged
  migrations into a legitimate0023 permission state omitted by final bootstrap.
  Existing0014 tests drop runtime roles first and cover different inherited ACLs.
fix: parent adds only reconstructed post0008 ACL/private-default bootstrap pair;
  existing unchanged grant reset normalizes inherited redundant column grants into
  unchanged canonical runtime authority. Investigator owns regression/report only.
verification: genuine isolated PostgreSQL18 RED at unexpected closure privileges
  (8.41s; final preservation7.90s), followed by2 GREEN cases in18.24s covering both
  Python and actual administrator normalization, repeatability and strict refusals.
files_changed: backend/tests/test_configured0008_migration.py and this report.

## Reproduction Evidence

- timestamp: 2026-11-22
  checked: genuine Alembic0008 plus grants/default statements from released
    commit46d24c8 deploy/db/bootstrap-roles.sql, then untouched migrations to0023
  found: require_migrator admits0008; reconstructed entry catalogue
    5663997b9e3c2c5e0631ecd5b2aaf46a7b1515cb5c0b24b10aad1b0afe3bb307,
    ACLbe589edb750b1e626251747ce506e32d7743dad03ee2ef18983d63072d5807c0.
  implication: authentic original runtime grants, no modern grant reset or schema stamp.
- timestamp: 2026-11-22
  checked: postmigration authority using complete current projection
  found: catalogue59aeeee9428fac73f96143cc8afdd77e3b6a8f81b30ed37b752666579d69a66e;
    ACLb4d138c09ace93ff69484b1b2932a667b17a19ce453a5623cae861e3e5a6ad62;
    defaults4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945.
    Triple independently matches sanitized supplied live metadata. Permission shape
    has129 nongrantable entries:104 relation,16 column,9 routine. Six scheduler
    column SELECT grants on trades survive alongside later table SELECT.
  implication: finite distinct inherited bootstrap state; schema and private defaults correct.
- timestamp: 2026-11-22
  checked: focused new regression before any app fix
  found: two owners original users/accounts/holdings/trades compare equal;
    new economic tables empty; new portfolio associations retain original owners;
    six original identity sequence last_value/is_called unchanged. After rollback
    of refused preflight, original rows/tails/authority still equal, printing
    configured0008_refusal_preserves_rows_tails_authority=true. Final test rethrows
    refusal and remains RED, expecting future supported bootstrap success.
    Ruff check/format pass. Initial sandbox socket error and absent-vs-new-empty
    oracle were corrected before the actual RED evidence above.
  implication: permission refusal reproduced without schema drift or financial mutation.

Keep canonical catalogue59aeeee…a66e, runtimeACL71896f…f748, historical pins
and all role/schema/default/inventory guards unchanged. Parent should verify GREEN
bootstrap/normalization/repeatability and extra/missing grant/default drift refusals.
No app/SQL/contracts changes, packages, production access or commit performed.

## Local GREEN Verification

- timestamp: 2026-11-22
  checked: extended tests/test_configured0008_migration.py after parent's exact-pair fix
  found:2 passed18.24s, normalizers python/admin. Both start from independently
    reconstructed129-entry inherited authority and pass both preflights. Python's
    existing GRANTS_0023_SQL and actual full deploy/db/bootstrap-roles.sql via local
    psql stdin each normalize twice to catalogue59aeeee…a66e/ACL71896f…f748/
    defaults4f53…b945. Runtime require_schema and restricted require_migrator pass.
    Original economic rows, six identity tails and owner/root associations compare
    unchanged after each normalization. Existing global per-column reset already
    removes the six redundant trades SELECT column entries; no new REVOKE needed.
  implication: exact bootstrap admission suffices; qualified grant contracts stay unchanged.
- timestamp: 2026-11-22
  checked: four benign committed near-miss states against BOTH entry surfaces
  found: extra accounts SELECT to operator; missing prices SELECT for app; builtin
    PUBLIC EXECUTE function default; schema-local table SELECT default. Every Python
    preflight and actual admin apply=true attempt refuses, retaining exact damaged
    authority and original financial rows/tails. Fixtures restore only their owned
    mismatch after proving retention. Administrator stdin preserves existing random
    test migrator password; no credentials printed. Ruff check/format pass.
  implication: new recognizer is paired narrowly and does not admit adjacent drift.

Local verification only; original production symptom awaits parent-controlled
deployment confirmation. Session is retained here and not archived as resolved.

## Bounded Hotfix Review

Session manager reviewed the parent's hotfix inline against the original released
bytes and the new regression; this was not a fresh third-party review. Result:
0 blockers, 0 warnings. Both entry surfaces admit only the reconstructed ACL
with private defaults. Runtime admission still separately requires canonical
ACL71896f…f748. AST comparison confirms the only changed Python bootstrap
assignments are the new inherited ACL constant and final preflight; existing
grant strings and historical contracts remain unchanged. Administrator edits
are confined to0023 preflight. Current producer/consumer source maps are equal
and every source digest matches its bytes; deploy binding and frontend audit
manifest/lock digests also match. First-party0.6.1 metadata changes no dependency
graph, advisory scope or expiry. git diff --check passes.

Exact successful command, from the hotfix backend directory:

```bash
UV_PROJECT_ENVIRONMENT=/home/YokaiExchange/backend/.venv UV_CACHE_DIR=/tmp/birja-uv-cache uv run --no-sync pytest tests/test_configured0008_migration.py -x -s --tb=short
```

Result:2 passed in18.24s against owned disposable PostgreSQL, followed by owned
stack cleanup. No new test campaign or database operation during review.

## Parent Fix Status

Exact bootstrap-only inherited ACL/private-default pairing is implemented in
Python and administrator SQL. Existing normalization, canonical runtime authority
and qualified historical literals are unchanged. Current producer/consumer and
deployer source bindings match new source bytes. Version0.6.1 changes first-party
metadata only, with unchanged third-party graphs and issue35 scope/expiry.
Publication, full hosted CI and production fix-forward remain pending.

Final affected PostgreSQL regression:79passed507.63s. Owned test services/network
removed. Production still paused; publication/fullCI/guarded fix-forward are next.
