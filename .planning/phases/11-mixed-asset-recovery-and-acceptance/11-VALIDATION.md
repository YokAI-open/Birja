---
phase: 11
slug: mixed-asset-recovery-and-acceptance
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-11-13
---

# Phase 11 — Validation Strategy

## Test Infrastructure

Reuse pytest9.1.1/pytest-asyncio/coverage with isolated PostgreSQL/Redis,
Vitest5.0.5 and Playwright1.64.1. Configuration: backend/pyproject.toml,
frontend/package.json, frontend/playwright.config.ts, docker-compose.test.yml.
No framework installation is planned.

Quick offline samples (actual final Plan04 combined mandatory feedback1.247s): `python3 deploy/tests/test-stock-recovery-contracts.py RevisionContracts`
and `python3 deploy/tests/test-ci-ops.py`. These are small samples,
not substitutes for financial/integration acceptance.

Full backend: `cd backend && uv run pytest --cov=app --cov-branch --cov-fail-under=80`,
then existing exact47-module100%statement/branch command from CLAUDE.md/CI.
Full frontend: `cd frontend && npm run test -- --coverage`.
Browser: `python3 deploy/tests/run-stock-browser.py`.
Recovery: existing CI serial same-archive campaign, explicit archive roundtrip,
roles, populated/fresh verify-full TLS authority parity, image transition and
selected rollback. Extend bounded current0014 compatibility proof as planned;
legacy0008 evidence does not establish it. Integration runtime is minutes,
historical full recovery1391s at7196d5f remains separate. Current qualified
same-archive stages total1680.876s across their explicit source commits (not a
fresh successful complete block at final source).

## Sampling Rate

After each changed task run relevant offline contracts; financial changes also
need affected real-isolated-DB assertions. Each wave runs affected suites.
One source-frozen final campaign follows source stabilization. Do not repeatedly
rerun long unaffected gates. No watch mode. Planner fills exact per-task mapping
and measured feedback budget; long integration gates are explicit exceptions.

## Per-Task Verification Map

All rows are reconciled to actual execution and independent04 verification.
Planning itself ran no product tests. Short commands target under30s and are
expected under60s; actual Plan04 mandatory feedback is1.247s.
Long gates below are explicit integration exceptions, never short feedback.

| Task | Req | Threats | Secure oracle / existing or Wave0 fixture | Automated verification | Status |
|---|---|---|---|---|---|
|11-01-1|SAFE-02|T-11-01-01/SC|Wave0 test-deploy-compatibility.sh:0014 old target refuses before checkout/build/start; tested source allowed; original legacy rollback/service tests retained|`bash deploy/tests/test-deploy-compatibility.sh && bash deploy/tests/test-rollback-target.sh && bash deploy/tests/test-app-services.sh && bash -n deploy/deploy.sh`|PASS — actual A/N execution and independent04 review|
|11-01-2|SAFE-02|T-11-01-01/02/03/SC|Wave0 test-selected-cutover-contracts.py: actual dispatch/archive, canonical/identity oracles and intended refusal/finally cleanup contract; existing RevisionContracts|`python3 deploy/tests/test-selected-cutover-contracts.py && python3 deploy/tests/test-stock-recovery-contracts.py RevisionContracts`|PASS — actual A/N execution and independent04 review|
|11-02-1|SAFE-02/03|T-11-02-01/SC|Existing test-ci-ops.py extended mutation cases reject missing/reordered current/legacy dispatch, changed archive and swallowed errors|`python3 deploy/tests/test-ci-ops.py && python3 deploy/tests/test-selected-cutover-contracts.py && bash deploy/tests/test-deploy-compatibility.sh`|PASS — actual A/N execution and independent04 review|
|11-02-2|SAFE-02/03|T-11-02-02/SC|Acceptance matrix maps exact oracles and distinguishes historical/synthetic/new PENDING; source review, no artificial RED|`git diff --check && rg -n 'SAFE-02\|SAFE-03\|0014\|0008\|PENDING\|48d970c\|SAFE-01' .planning/phases/11-mixed-asset-recovery-and-acceptance/11-ACCEPTANCE.md`|PASS — actual A/N execution and independent04 review|
|11-03-1|SAFE-02/03|T-11-03-01/02/03/SC|Existing actual DB/browser/dev/native gates, exact expected cash/counts, owner isolation,80%overall/47critical100%, all audits/five strict scans|`cd backend && uv run pytest --cov=app --cov-branch --cov-fail-under=80`; canonical exact critical/static/audit/scan commands in CLAUDE/CI; `cd frontend && npm run test -- --coverage`; `python3 deploy/tests/run-stock-browser.py`; `python3 deploy/tests/test-dev-bootstrap.py --image birja-backend-test:phase05-07`|PASS — actual A/N execution and independent04 review|
|11-03-2|SAFE-02|T-11-03-01/02/03/SC|Existing PGContracts and serial ops plus Wave0 current0014 actual startup/cutover/replay/refusal/rollback; exact rows/totals/schema/authority/identity and original volumes unchanged; cleanup|Exact runnable command reproduced below; extracts current CI block by unique step/heredoc markers and preserves all stage/integrity assertions|PASS — actual A/N execution and independent04 review|
|11-04-1|SAFE-02/03|T-11-04-01/02/SC|Distinct code/security/UI reviews inspect actual receipts and all threats; HIGH/CRITICAL/missing mitigations block; UI continuity assessed|`git diff --check && bash deploy/tests/test-deploy-compatibility.sh && python3 deploy/tests/test-selected-cutover-contracts.py && python3 deploy/tests/test-ci-ops.py` plus distinct source/evidence review|PASS — independent reviews0code blockers,14/14threats,UI24/24;17deploy/7selected/16CI1.247s|
|11-04-2|SAFE-02/03|T-11-04-01/02/SC|Goal-verifier receipt/source comparison covers3criteria/all clauses; unproven0014 blocks SAFE-02; human needs remain pending|`git diff --check && rg -n 'SAFE-02\|SAFE-03\|0014\|0008\|SAFE-01\|48d970c' .planning/phases/11-mixed-asset-recovery-and-acceptance/11-VERIFICATION.md` plus actual receipt SHA/source comparison|PASS — independent goal3/3,full SAFE-02/03 clauses; source/archive/raw evidence authenticated|

Offline tests are dispatch/refusal/order feedback, never financial success proof.
Plan03 actual backend310.53s/browser326.1s and selected0014 342.673s are long
integration gates; their source identities and qualification are in LOCAL-PROOF.
Historical Phase10 timings remain separately attributed.
Budget/job timeout changes need actual measurements and rationale, no gate bypass.

### Task11-03-2 exact integration command

Run from repository root only during authorized execution, after Plan01/02 offline
tests pass and source/images settle. The command rejects an occupied evidence
directory, hashes original/executed CI block and changes only its synthetic archive
path. Retain prior evidence; choose another fresh synthetic path explicitly if
the fixed path is occupied. The block's own final success marker and every stage
assertion remain mandatory. This is a measured long-gate exception: provide
stage/progress updates while running and record actual elapsed time; no under60s
claim. Extraction/compilation alone is not execution evidence.

```bash
sudo -- python3 deploy/tests/test-stock-recovery-contracts.py --postgres && sudo -- python3 -c '
import hashlib
import textwrap
from pathlib import Path
root = Path.cwd()
assert (root / ".planning/phases/11-mixed-asset-recovery-and-acceptance").is_dir()
workflow = (root / ".github/workflows/ci.yml").read_text()
marker = "      - name: Serial real PostgreSQL recovery roles TLS and old-image rollback"
assert workflow.count(marker) == 1
step = workflow.split(marker, 1)[1].split("\n      - name:", 1)[0]
lines = step.splitlines()
opening = "          sudo -- python3 - <<" + chr(39) + "PY" + chr(39)
assert lines.count(opening) == 1
start = lines.index(opening) + 1
end = lines.index("          PY", start)
block = textwrap.dedent("\n".join(lines[start:end])) + "\n"
print("ci_serial_original_sha256=" + hashlib.sha256(block.encode()).hexdigest(), flush=True)
old = "archive = Path(" + chr(34) + "/tmp/birja-backup-test-ci-final/recovery.tar" + chr(34) + ")"
archive = Path("/tmp/birja-backup-test-phase11-final/recovery.tar")
assert not archive.parent.exists(), "fresh synthetic output directory required; preserve prior evidence"
assert block.count(old) == 1
block = block.replace(old, "archive = Path(" + chr(34) + str(archive) + chr(34) + ")")
print("ci_serial_executed_sha256=" + hashlib.sha256(block.encode()).hexdigest(), flush=True)
exec(compile(block, ".github/workflows/ci.yml:serial-ops", "exec"), {"__name__": "__main__"})
'
```

## Wave 0 Requirements

Existing infrastructure covers frameworks. Missing acceptance ledger/current0014
selected-tool compatibility evidence must be implemented as bounded tests before
claiming those clauses. No schema migration or new dependency is currently justified.

- [x]11-01-1 creates offline behavioral target/schema guard regressions first.
- [x]11-01-2 implements current0014 scenario and its bounded offline contracts.
- [x]11-02-1 wires both scenarios into required serial CI with mutation checks.
- [x]11-02-2 maps all clauses/oracles before Plan03 real integration.
Wave0 completion rests on actual positive/negative execution and independent
verification, not fixture existence. Current0014 compatibility and supported
rollback were actually exercised.

## Manual-Only Verifications

Reuse Phase10 owner UI/native200% checks only under final relevant source/build/
runtime/response continuity. Material UI changes require affected owner review.
Live provider rights/access/freshness and production rollout remain deferred,
not passed by synthetic testing. Do not close Phase7 SAFE-01 or live prerequisites.

## Validation Sign-Off

- [x] Every task has automated verification or explicit Wave0 dependency.
- [x] No three consecutive tasks lack automated verification.
- [x] All missing references covered by Wave0.
- [x] Source-attributed actual financial/browser/recovery/security gates pass under the independently reviewed qualification.
- [x] No watch mode; short feedback measured separately from integration gates.
- [x] Nyquist compliance and Wave0 completion set only from actual execution evidence.

Approval: validated after actual execution and independent Plan04 goal verdict
passed3/3 (2026-11-13). No local gap or outstanding human verification; canonical
requirement/phase completion belongs to the coordinator.

## Plan03 actual execution update

Tasks01/02/03 pass with measured offline24PG/16CI/7selected and full application,
browser/native/audit/image/dev results in11-LOCAL-PROOF.md. Task03-2 uses the
explicitly approved three-source qualified same-archive proof: five actual stages
atfb926d8, legacy22c44d6, fresh complete current0014 a7f965f. All11retained bytes,
archive and runtime/build/authority remain identical; no new full CI-block pass
is claimed at final source. Independent Plan04 code/security/UI/goal reviews now pass:0code blockers/warnings,
14/14threats closed,UI24/24,goal3/3. SAFE-02/03 are locally verified; canonical
requirements and phase status are coordinator-owned. Wave0 actual positive/
negative paths pass. No new human outcome is inferred from the UI contract.

## Plan04 final sign-off

Four fresh reviewer contexts are named in11-REVIEW/SECURITY/UI-REVIEW/VERIFICATION.
Mandatory short checks:17deploy/7selected/16CI plus whitespace,1.247s; receipt
`/tmp/birja-phase11-04-offline/receipt.json` SHA256
`d6c27240f771c0234b0e9ff6fc6d595908559792da97b8dec6503fcdfb6233c4`.
Verifier additionally ran7selected contracts0.023s and shell syntax/whitespace.
All27acceptance rows pass; local goals3/3. Existing48d970c owner/native200% scope
is reused only after independent source/build/runtime/response continuity review.
No duplicate full suite/campaign or new package was needed for this docs-only plan.
Only deployed-CSP W07 remains skipped; SAFE-01/live/provider/production/B2/tools/
timers/publication and W01–W08 remain deferred. No hosted-CI or fresh final-source
full serial-block pass is claimed.
