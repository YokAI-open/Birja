# Birja Design System (MASTER)

Global source of truth for how Birja looks. Page files in `pages/<page>.md`, if any, override this file for that page only.

**Visual direction:** The approved Markets layout sets the style for Birja. Use warm paper surfaces, dark ink, restrained fox red, and Inter. Give prices and balances room to breathe. Use rules to separate rows and reserve panels for related controls or figures.

**Mode:** light only in v1. Dark mode goes in the backlog: it doubles visual QA and isn't needed for the MVP.

---

## 1. Principles

1. Give prices, balances, and the next available action the strongest hierarchy.
2. Use warm neutrals for surfaces, fox red for focus, and green, red, or amber for outcomes and states.
3. Pair state colors with text or symbols. Show the source time where pricing decisions depend on it.
4. Use spacing and rules to group information. Keep forms focused and aligned to their related preview.
5. Show labels and controls when they help someone understand or act. Make the item’s name the link when it opens the item. Omit placeholders for optional descriptions left blank.

---

## 2. Color tokens

Define these as CSS variables in `src/index.css` and map them in Tailwind v4 `@theme`. They follow shadcn/ui's token names so its components pick them up. **Components never use raw hex.**

| Role | Token | Value |
|---|---|---|
| Canvas | `--background` | `#FAF9F6` |
| Panel | `--card` | `#FDFCF9` |
| Primary text and actions | `--foreground`, `--primary` | `#201F1D` |
| Secondary text | `--muted-foreground` | `#625E53` |
| Quiet fill and hover | `--muted`, `--accent` | `#F0EBE4`, `#F2EDE7` |
| Divider and input border | `--border`, `--input` | `#DEDAD0`, `#9D988C` |
| Focus and brand accent | `--ring`, `--brand` | `#A52317` |
| Links and allocation fill | `--link`, `--data-fill` | `#853428`, `#776D5F` |
| Gain and fresh price text | `--gain-text` | `#2E7A2E` |
| Loss, stale price, and destructive action | `--loss-text`, `--destructive` | `#9C3025` |
| Warning and delayed price text | `--warn-text` | `#8F5200` |

Use the corresponding `*-soft` fill for badges or inline state notices.

---

## 3. Typography

**Family:** [Inter](https://fonts.google.com/specimen/Inter) (variable, with the optical-size axis). Large sizes automatically get the tighter "Display" cut, which matches the reference's numbers. One family keeps the bundle small. Self-host it via `@fontsource-variable/inter` rather than loading it from Google at runtime.

```css
--font-sans: "Inter Variable", ui-sans-serif, system-ui, sans-serif;
font-optical-sizing: auto;
```

**All numbers use tabular figures** (`font-variant-numeric: tabular-nums;`, Tailwind `tabular-nums`), so prices and balances don't jitter as they refresh and columns line up.

| Role | Size / line-height | Weight | Tracking | Example |
|---|---|---|---|---|
| Display value | 32–52px, depending on width | 600 | tight | Position value |
| Page title | 30px mobile, up to 44px desktop | 600 | tight | Trade BTC |
| Section title | 24px | 600 | normal | Holdings |
| Body and control text | 16px | 400–600 | normal | Search, form options |
| Supporting labels | 13–14px | 400–500 | normal | Column headers, source time |

- **Money formatting:** done in the UI only, from server strings. Use `Intl.NumberFormat` with `currency: "USD"`. Show cash amounts (balances, totals, fees, P/L) to 2 decimals. Show unit prices to 2 decimals when ≥ $1 and to 4 significant digits below $1 (e.g. `$0.1287`, `$0.5821`), so cheap coins don't look frozen. Show coin quantities with up to 8 decimals, trimming trailing zeros (minimum 2 shown). Never use JS `number` arithmetic on money; use `decimal.js` if the UI must compute.
- Gains get a `+` prefix; losses use a real minus sign (`−`, U+2212), not a hyphen.

---

## 4. Spacing, radius, elevation

Use a 4px spacing scale. Use 16px page gutters on phones and up to 32px on desktop. Shared page layouts use `app-page` for a 1280px maximum and responsive vertical margins. Major page headings use `app-heading`.

- Panels use 20px padding on phones, 28px on wider screens, a single border, and a 14px radius.
- Separate major groups with 24–40px. Rows get more vertical room on wider screens.
- Primary buttons are at least 48px tall. Shared inputs are 52px tall with a visible label.

---

## 5. Layout

- **App shell:** a top bar, no sidebar, following the reference. v1 has only a few pages, so a sidebar would be empty weight.
  - Left: the fox logo on desktop or the compact fox icon on phones, beside the
    "Birja" wordmark. Brand originals and browser-sized copies live in
    `frontend/public/brand/`. The compact icon also serves as the favicon.
  - Place **Markets · Portfolios · History** beside the logo and wordmark in
    the same row. Use a dark pill for the active destination and keep all three
    labels visible on phones.
  - Right: a door icon with a 44px target. It focuses the sign-in form for
    signed-out users and signs out from the current page for signed-in users.
- **Page heading:** retain a semantic heading. Visually hide repeated titles on Markets, Portfolios, and History when the header already identifies the destination. Use visible headings for focused tasks and detail pages.
- **Portfolio switching:** use a single labelled dropdown. Selecting a portfolio opens it.
- **Responsive layout:** use columns for separate tasks or sections on wide screens. Stack them in reading order on phones. Use a ruled list for narrow tables, with values and labels that can wrap.
- Breakpoints: 375, 768, 1024, 1440.

---

## 6. Components

All built from shadcn/ui source in `src/components/ui/` and restyled with the tokens above.

### Card
`--card` background, `--radius-card` and a single border. Use an `h2` for named sections.

### Buttons
| Variant | Look |
|---|---|
| Primary | `--primary` fill, white text, pill, at least 48px tall, 20px horizontal padding. One per view: Confirm buy/sell, Get code, Sign in |
| Secondary | White fill, 1px `--border`, `--foreground` text, pill |
| Ghost | Text only, `--muted` fill on hover |
| Icon | 40×40 (44×44 hit area) circle, white, 1px border, 20px Lucide icon, `aria-label` required |
| Buy / Sell toggle | Segmented control on `--muted`. The selected segment is white with `--shadow-pop`. Text is "Buy" / "Sell"; no green/red buttons |

States: hover darkens the fill by about 6% over 150ms. Active scales to 0.98. The focus ring is 2px `--ring` with a 2px offset, and is never removed. Disabled is 40% opacity with `cursor: not-allowed`, plus a text reason nearby.

### Inputs
White fill, 1px `--input`, `--radius-control`, 52px tall, 16px text (prevents iOS zoom). The label is always visible above the field. Errors appear below the field in `--loss-text` with an icon. Money and quantity inputs use `inputmode="decimal"` and tabular numbers, with a right-aligned unit suffix (`USD`, `BTC`). The one-time-code field uses `autocomplete="one-time-code"` and paste support.

### Change badge (P/L)
A pill with a soft tint and the text color, containing an arrow icon, sign and value. Example: `▲ +4.21%` uses `--gain-soft` and `--gain-text`; `▼ −1.08%` uses `--loss-soft` and `--loss-text`. Zero is neutral: `--muted` with `--muted-foreground` and no arrow.

### Price freshness badge
Every price shows a small dot + label + relative age. The full timestamp is in a tooltip and `title`.

| State | Dot | Label | Behavior |
|---|---|---|---|
| Fresh (≤120s) | `--gain` | `Live · 42s ago` | normal |
| Aging (120s – max age) | `--warn` | `Delayed · 2m ago` | amber text `--warn-text` |
| Stale (> max age) | `--loss` | `Stale · 7m ago` | Trade button disabled, with the inline message "Prices are out of date, so trading is paused. We'll resume automatically." |

The dot does not pulse. Ages update every second client-side from `as_of`, and the age is announced politely (`aria-live="polite"`) only on state changes, not every second.

### Allocation / progress bar
Uses the reference's "Gross Volume" bars: an 8px tall bar on a `--muted` track, with `--radius-bar` ends. The fill is solid; the **diagonal hatch** is reserved for previews and projected values (e.g. "after this trade"):

```css
background: repeating-linear-gradient(135deg, var(--data-fill) 0 2px, transparent 2px 6px);
```

Above each bar: the label on the left (`body`, muted) and the value on the right (`body-strong`, tabular).

### Tables (holdings, history, markets)
Rows sit directly on the card, with no zebra striping. 1px `--border` dividers, 52px rows, `--accent` tint on hover. The header is `label` style, in muted color. Number columns are right-aligned and tabular. The coin cell shows a 24px coin icon, symbol (`body-strong`) and name (`caption`, muted). On mobile, rows become stacked cards with the key value on the right.

### Trade preview
A card section with a definition list:
```
Market price          $67,412.30
Execution price       $67,479.71   (incl. 0.10% spread)
Fee                   $0.10        (0.10%)
Quantity              0.00148044 BTC
────────────────────────────────
Total cash change     −$100.00
```
The total row uses `body-strong` at 17px. If the price changed, swap the whole block with a 150ms crossfade and show an inline `--warn-soft` notice: "Price updated. Please review again."

### Portfolio value
Use a warm neutral panel with dark, large tabular figures. Show cash and allocation nearby. Incomplete values and the reason for their unavailability stay readable in the same layout.

### Feedback
Toasts appear at the bottom-center on mobile and the top-right on desktop, styled white with `--shadow-pop`, and auto-dismiss after 4s, except errors. A successful trade shows the fill summary. Loading uses skeletons in `--muted` with the same shapes as the content, never spinners for full cards. Every list has an empty state: one sentence plus a primary action, e.g. "No holdings yet. Buy your first coin."

### Icons
[Lucide](https://lucide.dev) (shadcn default), 1.75px stroke, 20px in UI and 16px inline. No emoji as icons. Coin logos are local SVGs for the curated list only.

---

## 7. Data visualization (v1 + later)

v1 has no charts. The value-over-time chart is v2. When charts arrive:

- Bars use solid `--data-fill` for the focused or current period. Comparison or other periods use the hatched fill. This follows the reference's funnel chart.
- Lines use a 2px step or smooth line in `--data-fill`. Gain/loss coloring applies only to the final delta badge, never to the line itself.
- Dot-matrix mini charts, like the reference's "Transactions" widget, suit activity counts such as trades per day.
- Tooltips use the white pill/popover style with `--shadow-pop`. Every chart has a text equivalent (summary sentence or table) for screen readers.
- The axis and grid use `--muted-foreground` at 12px with hairline gridlines in `--border`, and only a few ticks.

---

## 8. Motion

Subtle, functional, and quick.

| Interaction | Duration | Easing |
|---|---|---|
| Hover / press | 120–150ms | `ease-out` |
| Popover / menu / toast enter | 180ms (exit 120ms) | `cubic-bezier(0.2, 0, 0, 1)` |
| Preview update crossfade | 150ms | `ease-out` |
| Price value change | 600ms background flash in `--gain-soft` / `--loss-soft`, then fade | `ease-out` |

- Animate only `opacity` and `transform`. Don't animate width or height, and don't add scroll-reveal or GSAP for v1.
- Under `prefers-reduced-motion: reduce`, disable the price flash and crossfades and show the final state instantly.

---

## 9. Accessibility checklist

- [ ] Text contrast is ≥4.5:1 (all `*-text` tokens and `--muted-foreground` pass on `--card` and `--background`). Non-text UI is ≥3:1.
- [ ] Gain/loss and freshness never rely on color alone: they always have a sign, arrow or label.
- [ ] Focus ring is visible on every interactive element, and keyboard order follows the visual order.
- [ ] Touch targets are ≥44×44px with ≥8px between them.
- [ ] Icon-only buttons have an `aria-label`. Decorative icons have `aria-hidden="true"`.
- [ ] Body text is ≥15px, never below 12px. Inputs are 16px.
- [ ] Layout works at 375, 768, 1024 and 1440px with no horizontal page scroll.
- [ ] `prefers-reduced-motion` is respected.
- [ ] Form errors appear next to the field and are announced (`aria-describedby`, `aria-invalid`).

---

## 10. Anti-patterns (don't)

- The reference's very light grey labels (`#C8C8C8`). They fail contrast.
- Green "Buy" and red "Sell" buttons. This is a learning tool, so buy and sell are neutral choices. Color is for outcomes, not actions.
- Decorative gradients and gradient text.
- Raw hex or arbitrary Tailwind colors (`text-[#123456]`, `bg-green-500`) in components. Use tokens.
- Proportional (non-tabular) figures for any number that updates.
- Spinners for whole cards, or layout shift when prices arrive. Reserve space with skeletons.
- Dark mode, glassmorphism, neumorphism or glow effects in v1.
- Emoji as icons.

---

## 11. Page map

| Page | Layout |
|---|---|
| **Sign in** | A centered email or code form below the shared brand header. |
| **Markets** | A searchable list and selected-asset detail. See `pages/markets.md`. |
| **Portfolios** | Roomy cards with a prominent portfolio name, total value, cash, and return. The whole card is a single link labelled by the portfolio name. Use one column on phones and two on wider screens. Keep the name and figures close enough to scan together. Label the last card “New portfolio”. Show capacity only when it blocks creation. Detailed valuation belongs in the opened portfolio. |
| **Portfolio** | Put the portfolio selector, Edit, Remove, Update and freshness in one toolbar. The overview card shows total value, profit or loss, and cash, crypto and stock allocation. Use holding cards with asset-class filtering and sorting. Show asset name, position value, quantity, return and the Trade action on the card. Open deletion review from the toolbar. |
| **Crypto and stock trade** | The order form and its pricing information on the left, preview or receipt on the right. Stacked in that order on phones. |
| **History** | A chronological list of expandable event cards. Show the event, symbol, time, and cash change first. Keep the portfolio selector and Update together. Open a card for full trade or corporate-action details and original-event links. |
| **System status** | A single panel at `/health`, available when signed in. |
| **Deletion recovery** | A focused single-column view for reviewing the original request. |
