# Phase 13 — UI Review

## Current Recheck — Four Warnings Resolved

**Rechecked:** 2026-11-18, after the bounded review repair.
**Current baseline:** Approved `13-UI-SPEC.md` and existing Birja MASTER; unchanged scope.
**Current render source:** `8cdd17582ba69cb0815bb0ecd48e4819a2c2f762`.
**Current packet:** `/tmp/birja-phase13-ui-review/`; ZIP SHA256 independently checked: `eac081810b48e9ddad875f3abc2a07510b3795c4b8d8aca7bec3ef29b8464c68`.
**Render binding:** 339 inputs, digest `9eee8a15364a997f189881aca49140c9e1ea7e56ae32dc78f15cf30cfaf86cbb`; Chromium `156.0.8078.4`; 72 HTML states / 120 PNGs / 265 hashed artifacts.
**Screenshots:** Actual recaptured PNGs inspected with `view_image`; no new capture, live probe, DB operation, package installation or source change by this auditor.

The four original findings are resolved by source and visible implementation evidence. The initial **19/24**, original warning text and its evidence are retained verbatim below as historical findings. Their screenshot references belong to the preserved packet `/tmp/birja-phase13-ui-review-before-review-fix/`, whose ZIP SHA256 remains `1fb8795e5acc82bf74186a12050363960a8469d2838db571fe4b9d44a874e8c6`. They do not describe the current packet.

### Current Pillar Scores

| Pillar | Score | Current specific evidence |
|--------|-------|---------------------------|
| Copywriting | 4/4 | Incomplete 1280 now visibly says “1 holding cannot be valued.” Source branches singular/plural; funding, cap and unavailable-return copy remain intact. |
| Visuals | 4/4 | Unknown 320/375 and desktop 1440 show a legible, nonshrinking error icon; hierarchy and neutral independent-book comparison remain intact. |
| Color | 4/4 | Repair introduces no palette/color changes; existing token and surface-balance findings still apply. |
| Typography | 4/4 | Repair retains the four approved sizes/two weights; mobile selector label now reads on one line without shrinking text. |
| Spacing | 4/4 | Stale-draft 320/375 now has a full-width 288/343×48px select, one-line 20px label and 8px gap before actions. |
| Experience Design | 4/4 | Unknown 320/375/1440 displays one recovery instruction; original read-only fields, explicit Retry/Close and stale-draft review remain available. |

**Current overall: 24/24.** No unresolved WARNING or BLOCKER was established in this bounded recheck. This score reflects the repaired warnings plus the unchanged passing baseline; it is not a claim of owner acceptance or full final-source qualification.

### Finding Dispositions

| Original finding | Disposition | Repair and recheck evidence |
|------------------|-------------|-----------------------------|
| W-01: collapsed mobile selector | Resolved | `frontend/src/components/PortfolioSwitcher.tsx:50` now uses `w-full flex-none` below md and restores `md:w-auto md:flex-1` above. Recaptured `phase13-stale-draft-320.png` and `-375.png` visibly put selection on its own row and actions below. Current manifest capture.layout records select widths 288/343px, height 48px, label height 20px and Open gap 8px. These measurements support the observed layout and replace the original roughly 34px control. |
| W-02: duplicate unknown recovery message | Resolved | `frontend/src/components/PortfolioCreateForm.tsx:292` suppresses the status copy when the alert already contains that exact instruction. Recaptured unknown 320/375/1440 visibly contains one instruction, with Retry creation and Close creation. The conditional retains status feedback for restored attempts with no matching alert; frozen original field/retry behavior is unchanged. |
| W-03: shrinking alert icon | Resolved | `PortfolioCreateForm.tsx:149` uses `size={20}` and `className="shrink-0"`. The unknown 320/375 images visibly retain a clear circular error mark; both current manifest layouts record a 20×20px icon. The 20px control/error symbol is consistent with existing MASTER icon guidance. |
| W-04: singular holding grammar | Resolved | `frontend/src/pages/PortfoliosPage.tsx:55` selects holding/holdings by count. `phase13-incomplete-1280.png` visibly confirms singular copy while retaining Known value, Return unavailable, source-time notice and the unaffected complete sibling. |

### Current Priority Fixes and Recommendation Count

No further priority fix or minor recommendation is established by this recheck. The original three priorities and one additional minor recommendation are all resolved; no extra redesign is proposed to fill a template.

- Open priority fixes: **0**.
- Open minor recommendations: **0**.
- Open BLOCKER findings: **0**.
- Historical WARNING findings: **4, all resolved**.

### Current Evidence and Remaining Gates

Personally inspected the six recaptured images `phase13-stale-draft-320.png`, `phase13-stale-draft-375.png`, `phase13-unknown-320.png`, `phase13-unknown-375.png`, `phase13-incomplete-1280.png` and `phase13-unknown-1440.png`. Read updated `13-UI-EVIDENCE.md`, the bounded-repair portion of `13-16-SUMMARY.md`, the three changed components and the current manifest/layout fields. This is targeted verification of repaired findings, not a second claim to have visually inspected all 120 images. Packet-verifier inventory correctness remains the separate code review's responsibility.

The updated execution evidence records 140 affected UI tests, 12 evidence-contract methods, an actual current-source 20-case browser run and 72-file/120-layout offline verification. Those are recorded executor receipts, not additional commands rerun by this UI auditor. Prior full-sourceA results and current focused-sourceC results remain distinct. Plan 17 must still execute its complete current-source qualification.

**Owner UI acceptance and genuine desktop native 200% acceptance remain pending Plan 18.** The current manifest independently inspected here has `owner_accepted: false` and `native_200_percent_verified: false`. Neither repaired screenshots nor automated viewport geometry satisfies those checks. `needs_human_review: true` remains applicable to those two owner outcomes. No phase-completion state is advanced.

Registry status is unchanged: initialized local shadcn source, zero third-party registry blocks, no flags or downloads.

---

## Initial Audit — Historical 19/24, Before Review Repair

**Audited:** 2026-11-18
**Baseline:** Approved `13-UI-SPEC.md`, checked by `13-UI-CHECK.md`, and `design-system/birja/MASTER.md`.
**Screenshots:** Existing actual Chromium captures inspected; no new live captures or server probes. This is a visual and source audit, not a code-only review.
**Scope:** New overview, creation, metadata editing and explicit portfolio switching. Existing accepted financial components retain their established styling.

## Evidence and limits

The reviewed packet is `/tmp/birja-phase13-ui-review/`, with index and manifest. ZIP SHA256 independently read during this audit: `1fb8795e5acc82bf74186a12050363960a8469d2838db571fe4b9d44a874e8c6`. The packet records render revision `e791d8888a2f09981a707e00504eaae4ac3674fe`, 339 render inputs, digest `304e012896cf3dc5e385bfa6dbb411d6e8007323c136204c660a1dc51eafde71`, Chromium `156.0.8078.4`, 72 HTML states and 120 PNGs. Provenance/test-engine correctness has a separate review; inventory is not a claim that this auditor visually inspected every image.

Images personally inspected through `view_image`: overview 320/768/1440; create-long-astral 375 and 1280 reflow; keyboard-error-focus 1280; edit 320; stale-draft 375/1440; unknown 375; incomplete 1280; cap 320; empty 375; error 1440; failed-refresh 375; switch 1280. Actual captured HTML/CSS and the manifest were also inspected. Full-page PNGs show fixed mobile navigation at the captured viewport position; content passing behind that bar in a stitched image does not by itself prove that scrolling cannot reach it.

The screenshot-storage gate ran: `.planning/ui-reviews/` exists, its existing `.gitignore` covers all required screenshot formats, and `git check-ignore .planning/ui-reviews/phase13-audit.png` confirms protection. No images were added to the repository. No Playwright MCP tools are available. Live server detection was deliberately skipped under the audit's explicit no-probe instruction. An optional file-only Playwright inspection failed at browser launch because the sandbox refused its socket; no extra runtime assertions or captures are claimed.

`13-UI-EVIDENCE.md` records 20 actual management browser cases and 120 offline viewport layouts. Those automated results supplement source and image inspection; they are neither owner acceptance nor genuine desktop native 200% zoom. Both manifest acceptance flags remain false. Plan 17 complete final-source qualification and Plan 18's two explicit owner outcomes remain separate gates. `needs_human_review: true` for owner visual acceptance and actual desktop browser-menu 200% acceptance.

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Exact funding/recovery language largely matches; singular unvalued holding uses plural grammar. |
| 2. Visuals | 3/4 | Clear hierarchy and truthful independent comparisons; recovery alert icon collapses on mobile. |
| 3. Color | 4/4 | Token palette, restrained accent surface and labeled states meet the contract. |
| 4. Typography | 4/4 | New management content uses the four approved sizes and normal/medium weights. |
| 5. Spacing | 2/4 | At 375px the new switcher select collapses below the required touch width. |
| 6. Experience Design | 3/4 | Recovery and stale-draft safeguards are present; unknown creation repeats the same live message. |

**Overall: 19/24**

No task-completion BLOCKER was established. Four distinct WARNING findings follow. Scores are independent; passing color and typography do not compensate for the mobile control defect.

## Top 3 Priority Fixes

1. **W-01 — Give the mobile selector its own full-width row.** In `frontend/src/components/PortfolioSwitcher.tsx:49`, the flexible field surrenders width to the Open button and Portfolios link. At 375px its select is roughly 34px wide and its label wraps into fragments. Use a full-width/basis-full field below the desktop breakpoint, with the actions wrapping beneath; retain 48px height and at least 8px separation. Recheck 320/375 and narrowed desktop layouts with long current names.
2. **W-02 — Announce unknown creation once.** `frontend/src/components/PortfolioCreateForm.tsx:281` and `:292` render the same recovery sentence in both an alert and a status. Keep one persistent recovery message with one appropriate live announcement and retain Retry creation/Close creation and the frozen original attempt. Verify the ordinary transport-unknown and restored-after-reload paths.
3. **W-03 — Prevent the error icon from shrinking.** Add `shrink-0` to the 16px `AlertCircle` at `frontend/src/components/PortfolioCreateForm.tsx:149`. The 375px unknown screenshot shows it compressed to a tiny mark. Preserve the existing gap and token color; recheck long error text at 320/375px.

## Detailed Findings

### Pillar 1: Copywriting (3/4)

**WARNING W-04 — Singular count uses plural grammar.** `frontend/src/pages/PortfoliosPage.tsx:54` always renders `{count} holdings cannot be valued.` The incomplete 1280, failed-refresh 375 and cap 320 images visibly say **“1 holdings cannot be valued.”** The approved contract explicitly distinguishes singular and plural. Render `1 holding cannot be valued.` for one and the existing plural for other counts. This does not make the amount misleading, but it is an observable contract deviation.

Positive evidence: the overview explanation and empty-state funding language match the contract (`PortfoliosPage.tsx:133`, `:193`); cap refusal remains explicit (`:136`). Creation names its independent $10,000 funding and separates Discard draft from submitted Close creation (`PortfolioCreateForm.tsx:276`, `:350`). The unknown screenshot offers Retry creation without claiming cancellation. Metadata editing explains that financial records remain unchanged (`PortfolioMetadataForm.tsx:116`). Missing values show Return unavailable, and undefined percentages use Not applicable (`PortfoliosPage.tsx:43`, `:59`). No generic Submit or destructive/reset/transfer/deposit control was introduced on these new surfaces.

### Pillar 2: Visuals (3/4)

**WARNING W-03 — Mobile error symbol loses its intended size.** In `phase13-unknown-375.png`, the decorative alert icon is almost a dot beside a four-line message. `PortfolioCreateForm.tsx:148` uses a flex row and `:149` fixes nominal size without disabling flex shrink. A 16px nonshrinking icon keeps the error visual consistent. The message is still readable and labeled, so this is a quality defect rather than a task blocker.

Positive evidence: overview 1440/768 exposes a semantic table, while overview 320 exposes labeled card values (`PortfoliosPage.tsx:200`, `:249`). Names wrap fully as links, metadata is separate, neutral Open links remain visible, and there is no pooled wealth hero or ranked order. Incomplete 1280 keeps the unaffected sibling complete while clearly labeling known value and unavailable return. Create/edit use inline cards before the financial content; stale-draft 1440 shows the latest authoritative description next to the preserved draft. The inherited detail gradient is not a new overview accent or a reason to restyle accepted financial components.

### Pillar 3: Color (4/4)

No color defect established. New surfaces use existing semantic tokens rather than arbitrary colors. A scan of `PortfoliosPage`, `PortfolioCreateForm`, `PortfolioMetadataForm` and `PortfolioSwitcher` found zero raw hexadecimal colors; these files contain three `bg-warn-soft`/`text-warn-text` pairs, one `bg-loss-soft` alert and three `text-loss-text` sites. Direct `bg-primary`/`text-primary`/`border-primary` occurrences are zero because primary action styling comes from the reused Button variant, not because primary actions are absent.

Overview 1440 and empty 375 are predominantly neutral canvas/cards; the primary action and active navigation occupy a small portion of the surface. No new gradient, colored action or decorative accent proliferation appears. Semantic warning/error fills in failed-refresh/stale-draft/unknown explain exceptional state and do not replace the palette. The source tokens are `--loss-text: #B83270`, `--loss-soft: #FBEAF2`, `--warn-text: #8F5200` and `--warn-soft: #FEF4E2` (`frontend/src/index.css:36`). A read-only PNG pixel check of the duplicate-error region confirmed the actual error text includes RGB(184,50,112) and its fill RGB(251,234,242), matching these tokens. Incomplete and failure meaning also appears in words, not color alone. The 60/30/10 rule is assessed as surface balance, not an invented exact pixel quota.

### Pillar 4: Typography (4/4)

No new-surface typography defect established. The four audited management files contain 15 `text-sm`, 21 `text-base`, seven `text-xl` and one `text-[32px]` occurrences. Nine explicit `font-medium` occurrences are the only declared weight utility; body content inherits normal weight. This is the approved 14/16/20/32px and 400/500 system, with 20/24/28/40px role line heights in the source (`PortfoliosPage.tsx:107`, `:110`, `:208`, `:252`; `PortfolioCreateForm.tsx:78`, `:106`, `:261`; `PortfolioMetadataForm.tsx:80`, `:116`).

Monetary columns, counters and times use tabular figures (`PortfoliosPage.tsx:20`, `:229`, `:261`; `PortfolioCreateForm.tsx:116`). Full metadata wraps in read views; text fields retain input editing behavior rather than silently truncating stored input. The existing reused PortfolioContext, shell and accepted financial detail have their older MASTER typography, expressly retained by the phase contract and Plan 13 summary. They are not counted as newly invented management sizes. W-01's fragmented label is a width-allocation defect, not evidence for adding font sizes or shrinking text.

### Pillar 5: Spacing (2/4)

**WARNING W-01 — Mobile selector collapses below the minimum control width.** `phase13-stale-draft-375.png` visibly shows a very narrow select at the left of Open selected portfolio and Portfolios. Its label breaks “Open portfolio” into several fragments. The image places the select at about x16–50, approximately 34px wide, below the approved 44px minimum hit width. The same layout in edit 320 gives the field only a narrow text window. Source cause: `PortfolioSwitcher.tsx:49` uses a wrapping action row, while `:50` grants the field `flex-1 min-w-0` without a mobile minimum or full-row basis; the button does not shrink. Full current metadata remains readable separately, but choosing another strategy is unnecessarily hard. Give the field a complete mobile row and retain explicit Open below it. This is a notable responsive contract gap and justifies 2/4 even though page overflow checks pass.

Other audited spacing utilities are `gap-1/2/3/4`, `p-3/4/6`, `px-3`, `py-3`, `mb-3`, `mt-2/4`, `my-4/8`: 4/8/12/16/24/32px scale values. Twelve-pixel compact spacing and the 40px heading line box are explicitly allowed by MASTER/UI-CHECK and are not violations of a generic scale. Cards use 16px mobile and 24px desktop padding, field content is capped at 640px, inputs are 48px high and ordinary actions have minimum 44px height. Overview 320 and long-form reflow 1280 preserve ordinary page scrolling and wrapping rather than a fixed-width modal or horizontal comparison scroller. The 52px table row minimum is functional sizing, not an arbitrary spacing exception.

### Pillar 6: Experience Design (3/4)

**WARNING W-02 — Unknown result is duplicated visually and across live regions.** `PortfolioCreateForm.tsx:248` obtains the exact unknown message from `managementMessage`; `:281` renders it through focused `FormError` (`role="alert"`), and `:292` renders the same text again in `role="status"`. Both copies are visible in `phase13-unknown-375.png`. This adds noise at the moment the user needs one clear recovery instruction and can cause duplicate assistive-technology announcements. Keep a single persistent message while preserving an announcement for restored attempts where there is no error object. Do not remove or change the original-key recovery behavior to address presentation.

Positive state coverage: initial loading is neutral skeleton/status, failure has Try again, empty is a valid state, failed refresh labels retained data, and cap disables new creation with a reason (`PortfoliosPage.tsx:136`, `:154`, `:177`, `:193`). Incomplete handling leaves sibling strategies usable and presents source-time limitations (`:17`, `:43`). Field errors have explicit labels, `aria-invalid` and `aria-describedby`; the focused error summary links to the invalid field (`PortfolioCreateForm.tsx:80`, `:137`). Existing actual browser cases assert focused duplicate alerts and keyboard field recovery (`frontend/e2e/portfolio-strategies.spec.ts:205`, `:770`).

Creation freezes fields for pending/unknown intent and provides explicit retry/close (`PortfolioCreateForm.tsx:208`, `:292`, `:321`). Success navigation checks a current receipt (`:216`); closed forms do not cancel the submitted attempt. Stale-draft 375/1440 visibly retains user input, shows latest authoritative values and disables Save until review (`PortfolioMetadataForm.tsx:130`, `:170`). Switching is a native select with immutable-ID option values and a separate guarded Open action (`PortfolioSwitcher.tsx:40`, `:54`, `:69`). Selecting alone does not navigate. Source guards retain route/editor lease, original creation identity and owner/session checks (`usePortfolioManagement.ts:125`, `:334`, `:393`, `:469`, `:527`). Monetary values are formatted from server strings; this page computes no pooled total or financial return. No destructive confirmation is needed because deletion is deferred and no delete control exists.

These observations do not substitute for Plan 17's complete final-source browser/security/recovery qualification or Plan 18's owner/native-zoom outcomes.

## Registry Safety

Registry audit: **0 third-party blocks checked, no flags**. `frontend/components.json` is initialized but its `registries` object is empty. The approved registry table declares only existing local official Button/Input/Card/Badge source. No registry fetch, `npx`, install or package change was needed.

## Files Audited

- `AGENTS.md`, `CLAUDE.md`, `.codex/GSD-ADAPTER.md`; GSD UI review skill/workflow/auditor role and ui-brand reference; UI/UX Pro Max skill and local error-summary search results.
- `design-system/birja/MASTER.md`; current project/requirements/roadmap/state context; Phase 13 context, UI-SPEC, UI-CHECK, UI-EVIDENCE, plan intent and execution summaries, especially Plans 08–13/16/18.
- `frontend/src/pages/PortfoliosPage.tsx`, `frontend/src/components/PortfolioCreateForm.tsx`, `PortfolioMetadataForm.tsx`, `PortfolioSwitcher.tsx`, `PortfolioContext.tsx`.
- Relevant state/guard portions of `frontend/src/hooks/usePortfolioManagement.ts`, `usePortfolioOverview.ts`; UI focus assertions in `frontend/e2e/portfolio-strategies.spec.ts`.
- `frontend/src/components/ui/button.tsx`, `input.tsx`, `card.tsx`; `frontend/src/index.css`; `frontend/components.json`.
- Packet manifest, actual captured HTML/CSS and the 16 PNGs listed above; existing screenshot `.gitignore`.

**Recommendation count:** 3 priority recommendations, 1 additional minor recommendation, 0 BLOCKER findings. Owner/native 200% acceptance remains pending; this audit does not advance phase completion.
