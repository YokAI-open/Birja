# Birja Design System (MASTER)

Global source of truth for how Birja looks. Page files in `pages/<page>.md`, if any, override this file for that page only.

**Inspiration:** [Outcrowd, "Dashboard for payment and business analytics" (Dribbble)](https://dribbble.com/shots/26446179-Dashboard-for-payment-and-business-analytics). Colors below were sampled from that shot, then adjusted to meet WCAG AA contrast where the original fails. The original's light-grey labels are about 1.6:1 against the background, far below the 4.5:1 minimum.

**Style:** Bento Box Grid + Data-Dense Dashboard. Calm, light, Swiss-neutral surfaces; big confident numbers; color used only for data and state.

**Mode:** light only in v1. Dark mode goes in the backlog: it doubles visual QA and isn't needed for the MVP.

---

## 1. Principles

1. **Numbers are the hero.** Portfolio value, P/L and prices are the largest things on screen. Labels are small and quiet.
2. **Neutral chrome, colored data.** Backgrounds, cards and navigation are greys and near-black. Blue, green, rose and amber appear only for data, state or the single primary action.
3. **Never color alone.** Gains and losses always carry a sign (`+`/`−`) and an arrow icon as well as a color. Price freshness always has a text label.
4. **Honest about time.** Every price shows its "as of" age. Stale prices look stale, and trading on them is visibly disabled.
5. **Soft, not fuzzy.** Large radii and very light shadows. No neumorphism, glows or glassmorphism on data.

---

## 2. Color tokens

Define these as CSS variables in `src/index.css` and map them in Tailwind v4 `@theme`. They follow shadcn/ui's token names so its components pick them up. **Components never use raw hex.**

### Neutrals and surfaces

| Token | Hex | Use | Contrast notes |
|---|---|---|---|
| `--background` | `#F2F2F2` | App canvas behind cards | — |
| `--card` | `#FAFAFA` | Card / widget surface | — |
| `--card-foreground` | `#111113` | Text on cards | 18.1:1 on card |
| `--popover` | `#FFFFFF` | Popovers, menus, tooltips, inputs, chips | — |
| `--foreground` | `#111113` | Default text, headings, big numbers | 16.9:1 on background |
| `--muted` | `#EDEDED` | Subtle fills: progress tracks, skeletons, segmented control background | — |
| `--muted-foreground` | `#6B6B70` | Labels, captions, secondary values | 5.1:1 on card, 4.7:1 on background |
| `--border` | `#E6E6E6` | Card outlines, dividers, table rows | decorative |
| `--input` | `#E0E0E0` | Input borders | paired with focus ring |
| `--ring` | `#3451D1` | Focus ring (2px, 2px offset) | 6.2:1 on card |

### Brand and actions

| Token | Hex | Use |
|---|---|---|
| `--primary` | `#18181B` | Primary buttons, active nav pill (the black pill in the reference) |
| `--primary-foreground` | `#FFFFFF` | Text on primary (18.9:1) |
| `--secondary` | `#FFFFFF` | Secondary buttons and icon buttons: white, 1px `--border` |
| `--secondary-foreground` | `#111113` | Text on secondary |
| `--accent` | `#EEF1FE` | Hover/selected tint for rows, menu items |
| `--accent-foreground` | `#3451D1` | Text/icons on accent tint |
| `--brand` | `#F07A1A` | Logo mark only (2.7:1 — never for text) |

### Data and state

Each data color comes as a **fill** for bars, dots and icons (3:1 minimum against the card) and a **text** variant for numbers and labels (4.5:1 minimum).

| Meaning | Fill token | Fill hex | Text token | Text hex | Text on card |
|---|---|---|---|---|---|
| Info / neutral data / links | `--data-blue` | `#4A6BF0` | `--data-blue-text` | `#3451D1` | 6.2:1 |
| Gain / positive / fresh price | `--gain` | `#56A342` | `--gain-text` | `#2E7A2E` | 5.1:1 |
| Loss / negative / stale price | `--loss` | `#D64C87` | `--loss-text` | `#B83270` | 5.4:1 |
| Warning / aging price | `--warn` | `#F5A524` | `--warn-text` | `#8F5200` | 6.0:1 |
| Destructive actions (shadcn) | `--destructive` | `#B83270` | — | — | same as loss text |

- Gains are **green** and losses are **rose/pink**, as in the reference, not a pure red. Rose stays distinct from green for most color-blind users, and the sign plus arrow carry the meaning anyway.
- Soft tints for badges: `--gain-soft #EAF5E7`, `--loss-soft #FBEAF2`, `--warn-soft #FEF4E2`, `--data-blue-soft #EEF1FE`. Use the matching `*-text` color on top.

### Highlight gradient (one per page, max)

The reference's "Insights" card uses a rich gradient. Use it **once per page at most**, for a highlight card such as the portfolio's total P/L summary. Never put it behind tables or forms.

```css
--highlight-gradient:
  radial-gradient(120% 90% at 85% 10%, #F0A36B 0%, transparent 55%),
  radial-gradient(90% 80% at 100% 60%, #EADEAC 0%, transparent 60%),
  linear-gradient(160deg, #3A4FC4 0%, #212C69 70%);
```

Text on it is always `#FFFFFF`, placed over the navy area (12.9:1 on `#212C69`). Keep text in the lower-left, where the gradient is darkest.

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
| `display` | 56/60 (40/44 on mobile) | 500 | -0.03em | Portfolio value `$12,431.07` |
| `h1` page title | 40/44 (32/36 mobile) | 500 | -0.02em | "Portfolio" |
| `kpi` | 32/36 | 500 | -0.02em | Card headline number |
| `h2` card title | 20/28 | 600 | -0.01em | "Holdings" |
| `body` | 15/22 | 400 | 0 | Default UI text |
| `body-strong` | 15/22 | 500 | 0 | Values in rows, button text |
| `label` | 13/18 | 500 | 0 | Column headers, field labels (muted) |
| `caption` | 12/16 | 400 | 0 | "as of 14:02:31", helper text (never below 12px) |

- Use the light-grey "faded value" style from the reference only on decorative or comparison numbers, and only with `--muted-foreground`. The original's #C8C8C8 is not used.
- **Money formatting:** done in the UI only, from server strings. Use `Intl.NumberFormat` with `currency: "USD"`. Show cash amounts (balances, totals, fees, P/L) to 2 decimals. Show unit prices to 2 decimals when ≥ $1 and to 4 significant digits below $1 (e.g. `$0.1287`, `$0.5821`), so cheap coins don't look frozen. Show coin quantities with up to 8 decimals, trimming trailing zeros (minimum 2 shown). Never use JS `number` arithmetic on money; use `decimal.js` if the UI must compute.
- Gains get a `+` prefix; losses use a real minus sign (`−`, U+2212), not a hyphen.

---

## 4. Spacing, radius, elevation

**Spacing scale (4px base, dashboard density):** 4, 8, 12, 16, 20, 24, 32, 40, 48.

| Context | Value |
|---|---|
| Card padding | 24px desktop, 16px mobile |
| Gap between cards (bento grid) | 16px desktop, 12px mobile |
| Page side gutter | 32px desktop, 16px mobile |
| Row height (tables) | 52px (≥44px touch target) |
| Stack inside a card | 12–16px |

**Radius:**

| Token | Value | Use |
|---|---|---|
| `--radius-card` | 24px | Cards, highlight card, app frame |
| `--radius-control` | 14px | Inputs, segmented controls, dropdown triggers |
| `--radius-pill` | 9999px | Buttons, nav pills, badges, chips, icon buttons |
| `--radius-bar` | 6px | Bar/progress ends |

**Elevation:** almost flat. Cards are separated from the canvas by a tone step (`#F2F2F2` → `#FAFAFA`) plus a hairline.

```css
--shadow-card: 0 1px 0 rgba(255,255,255,0.9) inset, 0 0 0 1px var(--border), 0 1px 2px rgba(17,17,19,0.04);
--shadow-pop:  0 0 0 1px var(--border), 0 8px 24px rgba(17,17,19,0.08);   /* tooltips, menus, chips */
--shadow-pill: 0 1px 2px rgba(17,17,19,0.12), 0 4px 10px rgba(17,17,19,0.10); /* active nav pill */
```

---

## 5. Layout

- **App shell:** a top bar, no sidebar, following the reference. v1 has only a few pages, so a sidebar would be empty weight.
  - Left: logo mark (`--brand` square) + "Birja" wordmark.
  - Center: pill nav with **Markets · Portfolio · History**. The active item uses the `--primary` black pill with `--shadow-pill`; inactive items are text-only, with a `--muted` fill on hover.
  - Right: cash balance chip (`Cash $8,214.55`), then an account icon button with a sign-out menu.
  - Below 768px the center nav becomes a bottom tab bar (3 items, icon + label, 56px tall plus safe area).
- **Page header:** large `h1` on the left. Page-level controls go on the right as white pill/segmented controls, like "Daily ▾" in the reference.
- **Bento grid:** 12 columns, 16px gap, max content width 1440px, centered. Cards span 4, 6, 8 or 12 columns. Everything collapses to 1 column below 768px and 2 columns from 768 to 1023px. No horizontal page scroll at 375px. Wide tables scroll inside their card.
- Breakpoints: 375, 768, 1024, 1440.

---

## 6. Components

All built from shadcn/ui source in `src/components/ui/` and restyled with the tokens above.

### Card
`--card` background, `--radius-card`, `--shadow-card`, 24px padding. The header row has the `h2` title on the left and an optional 40px round icon button (`⋯` or info) on the right, with a white fill and 1px border, as in the reference.

### Buttons
| Variant | Look |
|---|---|
| Primary | `--primary` fill, white text, pill, 44px tall, 20px horizontal padding. One per view: Confirm buy/sell, Get code, Sign in |
| Secondary | White fill, 1px `--border`, `--foreground` text, pill |
| Ghost | Text only, `--muted` fill on hover |
| Icon | 40×40 (44×44 hit area) circle, white, 1px border, 20px Lucide icon, `aria-label` required |
| Buy / Sell toggle | Segmented control on `--muted`. The selected segment is white with `--shadow-pop`. Text is "Buy" / "Sell"; no green/red buttons |

States: hover darkens the fill by about 6% over 150ms. Active scales to 0.98. The focus ring is 2px `--ring` with a 2px offset, and is never removed. Disabled is 40% opacity with `cursor: not-allowed`, plus a text reason nearby.

### Inputs
White fill, 1px `--input`, `--radius-control`, 48px tall, 16px text (prevents iOS zoom). The label is always visible above the field. Errors appear below the field in `--loss-text` with an icon. Money and quantity inputs use `inputmode="decimal"` and tabular numbers, with a right-aligned unit suffix (`USD`, `BTC`). The OTP input has 6 boxes, `autocomplete="one-time-code"` and paste support.

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
background: repeating-linear-gradient(135deg, var(--data-blue) 0 2px, transparent 2px 6px);
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

### Highlight card
Uses `--highlight-gradient`, `--radius-card` and white text, with a large `display` number and a one-sentence plain-language explanation. Example: "Your portfolio is up 4.2% since you started." At most one per page.

### Feedback
Toasts appear at the bottom-center on mobile and the top-right on desktop, styled white with `--shadow-pop`, and auto-dismiss after 4s, except errors. A successful trade shows the fill summary. Loading uses skeletons in `--muted` with the same shapes as the content, never spinners for full cards. Every list has an empty state: one sentence plus a primary action, e.g. "No holdings yet. Buy your first coin."

### Icons
[Lucide](https://lucide.dev) (shadcn default), 1.75px stroke, 20px in UI and 16px inline. No emoji as icons. Coin logos are local SVGs for the curated list only.

---

## 7. Data visualization (v1 + later)

v1 has no charts. The value-over-time chart is v2. When charts arrive:

- Bars use solid `--data-blue` for the focused or current period. Comparison or other periods use the hatched fill. This follows the reference's funnel chart.
- Lines use a 2px step or smooth line in `--data-blue`. Gain/loss coloring applies only to the final delta badge, never to the line itself.
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
- More than one highlight-gradient card per page, or gradient text.
- Raw hex or arbitrary Tailwind colors (`text-[#123456]`, `bg-green-500`) in components. Use tokens.
- Proportional (non-tabular) figures for any number that updates.
- Spinners for whole cards, or layout shift when prices arrive. Reserve space with skeletons.
- Dark mode, glassmorphism, neumorphism or glow effects in v1.
- Emoji as icons.

---

## 11. Page map (v1)

| Page | Bento layout (desktop) |
|---|---|
| **Login** | Centered single card (max 420px) on `--background`: email step, then a 6-box code step. Logo above. |
| **Markets** | Header "Markets" with the oldest price age on the right. One 12-col card holding the coin table: coin, price, freshness badge, Trade button. |
| **Trade** (`/trade/:symbol`) | 7-col card for the coin's price, freshness and Buy/Sell form. 5-col card for the trade preview and Confirm. After success, the preview card becomes a fill summary. |
| **Portfolio** | Row 1: 8-col highlight card (total value + total P/L), 4-col card (cash + allocation bars). Row 2: 12-col holdings table. |
| **History** | 12-col card with the trade table and "Load more" (keyset pagination). |

---

*Created 2026-10-20 from the Outcrowd reference and the ui-ux-pro-max database (Bento Box Grid + Data-Dense Dashboard styles). Its suggested dark-OLED style and Fira fonts were rejected because they don't match the reference.*
