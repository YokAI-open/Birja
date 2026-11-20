---
phase: 14-end-strategies-safely
plan: "17"
reviewed: 2026-11-20
depth: deep
source_commit: a9580c4
diff_base: 1c370df
re_reviewed_source: 4a79c99
re_reviewed_code: 4a0ac10
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
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 14 Plan 17 — Independent Code Review

## Narrative Findings (AI reviewer)

The original review recorded two **BLOCKER** findings in the new packet
qualification boundary. Independent re-review at `4a79c99` resolves CR-01 and
keeps CR-02 open for the remaining early-policy placement edge described below.
There is **one remaining blocker and no warnings**. The
exact eight-file `1c370df`→`a9580c4` changeset was reviewed through browser
journeys, the process-only oracle, capture generation and packet verification.
No structural pre-pass was supplied. This review does not certify the pending
whole-source qualification or owner/native-zoom acceptance.

## Critical Issues

### CR-01: Render-source inventory silently omits linked directories

**Classification:** BLOCKER.

**Disposition at `4a79c99`: RESOLVED.** Original finding and proof retained;
current repair assessment follows below.

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

**Disposition at `4a79c99`: PARTIALLY RESOLVED; remains open for policy placement.**
The unsupported SVG and absent/weakened-policy cases are repaired. The remaining
document-structure edge is recorded in the re-review section below.

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

## Independent Repair Re-review at `4a79c99`

Reviewed repair source `4a0ac10` and the exact `70342c2`→`4a79c99` change set:
`deploy/tests/portfolio-ui-evidence.py`, its evidence contract file and the
append-only `14-17-SUMMARY.md` / `14-UI-EVIDENCE.md` records. No other original
source file changed in this repair. No new browser/security demonstration or
test was run during this re-review; this disposition is defensive source and
recorded-evidence analysis only.

### CR-01 resolved: descriptor traversal rejects links before filtering

`source_directory()` opens roots and their ancestors without following links.
`source_files()` inspects every entry before exclusions or suffix filtering,
rejects links/nonregular input, and recursively opens ordinary directories
without following links. `source_bytes()` independently checks ancestors,
opens the final file without following links and verifies its regular-file type
before reading. Font/configuration inputs use the same guarded path. This closes
the original silent omission and ancestor-link paths while retaining the
documented optional-public-root and ordinary cache-directory behavior.

Controlled linked-root/child/ancestor/font/configuration regressions now require
refusal, and ordinary-file positive/mutation controls preserve useful source
binding. The original finding is resolved without broadening allowed input.

### CR-02 remaining: pre-policy closing tags can leave effective head placement unverified

**Files:** `deploy/tests/portfolio-ui-evidence.py:503`;
`deploy/tests/portfolio-ui-evidence.py:560`.

The static icon vocabulary now excludes the previously accepted dynamic SVG
mechanisms. Exact policy directives, duplicate policies, explicit late-head
placement, early text and non-scaffolding opening tags are also refused. Those
parts of CR-02 are resolved.

However, the pre-policy rule applies only to opening tags and text.
`handle_endtag()` accepts document/body closing tags before any policy and sets
`head_closed` only for an explicit head-closing tag. HTML document parsing can
implicitly finish its head and enter its body when processing such closing
document tokens. A subsequently encountered policy can therefore be outside the
effective head even though this parser still considers it early. Presence of
the exact policy text alone does not establish that the browser applies it.

This is a remaining part of the original effective-policy requirement, not a
new application-runtime finding. The normal generated canonical pages use
ordinary structure; no active or unsafe current packet is claimed.

**Fix:** Before the first required Phase 14 policy, refuse unsupported closing
tags as well as unsupported opening tags/text, or track a complete strict
document-scaffolding state that cannot advance outside the effective head.
Generated pages need no document/body end tags before their policy. Add benign
closing-document scaffolding refusal cases and preserve positive generated
index/capture and Phase 13 compatibility controls. No executable content or
additional browser demonstration is needed to cover this parser-state gap.

### Repair evidence assessed

The 25 evidence methods / eight browser contracts cover the implemented
no-follow, static SVG and policy mutations, but do not cover the remaining
pre-policy closing-tag path. The recorded corrected six-width capture passed
6/6 cases in 220.327s with source unchanged. Its 114 captures, 419 artifacts and
190 offline layouts are bound to source `4a0ac10`, input digest
`6f6068c3f44b388e2ac3ade07764ac287dbbe19e0e84dfa876efaf32a2c20ea4`,
and ZIP SHA256
`9419f5f632f621ac85d89a161f75361bb36f5628bad1ce3ea8020ab1b5535944`.
Offline records report zero external requests and pending human/native flags.
The historical R1 packet is preserved; the interrupted R2 is explicitly
incomplete with separate owned cleanup, rather than counted as passing proof.
Those records were read; no capture, database, browser or whole suite was rerun.

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

## Fresh Defensive Repair Re-review — `70342c2` to `4a79c99`

This second, narrow independent pass preserves the original findings and earlier
disposition. Its exact source scope is `deploy/tests/portfolio-ui-evidence.py`
and `deploy/tests/test-portfolio-ui-evidence.py` in that repair diff, with the
unchanged `frontend/e2e/portfolio-review-capture.ts` cross-read for the trusted
policy and actual metadata contract. The two append-only repair evidence records
were also read. This pass does not repeat the original eight-file deep review.

**Disposition: one remaining BLOCKER (CR-02), zero WARNING findings.** CR-01
remains resolved: roots, ancestors, traversed entries, configuration and fonts
use the no-follow checks before filtering or consuming file bytes. Ordinary
source mutations remain bound; linked inputs refuse.

### CR-02: all events before the policy need a strict structural contract

**Classification:** BLOCKER; additional evidence for the existing finding.

**Files:** `deploy/tests/portfolio-ui-evidence.py:503`,
`deploy/tests/portfolio-ui-evidence.py:560`,
`deploy/tests/portfolio-ui-evidence.py:566`.

The earlier closing-tag finding is confirmed by source tracing. There is also
a text-classification mismatch: `handle_data()` uses Python's Unicode whitespace
trimming. It therefore accepts non-ASCII whitespace before the policy, including
whitespace obtained by decoding a character reference. HTML document parsing
recognizes a smaller, specific set of space characters at this boundary. Such
text can finish the effective head while this verifier still has no policy and
`head_closed` remains false. The later exact policy then passes the verifier
without proving effective placement in the browser head. These are two paths
through the same unresolved policy-placement boundary, not separate findings.

**Fix:** Require a small, explicit trusted document prefix through the first
policy. Validate every parser event against that contract, including closing
tags, decoded text and declarations; permit only HTML space characters where
whitespace is intended. Permit comments, doctypes or processing instructions
only under explicitly defined inert prefix semantics, or refuse unsupported
forms. Generated capture/index prefixes need no early closing document tags or
non-ASCII whitespace. Add benign refusal regressions for those two confirmed
paths at both index and capture boundaries, preserve generated positive cases
and the Phase 13 interface, then regenerate current-source evidence after the
repair source is committed. An end-tag-only patch would leave the text path.

The requested duplicate-attribute/case check found no additional defect in the
required policy check. Attribute names are normalized by `HTMLParser`, but a
recognized policy must have exactly two raw attributes and exactly the two
distinct expected names. Duplicate names therefore refuse even though conversion
to a dictionary would otherwise choose the last value. Policy values are
case-normalized for recognition; directive validation remains conservatively
exact. Every supplied handler/refresh/resource attribute is checked individually.
The trusted helper emits the required early policy and matching layout, trace,
source, browser, scope, artifact and pending-human metadata fields.

### Evidence and execution limits for this pass

The repair contracts contain 25 evidence methods and the records retain eight
browser contracts, six corrected actual capture cases in 220.327s, 114 HTML
captures, 190 PNGs, 114 sanitized traces and one index (419 hashed artifacts).
The R3 receipt records unchanged source and successful completion; its offline
receipt records 190 layouts and zero external requests. This pass independently
read those receipts and hashed the canonical ZIP, confirming
`9419f5f632f621ac85d89a161f75361bb36f5628bad1ce3ea8020ab1b5535944`.
The recorded capture source is `4a0ac10d8bde309b74cf3c7d0ca95b67e4d111ff`
and input digest is
`6f6068c3f44b388e2ac3ade07764ac287dbbe19e0e84dfa876efaf32a2c20ea4`.
R1 preservation and the explicitly incomplete R2/owned-cleanup records remain
intact. Existing tests do not cover the remaining structural-prefix paths.

No unit test, database, browser, capture, security demonstration or full campaign
was run by this pass. No executable example is included. Only this review report
was edited; source, global planning state and unrelated `.claude/` were preserved.
Both human acceptance flags remain false. Plans 18 and 19 are pending gates,
not defects inferred by this review.
