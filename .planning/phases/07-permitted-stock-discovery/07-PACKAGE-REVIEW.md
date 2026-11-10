---
phase: 07-permitted-stock-discovery
plan: "07"
task_completed: 07-07-01
status: awaiting-blocking-human-package-approval
reviewed_at: "2026-11-10T15:27:00Z"
package: exchange_calendars
version: 4.13.2
legitimacy_protocol: ASSUMED
owner_approval: pending
---

# Calendar package review and continuation handoff

Task 07-07-01 is complete. Task 07-07-02 remains a blocking human checkpoint.
No calendar dependency was installed, imported or executed. Project dependencies,
lock, virtual environment, Dockerfile and CI were unchanged by this review.
Six preceding plans are complete; this packet does not complete Plan 07 or MKT-01.

## Exact candidate and provenance

Public official sources were fetched on 2026-11-10 over verified HTTPS using
Python's standard-library HTTP client. Package archives were inspected as data;
no downloaded package code or build backend was executed.

| Evidence | Observed result |
|---|---|
| [Official versioned PyPI metadata](https://pypi.org/pypi/exchange_calendars/4.13.2/json) | Name `exchange_calendars`, version `4.13.2`, unyanked wheel and sdist |
| Normalization | `exchange_calendars`, `exchange-calendars` and `exchange.calendars` normalize to `exchange-calendars`; import is `exchange_calendars` |
| [Official release](https://github.com/gerrymanoim/exchange_calendars/releases/tag/4.13.2) | Published 2026-03-10T03:24:04Z; tag is `4.13.2`, without a `v` prefix |
| [Immutable source commit](https://github.com/gerrymanoim/exchange_calendars/tree/dbe38b1f6887434bbdd1a7d2df6ff8f1742a048a) | Tag resolves to `dbe38b1f6887434bbdd1a7d2df6ff8f1742a048a`; commit timestamp 2026-03-09T11:55:12Z |
| Signature status | Lightweight tag points directly to commit; GitHub commit verification says `unsigned`, not cryptographically verified |
| [Pinned build metadata](https://github.com/gerrymanoim/exchange_calendars/blob/dbe38b1f6887434bbdd1a7d2df6ff8f1742a048a/pyproject.toml) | SHA256 `0624504db59140714e6d12dd5039009e6517e20e88017c2e8989cf961645a266`; matches wheel name/version/dependency metadata |
| Python declaration | `>=3.10,<4` and explicit Python 3.14 classifier; upstream Python 3.14 test group requires numpy>=2.3.2 and pandas>=2.3.3 |
| License | Apache-2.0 in wheel metadata/tagged source; tagged LICENSE SHA256 `e35c4578f7db4498e62e278978f6c42e0fce6f21f9993a060b08a33549cd3044` |
| PyPI provenance endpoint | Versioned wheel `/integrity/.../provenance` returned HTTP 404; no attestation was obtained or verified |

The registry wheel is
`exchange_calendars-4.13.2-py3-none-any.whl`, 213306 bytes, uploaded
2026-03-10T03:24:37.055242Z. Its downloaded bytes match the registry SHA256:
`fc5a2ad0d61b5c3a6539a3061cd4cbb55c59f4a903455cec7926e4b798919996`.
The sdist metadata SHA256 is
`a9459425dd64142cd54fbc639847403c7e0c33d60fbc326c94fc1d6bd127f002`
(uploaded 2026-03-10T03:24:38.536533Z); the sdist was not downloaded or built.
Registry URLs and hashes identify artifacts, not an independent authenticity
signature or a finding that their complete code is safe.

The wheel has no `.pth` or `.data/scripts/` startup payload. Its declared console
entry point is `ecal = exchange_calendars.ecal:main`; it was not invoked.
The wheel's `exchange_calendar_xnys.py` exactly matches the immutable tagged file,
SHA256 `baa39f07163abafcf2800b69edc5d920c3db0a64f8bbb30dc7d522883d0b5bd7`.
This sampled source equality is not a complete wheel-to-source reproducible build.
No standalone Nasdaq-named calendar source file was present; Plan 08 must test
the package's Nasdaq alias and both exchange scopes against official fixtures,
rather than inventing or assuming a separate Nasdaq algorithm.

## Actual prospective resolution

Installed resolver: `uv 0.13.5`. A wheel-only metadata resolution targeted ordinary
CPython 3.14, Linux x86_64 GNU/glibc; Python downloads and configuration discovery
were disabled. There was no environment installation. Command:

```bash
uv pip compile /tmp/birja-phase07-calendar-review.in \
  --python-version 3.14 --python-platform x86_64-unknown-linux-gnu \
  --only-binary :all: --no-python-downloads --no-config --no-cache \
  --default-index https://pypi.org/simple --generate-hashes \
  --output-file /tmp/birja-phase07-calendar-review.txt
```

Input is exactly `exchange_calendars==4.13.2`. Resolution succeeded for these
eight packages. Official versioned PyPI metadata for every row was fetched;
all listed wheels are unyanked. All seven dependencies are new to Birja's lock.

| Distribution/version | Dependency path and Python declaration | Candidate wheel SHA256 from official registry |
|---|---|---|
| [exchange-calendars 4.13.2](https://pypi.org/pypi/exchange-calendars/4.13.2/json) | Direct; >=3.10,<4; universal py3 | `fc5a2ad0d61b5c3a6539a3061cd4cbb55c59f4a903455cec7926e4b798919996` |
| [numpy 2.5.4](https://pypi.org/pypi/numpy/2.5.4/json) | Calendar + pandas; >=3.12; cp314-cp314 manylinux_2_27/2_28 x86_64 | `d549420b8858885cea8838a727842249218b9c1da24dd517e25c9c7a948310a3` |
| [pandas 3.1.1](https://pypi.org/pypi/pandas/3.1.1/json) | Calendar; >=3.11; cp314-cp314 manylinux_2_24/2_28 x86_64 | `326459d8a9be11b5f48c7fc1d63e38ba7cfeaebe5d41bd19e4c5f4f11dc9ac91` |
| [pyluach 2.3.0](https://pypi.org/pypi/pyluach/2.3.0/json) | Calendar; >=3.8; universal py3 | `4497b731aef59508b079dbf5f00bc5bf4329ac45090a6cd37b5a83756f0e69ab` |
| [toolz 1.2.0](https://pypi.org/pypi/toolz/1.2.0/json) | Calendar; >=3.9; universal py3 | `890f820b1cb8152785aaf9386d8707770110809035800985ca65cb24ce1120ef` |
| [tzdata 2026.6](https://pypi.org/pypi/tzdata/2026.6/json) | Calendar + python-dateutil; >=2; universal py2.py3 | `0a10eec6e13ef16b627fabed9a5f2ba61a62b1c67f327305f4e7e412a70b4aec` |
| [korean-lunar-calendar 0.4.0](https://pypi.org/pypi/korean-lunar-calendar/0.4.0/json) | Calendar; >=3.6; universal py3 | `c042e20de0bb702add6bec8d0f6da1ea8d3b170838e63846f70420cf341fe4e7` |
| [python-dateutil 4.0.0](https://pypi.org/pypi/python-dateutil/4.0.0/json) | pandas; >=3.11; universal py3; itself requires tzdata | `a5e246f79eb80475e691bf93862cead98decd8a498cf53ba0516fcdc0f50dc1c` |

Direct declared lower bounds are numpy>=1.26.4, pandas>=1.5.0, pyluach>=2.3.0,
toolz>=1.0.0, tzdata>=2025.2 and korean_lunar_calendar>=0.3.1. For Python 3.14,
pandas 3.1.1 requires numpy>=2.3.3 and python-dateutil>=2.9.0. Optional pandas
extras were not selected. The seven dependency wheel hashes above are registry
metadata observations; their bytes were not independently downloaded/hashed and
their full source, signatures and build provenance were not audited.

A second wheel-only resolution included every production/dev/audit requirement
from Birja's pyproject, constrained every existing lock package to its current
version, and added the exact calendar candidate. It succeeded with the same eight
additions and **zero existing version changes**. No project lock was written.
The resolver emitted three warnings normalizing a `>=3.6.*` metadata specifier
to `>=3.6`; the output did not identify its originating package. This is recorded
as metadata uncertainty, not silently edited in project files. The initial
inspection command combined mutually exclusive `--no-build` and `--only-binary`
options and failed before resolving; removing `--no-build` while retaining
`--only-binary :all:` produced the successful non-building inspections above.

## Remaining uncertainty and required proof

The legitimacy protocol remains **ASSUMED**, not passed. Installed
`slopcheck 0.6.1` cannot perform the research protocol
`slopcheck install exchange_calendars --json`: `install` lacks that flag and
actually installs packages. Its separate `scan` command has a JSON option, but
that is not the requested install protocol; no clean scan/install verdict or
allowlist approval is claimed. No slopcheck installation was attempted here.

PyPI identity, release/tag metadata, one wheel byte hash, source sampling and
resolver compatibility are established. Package safety, compatible imports,
full calendar correctness, NumPy/pandas native library loading, and clean image
scans remain unproven. Recent major-version dependencies pandas 3.1.1 and
python-dateutil 4.0.0 require actual runtime compatibility proof. No unreviewed
version substitution, fallback source build or alternative holiday algorithm is
authorized if that fails. The GNU/glibc resolution does not establish the
actual Wolfi image's loader/native dependencies. Source metadata declares Python
support; it does not establish passing Birja tests.

After explicit approval, Plan 08 must:

1. Add only `exchange_calendars==4.13.2` through project `uv add --no-sync`,
   review `backend/pyproject.toml` and the committed `backend/uv.lock` before
   installing. Confirm precisely the eight versions above, registry sources and
   matching wheel hashes, preserving every existing locked version. If resolution
   differs materially, return the difference for review before installing it.
2. Install from the reviewed lock using uv and wheels only, with source builds
   disabled (`uv sync --locked --no-build`). Never use project pip/global installs,
   execute a downloaded setup/build backend or substitute another package.
3. Implement Plan 08's RED/GREEN official-session fixtures and fail-closed
   authority/expiry/generation evaluator, proving NYSE/Nasdaq regular sessions,
   holidays, early closes, DST and exceptional closure overrides. Calendar code
   creates derived bounds; it cannot establish authoritative admission evidence.
4. Build **both actual targets** in `backend/Dockerfile` with the reviewed lock,
   retain the Python 3.14 hardened Wolfi base/pin and nonroot runtime. Run imports
   for exchange_calendars, NumPy and pandas plus the bounded session smoke in the
   actual runtime image. Record source/lock and image digests. Keep calendar
   floating-point internals out of Decimal quote/money calculations.
5. Run existing `pip-audit` and strict actual-image Trivy gates through
   `deploy/scan-images.py` / `.github/workflows/ci.yml`, including the builder,
   runtime and the other three image lanes. **HIGH/CRITICAL including unfixed**
   remain blocking; no ignore file, reduced severity or base/interpreter change
   is approved. Final full coverage/security/integration proof remains Plan 13.

Reviewed unchanged targets (SHA256):

| File | SHA256 |
|---|---|
| backend/pyproject.toml | `326e66d083d35513b34190fe6e40a4070c5ac17e9e9660175bd0a2cbe7dc7a60` |
| backend/uv.lock | `ac547921306b90d312450b007325a785ebd7799f775e08ad856bcf4f7e0b7954` |
| backend/Dockerfile | `e7fc0740fdf1423f368d688181e582285f967b30c501a8ce99c73b7951a12cf5` |
| .github/workflows/ci.yml | `349cffc06f7d2f010652fb8961f19a5d40e7e528826467db63e2f09de4a7c633` |

## Blocking checkpoint and resume

**Question:** Approve `exchange_calendars==4.13.2` with the seven exact dependency
versions reviewed above for Birja's project uv lock and isolated local
installation/testing, accepting the documented unsigned/missing-attestation and
unsupported-protocol uncertainty while retaining all runtime/security gates?

This is approval of a bounded dependency change, not a safety certification.
Provider permission/access, private API calls, agreements, payment, production
installation/deployment, push/PR/merge remain separate. If declined, stop before
installation and request a scoped calendar-source/dependency decision; do not
invent an exchange holiday algorithm.

### Recorded owner approval — 2026-11-10

The owner answered **“Approve reviewed dependencies and continue local execution”**
to the explicit 07-07-02 question naming exchange-calendars 4.13.2, numpy 2.5.4,
pandas 3.1.1, pyluach 2.3.0, toolz 1.2.0, tzdata 2026.6,
korean-lunar-calendar 0.4.0 and python-dateutil 4.0.0. The question disclosed the
unsigned source commit, missing wheel attestation and unverified installed
legitimacy protocol, and retained runtime/image compatibility and strict scans.
This is actual explicit approval, not inferred from yolo mode or silence.

The package checkpoint is satisfied for this exact resolution and bounded project
lock changes plus isolated local installation/testing in Plan 08. This record
does not change ASSUMED protocol status or establish package safety. Materially
different resolution still requires review before installation. Production,
provider access, payment, publication and waiver of any security gate are excluded.
No package or project lock was changed while closing Plan 07. Plan 08 is next;
requirements remain pending whole-phase verification. Root removed only the disposable
birja-test containers/network after Plan 06; start the isolated test stack again
when subsequent DB tests need it. Temporary public-only review inputs/resolutions
are under `/tmp/birja-phase07-*`; committed evidence is this packet.

Verification: `git diff --check` must pass before committing this packet and its
scoped STATE handoff. Read-only documentary work does not need application tests.
