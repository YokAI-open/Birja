# Phase15 — Pattern Map

Mapped2026-11-22. Scope: existing recovery fixtures, finite campaign selection,
restored-request assertions and operator evidence. Five strong analog families
suffice; no application/schema/UI architecture or wider code search is needed.
This is source inspection, not execution or verification of a new change.

## File Classification

| Proposed file/responsibility | Role / data flow | Closest analog | Match |
|---|---|---|---|
| `deploy/tests/portfolio-smoke.py` installed consumer selection | test utility / archive file-I/O + batch restore | `ops-fixtures.py:373–470` installed recovery context | exact lifetime/installation |
| `deploy/tests/run-portfolio-validation.py` finite Phase15 archive selection | CLI utility / batch orchestration | existing constants/preflight and `recovery_operations:373–413` | exact existing entrypoint |
| `deploy/tests/run-portfolio-campaign.py` request/worker/status selection | CLI utility / process receipts | same file `private_directory`, `start`, `inspect_status` | exact existing entrypoint |
| `deploy/tests/portfolio-closure-recovery-fixture.py` restored original requests | test fixture / generated real-service batch | own `program/project/seed` + smoke `closure_role_program` | exact fixture and adjacent replay |
| `deploy/tests/test-portfolio-smoke-image.py` consumer context contracts | unittest / pure validation | own `test_real_smoke_dispatch_requires_the_declared_runtime_factory` | exact seam contract |
| `deploy/tests/test-portfolio-validation-contracts.py` finite selector contracts | unittest / pure validation | existing campaign/runner contracts and smoke contract family | role/data-flow match |
| `deploy/tests/test-portfolio-fixture-contracts.py` and affected recovery contract tests | unittest / generated-code contract | existing generated closure fixture and its contracts | exact current fixtures |
| `deploy/RUNBOOK.md` supported migration/rollback instructions | documentation / operator procedure | existing retained operations/recovery sections at183,362,397 | existing document |
| Phase15 evidence/acceptance records, names chosen by planner | documentation / source-bound evidence map | Phase14 LOCAL-VERIFICATION, RECOVERY-PROOF and VERIFICATION | direct prior-phase analog |

Prefer modifying these existing files. A new test/helper file needs a concrete
reason the existing fixture/contract cannot express the missing assertion.
`ops-fixtures.py` is a source analog, not an automatic modification target.

## 1. Authenticated Installed Consumer With Owned Lifetime

**Source:** `deploy/tests/ops-fixtures.py:373–382,406–432,453–470`.
The existing context manager installs the selected real archive under a private
synthetic root, binds its checksum, yields its release and checks immutable
inputs before its temporary directory is removed. Its core sequence is:

```python
archive = Path(archive_arg) if archive_arg else root / "recovery.tar"
sha = r.private(str(archive) + ".sha256").read_text().strip()
profile = archive_profile(archive, sha)
bind_source_archive(archive, sha)
```

The target command uses the trusted bootstrap verifier's real bundle installer:

```python
"bundle", "install", "--archive", str(archive), "--sha", sha,
"--require-profile", profile, "--synthetic-root", str(root / "host")
```

The selected release is `root / "host/var/lib/birja/recovery/releases" / sha`.
The session exposes `archive`, `archive_sha`, `release`, `tools` and immutable
file digests. Its cleanup assertion is:

```python
assert all(r.digest(path) == value
           for path, value in session.immutable.items())
```

**Apply to:** smoke cold recovery's consumer factory. Select the actual verifier
under the authenticated installed release, with all adjacent genuine retained
source archives present; keep that installation alive for the entire restore.
Do not return a module referencing an already-deleted temporary installation.
Reuse the installation mechanism, not a copy of the whole private Phase14 driver.
This helper also initializes a private restic repository; inspect its concrete
side effects when choosing the smallest reusable factory boundary.

**Current defect:** `portfolio-smoke.py:955` calls `load_recovery()`. The factory
at1092 imports `ROOT / "deploy/verify-restore.py"`; this checkout module lacks
the installed retained-source context. Historical source hashes must not be
repinned to make that selection pass. Preserve default checkout usage only
where a complete selected installation is not required.

## 2. Finite Campaign Identity, Paths and Read-Only Status

**Sources:** `run-portfolio-campaign.py:33–52,97–110,153–204,524–585`;
`run-portfolio-validation.py:25–32,373–413`.

The existing campaign accepts only owned synthetic receipt namespaces:

```python
r"birja-(?:backup-test-[A-Za-z0-9_.-]+|phase14-campaign-[a-z0-9-]+)"
```

It starts one invocation with a durable source-bound request:

```python
request = {
    "format": 1,
    "run_id": uuid.uuid4().hex,
    "suite": suite,
    "source_sha256": source_snapshot(runner),
    "preserved_archive_sha256": runner.preserved_archive(),
}
```

Existing path must refuse on launch; `--status`/`--resume` inspect the original
request, status, claim, source/artifact identity and original process. They do
not start a replacement. The worker is detached with `start_new_session=True`.

**Apply to:** one finite Phase14/15 choice, spelled by the planner, forwarded
consistently through CLI, immutable request, worker, runner, preflight, artifact
snapshot and status. Current `runner.ARCHIVE` is hardcoded to
`/tmp/birja-phase14-proof/recovery.tar.gz`; select an independent Phase15 path
without moving/removing that completed proof. Status must derive the same
selection from the original request, rather than a new default or new CLI value.
Preserve the existing Phase14/default contract and generic backup-test paths.
Do not accept arbitrary archive destinations or add another supervisor.

The existing complete recovery graph already separates operations:

```python
"current0023-cold": lambda: smoke.run(
    archive=archive, archive_sha=expected, revision="0023", cold=True)
```

Retained, roles, upgraded/fresh TLS and rollback remain existing operations.
Keep the full graph executable for CI; local evidence reuse must not remove a
CI operation or call component evidence a successful whole invocation.

## 3. Extend the Real Restored Fixture, Preserve Its Independent Oracle

**Sources:** `portfolio-closure-recovery-fixture.py:98–152,203–295,350–402,
530–588,589–650,694–829`; `portfolio-smoke.py:427–468`.

The fixture generates source-pinned real-service code, checks the exact owned
database and verified TLS before importing the backend, and uses distinct
app/scheduler engines. `program()` currently permits only:

```python
mode in {"create", "projection", "verify", "compare"}
database in {None, "birja_restore_test"}
```

It captures every declared table and identity tail. The output contract is:

```python
return {"revision": "0023", "tables": tables, "sequences": tails}
```

Independent expected economics live in `require_projection`, not in a computed
copy of the seed. Its current roots are Mixed/Active/Crypto/Blank/Zero, four
closed roots, two initialization latches and five original creation records.
Preserve complete31-table/24-tail restore equality before any business replay.

**Existing real replay analog:** `closure_role_program` injects this before the
projection print, retaining actual SQL/service behavior:

```python
for original in value.get('tables', {}).get('portfolio_closure_intents', []):
    async with ReplaySession(app) as replay:
        result = await replay_close_portfolio(replay, ReplayClosureIntent(...))
        assert result.replayed and result.outcome == original['outcome']
```

The elided arguments in this explanatory excerpt are the existing stored
owner/portfolio/key/name/policy fields at smoke:460–463; preserve them exactly.
The injection requires a known marker and raises if that boundary changed.

**Apply to:** a bounded restored-only replay through actual restricted services
using original persisted identities, payloads and original targets. Compare
before-replay exact restore first, then financial payload/effect counts after
replay. Sequence values may legitimately be consumed by attempted inserts;
never reset them or confuse post-business tails with restore equality.

### Concrete Seed Traps for the Planner

- Actual crypto buys in `seed:365–381` exist only for Mixed and Crypto; both are
  closed by392–402. Active has no real crypto fill available to replay. To prove
  a successful active original fill replay, minimally seed a genuine Active
  fill and update independently declared cash/holding/count expectations.
  Preserve separate closed-original refusal/frozen-sibling assertions.
- Creation uses stored `create_portfolio` keys and descriptions; do not invent
  new request identities. Replaying a closed creation must not grant replacement
  cash or create a new active root.
- Dividend targets contain portfolio/event/entitlement and expected revision/
  entitlement fingerprints at538–548; actual `process_dividend` runs under the
  scheduler session. The fixture later appends an uncertain revision and hold.
  Respect the real service's current revision/refusal policy when specifying
  expected replay outcomes; do not rewrite event evidence merely to force a
  successful response. Financial effects and original identities must stay
  unchanged whether the correct retry outcome is original replay or refusal.
- Seeding original operations is not post-restore replay. Place the new check
  explicitly on `birja_restore_test`, after restore/oracle validation, with
  retained original keys and counts; require a real receipt for that step.

## 4. Use the Existing Focused Offline Contract Style

**Source:** `test-portfolio-smoke-image.py:1–28,396–434`.

Tests load the actual hyphenated Python modules with importlib and patch narrow
transport/factory seams to verify dispatch before any database command:

```python
spec = importlib.util.spec_from_file_location(name.replace("-", "_"), path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
```

The existing dispatch case raises a recognizable factory sentinel, verifies the
real `smoke.run()` reaches it and asserts `factory.assert_called_once()`.
Use that style for finite selector propagation and consumer lifetime/signature
contracts. These pure contracts do not replace real restore/financial results.

**Signature traps:** cold recovery currently supplies
`restored(..., manifest=source_manifest)` and
`verify(..., quarantined=revision != "0023")`. Mocks must accept and assert
these exact arguments. A version probe during genuine bundle authentication
is not a container launch; tests should distinguish these effects rather than
fail on every allowed tool-metadata call.

## 5. Reuse Operator and Acceptance Record Structure

**Sources:** RUNBOOK retained operations/recovery at183,362,397; existing
Phase14 LOCAL-VERIFICATION, RECOVERY-PROOF and VERIFICATION.

Keep executable operator instructions in RUNBOOK and per-phase proof/acceptance
records in15's directory. Use one concise support/refusal table, source/input
reuse table and requirement→actual assertion/receipt map. Include custom migrated
baseline evidence from the genuine0014 upgrade; a new10000 baseline is not that
migration. Keep existing12/13/14 actual owner approvals for unchanged screens.

## Shared Patterns and Scope

- Existing authenticated producer/consumer, private owned roots, exact archived
  source/image identity and cleanup; no alternate backup or orchestration format.
- Real backend transactions and restricted roles own financial semantics;
  test drivers only select inputs and assert independently expected effects.
- Run affected contracts after small changes and one matching current archive
  proof when archived tooling changes. Explicitly scope evidence invalidation;
  backend/frontend/browser/image inputs do not all change with an ops fixture.
- Keep failed whole-run history and require full hosted CI before merge. New
  plans do not broaden issue35, Phase7 activation, package or production scope.

## No Analog Found

No missing framework or architectural analog. The new restored creation/fill/
payment assertion is a concrete behavior gap covered by the existing service
and generated-fixture patterns above; it needs no new abstraction.

## Metadata

Source inspection only,2026-11-22. Search scope was the five named recovery/
contract families and existing RUNBOOK headings. No tests, browser, Docker,
service, provider, install, source modification or Git operation was performed.
Only15-PATTERNS.md was written; other agents' work is preserved.
