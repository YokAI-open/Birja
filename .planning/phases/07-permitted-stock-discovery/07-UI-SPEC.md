---
phase: 7
slug: permitted-stock-discovery
status: approved
shadcn_initialized: true
preset: radix-vega (existing customized source)
created: 2026-11-10
verified: 2026-11-10
---

# Phase 7 — UI Design Contract

> Extend Markets with permitted read-only stock discovery. Existing crypto stays usable independently.

## Design System

| Property | Value |
|----------|-------|
| Tool | Existing shadcn/ui copied source, Tailwind v4; no initialization or new registry blocks |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing Radix-backed Button, Card, Badge; native table/list semantics |
| Icon library | Existing Lucide; 20px UI, 16px inline, decorative icons hidden from accessibility tree |
| Font | Existing self-hosted Inter Variable, tabular figures for prices and ages |
| Source of truth | `design-system/birja/MASTER.md`, `frontend/src/index.css`, current Markets/components |

No page override exists. User approved existing requirements/design system, research and this contract;
no `CONTEXT.md` exists or is inferred. No new package, font, visual system or illustration is required.
Local `shadcn info` from `frontend/` attempted 2026-11-10; registry DNS failed. Configuration and
checked-in component source above are authoritative; no download, downgrade or initialization occurred.

## Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon/text gaps |
| sm | 8px | Inline controls and badge groups |
| stack | 12px | Row detail stacks; mobile section gaps |
| md | 16px | Mobile card padding/gutters; desktop inner stacks |
| control | 20px | Button horizontal padding |
| lg | 24px | Desktop card padding and section gaps |
| xl | 32px | Desktop page gutters/vertical margin |
| 2xl | 40px | Large header spacing only where existing layout uses it |
| 3xl | 48px | Major section breaks if required |

Exceptions: 44px minimum interactive hit area; 52px minimum table row height, expanding for wrapped
details; these are existing component dimensions. The inherited 12/20/40px tokens are explicit project-scale exceptions to the
generic GSD checker scale, approved by the user’s choice to preserve MASTER.md.
No new spacing scale. Keep card/control/pill radii
24px/14px/9999px and existing shadows. Informational text is full contrast, not disabled-button opacity.

## Typography

Exactly four font sizes in this discovery surface; two weights, 400 and 500. Existing app-shell
typography remains unchanged. Use `font-medium` rather than adding a third weight to stock symbols.

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Body / price / section heading | 15px | 400 body; 500 price/heading | 22px |
| Label / source / status / metadata | 13px | 400 detail; 500 labels | 18px |
| Heading, below 768px | 32px | 500 | 36px |
| Heading, 768px and above | 40px | 500 | 44px |

Page title tracking −0.02em; other tracking normal. Symbols and prices are prominent through weight
and alignment, without extra typography sizes. No all-caps paragraphs; preserve canonical tickers.

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `--background` #F2F2F2 | Existing page canvas |
| Secondary (30%) | `--card` #FAFAFA; `--secondary` #FFFFFF | Cards and secondary controls |
| Accent (up to 10%) | `--accent` #EEF1FE, `--data-blue-text` #3451D1 | Row hover, explanatory links and focus ring |
| Primary action | `--primary` #18181B | Existing crypto actions only; stock recovery uses secondary buttons |
| State | Existing gain/warn/loss soft backgrounds and matching `*-text` tokens | Fresh, delayed and invalid/unavailable states with explicit text |
| Destructive | Existing `--destructive` #B83270 | No destructive action in this phase |

Components reference tokens, never raw hex. Accent reserved for the listed elements, not stock
company names or decorative panels. “Market closed” is neutral, not an error; “Market open” does not
imply executable. Keep normal text `--foreground` and supporting text `--muted-foreground` (AA).

## Layout and Component Inventory

- Keep `/markets`, current shell/navigation/cash balance, and page title “Markets”. No new nav item.
- Use two vertically stacked labelled sections: “Crypto” then “US stocks · 20”. Both are present on
  the same page without tabs, filters, search, charts or pagination; each has independent state.
- Keep existing crypto prices, age summary, fees and Trade links. Rename the existing page-wide
  oldest-age summary to “Oldest crypto price …” and place it in the crypto section; stocks must
  not make all markets appear stale/closed. Preserve all fifteen existing crypto entries.
- Page uses fluid width with existing shell gutters, up to `max-w-6xl`; no fixed minimum width.
  Cards use existing Card/CardContent. Crypto may retain its current contained table scroller.
- Stock header includes a visible shared `StockAttribution` component: “IEX prices” plus the always
  visible explanation below. Put “Stock trading coming later” directly below, even while open.
- At ≥1024px use a semantic table labelled “US stocks”: Stock (symbol/company/listing exchange),
  Bid, Ask, Quote time, Session and Status. Right-align USD sides; left-align text. Stable instrument
  IDs are row keys; names wrap. Do not confuse listing NYSE/Nasdaq with quote venue IEX.
- Below 1024px use a semantic list of stacked stock records: symbol/company/listing at top;
  labelled Bid/Ask definition list next; timestamp/freshness, session and eligibility below.
  Keep exactly one representation exposed at each breakpoint; no hidden duplicate focus targets.
- Include all twenty curated metadata records even if a quote is absent. Source quotes are nullable;
  display “Unavailable”, never $0, an invented midpoint, a previous-session quote labelled fresh,
  or a substituted consolidated/delayed feed. Use existing string-money formatter, no float math.
- No stock Trade/Buy/Sell controls, stock detail links or links into legacy `/trade/:symbol`.
  Stock records are informational, not clickable. Only crypto records retain executable links.
- Reuse Badge and freshness patterns; add focused stock state/source components only where needed.
  `StockAttribution` has tests for listing, preview and valuation contexts, but actual future trade
  and portfolio screens are outside Phase 7. Required provider attribution supplements this baseline
  once verified; disagreement is an activation blocker, never a reason to omit required wording.

## State and Time Contract

Render three independent facts: regular-session calendar, source quote freshness and execution
capability. Server response owns session/eligibility; browser clock never authorizes trading.

| State | Required rendering |
|-------|--------------------|
| Permission unverified/expired/revoked | Show catalogue and disabled notice; no provider quotes, cached numbers, source timestamps or action payloads. Purge denied stock query data and reject late responses from the former admission state. Crypto remains available. |
| Initial stock request pending | Skeletons matching stock record layout; one `role=status`, “Loading stocks”; do not block crypto. |
| Permitted but no accepted quote | Preserve row, Bid/Ask “Unavailable”, “Waiting for an IEX quote.” No fake age. |
| Valid current-session quote, age <120s | “Recent · {age}”; never “Trading enabled”. Retain backend eligibility and phase-disabled reason. |
| Source quote age ≥120s | “Out of date · {age}”; quote is not executable. If server provides a later stale band, use “Stale · {age}” above its documented threshold; no new eligibility interval. |
| Previous-session quote on reopening | “Previous session · {dated timestamp}”; wait for a current-session source event even if receipt time is new. |
| Closed regular session | Neutral “Market closed”; show next verified open if known. Last permitted quote is labelled “Last quote”, with date and time, not “Closing price” or “Live”. |
| Calendar open, status unknown | “Market open” AND “Stock status unverified”; never infer normal/halt-free from a quote. Trading-coming-later text stays visible. |
| Missing/expired calendar coverage | “Session unavailable”; do not guess open/close or next session. |
| Known halted/frozen status | “Halted” / “Suspended” with server-provided safe reason; no available-for-trading language. |
| Background provider/request failure | Keep only still-permitted last accepted values, labelled dated and refresh-failed; never reset their age. Missing symbols stay visible. |
| Stock API error/malformed response with no usable data | Stock section error and retry; preserve crypto and locally available verified metadata, no provider raw errors. |

Source quote timestamp is always available inline through semantic `<time datetime=UTC>`, showing
date, time and timezone in the viewer's locale (not ambiguous abbreviations alone). For session
boundaries show exchange time explicitly as America/New_York; optional local equivalent must carry
its zone. Server age plus elapsed response time drives relative age, using the existing useNow
pattern; fetched-at is never called quote time. Invalid/future timestamps show unavailable.
At stale admission/calendar deadlines, fail closed locally until a current server response; recompute
known session boundaries to avoid displaying open past the supplied close. Fetch/refocus recovery
uses independent TanStack stock queries, not direct provider calls or useEffect networking.

## Copywriting Contract

| Element | Copy |
|---------|------|
| Feed label | IEX prices |
| Feed explanation | Quotes come from IEX, one US exchange, and may differ from other exchanges. Birja uses virtual money and simulated execution. |
| Stage notice | Stock trading coming later. You can browse prices; crypto trading is available. |
| Primary stock recovery CTA | Retry stock prices (secondary Button; pending: Retrying stock prices…) |
| Permission notice | Stock prices are unavailable while data permissions are being verified. Crypto trading is available. |
| Disabled permission retry | No quote retry button; retry must not bypass permission checks. No provider signup/payment CTA. |
| Empty heading | Stock quotes are not ready |
| Empty body | The stock list is available. Quotes will appear after data access is verified and an IEX update arrives. |
| No accepted quote | Waiting for an IEX quote. |
| Missing/invalid source timestamp | Quote time unavailable. This quote cannot be used for trading. |
| Closed, next session known | Market closed. Next regular session: {date and time, America/New_York}. |
| Closed, next session unknown | Market closed. The next regular session is not yet verified. |
| Calendar/status unknown | Session unavailable. We cannot verify the regular trading session. / Stock status unverified. |
| Source sampling note | IEX quotes are checked about every minute. A check may return an older quote; the time shown is the source quote time. |
| Background refresh failure | Couldn’t refresh stock prices. Showing the last permitted update with its original time. |
| Initial error | Can’t load stock prices right now. Retry stock prices or continue with crypto. |
| Outdated quote | This quote is out of date. Waiting for a recent IEX update. |
| Destructive confirmation | Not applicable: discovery has no destructive or money-changing action. |

## Accessibility and Responsive Acceptance

- Verify 320/375/768/1280px, 200% browser zoom, long company names and long localized timestamps.
  No horizontal document scrolling; stock records wrap within their card. Tables retain associated
  column headers; mobile definitions retain visible labels. No tooltip-only essential information.
- Preserve visible 2px focus ring + 2px offset, keyboard order and focus across background refresh.
  Retry uses ≥44px hit area and ≥8px clearance. No focusable disabled pseudo-links or clickable rows.
- One contextual polite status region announces meaningful stock loading/error/state transitions,
  not twenty competing live regions or second-by-second ages. Status text never relies on color.
- Stock skeletons reserve space; no pulsing dots or forced motion. Existing short hover transitions
  respect reduced motion; no price flashes, gradients, remote logos or new animation dependency.
- Test stock failure/denial/revocation while crypto renders and its Trade link still works; prove
  twenty stable stock identities and no stock Trade links. Assert age 119.999/120, previous-session,
  closed/early-close/DST/unknown states via deterministic server fixtures and browser clock controls.

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | Existing checked-in Button/Card/Badge only; no downloaded blocks | No new registry entry; existing source read 2026-11-10 |
| Third-party | None; `components.json` registries is empty | Not applicable, verified 2026-11-10 |

## Evidence and Defaults

Approved requirements/roadmap supply the catalogue count, IEX attribution, freshness, permission
boundary, staged execution and crypto independence. Research supplies separate stock queries,
source-age and session/unknown rules. MASTER/source supply tokens, shell and components. Section
layout, exact copy, four-size/two-weight subset and mobile records are conservative defaults using
that system, not new user decisions. Local UI/UX searches verified contextual live updates,
React async-error feedback and semantic shadcn table structure; no framework API change is required.

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending independent checker
