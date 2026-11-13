---
phase: 11
slug: mixed-asset-recovery-and-acceptance
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-11-13
---

# Phase 11 — Validation Strategy

## Test Infrastructure

Reuse pytest9.1.1/pytest-asyncio/coverage with isolated PostgreSQL/Redis,
Vitest5.0.5 and Playwright1.64.1. Configuration: backend/pyproject.toml,
frontend/package.json, frontend/playwright.config.ts, docker-compose.test.yml.
No framework installation is planned.

Quick offline samples: `python3 deploy/tests/test-stock-recovery-contracts.py RevisionContracts`
and `python3 deploy/tests/test-ci-ops.py`. Runtime unmeasured here; these are
small samples, not substitutes for financial/integration acceptance.

Full backend: `cd backend && uv run pytest --cov=app --cov-branch --cov-fail-under=80`,
then existing exact47-module100%statement/branch command from CLAUDE.md/CI.
Full frontend: `cd frontend && npm run test -- --coverage`.
Browser: `python3 deploy/tests/run-stock-browser.py`.
Recovery: existing CI serial same-archive campaign, explicit archive roundtrip,
roles, populated/fresh verify-full TLS authority parity, image transition and
selected rollback. Extend bounded current0014 compatibility proof as planned;
legacy0008 evidence does not establish it. Integration runtime is minutes,
historical full recovery1391s at7196d5f, not measured on Phase11 source.

## Sampling Rate

After each changed task run relevant offline contracts; financial changes also
need affected real-isolated-DB assertions. Each wave runs affected suites.
One source-frozen final campaign follows source stabilization. Do not repeatedly
rerun long unaffected gates. No watch mode. Planner fills exact per-task mapping
and measured feedback budget; long integration gates are explicit exceptions.

## Per-Task Verification Map

All rows remain PENDING; planning ran no product tests. Short commands target
under30s and are expected under60s, with runtime measured during execution.
Long gates below are explicit integration exceptions, never short feedback.

| Task | Req | Threats | Secure oracle / existing or Wave0 fixture | Automated verification | Status |
|---|---|---|---|---|---|
|11-01-1|SAFE-02|T-11-01-01/SC|Wave0 test-deploy-compatibility.sh:0014 old target refuses before checkout/build/start; tested source allowed; original legacy rollback/service tests retained|`bash deploy/tests/test-deploy-compatibility.sh && bash deploy/tests/test-rollback-target.sh && bash deploy/tests/test-app-services.sh && bash -n deploy/deploy.sh`|PENDING|
|11-01-2|SAFE-02|T-11-01-01/02/03/SC|Wave0 test-selected-cutover-contracts.py: actual dispatch/archive, canonical/identity oracles and intended refusal/finally cleanup contract; existing RevisionContracts|`python3 deploy/tests/test-selected-cutover-contracts.py && python3 deploy/tests/test-stock-recovery-contracts.py RevisionContracts`|PENDING|
|11-02-1|SAFE-02/03|T-11-02-01/SC|Existing test-ci-ops.py extended mutation cases reject missing/reordered current/legacy dispatch, changed archive and swallowed errors|`python3 deploy/tests/test-ci-ops.py && python3 deploy/tests/test-selected-cutover-contracts.py && bash deploy/tests/test-deploy-compatibility.sh`|PENDING|
|11-02-2|SAFE-02/03|T-11-02-02/SC|Acceptance matrix maps exact oracles and distinguishes historical/synthetic/new PENDING; source review, no artificial RED|`git diff --check && rg -n 'SAFE-02\|SAFE-03\|0014\|0008\|PENDING\|48d970c\|SAFE-01' .planning/phases/11-mixed-asset-recovery-and-acceptance/11-ACCEPTANCE.md`|PENDING|
|11-03-1|SAFE-02/03|T-11-03-01/02/03/SC|Existing actual DB/browser/dev/native gates, exact expected cash/counts, owner isolation,80%overall/47critical100%, all audits/five strict scans|`cd backend && uv run pytest --cov=app --cov-branch --cov-fail-under=80`; canonical exact critical/static/audit/scan commands in CLAUDE/CI; `cd frontend && npm run test -- --coverage`; `python3 deploy/tests/run-stock-browser.py`; `python3 deploy/tests/test-dev-bootstrap.py --image birja-backend-test:phase05-07`|PENDING — LONG|
|11-03-2|SAFE-02|T-11-03-01/02/03/SC|Existing PGContracts and serial ops plus Wave0 current0014 actual startup/cutover/replay/refusal/rollback; exact rows/totals/schema/authority/identity and original volumes unchanged; cleanup|Exact runnable command reproduced below; extracts current CI block by unique step/heredoc markers and preserves all stage/integrity assertions|PENDING — LONG|
|11-04-1|SAFE-02/03|T-11-04-01/02/SC|Distinct code/security/UI reviews inspect actual receipts and all threats; HIGH/CRITICAL/missing mitigations block; UI continuity assessed|`git diff --check && bash deploy/tests/test-deploy-compatibility.sh && python3 deploy/tests/test-selected-cutover-contracts.py && python3 deploy/tests/test-ci-ops.py` plus distinct source/evidence review|PENDING|
|11-04-2|SAFE-02/03|T-11-04-01/02/SC|Goal-verifier receipt/source comparison covers3criteria/all clauses; unproven0014 blocks SAFE-02; human needs remain pending|`git diff --check && rg -n 'SAFE-02\|SAFE-03\|0014\|0008\|SAFE-01\|48d970c' .planning/phases/11-mixed-asset-recovery-and-acceptance/11-VERIFICATION.md` plus actual receipt SHA/source comparison|PENDING|

Offline tests are feedback for dispatch/refusal/order, never financial success
proof. Plan03 real gates remain mandatory. Historical browser~317s/backend~325s/
recovery~1391s are Phase10 measurements; current0014 extension duration is unknown.
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

- [ ]11-01-1 creates offline behavioral target/schema guard regressions first.
- [ ]11-01-2 implements current0014 scenario and its bounded offline contracts.
- [ ]11-02-1 wires both scenarios into required serial CI with mutation checks.
- [ ]11-02-2 maps all clauses/oracles before Plan03 real integration.
Flags remain false until actual execution; fixture existence alone does not
establish current0014 compatibility or supported rollback.

## Manual-Only Verifications

Reuse Phase10 owner UI/native200% checks only under final relevant source/build/
runtime/response continuity. Material UI changes require affected owner review.
Live provider rights/access/freshness and production rollout remain deferred,
not passed by synthetic testing. Do not close Phase7 SAFE-01 or live prerequisites.

## Validation Sign-Off

- [ ] Every task has automated verification or explicit Wave0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] All missing references covered by Wave0.
- [ ] Exact current-source financial, browser, recovery and security gates pass.
- [ ] No watch mode; short feedback measured separately from integration gates.
- [ ] Nyquist compliance and Wave0 completion set only from actual execution evidence.

Approval: pending execution. Planning does not validate requirements.
