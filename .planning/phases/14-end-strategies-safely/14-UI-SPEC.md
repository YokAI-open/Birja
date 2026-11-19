---
phase: 14
slug: end-strategies-safely
status: approved
reviewed_at: 2026-11-19
shadcn_initialized: true
preset: existing radix-vega / neutral / CSS variables
created: 2026-11-19
---

# Phase 14 — UI Design Contract

> Planning contract for terminal portfolio deletion and its privacy/recovery states. It is not implementation evidence, checker approval or owner acceptance.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing local shadcn source; no initialization or installation |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing React 19.3.1, Tailwind 4, shadcn/Radix; semantic native HTML for the inline confirmation |
| Icon library | Existing Lucide; 20px controls/errors, 16px inline, decorative icons hidden and nonshrinking |
| Font | Self-hosted Inter Variable; existing tabular figures for counts and timestamps |
| Authority | `design-system/birja/MASTER.md`, actual `frontend/src/index.css`, accepted Phase13 management patterns; no page overrides exist |
| Reused components | `Button` including its existing destructive variant, `Card`, `PortfolioContext`, metadata management surface, `PortfolioTargetBoundary`, existing overview/switcher |

Source/config detection satisfies the existing-system gate. `components.json` exists, declares no third-party registries, and the copied Button already supports destructive actions. No dialog, alert-dialog, new package, registry block, font, chart or image is necessary. No CLI initialization, online preset verification or package execution was performed. Preserve the accepted overview/create/edit/switch and financial layouts; add only the lifecycle controls and states specified here.

### Upstream decisions and boundaries

No Phase14 CONTEXT.md or new discussion record exists. Locked policy comes from approved `REQUIREMENTS.md` PMGT-03/04/05, PFIN-05/06, PCTX-03, PSAFE-01 and acceptance interpretations, PROJECT and ROADMAP. Technical recommendations come from `14-RESEARCH.md`; inline placement, exact copy, focus behavior and recovery presentation are design discretion resolved here.

Deletion ends any owned experiment, including one with holdings or the last portfolio. It freezes committed cash, holdings, basis and financial History, stops later dividends/splits/corrections including earned-but-unpaid effects, and keeps evidence outside normal screens. It does not sell assets, transfer money, reset another portfolio, purge evidence or offer undo/trash/restore/export. Existing stock activation remains gated; deletion must not depend on an open market, fresh quotes or live provider permission. Corrupt retained lineage refuses atomically instead of inventing missing evidence. No new owner approval, provider operation or production change follows from this contract. Phase13's accepted UI/native200 outcomes cover its unchanged surfaces only.

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Heading/helper and icon/text relationships |
| sm | 8px | Minimum action separation, status gaps |
| compact | 12px | Mobile card and stacked text gaps |
| md | 16px | Mobile card padding/gutters, confirmation text stack |
| lg | 24px | Desktop card padding and management section separation |
| xl | 32px | Desktop page gutters, page top/bottom separation |
| 2xl | 40px | New page heading line box |
| 3xl | 48px | Inherited form/select height |

All spacing values are multiples of four and reuse MASTER/Phase 13. Functional dimensions: controls have at least 44×44px hit areas, with at least 8px between actions; existing overview rows at least 52px high. Existing 24px card, 14px control and pill radii are shape tokens, not additional spacing. Content uses fluid width and natural height; no fixed-height warning box.

## Typography

Exactly four sizes and two weights on new lifecycle surfaces, preserving Phase13 management typography. Unchanged financial pages retain their accepted inherited hierarchy.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body / consequence text / actions | 16px | 400 | 24px (1.5) |
| Label / supporting status | 14px | 400 | 20px |
| Heading / named confirmation | 20px | 500 | 28px (1.4) |
| Display / new refusal or overview h1 | 32px | 500 | 40px (1.25) |

Buttons and brief emphasized text use 16px/500/24px; no extra size or weight. Full canonical portfolio names wrap with `min-width:0` and `overflow-wrap:anywhere`. Use plain escaped text, preserve casing/Unicode, and show a name separately from a native select whose option may be clipped. Never shrink a name or consequence copy, use ellipsis as its only presentation, or require hover to identify the target. Descriptions remain optional plain text; empty remains valid. No HTML/Markdown rendering or automatic links in user metadata.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` #F2F2F2 | App canvas and calm space |
| Secondary (30%) | `--card` #FAFAFA; `--popover` #FFFFFF | Existing cards, inputs and neutral controls |
| Accent (10% maximum) | `--primary` #18181B; `--accent` #EEF1FE / `--accent-foreground` #3451D1 | Existing active navigation, Create portfolio, selected control tint and focused navigation/recovery action |
| Destructive | `--destructive` #B83270 | Final Delete portfolio button and deletion trigger text only |

Accent reserved for: active navigation/selected choice, existing Create portfolio or current primary recovery action, and existing blue focus ring. Cancel and overview navigation are neutral secondary controls. The destructive button replaces the primary action within its confirmation section; do not decorate the whole page pink. Warning/unknown uses existing `--warn-soft`/`--warn-text`; refusal uses `--loss-soft`/`--loss-text`; success uses neutral text with an explicit status. Color never carries the only meaning. No new palette, gradient, raw component hex, orange text or new gain/loss semantics. Surface percentages describe visual balance, not literal color allocation to buttons.

## Copywriting Contract

Variable `{name}` means the exact canonical reviewed name rendered as escaped text; `{count}` is authoritative active count. Never interpolate server error detail or display financial data from a closed target.

| Element | Copy |
|---------|------|
| Management section heading | Delete portfolio |
| Collapsed explanation | End this strategy and remove it from your active portfolios. |
| Disclosure trigger | Delete portfolio… |
| Expanded confirmation heading | Delete “{name}”? |
| Confirmation consequence | This ends this strategy permanently. Its committed cash, investments and History will be frozen and unavailable in normal portfolio screens. |
| Future effects | Future dividends, splits and corrections—including unpaid dividends already earned—will not change this portfolio. |
| No liquidation/transfer/undo | Nothing will be sold or moved to another portfolio. Financial records are retained, and you cannot undo this in Birja. |
| Last-known-portfolio addition | This is your last active portfolio. You'll stay signed in and can create a new portfolio when you're ready. |
| Confirm / cancel | Delete portfolio / Cancel |
| Pending | Deleting portfolio… |
| Pending explanation | Checking the deletion of “{name}”. This portfolio is unavailable for new actions while the result is being confirmed. |
| Unknown result heading | Deletion result unconfirmed |
| Unknown result body | We couldn't confirm whether “{name}” was deleted. Check this original deletion request before using this portfolio again. |
| Unknown recovery CTA / pending | Check deletion result / Checking deletion result… |
| Leaving unresolved operation | You can leave this page. Leaving does not cancel the deletion request. |
| Overview recovery notice | A portfolio deletion result is unconfirmed. Review the original request to check its result. |
| Overview recovery link | Review deletion request |
| Another deletion unresolved | Check your original deletion request before deleting another portfolio. Other active portfolios remain available. |
| Recovery storage refusal | Can't preserve this deletion request for recovery. No deletion was sent. Keep this page open and try again. |
| Rename conflict | This portfolio's name changed. Review its latest name before confirming deletion again. |
| Conflict review CTA | Review latest portfolio |
| Confirmed active refusal | Couldn't delete this portfolio. Check its latest details before trying again. |
| Consistency/operational refusal | This portfolio couldn't be safely deleted. Try again later. If this continues, contact the operator. |
| Retry timing | Try again after the displayed wait. |
| Current-owner confirmed success | Portfolio “{name}” deleted. |
| Already-closed original acknowledgement | The original portfolio is already deleted. |
| Stale/private route heading | Portfolio unavailable |
| Stale/private route body | This portfolio is unavailable. Return to Portfolios to choose or create a portfolio. |
| Stale route CTA | Portfolios |
| Earlier unresolved trade notice | An earlier order's result is unconfirmed for this unavailable portfolio. It won't be retried in another portfolio. |
| Unknown identity loading | Checking portfolio access… |
| Access-check failure | Can't check this portfolio right now. Try again. |
| Signed-in empty heading | No portfolios yet |
| Signed-in empty body | Create a portfolio to start an independent strategy with $10,000.00 in virtual cash. |
| Empty primary CTA | Create portfolio |
| Overview count | {count} of 10 active portfolios |

Keep existing funding, naming, description, incomplete valuation and independent return copy elsewhere. No new financial History item labels deletion; there is no visible closed-book statement or archive. Last-portfolio text appears only when latest discovery supports it; correctness does not depend on that advisory count because other tabs can create/delete concurrently. Success is a brief inline polite status on the authoritative overview, not a mandatory toast. A failure/unknown notice persists until resolved and must not be duplicated in alert plus status regions. No generic “Are you sure?” without the name/effect, “Cancel deletion” after sending, “Reset”, “Sell all”, “Recover funds” or physical-erasure promise.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | Existing local Button/Card/Input/Badge; no new block | 2026-11-19: config and copied source inspected; no fetch/install; official vetting not required |
| Third-party | None | 2026-11-19: `components.json.registries` is empty; no third-party block declared, vetting not applicable |

## Placement, Layout and Component Contract

1. Extend the portfolio detail's existing management card adjacent to `PortfolioMetadataForm`, above financial detail content. Add a distinct Delete portfolio section after metadata, separated by 24px and an inherited border. The initially collapsed section has its heading, one-sentence explanation and neutral outlined trigger with destructive text. The trigger opens confirmation; it never sends a mutation.
2. Use one inline confirmation region, semantically a section named by its h2, with full name, three consequence paragraphs and actions in DOM order **Cancel, Delete portfolio**. No modal, overlay, new route, focus trap, typed-name challenge, checkbox or third approval step. Do not use `role=dialog`/`alertdialog` for an ordinary inline region. Trigger exposes `aria-expanded`/`aria-controls`; it is absent or disabled with a visible reason while management metadata is not authoritative.
3. Create/edit and deletion confirmation must not be editable simultaneously for this root. While metadata has a draft, show “Finish or discard your portfolio changes before deleting.” and disable the deletion trigger; do not silently discard description/name edits. Pending/unknown metadata requires its existing latest-details review before entering deletion. On opening deletion capture the latest current canonical name and immutable ID; disable metadata editing until pre-submit Cancel or definitive resolution.
4. The confirmation has full available width, content max 640px, 16px mobile/24px desktop padding; keep the containing layout max 1440px. At 320px buttons stack at full available width; at 375px and above they may share a wrapping row with 8px gap. Labels wrap; controls grow beyond 44px height when text requires it. Do not place the final action inline with an ellipsized name or in a compact overflow menu.
5. Existing `/portfolios` stays outside a selected-financial-target boundary. On confirmed closure revoke the original root, fetch authoritative active membership/overview, then navigate to `/portfolios`; never auto-open a sibling even if exactly one remains. Preserve stable ID ordering and no pooled wealth total. Omit the closed row and revoke its switcher option, cached money, shell cash chip and financial children. A same-name replacement is a new row/ID, never a reused target.
6. Zero active roots use the accepted signed-in empty overview/Create action. Markets, Account and Sign out remain accessible. Browsing, refresh, sign-in/session refresh, Back and returning to the overview do not create/fund a replacement. Explicit Create uses the existing once-only new-identity flow. Failed discovery is an error, not proof of zero.
7. Deletion pending/recovery must live in a metadata-only route/session lease outside the financial Outlet, following the existing metadata lifetime pattern. Revoking root authority must not unmount and lose the unresolved deletion. While submitted/unknown, show the named pending/recovery card instead of the financial subtree; keep Portfolios navigation reachable. On overview show one metadata-only recovery notice/link; omit the uncertain root's financial row rather than presenting its cached money as active. Other independently verified roots stay usable.
8. Stale closed detail, holding, trade, receipt, History/cursor and original-event links render the generic Portfolio unavailable boundary with Portfolios action. Do not display the closed name/description recovered only from a stale financial cache, amounts, holding quantities, receipt details or retry buttons. Preserve only the already-approved boolean notice of this session's unresolved earlier order. Missing/foreign and inaccessible closed normal routes use the same private presentation; do not reveal which reason applies. A current authenticated closure receipt is the narrow place for its minimal already-deleted acknowledgement.

## Confirmation, Authority and Recovery Contract

The following are prescriptive browser behavior. The planner must lock the matching exact endpoint/body/status schema with the API owner; proposed research names/codes are not claims of an implemented API.

- Capture original portfolio ID, canonical reviewed name, authenticated owner/session, route lifetime and operation generation before any CSRF/auth/network await. IDs remain canonical strings; names supply review context, never authorization. Final confirmation submits only that exact target/intent. Do not resolve a name or current select again after awaiting.
- Pre-submit Cancel closes the region, sends no DELETE/financial request and restores the same trigger's focus if still current. Browser Back/navigation before submission merely leaves the draft. Neither entering confirmation nor Cancel changes cash, grants, holdings, History, baseline, count or metadata.
- If authoritative metadata/invalidation indicates a rename while confirmation is open, disable final confirmation immediately, retain the reviewed name and show the conflict notice. “Review latest portfolio” fetches this same ID; only a fresh explicit confirmation displaying its latest canonical name can replace the unsubmitted review. A409 confirmation-name conflict has the same behavior. Never silently update the heading and submit under an old click handler. Description-only change does not change identity; a pending metadata operation still blocks deletion until reconciled.
- Persist a strictly validated same-tab owner-bound unresolved marker **before** sending: original ID, reviewed name, versioned closure intent and opaque owner/session/tab binding only. Allow exactly one unresolved deletion per authenticated owner/tab, separate from the existing creation marker; a new deletion cannot overwrite it. Until it resolves, another portfolio's deletion trigger shows the explicit unresolved-request reason, while normal trading, reading and metadata management in independently verified active siblings remain available. Reuse the existing creation-recovery storage discipline, without overwriting the original creation key/payload. No money, holdings, receipts, credentials, tokens or email in browser storage; no attempt names/keys in URLs, logs or cross-tab messages. If safe persistence fails, refuse the send with the storage error. On reload first authenticate the owner, then restore only the same owner's unresolved original; no automatic DELETE or economic action on mount/focus. The marker is context only: it cannot authorize a server action or construct a new target/body. Clear on definitive resolution/logout/owner change; never let a prior session's stale button send as a new one.
- Immediately on submission quarantine this root's browser authority: invalidate/cancel its reads and actionable previews, block new trade/retry/edit/second-delete actions, and mask cached finances. Preserve immutable original unresolved trade payload/key/ID separately. A stale closure/trade handler must recheck the capture at invocation; no Delete plus new-order UI race may retarget an operation. Server transaction order decides whether an already-submitted original fill precedes closure; the client does not guess or manufacture a fill.
- TanStack Query owns API fetching/mutations and bounded error handling. Disable automatic mutation retries and duplicate confirm submissions; an explicit recovery click is required. Abort, cancellation, navigation, timeout, malformed acknowledgement and ambiguous5xx are **unknown**, not success, rollback or cancellation. Retry-After controls the visible wait and recovery action availability; no invented countdown or unbounded retry loop.
- Unknown keeps original intent immutable and financial actions unavailable. **Check deletion result** explicitly replays the same safe original closure operation/intent, which may finish it if it had not committed, or receive minimal owned-already-closed acknowledgement. The copy describes checking the original request, not a new strategy deletion. A refreshed active-list result alone must not erase an outstanding request that may still commit. Do not replace the original name/ID with a new same-name portfolio.
- If recovery definitively refuses due to changed name, require fresh same-ID metadata review and new confirmation; do not automatically reclose under the new label. Other definitive noncommit refusals can restore activity only after the original operation is terminal and fresh owned-active authority is obtained. Retained-lineage corruption uses operational refusal, preserves records, and does not suggest enabling stocks or waiting for a quote.
- An owned already-closed acknowledgement is minimal and contains no financial statement, historical metadata or receipt. Foreign/missing targets remain private unavailable. No normal read/retry endpoint becomes a closed-book recovery backdoor. A success message with escaped captured name appears only if its owner/session/operation and completion destination are still current; otherwise invalidate permitted data quietly and suppress navigation, focus and announcement into newer context.
- Lifecycle invalidation across tabs carries identity-only advisory signals. Revoke the named target before authoritative refetch, including current actions/previews/cursors/receipts/shell values. Do not trust the broadcast as financial or ownership authority; retain focus-refetch fallback when channel unavailable. Clean subscriptions and private recovery on logout. A→B→A, same-owner new session, renamed original and delete/recreate same-name must not revive old captures.
- A known deletion confirmation from one tab makes its sibling tab unavailable at lifecycle invalidation/revalidation; background response timing cannot restore old money. The server/browser cannot retract bytes already delivered before closure; tests assert new displays/actions and late callbacks, not an impossible remote-memory wipe.

## Interaction and Failure State Matrix

| State / transition | Required rendering, action and focus |
|--------------------|--------------------------------------|
| Metadata loading/error | No actionable deletion; labeled loading/error with same-ID Retry; do not infer name from a financial cache |
| Active root / collapsed | Named metadata, distinct Delete portfolio section; trigger opens review only |
| Confirmation open | Full reviewed name/effects; Cancel initially focused; Delete final explicit action; ordinary keyboard tab order |
| Cancel before sending | Close review, restore trigger if current, no request or data mutation |
| Last-known active root | Add signed-in/empty destination sentence; same confirmation, no forced replacement |
| Metadata rename in this/another tab | Disable confirm; conflict alert, same-ID latest review; no automatic resubmission or silent target/name replacement |
| Submit | One request; busy status; frozen reviewed metadata; remove financial actions/content; no Cancel implying cancellation |
| Unknown/aborted/network/5xx | Persistent warning and Check deletion result; original target retained; navigation allowed, economic intent not discarded |
| Recovery pending | Disable duplicate check, show Checking deletion result; preserve original marker and named context |
| Terminal refusal | Inline focused error; latest same-ID authority required before restoring actions or reviewing again; no optimistic removal/success |
| Consistency refusal / bounded contention | Operational error/server wait; no partial ghost deletion, liquidation or redirect to another portfolio |
| Confirmed closure / original closed replay | Invalidate, authoritative overview, brief permitted acknowledgement; destination h1 focus; no money in acknowledgement |
| Overview request fails after closure | Keep deletion acknowledgement independent from overview error; show Try again; do not fall back to cached closed row or assert zero |
| Delete last then reload/sign-in | Valid empty overview/Create, same signed-in identity; no grant/read-created strategy |
| Delete/recreate same display name | New explicit ID/baseline, original request never touches replacement; old links still unavailable |
| Close market / stale quote / stock held uncertain | Deletion stays available if lineage valid; no price-dependent confirmation totals or quote refresh prerequisite |
| Other active book shares same stock | Its own permitted detail/overview remains independent; no banner claiming its dividends/splits stopped |
| Other-tab close during preview/receipt/History | Revoke old root/read/previews; generic unavailable boundary, optional unresolved-order boolean; no retained amount or retry action |
| Switch/navigation with unknown close | Keep original marker; no late navigation/result on newer target; overview recovery notice can reopen original check |
| Logout/owner/session change | Clear private UI/recovery and revoke captures; ignore old callbacks and stale buttons; no automatic closure under later login |

## Accessibility and Responsive Acceptance

- One h1 per routed surface; deletion section h2 and explicit region naming. Visible text labels, real buttons, trigger expansion semantics and logical DOM order. No visual-only confirmation or pointer-only action. Do not make a whole card clickable around nested buttons.
- Opening confirmation focuses **Cancel**, the safe default. Enter on the disclosure opens only review; focus/Enter on Cancel cancels, not deletes. Delete requires intentional activation of its own button. Escape while unsubmitted may close the review exactly like Cancel; after submission Escape must not erase an unknown intent or imply cancellation. No global Enter shortcut submits deletion from unrelated input or page.
- Pre-submit Cancel restores the original trigger only when still mounted/current. User-initiated submission failure focuses a `tabIndex=-1` linked error/status summary; background metadata invalidation announces once without stealing unrelated focus. If revocation removes the focused financial node, move focus to the available-state heading. On confirmed navigation focus overview h1; never leave focus in an unmounted form or move it after stale-owner results.
- Pending region uses `aria-busy` and one polite status announcement; unknown/refusal uses one concise alert on transition, not repeated polling alerts. Do not read every tick of a Retry-After countdown. Disabled actions have visible associated reasons; focus indicators remain 2px existing ring with 2px offset. Status remains understandable without color or a toast.
- Every action at least 44×44px and 8px apart, including Cancel/check/review/overview links. Preserve 4.5:1 text and 3:1 meaningful-control/focus contrast. Error icons 20px with `shrink-0`/`aria-hidden`; long names and helper copy must not squeeze them to dots. Keep content in ordinary page scroll; no tiny nested warning scrollbox.
- Reflow at 320, 375, 768, 1024, 1280 and 1440px; test longest 60-codepoint Unicode/unbroken/markup-looking names and 1000-codepoint descriptions. Use `min-width:0`, wrapping and content-driven button height. No horizontal page scrolling, clipped consequence text, overlapping controls or obscured focus behind the fixed mobile navigation. Below 768px preserve accepted overview cards and full-width native switcher row; do not reintroduce Phase 13's collapsed-select defect.
- New surfaces use only inherited 120–150ms hover/press, opacity/transform and reduced-motion overrides. No automatic scrolling animation, chart, decorative image or additional font. Viewport permits zoom.
- Execution must obtain **separate actual owner acceptance** for implemented deletion/unknown/stale/empty screens and **genuine desktop browser menu 200% acceptance** for readable/reachable content without overlap/horizontal page overflow. Automated viewport emulation, a planning checker pass or prior Phase 13 acceptance cannot satisfy either new outcome.

## Implemented Evidence and Requirement Coverage

No browser run, screenshot capture, UI implementation or human UAT was performed to create this contract. The following matrix is required future evidence, not passing tests. Unit/hook tests complement actual full-stack isolated browser journeys and real PostgreSQL race/privacy/freeze tests; mocks cannot establish financial atomicity.

| Requirement | Required implemented UI/browser evidence |
|-------------|------------------------------------------|
| PMGT-03 | Named inline review, effects, Cancel no DELETE/no state change, explicit confirm with holdings, repeated original acknowledgement, rename-between-review/commit refusal, loss/reload/retry original ID |
| PMGT-04 | Confirm copy accurately describes terminal freeze/no liquidation/no transfer/no undo; post-close normal screens/History/receipt lack retained finances; later events create no public closed History row |
| PMGT-05 | Actual deletion of last via public API/UI, authoritative empty overview, login/refresh/Back remain zero, explicit new creation only/new ID/one grant |
| PFIN-05 | Synthetic same-stock active sibling remains independently usable after closure and successive splits; closed route remains unavailable, no mismatched cached unit/basis values |
| PFIN-06 | Double-click/stale handlers, simultaneous trade/delete and create/delete cap/name race, queued job outcomes consistent with real commit boundary; unknown operation not retargeted to replacement |
| PCTX-03 | Direct stale detail/holding/trade/receipt/History/original routes, two tabs and same-name replacement; overview offered, no auto-sibling, retained figures or executable retries |
| PSAFE-01 | Foreign/missing/closed normal pages share private refusal; strict error/ack parsing, owner/logout/session/callback revocation and guessed IDs/cursors; no financial persistence or arbitrary server error detail |

UI capture matrix must include active collapsed/confirm/cancel, longest-name confirmation, last-book confirmation, submitting, transport-unknown and restored unknown, retry waiting, rename conflict, consistency refusal, confirmed overview with sibling, signed-in zero, discovery-error after success, stale unavailable with/without unresolved-order boolean, stock-uncertain delete, and cross-tab deletion during an original trade. Bind captures and route/focus/geometry measurements to the actual reviewed source. Preserve prior accepted packets; don't repurpose Phase13 captures as deletion evidence. Verify source, artifact inventory, no injected active content and current owner-acceptance provenance using the established evidence tooling when extended.

Focused future assertions include keyboard default-focus/Cancel/no accidental submit; recovery persistence failure-before-send; unknown marker surviving refresh without automatic DELETE; original same-ID replay even after same-name replacement; stale same-owner/new-session and foreign-owner callbacks unable to mutate or navigate; all pending/unknown financial caches masked; no duplicate live announcement; minimum target/gap and wrapping at all sizes. Final current-source browser qualification and human/native200 checkpoints remain in execution, alongside unchanged critical coverage, strict security/image and exact successor/retained recovery gates.

## Research Provenance

Read project instructions/adapter/current planning, `14-RESEARCH.md`, Phase13 UI-SPEC/UI-REVIEW/UAT, MASTER, actual component/config/tokens and management/target boundary/switcher/overview/metadata source. No page override directory exists. Earlier intermediate Phase13 UI audit pending language is superseded by its final UAT source association; neither result approves Phase14.

2026-11-19 local ui-ux-pro-max searches:

- `destructive action confirmation --domain ux -n 2`: Confirmation Dialogs (confirm irreversible action) and Confirmation Messages (brief success feedback). An inline explicit review satisfies the semantic guidance without installing a modal.
- `focus management confirmation --domain ux -n 3`: confirmation results fit, z-index result does not address focus and was not used. Narrowed once to `focus visible keyboard navigation --domain ux -n 3`: Keyboard Navigation/Focus States support logical order and visible focus; enhanced fully-unobscured focus is a deliberate project quality target, not falsely labelled an AA criterion.
- `zoom reflow horizontal scrolling --domain ux -n 3`: Horizontal Scroll, Text Reflow and Spacing, Long Token Wrapping directly support fluid height/width and full-name wrapping. Do not hide overflow as a substitute for making content reachable.

Existing source establishes the component APIs; no framework/library documentation lookup was necessary, and no new package/current-version recommendation is made. No design-system search persistence, MASTER regeneration, registry download, provider call, production inspection or commit occurred. Proposed recovery/confirmation transport must be reflected consistently in checked plans; API status/code spelling remains technical planning detail, never a product-policy change.

## Checker Sign-Off

- [x] Dimension 1 Copywriting: PASS
- [x] Dimension 2 Visuals: PASS
- [x] Dimension 3 Color: PASS
- [x] Dimension 4 Typography: PASS
- [x] Dimension 5 Spacing: PASS
- [x] Dimension 6 Registry Safety: PASS

**Approval:** independent planning checker approved all six dimensions; see14-UI-CHECK.md. Implemented owner UI and genuine native200 acceptance remain separate future execution checkpoints.
