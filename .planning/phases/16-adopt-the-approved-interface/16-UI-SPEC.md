---
phase: 16
slug: adopt-the-approved-interface
status: approved-direction
created: 2026-11-23
---

# Phase 16 — UI Design Contract

Use Birja's existing design system, self-hosted Inter, supplied brand assets,
neutral warm surface tokens, dark primary actions and established semantic
gain/loss colors. Use existing React, Tailwind, Lucide and copied shadcn
components. `design-system/birja/MASTER.md` defines tokens and page layouts.

| Surface | Essential visible content and actions |
|---|---|
| Header | Fox, Birja, Markets, Portfolios, History and right-aligned door. Keep semantic headings even when hidden visually. Door has a state-specific accessible label and a 44px target. |
| Markets | Search and asset-type switch, a market list, current selection with prices and availability, and a trade action. Show IEX source where stock prices appear. Mobile users can return to the list. |
| Portfolios | Named whole-card links with cash, value and return, and the final New portfolio card. A create or edit form supports an empty description. Explain capacity when it blocks creation. |
| Selected portfolio | One chooser/Edit/Remove/Update toolbar with freshness, performance and three allocation categories, then holding cards with filters and sorting. Keep exact values, unavailable states and explicit deletion confirmation. |
| Trade | Identify the selected portfolio and keep preview, price changes, confirm, receipt, error and original-result recovery as distinct actionable states. |
| History | One chooser and Update, followed by chronological cards. The summary shows event, symbol, time and cash change. Expanding reveals the stored values and original links. Keep pagination and retry reachable. |
| Sign-in | Focused OTP form and icon-only header control. Failed sign-out is visible on the current screen and retry remains available. |

Use spacing and typography from the master document. Keep keyboard focus
visible, announce pending/error results and preserve nonvisual names when
labels are hidden. Check representative signed-in and signed-out routes at
320px, 390px, 768px and 1440px, with enlarged-text reflow and the owner's
desktop zoom check. Load, zero-data, partial valuation, closure, order recovery
and corporate-action refusal retain meaningful text and keyboard actions.


## State copy and navigation

Keep the existing empty, error and recovery copy unless correcting a demonstrated
regression. This includes Markets “No assets match your search” and “Try again”,
“No portfolios yet” with “New portfolio”, History “No activity yet” and “Try
loading more”, and “Couldn't sign out. Try again” with the same sign-out icon.
Trade and deletion retain their explicit recovery actions. Pending, backend
failure and confirmed empty data each have their own state.

Signed-in `/account` URLs redirect to Markets. Signed-in system status is at
`/health`. On narrow Markets screens, returning from asset detail restores focus
to the selected asset. Keep fox accent for selected-market emphasis and the
existing focus treatment. Keep third-party registries empty.
