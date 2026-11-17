---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "27"
status: passed
verified: 2026-11-17
source_commit: 1f8d5a4eb500dad879440c2f2ebba892b8b5f65c
source_tree: 795b50bace62d54e0a2719c66a013f9198de2cf2
---

# Phase 12 Local Automated Qualification

The actual complete security runner passed from start to finish. This is a
local synthetic qualification, not hosted CI, owner acceptance or deployment.
The independent complete seven-stage recovery proof is recorded in
[12-RECOVERY-PROOF.md](12-RECOVERY-PROOF.md), with its original source identity
and explicit equivalence to the final executable inputs.

## Complete Security Campaign

Command: `python3 deploy/tests/run-portfolio-validation.py --suite all-security`.
The existing runner and all thresholds remained unchanged. Its stripped test
environment used fake prices, console email and exclusive disposable PostgreSQL/
Redis. Exact checks found no preexisting owned resources or competing test.

| Campaign | Measured result |
|---|---|
| Committed source |1f8d5a4eb500dad879440c2f2ebba892b8b5f65c |
| Tree |795b50bace62d54e0a2719c66a013f9198de2cf2 |
| Start / finish |2026-11-17T15:30:36.796961Z /15:56:18.068164Z |
| Whole command |Exit0,1541.269seconds,25min41sec |
| Source freeze |Zero changed tracked files during the complete command |
| Backend lint/format/types |Ruff227files and mypy101application sources pass |
| Complete backend |3108/3108pass,136warnings,856.87seconds |
| Overall branch-inclusive coverage |99.8537477%;6409statements/1796branches,8missing lines/4missing branches |
| Exact CI critical inventory |All60modules100%;5020statements/1604branches, zero misses/partials |
| Python audit |No known vulnerabilities |
| Frontend lint/types/whole formatting/build |Pass |
| Complete frontend |44files/958tests pass; statements97.50%,branches94.65%,functions98.58%,lines98.68% |
| npm audit |Existing high/critical gate passes;14MODERATE findings remain, not zero total findings |
| Complete browser |All60collected,59pass/1original deployed-CSPskip,536.7seconds; no added skip/filter/retry |
| Actual declared images |Backend test-builder/runtime and frontend toolchain builds pass; pinned PostgreSQL/Redis/scanner pulls pass |
| Containerized smoke |5/5pass,2.11seconds |
| Strict images |All five0HIGH/CRITICAL, including unfixed findings; immutable identities and fresh Trivy0.76.1database metadata verified |

The existing CSP skip is the retained production-only header test; this local
proof does not establish deployed CSP. Existing warnings and npm moderate
findings are disclosed, not silently waived or repaired with unapproved packages.
Overall80% and exact critical100% gates, all old suites and economic/security
assertions remain enforced.

The final immutable scanned IDs are:

- Runtime: sha256:0ad71010b061b4566d9c5d80087f55ebdeddf0e4d7c64ba226ed375abdf71aac.
- Builder: sha256:1df571a3bf1c58da6433be34eff75ed35bb1196d3c8ef68933efa133a6d2c268.
- Node: sha256:8b4a71c8c05ea21d9a2bafc02d4b842b900d5f659a0d823bef6ba869eceab18b.
- PostgreSQL: sha256:adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de.
- Redis: sha256:26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48.

## Source-Bound Evidence

Private complete log, source inventory and atomic result are
`/tmp/phase12-27-security-finish-second.log`, `.source.json` and `.result.json`.
The browser child evidence is `/tmp/birja-phase09-browser-tkan1g3j/browser-all.log`.
Read-only preserved copies, clean coverage data, coverage JSON and every final
image report are under `/tmp/phase12-27-qualified-final-1f8d5a4/`, with SHA256.json.
Generated root image-reports were hash-verified and preserved outside the repo
at `/tmp/phase12-27-final-image-reports-working`; no generated output is left
untracked in the working tree.

This final campaign is distinct from all earlier failed/interrupted diagnostics.
Their detailed repair receipts remain in12-27-AUTOMATED-CONTINUATION.md.
The immediately preceding attempt atfacfa1e was deliberately interrupted only
after its real migration block finished:1465passed/1failed, not a full result.
The actual failure showed a supposed later split occurring before the current
session's dividend cutoff during the first opening hour. Owning12-13 fix1f8d5a4
selects a genuinely completed reviewed session and asserts cutoff ordering.
Eighteen deterministic NYSE/Nasdaq open/close, holiday, early-close, weekend and
DST cases are RED before/GREEN after;61real entitlement/split/ownership cases
pass. Runtime entitlement semantics and original exact-money assertions did
not change. The final complete3108case run includes that regression.

## Current Owner Review Packet

Combined read-only owner ZIP:
`/tmp/birja-phase12-ui-review-owner-1f8d5a4.zip`.
SHA256:c87cb4a3eb3feb52c42a37aa60ff69cce66d2ac8e2637847e6a977af1714d55f.
Extract and open its top-level index.html.

The combined ZIP preserves both original packets and their manifests:

- Main: `/tmp/birja-phase12-ui-review-final-e61f89b-retry1.zip`,
  SHA256:935963b10965a9b343a1da4b09a3eebf5b2e8ac8fa47c6f416a0d87c8de61eac.
  Its actual full browser proof passes59/1original skip atfacfa1e, with102
  rendered artifacts and249covered source hashes. All249still match1f8d5a4.
- Zero/multiple supplement: `/tmp/birja-phase12-ui-review-zero-many-1f8d5a4.zip`,
  SHA256:86d073b1a4adfc3225e1d65d544f67c676bb9bb57e47043185055277e41ac7d8.
  This is explicitly capture-only, not another test-suite result. It uses the
  unchanged guarded renderer/seed/cleanup and existing installed Playwright to
  show actual zero/multiple states at320/768/1280. Each capture checks the safe
  heading, zero financial requests, email-only identity, no cash or actionable
  order and no page overflow. Twelve inert HTML/PNG artifacts pass source/hash
  verification; the synthetic project cleans completely.

`PROVENANCE.json` preserves both render commits, identical249source inventories,
original ZIP hashes and private capture-script/runner SHA256 values. The combined
manifest verifies120copied/provenance/index files; original ZIPs remain unchanged.
The private supplementary receipt/source record is
`/tmp/phase12-27-zero-many-capture.result.json` /`.source.json`.
Its runner SHA256 is902ef7bdd6f6511bcde7bb7dc057ae03bc84485a3bd4c893a4dc9a2032c2dded.
The private capture script SHA256 is847afdbba3488c572a58d3b4c420f15145bb3e5887d37f739358c2db19c8ee35;
wrapper SHA256:ca91ef8a367890a9698698f91359513395851d61d7913380959ad3a1f195949d.

Loaded320px crypto receipt,1280px stock receipt,320px zero and1280px multiple
states were visually inspected. Names remain escaped/wrapped and controls
readable. Automated reflow and these inspections do not establish owner
acceptance or genuine native200% zoom. Both remain blocking in
[12-HUMAN-UAT.md](12-HUMAN-UAT.md).

## Final Boundary

All five exact owned test projects have zero containers/networks/volumes; no
test/migration child remains. Source and qualified recovery archive are intact.
Only unrelated.claude/ remains untracked and untouched. No new dependency,
provider call, private production configuration, B2 access, publication, merge
or deployment occurred. Phase7's consumed campaign, six pending requirements
and disabled live stock admissions are unchanged. Plan28 and final phase
reviews/goal verification remain; no phase or requirement completion is claimed.
