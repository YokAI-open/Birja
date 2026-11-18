---
phase: 13
slug: create-and-compare-independent-strategies
status: approved
reviewed_at: 2026-11-18T07:06:48.452796+00:00
shadcn_initialized: true
preset: existing radix-vega / neutral / CSS variables
created: 2026-11-18
---

# Phase 13 — UI Design Contract

> Planning contract for the new management surfaces. Checker approval and actual implemented owner acceptance are separate gates.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing shadcn source; no initialization or installation |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing React, Tailwind v4, shadcn/Radix; native HTML controls where no copied component exists |
| Icon library | Existing Lucide, 20px controls / 16px inline, decorative icons hidden |
| Font | Existing self-hosted Inter Variable; tabular figures on monetary values, counts and timestamps |
| Authority | `design-system/birja/MASTER.md`, `frontend/src/index.css`; no page overrides exist |
| Existing components | `Button`, `Input`, `Card`, `Badge`; reuse `PortfolioContext`, monetary formatters, outcome and freshness semantics |

Sources: CONTEXT D-13; actual `frontend/package.json`, component source and tokens. Existing financial detail, holdings, trading, receipts and History retain Phase12's accepted layout. New UI uses the bounded typography below without globally restyling those surfaces. Native select and textarea use existing input tokens; no new package, registry block, font, image, chart or gradient is required.

The installed local shadcn `info` command was attempted on 2026-11-18 and failed resolving `ui.shadcn.com/r/index.json` (`EAI_AGAIN`). Local configuration/source provide the recorded setup; no online preset verification or download is claimed. Existing setup is already required by D-13, so no initialization or design-system confirmation interview is needed.

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Label/helper relationship, inline icon gap |
| sm | 8px | Adjacent controls and badge gaps |
| compact | 12px | Mobile card gaps and field stacks |
| md | 16px | Mobile gutters/card padding, desktop card gaps |
| lg | 24px | Desktop card padding, form section separation |
| xl | 32px | Desktop gutters and page top/bottom spacing |
| 2xl | 40px | Maximum new heading line box |
| 3xl | 48px | Input/select height |

Source: MASTER spacing scale; subset used for this phase. Controls have minimum 44×44px hit areas; overview table rows have minimum 52px height. Both are multiples of four and explicit functional dimensions. Cards use existing 24px radius, inputs 14px and buttons pill radius; these are inherited shape tokens rather than spacing exceptions. No additional spacing values.

## Typography

Exactly four sizes and two weights on new surfaces. Source: Inter and MASTER role hierarchy; phase defaults choose a 16px body and compact comparison density under D-13 discretion.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body / form input / option | 16px | 400 | 24px (1.5) |
| Label / helper / timestamp | 14px | 400 | 20px |
| Heading / strategy name | 20px | 500 | 28px |
| Display / page h1 | 32px | 500 | 40px (1.25) |

Buttons and emphasized financial values use 16px/500/24px. Use 14px/500 for column headings. Monetary values in the overview use 20px/500/28px only when presented as mobile card headlines. Long names/descriptions and large numbers wrap with `min-width: 0` and `overflow-wrap: anywhere`; never shrink critical text or require hover to read full metadata.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` #F2F2F2 | App canvas, calm empty space |
| Secondary (30%) | `--card` #FAFAFA; `--popover` #FFFFFF | Overview/form cards, white inputs and secondary controls |
| Accent (10% maximum) | `--primary` #18181B; `--accent` #EEF1FE / `--accent-foreground` #3451D1 | One primary action, active navigation, selected control tint |
| Destructive | `--destructive` #B83270 | No destructive action in Phase13; token retained, no delete control |

Accent reserved for: Create portfolio (Save changes while editing), active main navigation, selected switcher choice and existing focus rings. Neutral Open portfolio links/buttons remain secondary. Logo orange stays logo-only. Gains use existing `--gain-text`/soft, losses `--loss-text`/soft, warnings `--warn-text`/soft; signs, arrows and explicit labels accompany meaning. Errors use existing loss text with an error icon, distinct from an action. Ratios describe visual surface balance, not replacement palette tokens. Components use token classes, never raw hex. New overview has no highlight gradient and no pooled hero amount.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Page title / navigation | Portfolios |
| Primary CTA | Create portfolio |
| Creation heading | Create portfolio |
| Name label / helper | Portfolio name / 1–60 characters. Names must be unique among your active portfolios, ignoring case. |
| Description label / helper | Description (optional) / Plain text. Up to 1,000 characters. |
| Description counter | `{count} / 1,000 characters` |
| Funding explanation | Each new portfolio starts with $10,000.00 in virtual cash. Its cash and investments stay separate. |
| Empty state heading | No portfolios yet |
| Empty state body | Create a portfolio to start an independent strategy with $10,000.00 in virtual cash. |
| Zero-description view | No description. |
| Overview explanation | Compare each portfolio with its own starting cash. Returns are since each portfolio began. |
| Count / cap | `{count} of 10 active portfolios` / You have 10 active portfolios. You can't create another right now. |
| Open / edit / save | Open portfolio / Edit portfolio / Save changes |
| Unsubmitted creation discard | Discard draft |
| Metadata edit discard | Discard changes |
| Pending / unknown creation close | Close creation |
| Editing explanation | Changes to the name or description do not change cash, investments or History. |
| Loading / refresh | Loading portfolios… / Refresh portfolios / Refreshing portfolios… |
| Initial overview error | Can't load your portfolios right now. Try again. |
| Failed background refresh | Couldn't refresh your portfolios. Only still-permitted values from the last update are shown. |
| Generic creation refusal | Couldn't create this portfolio. Review the message below and try again. |
| Unknown creation result | We couldn't confirm whether your portfolio was created. Retry this creation to check its original result. |
| Unknown recovery CTA | Retry creation |
| Creation pending | Creating portfolio… |
| Creation success | Portfolio created. |
| Active creation replay success | Original portfolio confirmed. |
| Required name | Enter a portfolio name. |
| Name length / controls | Use 1–60 characters. / Remove control characters from the name. |
| Duplicate name | You already have an active portfolio with this name. Choose another name. |
| Description limit / controls | Use 1,000 characters or fewer. / Remove unsupported control characters from the description. |
| Creation payload conflict | This creation attempt has different details. Retry the original creation; no new portfolio has been requested. |
| Closed original creation | The original portfolio is unavailable. This creation cannot create it again. |
| Rate refusal | Too many attempts. Try again `{after the displayed wait}`. |
| Capacity/service refusal | Creation is unavailable right now. Your details are kept here. Try again later. |
| Metadata pending / success | Saving changes… / Portfolio updated. |
| Metadata unknown result | We couldn't confirm your changes. Check the latest details before saving again. |
| Metadata stale change | This portfolio's details changed. Review the latest details before saving. |
| Unavailable target | This portfolio is unavailable. Choose another portfolio from Portfolios. |
| Switcher label / action | Open portfolio / Open selected portfolio |
| No chosen target | Choose a portfolio to continue. |
| Incomplete valuation | Known value: `{amount}` — incomplete |
| Missing holdings | `{count} holding cannot be valued.` / `{count} holdings cannot be valued.` |
| Missing return | Return unavailable |
| Missing retained value | Value unavailable — refresh required |
| Baseline | Compared with your `{starting_cash}` start |
| Undefined percentage | Not applicable |
| Destructive confirmation | None. Do not expose Delete, Trash, Restore, reset, transfer or deposit controls. |

Errors are inline and persistent until resolved; successes use a polite inline status. Do not require a toast to understand an outcome. Replace the variable rate wait with the server's Retry-After timing, never a fabricated countdown. Authentication expiry uses the existing sign-in screen, not an order-specific error message.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | Existing local Button, Input, Card, Badge source only | 2026-11-18: existing source/config inspected; no new block fetch; official gate not required |
| Third-party | None | 2026-11-18: `components.json.registries` is empty; no third-party block declared; vetting not applicable |

## Routes, Layout and Components

These are concrete phase choices under CONTEXT Agent Discretion, grounded in `App.tsx` and `PortfolioTargetBoundary.tsx`.

1. Make existing `/portfolios` the signed-in overview, independent of having a selected financial target. It currently renders a target-required refusal; replace that route's element deliberately. Never mount overview through a boundary that requires one portfolio. The main Portfolio tab becomes **Portfolios**, linking here; preserve three mobile tabs (Markets, Portfolios, History), existing Account access and shell safe-area padding.
2. Keep `/portfolios/:portfolioId`, `/portfolios/:portfolioId/history`, `/portfolios/:portfolioId/trade/:symbol` and `/portfolios/:portfolioId/trade/stocks/:symbol`. IDs stay canonical bigint strings. Preserve legacy `/portfolio`, `/history` and trade entry behavior when one identity is unambiguous; multiple possible targets offer the overview, never a financial fallback. An explicit unavailable ID always refuses rather than selecting another identity.
3. Overview header: h1, active count, secondary Refresh portfolios and primary Create portfolio. At ten, keep Create visible but disabled with its visible reason. While list/cap is unknown, disable submission until authoritative state is available. An existing unknown creation remains retryable even at ten.
4. Overview uses a semantic table at 768px and wider, with columns Portfolio, Cash, Total / known value, Return, Open. Stable ascending numeric ID order, no sorting or ranking. At narrower widths use a one-column list of cards with labeled values in the same order and exactly one Open portfolio link per strategy. Only one responsive representation is exposed to assistive technology. Names are full, wrapping links to explicit detail IDs; rows are not nested clickable regions. Description appears in a separate wrapping metadata line in each card/portfolio cell; empty descriptions show No description.
5. Create opens an inline card immediately below the header, before the list. Heading Create portfolio; name, optional description, funding explanation, Create portfolio, Discard draft. No new `/new` dynamic-ID collision or modal dependency. Keep at most one create form/attempt. On open, focus name. Discard draft closes an unsubmitted form and returns focus to Create; no request occurs. Pending/unknown creation replaces Discard draft with Close creation: closing preserves the original attempt and leaves a visible recovery notice on overview. Close creation never asserts cancellation of a submitted request or resets its mutation/recovery state.
6. On definitive creation or active replay, invalidate management data, navigate to `/portfolios/{original_result_id}` and focus the existing page h1 when mounted. Display the authoritative current name/description, including a later rename; don't rewrite the original creation payload. A first creation from zero follows exactly this flow. Existing initial signup still creates only My portfolio with an empty description and the one grant.
7. Detail retains its accepted financial content. Add a metadata card adjacent to existing portfolio context: full name, description (preserved line breaks), Edit portfolio and Back to Portfolios. Edit expands in place to the same labeled fields, Save changes and Discard changes. Empty textarea plus Save clears the description. No separate destructive Clear button. Discard changes discards unsaved edits and restores focus to Edit portfolio. Success closes editor, restores focus, announces Portfolio updated and refreshes name/description across relevant views.
8. Add a labeled native select and Open selected portfolio button in the context area of portfolio-specific views; use the same control in Markets when choosing a financial target. Options are stable ID ascending and display `{name} · #{id}`; option values are immutable IDs. Show the current name separately and select its ID. Selecting changes only the pending choice; explicit Open navigates to the selected detail route. Do not automatically navigate on arrow-key selection or carry a trade ticket into another strategy. An overview link stays available. No custom popup menu is required.

Cards use max content width 1440px, the existing shell gutters, 24px desktop / 16px mobile padding and min-width zero. Create/edit cards use full available width with field content capped at 640px. At 320px all header actions and form actions stack; no fixed-width dialog or clipped select. Desktop table may become cards at any effective width below 768px, including zoom. Footer navigation must not cover focused fields, status or buttons.

## Metadata and Data Contract

Sources: D-01–D-09; research Concrete metadata rule, API transport and Bounded exact overview. These technical choices are selected under Agent Discretion, not new owner requirements.

- Names: reject C0/C1 controls in raw input before trimming; use the research's explicit Unicode White_Space trim set, then NFC and 1–60 Unicode code points. Reject NUL/unpaired surrogates. The database is authoritative for `NFC(casefold(display_name COLLATE pg_catalog.pg_unicode_fast))`; do not implement uniqueness with browser lowercase. Preserve accents and display casing. UI accepts Unicode, sends raw validated strings and uses canonical returned metadata. Client validation is assistance; duplicate/race validation comes from the server.
- Descriptions: initial/default `''`; 0–1000 Unicode code points after CRLF/CR → LF, preserve whitespace and line breaks, allow TAB/LF, reject remaining C0/C1 controls, NUL and unpaired surrogates. Count Unicode code points, not UTF-16 units; do not use HTML maxlength alone as the Unicode boundary. Permit editing/pasting over the bound and show an error/counter without silent truncation; disable submission until valid. Omission on create means empty, PATCH absence means unchanged, explicit empty clears; null is invalid.
- All metadata uses React escaped text, including labels/options and strings resembling HTML, scripts, URLs or currency. No HTML/Markdown interpretation, automatic links or `dangerouslySetInnerHTML`.
- Preserve exact two-key `{id,name}` parsing of GET `/api/v2/portfolios`. Use the research's separate GET `/api/v2/portfolios/overview`, POST `/api/v2/portfolios`, PATCH `/api/v2/portfolios/{id}` and explicit strict management response parsers for descriptions. Register static overview before dynamic backend routes. Do not append description or financial fields to the existing identity list without an explicit coordinated parser change.
- Comparison shows each portfolio's own cash, stored starting_cash, total_value or known_value, dollar and percentage return, completeness, unvalued count, valued_at and prices_as_of. Never calculate returns, sums or a pooled wealth amount in JavaScript. Strict string money parsing and existing formatUsd/signed outcome helpers preserve exact transport and escaping. No NaN, Infinity or fabricated zero for missing values.
- Complete books show total and signed dollar/percentage return. Incomplete books show known value explicitly marked incomplete and Return unavailable for both overall returns; missing safe known value shows Value unavailable — refresh required. Zero-baseline percentage is Not applicable, not 0%. Empty holdings with cash are a valid complete strategy.
- Show Calculated at and applicable oldest source timestamp in each row/card with full accessible local timestamp/time-zone text using existing timestamp formatting and `<time dateTime>`. Preserve dated/halted stock mark, expiry and safe-value suppression semantics from detail; a fresh network response alone does not make a mark fresh. Ages do not announce every tick. Overview/detail parity means equal valuation inputs/time produce equal figures; independent requests need not pretend to share a historical timestamp.
- One incomplete strategy does not replace other rows with an error. If the overview endpoint itself fails, use the whole-request state below. Newly completed trades/events invalidate the appropriate overview/detail queries; overview must consume shared market evidence, not create per-book market polling.

## Interaction and Failure States

| Surface / transition | Required behavior |
|----------------------|-------------------|
| Overview initial loading | Content-shaped neutral skeletons, Loading portfolios status, no fabricated count/value |
| Overview empty | Valid signed-in state, empty copy and Create portfolio action; browse Markets/account still work; no automatic grant or target |
| Overview initial failure / malformed data | Inline error with Try again; never turn invalid data into an empty list or choose a fallback portfolio |
| Overview refresh | Keep stable order and focus; disable duplicate refresh, announce pending then completion |
| Failed refresh | Retain only still-authorized, unexpired permitted values with visible failed-refresh notice and timestamps; suppress unsafe financial values individually as detail does; Retry refresh action |
| Creation editing → submitting | Freeze exact key/payload and owner/session; disable field changes and duplicate submit; show Creating portfolio; no optimistic cash, strategy row or grant |
| Creation definitive input/name error | Restore editing, keep all fields; focus linked error summary then field; no lost description; a corrected explicitly submitted creation may get a new key only after definitive refusal |
| Creation limit race | Keep form data and visible limit reason; disable new creation. Original unknown retry must still work because replay precedes count/name checks |
| Creation rate/service refusal | Keep data; honor server retry timing; definitive refusal can return to editing; transport errors or ambiguous server failures stay unknown |
| Creation submitting → unknown | Freeze original request; show persistent recovery notice and Retry creation. Never silently allocate a new key, even after refresh, navigation, changed count/name or renamed original portfolio |
| Creation reload recovery | Restore strictly validated bounded owner-bound outstanding attempt; show original form read-only and ask for explicit Retry creation. No automatic resubmission on mount, sign-in or focus |
| Creation key conflict | Keep original attempt/payload; show explicit conflict message and recovery retry path. Do not silently “fix” it with a new key or fund a replacement |
| Creation replay closed target | End the unavailable attempt with the closed-original message; no recreation or redirect to another book. A later explicit new creation is a separate intent/key |
| Metadata submitting / unknown | Freeze submitted metadata, retain draft; on ambiguity refetch this ID's latest management metadata for review. Never overwrite newer metadata with an automatic retry. No cash invalidation grants or creation request |
| Metadata changed in another tab | Invalidate metadata. While editing retain draft and show stale-change notice; require review/reload of current metadata before explicit Save. Outside editing update labels from authoritative response |
| Switch | Revoke captured previews before mounting next financial page; load verified explicit target, reset scoped cursors; no previous book's money displayed while loading |
| Rename with unresolved order | `usePortfolioTarget.isCurrent` currently compares name as well as ID. Refresh/revoke actionable previews safely, but retain each original unresolved order's ID, original payload and captured label; never drop it as a failed order or rebind it to the new label/target |
| Switch while create/order unresolved | Preserve original attempt at its root; navigation neither cancels a committed request nor creates a new target for it. Late callbacks cannot navigate, announce success or publish financial state into a newer owner/session/target |
| Unavailable explicit target | Existing refusal/privacy boundary; offer Portfolios for another explicit choice; no hidden financial child, historical payload or arbitrary fallback |
| Logout / owner change / auth expiry | Revoke private scopes and clear private queries/drafts/creation recovery state; ignore old callbacks and stop showing private metadata or numbers. No automatic create on subsequent sign-in |

Creation recovery uses the research's bounded owner-scoped sessionStorage for one immutable original key/payload only; use an opaque owner binding rather than an email in storage. Store no tokens, balances, holdings, receipts or other financial state, and no PII in localStorage. Persistence must succeed before a new POST; if unavailable, keep the draft and refuse submission with an inline recovery-storage explanation rather than risking a lost retry identity. Clear only on definitive resolution/logout/owner change, not simple close/navigation. This narrowly scoped metadata is solely for same-tab refresh recovery and is never a financial authority. Do not put names/descriptions or attempt keys in URLs, logs or cross-tab messages.

Cross-tab coordination uses identity-only same-origin invalidation signals (opaque scope/portfolio ID, no names, descriptions, financial state or credentials) with focus-refetch fallback. Revalidate authoritatively before applying changes; clean listeners on logout. Never store shared financial state in browser storage. Owner/session and abort/serial checks govern all new management/overview results and mutations just as the existing target hooks do.

## Accessibility and Responsive Acceptance

- Use one h1 per routed page, semantic table captions/column headers or card definition lists, real labels, descriptive button names and native select behavior. Every form error connects through aria-describedby and aria-invalid; failed submission focuses a summary with field links. Status messages are polite; errors use alerts without repeated announcements on each poll.
- Route transitions focus the destination h1 using the existing shell behavior; inline create/edit focus the name on entry and restore the trigger on close. Background refetch/rename must not steal focus. No modal/dialog is introduced; no hidden focus trap. Browser Back follows real explicit routes and does not resubmit a mutation. In-page form close changes no route/history entry.
- Keep all controls at least 44×44px with 8px separation; existing 2px ring / 2px offset, contrast at least 4.5:1 for text and 3:1 for meaningful UI indicators. No hover-only details, color-only profit/loss, disabled-zoom viewport or clipped long option text as the sole current-name display.
- Reflow checks at 320, 375, 768 and 1280px, plus inherited MASTER 1024/1440 cases: no horizontal page overflow, overlap, hidden menu/focus, inaccessible form errors or financial text clipped by bottom navigation. Use ordinary page scrolling, not tiny nested form scroll regions. Table changes to cards rather than forcing horizontal comparison scrolling.
- Existing 120–150ms hover/press timing; only opacity/transform, respect reduced motion. No chart, decorative animation, new asset or additional font download.

## Execution Evidence and Requirement Coverage

Sources: CONTEXT D-01–D-14 and `13-VALIDATION.md`. No tests, browser runtime or human UAT were performed to write this contract. The executor must provide implemented evidence; checked planning documents do not constitute accepted UI.

| Requirement | Implemented evidence required |
|-------------|-------------------------------|
| PMGT-01 | 0/1/10 overview, active-cap race with preserved draft, retained closed slot/name fixture permits a new ID; no public delete controls |
| PMGT-02 | Rename, Unicode normalization/duplicate/casefold/control/length corpus, independent owner names, unchanged money/history |
| PMGT-06 | Initial empty description, create/view/edit/clear, whitespace and 1000-codepoint boundaries including astral characters, escaped markup |
| PFUND-01 | Exact new $10,000 once, initial My portfolio empty description, preserved migrated/custom baseline and zero-book identity |
| PFUND-02 | Lost creation response and refresh recovery with original key/payload, renamed/cap/closed replay, conflict; no silent new grant |
| PFIN-01 | Two API-created strategies buy/sell the same crypto/stock independently; per-book cash and basis display |
| PFIN-04 | Active sibling dividends/corrections/split effects and History stay attributable; overview refreshes correct roots |
| PCTX-02 | Keyboard switch, pending/unknown create/order, late responses, metadata rename/isCurrent invalidation, logout/owner change and cross-tab refresh isolation |
| PVIEW-01 | Stable numeric-ID order, all active names/cash/value/returns, no pooled total or ranked sorting |
| PVIEW-02 | Shared valuation/detail parity; mixed complete/incomplete rows, authority expiry and safe failed-refresh suppression, visible source timestamps |
| PSAFE-07 | Bounded request/response/cap/rate states, no duplicate polling, existing stock/backup guards retained |

Automated evidence belongs in strict API/parser/hook/component tests plus the actual new browser management journey, alongside the validation strategy's isolated database/accounting, critical coverage, security and current/retained recovery gates. Owner UAT must inspect implemented overview/create/edit/switch, success/error/retry/empty/cap/incomplete states and keyboard behavior. Owner must also perform actual desktop browser native 200% zoom and confirm readable/reachable controls, no overlap, horizontal page overflow or obscured focus; CSS scaling/device emulation alone does not satisfy this check. Phase12 acceptance applies only to unchanged screens. Phase14 public deletion/full zero-after-delete journey and Phase15 integrated lifecycle acceptance remain deferred; zero-book retained fixtures and basic creation are valid now.

## Research Provenance

2026-11-18 local UI skill searches: `financial portfolio comparison dashboard neutral bento --design-system -p Birja`; `form error loading keyboard focus responsive --domain ux -n 5`; `accessible form select controlled state --stack react -n 3`. The generic design-system search suggested dark/Fira/enterprise marketing; those conflict with MASTER and are rejected. Focus visibility, keyboard navigation, focused error summary and controlled field guidance support this contract. No `--persist`/`--force` or design-system modification occurred. Existing source supplies all component/token APIs used here; no external library documentation, dependency change or design asset is needed.

Pre-populated: CONTEXT's 14 decisions; research metadata/transport/recovery/valuation recommendations; existing `components.json` and actual route/hook/component contracts. New discretion resolved here: stable ID order, `/portfolios` overview, inline forms, explicit native-select Open action, success navigation, compact four-size/two-weight typography, Unicode/description bounds and failure copy. No new product question is outstanding. Issue35 accepted-risk and Phase7 deferred boundaries remain unchanged.

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Planning checker approval:** approved in13-UI-CHECK.md; actual implemented owner UI/native200 acceptance remains pending Plan18.
