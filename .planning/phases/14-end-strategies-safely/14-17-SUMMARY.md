---
phase: 14-end-strategies-safely
plan: "17"
subsystem: testing
tags: [playwright, portfolio-deletion, lifecycle, privacy, evidence]
requires:
  - phase: 14-14
    provides: accepted implementation contracts for deletion and stale-route privacy
  - phase: 14-16
    provides: reviewed legacy transition and isolated recovery qualification
provides:
  - eight real public deletion behavior journeys and six responsive capture cases
  - separate source-bound Phase 14 read-only review packet with strict refusal contracts
affects: [14-18, 14-19]
tech-stack:
  added: []
  patterns: [read-only lifecycle oracle, source-bound inert review family]
key-files:
  created:
    - frontend/e2e/portfolio-deletion.spec.ts
    - frontend/e2e/portfolio-review-capture.ts
    - .planning/phases/14-end-strategies-safely/14-UI-EVIDENCE.md
  modified:
    - frontend/e2e/portfolio-strategies.spec.ts
    - frontend/e2e/portfolio-browser-fixture.py
    - deploy/tests/run-stock-browser.py
    - deploy/tests/test-portfolio-browser-contracts.py
    - deploy/tests/portfolio-ui-evidence.py
    - deploy/tests/test-portfolio-ui-evidence.py
key-decisions:
  - All current browser closure setup uses authenticated public DELETE, never privileged direct closure.
  - Keep Phase 13/default evidence compatible and require an explicit independent Phase 14 inventory.
  - Keep owner and native zoom acceptance false until the separate Plan 19 human result.
requirements-completed: []
duration: 44min
completed: 2026-11-19
---

# Phase 14 Plan 17: Public deletion journeys and source-bound UI evidence

**Actual routed deletion, finance-free stale recovery and 114 captured lifecycle
states are verified without changing application or database authority.**

## Performance and commits

Execution receipts use UTC; the workstation timezone may show November 20.
The first RED commit was recorded at `2026-11-19T22:54:02Z`; closeout followed
the canonical capture at `2026-11-19T23:34:14Z`. Two tasks completed locally.

| Task | Commit | Result |
| --- | --- | --- |
| 1 RED | `fdc6600` | Independent 13th-spec registration contracts fail against the old 12-spec runner |
| 1 GREEN | `e4f967b` | Real public deletion journeys, guarded READ ONLY oracle and six-width captures |
| 2 RED | `5f0b2bc` | Independent 19×6 packet matrix and active-content refusal failures reproduced |
| 2 GREEN | `413c25d` | Explicit Phase 14 evidence family, strict source/artifact/ZIP verifier and capture metadata |

The final documentation commit records this summary and `14-UI-EVIDENCE.md`.
No changes were pushed. Global state, roadmap and requirement completion remain
the parent orchestrator's responsibility; this plan alone completes no whole
requirement.

## Task 1 results

The 13th registered spec contains eight real behavior cases and six actual
capture cases. It preserves all 12 older specs and the deployed-CSP skip. Real
authenticated create/trade/DELETE proves named Cancel without a request or DB
change, held-asset freeze, closed private routes/cursors/quotes/original retries,
last-book signed-in zero across reload/Back/sign-in and explicit new-ID funding.
It covers committed response loss, delayed unsent original requests, siblings
trading while the target is unknown, same-name replacement isolation, durable
rename 409, unavailable storage before sending, two-tab unknown fills and late
owner/session A→B→A callbacks. Active GET never clears unknown deletion state.

The private lifecycle oracle guards the synthetic owner and owned stack, asserts
PostgreSQL READ ONLY, and compares exact retained JSON text. It includes account
cash/start/identity and all financial tables; no float-based money comparison or
closure mutation is used. The three older empty-state fixture calls now issue
public DELETE too. The additional capture helper leaves Phase 13 capture source
unchanged.

| Actual run | Result and elapsed |
| --- | --- |
| Last-book bounded journey | 1 passed, 47.789s complete stack; browser 15.8s |
| Eight behavior cases | 8 passed, 124.555s complete stack |
| First 320px capture diagnostic | 1 passed, 60.415s complete stack |
| Full new spec, all six widths | 14 passed, 313.989s complete stack; browser 279.1s |
| Strengthened exact account-financial comparison | 1 passed, 53.714s complete stack |
| Registration/isolation contracts | 8 passed, 0.279s final run |

These are measured disposable DB/integration exceptions to routine 60-second
targets. No unnecessary full-spec rerun followed the passing 14-case run: the
strengthened oracle used its single affected case, and final evidence generation
used only the six capture cases.

## Task 2 results

Source was committed as `413c25dcc8500c248a0343a9ce7063f4403435be` before
the exclusive canonical capture. All six capture cases passed in 224.794s total
(browser 186.5s), with unchanged source. The packet is
`/tmp/birja-phase14-ui-review.zip`, SHA256
`3cb80b86097dd6a208da379ac89f4d58d4ed72c98ff9f17e68bdd0bf49fe6f51`.
Its 365-input digest is
`ea4981cf430a64d030c7693fc55dd7b4d74ac604251a7cc3cf89a7863ce30c16`.

All 19 required states at six widths yield 114 HTML captures, 190 PNGs, 114
sanitized timing traces and an index: 419 independently enumerated hashed
artifacts plus manifest. The verifier refuses source drift, missing/extra or
coherently omitted entries, altered bytes, incorrect PNG dimensions, forged
metadata/trace/layout/acceptance, active content and unsafe/duplicate ZIP members.
The existing 12 Phase 13 contract methods/default interface remain intact.

The final evidence suite passed **21/21 in 2.825s**. Read-only current-source,
artifact and ZIP verification returned `CURRENT SOURCE AND ARTIFACTS VERIFIED`.
The extracted HTML was then opened in actual installed Chromium `156.0.8078.4`
at all **190 layouts**, with one visible h1, no horizontal overflow, loaded fonts,
no active forms/scripts/frames and zero HTTP(S) requests. These measurements
are viewport reflow, not native browser-menu zoom. Both human flags remain false.
The evidence document lists the complete state inventory and inspection limits.

## Deviations and repaired local blockers

1. **[Rule 2 — proof completeness, parent-approved scope amendment]** Added a
   Phase 14-only capture helper and guarded READ ONLY finance oracle. Replaced
   three older privileged zero-state setups with public DELETE. No runtime,
   admission, migration or package change was needed.
2. **[Rule 3 — immutable migration fixture ordering]** Initial startup failed in
   18.136s because the runner precreated a scheduler role whose inherited ACLs
   are rejected by the exact legacy 0014 profile. Removing all prerequisite
   roles then failed in 11.916s because immutable 0011 requires the operator.
   The final runner provisions only the source-required operator and temporary
   migrator before legacy seed; genuine current bootstrap provisions scheduler
   afterward. Legacy/runtime authority contracts were not relaxed.
3. **[Rule 1 — test helper contract]** The first behavior campaign had two passes
   and six fixture failures in 99.481s: CSRF correctly returns 204, not the helper's
   assumed 200; the old OTP reader could select an earlier consumed delivery.
   Corrected the status assertion and used a fresh delivery-event cursor, which
   also permits legitimately repeated random code digits. The subsequent eight
   behaviors and full 14-case run passed.
4. **[Rule 2 — packet integrity]** Expanded source inputs to include omitted
   build/configuration bytes and strict committed-input admission. Added explicit
   narrow-layout metadata and independently checked PNG/ZIP correspondence.

All repairs stayed in the local fixture/evidence scope. No authentication gate,
dependency approval, production operation or user checkpoint was encountered.

## Static checks, cleanup and preserved authority

Scoped TypeScript ESLint, Prettier and `git diff --check` pass. An additional
diagnostic Ruff scan reports six pre-existing findings: three non-executable
shebangs, two preserved ValueError/type checks and the old legacy fixture's
blocking subprocess in async code. Baseline comparison confirmed the existing
evidence findings; no new Ruff finding was introduced. This is not presented as
a clean whole-source lint gate; Plan 18 owns the required full checks.

Every successful disposable run recorded unchanged source and no remaining owned
containers, networks or volumes. Durable PID/start-tick/source/log/exit receipts
are under `/tmp/birja-phase14-plan17/`; `canonical-r1.json` and `offline.json`
bind the final package and portable inspection. No active browser/DB process
remains. Unrelated untracked `.claude/` is preserved.

Phase 13 UI ZIP remains `724607e83592bd1bda5e86a0b92217478aba93b53127b7cdf5f2d04f0142c361`.
Phase 13 recovery remains `6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92`.
Plan 16 R3 remains `7a698a7667efc0c3ff6b7545dabd89e969d6f4d9adcd5fde5d93b9f5a19aceff`.
Plan 15 R4 was not modified. The canonical Phase 14 recovery archive remains
absent for Plan 18. Existing issue 35 scope/expiry, security thresholds and image
pins are unchanged. No provider calls, production access, installations or
publication occurred.

## Remaining gates

- Parent independent review of these changes and packet provenance.
- Plan 18 full all-browser/backend/security/recovery integration, including
  rechecking the current packet against final render inputs.
- Plan 19 actual owner UI acceptance and genuine desktop native 200% result.

No product stub was introduced. Synthetic refusal, unknown-response and review
snapshots are intentional test inputs, not disconnected application features.
The new file-access boundary is process-only synthetic evidence/oracle tooling,
guarded and tested; no new public endpoint or runtime authority was added.

## Self-Check: PASSED

All four task commits exist. The new spec/helper, evidence document, summary,
canonical manifest/ZIP and durable run receipts exist. The complete packet passed
current-source/artifact/ZIP verification; its source binding remains current
after documentation-only closeout. Human acceptance is explicitly pending.

## Independent-review repair follow-up

The parent review committed as `70342c2` identified two blockers in the packet
boundary, not the application runtime: linked-directory inventory omission and
unsupported SVG/missing-policy acceptance. The original review remains unchanged.
This follow-up supersedes the earlier packet/current-verification identity while
retaining the historical proof and its limits.

Repair commits:

- `8f36c8b` — RED: controlled linked-root/child/ancestor/font/configuration tests
  and benign SVG/CSP regressions reproduced four refusal failures plus the absent
  Phase 14 validation interface.
- `470093b` — GREEN: no-follow descriptor traversal/read, static icon vocabulary,
  exact early Phase 14 CSP, coherent hash-updated packet refusals; 25 methods pass.
- `4a0ac10` — final benign pre-policy html/head style refinement; two additional
  failing subcases reproduced before the minimal structural whitelist repair.

No-follow traversal examines every relevant ancestor/entry before exclusions or
file filtering. File reads reject links and nonregular types. Ordinary controlled
source mutations change the snapshot; linked target mutations continue to refuse.
Only the absent optional public root and ordinary `__pycache__` exclusions retain
their existing meaning. Static SVG is limited to the four elements used by
current icons. Both Phase 14 index and captures require one exact restrictive
policy before content, with only inert html/head/charset scaffolding preceding
it. Phase 13 defaults remain explicitly compatible. All tests are benign;
no executable payload, browser dialog or external network test was run.

Final contracts: **25/25 evidence methods, 4.012s**, preserving the original 21;
**8/8 browser contracts, 0.290s**. Scoped Ruff retains only the already documented
baseline findings. Diff checks pass. No runtime, API, migration, SQL authority,
dependency or capture-helper change was needed. The eight behavior cases were
not unnecessarily rerun.

The original canonical R1 directory/ZIP was moved to exclusive
`/tmp/birja-phase14-ui-review-r1-historical[.zip]`, preserving SHA256
`3cb80b86097dd6a208da379ac89f4d58d4ed72c98ff9f17e68bdd0bf49fe6f51`.
`canonical-r1-preservation.json` records its source/digest/hash. Intermediate R2
was intentionally interrupted for the final scaffolding refinement at 60.591s,
exit -2, source unchanged. It is explicitly **INCOMPLETE**, with no canonical
packet created. Raw partial captures and supervision receipts remain preserved.
The process-group interruption bypassed automatic cleanup, so exact owned-project
cleanup and separate empty resource/process-group checks were completed before
source edits. See `canonical-r2-cleanup.{json,log}`; this is not a passing run.

Final R3 was generated after committing
`4a0ac10d8bde309b74cf3c7d0ca95b67e4d111ff`, with tracked source frozen:

- 6/6 actual capture cases pass; **220.327s total**, browser **182.2s**.
- 365-input digest `6f6068c3f44b388e2ac3ade07764ac287dbbe19e0e84dfa876efaf32a2c20ea4`.
- Canonical ZIP `/tmp/birja-phase14-ui-review.zip`, SHA256
  `9419f5f632f621ac85d89a161f75361bb36f5628bad1ce3ea8020ab1b5535944`.
- Full 114-capture/419-artifact matrix passes current source/artifact/ZIP checks.
- All **190 actual offline layouts** pass with zero HTTP(S) requests, one visible
  h1, no horizontal overflow, loaded fonts and no active forms/scripts/frames.
- Both human acceptance flags remain false; the current mobile restored-unknown
  screenshot was visually inspected without claiming owner acceptance.
- Final source unchanged and all owned containers/networks/volumes removed.

Final durable receipts are `/tmp/birja-phase14-plan17/canonical-r3.{json,log}` and
`offline-r3.json`. Phase 13 UI archive remains unchanged at `724607e8…`; earlier
recovery artifacts and the absent Plan 18 canonical recovery output are preserved.
Parent independent re-review controls review disposition. Plans 18/19 remain
pending; global state and requirement completion remain with the orchestrator.

### Repair self-check: PASSED

All three repair commits, corrected packet/manifest, historical packet and
preservation/cleanup receipts exist. Strict current verification passes after
append-only documentation changes. The original review is unchanged; unrelated
`.claude/` remains untracked and preserved. No active owned test process remains.
