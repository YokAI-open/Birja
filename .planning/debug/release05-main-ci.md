---
status: resolved
trigger: Finish the approved v0.5.0 release CI workflow
created: 2026-11-14
updated: 2026-11-14
---

## Current Focus

hypothesis: The private selected-cutover clone inherits main as its checked-out branch on push CI, so unconditional branch creation fails.
next_action: None; both corrective target PRs passed all required hosted jobs and merged under the owner-approved CI completion policy.

reasoning_checkpoint:
  hypothesis: A local clone can already contain main; unconditional branch creation fails although current is correct.
  confirming_evidence:
    - Hosted main push fails at branch main current with fatal branch already exists.
    - Actual-Git regression executes the unchanged fixture AST and fails for both main and detached source checkouts; feature passes.
  falsification_test: The same regression still fails after normalizing only the private clone branch, or source refs change.
  fix_rationale: checkout -B creates or resets the private clone main to its already committed synthetic current, including when main is checked out.
  blind_spots: Full hosted recovery/rollback remains to run; focused Git tests establish branch preparation only.

## Symptoms

expected: Complete serial recovery/TLS/rollback on both pull-request and main push CI.
actual: PR32 passed all six checks; identical main tree fails in selected-cutover private Git setup.
errors: fatal: a branch named 'main' already exists
reproduction: main push run 43596780499, selected-cutover.py line419, git branch main current.
started: First release main push run; release PR had a detached checkout.

## Evidence

- Main c2c7af1 has exactly candidate 2e8cb92 tree 88cd21ca35c7724c151bdeadce3dc764774d1780.
- /tmp/birja-main05-ci-failure.log: financial, recovery, roles and TLS checks succeed before the private fixture branch creation fails.
- Back-merge PR33 run43596978120 is still active at head3bc8ec8; no reported failure.
- Red regression: python3 deploy/tests/test-selected-cutover-contracts.py Contracts.test_private_clone_main_tracks_current_for_every_source_checkout failed with exit128 in main and detached subtests, while feature passed. Three real private source clones are used; actual fixture statements are AST-executed rather than duplicated.
- Green: the same actual-Git regression passes all main/feature/detached subtests after the one-line private checkout -B fix. Each verifies current equals private HEAD/main/bare-origin main, differs from original, and source HEAD/main remain unchanged.
- Focused verification: eight selected-cutover contracts pass; sixteen CI/ops contracts pass; git diff --check passes. No Docker, provider, production, dependency or publication operation was performed by the debugger.

## Resolution

root_cause: Local clones of main (and detached source HEAD at main) can contain a local main branch; unconditional creation was valid only when absent.
fix: Normalize only the disposable clone with git checkout -B main current after committing synthetic endpoint relocations.
verification: Red/green real-Git checkout matrix, eight selected-cutover and sixteen CI/ops contracts pass. Full hosted serial proof and independent review remain pending with the parent.
files_changed: deploy/tests/selected-cutover.py, deploy/tests/test-selected-cutover-contracts.py, .planning/debug/release05-main-ci.md

Published tags must not be rewritten. Production and provider operations are excluded.

## Independent Review

The parent reviewer independently inspected the debugger's diff and reran all
eight cutover and sixteen CI/ops contracts. APPROVED: the one-line change affects
only the guarded disposable clone after its synthetic commit; it preserves the
exact selected current commit and does not change source refs, runtime tooling,
data guards or recovery assertions. The regression executes the actual fixture
statements with real Git rather than a duplicated imitation. The hosted matrix
remains required before corrective PR merges.

Original back-merge run43596978120 completed its five substantive jobs successfully;
the test-only correction will get fresh required CI. A corrective release PR to
main will carry the same reviewed CI/test/planning-only head under the owner's
existing authorization to finish release CI. Neither published tag is moved.

## Hosted completion

Both target runs43598785838/43598814564 passed all six checks, including the full
serial campaign with this correction; PR34/main and PR33/develop merged tested
head952881b. Final trees match. Resolution is based on the owner's explicit
machine-check-until-green authorization and observable hosted results, not a
claim that the owner manually inspected a run. The focused regression also
exercises the main-checkout condition that differs from a detached PR checkout.
Published tags and production remain unchanged. No further fix is required.
