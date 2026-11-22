---
phase: 12-preserve-existing-investing-under-portfolio-ownership
reviewed: 2026-11-17
source_commit: d3c603e5a6584d6bba76c16a59496be0b6f4e6d2
qualified_source: 1f8d5a4eb500dad879440c2f2ebba892b8b5f65c
baseline: 12-UI-SPEC.md
status: passed
overall_score: 24
max_score: 24
findings:
  blocker: 0
  warning: 0
  total: 0
owner_ui_accepted: true
native_200_percent_verified: true
registry_flags: 0
---

# Phase 12 — UI Review

**Audit:** Independent six-pillar source and visual review, 2026-11-17.
**Baseline:** Approved `12-UI-SPEC.md`, the existing Birja master and locked
Phase12 decisions. All28 execution plans and their recorded intent were checked;
the detailed UI comparison covers Plans19–28 and the changed financial surfaces.
**Screenshots:** Existing actual synthetic captures inspected, not newly captured
or inferred from unit-test styles. No application or production server was started.

## Pillar Scores

| Pillar | Score | Specific verified finding |
|---|---|---|
| Copywriting | 4/4 | Explicit Portfolio/name, original-order recovery and non-enumerating target refusals match the approved wording; Account carries identity without pooled cash. |
| Visuals | 4/4 | Neutral portfolio context supports the existing money/confirmation focal point, with the original7/5 ticket and mobile stacked hierarchy retained. |
| Color | 4/4 | Context uses foreground/muted tokens; blue remains selected IEX/data, amber communicates uncertainty, and signed financial outcomes retain non-color cues. |
| Typography | 4/4 | New context uses the specified13/18 and15/22 sizes and medium/normal content weights; long literal names wrap without truncation or shrinking. |
| Spacing | 4/4 |8px label/value gap,16px surrounding stacks, existing16/24px cards and44px actions remain on the established scale; mobile/reflow captures retain readable controls. |
| Experience Design | 4/4 | Explicit-target boundaries suppress unavailable finance, zero/many states never choose a root, original details remain target-scoped, and focus/recovery behavior is preserved. |

**Overall:24/24.** No BLOCKER or WARNING was established within this phase's
changed UI contract. A4/4 records a checked contract outcome; it is not a claim
that every possible browser, assistive technology or future workflow was tested.

## Top Priority Fixes

None. No implementation edit is requested by this audit. Phase13's creation,
name/description editing and comparison overview, and Phase14's public deletion,
are approved future work rather than missing Phase12 controls. This review does
not introduce a selector or ask the preservation slice to ship those features.

## Provenance and Inspection Method

The accepted combined packet is
`/tmp/birja-phase12-ui-review-owner-1f8d5a4.zip`, SHA256
`c87cb4a3eb3feb52c42a37aa60ff69cce66d2ac8e2637847e6a977af1714d55f`.
Independent hashing matched:

- All102 main and12 zero/multiple artifact hashes, in both ZIP and extracted
  files, plus the top-level120-member hash inventory.
- All249 covered source hashes against the current checkout; zero differences.
- Main render commit`facfa1e` and supplemental render`1f8d5a4`, retained separately
  in the manifests and`PROVENANCE.json`. Later changes relevant to this audit
  are documentation or the unused backend clock-boundary test, not rendered UI.

The screenshot storage gate created `.planning/ui-reviews/.gitignore` before
inspection/capture work. All viewed binaries remain in ignored test output or
private `/tmp` paths; none is added to the repository. Loopback detection found
no server on3000,5173 or8080. Existing qualified captures provide the visual
evidence; this is not a code-only audit and no new capture was necessary.

Fifteen loaded captures were viewed directly:

| Surface | Actual inspected capture |
|---|---|
| Crypto original receipt and long literal name | `main/crypto-receipt-320.png` |
| Stock preview and receipt | `main/stock-preview-1280.png`, `main/stock-receipt-1280.png` |
| Combined holdings and incomplete valuation | `main/holdings-320.png`, `main/incomplete-768.png` |
| Mixed History and original/held correction | `main/history-1280.png`, `main/mixed-original-320.png`, `main/held-correction-320.png` |
| Unavailable portfolio and identity-only Account | `main/unavailable-320.png`, `main/account-320.png` |
| Zero and ambiguous multiple roots | `zero-many/zero-portfolios-320.png`, `zero-many/multiple-portfolios-1280.png` |
| Equivalent reflow | `main/automated-reflow-stock-receipt-1280.png`, actual640px layout |
| Actual retained repricing and closed draft | Current `frontend/test-results/stock-trades-actual-change-84ad7-with-the-exact-server-delta-chromium/stock-reprice.png` and `stock-trades-closed-drafts-6c251-cit-preview-after-reopening-chromium/stock-closed-draft.png` |

The last two supplemental test-output images are outside the combined ZIP.
They show the current retained stock journeys from the qualified browser output;
their independently recorded SHA256 values are respectively
`bd023183d7bd429333953d06e7fb4d58ab16b721e9004286e48e4a0c908d6ccf` and
`a8d342c4a18b537d5c7613cd998687ac662f7704017133a9f745dbcc1f03755a`.
The primary packet's source and artifact verification does not depend on these
two mutable test-output paths.

Full-page screenshots preserve fixed mobile navigation at the captured viewport's
bottom, which can place it midway through a tall stitched image. They are not
treated as evidence that the whole long page fits in one viewport. The shell's
bottom clearance, scoped focus behavior, actual browser journeys and separately
reported native zoom result provide the corresponding interaction evidence.

## Detailed Findings

### 1. Copywriting —4/4

`PortfolioContext.tsx:4` uses a semantic definition list with the visible
`Portfolio` label and actual metadata name. `PortfolioTargetBoundary.tsx:75`
distinguishes empty, ambiguous/required, unavailable and network-error copy,
with the exact safe Markets/retry actions. The unavailable unresolved-order
notice at`:108` does not claim that no trade happened or offer a different
portfolio retry. The zero/many captures contain no private cash or financial
action, and no create button outside the approved phase boundary.

`TradePage.tsx:300` and`StockTradePage.tsx:275` retain original attempt context
in preview/repricing. Recovery copy at`TradePage.tsx:301` and stock message
selection at`StockTradePage.tsx:60` names the unknown outcome and explicit
result-check action. The repricing capture visibly shows previous/new price,
previous/new cash change and difference, followed by another confirmation.
`HistoryPage.tsx:181` explains cash change as this portfolio's USD balance.
`AccountPage.tsx:11` retains Email/Sign out and removes the user-wide cash block.

### 2. Visuals —4/4

The1280px stock preview/receipt keeps the draft left and preview/result right;
the320px crypto receipt stacks these naturally. `StockTradePage.tsx:101` and
`TradePage.tsx:335` retain the existing12-column7/5 split and single-column
mobile layout. Context is below the page heading and before financial content,
then repeated in independent preview/receipt/holdings/detail regions. It is
plain labelled text, not a disabled dropdown or competing headline.

`PortfolioPage.tsx:105` preserves the complete/known-value summary and cash cards.
`PortfolioHoldings.tsx:241`/`:284` retain desktop tables and mobile lists. The
incomplete capture uses an explicit known value and unvalued count while
disabling overall return/allocation meaning; it does not substitute zeros.
Decorative shell icons remain hidden from assistive reading in`App.tsx:117`.

### 3. Color —4/4

The new context uses only`text-muted-foreground` and`text-foreground`
(`PortfolioContext.tsx:5`–`:6`). New target states reuse neutral cards and the
existing primary button. No portfolio identity receives gain/loss color or a
new highlight. The stock selected ask and warning treatment are established
state tokens, not additional portfolio accents. The existing highlight remains
one summary region (`PortfolioPage.tsx:109`).

Signed gain/loss, arrow icons and explicit unavailable text remain present
(`PortfolioHoldings.tsx:14`–`:32`, `HistoryEventDetails.tsx:48`–`:57`), so the
financial meaning does not depend on hue. The changed components introduce no
raw hex colors. This is a token/visual contract check, not a new claim of
exhaustive contrast certification for all inherited states.

### 4. Typography —4/4

The new label is13px/18px and value15px/22px, using the existing font family and
medium content weight (`PortfolioContext.tsx:5`–`:6`). New refusal headings are
32px/36px mobile and40px/44px desktop (`PortfolioTargetBoundary.tsx:96`).
`min-w-0`, word breaking and`overflow-wrap:anywhere` keep the literal
`<Strategy>& UnbrokenPortfolioNameUnbrokenPortfolioName` visible in narrow
captures without HTML interpretation, ellipsis or font shrinking.

Inherited card headings, stock24px subheadings and the pre-existing crypto
receipt emphasis retain their earlier component rules. The approved contract
explicitly preserves unchanged components; they are not newly introduced
context/error typography and were not restyled merely to make a size counter
appear smaller. Financial figures remain tabular and existing formatters remain
in place (`PortfolioHoldings.tsx:274`, `StockTradeReceipt.tsx:22`).

### 5. Spacing —4/4

The context's`gap-2` gives8px label/value separation and the surrounding
financial page`gap-4` gives16px between regions. Existing Card uses24px desktop
and16px mobile padding (`components/ui/card.tsx:9`), and default Button is44px
high (`components/ui/button.tsx:19`). New boundary and History controls reuse
these components; wrapped names and refusal text increase height naturally.

`App.tsx:177`/`:181` retain16/32px gutters,1440px maximum width and mobile safe-area
clearance. Actual320px names, actions and financial rows remain within the page;
the640px equivalent-reflow receipt stacks without horizontal page overflow.
`App.tsx:181` and History's`scroll-mb-24` provide focused-content clearance above
the fixed mobile navigation. No new fixed-height identity chip or floating
overlay was added.

### 6. Experience Design —4/4

`PortfolioTargetBoundary.tsx:54` does not mount financial children until explicit
active metadata resolves. Loading has status/busy semantics at`:61`; refusal
states replace finance and focus the initial state heading at`:46`. The0/many
states deliberately permit market browsing without picking the first root.
`usePortfolioTarget.ts:145` captures owner/root/session and revokes old authority;
`useMe.ts:14` removes private queries across owner changes. Original History
state and focus are keyed to the target and session (`HistoryPage.tsx:35`–`:59`,
`HistoryEventDetails.tsx:121`–`:130`), with explicit original-return focus at`:265`.

The two trade pages and receipt retain current-target checks and freeze original
attempt context, while actual API/hook/browser negatives support the no-stale-
finance result. `StockTradePage.tsx:336` keeps unknown/submitting recovery separate
from a new order; `StockTradeReceipt.tsx:103` links to the same root. Receipt
focus is guarded against invalid targets and repeated polling focus. Existing
route heading focus and global2px/2px-offset focus styling are preserved
(`App.tsx:87`, `index.css:127`). No extra per-name live region is introduced.

The complete browser suite records59 passes and the one original deployed-CSP
skip; these support actual interactions, not a new deployment claim. The owner
separately accepted UI with`approved` and genuine desktop native200% with
`Yes—native 200% passed`, recorded in`12-HUMAN-UAT.md`/`12-28-SUMMARY.md`.
The capture-time manifests remain`native_200_percent_verified:false`; the later
human result is not written back into immutable screenshots. Browser name was
not supplied and is not invented. Automated640px reflow is supporting evidence,
not native-zoom verification by this auditor.

## Registry Safety

`frontend/components.json` has an empty`registries` object; the Phase12 contract
lists only existing checked-in official shadcn source and no third-party blocks.
Registry audit:0 third-party blocks,0 flags. No registry fetch, CLI installation,
font download or component package change was required or performed.

## Files Audited

Runtime source/structural inspection:

- `frontend/src/App.tsx`
- `frontend/src/components/PortfolioContext.tsx`
- `frontend/src/components/PortfolioTargetBoundary.tsx`
- `frontend/src/components/PortfolioHoldings.tsx`
- `frontend/src/components/HistoryEventDetails.tsx`
- `frontend/src/components/StockTradeReceipt.tsx`
- `frontend/src/pages/AccountPage.tsx`
- `frontend/src/pages/TradePage.tsx`
- `frontend/src/pages/StockTradePage.tsx`
- `frontend/src/pages/PortfolioPage.tsx`
- `frontend/src/pages/HistoryPage.tsx`
- `frontend/src/pages/MarketsPage.tsx`
- `frontend/src/components/StockSection.tsx`
- `frontend/src/hooks/usePortfolioTarget.ts`
- `frontend/src/hooks/useMe.ts`
- `frontend/src/hooks/usePortfolio.ts`
- `frontend/src/hooks/useEventHistory.ts`
- `frontend/src/index.css`
- `frontend/src/components/ui/button.tsx`
- `frontend/src/components/ui/card.tsx`
- `frontend/components.json`

Supporting evidence: all Phase12 plan objectives and summary intent, detailed
UI Plans19–28, UI-SPEC/context/master, the main/supplement/top-level manifests,
`frontend/e2e/portfolio-ownership.spec.ts`, current local qualification and
owner UAT. The targeted local UX search for`focus not obscured` confirmed the
contract's intentionally enhanced full-visibility rule; it is not mislabelled
as a new AA minimum. The compact-label search is not applied as a nowrap rule:
Portfolio identity is a text group whose approved contract explicitly requires
full wrapping, not a badge. No new visual design system was generated.

## Scope and Outcome

No runtime, test, lock, financial state, provider or production file was changed.
Only this audit report and the screenshot `.gitignore` gate were created. No
new binary was captured or staged and no commit was made by the auditor.
Phase completion and requirement verification remain the orchestrator's next
gates. Phase7's deferred live outcomes and OFF admissions are unaffected.
