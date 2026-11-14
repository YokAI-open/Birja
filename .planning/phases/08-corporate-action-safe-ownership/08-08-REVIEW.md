---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T15:03:19Z
depth: deep
review_head: f6c79f0
migration_source_sha256: 439a36e6c10c67600d0388c5d1ee11be6425fb4b2c3b71523d6c430928bd8ce0
accounting_source_sha256: 922e966d7dfc4eb49498e6318f209339999caf8c323e83dc9bc6892381825baa
bootstrap_source_sha256: 43e399f095b5ffdea3f92b90624954e9225db7880e271fb27848fa90277b34dd
service_source_sha256: 3633a7a83febea3bb629c64888ced272080b0eb017a8b228e8274bdd9fe8def9
cli_source_sha256: fb493fcbd19192ae3a6fadab3df61e1d92e560d552c50efa18faa149263c93db
files_reviewed: 13
files_reviewed_list:
  - backend/alembic/versions/0012_stock_action_resolution.py
  - backend/app/services/corporate_actions.py
  - deploy/db/bootstrap-roles.sql
  - backend/tests/test_stock_action_resolutions.py
  - backend/app/services/stock_action_reconciliation.py
  - scripts/stock-actions.py
  - deploy/backup-snapshot.py
  - deploy/backup-manifest.sql
  - deploy/verify-restore.py
  - deploy/tests/ops-fixtures.py
  - deploy/tests/test-db-operations.sh
  - deploy/tests/test-stock-recovery-contracts.py
  - deploy/tests/test-restore-safety.sh
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan 08-08: Early Scoped SQL Authority Review

Reviewed frozen Task 1 SQL, bootstrap and hold-reader integration against Plan 08
and stable schema/gate contracts. Task 2 private tooling and Task 3 recovery proof
were still in progress and are excluded from this early conclusion. No tests,
database/provider calls, credentials, source edits or commits were performed.

## Narrative Findings (AI reviewer)

### NOLOGIN operator ACL fixture re-review at `f6c79f0`

**Zero active findings.** Raw SQL ACL checks now authenticate the trusted fixture
bootstrap connection solely to enter `SET LOCAL ROLE birja_action_operator`
inside BEGIN/ROLLBACK, rather than incorrectly trying to log in as a NOLOGIN
group. PostgreSQL checks the submitted static statements against the current
operator role; failed commands close the connection and roll back. Existing
42501 assertions still require actual privilege refusal, and successful queries
remain bounded. Added positive five-column coin read and negative metadata,
catalogue/action/holding mutation checks preserve the intended boundary.
This helper does not establish dedicated-login membership or TLS; their separate
real nonprivileged consumer is unchanged and remains required.

ops-fixtures.py SHA-256:
`edc0b3ecf4f9e8b71d4533f5bcb8c3cfc319468a42e0ef7222136e43809173fd`.
The root reports the final db27 encrypted archive completed all six revisions,
13 authority corruptions and actual restored operator/split replay in301.665s.
That executor evidence is distinct from the later raw-ACL fixture login failure.
Core recovery source/archive is unchanged, so source review clears only the
remaining `--roles` mode including its roles and both TLS lanes; another archive
run is not required by this test-only correction. No reviewer tests or database
operations were performed.

### Fixture-only corruption connection re-review at `29b40d1`

**Zero active findings.** Deliberate authority-corruption setup now connects as
the existing bootstrap identity to the explicitly fixed restore clone. Each
static corruption plus canonical read is wrapped in BEGIN/ROLLBACK, with
ON_ERROR_STOP and connection exit preserving rollback on failure. Labels are
fixed bounded literals and expose no data or credentials. Actual verification,
normal restoration and operator/service replay retain restricted identities.
No source/runtime privilege is granted to make a negative control succeed.

ops-fixtures.py SHA-256:
`5ee487280fd5e7dacf34e53729673216dc4480374a4afadf75626bbc5bc3a609`.
The verifier remains
`1aa4337745716237f228e468da6a09202907fffbdd9621e9913a8a8272c08bf6`.
Source review clears the single final full `--all` run including all six retained
revisions and roles/TLS. The previous encrypted run reached every restore but
failed before post-restore operator replay/roles/TLS; direct-dump diagnostics
and earlier archive results are separate historical evidence, not a final
same-archive operational pass. No reviewer tests/database operations occurred.

### Fresh-server role preprovisioning re-review at `17cbe97`

**Zero active findings.** The actual operational run exposed a fresh-server
operator-role creation failure after predecessor archives restored. The narrow
correction routes only the static reviewed role-preflight DO block through the
already allowlisted bootstrap database/connection. It runs after the clone's
independently pinned function-definition and owner checks; it creates only the
fixed missing NOLOGIN/NOINHERIT operator role and rejects unsafe existing role
attributes/memberships. No supplied manifest SQL, names or authority are executed.
Function/table grants and final canonical validation still use the restricted
clone owner. The migrator gains no CREATEROLE or broad privilege, and an unsafe
existing role is not repaired. `restored()` retains quarantined clone cleanup.

Current verify-restore.py SHA-256:
`1aa4337745716237f228e468da6a09202907fffbdd9621e9913a8a8272c08bf6`.
Other functional/tooling identities and the final function anchor remain intact.
The root reports the fresh populated0012 restore and unsafe-existing-role refusal
passed; those are executor evidence, not reviewer-executed tests. The prior
0007–0011 results are historical for the previous archive. Source review clears
the repackaged same-archive0007–0012 plus roles/TLS rerun; that full final proof
remains pending. No reviewer tests or database/runtime/source changes occurred.

### Final CR-11 re-review at `0acb2b2`

**Zero active BLOCKER/WARNING findings in the reviewed functional and recovery
source scope.** CR-11 is resolved. `_admission_snapshot` selects the full database
row and its PostgreSQL canonical row digest in one statement snapshot. The
service constructs and validates the corresponding complete ProductAdmission,
requires the supplied digest to match that same snapshot before SQL invocation,
and retains the SQL locked row-digest comparisons after gate/row-lock waits.
Both actions and calendar receive this binding; exact stored replay retains its
existing idempotent path. The replacement inline actions checks preserve the
former `_authority` purposes, feed, REST capability and configured scope.

The service SHA-256 is
`3633a7a83febea3bb629c64888ced272080b0eb017a8b228e8274bdd9fe8def9`.
SQL and recovery identities remain those captured at `05a4321`; CR-07–10 remain
resolved. The first full owned six-revision archive/restore and TLS operational
run may proceed on this frozen source. This clears source review only: no such
operational pass is claimed here, and the reviewer performed no tests, database
operations, runtime/source changes or commits.

### Combined targeted re-review at `05a4321`

CR-10 is resolved: canonical authority now covers every ordinary-table column's
effective SELECT/INSERT/UPDATE/REFERENCES and corresponding grant options. Its
expected matrix permits the 13 declared stock/action tables and five coin columns
only, with no column mutation or delegation rights. CR-07–09 remain resolved;
fixed restoration does not consume manifest-provided SQL or widen runtime roles.
The independently pinned current PostgreSQL function hash is
`a612d7fb2f5b4f50549f4d40b01e6e83a2bfaf8a7d4ce1f77ff2df22b13b2dc1`.

The new actions-row digest is checked under SQL locks, but its missing binding
to the snapshot validated by Python leaves CR-11 below. No reviewer tests or
database operations were performed; the full six-revision operational proof is
not claimed complete.

Frozen SHA-256 identities:

- migration0012: `439a36e6c10c67600d0388c5d1ee11be6425fb4b2c3b71523d6c430928bd8ce0`
- reconciliation service: `9f9a6700b3ce48db6752d8b8c5686f08ffd05b276d51e98b3514ffd20293bb93`
- backup-snapshot.py: `9e24a224718c3aab9c5252185da64a6e44ee6c26c320f2cbcb8b4b12246cf2d4`
- verify-restore.py: `79b61631ee7f6a55d9e419f1d957f5f98ea64f38e1c8ffb384fe4d6e4ded5816`
- ops-fixtures.py: `e4fb19b2bb2eb0833be7177e3ded305e9af4bb16c34913725a3eaad56012611c`
- test-stock-recovery-contracts.py: `d6b5b8d917f03088205427b30b3584fad4dbc298cacc325397d48575c30baada`

### CR-11 — BLOCKER, RESOLVED: Caller digests are not bound to the authority snapshots actually validated

**File:** `/home/YokaiExchange/backend/app/services/stock_action_reconciliation.py:202`

**Also affected:** SQL locked actions/calendar digest comparisons near0012
migration lines 83 and 98.

**Issue:** `reconcile()` validates actions authority A and calendar A, but never
compares their complete snapshot identities with the caller's
`admission_digest`/`calendar_digest`. SQL subsequently matches those supplied
digests only against the later locked rows. An evidence file naming snapshot B
can therefore pass Python validation against A, wait behind the instrument gate,
and pass SQL after a same-generation A→B change. If B has revoked allowed fields,
quota or a capability that `_authority()` checks but SQL's partial semantic
checks omit, the audit is accepted against authority never fully validated. The
new digest comparison closes ordinary stale-A evidence but does not establish
the required identity between the validated and effect-time snapshots.

**Fix:** Bind both expected digests to the exact complete row snapshots validated
by Python before invoking SQL, retaining the final locked equality checks.
Compute the authoritative PostgreSQL row digest together with the snapshot read,
or acquire the authority row locks before reading/validating the exact snapshots;
do not use a later unrelated digest query as proof of an earlier validation.
Reject evidence naming a different snapshot even if SQL later observes it. Add
an actual gate-wait regression with evidence naming B, Python validation at A,
and same-generation transition to semantically revoked B, plus the equivalent
calendar snapshot-identity case.

### Targeted recovery re-review at `7aac11e`

CR-07, CR-08 and CR-09 are resolved. Seed transactions now keep one instrument
per root transaction; restored decision replay authenticates a dedicated operator
after clone authority validation and is separate from split replay. Fixed restore
grants now supply the exact 13 operator-readable stock/action tables, and the
canonical inventory rejects missing table reads, table-wide mutations, sequence
rights and outgoing operator memberships. The sequence metadata query protects
type-specific privilege inspection with CASE. Existing function hash anchoring,
quarantine and predecessor SQL dispatch remain intact.

One adjacent BLOCKER remains: effective column-only authority is not covered by
the new table-level inventory. No runtime operations or tests were performed by
the reviewer; executor-reported actual proof remains separate evidence.

Frozen re-review SHA-256 identities:

- backup-snapshot.py: `4497a7e7d36fd8277ace59025eb0acf929e37428e51944f6d04e5d96e5ed8d6f`
- verify-restore.py: `79b61631ee7f6a55d9e419f1d957f5f98ea64f38e1c8ffb384fe4d6e4ded5816`
- ops-fixtures.py: `b5850e1d6ac0190794816834cf0d4004524a038ac579bdbd008f83d29f02b624`
- test-stock-recovery-contracts.py: `679f1a5c9e6e7b224b723fc67557e6e6ce2c04ca9512e0c131ea72d49734b68e`

### CR-10 — BLOCKER, RESOLVED: SELECT-only operator inventory misses column-only mutations

**File:** `/home/YokaiExchange/deploy/backup-snapshot.py:136`

**Issue:** `operator_table_acl` uses only `has_table_privilege`, including its
filter. PostgreSQL column grants do not become table-wide grants. For example,
`GRANT UPDATE(cost_basis) ON holdings TO birja_action_operator` lets the operator
change basis directly, but the holdings table remains absent from this inventory
and every checked field is unchanged. Column-only UPDATE on an allowed stock
table is likewise invisible: its table SELECT remains true and table UPDATE
remains false. `operator_catalogue_columns` checks only coin SELECT, so it does
not close this gap. The source passes validation despite bypassing the reviewed
no-financial-repair boundary, and restore silently strips that unrecorded right.

**Fix:** Inventory effective column privileges across public ordinary tables,
requiring INSERT/UPDATE/REFERENCES to be absent everywhere for the operator, and
requiring SELECT only on the declared stock/action tables and five coin columns.
Preserve the table-wide/sequence checks and fixed restore allowlist. Add an actual
column-only financial mutation corruption control, plus an allowed-table
column-only mutation case, proving rejection before manifest publication.

### Recovery review at `aaeec79`

Functional scope at `8473edd` remains clean. The recovery extension has three
active BLOCKER findings below. Review was source-only: no tests, database calls,
provider calls, runtime changes or commits. The test-only predecessor table-count
correction reported by the root was observed separately in the working tree and
does not alter these findings. Earlier revision dispatch branches remain unchanged
apart from adding `0012` to the corresponding `0011` paths; the new function hash
is independently pinned, not accepted from manifest-supplied SQL or a self-hash.
All 17 identities use the existing archive-derived sequence mechanism.

Recovery source identities measured before fixes:

| File | SHA-256 |
| --- | --- |
| backup-snapshot.py | `5483e86f42088215d625566b2dd118d16de5423b6f6991248031b0372f7f63b9` |
| backup-manifest.sql | `87bd7c1962214fcf1cb63c8df0b6cd7acf42ae05e86b27d94368db6ec12aad81` |
| verify-restore.py | `cad4324197bb5cfd41a3c333275f3862811701c1a730d04b0230e5c0868a837c` |
| ops-fixtures.py | `71139d3ef12289b6360c881d56ee23796ce46eaa06452de98a8bea14f3854429` |
| test-db-operations.sh | `7c4cf599ff2afe518180d913358a2aef027502d44163d4994527d09628f9cc31` |
| test-stock-recovery-contracts.py (test-only table-count correction present) | `aaff20950c07caeed13755f982dbd350098ae1bd544ba95c0f58dc57ddbc473d` |
| test-restore-safety.sh | `d0ed5052a81b7037d07941d1841f211fa2417b12132227538f9322fdbeb493b8` |

### CR-07 — BLOCKER, RESOLVED: Recovery seed violates the one-instrument transaction contract

**File:** `/home/YokaiExchange/deploy/tests/ops-fixtures.py:1973`

**Issue:** `scenario(db, True)` first persists the dividend on `catalog[2]`, then
persists the split on `catalog[1]`. `RECOVERY_SEED_SCENARIO` invokes both inside
one `factory.begin()` transaction (lines 1983–1984). Each persistence acquires the
stock gate; `stock_ownership.py:96–98` explicitly rejects changing instruments
within the same root transaction. Consequently the second persistence raises
`one_instrument_per_transaction`, preventing the genuine populated0012 retained
archive proof from running.

**Fix:** Seed/reconcile each instrument in a separate committed transaction,
without bypassing the production gate. Preserve the dividend evidence snapshot
and replay IDs across the transaction boundaries. Exercise the real0012 seed
before beginning the long serial archive proof.

### CR-08 — BLOCKER, RESOLVED: Restored operator authority lacks reads required by its real service

**File:** `/home/YokaiExchange/deploy/verify-restore.py:876`

**Issue:** `pg_restore --no-acl` removes the operator's table reads. The fixed
authority helper recreates EXECUTE, schema usage and five coin-column reads only;
it omits the canonical action-table and stock-instrument/admission/quote/session
reads granted in bootstrap. `reconcile()` immediately selects
`stock_action_resolutions`, even for replay, so the intended operator receives
permission denied in a fresh restored clone. The fixture's restored service replay
runs as `birja_migrator`, masking the missing authority; manifest comparison also
omits these reads and therefore incorrectly reports equality.

**Fix:** Extend the reviewed fixed allowlist and canonical authority inventory to
the exact existing operator read contract, without granting financial-table reads
or mutation privileges. Prove restored reconciliation replay with a dedicated
operator login/role under verified TLS, retaining app/scheduler/PUBLIC denials.
Keep split replay under its intended separate actor; do not claim migrator success
as operator recovery.

### CR-09 — BLOCKER, RESOLVED: Source authority accepts outgoing operator role escalation

**File:** `/home/YokaiExchange/deploy/backup-snapshot.py:131`

**Issue:** Canonical authority records runtime-role membership in the operator
role but does not record the operator's membership in other roles. For example,
`GRANT birja_scheduler TO birja_action_operator` leaves all seven checked role
attributes false and runtime-to-operator membership false; the source manifest
passes, although the operator can `SET ROLE birja_scheduler`. Both reviewed0012
migration and the restore helper reject outgoing operator membership, so this
unsafe source boundary is silently omitted from the supposedly exact inventory.

**Fix:** Include and require an empty outgoing operator-membership set (consistent
with migration/restore), and add an actual corruption control showing that such a
grant is rejected before publishing a backup manifest. Do not remove the existing
runtime-to-operator transitive checks.

### Targeted functional re-review at `8473edd`

**Zero active BLOCKER/WARNING findings in the functional scope.** CR-05/06 and
WR-01 are resolved. SQL compares the complete calendar row digest after its gate
and authority-row locks, preserving the earlier genuine-cutoff validation against
same-generation changes. CA content is read with the bounded protected no-follow
descriptor helper and loaded using cadata, without reopening a checked path.
Sanitized CLI output is printed only after successful transaction-context exit;
the state label is the durable `recorded` outcome. Prior alias/membership/hold
corrections remain intact.

Source hashes were independently measured above. No tests or runtime operations
were performed; the executor's 52-case and actual PostgreSQL function-definition
proof remain separate evidence. Task 3 recovery changes/proofs are still outside
this functional review and require their own final review.

### Functional re-review at `2c0c713`

CR-04 is resolved: alias verification now reads each source's latest immutable
observation joined to its shared revision, refusing missing/uncertain/conflicting
evidence. Private service/CLI source was additionally reviewed; recovery Task 3
remains excluded. No tests or runtime operations were performed. Three new
findings remain:

### CR-05 — BLOCKER, RESOLVED: Genuine calendar proof is stale after the SQL gate wait

**File:** `/home/YokaiExchange/backend/app/services/stock_action_reconciliation.py:195`

**Also affected:** SQL calendar validation in 0012 and function invocation near
service line 237.

**Issue:** Python derives the genuine cutoff before calling SQL, whose instrument
gate may block. SQL subsequently compares only calendar generation/deadlines and
a derived session row, not the complete calendar snapshot Python validated. A
same-generation authoritative override changing the prospective session to closed
while the caller waits leaves its old derived session row intact; SQL can accept
the old cutoff against the new calendar and append a stale resolution. Derived
session generation alone is not calendar authority.

**Fix:** Bind the complete expected calendar evidence snapshot/digest to protected
resolution evidence and compare it under the SQL authority lock before accepting
the previously computed genuine cutoff. Preserve reviewed deadline checks. Add
an actual instrument-gate race that changes a same-generation official override
between Python validation and SQL lock acquisition; the decision must refuse
without audit/state changes.

### CR-06 — BLOCKER, RESOLVED: CA trust material bypasses protected-file checks and is reopened by path

**File:** `/home/YokaiExchange/scripts/stock-actions.py:47`

**Issue:** The CA path is checked only with resolve/is_file and then reopened by
`ssl.create_default_context(cafile=...)`. Its ownership, writable parent/file
permissions and bounded descriptor identity are not checked, despite the adjacent
protected-policy claim. A CA file writable/replacable by another local user can
therefore supply attacker-controlled database trust, including a leaf replacement
between the path check and open. This can expose the dedicated operator login to
an authenticated-looking MITM.

**Fix:** Read CA bytes through a bounded, no-follow verified descriptor under
trusted nonwritable parents, validating ownership and write permissions; load the
already validated bytes using SSL cadata rather than reopening the path. Public
readability need not be prohibited if explicitly allowed; untrusted writes must
be. Add unsafe-parent/file/symlink replacement rejection tests and valid-CA loading.

### WR-01 — WARNING, RESOLVED: Success JSON is printed before transaction commit

**File:** `/home/YokaiExchange/scripts/stock-actions.py:94`

**Issue:** Reconciliation prints its resolution ID/state inside `factory.begin`,
before context exit commits the transaction. A commit failure can emit a success
record for an audit that was never committed, followed by the generic failure
message/exit status. This is misleading for operators or stdout consumers.

**Fix:** Build the sanitized result inside the transaction and print it only after
successful context exit. Add a commit-failure regression asserting no success
JSON is emitted.

### Targeted re-review at `f549c86`

CR-01 and CR-03 are resolved: identical confirmations preserve the disposition,
later missing/uncertain observations invalidate it, and transitive runtime access
to the operator role is rejected before authority creation. The operator's added
coin read is limited to the five declared metadata columns. CR-02's missing
semantic validation was corrected, but its new per-source lookup introduces the
valid-alias failure below. No tests or runtime operations were performed.

### CR-04 — BLOCKER, RESOLVED: Alias proof requires an impossible duplicate economic revision

**File:** `/home/YokaiExchange/backend/alembic/versions/0012_stock_action_resolution.py:184`

**Issue:** Each alias is checked by selecting the latest revision whose
`source_id` equals that alias. The reviewed schema intentionally allows source S2
to observe existing revision R originally owned by S1, because
`UNIQUE(event_id,fingerprint)` prevents a second revision with identical economic
terms. That legitimate S2 observation has no S2-owned revision; the new
`latest.id IS NULL` check rejects it. Requiring an independent equal revision for
every source contradicts the alias-observation contract fixed in Plan 01.

**Fix:** For each source, inspect its latest immutable observation joined to the
referenced economic revision, retaining same-event checks and exact supported
term/classification/unit/cutoff/generation agreement. Reject missing/conflicting
observations. Add success coverage for two source aliases observing one unchanged
revision with no fabricated alternate fingerprint or duplicate economic revision,
plus disagreement and missing-evidence rejection.

## Historical Findings

### CR-01 — BLOCKER, RESOLVED: Routine identical observations undo every resolution before recovery

**File:** `/home/YokaiExchange/backend/app/services/corporate_actions.py:701`

**Issue:** Resolution applicability requires the maximum ID of *all* event
observations to equal its evidence value. A resolution deliberately sets health
to reconciling, requiring a subsequent monitor cycle before availability can
recover. That cycle appends routine identical successful REST observations,
changes the maximum observation ID and invalidates the resolution, reintroducing
all historical held revisions. Thus a legitimately corrected event cannot
actually recover through the required normal monitoring path. The current test
`test_authority_new_observation_invalidates_old_disposition` explicitly codifies
this unwanted behavior using unchanged `batch(action)` source facts.

**Fix:** Invalidate a disposition for new revisions or materially uncertain/
conflicting/missing observations, while preserving it across identical successful
confirmations. Bind SQL evidence and the reader to the same meaningful uncertainty
frontier. Replace the overly broad test with separate identical-confirmation
survival and new-uncertainty invalidation cases, including actual monitor recovery.

### CR-02 — BLOCKER, RESOLVED: Alias decision does not verify agreeing economic terms

**File:** `/home/YokaiExchange/backend/alembic/versions/0012_stock_action_resolution.py:177`

**Issue:** `link_verified_alias` only requires the same event ID, two source rows
and a currently supported classification. It does not establish that the aliases'
observed economic terms agree. Conflicting same-event source histories can
therefore be cleared by this decision even though the plan explicitly requires
exact agreement. The runtime can append source/revision/observation rows, so source
count alone is not privileged evidence that their identities/economics were
verified. The accepted audit causes the reader to clear every historical held
revision listed for the event.

**Fix:** Validate the actual alias identities and their immutable observed
normalized terms against the approved current economic terms, with no competing
application/entitlement history. Reject missing/ambiguous/conflicting source
evidence; source count or a claimed equal event ID is insufficient. Apply the
same supported semantic checks required by correction acceptance where relevant.
Add a two-source, conflicting-rate/currency/cutoff regression and a genuinely
equal verified-alias success case.

### CR-03 — BLOCKER, RESOLVED: Upgrade accepts runtime membership in the new operator authority

**File:** `/home/YokaiExchange/backend/alembic/versions/0012_stock_action_resolution.py:204`

**Issue:** Operator role preflight validates attributes but not runtime role
membership. After 0011, a pre-existing `GRANT birja_action_operator TO birja_app`
or scheduler membership survives 0012; the new EXECUTE grant then exposes the
SECURITY DEFINER operation through SET ROLE despite NOINHERIT. Fresh bootstrap
rejects unsafe operator membership, but the restricted upgrade path does not.

**Fix:** Reject direct or transitive app/scheduler access to the operator role
before function creation/grant, without widening the migrator's role privileges.
Retain explicit separately provisioned operator-login policy. Add an actual
predecessor-upgrade regression with unsafe runtime membership, assert refusal
before authority is exposed, and preserve the clean restricted upgrade/fresh
privilege parity cases.
