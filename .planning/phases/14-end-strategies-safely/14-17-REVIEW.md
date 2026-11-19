---
phase: 14-end-strategies-safely
plan: "17"
reviewed: 2026-11-20
depth: deep
source_commit: a9580c4
diff_base: 1c370df
files_reviewed: 8
files_reviewed_list:
  - deploy/tests/portfolio-ui-evidence.py
  - deploy/tests/run-stock-browser.py
  - deploy/tests/test-portfolio-browser-contracts.py
  - deploy/tests/test-portfolio-ui-evidence.py
  - frontend/e2e/portfolio-browser-fixture.py
  - frontend/e2e/portfolio-deletion.spec.ts
  - frontend/e2e/portfolio-review-capture.ts
  - frontend/e2e/portfolio-strategies.spec.ts
findings:
  critical: 2
  warning: 0
  info: 0
  total: 2
status: issues_found
---

# Phase 14 Plan 17 — Independent Code Review

## Narrative Findings (AI reviewer)

Two **BLOCKER** findings remain in the new packet qualification boundary. The
exact eight-file `1c370df`→`a9580c4` changeset was reviewed through browser
journeys, the process-only oracle, capture generation and packet verification.
No structural pre-pass was supplied. This review does not certify the pending
whole-source qualification or owner/native-zoom acceptance.

## Critical Issues

### CR-01: Render-source inventory silently omits linked directories

**Classification:** BLOCKER.

**File:** `deploy/tests/portfolio-ui-evidence.py:71`;
`deploy/tests/portfolio-ui-evidence.py:80`;
`deploy/tests/portfolio-ui-evidence.py:115`.

**Issue:** `source_snapshot()` filters traversal results to files before its
unsafe-link check. Directory links are not files, and recursive glob traversal
does not descend through a linked child directory. The link and every render
input beneath it therefore disappear from the snapshot instead of causing
refusal. The later `is_symlink()` check examines only the already-filtered file
set and cannot detect the omitted directory.

A frontend build can resolve an imported linked render directory while the
packet's source digest does not include that directory or its target. Changing
those render bytes consequently leaves both the before/after source snapshot
and later current-source verification unchanged. Checking only returned paths
for committed inputs does not close this omission. The new tool must reject
unsupported render inputs rather than report a complete source binding while
silently excluding them.

**Independent controlled proof:** Parent authorized a bounded temporary fake
checkout with a linked directory whose target also lived inside the controlled
temporary area. No real source or secret was modified or read. The actual
snapshot implementation accepted the directory link, omitted its render file,
and returned identical snapshots after that target file changed. A normal-file
control change did alter the snapshot. The temporary fixture was removed.

**Fix:** Inspect each render root, its relevant ancestors and every traversed
entry for unsupported links before filtering to files. Reject linked render
directories and path escapes explicitly without following external targets.
Use the same safe traversal for all inventoried root/font/configuration paths;
retain only the documented intentional exclusions. Add controlled root-link,
child-directory-link and linked-target-mutation regressions that require refusal
before capture, with a normal-directory positive control. Preserve the fixed
artifact matrix and historical packet rather than broadening the allowed input
set to hide the missing binding.

### CR-02: Inert HTML verification accepts unsupported active SVG without its required policy

**Classification:** BLOCKER.

**File:** `deploy/tests/portfolio-ui-evidence.py:382`;
`deploy/tests/portfolio-ui-evidence.py:406`;
`deploy/tests/portfolio-ui-evidence.py:430`.

**Issue:** The verifier rejects selected active elements, handlers and static
URL attributes, but allows SVG animation elements that can change an anchor's
navigation target after parsing. Those animation values do not pass through its
static resource-attribute check. Separately, `validate_html()` does not require
the restrictive content policy emitted by the trusted capture helper, or reject
a missing or weakened policy. Unsupported active SVG combined with a missing
policy is therefore accepted as inert HTML.

This is a defect in the packet's independent refusal gate: consistent declared
artifact hashes cannot establish that the accepted HTML is read-only. The
current canonical packet has not been shown to contain active content; its
generated pages include a restrictive policy and ordinary static icons. The
finding concerns the verifier accepting altered packet data while claiming that
active content has been excluded.

**Independent bounded proof:** Parent authorized a controlled inline-only page
in the already-installed Chromium with dialog interception and all network
requests blocked. The actual validator accepted unsupported animated SVG with
the restrictive policy absent. Clicking its controlled test link executed the
intercepted dialog. Observed external requests were **zero**. The owned browser
was closed, controlled temporary material was removed, and the canonical review
directory/ZIP and repository sources remained untouched. No executable test
content is reproduced in this report.

**Fix:** Restrict captures to the static SVG vocabulary needed by existing icons
and reject SVG animation or other unsupported active mechanisms. For the new
Phase 14 family, require the project-owned restrictive content policy in its
effective document position, with no missing, weakened or overriding policy.
Apply checks to both the index and every capture. Add benign refusal regressions
for unsupported SVG animation and absent/weakened policies, including otherwise
consistent metadata and artifact declarations. Keep static-icon and generated
packet positive controls, preserve the Phase 13 interface explicitly, and
recapture/reverify the corrected current-source packet before owner review.

## Other Assessed Boundaries

- The eight behavioral journeys use actual authenticated create/trade/DELETE,
  retain the original request on uncertain results, and assert closed-route,
  old-cursor/original-quote and two-tab privacy. Last-portfolio reload, Back and
  sign-in remain zero until explicit new-identity creation. Named Cancel and
  Escape assert no DELETE and unchanged oracle state. Late owner/session
  callbacks and sibling activity are checked without replacement retries.
- The lifecycle oracle uses a guarded synthetic owner and repeatable-read
  PostgreSQL READ ONLY transaction. It checks read-only mode and preserves exact
  JSON text for the enumerated account/holding/fill/stock/dividend/lifecycle
  records. The three older current strategy setups use public DELETE; no direct
  closure update remains in the changed fixture. No application route exposes
  the oracle.
- All twelve older browser specs and the existing deployed-CSP skip remain
  registered alongside deletion. Legacy startup preserves the immutable role
  provisioning order and does not relax current migration admission. Disposable
  project ownership checks precede work, and cleanup remains scoped to owned
  resources.
- Phase 14 independently enumerates nineteen states at six widths, with exact
  HTML/PNG/reflow/trace/index names. Manifest checks retain synthetic/pending
  human flags, one browser version and per-width owner scope. Embedded metadata,
  trace correspondence and PNG dimensions are cross-checked. On-disk and ZIP
  inventories reject unexpected names, duplicates, links and byte differences.
- Generated captures embed actual styles/fonts, preserve real application
  state, remove ordinary scripts/forms/handlers and retain a restrictive policy.
  Automated viewport/portable-layout evidence is explicitly distinguished from
  genuine native browser-menu zoom. Prior Phase 13 packet bytes are preserved.

## Evidence and Limits

The executor's real fourteen-case browser result, strengthened finance case,
six-case canonical capture, twenty-one evidence contracts, eight browser
contracts and 190 portable-layout inspection were checked against their
assertions and recorded source/artifact binding. They do not cover the two
findings above. No duplicate database, full-stack browser or capture campaign
was run by this reviewer.

Only parent-authorized bounded controlled proofs were independently executed;
they used no provider, production data, package installation or external
requests. The canonical packet and all repository source remained unchanged.
Temporary proof material and owned browser processes were cleaned. A failed
sandbox-only browser launch was followed by the authorized isolated execution;
it is not presented as an application failure.

The full backend/browser/security and seven-stage same-archive qualification
remain Plan 18 work. Owner UI and genuine native-200% outcomes remain Plan 19
work. The six documented baseline Ruff diagnostics were not relabelled as new
defects, and no push, merge, deployment or live-provider permission follows from
this review.
