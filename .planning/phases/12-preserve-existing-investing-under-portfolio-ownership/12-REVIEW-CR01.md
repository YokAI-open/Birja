---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17
depth: standard
review_type: independent_targeted_recheck
reviewed_commit: 4c16a30c01e6040c1005fe4067e791d0ec2bc40c
reviewed_worktree: /tmp/sv-12-reviewfix-G1RXLm
files_reviewed: 8
files_reviewed_list:
  - backend/alembic/sql/0017_stock_portfolio.sql
  - backend/alembic/versions/0017_portfolio_ownership.py
  - backend/app/db/portfolio_bootstrap.py
  - backend/app/db/portfolio_migrate.py
  - backend/tests/test_portfolio_dividend_first_buy.py
  - deploy/backup-snapshot.py
  - deploy/db/bootstrap-roles.sql
  - deploy/tests/fixtures/portfolio-recovery-0017.json
resolution:
  CR-01: resolved
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 12 CR-01 Independent Repair Recheck

## Narrative Findings (AI reviewer)

**CR-01 is resolved at the exact reviewed commit. No new BLOCKER or WARNING was established in this repair.** This is a targeted receipt; it does not close the main Phase 12 review or replace final integrated qualification.

All eight changed paths were examined at standard depth, including the complete amended final-authority routine, migration/bootstrap/migrator context, backup producer, grants and the complete new regression module. The large recovery JSON was parsed throughout and recursively compared against the immutable parent: its sole changed scalar is the final-authority function definition. No other catalogue, schema, ACL or financial field changes. Original CR-01 and the repair worktree's `12-REVIEW-FIX.md` were read. Related stock execution/journal paths were traced without changing them.

### Authority and accounting assessment

At `backend/alembic/sql/0017_stock_portfolio.sql:127–149`, the exemption applies only to a supported dividend. It requires journal start, complete-from and coverage boundaries spanning the verified cutoff, no target movement or other trade before that exclusive cutoff, and an exact match between this fill's before quantity/basis and the preceding target journal. `coalesce(...,false)` prevents missing evidence from granting the exemption. A never-owner starts at zero; subsequent legitimate post-cutoff purchases reconcile to their retained preceding movements, so the fix covers the second purchase as well as the first.

An unknown positive holding without matching journal cannot satisfy the before-quantity comparison. Unknown basis similarly fails. Recorded pre-cutoff ownership—including a sold-out historical position—retains the missing-entitlement obligation. Incomplete or NULL coverage fails closed. The strict `< cutoff` comparison agrees with the existing exclusive-cutoff ownership rule. The exemption cannot apply to a pending forward split, and revision-change/held-event guards remain independent.

The instrument gate and active-root lock order remain unchanged. The normal append path still validates the entire journal and historical trade causes before final SQL; instrument serialization prevents concurrent valid fills or scheduler actions from changing that evidence beneath the decision. The application gains no UPDATE on action coverage, historical immutable records, grants or routine bodies. Existing active-root, receipt identity/arithmetic, holdings/cash equality, permission, quote/status/session freshness and last-business-statement authority checks are retained. Replay still returns the original immutable receipt, and no zero entitlement, payment or History entry is synthesized.

### Regression assessment and observed evidence

The new 225-line regression module uses genuine scheduler derivation/payment followed by application-role execution, rather than replacing financial services with mocks. It first verifies another owner's actual dividend credit and the target's missing entitlement. Its three positive variants cover another existing owner, a same-user sibling and a root created after cutoff; each asserts first/second fills, exact original replay after later state changes, unchanged original-owner finances and no target dividend payment. Negative cases retain a pre-cutoff owner, incomplete historical coverage and a closed root. The first two negative probes observe actual final-authority invocation and verify complete financial rollback; they cannot pass merely because an earlier gate refused the order.

Existing logs were inspected: RED reproduces the original restricted execution's `quote_unavailable`; GREEN records six passing cases; affected tests record 106 passes; recovery records ten contracts and an actual mixed-0017 logical restore with equality, invariant and identity checks. These are worker-produced execution evidence, independently read here, not tests rerun by this reviewer. This review ran no test or database processes.

### Independent source and catalogue pin verification

Read-only source analysis independently recomputed the SQL asset SHA256 `3dc967baccb425ba26f73bb2fab66b7947aff73f5454ea2f85e03a6e0aa5e08b`, migration SHA256 `92cff0699a40b0b8f5f4d66bc56a39a2ef88e3184860d86d6957607a3413f32b` and routine-body SHA256 `dd923d5797c95072163bd59918a95935849e9acc7af884b406706dcedfa7c158`. They match the checked-in migration/migrator/bootstrap pins.

The parent recovery catalogue independently reproduces all three original authority hashes and its final routine body exactly matches the immutable parent SQL asset. The amended catalogue changes only that routine definition, whose body exactly matches the new source. Reconstructing the existing fixed quarantine/no-ACL transformations from that source catalogue yields:

- Source: `617fcabb4fe6d24f0cd0c306680f759f5d9dc21d970e7ed8919c8913980a9696`.
- Quarantined: `7dff7b4ee651cb94592debe260bde4dd4148be3c2c977ac6324327cc23e119b6`.
- No-ACL: `87d1f2cd9dd78a74da974b7a5a86aaf092dc58af1b66bd53e5455c82f1e4afaa`.

These match the new producer constants. The schema remains byte-equivalent as a parsed value and retains its original hash. This establishes a source-derived replacement of the previously verified catalogue, without adopting any live database's self-description. No grants, routine declaration attributes, role isolation or restore admission checks were weakened. Updating the still-unmerged 0017 asset is within the authorized local repair boundary; this receipt does not authorize rewriting a published migration.

## Boundary

Only this report was written in the main checkout. No source edits, commits, test runs, dependency installations, provider calls or production operations were performed. Parent aggregation, integration and affected final qualification remain separate.
