---
phase: 22-adopt-the-market-workspace
reviewed: 2026-11-26T09:38:34Z
rechecked: 2026-11-26T09:47:02Z
depth: standard
source: 519199143fb8e1ae6793825569c794dab428c96a
initial_source: 463502a
files_reviewed: 7
files_reviewed_list:
  - frontend/src/App.tsx
  - frontend/src/App.test.tsx
  - frontend/src/components/PortfolioSwitcher.tsx
  - frontend/src/components/MarketOpening.tsx
  - frontend/src/pages/MarketsPage.tsx
  - frontend/src/pages/MarketsPage.test.tsx
  - frontend/src/pages/markets.css
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Phase 22 code review

Compared the Phase 22 implementation through `463502a` with the planning
baseline `62f8299`. Traced explicit portfolio selection and the legacy
route through the existing target boundary. Checked selected catalog
identity, retained quote invalidation, market opening projection, and the
affected component tests. The selection state stays with the mounted
signed-in identity, explicit pending or unavailable portfolios suppress
the Markets trade link, and the existing route checks still gate direct
navigation. The countdown is display-only and historical charts remain
scheduled for Phase 23.

Rechecked both findings against `b516bac2d795d5978743e5ad4df7907479dadf1e`.
Both are resolved. The executor reported 24 passing Markets component tests,
including focused regression assertions, plus lint and type checking.

## Resolved findings

### WR-01 — Stacked layout and selection focus use the same breakpoint

**Original issue** The stacked layout stopped at `48rem`, while the
selection focus check used `767px`. A larger browser default font could
leave selection focus on the row in a stacked layout.

**Resolution** Selection focus now uses `(width < 48rem)`, complementary
to the CSS grid query, and the component test checks that exact query.
[MarketsPage.tsx](/tmp/birja-v15-market-charts/frontend/src/pages/MarketsPage.tsx:221)

### WR-02 — Focus returns to search when refreshed results remove detail

**Original issue** A catalog refresh could remove the selected detail panel
and the Back to results control while the panel held focus.

**Resolution** The detail ref cleanup records whether the panel held focus.
The next frame restores focus to the search input only once the panel has
been removed and focus is on the document body. The regression test covers
a selected catalog detail being removed by a refetch. [MarketsPage.tsx](/tmp/birja-v15-market-charts/frontend/src/pages/MarketsPage.tsx:66)

The review used static source tracing and the project accessibility
guidance. Browser execution and evidence remain part of Plan 22-03.

## Enlarged-text browser finding

The isolated browser run found header overflow with enlarged text at
375px, 768px, and 1024px. Commit `519199143fb8e1ae6793825569c794dab428c96a`
restores wrapping on both header flex groups and keeps the 44px account
control from shrinking. The reviewed diff is limited to those classes.
The executor reported 67 passing App tests, type checking, and lint.
The final isolated browser run passed all enlarged-text and normal-text
header checks. It finished with 105 passing tests and one expected
production-only skip. [Browser receipt](22-BROWSER-RECEIPT.md)
[App.tsx](/tmp/birja-v15-market-charts/frontend/src/App.tsx:166)
