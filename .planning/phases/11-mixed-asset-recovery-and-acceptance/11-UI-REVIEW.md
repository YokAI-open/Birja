# Phase 11 — UI Review

**Audited:** 2026-11-13
**Reviewer:** independent delegated UI auditor `/root/phase11_execute04/ui_review`; separate context from implementation, code/security review and goal verification. This reviewer authored only this report, with no application edits, commits, installations or test reruns.
**Source:** `6be913cf56e8713d8e48a045dfad91644619215d`, compared with accepted `48d970c262c7f52bb5692d38db0748e5169cf389`.
**Baseline:** approved `11-UI-SPEC.md`, independent `11-UI-SPEC-REVIEW.md`, existing MASTER and accepted Phase7–10 scope.
**Screenshots:** no new captures; existing accepted Phase10 desktop/mobile captures inspected. Ports3000/5173/8080 returned000; no server started. No Playwright MCP is exposed. The screenshot-ignore gate was inspected and `.planning/ui-reviews/.gitignore` is absent. No repository capture/copy occurred; existing PNGs remain under `/tmp`. Any future repository capture must first create the prescribed ignore gate. The task expressly excludes new captures and limits writes to this report.

## Verdict

PASS for this verification-only UI continuity contract. No material presentation, interaction, financial-meaning or served-response regression was identified. Reuse the actual scoped owner acceptance; no phase-number-only human checkpoint is needed. This verdict does not establish hosted CI, live provider rights, production readiness or a fresh full serial recovery block at final source.

## Pillar Scores

| Pillar | Score | Specific finding |
|--------|-------|------------------|
| Copywriting |4/4| PASS: applied cash and held proposals remain explicitly distinct; scoped read retries retain their precise labels. |
| Visuals |4/4| PASS: responsive table/cards preserve labelled financial hierarchy, long references and original lineage. |
| Color |4/4| PASS: neutral surfaces dominate; signed cash uses semantic gain/loss and held explanations use warning tokens. |
| Typography |4/4| PASS: History uses the four contracted content sizes and400/500 weights; exact tiny rates remain readable. |
| Spacing |4/4| PASS: accepted16px detail spacing, wrapping52px rows, bottom clearance and focus scroll margins are preserved. |
| Experience Design |4/4| PASS: actual browser proof measures completion focus above navigation, read failure recovery and owner isolation. |

**Overall:24/24.** Scores apply to the approved preservation contract, not a new universal accessibility certification. No unresolved BLOCKER or WARNING was found in this scope; positive findings below justify every score.

## Top 3 Priority Fixes

None required. Three acceptance safeguards to preserve, rather than invented product defects:

1. Keep the exact deployed-CSP W07 skip visible; do not report it as a local pass or expand the exception.
2. Preserve native completion scrolling and the owner/epoch/focus-intent guards together; focus ownership alone does not prove reachability.
3. Reopen scoped owner/native-menu200% verification only after a material relevant UI/build/response change; never substitute CSS enlargement or a smaller viewport.

## Detailed Findings

### Pillar 1: Copywriting (4/4)

PASS: `HistoryPage.tsx:142–176` distinguishes retained refresh failure from empty state and explains actual shared cash. `HistoryEventDetails.tsx:53–55,132,155–176` preserves signed actual cash, gross dividend explanation, **No cash changed**, applied zero and separately labelled verified proposals. `StockTradePage.tsx:19–27,329–337` retains closed editable drafts/no queued order, unverified/stale refusals, Check order result and Confirm buy/sell. No generic action replacement or operator recovery control was introduced. Source strings are unchanged from the accepted baseline.

### Pillar 2: Visuals (4/4)

PASS: `HistoryPage.tsx:15–30,181–241` retains semantic Recorded/Event/Asset/Details/Cash change labels and mutually exclusive table/list layouts at1024px. Existing `mixed-history-375-viewport.png` and `dividend-original-viewport.png` were personally inspected: long names/references wrap, exact rates remain visible, neutral card hierarchy separates metadata from signed cash, and original-return controls remain legible. These are accepted historical captures, not new Phase11 captures. The current browser scenario at `dividends-history.spec.ts:187` independently exercises these unchanged layouts; its passing raw log is verified below.

### Pillar 3: Color (4/4)

PASS: `index.css:15–47,71–101` retains MASTER surfaces and semantic colors; `HistoryEventDetails.tsx:53` combines gain/loss color with signed values and words. `HistoryPage.tsx:145,214` uses warning panels and restrained row hover accents. A focused scan of production `.tsx` files found **zero raw hex/rgb component colors**. No phase frontend/color delta exists. The inspected captures support neutral dominance and restrained accents;60/30/10 is a design distribution, not a claimed pixel histogram. Orange remains the logo mark, not financial text.

### Pillar 4: Typography (4/4)

PASS: focused History class extraction finds exactly `text-[13px]`, `text-[15px]`, `text-[32px]`, `text-[40px]` and explicit `font-normal`/`font-medium`. `HistoryPage.tsx:108–110,201` preserves body/headline/metadata hierarchy. `HistoryEventDetails.tsx:53,64` uses tabular financial figures. `index.css:68,117–129` retains self-hosted Inter,15/22 body and2px focus outline/offset. Inherited16px inputs and surrounding shell typography are approved contract exceptions, not findings to restyle. No ellipsis or rounding-to-zero defect was found in the inspected tiny-rate/long-reference evidence.

### Pillar 5: Spacing (4/4)

PASS: `HistoryPage.tsx:108,214,241,282` preserves16px gaps/padding,52px minimum growing rows and96px scroll clearance; `App.tsx:144` adds safe-area-aware page padding and focus margins. `dividends-history.spec.ts:43–55,226–284` checks full focused rectangles against viewport and fixed navigation, plus document overflow at320/375/768/1024/1440. The actual passing scenario proves more than presence of utility classes. Accepted MASTER component geometry and four-pixel-multiple exceptions remain unchanged; no arbitrary new spacing was added.

### Pillar 6: Experience Design (4/4)

PASS: `HistoryPage.tsx:48–105,282–294` retains append intent, matching owner/epoch and active-element checks, with native `node.focus()` scrolling only at intentional completion. Read retries, loading, empty, retained rows and inline original-return behavior remain intact. `HistoryEventDetails.tsx:195–236` preserves expanded/original semantics and Back to correction. Browser proof includes actual ask/bid fills, repricing/reconfirmation, lost-response original-key resolution after close, incomplete Portfolio, held/corrected dividends, crypto coexistence and late former-owner response denial. Successful financial effects use actual services; synthetic long labels, permissions/status inputs and read-error interception do not prove live provider authority or economic mutations. Existing accepted W01–W08 follow-ups are neither newly fixed nor erased by this review.

## Source, Build, Runtime and Served-Response Continuity

Direct `git diff 48d970c` found no changes in the entire frontend (including lock/config/build recipe/e2e), design system, backend application/Alembic/build recipe, nginx or development Compose. Backend `pyproject.toml` is unchanged. The sole backend lock delta is approved transitive `opentelemetry-api1.45.1→1.45.2` with pinned replacement artifacts. It is not silently treated as unchanged runtime: patched full API/accounting/browser, native/runtime, ordinary-dev and image evidence is required and present.

Independently recomputed **235 relevant UI/build/response source hashes** against the final receipt: zero mismatches. Verified raw frontend host and fixed-toolchain build-log hashes; both emit `index-Clv1h4rZ.css` and `index-D9-pSJqf.js` with the same font assets. Verified native/package inventory artifact hash; it records approved inventory parity, UID1001 native History/dividend checks and oversized traceparent refusal. Node image remains `sha256:f2e7cc228ec174d5df1bca0e61050f39b8c3685aa36095459df1b28583971feb`; patched runtime is `sha256:2c91676c9d4408bb7ab7458a6dfef353157aef44dca18a77a9a60fe97dbfb80b`. No material UI or financial-response effect was identified. This is a bounded source/evidence assessment, not a byte-for-byte comparison of every possible HTTP response.

Verified private receipt hashes:

| Evidence | SHA256 |
|----------|--------|
| `/tmp/birja-phase11-gates/task1-receipt.json` |`a9ae4672b48c9d848ab8b9e613b59f8d327c99246d89eb68915e8a2aa90608d9`|
| `/tmp/birja-phase11-gates/final-receipt.json` |`bb90d570e6b2313f7b1fd3fc5d53cf2a6ebe558831b7f0e57a4760d16255f5af`|
| `/tmp/birja-phase11-04-offline/receipt.json` |`d6c27240f771c0234b0e9ff6fc6d595908559792da97b8dec6503fcdfb6233c4`|
| Actual complete browser raw log `/tmp/birja-phase09-browser-lyd7v9za/browser-all.log` |`76104b254578985b75e2e8446692eba1d1eb2fc4d513af7e9d6a681fb9adc697`|

Raw browser evidence confirms49passes/326.1s and exactly one skip: `csp.spec.ts:12`, deployed site CSP with absent `E2E_PROD_URL`. It explicitly prints `native_browser_zoom_200pct=false`; CSS root enlargement and reflow-equivalent cases remain supplementary. Task1 at `f970d90` records2557backend passes,47critical modules100%,697frontend passes and patched runtime/image/dev checks. Current relevant bytes match; later harness changes do not convert that run into a new run at HEAD. Plan04's recorded17deploy/7selected/16CI checks took1.247s; this auditor verified its receipt rather than rerunning tests. Fresh `git diff --check` passes.

The final recovery receipt is qualified same-archive multi-source evidence: first five stages at `fb926d8`, legacy lanes at `22c44d6`, current0014 at `a7f965f`. Three test harness paths differ from the five-stage source. It is not a fresh successful full extracted CI block at final source. Full recovery/389-source/archive validation belongs to the independent code/security/goal reviews; this UI reviewer does not claim to have repeated it.

## Human Acceptance and Native Zoom Limits

Read actual `10-HUMAN-UAT.md`: owner explicitly answered **“Reviewed: accept the new UI”** and **“Checked native 200%: passes”** on2026-11-13, for accepted48d970c and ZIP SHA256 `cf4e4817bdae885c2feea4c5fe9e6368ef834394a83f618e6bddddaa5fb9845d`. Independently recomputed the ZIP hash: matches. Browser/window dimensions were not supplied; none are invented. The native answer concerns the specified mixed History/held-correction/error packet pages. Preserve earlier Phase7–9 discovery/action/ticket/Portfolio acceptance under their own unchanged scope, rather than extending History's answer to them.

The exported packet is rendered static DOM/CSS/local fonts with synthetic data; controls do not execute. It supports presentation and owner readability review. Actual private/auth/focus/financial interactions are supported by the service/browser proof, not by clicking static exports. No new owner result or native-menu measurement is claimed. No materially affected scope was found requiring a renewed answer. Provider rights/live activation, SAFE-01, production/B2/tools/timers/publication and accepted W01–W08 debt remain outside this verdict.

## Registry Safety

Registry audit:0third-party blocks; no flags. `frontend/components.json` retains `registries: {}` and the approved official copied components. No registry acquisition/view/install is needed or performed.

## Files Audited

- Project AGENTS/CLAUDE/GSD adapter; UI auditor role, UI review workflow/skill/ui-brand; UI/UX skill and focused local `focus not obscured --domain ux` results; MASTER.
- Phase11 plans01–04/summaries01–03, UI-SPEC/UI-SPEC-REVIEW, LOCAL-PROOF, ACCEPTANCE, VALIDATION, REVIEW and SECURITY; project planning context and Phase10 HUMAN-UAT/VERIFICATION/UI-REVIEW.
- Focused implementation: `frontend/src/pages/HistoryPage.tsx`, `StockTradePage.tsx`, `frontend/src/components/HistoryEventDetails.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/e2e/dividends-history.spec.ts`, config and235relevant source/hash comparisons.
- Raw browser/build/package receipts and logs above; accepted review ZIP and two existing viewport captures. No private payload copied into this report.

**Recommendation count:**0required priority fixes;0minor product recommendations;3evidence-preservation safeguards. No commit performed.
