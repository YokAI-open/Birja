# Phase 22 browser verification receipt

The guarded disposable stack completed all 14 Playwright specs on
2026-11-26. It passed **105 tests** and skipped the optional deployed-site
CSP check. The runner used synthetic data, a console email backend, and an
isolated Compose project. Cleanup verified zero remaining owned containers,
networks and volumes. [Playwright output](/tmp/birja-phase09-browser-bsctkx__/browser-all.log)

## Tested source and checks

- Runtime commit `519199143fb8e1ae6793825569c794dab428c96a`.
- Browser assertions committed as `23b1e5bfc1c5a51a565448e95c79621c26b1c19e`. During the run they
  were present as the exact two-file worktree diff against the runtime
  commit. Its SHA-256 is `e4b791d7c37a31df0ab70f841fafdb02011c37f3549036f25f731d7acc86f392`.
- The full frontend Vitest run passed **1,376 tests in 61 files**. ESLint,
  TypeScript, scoped Prettier and the Vite production build passed.
  The build emitted a bundle-size advisory. [Vitest output](/tmp/birja-phase22-vitest-final.log)
- Browser command `python3 deploy/tests/run-stock-browser.py --suite all`.
  It started at 11:00:59 CET and used the checked-in single-worker runner.

## Requirements exercised

| Requirement | Observed evidence |
|---|---|
| WS-01 | One header row at 320, 390, 640, 768 and 1440px. The existing Portfolio/History cases also fit at 200% enlarged text. The mobile selection and return retained keyboard focus. |
| WS-02 | Twenty original stocks on entry and after clearing search. Name, ticker, alias and class lookup against the synthetic catalog. A failed catalog search preserved curated browsing and crypto. |
| WS-03 | Detail beside the list on desktop and below it on phones. Only the selected listing requested a quote. The same listing and search survived switching portfolios, and the actual ticket opened under the chosen portfolio ID. |
| WS-04 | Fixed holiday and early-close calendar fixtures preserved the last price and exact next opening. The owned catalog path preserved a SQL-backed closed price and refused order preview. Existing stock and crypto trade suites passed. |

The browser checks are in [Markets](../../../frontend/e2e/markets.spec.ts),
[stock catalog](../../../frontend/e2e/stock-catalog.spec.ts),
and [Portfolio and History](../../../frontend/e2e/portfolio-history.spec.ts).

## Screenshots from the verified build

| Capture | SHA-256 |
|---|---|
| [Desktop open market](/tmp/birja-phase22-markets-5191991-m7dt_0k0/markets-desktop-open.png) | `8c54dc1e4d91d77f84165bc016028800c108979703180280f695cd1c5b60aca0` |
| [Desktop holiday closure](/tmp/birja-phase22-markets-5191991-m7dt_0k0/markets-desktop-closed.png) | `8af4069bcceb420e724a3c28498eb66b369fc2e727ba0aef89d062a432725053` |
| [390px selected catalog detail](/tmp/birja-phase22-markets-5191991-m7dt_0k0/markets-mobile-detail.png) | `575fce6c891fc17bd272a6e285c24675866a186070dcc61638782694443eed9b` |

The rendered app follows the approved prototype's compact header, stock tab
and search, split desktop workspace and quote-led detail. The open view has
the selected portfolio and Trade action. The closed view shows its retained
price, countdown and View details action. The mobile image shows the query,
selected result and visible keyboard focus with no horizontal overflow.
Market history and period changes are scheduled for Phase 23. These images
use deterministic test fixtures. Zoom evidence consists of 640px reflow and enlarged CSS text assertions.

## Repairs verified by the rerun

The first run recorded 100 passes, five failures and one expected skip. It
exposed enlarged-text header overflow at 375, 768 and 1024px and two fixture
assumptions. The header now wraps when the larger text needs space. The
early-close fixture supplies a quote whose timestamp agrees with its stale
status, and the owned-portfolio test reloads metadata after creating a
portfolio directly through the API. The final run includes those repairs
and the two focus fixes from review. [Initial browser output](/tmp/birja-phase09-browser-njaxg2qi/browser-all.log) · [Code review](22-REVIEW.md)
