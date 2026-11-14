---
phase: 11
slug: mixed-asset-recovery-and-acceptance
status: approved
reviewed_at: 2026-11-13T17:07:59Z
shadcn_initialized: true
preset: radix-vega (existing customized source)
created: 2026-11-13
---

# Phase 11 — UI Design Contract

> Verification contract for the existing accepted mixed-asset interface. No new product design, screen or control is required. Writing this contract proves neither execution nor current acceptance gates.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing shadcn/ui copied source and Tailwind v4; preserve initialization |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing Button/Input/Card/Badge; native forms, tables, lists and definition lists |
| Icon library | Existing Lucide, 20px controls/16px inline; decorative icons hidden |
| Font | Existing self-hosted Inter Variable; tabular financial figures |
| Canonical sources | `design-system/birja/MASTER.md`, `frontend/src/index.css`, accepted source `48d970c`, Phase7–10 UI contracts and Phase10 HUMAN-UAT |

The shadcn gate is satisfied by the checked-in initialized config and established customized components. Preserve the existing preset; no CLI download, initialization, registry acquisition, package installation or reconfirmation is needed. No page override exists. No Phase11 CONTEXT exists; do not invent discussion decisions. Approved requirements and the owner's instruction to derive a verification contract from accepted screens supply scope. Phase9/10 integrated behavior supersedes earlier Phase7/8 staged “coming later” rules where already implemented; this does not activate live data or trading.

Focused ui-ux-pro-max search on2026-11-13: `focus not obscured --domain ux` returned the Web minimum/enhanced focus-obscuration guidance. Apply it to fixed mobile navigation and History completion focus; do not claim blanket AAA conformance. No new framework API is proposed, so no library documentation or dependency lookup is required.

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Existing icon/label gaps |
| sm | 8px | Controls and metadata clearance |
| md | 16px | Mobile gutters/card padding and History detail groups |
| lg | 24px | Desktop card padding and section separation |
| xl | 32px | Desktop gutters and page spacing |
| 2xl | 48px | Inherited major separation where used |
| 3xl | 64px | Reserved template token; no new spacing requirement |

Preserve the master’s existing12/20/40px component spacing where present; all are multiples of four. This table is a verification subset, not an instruction to restyle accepted UI. Keep24px cards,14px controls, pill radii and existing shadows. Rows have minimum52px height and grow for content; inputs remain48px tall; targets are at least44×44px with8px clearance. Never clip a financial string, warning, company name or reference to maintain height.

## Typography

Four content sizes and two content weights,400/500, inherited from approved Phase9/10 surfaces:

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body, values, card headings, buttons | 15px | 400 body;500 values/headings | 22px |
| Metadata, source, reasons, timestamps | 13px | 400 detail;500 labels | 18px |
| Mobile page heading/headline | 32px | 500 | 36px |
| Page heading/headline at≥768px | 40px | 500 | 44px |

Preserve inherited16px input text as the already accepted control accessibility exception. Preserve surrounding shell/crypto/master typography rather than forcing this subset globally. Page headings retain−0.02em tracking. Financial values use tabular figures; text wraps without ellipsis. No added weights, tiny metadata or typography reset.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` #F2F2F2 | App canvas |
| Secondary (30%) | `--card` #FAFAFA; `--secondary` #FFFFFF | Cards, secondary controls |
| Accent (up to10%) | `--accent` #EEF1FE; `--data-blue-text`/`--ring` #3451D1 | Existing hover/selection, explanatory/original links and focus |
| Primary | `--primary` #18181B / white | Confirm and established primary actions; active navigation |
| Warning | `--warn-soft` #FEF4E2 / `--warn-text` #8F5200 | Held, uncertain, repriced and retained-page error notices |
| Gain/loss | Existing gain/loss text and soft tokens | Signed actual financial outcomes/freshness with text |
| Destructive | `--destructive` #B83270 | Existing validation/error emphasis; no new destructive action |

Accent is reserved for the listed existing elements, not all controls or asset-class decoration. Components use token classes, never new raw hex. Preserve neutral Buy/Sell controls and the single existing Portfolio highlight maximum. Held proposals must not look posted; closed states remain neutral. Status and gain/loss meaning use words/signs as well as color. MASTER remains authoritative for contrast and existing data-blue allocation bars.

## Scope and Component Inventory

Keep Markets / Portfolio / History navigation, the one shared cash chip, existing stock/crypto routes and authentication lifecycle. Reuse `StockSection`, `StockAttribution`, `StockActionState`, `StockTradePage`, `StockTradeReceipt`, `PortfolioPage`, `PortfolioHoldings`, `PortfolioAllocation`, `HistoryPage`, `HistoryEventDetails`, exact money helpers and existing query/parser/owner-epoch guards.

Focal anchors remain the ticket's server preview/confirmation, the persisted receipt, Portfolio's complete or explicitly incomplete value, and each History event's actual cash effect or explicit no-cash state. Preserve their hierarchy. There is no recovery dashboard, restore button, rollout approval, admin correction/payment control, reset, new filter/chart/export, new route or reconciliation feature in Phase11. Operator recovery evidence belongs in planning/verification artifacts, not the investing UI.

## Interaction and State Preservation

| Surface/state | Required observable behavior |
|---------------|------------------------------|
| Discovery | Exactly20 stock identities alongside15 crypto; visible IEX/simulation attribution. Bid/ask, actual source time, session, stock status and corporate-action state remain independent. Crypto remains usable during stock denial/failure. |
| Open stock trade | Positive whole shares only; Buy max/Sell all populate drafts only. Buy uses eligible ask, sell eligible bid; zero commission/added spread and immediate virtual proceeds remain disclosed. Server preview precedes explicit Confirm buy/sell. |
| Repricing | Retain labelled previous/new execution price and cash change/difference; require renewed review and another confirmation. No silent automatic fill. |
| Closed/stale/unknown/hold | Explicit refusal with saved editable draft; no queued order or unsafe executable preview. Source age≥120s fails closed. Fresh quotes alone cannot clear unknown status or an action hold. Rights/action deadlines remove unauthorized numeric values. |
| Uncertain submitted outcome | Freeze the original payload/key; Check order result resolves the same attempt even after closure/hold. A timeout is not proof of no fill. No second economic attempt while unresolved. |
| Persisted receipt | Original fill price/source time, shares, signed cash effect, reference and historical after-trade balances remain immutable on replay, including after a split/rename/later trade. Portfolio/Trade again preserve established behavior. |
| Combined Portfolio | One shared cash balance/original starting amount; labelled alphabetic stock/crypto holdings and explicit basis/cost/value. Eligible stock marks use server midpoint. Closed/halted retained marks carry actual dates and labels. |
| Incomplete valuation | Known value: {USD} — incomplete with unvalued count; unsafe values, overall P/L and allocations unavailable. No hidden holdings, zero replacement, normalized partial allocation or browser-computed total. |
| Dividend and correction | Original gross ordinary USD credit remains immutable; applied correction shows its actual delta and original reference. Held uncertain/unaffordable correction shows No cash changed and applied0 separately from any verified proposal. Later resolution is a linked separate event. |
| Forward split | Visible verified new:old ratio, effective time, before/after shares and unchanged total basis; No cash changed. No guessed cash-in-lieu or rewriting original fills. |
| Mixed History | Preserve server newest-recorded-first order including ties, stable kind+ID identity, event-specific detail and private owner-scoped original lineage. An offpage original opens inline without loading unbounded pages. Back to correction restores initiating focus. |
| Loading/empty/error/paging | Skeletons distinguish initial loading from empty. Refresh/append errors retain only valid current-owner rows and offer scoped read retries. Guard concurrent fetches; preserve append position and completion focus; All events loaded remains reachable above mobile nav. |
| Auth/late responses | Clear former-owner financial data and drop delayed obsolete results. A denied/restricted/older response cannot restore removed prices or cash/history from another session. No direct provider requests or authority decisions in the browser. |

Financial facts come from validated exact server strings; preserve established string-safe formatting, USD cash two decimals, signed deltas, exact small dividend rates and whole-share versus crypto quantity distinctions. No Number/parseFloat money arithmetic, local entitlement multiplication, optimistic cash credit or summing History into current cash. Dividend cash appears once through the server account balance. Instants show local dated time and zone with semantic `<time dateTime>`; date-only dividend terms retain their calendar date, with payable New York convention labelled. Never fabricate absent source dates or label dividends/splits as quote prices.

## Copywriting Contract

Preserve accepted fixed domain copy and source mappings. Representative exact strings below are verification anchors; they do not authorize replacing other accepted messages.

| Element | Copy |
|---------|------|
| Primary trade CTA | Confirm buy / Confirm sell |
| Uncertain attempt CTA / message | Check order result / We couldn't confirm the result. Check this order before placing another. |
| Closed draft | Market closed. You can edit a draft; no order is queued. |
| Unknown status | Stock status is unverified. New orders are unavailable. |
| Stale quote | This quote is out of date. A fresh eligible quote is required before trading. |
| Action hold | Suspended for corporate-action review. |
| Corporate-action persistence | Corporate-action review is still required. A price update does not clear it. |
| Receipt heading | Order filled |
| Incomplete headline | Known value: {USD} — incomplete |
| Portfolio empty heading/body | No holdings yet / Explore Markets to buy your first stock or crypto. |
| History primary / refresh | Load more / Refresh history |
| History empty heading | No activity yet |
| History empty body / CTA | Your trades, dividends, splits and corrections will appear here. Browse markets to make your first trade. / Browse markets |
| Initial History error / retry | Can't load your history right now. Try again. / Try again |
| Refresh error / retry | Couldn't refresh your history. Showing the last successful update. / Retry refresh |
| Append error / retry | Couldn't load more events. Your loaded events are still here. / Try loading more |
| Completion | All events loaded. |
| Dividend explanation | Gross ordinary USD dividend. No tax withholding or automatic reinvestment. |
| Held cash | No cash changed |
| Held insufficient cash | Not enough available cash for this correction. No cash changed. |
| Held uncertainty | The corrected dividend terms need verification. No cash changed. |
| Lineage controls | View original dividend / Back to correction |
| Destructive confirmation | None added. Existing simulated trades retain itemized preview and explicit Confirm action; History is read-only. |

Use validated public reason mappings, never raw provider/operator errors, private evidence or promises of automatic hold resolution. Existing IEX single-venue/simulation, stock fee/proceeds and valuation disclosures remain visible on their established surfaces.

## Responsive and Accessibility Contract

Preserve the current shell and breakpoints. Below768px retain the56px bottom navigation plus safe area; preserve sufficient page bottom padding and scroll margins. Stock listings, holdings and History use their current table at≥1024px and stacked labelled records below; stock ticket/preview stack below1024px. Exactly one layout is exposed to assistive technology. Preserve current fluid container widths rather than replacing them with the master's aspirational maximum.

Use320/375/768/1024/1440px as the existing mixed-history/portfolio verification set, with long saved names/references, large signed amounts, exact tiny rates and local timezone strings. Require no horizontal document overflow, obscuring overlap, clipped financial facts or unreachable controls. Tables have scoped headers; mobile definitions retain labels and logical reading order. Essential timestamps/reasons/cash/proposals remain visible without hover or tooltip.

Preserve2px focus ring/2px offset, visible labels, `aria-describedby`/`aria-invalid` errors, keyboard Buy/Sell/shortcuts/confirm and native button behavior. Receipt and original-detail headings receive intentional action focus; Back to correction returns it. Refresh/append/background polling do not steal focus. Retain the repaired final-page focus behavior and keep focused controls fully visible above navigation as the accepted project requirement. Contextual polite status announces meaningful changes, not every second or polling tick. Preserve reduced-motion behavior; expired financial facts disappear immediately without an animation retaining them.

## Acceptance and Evidence Contract

SAFE-03 acceptance maps the existing isolated real-service browser stories in `stocks.spec.ts`, `stock-actions.spec.ts`, `stock-trades.spec.ts`, `dividends-history.spec.ts` and `portfolio-history.spec.ts` to discovery→preview/reprice→confirmation→receipt→Portfolio/History, open/closed/stale/unknown/hold, split, dividend/correction and crypto coexistence. Follow `11-RESEARCH.md` for final accounting/concurrency/CI gates and evidence gaps. Browser presentation alone is not exact financial or restore proof; do not mock successful financial effects to manufacture acceptance. Synthetic rights/status inputs are not live-provider approval.

Existing human evidence is reusable by scope, not by phase name:

- `10-HUMAN-UAT.md` records the owner's explicit “Reviewed: accept the new UI” and “Checked native 200%: passes” on2026-11-13, bound to source `48d970c262c7f52bb5692d38db0748e5169cf389` and ZIP SHA256 `cf4e4817bdae885c2feea4c5fe9e6368ef834394a83f618e6bddddaa5fb9845d`. Browser/window dimensions were not supplied; do not invent them.
- Read-only comparison during this contract found no diff from48d970c in `frontend/src`, `frontend/components.json` or `design-system/birja`. This is bounded source continuity, not a fresh runtime or final Phase11 acceptance claim. At closeout also assess relevant build/dependency/runtime and server-response behavior changes before reusing evidence. Record the final reviewed source and affected-path assessment.
- Preserve Phase7–9 acceptance for their unchanged discovery/action/ticket/Portfolio scopes; Phase10 evidence covers the new mixed History/correction/held screens. Do not extend a History export’s native-zoom answer to unreviewed surfaces or treat static exported controls as executed interactions.
- If relevant presentation, interaction, financial meaning, layout, build styling or served response behavior materially changes in Phase11, capture and verify the affected states at the final source and obtain scoped renewed owner acceptance. Renew genuine desktop browser-menu200% verification for affected zoom/readability/reachability surfaces. Unchanged surfaces retain prior acceptance; no gratuitous new human checkpoint is required merely for Phase11.
- A smaller viewport, CSS zoom, device scale, screenshot magnification or unverified shortcut remains supplementary reflow evidence, never proof of native browser200%. A newly required human result stays pending until supplied.

Writing this file executes no tests and makes no gate pass claim. Final Phase11 evidence must distinguish historical runs from actual final-source checks, preserve the one existing deployed-CSP W07 skip without expanding it, and state remaining blockers honestly. SAFE-02 exact encrypted recovery/current0014 compatibility and distinct legacy0008 rollback evidence remain separate from UI approval. SAFE-01, provider rights/live activation, production migration/deployment/B2/installed tools/timers, publication and accepted W01–W08 follow-ups remain outside this UI contract.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| Existing shadcn official copied source | Existing Button/Input/Card/Badge only; no new block | 2026-11-13: checked-in config, tokens and existing source references inspected; no new acquisition |
| Third-party registries | None | 2026-11-13: `frontend/components.json` has `registries: {}`; no third-party block declared |

UI safety gate is enabled. No third-party block enters this contract, so registry view/vetting approval is not applicable. Any later proposed registry addition requires its actual applicable gate before inclusion.

## Source and Default Provenance

| Source | Decisions Used |
|--------|----------------|
| REQUIREMENTS / ROADMAP | SAFE-02/03 scope, existing asset/financial semantics, mandatory local acceptance and deferred live boundaries |
| PROJECT / STATE /11-RESEARCH | Reuse accepted evidence, close concrete gaps, retain current0014 versus0008 scope and final-source attribution |
| Phase7–10 UI contracts | Existing discovery, holds, trade/repricing/replay, complete/incomplete Portfolio, mixed History/lineage/error contracts |
| MASTER / current config/CSS/source | Existing tokens, components, fonts, wrapping, focus and initialized registry state |
|10-HUMAN-UAT / accepted48d970c | Explicit owner UI/native200% acceptance and exact source/packet limits |
| CONTEXT | None exists for Phase11; no decisions inferred |
| Current session | Verification-only contract from accepted requirements/screens; no design interview, features, installs, execution or commits |
| Defaults | Evidence mapping and change-triggered scoped recheck structure only; no new visual defaults |

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending checker; prior owner acceptance remains evidence with the source/behavior limits above.
