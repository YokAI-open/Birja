# Phase 11: Mixed-Asset Recovery and Acceptance — Pattern Map

**Mapped:** 2026-11-13
**Files classified:** 10 candidate new/modified files; existing gates additionally inventoried below
**Analogs found:** 10 / 10 (9 exact existing-file/format matches, 1 role match)

This is an acceptance-only map from `11-RESEARCH.md`, approved `11-UI-SPEC.md` and draft `11-VALIDATION.md`. No CONTEXT exists. File names for new acceptance artifacts below are recommendations for the planner, not existing APIs or mandatory product implementation. Only this pattern map was written; no tests, installs, services, provider/private configuration access or commits were performed.

## File Classification

| Candidate new/modified file | Role | Data flow | Closest analog | Match quality / condition |
|---|---|---|---|---|
| `deploy/tests/selected-cutover.py` | test | file-I/O, request-response | Same file | exact; bounded populated0014 compatibility/refusal lane, preserve legacy0008 |
| `deploy/tests/test-rollback-db-security.sh` | test | batch, file-I/O | Same file | exact; only necessary existing-runner integration |
| `deploy/tests/test-stock-recovery-contracts.py` | test | transform, request-response | Same file `RevisionContracts` | exact; only new boundary/ordering regression assertions |
| `deploy/tests/test-ci-ops.py` | test | transform, file-I/O | Same file `CI` | exact; protect actual new mandatory lane if added |
| `deploy/tests/ops-fixtures.py` | test | batch, file-I/O | Same file `installed_recovery` / `successor_roundtrips` | exact; reuse existing fixture, edit only a demonstrated gap |
| `.github/workflows/ci.yml` | config | batch | Same file serial ops / `ci-pass` | exact; preserve gates, alter only required acceptance wiring |
| `.planning/phases/11-mixed-asset-recovery-and-acceptance/11-ACCEPTANCE.md` | utility (evidence document) | transform | Phase10 `10-LOCAL-PROOF.md` + `10-VERIFICATION.md` | role match; consolidated SAFE-02/03 behavior-to-evidence ledger is new |
| `.planning/phases/11-mixed-asset-recovery-and-acceptance/11-LOCAL-PROOF.md` | utility (evidence document) | file-I/O, transform | Phase10 `10-LOCAL-PROOF.md` | exact format; new source-bound execution receipt |
| `.planning/phases/11-mixed-asset-recovery-and-acceptance/11-VERIFICATION.md` | utility (verification document) | transform | Phase10 `10-VERIFICATION.md` | exact format; goal verifier owns final disposition |
| `.planning/phases/11-mixed-asset-recovery-and-acceptance/11-VALIDATION.md` | config (validation document) | transform | Existing Phase11 validation file | exact; fill actual per-task map and execution sign-off later |

Evidence documents use the available role vocabulary; they are not application utilities. None of the optional existing-file edits is justified merely by appearing in this table. No migration, model, controller, service or UI component is implied.

## Pattern Assignments

### Selected compatibility fixture and rollback runner

**Files:** `deploy/tests/selected-cutover.py`, `deploy/tests/test-rollback-db-security.sh`.

**Primary analog:** `deploy/tests/selected-cutover.py`. Imports and local module loading, lines20–26:

```python
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "fixtures", ROOT / "deploy/tests/ops-fixtures.py"
)
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)
r = f.r
```

**Bounded process/error pattern**, lines33–42,47–54: `call(argv, data=None, ok=True, timeout=180, env=None)` invokes `subprocess.run` with captured output, explicit timeout, `env or r.ENV`, `check=False`, then asserts `(result.returncode == 0) == ok`. It returns stdout. Copy that explicit expected-failure convention for a real refusal assertion; process failure alone does not identify the refusal reason or prove ledger preservation. Fixture subprocess diagnostics can contain argv/stdout/stderr; public evidence should record safe markers and hashes, not raw private diagnostics.

**Isolation/guard pattern:** lines71–101 assert no existing resources for fixed project `birja-ops-test`, reject occupied owned volumes, and enter `f.installed_recovery(archive)` with a temporary `birja-backup-test-` root. Lines57–68 isolate launcher Git configuration and temporary metadata. Preserve these restrictions rather than inheriting the operator's environment.

**Critical existing scope**, lines121–129:

```python
# Preserve the actual legacy0008 rollout/old-runtime rollback lane.
# Only this private clone receives immutable v0.4.0 application/schema
# bytes; reviewed current retained ops and build instructions remain.
for directory in ("backend/app", "backend/alembic"):
    shutil.rmtree(app / directory)
with tarfile.open(fileobj=io.BytesIO(f.source_git("archive", "v0.4.0", "backend/app", "backend/alembic"))) as archive:
    archive.extractall(app, filter="data")
git("add", "backend/app", "backend/alembic")
```

Thus calling the existing `integration(archive=None)` again does not create0014 evidence. Preserve this legacy lane and add a narrowly named current-schema scenario only if implemented and tested. There is no existing0014 flag or compatibility helper to cite.

**Actual tool and independent preservation assertions**, lines734–757 (selected excerpts):

```python
result = target([str(launcher)])
assert b"Deploy complete" in result.stdout
check_redis_state()
assert selected_query("SELECT version_num FROM alembic_version") == b"0008"
```

```python
result = target([str(launcher), "--rollback"])
assert b"Rolling back" in result.stdout and git("rev-parse", "HEAD") == old
```

```python
assert selected_query("SELECT version_num FROM alembic_version") == b"0008"
assert selected_query("SELECT count(*) FROM transition_fixture.cutover_probe") == b"3"
assert all(fingerprint(name) == value for name, value in originals.items())
assert all(r.digest(path) == value for path, value in retained.items())
```

The existing physical original-volume fingerprint helper is lines570–588. For populated0014 require full canonical ledger/schema/identity comparison as well, using the recovery analog below; the three-row legacy probe is insufficient. Positive claims require actual restricted services, source/image/archive identities and exact pre/post state. At minimum the unsupported old-runtime/schema pair must truthfully refuse with unchanged full state. Do not claim a supported rollback target until exercised.

**Cleanup**, lines771–796: `finally` closes server/lock, stops only owned Compose projects, removes owned candidate volumes, verifies empty project container/network/volume listings and emits `selected_cutover_cleanup_complete=true`. Retain failure-path cleanup and independent resource receipts.

**Runner seam:** `deploy/tests/test-rollback-db-security.sh:42–46` validates synthetic archive path, private sidecar hash and `deploy-recovery-v2` profile. Lines403–409 run existing orchestration self-test, legacy integration, then dynamically load selected fixture and call `selected.integration(args.recovery_bundle)`. Preserve the same explicit archive; do not package a new one per stage.

**Tool caution:** `deploy/deploy.sh:75–78` supports only `main`, `v0.3.1` and retained tested source; lines122–160 bind protected restore evidence to source/snapshot/revision. Lines472–477 restrict rollback SHA but do not prove compatibility with0014; lines500–505 start services while explicitly leaving migrations in place. The permitted-ref set and successful revision-string validation are not runtime/schema compatibility proof. Do not broaden grants, modify immutable migrations, downgrade financial data or perform production rollout to obtain acceptance. If unresolved, record **current0014 selected deployment/rollback compatibility unproven — rollout blocked** and leave the corresponding SAFE-02 clause unresolved.

### Existing exact recovery fixture

**File/analog:** `deploy/tests/ops-fixtures.py`; primary reuse for existing producer/consumer and any narrowly necessary fixture extension.

**Imports**, lines21–27: set `sys.dont_write_bytecode = True`, derive ROOT from file, load `deploy/verify-restore.py` with `importlib.util.spec_from_file_location`, use the loaded module as `r`.

**Retained archive guard**, lines354–363:

```python
def installed_recovery(archive_arg=None):
    """Install once; caller exclusively owns source server, seed and transitions."""
    with tempfile.TemporaryDirectory(prefix="birja-backup-test-") as tmp:
        root = Path(tmp)
        root.chmod(0o700)
        archive = Path(archive_arg) if archive_arg else root / "recovery.tar"
        if not archive_arg:
            r.bundle_package(archive)
        sha = r.private(str(archive) + ".sha256").read_text().strip()
        r.bundle_verify(archive, sha, required_profile="deploy-recovery-v2")
```

Lines425–447 hash archive, installed tools, CORE, inventory, checksums and restic; the context manager's `finally` asserts immutable bytes. `recovery_roundtrip(session, *, source_revision, source_release, inherited=None)` is the actual existing signature at line450. Use it, not an invented restore API.

**Revision-selected real scenarios:** `successor_roundtrips` lines562–619 loops0008–0014, prepares/exercises actual dividend fixture at0014, actual stock runtime at0013, captures `r.canonical` and identity state, then invokes retained roundtrip. Lines630–638 restore and verify exact archive contents:

```python
job.restic('restore', sid, '--target', str(directory), '--verify')
manifest = json.loads((directory / 'manifest.json').read_text())
```

```python
assert all(manifest[key] == before[key] for key in ('tables','financial','revision','schema'))
with r.restored(dc, (directory / 'database.dump').read_bytes()):
    r.verify(dc, manifest)
    assert identity_state(dc, r.CLONE) == sequences
```

**Current0014 replay**, lines659–667:

```python
if revision == '0014':
    r.sql(dc,'GRANT CONNECT ON DATABASE birja_restore_test TO birja_app,birja_scheduler,birja_migrator','birja_ops_test')
    assert dividend_digest(role_python(dividend_program(mode='verify',database='birja_restore_test',expected=dividend_saved),'birja_migrator')) == dividend_saved
    current_runtime = role_python(runtime_program(seed=False,database='birja_restore_test',expected=runtime_digest),'birja_migrator')
    assert runtime_receipt_digest(current_runtime) == runtime_digest
    assert b'runtime_current_mixed_history=true revision0014=true' in current_runtime
    r.verify(dc,manifest)
```

CONNECT here is fixture-only network entry after verified restore, not financial EXEC authority. Preserve owner replay versus app/scheduler42501 quarantine distinctions. Lines668–698 mutate a calendar generation and require verifier refusal, restore it, exercise dumped identity behavior, and assert source canonical/sequence/config/container/mount identity unchanged. Retain all existing negative controls, exact sequence facts and source comparisons; do not replace with samples or `max(id)`.

`deploy/tests/{stock-runtime,dividend-execution}-fixture.py` remain the existing actual source/replay engines reached via `runtime_program(seed=..., database=..., expected=...)` and `dividend_program(mode=..., database=..., expected=...)` at ops lines531–544. Reuse their current validated parameters; no new service API or payout grant is proposed.

### Offline regression and CI contracts

**Files/analogs:** `deploy/tests/test-stock-recovery-contracts.py`, `deploy/tests/test-ci-ops.py`, `.github/workflows/ci.yml`.

**Offline loader**, recovery contracts lines37–43, uses ROOT-relative importlib loading without a framework dependency. `RevisionContracts` lines46–71 checks refusal before SQL/grants. Concrete error-order assertion, lines54–57:

```python
with mock.patch.object(producer,'manifest_sql',return_value=query),mock.patch.object(restore,'recovery_contract',return_value=producer),mock.patch.object(restore,'sql') as sql:
    with self.assertRaises(ValueError):
        restore.dividend_pregrant_structure([])
    sql.assert_not_called()
```

Use mocks only for offline dispatch/order assertions. Real compatibility and money proof still require isolated PostgreSQL and actual retained tools. Existing real privilege regression at lines837–860 checks direct/transitive migrator membership refusal and restored app/scheduler financial denial; do not weaken it.

**CI contract:** `test-ci-ops.py:18–26` parses current job blocks using stdlib regex, `CI` starts at100. `test_same_archive_recovery_rejects_missing_or_reordered_stages` at113 additionally compiles the extracted Python block (line117). Preserve mutation-style omission/reordering tests if the actual block changes. Existing coverage/security preservation at375–395 asserts backend80%/critical100%, pip-audit, frontend coverage/audit/lint/typecheck and exact owned browser runner. Updating a string assertion alone does not prove the new lane executes.

**Core serial campaign**, `.github/workflows/ci.yml:312–335` (excerpts):

```python
archive = Path("/tmp/birja-backup-test-ci-final/recovery.tar")
archive.parent.mkdir(mode=0o700)
ops.r.bundle_package(archive)
expected = ops.r.digest(archive)
source = {name: ops.r.digest(ROOT / name) for name in ops.r.CORE + ops.r.UNITS}
```

```python
unchanged()
ops.image_transition()
unchanged()
ops.roundtrip(archive)
unchanged()
ops.roles()
unchanged()
assert ops.tls() == ops.tls(fresh_bootstrap=True)
unchanged()
subprocess.run(["bash", str(ROOT / "deploy/tests/test-rollback-db-security.sh"),
                "--recovery-bundle", str(archive)], check=True)
unchanged()
```

`unchanged()` lines317–322 checks archive checksum, current CORE/unit file hashes and exact archived/current bytes. Keep stages serial because they share fixed resources. Final `ci-pass` lines347–359 needs backend/frontend/image/e2e/ops and rejects failure, cancellation or skip; the always-cleanup step at337–345 targets only the two owned ops projects. Keep dependency audits, five strict scans and existing coverage thresholds intact.

### Consolidated acceptance and execution evidence

**Files:** proposed `11-ACCEPTANCE.md`, `11-LOCAL-PROOF.md`, `11-VERIFICATION.md`; existing `11-VALIDATION.md`.

**Analog:** `.planning/phases/10-dividend-cash-and-event-history/10-LOCAL-PROOF.md:5–23` records measured six-stage proof with explicit separate scope. Exact scope excerpt, lines19–23:

```text
**Scope:** selected-volume cutover and actual old-app rollback are proven at
**0008**. No old-runtime-on0014 or selected0014candidate-cutover claim is made.
Current0014 proof is exact retained restore plus genuine current owner/service
replay/History/Portfolio and app/scheduler financial quarantine. Plan17 assesses
these facts against the phase goal; Phase11 rollout remains separate.
```

Copy evidence structure from lines10–17 (stage/seconds/outcome),25–40 (actual command, source hashes, archive size/SHA, report/log/receipt identities),42–47 (owned cleanup/image IDs),49–70 (affected-source deltas and lane-specific fingerprints). The1391.017s campaign is historical source7196d5f evidence; it is not a newly executed final Phase11 gate. A matching archive hash alone cannot promote it to new application/image evidence.

**Verification format:** `10-VERIFICATION.md:1–16` records verified date/status/score/review_source and re-verification gaps. Lines41–56 map plan truths to actual source/test/human evidence. Copy structure, never old PASS values. `11-ACCEPTANCE.md` should join each SAFE-02/03 clause to exact behavior, existing test, independent expected oracle, command, source/image/archive identity, actual result/time, safe evidence path/hash, review and blockers. There is no existing fully consolidated Phase11 acceptance ledger; the proposed name is discretionary.

**Validation:** retain current `11-VALIDATION.md` draft status and unchecked execution flags until actual execution. Fill per-task exact commands, existing/Wave0 fixtures, threat identifiers, secure expected behavior and measured quick-feedback budget. Keep long integration gates explicit; do not claim they fit an unmeasured quick-test budget.

## Shared Patterns

### Financial assertions and existing gate inventory

These are existing acceptance inputs, not proposed new implementations. Classify backend test files as **test / request-response, event-driven**; browser specs as **test / request-response**; recovery producer/verifier as **utility / file-I/O**; runner/Compose/manifests as **config or utility / batch**.

| Existing files to reuse without edits by default | Concrete responsibility |
|---|---|
| `deploy/{backup-snapshot.py,backup-manifest.sql,verify-restore.py}` | Exact reviewed producer/consumer; change only a reproduced contract defect |
| `deploy/tests/{stock-runtime,dividend-execution}-fixture.py` | Actual source effects and restored current-service replay; ops call sites above |
| `backend/tests/test_stock_trading_concurrency.py` | Independent sessions, exact counts/cash/positions, shared stock/crypto cash/key contention |
| `backend/tests/test_stock_trading_{waits,service}.py` | Actual post-lock eligibility/expiry and immutable closed replay |
| `backend/tests/test_dividend_{payments,corrections,concurrency,waits}.py` | Exact original/correction/held effects, independent races/waits and replay |
| `backend/tests/test_stock_{ownership,action_resolutions,action_monitoring}.py` | Cutoff/split ordering, once-only basis and uncertain suspension |
| `backend/tests/test_event_history*.py`, `backend/tests/test_portfolio_snapshot.py` | Private tied pagination/original lineage and cash counted once |
| `frontend/e2e/{stocks,stock-actions,stock-trades,dividends-history,portfolio-history}.spec.ts` | Existing accepted discovery/trade/action/Portfolio/History journeys |
| `deploy/tests/run-stock-browser.py`, `frontend/playwright.config.ts`, `docker-compose.test.yml` | Existing owned isolated harness; no substitute runner or install |
| `backend/pyproject.toml`, `frontend/package.json`, `backend/tests/test_critical_coverage_config.py` | Existing locked framework/coverage contracts |

Concrete backend pattern, `test_stock_trading_concurrency.py:23–28`: each request opens its own `factory()` session, calls actual `stock_trading.execute` and maps only `TradeRefused` to its domain code. Lines31–47 independently query cash/counts/holdings. Lines148–157:

```python
async with asyncio.timeout(15):
    results = await asyncio.gather(
        stock_request(factory, uid, settings, trade_order(quantity="1", idempotency_key=key)),
        crypto(),
    )
assert sum(isinstance(r, tuple) for r in results) == 1
assert results.count("idempotency_conflict" if same_key else "insufficient_cash") == 1
cash, counts, positions = await books(factory, uid)
assert cash == 0 and counts[0] == 1
assert counts[1:] in ([0, 0], [1, 1])
```

Retain Decimal/NUMERIC and exact server monetary strings. Browser `dividends-history.spec.ts:14–32` invokes the real fixture only after asserting the owned Compose project. Lines133–145 perform actual preview/Confirm buy, require201 and exact cash1490000n, then actual crypto buy and exact remaining cash490000n; lines148–180 assert held cash unchanged, resolution delta and repeated cycle equality. Use these existing economic assertions; intercepted read-only presentation fixtures are not financial success evidence. Do not generalize that file's cents helper to tiny rates or arbitrary signed currency arithmetic.

### Authentication, authority and public errors

No new HTTP route/auth wrapper is needed. Preserve existing authenticated service/browser gates and owner isolation. In recovery fixtures authentication means exact archive/profile/source evidence, safe role flags, pinned authority definitions and quarantined clone grants; a successful migrator read is not runtime financial permission. Operator error details must not become user-facing messages or public evidence containing secrets. Negative assertions must preserve state and check intended refusal rather than accept any unrelated failure.

### Existing UI acceptance provenance

`10-HUMAN-UAT.md:18–20` binds the reviewed ZIP size15497014/SHA256`cf4e4817bdae885c2feea4c5fe9e6368ef834394a83f618e6bddddaa5fb9845d`; lines29–41 distinguish static presentation from executed financial/browser behavior. `10-VERIFICATION.md:55–56` records actual owner UI and native200% acceptance at source48d970c. Reuse by unchanged scope, assessing final relevant UI, build/dependency/runtime and served-response behavior. Do not infer window dimensions or extend the History packet to unreviewed screens. Material affected changes require scoped renewed owner/native-menu200% evidence; CSS zoom or narrow viewport is supplementary. Preserve the one existing W07 deployed-CSP skip, no new hidden skips. No UI feature or replacement component is planned.

## No Analog Found

| Missing exact behavior | Role / flow | Planner treatment |
|---|---|---|
| Supported populated0014 selected-start/cutover and old-runtime/schema refusal proof | test / file-I/O, request-response | Existing selected fixture is a structural analog only;0008 does not prove0014. Implement bounded assertion in existing fixture or retain explicit unresolved compatibility/rollout blocker. No passing0014 command/API is claimed. |
| Fully consolidated SAFE-02/03 final-source acceptance ledger | evidence / transform | Combine existing proof and verification formats into proposed11-ACCEPTANCE.md; requirement disposition stays pending until actual evidence. |

## Metadata

**Search scope:** deploy retained tools/tests, current CI, focused backend/browser tests, Phase10 evidence and Phase11 research/UI/validation; repository instructions/adapter/current project state read. Five principal pattern families selected: selected compatibility, exact recovery, offline/CI contracts, financial/browser assertions, source-bound evidence. No broad replacement architecture search was needed.

**Files classified:** 10 candidate targets plus grouped existing gates above. **Extraction date:**2026-11-13. Excerpts are actual checked-in source, with omissions explicitly separated; proposed artifact names and missing0014 behavior are recommendations. No integration execution/pass or Phase11 completion is asserted. SAFE-01/Phase7 live campaign, provider rights/access/freshness, production/B2/installed-tool/timer changes, publication and accepted W01–W08 follow-ups remain outside this acceptance map.
