---
phase: 13-create-and-compare-independent-strategies
plan: "16"
reviewed: 2026-11-18T14:40:36Z
initial_reviewed: 2026-11-18T14:19:21Z
depth: standard
diff_base: ecad19a
diff_head: 4049e42
initial_diff_head: 7e4c1f2
repair_diff_base: 7e4c1f2
files_reviewed: 12
files_reviewed_list:
  - deploy/tests/portfolio-ui-evidence.py
  - deploy/tests/test-portfolio-ui-evidence.py
  - frontend/e2e/portfolio-browser-fixture.py
  - frontend/e2e/portfolio-history.spec.ts
  - frontend/e2e/portfolio-strategies.spec.ts
  - frontend/e2e/stock-trades.spec.ts
  - frontend/src/components/PortfolioCreateForm.test.tsx
  - frontend/src/components/PortfolioCreateForm.tsx
  - frontend/src/components/PortfolioSwitcher.test.tsx
  - frontend/src/components/PortfolioSwitcher.tsx
  - frontend/src/pages/PortfoliosPage.test.tsx
  - frontend/src/pages/PortfoliosPage.tsx
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings:
  critical: 1
  total: 1
status: clean
---

# Phase 13 Plan 16: Code Review Report

**Reviewed:** 2026-11-18T14:40:36Z  
**Depth:** standard, with focused provenance and call tracing  
**Files Reviewed:** 12 source/test files across initial and repair reviews; summary and UI evidence document inspected as context  
**Status:** clean — initial blocker resolved

## Summary

Initial review of `ecad19a..7e4c1f2` established one blocker in the evidence verifier's completeness contract. Independent focused re-review of `7e4c1f2..4049e42` finds it resolved, with no remaining BLOCKER or WARNING. The original finding remains below as resolved history. This source/provenance result is separate from the visual auditor's review and pending full qualification.

## Narrative Findings (AI reviewer)

## Repair Disposition

**CR-01 — Resolved by `8cdd175`.** The verifier derives the 265 required filenames from source-owned widths/states, requires exact manifest-key and on-disk inventory equality, and rejects symlinked directories/members/manifests. Every capture must declare its canonical paths. Embedded HTML state, width, source, browser/version, scope and artifact paths must correspond to that capture; the stored timing trace must equal its embedded counterpart. Both packaging and final verification use these checks.

RED `fb33b6a` independently enumerates the complete matrix and tests coherent omission of HTML, main PNG, narrow PNG, timing trace and index, removing their declarations and rewriting surviving metadata/checksums. The omitted artifact can no longer disappear from the source-owned required set. Tests also retain a materialized complete positive control, index-only/extra/missing/symlink/traversal negatives and path/HTML/trace correspondence negatives. The source and reported RED/GREEN receipts were inspected without rerunning tests.

The accompanying product changes are bounded copy, icon sizing, duplicate unknown-instruction suppression and switcher-width changes. They retain original-key/payload recovery, native selection and explicit Open semantics; no additional concrete code defect was established. Visual disposition remains the separate auditor's responsibility.

Read-only inspection confirms current ZIP SHA256 `eac081810b48e9ddad875f3abc2a07510b3795c4b8d8aca7bec3ef29b8464c68`, committed capture source `8cdd17582ba69cb0815bb0ecd48e4819a2c2f762`, 72 captures, 265 matching artifact hashes, 339 matching current input hashes and digest `9eee8a15364a997f189881aca49140c9e1ea7e56ae32dc78f15cf30cfaf86cbb`. The directory has exactly those artifacts plus manifest, with no symlinks or extra files. The original ZIP is preserved at `/tmp/birja-phase13-ui-review-before-review-fix.zip` with its original SHA256 `1fb8795e5acc82bf74186a12050363960a8469d2838db571fe4b9d44a874e8c6`. Both acceptance flags remain false.

## Initial Critical Issue — Resolved History

### CR-01: BLOCKER — Coherent omission of capture artifacts passes final evidence verification

**Disposition:** Resolved by `8cdd175`; original initial-source evidence and severity retained below.

**File:** `/home/YokaiExchange/deploy/tests/portfolio-ui-evidence.py:94-100`  
**Caller:** `/home/YokaiExchange/deploy/tests/portfolio-ui-evidence.py:168-172`  
**Related contract:** `/home/YokaiExchange/deploy/tests/test-portfolio-ui-evidence.py:65-82`

**Issue:** `validate_manifest` requires 72 capture metadata entries, but neither it nor `verify_artifacts` derives the files those captures require. `verify_artifacts` accepts any nonempty artifact map and checks only its supplied entries. The final `--verify` path then prints `CURRENT SOURCE AND ARTIFACTS VERIFIED`.

A concrete coherent omission is to retain the complete valid capture metadata/source map, delete `phase13-unknown-1280.html`, and remove only its entry from `manifest.artifacts`. Every remaining hash still matches; all source, browser, scope and capture-matrix checks still pass; the absent unknown-state page is never examined. The same applies to its screenshot, narrow screenshot or timing trace. Even an artifact map containing only the valid `index.html` entry satisfies this implementation. The existing missing-file test retains the missing file's hash entry, so it covers stale declarations but misses this omission.

This defeats the explicit requirement that missing evidence must refuse: capture metadata alone can qualify missing implemented-state evidence. The separate published ZIP digest detects a changed ZIP when a reviewer checks it, but the directory verification command does not require that digest or even open the ZIP, so it does not repair this false-success path.

**Fix:** Derive the exact required artifact names from `WIDTHS` and `STATES`: HTML, PNG and trace for each pair; reflow PNG for each width at least 768; and `index.html`. Require exact equality with the manifest artifact keys before hashing, and reject unexpected directory members apart from `manifest.json`. Add coherent-omission negatives that remove both a required file and its hash entry while preserving all capture/source metadata, covering HTML, ordinary/narrow screenshots and traces. A complete actual packet must remain accepted. Changes to the hashed evidence tool/contracts require recapture or explicit matching-source evidence under the existing provenance rule; preserve the current packet rather than overwriting it.

## Reviewed Boundaries and Limits

The production repair filters only definitive old `name_taken` feedback when the editor has neither submitted nor observed an original key; recovered-original/new refusal, cap/rate and unknown intent state remain outside that filter. Browser response-loss handlers fetch the actual committed result before aborting, and the creation recovery case compares the same key and body after reload, rename and cap. Retained navigation changes preserve the original target IDs and financial assertions. Fixture money/journal comparison retains PostgreSQL JSONB text rather than decoding monetary numbers to Python floats; empty capture setup precedes stock ownership.

Initial read-only packet inspection confirmed original ZIP SHA256 `1fb8795e5acc82bf74186a12050363960a8469d2838db571fe4b9d44a874e8c6`, 72 captures, 265 matching artifact hashes, no extra directory files, and 339 matching source hashes with initial input digest `304e012896cf3dc5e385bfa6dbb411d6e8007323c136204c660a1dc51eafde71`. Updated packet verification is recorded in Repair Disposition. This is byte/inventory inspection, not browser execution or a six-pillar visual audit.

No tests, browser/runtime harnesses, database operations, providers, dependency changes, source edits or commits were performed in either review; only this report was written. SourceA's reported 79 passes/one retained CSP skip, sourceB's reported 20 passes/128 affected tests and repair sourceC's reported 20 passes/140 affected tests remain distinct. The reported 12 offline contracts and 120-layout checks were inspected as execution receipts, not rerun. The mandatory current unfiltered browser run inside Plan 17's actual all-security campaign, restricted-role/TLS/recovery qualification and Plan 18 owner/native200 outcomes remain pending. The dev-administrator browser connection does not establish restricted database authority.

---

_Reviewer: gsd-code-reviewer_  
_Depth: standard_
