---
phase: 8
slug: corporate-action-safe-ownership
status: approved
reviewed_at: 2026-11-11T09:50:24Z
shadcn_initialized: true
preset: radix-vega (existing customized source)
created: 2026-11-11
---

# Phase 8 — UI Design Contract

> Extend the existing read-only stock discovery surface with honest corporate-action safety states. Corporate-action accounting is backend-owned; this phase adds no stock orders, cash payments or public event History.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing shadcn/ui copied source and Tailwind v4; no initialization |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing Radix-backed Button/Card/Badge; native table/list/definition-list semantics |
| Icon library | Existing Lucide only; 20px UI, 16px inline; decorative icons aria-hidden |
| Font | Self-hosted Inter Variable; tabular figures for numerical content |
| Source of truth | `design-system/birja/MASTER.md`, existing `07-UI-SPEC.md`, actual `StockSection.tsx`, `StockAttribution.tsx`, `useStocks.ts`, `api/stocks.ts`, checked-in tokens/components |

Owner approved research, UI contract and planning using the existing design system. No Phase 8 CONTEXT exists and no discussion D-IDs are inferred. Existing configuration/source confirms initialization; no new preset confirmation is needed. The local shadcn executable is absent; do not download or run a registry CLI to inspect already checked-in components. No new package, registry, font or visual system is required. Exact new copy and projection field names below are planning defaults, not claimed provider facts or additional owner decisions.

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon/text gaps and compact status stacks |
| sm | 8px | Badge-to-reason gaps and interactive clearance |
| stack | 12px | Mobile stock detail groups |
| md | 16px | Mobile padding/gutters and card-content stacks |
| control | 20px | Existing button horizontal padding |
| lg | 24px | Desktop card padding |
| xl | 32px | Desktop page gutters |
| 2xl | 40px | Inherited page-header spacing only |
| 3xl | 48px | Existing major section spacing only |

All values are multiples of four and preserve the master. Existing 12/20/40px tokens are project-scale exceptions to the generic checker scale. Preserve 24px card/14px control/pill radii and existing shadows. Informational status text remains full readable contrast. Rows have minimum height 52px and expand freely for reasons; interactive targets are at least 44×44px. No fixed-height/clipped warning panels.

## Typography

Exactly four sizes and two weights, 400 and 500, in the stock discovery surface. Preserve surrounding shell/crypto typography.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body, price, stock-section heading | 15px | 400 body; 500 prices/headings | 22px |
| Label, source, safety reason, timestamp | 13px | 400 detail; 500 labels | 18px |
| Markets heading below 768px | 32px | 500 | 36px |
| Markets heading at/above 768px | 40px | 500 | 44px |

Only the inherited page heading uses −0.02em tracking. Canonical tickers retain capitals; paragraphs use sentence case. Safety reasons wrap without ellipsis. No smaller tertiary timestamp or extra semibold weight.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` #F2F2F2 | Existing canvas |
| Secondary (30%) | `--card` #FAFAFA; `--secondary` #FFFFFF | Existing cards and secondary retry button |
| Accent (up to 10%) | `--accent` #EEF1FE; `--data-blue-text` #3451D1 | Existing row hover, explanatory links and focus indication |
| Warning | `--warn-soft` #FEF4E2 with `--warn-text` #8F5200 | Monitoring unavailable/reconciling and persistent corporate-action suspension |
| Neutral | `--muted` #EDEDED with `--muted-foreground` #6B6B70 | Market closed, status unverified, no mark |
| Price state | Existing gain/warn/loss text and soft variants | Quote freshness only, independently of action safety |
| Destructive | `--destructive` #B83270 | No destructive UI operation in this phase |

Accent is reserved for the listed elements, never decorative company highlights. Use tokens in components, never raw hex. Black primary buttons remain existing crypto actions. An action-safe state uses neutral text, not a green “safe to trade” badge. No disabled opacity on explanatory text; color always accompanies readable state words.

## Scope and Component Inventory

- Keep `/markets`, top/bottom navigation and existing cash display. Preserve vertically stacked Crypto and US stocks · 20 sections, all fifteen crypto instruments and their working Trade links.
- Extend existing `StockSection` only. Preserve `StockAttribution` and visible “IEX prices”/single-venue/simulation explanation. No new page, navigation item, chart, stock detail link, operator dashboard or event-history list.
- Reuse Card/CardContent, Badge warning/neutral, Button secondary, existing money formatting and semantic timestamps. Add a focused stock action-state renderer if needed to avoid duplicate table/mobile copy.
- Preserve desktop six-column table (Stock, Bid, Ask, Quote time, Session, Status) at ≥1024px. Expand Status into clearly labelled independent lines: “Corporate actions”, “Stock status”, “Trading”. Never add a seventh dense column. Below 1024px preserve the stacked list and labelled definition lists.
- Render every stock identity even when monitoring or price permission fails. Do not hide affected companies or substitute a zero price. Global action-monitor loss can affect all twenty stocks; an issuer-specific event affects only its stock. Neither suppresses crypto.
- No stock Trade/Buy/Sell/Confirm controls or disabled stock trade-link placeholders. Keep `execution_enabled=false` and phase-disabled reason throughout Phase 8. No UI to acknowledge, clear, bypass or manually resolve a hold.
- Reconciliation remains privileged backend CLI with auditable evidence. No browser uploads, operator text fields or links to private evidence. Dividend cash, entitlement detail views and split/payment History belong to later phases.

## Independent State Contract

Quote freshness, regular session, exchange halt/status, action monitoring and persistent action holds are separate facts. “Market open”, “Recent quote”, a successful refresh, or current corporate-action monitoring never means stock trading is enabled or halt status is verified.

| Condition | Corporate-action rendering | Quote/valuation behavior |
|-----------|----------------------------|--------------------------|
| Current monitoring, no unresolved action | “Corporate actions checked.” | Only an independently permitted compatible quote may appear; stock status remains unverified and trading remains coming later |
| Monitoring absent/disabled/expired or source coverage uncertain | “Corporate-action checks unavailable.” plus reason below | Bid/Ask “Unavailable”; “Valuation unavailable”; retain stock identity/session facts only if independently authorized |
| Catch-up in progress | “Checking corporate actions…” | Same unavailable price behavior; do not relabel stale monitoring as current |
| Unsupported/reverse/merger/identity/fractional/disputed event | “Suspended for corporate-action review.” plus fixed reason below | Bid/Ask “Unavailable”; no usable numeric quote, midpoint or quote timestamp; no guessed adjusted mark |
| Verified split applied but compatible quote absent | “Waiting for a post-split quote.” | “Valuation unavailable”; never multiply the old quote by a ratio in the browser |
| Monitoring recovers but unresolved hold remains | Keep suspension and persistent reason | A fresh quote or healthy source must not clear the hold |
| Verified resolution plus compatible fresh quote | Render latest server action state | Browser may display a newly authorized compatible quote from the new response; never revive a cached old-unit value |
| Closed market, action-safe and display rights valid | Keep neutral “Market closed” and separate action state | Dated permitted last quote may display under existing Phase 7 contract; an uncertain action overrides numerical display |
| Quote permission unavailable | Existing permission notice; no provider-derived action detail without its separate permission | Purge quote values/times and denied action-derived facts; local fixed unavailability reason remains |

Phase 8 chooses the conservative projection: unsafe action state suppresses numeric stock quotes, rather than retaining potentially confusing old-unit amounts as historical observations. Do not introduce a second historical-price panel. Existing portfolio stock placeholders remain unavailable; combined totals and their “incomplete” behavior integrate in Phase 9, not new Phase 8 portfolio work.

## Minimal API and Client Safety Contract

Extend the authenticated no-store `/api/v1/stocks` response additively with a small per-stock action availability envelope. Suggested fields are `actions.state` (`current`, `unknown`, `reconciling`, `suspended`), `actions.reason` (fixed enum), `actions.epoch` (monotonic nonnegative safe integer), `actions.checked_at` (UTC or null), `actions.valid_until` (UTC or null), and `valuation_reason` (fixed enum). Expose only the safe decision, not event payloads, ratios, entitlement/user quantities, operator identity, ticket references, evidence URLs or reconciliation notes. Missing/invalid safety envelope cannot default to current.

1. Current quote disclosure requires current relevant product rights, calendar/display deadlines, current action monitoring, no unresolved hold, and quote compatibility with the current action epoch/effective unit boundary. `valid_until` bounds the earliest relevant authority, monitoring lease and known future blocking/effective action boundary. The response must not authorize an old-unit quote beyond a known split instant even if the next poll is delayed. Keep raw action details private; a timestamp bound is sufficient.
2. The server must final-read current action/permission generation and UTC before projection, covering changes committed during the same request. Quote provenance or verified boundary compatibility must be established server-side; the UI never infers it from price change, receipt time or a successful request.
3. Preserve `useStocks` authenticated query isolation, transport timing, no-store and full-round-trip monotonic conservative clock. At `valid_until` equality or later, immediately reduce action state to unknown and purge numeric quote values/timestamps from active view and query cache; do not wait for the 30-second refetch. Also fail closed if the safety fields are missing/malformed. Projection uses source time for price age and never resets it after refresh.
4. Preserve latest per-instrument action epoch within the authenticated cache lifecycle. A delayed response from an older epoch cannot replace a newer split/hold/resolution; cancel or reject it. Preserve existing envelope admission-generation and server-time guards. Equality of action epoch does not permit an older response to undo a later observed suspension or unavailable state.
5. An unknown new event cannot be discovered by a disconnected browser. Known boundaries must expire locally; previously unseen changes become visible only on the next valid server response. Do not claim instantaneous news delivery or use UI expiry as proof of provider completeness. Backend monitoring and future execution guards remain authoritative.
6. Refresh/refocus/network recovery uses existing TanStack Query only; no direct provider calls, ad hoc network effects or localStorage persistence. Browser clocks can remove eligibility, never promote unknown/closed to current/open. Stock execution remains false regardless of action state.

The planner may refine field naming with backend research but must retain epoch ordering, bounded validity, compatible post-action prices and independently sanitized reasons in strict client tests.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Persistent stage notice | Stock trading coming later. You can browse prices; crypto trading is available. |
| Current action state | Corporate actions checked. |
| Unknown action state | Corporate-action checks unavailable. Valuation is unavailable until checks are current. |
| Reconciliation in progress | Checking corporate actions… Valuation is unavailable until checks finish. |
| Persistent hold heading | Suspended for corporate-action review. |
| Unsupported reason | This corporate action needs review before this stock can be valued. |
| Fractional entitlement reason | This action may create fractional shares and needs review. |
| Conflicting/revised event reason | Corporate-action information has changed or conflicts and needs review. |
| Identity-change reason | This stock’s identity is changing and needs review. |
| Source/coverage gap reason | We cannot verify complete corporate-action information for this stock. |
| Post-split mark missing | Waiting for a post-split quote. Valuation is unavailable. |
| Numeric fallback | Unavailable |
| Valuation label | Valuation unavailable |
| Checked timestamp | Corporate actions checked: {dated time and timezone}. |
| Unknown timestamp | Corporate-action check time unavailable. |
| Exchange status | Stock status unverified. |
| Healthy source with unresolved hold | Corporate-action review is still required. A price update does not clear it. |
| Primary recovery CTA | Retry stock prices (existing secondary Button) |
| Pending recovery CTA | Retrying stock prices… |
| Initial loading | Loading stocks |
| Initial error | Can’t load stock prices right now. Retry stock prices or continue with crypto. |
| Background error with retained data | Couldn’t refresh stocks. Only still-permitted, currently verified prices are shown. |
| Empty heading | Stock quotes are not ready |
| Empty body | The stock list is available. Prices appear when data access, corporate-action checks and an IEX quote are verified. |
| No stock catalogue / malformed response | Can’t load stock prices right now. Retry stock prices or continue with crypto. |
| Destructive confirmation | Not applicable: no destructive or money-changing UI action |

Use a fixed reason-enum-to-copy map. Unknown enum values fail validation/unavailable; never interpolate raw provider or operator text. Retry only re-reads the authenticated stock API: it cannot resolve a hold, renew a monitoring lease, import permission or trigger provider collection. Do not show a “Resume trading”/“Resolve” action, payment/sign-up CTA or promise automatic recovery from a persistent dispute.

## Loading, Errors and Recovery

Retain twenty layout-shaped skeletons only during initial stock fetch, one contextual loading status and independent crypto rendering. Existing identities remain stable during background refresh, preserving all current restrictions. An action monitor outage is a data state, not a perpetual request spinner. Expired safety hides numbers even when the last fetch failed. A fresh successful request with no current evidence still renders unavailable.

Keep one stock section retry button for request failure, with pending label and duplicate-click protection. No button is required for an unsupported event or missing product rights. After successful user-initiated retry, preserve existing focus transfer to the stock-section heading; failed retry retains button focus. Background polling never moves focus. No hover-only help, transient toast-only safety explanation or browser alert dialog.

## Accessibility and Responsive Acceptance

- Test 320/375/768/1280px and 200% browser zoom. Below 1024px use single-column stock records; at ≥1024px table rows expand. No horizontal document scroll, overlap, truncated reasons or clipping of long company names/timestamps. Preserve logical DOM reading order and exactly one exposed layout per breakpoint.
- Mobile order: identity; Bid/Ask labels and unavailable/value; quote time if permitted; session; corporate actions/reason/checked time; independent stock status; coming-later notice. Desktop groups the last three facts under Status using explicit text labels. No color-only hold, tooltip-only reason or ambiguous dash for unavailable prices.
- Render timestamps with semantic `<time dateTime=UTC>`, dated local time plus zone; session boundaries explicitly America/New_York. Show no timestamp when unknown/denied. Corporate-action checked time is never called quote time, effective date or provider update time.
- Preserve keyboard order, visible 2px ring with 2px offset and 44px targets with 8px clearance. Records/status badges remain noninteractive. No focus trapping or new tab stops for every warning. Long badges can wrap with `whitespace-normal`, automatic height and no inherited `overflow-hidden` clipping, or use a short badge plus a wrapping paragraph.
- Use one contextual `role=status`/polite atomic announcement for meaningful changes, including affected symbol and reason (for example “AAPL suspended for corporate-action review. Valuation unavailable.”). Aggregate multiple changes rather than twenty competing live regions. Do not announce seconds, unchanged polling cycles or every price tick.
- Skeletons reserve space without pulse; no price flash/gradient/new animation. Existing short hover transitions respect `prefers-reduced-motion`; safety state/number removal is immediate, with no crossfade retaining an expired numeric value.

## Required Verification Stories

1. Exactly 20 stocks plus 15 crypto remain visible; single affected stock gets suspension copy and no price, while unaffected stock values and crypto Trade links remain independently usable. Global monitor loss marks all 20 unavailable without touching crypto.
2. Fresh quote plus open session plus unknown monitoring still means no usable stock value; action-current plus exchange-status-unknown keeps “Stock status unverified” and `execution_enabled=false`.
3. Unsupported/fractional/disputed/identity reasons render safe text and survive repeated healthy quote responses. No event/private evidence or real holdings appear in the API/UI.
4. Clock-controlled expiry at the exact action deadline/known split boundary clears displayed and cached pre-split amounts before refetch, including background-error state. Restore only from a new authorized compatible response. Admission/calendar expiry retains existing stronger suppression.
5. Out-of-order older epoch, later-arriving stale response, logout/login and denied/malformed envelopes cannot restore old prices or clear a hold. Source timestamps and age119.999/120 behavior remain truthful.
6. Post-split waiting state shows no adjusted old price. New compatible quote appears only with current backend evidence; old-unit cached marks never revive. A known unsupported event stays held after reconnect.
7. Keyboard retry success/failure and background updates preserve focus as specified. Screen-reader output has contextual status/reason without per-second announcements. Verify mobile/desktop/zoom/reduced-motion screenshots with long strings and correct accessible table/list semantics.
8. No stock trade controls, reconciliation actions, payment/history records or additional product activation appear. All proofs use isolated synthetic fixtures; they do not pass the owner-deferred Phase 7 live-data gate.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | Existing checked-in Card/Button/Badge only | Source/config inspected 2026-11-11; no registry fetch or new block |
| Third-party | None; `frontend/components.json` registries is empty | Not applicable; verified 2026-11-11 |

## Evidence and Defaults

Sources read: AGENTS/CLAUDE/adapter, PROJECT/REQUIREMENTS/ROADMAP/STATE,08-RESEARCH,07-UI-SPEC, Birja MASTER, `frontend/components.json`, actual StockSection/StockAttribution references, useStocks/api validator and Badge source. The approved scope supplies corporate-action suspension, independent crypto, whole shares and deferred payments/trading. Research supplies monitoring/hold separation, epoch/boundary-compatible prices and private reconciliation. Existing source supplies actual typography, layout, retry/focus and monotonic response timing.

Local UI/UX search 2026-11-11 (`live status screen reader`, ux) returned contextual live badge guidance: one atomic contextual announcement without moving focus. This contract uses that verified match. No new framework API is introduced; existing source is sufficient for component reuse, so no library install/documentation executable was required. Projection field names, safe copy and conservative number suppression are implementation-ready defaults, not new provider permissions. Phase 7 live evidence remains pending/deferred independently.

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending independent checker
