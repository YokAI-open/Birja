---
phase: 14-end-strategies-safely
reviewed: 2026-11-20
reviewer_role: independent-gsd-ui-auditor
source_commit: 426435789f8f41dea0b3fe9a4c0852c85b314a46
diff_base: 9527e358bc6953cec7580043703324db194ba396
capture_source: 724aa2af46c24a863929bd786a6e859eb383da51
status: implementation-reviewed-human-pending
score: 24
blockers: 0
warnings: 0
needs_human_review: true
owner_accepted: false
native_200_percent_verified: false
---

# Phase 14 — Independent UI review

The implemented deletion, original-request recovery and private unavailable
surfaces meet the inspected Phase14 UI contract. No implementation blocker or
warning was found. **Actual owner UI acceptance and genuine desktop browser-menu
200% acceptance remain PENDING Plan19.** This independent UI pass supplies
neither outcome, whole-security qualification nor recovery qualification.

Baseline: approved `14-UI-SPEC.md`, actual `design-system/birja/MASTER.md`,
`frontend/src/index.css`, existing components and repaired Plans12–14 contracts.
This is a distinct UI review role, separate from Plan18's code/security reviewers.
Original per-plan reviews and their repair histories were preserved.

## Evidence and inspection boundary

Reviewed the existing actual R5 packet rather than creating a replacement:

- ZIP `/tmp/birja-phase14-ui-review.zip`, measured SHA256
  `372c94808a6741f410522f1559221d5d2b71b02aefaa95ebe417a15911bffdfe`.
- Manifest capture source `724aa2af46c24a863929bd786a6e859eb383da51`, input digest
  `6a644be75ac56fd92287603b2b8785c0f850f8b7e553e8cd5a31d1353850bb18`.
- Direct read-only comparison found **zero mismatches across365 source-input
  hashes and419 artifact hashes** against the current checkout and packet.
- Manifest enumerates19 states at320/375/768/1024/1280/1440px:114 HTML captures,
  190 PNGs and114 sanitized traces plus index. All114 recorded base layouts and
  76 recorded narrow layouts have one h1 and no horizontal overflow.
- Existing actual offline receipt `/tmp/birja-phase14-plan17/offline-r5.json`
  reports190 layouts, zero external requests and Chromium156.0.8078.4. Those
  are the retained executor's measurements, not a newly repeated browser run.
- Both human flags are false in the actual manifest and remain false here.

Visually opened ten actual PNGs: confirmation320, long confirmation375,
restored-unknown320, empty1440, cross-tab768, rename-conflict1440.reflow,
retry-waiting375, submitting1440, discovery-error320 and uncertain-stock1024.
The720px rename reflow screenshot is a separate rendered narrow layout; it is
not native zoom. The long-name/description page has natural document height,
with all consequence text and controls present. User-supplied rocket characters
are escaped fixture metadata, not UI icons.

The screenshot-storage gate was checked: the existing
`.planning/ui-reviews/.gitignore` excludes PNG/WebP/JPEG and other raster assets.
No screenshot was created. Per the assigned exclusive-lane scope, no dev-server
probe, new browser, DB, test suite, external request, installation or active
HTML demonstration was performed. Fixed mobile navigation appearing across a
full-page screenshot records the original viewport position; that alone does
not prove live content is obscured. Current source padding, ordinary scrolling
and the retained live keyboard/focus assertions were inspected separately.

## Pillar scores

| Pillar | Score | Specific finding supporting the score |
|---|---|---|
| Copywriting |4/4|Named consequences explain terminal freeze, unpaid/future effects, retained records and no sale/transfer/undo; unknown copy preserves the original request.|
| Visuals |4/4|Stable h1 precedes management/recovery h2; neutral Cancel and a distinct rose final action remain legible in narrow and long-name captures.|
| Color |4/4|Existing semantic tokens preserve neutral canvas/cards, limited destructive emphasis and text-labelled status; no new raw component colors.|
| Typography |4/4|New lifecycle surfaces use the contracted16/14/20/32px hierarchy and400/500 weights with wrapping, without shrinking long names.|
| Spacing |4/4|Confirmation/recovery use16/24px padding,16px stacks,8px action gaps and at least44px controls;320px stacks actions and wider widths wrap.|
| Experience design |4/4|Explicit review/Cancel, durable unknown recovery, terminal-refusal retry, private stale routes and signed-in zero are present with current-context guards.|

**Overall:24/24.** Scores describe the inspected implementation and evidence;
they do not claim owner approval or complete accessibility certification.

## Priority fixes

None identified in this UI scope. No arbitrary three recommendations are added
to a passing audit. The separate code/security source-inventory blocker remains
owned by Plan16 and tracked in `14-REVIEW.md`/`14-SECURITY.md`; this UI score does
not resolve or waive it.

## Detailed findings

### Copywriting —4/4

`PortfolioDeleteForm.tsx:251` renders the exact escaped reviewed name in the
confirmation heading. Lines295–311 explain committed cash/investments/History
freeze, earned-but-unpaid and later effects, retained records, no liquidation,
no transfer, no undo and last-book signed-in behavior. The named text wraps
rather than becoming an ellipsis-only identity. Lines170–225 preserve the
captured original in busy/unknown states, explain that leaving does not cancel,
show the server wait boundary and label the explicit original-result check.
Terminal rename and safe metadata retry are generic when authority is absent;
they expose no stale financial data (`PortfolioDeleteForm.tsx:115`).

`PortfoliosPage.tsx:147–162` distinguishes a known closure acknowledgement from
an unresolved deletion notice. Its error/zero branches at188–233 do not equate
failed membership discovery with an empty account. The empty1440 and
discovery-error320 captures show readable separate outcomes.

### Visuals —4/4

`App.tsx:58–86` supplies one generic primary heading before the persistent
management host on detail routes. `PortfolioDeletionPage.tsx:6–8` supplies the
static recovery page heading. The boundary suppresses its duplicate when the
layout owns the heading (`PortfolioTargetBoundary.tsx:131–140`). Submitting and
restored-unknown screenshots show h1 first and a separately named recovery h2.

The ordinary page flow keeps confirmation within a640px maximum, with a separate
metadata card and explicit controls. The320 confirmation screenshot shows Cancel
above the final rose Delete button;375 long confirmation retains both labels.
No new decorative image, chart, modal or visual-only acknowledgement was added.
The error icon is20px, hidden from assistive technology and nonshrinking
(`PortfolioDeleteForm.tsx:259–262`).

### Color —4/4

Actual CSS retains MASTER's neutral background/card/foreground, ring, destructive,
warning and loss tokens. Inspected new deletion/recovery/page components contain
no raw hex/rgb values. The form uses destructive text on its disclosure and the
existing destructive variant only for final confirmation; Cancel/overview links
remain neutral. Unknown/wait/refusal meanings have explicit text and do not
depend on color. The inspected screenshots retain the intended neutral visual
balance with a small state/action accent; no whole-page destructive tint or
additional gradient was introduced.

### Typography —4/4

The lifecycle form's shared action class is16px with natural height and wrapping;
body is16/24, supporting timing14/20, heading20/28 at500. New routed h1 is32/40
at500. These match the Phase14 contract's override of the inherited financial
hierarchy. Inter remains locally imported by `index.css`; no external font was
introduced. Long canonical names use `min-w-0` and `wrap-anywhere`, and screenshots
show literal markup-looking text and Unicode without clipping consequence copy.
Native selects may shorten visible options, while the full selected name and
named confirmation remain separate readable text.

### Spacing —4/4

`PortfolioDeleteForm.tsx:247` and its recovery sections use `p-4 md:p-6`, `gap-4`,
`max-w-[640px]` and fluid width. Lines327–348 use `gap-2`, a320px column and
wrapping rows from375px; the action class sets `min-h-11 min-w-11 h-auto py-3`.
Existing card/pill/control radii are preserved. No fixed-height warning panel or
nested warning scrollbox clips long content. Source capture assertions in
`portfolio-review-capture.ts:reviewedLayout` measure44px controls and an8px gap
with subpixel tolerance; the recorded190 layouts cover the prescribed widths
and the corresponding narrow desktop alternatives. This reviewer inspected
those assertions/records and ten PNGs, without claiming a repeated measurement.

### Experience design —4/4

The disclosure opens review only. A current review focuses Cancel, Cancel/Escape
send nothing, and submission requires its own button (`PortfolioDeleteForm.tsx:
useLayoutEffect`, `cancelReview`, lines278–348). These behaviors have actual
retained keyboard assertions in `portfolio-deletion.spec.ts:177–216`, including
overview h1 focus after known closure; they are supplemented by component/App
regressions. Focus/error/busy semantics use one status or alert per recovery
state. Reduced-motion overrides accompany new action controls.

The metadata host survives financial quarantine, while its editor child remains
revocable (`PortfolioMetadataForm.tsx:15–45`, `App.tsx:71–86`). The deletion hook
persists before synchronous quarantine and transport, disables automatic mutation
retries, and checks owner/session/operation before and after async work
(`usePortfolioDeletion.ts:459–569`). Completion calls navigation only after
`receipt.isCurrent()`. Active GETs do not clear a current unknown original.
`checkDeletionResult` sends only the stored original after explicit activation
and respects Retry-After. Safe terminal-refusal metadata reads do not send DELETE.

Target, switcher and overview consume accepted projections. A masked sole root
does not become proof of zero (`usePortfolioTarget.ts:acceptedPortfolios`);
`usePortfolioOverview.ts:80–106` removes quarantined/hinted rows before display.
The stale boundary reveals only generic unavailability and the approved boolean
original-order notice (`PortfolioTargetBoundary.tsx:149–153`). Cross-tab768 and
restored-unknown320 show no retained finance. Signed-in empty/Create and explicit
new identity remain separate from unknown membership and automatic selection.

## Registry and local guidance

`frontend/components.json` retains the existing radix-vega configuration with
`registries:{}`. **Zero third-party registry blocks; no registry flags.** No
registry command, package fetch, font change or design-system regeneration ran.

The local UI/UX skill searches were scoped to `focus visible keyboard navigation`
and `text reflow long tokens` in the UX domain. Relevant results were keyboard
order/visible focus and natural-height reflow. Enhanced fully-unobscured focus
was treated as the project's quality target, not mislabelled an AA criterion.
The existing MASTER was preserved; no new style recommendation replaced it.

## Scope and remaining gates

Direct source inspection included the deletion form/page, metadata host/editor,
App detail/signed-in routing, target boundary, switcher, overview/page, deletion
hook and its target/overview consumers, tokens/Button and capture helper/spec.
The Phase14 baseline diff, interface/UI/validation/coverage artifacts, seventeen
completed-plan handoffs and relevant existing Plans12/13/14/17 review/repair
records establish integrated progress. Original reports remain unchanged.

Plan18 still owns complete same-source security/recovery proofs and resolution
of its independent non-UI findings. Plan19 must obtain two actual human outcomes
on the current reviewed evidence. Automated viewport/reflow, this review and
prior Phase13 approval cannot satisfy them. No requirement, shared state,
production configuration or publication status was advanced. Only this report
was created; no source/tests were edited and no commit was made.
