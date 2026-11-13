# Phase 10 — UI Review

**Audited:** 2026-11-13, independent initial audit and final re-audit at48d970c
**Baseline:** approved `10-UI-SPEC.md` / `10-UI-CHECK.md`, `10-CONTRACTS.md` C05a/C06 and `design-system/birja/MASTER.md`
**Screenshots:** fresh final Plan17 actual Chromium captures independently visually inspected. The coordinator executed the browser run; this auditor inspected its source, logs and captures without starting another run.

## Pillar Scores

| Pillar | Score | Key finding |
|--------|-------|-------------|
| Copywriting | 4/4 | Applied cash, held proposals, dates and immutable originals are explained accurately. |
| Visuals | 4/4 | Equivalent desktop table/mobile cards preserve the financial hierarchy and long content. |
| Color | 4/4 | Neutral surfaces dominate; state colors distinguish posted changes from neutral holds. |
| Typography | 4/4 | Cash headlines now have the contracted500 weight; declared sizes/weights retained. |
| Spacing | 4/4 | All four undeclared12px gaps replaced with declared16px gaps. |
| Experience Design | 4/4 | Guarded native focus scrolling keeps final completion visible; real five-width regression passes. |

**Overall: 24/24.** Zero active product findings; all three initial warnings are resolved with source/evidence below. Owner acceptance of the new UI and genuine native200% zoom remain pending, separately from these scores. This score records the inspected technical/visual contract, not human acceptance or blanket accessibility certification.

## Initial Top 3 Findings — All Resolved

The initial independent review scored21/24 (4/4/4/3/3/3). Its actual Plan16 images are preserved under `/tmp/birja-phase10-ui-review-before-focus17/`, with ZIP `/tmp/birja-phase10-ui-review-before-focus17.zip`, SHA256 `482f3ec3f763d273416cfe8ec80a8dd6f94c0e6624a3c5d7812a46a4eb409862`. These are historical evidence, not the current capture paths.

1. **RESOLVED WARNING UX-01 — Completion focus was offscreen.** The initial paired viewport/full captures showed middle rows despite completion receiving focus. Parent treated this required-contract gap as blocking readiness. Behavioral REDdb19cf5 confirmed completion bottom3616 exceeded900px viewport (`/tmp/birja-phase09-browser-nnh4g3e4/browser-dividends.log`). GREEN48d970c changes only final completion to `node.focus()` at `HistoryPage.tsx:293`, after unchanged owner/epoch/append-intent/active-element guards. The fresh `history-all-loaded-viewport.png` now visibly contains the focused message. `dividends-history.spec.ts:43–56,263–285` checks full target viewport/fixed-navigation bounds, retry visibility and final append at320/375/768/1024/1440. Retained append/retry focus protections remain; no background/auth focus expansion.
2. **RESOLVED WARNING TY-01 — Cash values used400 rather than500.** GREEN48d970c adds `font-medium` at `HistoryEventDetails.tsx:53`. Fresh mixed/held/original captures show the restored cash/no-cash emphasis without changing financial values.
3. **RESOLVED WARNING SP-01 — Four new12px gaps exceeded the approved subset.** GREEN48d970c replaces all four `gap-3` occurrences with `gap-4` at `HistoryPage.tsx:145,169,243,260`. The new16px spacing is declared in Phase10; the global MASTER12px allowance was not used to waive the original drift.

No remaining priority fixes or minor recommendations identified in this re-audit; no replacement findings invented to fill the template.

## Detailed Findings

### Copywriting (4/4)

PASS: `HistoryEventDetails.tsx:28–55,69–82,129–185` preserves named event kinds, exact tiny rates, calendar-date labels, gross-income explanation, separate applied/proposed amounts and both fixed held reasons. Inspected original, unaffordable, uncertain and reconciled captures confirm proposals never replace `No cash changed`. `HistoryPage.tsx:134–176,261–308` matches the contract's empty/error/retry/count/completion copy. Stock attribution is retained at `HistoryEventDetails.tsx:108–125`; no financial retry/payment action appears.

### Visuals (4/4)

PASS: `HistoryPage.tsx:181–253` exposes the five-column table at1024px and above and labelled ordered cards below it; asset row headers and explicit Stock/Crypto labels remain. Inspected1440/1024/375/320 captures show wrapped saved names/references, right-aligned desktop cash and distinct original-detail enclosure. Native-looking secondary original/back controls remain44px high. Large row heights result from contract-required visible financial details, not clipping or missing hierarchy. No duplicate visible responsive layout or invented assets found.

### Color (4/4)

PASS: changed renderers contain no raw hex/RGB colors. There are two gain/loss text-token branches (`HistoryEventDetails.tsx:53`), one held warning text use (`:163`), one refresh-warning surface (`HistoryPage.tsx:145`) and one restrained row-hover accent (`:214`), plus focus-ring tokens. The screenshots remain predominantly neutral canvas/card surfaces; no decorative accent proliferation. Gain/loss signs and explicit no-cash text carry meaning without color. The60/30/10 contract is respected qualitatively; no exact pixel-area measurement is claimed.

### Typography (4/4)

PASS after TY-01 closure. Declared content sizes are13/15/32/40px; content uses400/500, with `font-medium` now on cash headlines. Page headings use32/36 mobile and40/44 desktop (`HistoryPage.tsx:108–110`); event details use13/18 (`HistoryEventDetails.tsx:101`). Semantic timestamps retain seconds, zone and UTC accessible text (`:11–24`). Financial displays remain tabular and string-safe (`money.ts:1–38`); tiny rates remain visible rather than rounded to zero. No extra font family or600 content weight introduced.

### Spacing (4/4)

PASS after SP-01 closure. Main new padding/gaps use8/16/32px; table rows have52px minimum with wrapping growth (`HistoryPage.tsx:214`). Existing component card geometry is preserved. Page bottom padding and scroll margins are96px (`:108,214,241,282`), and fresh mobile original/back captures clear the fixed navigation. Actual browser assertions cover320/375/768/1024/1440 overflow and original/back/final focus bounds. No undeclared12px gap remains on these changed surfaces.

### Experience Design (4/4)

PASS after UX-01 closure. Reviewed the actual RED failure, minimal guarded source correction and fresh visible completion capture; the regression now measures rectangle bounds rather than accepting focus ownership alone. Native scrolling uses existing scroll margin and does not remove the guards that prevent stealing focus after background/auth changes.

PASS: loading/empty/initial-error/retained-refresh-error/append-error states remain covered. Safe accepted rows remain after read failure; pagination is explicitly bounded and guards overlapping fetches (`HistoryPage.tsx:82–105,258–308`). Inline offpage originals focus their heading and return to the initiating control without scanning History (`HistoryEventDetails.tsx:191–238`). The hook scopes data to owner/session epoch, removes previous-owner pages and rejects late responses (`useEventHistory.ts:17–25,45–72,97–101`); new events invalidate authoritative cash/portfolio rather than summing local income (`:80–95`). The exact parser rejects malformed money/date/type/lineage/cursor input (`eventHistory.ts:63–334`). Relevant tests cover native-disabled blur, retry focus, non-stealing focus, logout originals, malformed refresh retention and same-owner relogin. Coordinator's fresh targeted browser1pass40.2s,29component/page4.15s, fullfrontend697/36files16.42s (98.37%statements/94.82%branches), full static/build and fullbrowser49pass evidence support closure; this auditor did not rerun tests.

## Evidence and Acceptance Limits

- Personally inspected fresh Plan17 viewport PNGs: mixed1440/375, original, held unaffordable/uncertain, loading, empty, initial error, append/refresh error and end. End now shows a visible full focus ring around `All events loaded.`; current desktop/mobile cash weight and spacing changes are visible. Initial audit additionally inspected1024/320. Current captures live in `/tmp/birja-phase10-ui-review/images/`; initial captures are preserved only in the historical directory above.
- Attribution: fresh final Plan17 full run `/tmp/birja-phase09-browser-5bjhfgb1/browser-all.log`, runner `/tmp/birja-phase10-17-browser-all-final.log`,49passed/one expected deployed-CSP skip/317.3s. Source48d970c;385before/after/current sources unchanged in `/tmp/birja-phase10-17-browser-source-receipt.json`. This supersedes Plan16 capture reuse for the current packet.
- Independently checked107current UI/support source hashes,385current source hashes and capture/current equality,49review-file hashes, ZIP SHA and50-entry CRC: no mismatch. ZIP `/tmp/birja-phase10-ui-review.zip`,15,497,014bytes, SHA256 `cf4e4817bdae885c2feea4c5fe9e6368ef834394a83f618e6bddddaa5fb9845d`. Tracked manifest binds48exact exports as well.
- The16HTML pages preserve actual rendered DOM/CSS/local fonts. Exported controls do not execute; the screenshots/exports support presentation review, while source and prior real browser journeys support interactions. Actual financial effects used real services/SQL; synthetic long labels and tied read-only timestamps remain presentation fixtures, not provider/financial mutation claims.
- No Playwright MCP available. Dev-server probes at3000/5173/8080 found none; no server/stack/install started. Screenshot storage gate was inspected: `.planning/ui-reviews/.gitignore` is absent. No screenshot was captured or copied into the repository; existing evidence remains under`/tmp`, outside git. A future repository capture must create the prescribed ignore gate first. This audit's only write is this report.
- **needs_human_review: true:** new Dividend/correction/held UI acceptance and genuine native200% browser zoom remain Plan18 owner checks. Root-font enlargement/deviceScale/CSS zoom are not native zoom. Earlier Phase9 approval does not accept Phase10. No live-provider, deployed-CSP, publication or deployment acceptance inferred.

## Registry Safety

Registry audit:0third-party blocks checked, no flags. `frontend/components.json` has an empty registry map; the UI-SPEC lists only existing official copied components. No registry fetch, install or network source execution was warranted.

## Files Audited

- `frontend/src/pages/HistoryPage.tsx` and `.test.tsx`
- `frontend/src/components/HistoryEventDetails.tsx` and `.test.tsx`
- `frontend/src/hooks/useEventHistory.ts` and `.test.tsx`
- `frontend/src/api/eventHistory.ts` and `.test.ts`
- `frontend/src/lib/money.ts` and `.test.ts`
- `frontend/e2e/dividends-history.spec.ts`, `frontend/components.json`
- `design-system/birja/MASTER.md`; Phase10 UI-SPEC/UI-CHECK,17PLAN, C05a/C06,14–16SUMMARIES, BROWSER, HUMAN-UAT, UI-SOURCE-HASHES and LOCAL-PROOF; shared project/workflow instructions.
