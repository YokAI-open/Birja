# Phase 14 — Local qualification

Plan18 is **in progress**. Neither whole-security nor final recovery has been
launched or passed. All results below are local; no hosted CI, publication,
deployment or human acceptance is inferred.

Execution began2026-11-20T08:03Z on `feature/milestone-v1.2`, initial
HEAD `426435789f8f41dea0b3fe9a4c0852c85b314a46`. SDK initialization confirms
17/19 plans have summaries; Plans18/19 remain incomplete. All seven whole
Phase14 requirements remain pending. The parent owns shared STATE/ROADMAP and
requirements; this executor does not advance them.

## Independent reviews

Distinct code, security and UI role passes are required before qualification.
The configured collaboration limit permits one reviewer at a time in this
session, so the roles run sequentially. No DB/browser campaign or source edits
run while reviewers are active. Existing per-plan findings and their repair
history remain in their original reports.

The initial independent code pass identified a Plan16 source-inventory blocker:
`security_sources` checked links only at the final path component and could
follow a linked ancestor while reading cached source paths. The parent has
authorized a narrow descriptor-relative no-follow repair in the runner and
meaningful controlled temporary-directory regressions, after all review passes
return. Finding disposition and final independent re-review belong in
`14-REVIEW.md`; no passing security campaign is claimed before that repair.

### Source-integrity repair and independent disposition

RED `407a6c0` reproduces the missing directory/root/open-race refusals with
controlled temporary trees. GREEN `d2e8885` opens every root/ancestor directory
and ordinary file with no-follow descriptors, validates regular-file identity,
and rechecks parent/root/ignore metadata. Safe in-root leaf links bind link
metadata without reading target bytes. A replacement after opening the parent
reads only the original descriptor's controlled bytes, then refuses the changed
pathname. No real outside source or credential is read by these regressions.

Final frozen tests:33 runner/supervisor contracts pass8.250s and94 CI operations
contracts pass23.865s; scoped Ruff F/E9 and whitespace checks pass.22 image/source
contracts passed5.684s before the final target-directory metadata recheck; image
binding code was unchanged. An earlier CI run passed94 in24.352s but overlaps
the last edit and is retained as diagnostic history, not the final frozen run.
Logs are `/tmp/birja-phase14-campaign-plan18-repair/{source-red,source-frozen,ci-frozen,image-final}.log`.

Independent code re-review resolves CR-01 atd2e8885 with0 blockers/0 warnings.
Independent security re-review closes T-14-16;36/38 threats are closed, with
only actual whole Plan18 qualification and separate actual Plan19 outcomes
pending. Independent UI review scores24/24 with0 blockers/0 warnings, inspecting
ten actual R5 PNGs and verifying365 source hashes and419 artifact hashes.
Original findings and all earlier evidence remain preserved in their reports.

Strict current-source/artifact/exact ZIP verification returns
`CURRENT SOURCE AND ARTIFACTS VERIFIED` after the repair. Current ZIP remains
`372c94808a6741f410522f1559221d5d2b71b02aefaa95ebe417a15911bffdfe`.
Phase13 recovery/UI, Plan15 R4, Plan16 R3 and historical R1/R3 UI archive hashes
match their original recorded values. Canonical Phase14 recovery directory is
absent before qualification. Both human acceptance flags remain false.

## Required qualification order

1. Resolve independent review findings and commit reviewed nonplanning inputs.
2. Verify the current Phase14 UI packet and preserved prior archives.
3. Run actual bounded preflight and one complete uninterrupted all-security
   child through the one-shot supervisor with an exclusive private receipt path.
4. Only after whole security passes, run one fresh uninterrupted seven-stage
   recovery at the same source and exact canonical archive.
5. Verify unchanged source, exact image/archive bindings, owned cleanup and
   current UI evidence again; record actual commands, hashes, times and counts.

The literal children remain:

```text
python3 deploy/tests/run-portfolio-validation.py --suite all-security
python3 deploy/tests/run-portfolio-validation.py --suite recovery
```

Earlier bounded or partitioned proofs are supplemental evidence only. Actual
owner UI acceptance and genuine desktop native200% remain separate Plan19 gates.
