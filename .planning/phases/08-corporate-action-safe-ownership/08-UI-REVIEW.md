---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T16:55:11Z
review_head: 0cea8b5
status: pass
screenshots_inspected: true
score: 24
score_maximum: 24
findings:
  blocker: 0
  warning: 0
---

# Phase8 UI review

**PASS:24/24, zero active BLOCKER/WARNING findings.** Independent source and
actual screenshot review is complete for this UI scope. Both observed defects
were corrected and re-reviewed. This is not owner acceptance or a completed
whole-phase/CI/production/provider gate. The reviewer inspected existing images
and browser receipts but ran no browser tests, runtime/DB/provider operations or
source edits. The owner Phase8 UI acceptance remains separate.

## Final six-pillar assessment

| Pillar | Score | Specific contract evidence |
| --- | --- | --- |
| Copywriting |4/4| Fixed state/reason helper implements approved suspension, uncertainty, split-wait, current/recovery copy. Source/status/trading labels stay independent; explicit Unavailable and valuation text replace unsafe amounts. No raw provider/private evidence interpolation. |
| Visuals |4/4| Actual320/375/768/1280 captures retain stock identity and clear bid/ask, source/session and status hierarchy; desktop keeps six columns, mobile a single exposed record layout. Long reason/name/time text wraps; corrected CSS200% image has no adjacent-cell overlap. |
| Color |4/4| Source uses established semantic neutral/amber tokens, restrained row-hover accent and readable text rather than color alone. Inspected captures match MASTER light-only surfaces; no new raw component colors, gradients or green action-safe trading claim. |
| Typography |4/4|15/22 body/value and13/18 labels/details,400/500 weights, tabular amounts/times. Dated semantic times include explicit local zone and America/New_York session zone. Zoom reflows complete words/reasons; narrow value labels wrap rather than clip. |
| Spacing |4/4| Existing card/control tokens,4/12/16px component rhythm, expanding desktop rows and44px retry target retained. Actual ordinary/mobile/zoom evidence and executor cell-bound assertions show no document scroll or clipped warning panel. |
| Experience design |4/4| One atomic contextual polite aggregate excludes ticking ages; safe expiry removes prices; persistent hold survives healthy refresh; loading/error/permission/waiting/current states remain truthful. Browser receipts cover retry failure focus/success heading, crypto keyboard navigation, reduced-motion and no duplicate accessible layout. |

### Final fixes and limitations

CR-01 retained-error recovery and CR-02 CSS zoom overlap are resolved. **No
remaining priority fix or minor recommendation is required by this audit.**
The final three class changes are limited to block/min-width/word-wrap values,
auto-height wrapping quote badges and intrinsic timestamp bounds; they introduce
no new interaction or authority behavior. Actual corrected zoom inspection shows
separate bid/ask labels wrapping inside their cells instead of overlapping.

Current frozen source identities:

- StockSection.tsx: `aee6a806a4588c1af653fe84f2e40cecae286a2fa59101369f3c4cb98ef2516d`
- StockActionState.tsx: `3c0d4ef7af80cbe291f95a82d02929b17114fac3f128dc4b6cbd7dc7ea6bb726`
- lib/stockActionCopy.ts: `f4c78027395273fed3976c9e40a46f4ab1fc141a1b7ad690a3e28a19b62e1f5a`

### Actual evidence inspected

Final corrected captures:
`/tmp/birja-phase08-ui-mqq4ss1g/screenshots/actions-css-zoom-200pct-first-stock.png`,
`actions-375-first-stock.png`, `actions-1280-first-stock.png`.
The corrected CSS zoom image was independently viewed at readable detail: all
fallback values remain inside their own cells; reasons/times/status remain
readable. Earlier320/375/768/1280 and full-page synthetic captures listed below
were also independently inspected for ordinary layout and crypto coexistence.

Read the actual final scoped receipt
`/tmp/birja-phase08-ui-mqq4ss1g/browser-final.log`:5 stories passed21.5s, covering
all four ordinary widths and the corrected zoom/reflow story. Read the prior
full receipt `/tmp/birja-phase08-ui-obqbh0ko/browser-final.log`:21 stories passed,
including safety/error/focus journeys. The later class-only correction received
the affected5-story rerun; full final frontend/CI/browser gate is still Plan12,
not falsely represented as already rerun here.

640CSSpx at2× density is **reflow-equivalent emulation**, not native browser zoom.
The additional1280px `documentElement.style.zoom=2` capture and cell/document
bounds assertions are **actual CSS zoom stress proof**, not browser-chrome zoom.
Both are labelled accurately. Reduced motion and keyboard/focus assertions are
executor browser evidence, not subjective pixels or a claim of screen-reader
device testing. No owner acceptance is inferred from synthetic fixtures.

Screenshots were supplied as existing files under `/tmp`, outside the repository;
the reviewer captured none and introduced no binary artifact. Registry audit:
`frontend/components.json` has empty third-party registries; only existing
checked-in Card/Button/Badge are used. No registry/network/package operation was
performed. No unaudited third-party block was introduced.

## Historical interim review notes

The following records preserve earlier findings, hashes and explicitly pending
states at their review time; the final assessment above supersedes their pending
status. They are not claims that a now-corrected defect remains active.

Read UI auditor/skill instructions, approved08-UI-SPEC/UICHECK/Plan11 and Birja
MASTER. Native-only extra guidance does not override the project's web/light-only
design contract. Reviewed frozen StockSection, StockActionState and shared fixed
copy helper at `a09324b`; shared FastRefresh-compatible copy helper is appropriate.

## Source findings

### CR-02 — BLOCKER, RESOLVED: CSS200% zoom causes adjacent unavailable values to overlap

**File:** `/home/YokaiExchange/frontend/src/components/StockSection.tsx:97`

**Actual image:**
`/tmp/birja-phase08-ui-zmgtviq5/screenshots/actions-css-zoom-200pct-first-stock.png`.

Independently inspected the supplied actual CSS200% zoom capture. Bid/Ask
Unavailable labels overflow their narrow fixed desktop table cells and collide
with each other/source-time text. The surrounding reasons and dated times wrap,
but the numeric fallback is unreadable. This was found by the executor's added
zoom proof and confirmed visually here. Make Side's value block-level/min-width
safe with wrapping within the cell; preserve explicit Unavailable rather than
clipping it. Reprove table-cell bounds and capture the corrected row. Actual CSS
zoom with desktop media queries is an additional stress condition, distinct from
native browser zoom and640CSSpx@2× reflow emulation; do not conflate the evidence.
Worker correction is in progress; final score remains pending.

### Sticky request-failure integration at `aaab66a`

Source review is clear for the actual request-error→local cache purge path.
The component retains a generic failed-request flag when Query's transient error
is cleared by local safety data replacement; request-state transitions prevent
render loops and new pending lifecycle resets it. Failed explicit retry restores
button focus on the next animation frame; successful explicit retry focuses the
heading. Background updates do not call that focus path. The state contains no
account/provider facts; authenticated data isolation remains in the reviewed hook.

Fetch completion alone does not distinguish cancellation from success. The actual
production cancelQueries caller is private auth teardown, immediately followed
by removal/identity change; no retained-auth user-visible cancellation failure
was demonstrated. This is recorded as a limit of the inspected flags, not an
invented blocking UI flow or a claim that cancellation was browser-tested.
Root/executor browser proof remains separate.

Current StockSection.tsx SHA-256:
`6b07a454a034eae5728913b04d3b0ec7a30ed0c36e62cd8501c75423cac699be`.

### Actual screenshot inspection

Read actual synthetic captures under
`/tmp/birja-phase08-ui-obqbh0ko/screenshots/`:

- actions-320-first-stock.png
- actions-375-first-stock.png
- actions-768-first-stock.png
- actions-1280-first-stock.png
- actions-375.png and actions-1280.png (full-page context)

At320/375px the deliberately long unbroken company name, disputed-action reason
and dated zone text wrap without clipped warning panels. At768px the mobile
record remains readable; at1280px the six desktop columns retain separate bid,
ask, source-time, session and grouped status semantics. The suspended first stock
shows explicit Unavailable values, no source quote timestamp, a readable amber
reason and independently checked time/status/trading text. Other stock values and
the crypto section/Trade controls remain present in the full-page captures.
Neutral card/canvas, amber state text, restrained row-hover accent, typography
and expanding row spacing match the approved contract. No new visual defect was
found in these captures. Full-page images were inspected for structure; row
captures provide the readable text evidence.

Actual browser-level DOM overflow/accessibility/focus/reduced-motion assertions
remain executor evidence to be supplied, not inferred from pixels. A640CSSpx
reflow at2×density is not described as native200%zoom; the requested actual CSS
zoom capture/proof remains pending before final scoring.

Read the actual ordinary browser receipt
`/tmp/birja-phase08-ui-obqbh0ko/browser-final.log`:21 passed, with retries disabled
per executor. Committed stories assert failed-retry focus and successful heading
focus, one exposed layout, no document overflow and reduced-motion reflow.
`frontend/components.json` has no third-party registries. These source/log
observations are separate from the added CSS zoom defect and do not imply that
the not-yet-corrected zoom run passed.

### Targeted CR-01 re-review

CR-01 is resolved in the frozen one-line working-tree correction aftera09324b:
retained-data request error now shows retry independently of disclosure permission.
The initial-no-data branch remains exclusive, so there is still one recovery
button. Disabled/pending labels and existing explicit retry focus behavior are
unchanged. No additional source finding arose. Actual browser matrix/screenshots
and six-pillar scoring remain pending; no visual pass is inferred from this fix.

Current StockSection.tsx SHA-256:
`96023482696a5bc53692749f042de7945451a4302084cb0444ed676ffa4b276f`.
Other source identities below are unchanged. The root reports a meaningful
browser RED and scoped RTL/static GREEN; these are executor evidence, not tests
performed by this reviewer.

### CR-01 — BLOCKER, RESOLVED: Retained-error retry disappears after permission expiry

**File:** `/home/YokaiExchange/frontend/src/components/StockSection.tsx:170`

**Issue:** Background request failure with retained data exposes retry only when
`allowed` is true. The existing safety deadline projection can subsequently make
admission unavailable while data/isError remain; the button disappears. The
user's failed-request recovery path is then unavailable precisely when safe
redaction occurs. Permission-only unavailability need not create a retry, but
an existing request failure must retain it.

**Fix:** Gate the retained-data retry on request error, independent of permitted
numeric disclosure. Keep one button, pending duplicate-click protection and
failure/success focus behavior. Reproduce request error→permission expiry in an
actual browser and assert the recovery control remains available. The executor
already identified this same issue and is preparing its behavioral RED.

## Source contract observations

Fixed enums map to safe approved copy, with no raw provider/evidence interpolation.
Status/action/trading are independently labelled; stock orders/reconciliation
controls are absent. Unsafe quote sides/times use explicit unavailability.
Checked and source times use semantic time elements with dates and explicit
zones; session boundaries use America/New_York. One contextual atomic status
aggregate includes affected symbols/reasons and excludes ticking ages/check-time
changes. Initial skeletons are aria-hidden and do not pulse. Successful explicit
retry focuses the heading; failed retry keeps its button; background updates do
not move focus.

Source layout retains six desktop columns and a single exposed mobile list via
CSS breakpoint hiding; long action reasons are normal wrapping paragraphs without
the fixed-height Badge. Existing semantic tokens and15/22,13/18 typography are
used. These are source observations only: width/overflow/zoom/contrast/focus and
actual20-stock/15-crypto coexistence still need browser and visual evidence.

## Frozen source identities

- StockSection.tsx: `f298cd82c3c394d1538e9d7f5fde044d209f4718fbc11afad6aa11cf7d5eb411`
- StockActionState.tsx: `3c0d4ef7af80cbe291f95a82d02929b17114fac3f128dc4b6cbd7dc7ea6bb726`
- lib/stockActionCopy.ts: `f4c78027395273fed3976c9e40a46f4ab1fc141a1b7ad690a3e28a19b62e1f5a`

## Remaining visual pass

Inspect actual320/375/768/1280,200%zoom/reduced-motion captures with long names,
timestamps and reasons; score copywriting, visuals, color, typography, spacing
and experience with concrete evidence. Confirm one exposed layout, no clipping
or document overflow, dated time honesty, independent crypto controls, retry
focus and no unsafe numbers after deadlines. Third-party registry installation
is not planned; verify checked-in component registry configuration at final pass.
