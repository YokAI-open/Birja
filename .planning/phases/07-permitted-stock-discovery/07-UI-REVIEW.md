# Phase 7 — UI Review

**Audited:** 2026-11-10
**Baseline:** approved `07-UI-SPEC.md`, existing Birja MASTER and source tokens
**Source:** `7fb4bed`; independent read-only review during Plan13
**Screenshots:** reused authenticated synthetic Plan12 captures; no new captures
**Disposition:** two nonblocking WARNINGs; no UI BLOCKER found. Owner acceptance and live provider permission remain unverified.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| Copywriting | 4/4 | Visible IEX/simulation attribution; session, recency and execution capability remain distinct. |
| Visuals | 3/4 | Loading placeholders reserve substantially less space than the twenty actual records. |
| Color | 4/4 | Existing semantic surfaces and labelled freshness states; no new raw colors or action accent overuse. |
| Typography | 4/4 | Exactly the approved 13/15/32/40px surface sizes and 400/500 weights. |
| Spacing | 4/4 | Approved scale, responsive record layout and existing Card/Badge/Button dimensions retained. |
| Experience Design | 3/4 | Successful retry removes the focused recovery control without retaining a focus destination. |

**Overall: 22/24.** Scores reflect the submitted source, before any subsequent fixes.

## Top 3 Priority Fixes

1. **UI-W01 — preserve keyboard focus after successful retry.** The focused retry button disappears as soon as recovery succeeds. Retain a stable recovery control while focused, or deliberately move focus to a stable section heading/status destination after a user-triggered recovery. Add an assertion after the successful response, rather than only before pressing Enter.
2. **UI-W02 — reserve the actual catalogue layout during loading.** Replace the five short blocks with twenty responsive record/table skeletons that approximate the real identity, quote and session stacks. Test the pending-to-populated transition with long company names and session times.
3. No third concrete defect was established. Do not invent a third issue to fill the template. Owner visual acceptance and a genuinely passing final full-browser run remain separate gates, not additional product defects.

## Evidence and Limits

- Inspected existing `/tmp/birja-phase07-e2e-vnwyv5ep/screenshots/stocks-1280.png` and `stocks-320.png` using the image viewer. These are Plan12 authenticated Chromium captures with fixture stock HTTP responses, fake crypto and isolated authentication; not real IEX data. The full-page mobile image is downscaled by the viewer, so fine pixel claims rely on source and the recorded browser assertions rather than its thumbnail. The directory also contains375/768 captures, but those two images were not independently visually inspected here.
- Ports3000,5173 and8080 returned no HTTP response during this audit. No available Playwright MCP tools were found. No server was started, no new capture taken and no tests rerun by this reviewer.
- Screenshot-ignore gate was checked: `.planning/ui-reviews/.gitignore` was absent. Parent restricted this review to its one report file and explicitly directed reuse of `/tmp` captures only. Accordingly no screenshot directory, binary or repository ignore file was created. The missing gate must be established before any future repository screenshot capture.
- Plan12 summary records11 passing markets/stock browser journeys. Current `frontend/e2e/stocks.spec.ts:133–171` asserts320/375/768/1280 widths, twenty records, fifteen crypto links, one accessible representation, source datetime, no document overflow and640px effective-width reflow. This is200% zoom-equivalent layout coverage, not a fresh actual browser-zoom test by this auditor.
- At inspection, `/tmp/birja-phase07-plan13-browser-reviewed.log` ended with `all-browser failed`; do not infer that a fresh full-suite rerun passed. The parent owns diagnosis and final test disposition. This audit does not waive that gate or promote unrelated historical advisory debt.
- Local UI/UX search `live updates screen reader --domain ux` returned contextual atomic-live-status and semantic-screen-reader guidance. Applied to the actual one-region implementation, without replacing approved fonts or tokens.

## Detailed Findings

### Pillar 1: Copywriting (4/4)

**PASS — attribution and staged capability are visible.** `frontend/src/components/StockAttribution.tsx:14–24` renders “IEX prices”, the complete single-exchange/virtual-money/simulated-execution explanation and supplemental provider text as escaped React text. No tooltip is needed. `StockSection.tsx:125–129` always shows attribution, trading-coming-later copy and the source-sampling explanation. `Session` at39–63 and `QuoteTime` at65–85 distinguish market open/closed/unknown, previous session, last quote and out-of-date values. No stock Buy/Sell/Trade CTA is rendered. Missing quotes use words rather than fabricated zero prices (`Side`,88–93).

Initial and retained-data failure copy is specific to stocks (`StockSection.tsx:10–13,109–117`) and does not expose raw provider errors. Crypto's oldest-age text is explicitly scoped at `MarketsPage.tsx:120–129`. No copy change is recommended.

### Pillar 2: Visuals (3/4)

**WARNING UI-W02 — skeleton geometry does not match the delivered catalogue.** `StockSection.tsx:154–158` produces five104px mobile or52px desktop blocks. Loaded records number twenty (`199–225,228–260`), with identity, prices, source datetime and multi-line session/status content. The inspected desktop capture confirms session wrapping expands rows well beyond52px; mobile records have several detail stacks. This source-proven mismatch makes the card expand sharply on first successful load and misses the contract's reserved-shape requirement. It does not prevent task completion. No numerical CLS score was measured.

Fix within the existing design: render twenty presentation-only skeleton records with the same responsive table/list structure and reasonable bounds for wrapped text. Preserve the one loading status and reduced-motion behavior. The Markets heading, Crypto-first hierarchy and separate stock card are otherwise evident in source and desktop capture.

### Pillar 3: Color (4/4)

**PASS — neutral surfaces dominate and state color is redundant with text.** `frontend/src/index.css:11–47` supplies the approved canvas/card/muted/gain/warning tokens. New stock presentation contains zero raw hex/rgb colors and zero `text-primary`, `bg-primary` or `border-primary` occurrences. Its one direct accent use is table row hover (`StockSection.tsx:202`); Markets retains one existing crypto row-hover accent (`MarketsPage.tsx:83`). Freshness uses two Badge variants, success/warning, with explicit “Recent”/“Out of date” labels (`StockSection.tsx:79–81`); closed state remains neutral. Recovery uses secondary buttons rather than adding primary actions.

The desktop capture supports neutral canvas/card dominance with small state badges, compatible with the intended60/30/10 hierarchy. Exact pixel-area percentages were not measured. No color change is recommended.

### Pillar 4: Typography (4/4)

**PASS — approved four-size/two-weight subset.** Direct surface size classes are13px/15px in stock presentation and32px/40px in the Markets title (`StockSection.tsx:31–34,90,183,239–254`; `StockAttribution.tsx:17`; `MarketsPage.tsx:116`). Direct explicit weight is only `font-medium` (500); ordinary text inherits400. No stock `font-semibold`/`font-bold` or additional font family is introduced. The existing self-hosted Inter mapping is in `index.css:4,68,117–124`; source times and money use tabular figures (`StockSection.tsx:18,90`). Title tracking/line heights match the contract.

Existing CardTitle has a different style but is not consumed by this discovery surface. Do not count unused component definitions as typography violations. No change recommended.

### Pillar 5: Spacing (4/4)

**PASS — explicit project scale and responsive layout retained.** Stock stacks use4/12/16px gaps; table padding uses12/16px (`StockSection.tsx:56,73,121,191,204–219,232,237`). Page separation uses24px (`MarketsPage.tsx:114`). Card supplies24px desktop/16px mobile padding and24px radius (`components/ui/card.tsx:9`). Existing Badge internal padding is reused rather than introducing another component scale. Retry controls explicitly use44px minimum height (`StockSection.tsx:148,164`).

Desktop table is hidden below1024px and mobile list hidden at or above1024px (`180,228`); source uses wrapping and a fluid card. The recorded browser assertions cover no document overflow at all required widths and the zoom-equivalent width. The skeleton mismatch is scored in Visuals once, not counted again as a spacing deduction. No spacing fix recommended.

### Pillar 6: Experience Design (3/4)

**WARNING UI-W01 — keyboard recovery loses its focus target on success.** The retained-data retry button exists only under `data && allowed && isError` (`StockSection.tsx:144–153`); initial-error retry exists only without data (`160–168`). A successful refetch removes either focused button. No focus retention/transfer is implemented. The current browser journey focuses the button and presses Enter, but its post-success assertions check only status and crypto visibility (`frontend/e2e/stocks.spec.ts:123–130`). Keyboard users lose their current position during this explicit action. This is a recoverable accessibility degradation, not a task-blocking failure.

Preserve an intentional focus destination after a user-triggered retry; do not move focus on routine polling. Extend browser coverage to assert that destination after the successful response, with keyboard order still coherent. Avoid merely keeping a disabled focused control that can no longer be reached.

**PASS — data authority, independent sections and semantic presentation.** `useStocks.ts:8–69` computes conservative source age, session boundaries and display lifetimes from server time plus full transport duration and monotonic elapsed. `74–87,136–142,158–168` redact expired/private stock values and handle final401. `97–135` binds requests to identity/query ownership and rejects superseded/cancelled responses; crypto query keys are separate. `api/stocks.ts:82–105,151–176` checks exact string money, complete twenty unique identities and known states before publication. `StockSection.tsx:131–143` provides one atomic contextual status; ages remain ordinary text. No second-by-second competing live region, stock link, destructive action or money-changing control was found.

The relevant tests explicitly cover malformed data, delayed transport,120-second boundary, retained background failures, logout/unmount, permission/calendar/retention expiry and denied generation. Their presence supports implementation review; this auditor did not rerun them or claim live provider acceptance.

## Registry Safety

Registry audit:0 third-party blocks checked, no flags. `frontend/components.json` has empty registries; approved UI-SPEC uses only existing checked-in Button/Card/Badge. Source inspection found no new registry addition, remote component download or provider credential in presentation. No networked registry CLI was needed.

## Files Audited

- `AGENTS.md`, `CLAUDE.md`, `.codex/GSD-ADAPTER.md`; relevant UI-review workflow/agent, UI brand and UI/UX skill.
- `.planning/PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md` for scope/state; `design-system/birja/MASTER.md` and Phase7 `07-UI-SPEC.md` as design baseline.
- Phase7 Plans11/12 and summaries11/12.
- `frontend/src/components/StockSection.tsx`, `StockAttribution.tsx`, `StockSection.test.tsx`; Card/Badge component source.
- `frontend/src/pages/MarketsPage.tsx`, `frontend/src/hooks/useStocks.ts`, `useStocks.test.tsx`, `frontend/src/api/stocks.ts`, `stocks.test.ts`, `client.ts`.
- `frontend/e2e/stocks.spec.ts`, `frontend/src/index.css`, `frontend/components.json`.
- Two existing Plan12 screenshots and the final-browser log tail described above.

**Recommendation count:**2 priority fixes,0 additional minor defects. No implementation change, test execution, provider access, production operation or commit was performed by this audit. Final owner visual acceptance remains `needs_human_review: true`.

## Focused Independent Re-review — 670b221

**Reviewed:** 2026-11-10, after behavioral RED commit `bd2a83f` and corrective commit `670b221`. Original findings and22/24 assessment above are retained as historical evidence. This pass inspected only the bounded source/test corrections and browser-helper readiness change; no new capture, test run, implementation edit or commit was performed by this reviewer.

| Finding | Current disposition | Evidence |
|---------|---------------------|----------|
| UI-W01 | Resolved in source; final real-browser confirmation remains pending | `StockSection.tsx:98–103` awaits the user-triggered refetch and focuses the stable heading on success; `128` makes the heading programmatically focusable without adding it to Tab order. Both retry controls use this handler (`155,171`). An error result does not focus the heading. Routine background polling never invokes the handler. Component coverage now asserts the heading destination, and `frontend/e2e/stocks.spec.ts:130` explicitly checks it after successful retained-data recovery. |
| UI-W02 | Resolved in source | `StockSection.tsx:160–164` reserves twenty responsive blocks,320px mobile/160px desktop, instead of five104px/52px blocks. This approximates the actual multi-line record footprint and retains one semantic loading status with presentation-only placeholders. Component coverage now requires all twenty placeholders. Exact CLS or pixel-perfect skeleton equivalence is not claimed. |

The helper change at `frontend/e2e/helpers.ts:44–49` waits for the actual `/markets` URL and visible Markets heading after submitting the code. It strengthens authenticated journey readiness and does not mock authentication or bypass app navigation. No new product UI, attribution, feed authority, stock execution control, typography or color change was introduced.

**Current source assessment:24/24** — Copywriting4, Visuals4, Color4, Typography4, Spacing4, Experience Design4. No active concrete UI defect remains from this audit. This score is a focused source reassessment, not a claim of fresh screenshot verification or final acceptance. The unchanged pillars retain their evidence above; Visuals now has twenty reasonably sized placeholders and Experience has an explicit stable post-recovery focus destination.

At the re-review log check, `/tmp/birja-phase07-plan13-browser-final.log` had completed render/build/startup and reached `START all-browser`, with no final browser result yet. Parent-reported component evidence is310 passing tests with98.91% line coverage; it was not independently rerun here. The final browser gate, live provider permission and owner visual acceptance remain separate and must not be marked passed from this report alone.
