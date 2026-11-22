---
phase: 15
slug: verify-exact-portfolio-recovery-and-acceptance
status: approved
reviewed_at: 2026-11-22T07:49:43.575671+00:00
shadcn_initialized: true
preset: existing radix-vega / neutral / CSS variables
created: 2026-11-22
scope: verification of accepted surfaces; no new UI
---

# Phase15 — UI Verification Contract

This contract preserves the implemented Phase12–14 screens while Phase15
qualifies recovery and the complete strategy lifecycle. It introduces no new
page, component, palette, typography, copy or interaction. It is not a fresh
implementation/test result or a request to repeat accepted owner checks.

## Design System

| Property | Required existing value |
|---|---|
| Tool | Copied local shadcn/ui source; no initialization or CLI download |
| Preset | `frontend/components.json`: radix-vega, neutral, CSS variables, subtle menu accent |
| Component library | Existing React/Tailwind/shadcn-Radix, semantic native forms/select/table/links |
| Icon library | Existing Lucide;20px controls,16px inline; decorative icons hidden |
| Font | Self-hosted Inter Variable; tabular financial figures |
| Authority | `design-system/birja/MASTER.md`, `frontend/src/index.css`, accepted12/13/14UI-SPEC contracts |
| Reuse | PortfolioCreateForm, PortfolioMetadataForm, PortfolioSwitcher, PortfolioContext, PortfolioDeleteForm, PortfolioTargetBoundary and existing financial pages |

Local config, package manifest, CSS and consumers were inspected on2026-11-22.
The existing-system gate is satisfied by this checked-in configuration and
locked reuse decision; no `npx shadcn`, online preset check, library lookup,
registry fetch or installation is required for unchanged source usage.
Do not restyle legacy financial surfaces to fit a new global template.

## Spacing Scale

| Token | Value | Existing use |
|---|---|---|
| xs |4px| Labels/helpers and compact icon/text gaps |
| sm |8px| Control separation and status gaps |
| compact |12px| Mobile cards and form stacks |
| md |16px| Mobile padding/gutters and confirmation content |
| lg |24px| Desktop card padding and management sections |
| xl |32px| Desktop page gutters |
| 2xl |40px| Management page-heading line box |
| 3xl |48px| Existing input/select height |

These are existing multiples of four. Preserve at least44×44px action hit
areas and8px separation,52px overview rows,24px card radius,14px control radius
and pill buttons. Functional dimensions are inherited, not new spacing tokens.
Long text grows naturally; no fixed-height warning or clipped action label.

## Typography

The accepted management/deletion surfaces use four sizes and two weights:

| Role | Size | Weight | Line height |
|---|---|---|---|
| Body/input/actions |16px|400 body;500 action emphasis|24px |
| Label/helper/timestamp |14px|400 body;500 column labels|20px |
| Section/strategy heading |20px|500|28px |
| Management page h1 |32px|500|40px |

This inventory does not override unchanged financial pages: their Phase12
contract retains15/13/32/40px content roles at400/500 and inherited16px input
text. Phase15 creates no additional size or weight. Names/descriptions wrap
with `min-width:0` and safe word breaking; never shrink or make hover the only
way to identify the target. Keep exact server-string money formatting, signs,
timestamps and tabular numbers; no browser financial arithmetic or pooled sum.

## Color

| Role | Existing value | Usage |
|---|---|---|
| Dominant60% | `--background` #F2F2F2 | Neutral canvas |
| Secondary30% | `--card` #FAFAFA; `--popover` #FFFFFF | Cards, inputs and neutral controls |
| Accent10% maximum | `--primary` #18181B; `--accent` #EEF1FE; `--accent-foreground`/`--ring` #3451D1 | One current primary action, active navigation, selection and focus |
| Destructive | `--destructive` #B83270 | Final Delete portfolio action and its trigger text |

Accent is reserved for the listed actions/navigation/selection/focus; never
all controls. Create portfolio, Save changes or the current recovery action
is the local primary action; Cancel/overview navigation stay neutral. Delete
replaces that section's primary action with the existing destructive variant.
Unknown/wait uses warning tokens; refusal uses existing loss tokens. Gains and
losses retain explicit signs/text. Components use semantic classes, not raw
hex. Keep logo orange logo-only and add no gradient or asset. Existing financial
highlight treatment remains under its original contract; the overview has no
pooled hero. Ratios describe inherited surface balance, not new allocation.

## Copywriting Contract

Preserve actual source copy. The following strings anchor verification, not a
rewrite; detailed financial and error variants remain under accepted contracts.

| Element | Existing copy / required meaning |
|---|---|
| Overview / primary action | Portfolios / Create portfolio |
| Name / description labels | Portfolio name / Description (optional) |
| Edit / save / discard | Edit portfolio / Save changes / Discard changes |
| Empty heading | No portfolios yet |
| Empty body | Create a portfolio to start an independent strategy with $10,000.00 in virtual cash. |
| Overview initial failure | Can't load your portfolios right now. Try again. |
| Explicit switching | Open portfolio / Open selected portfolio |
| Incomplete value / return | Known value: `{amount}` — incomplete / Return unavailable |
| Unknown creation | We couldn't confirm whether your portfolio was created. Retry this creation to check its original result. |
| Original creation recovery | Retry creation |
| Trade actions | Existing crypto Preview / stock Preview trade; Confirm buy / Confirm sell; Check order result for an unknown original order |
| Delete review | Delete “{name}”? |
| Terminal effect | This ends this strategy permanently. Its committed cash, investments and History will be frozen and unavailable in normal portfolio screens. |
| Future effects | Future dividends, splits and corrections—including unpaid dividends already earned—will not change this portfolio. |
| No liquidation/undo | Nothing will be sold or moved to another portfolio. Financial records are retained, and you cannot undo this in Birja. |
| Last portfolio | This is your last active portfolio. You'll stay signed in and can create a new portfolio when you're ready. |
| Review actions | Cancel / Delete portfolio |
| Unconfirmed deletion | Deletion result unconfirmed / Check deletion result |
| Rename refusal | This portfolio's name changed. Review its latest name before confirming deletion again. |
| Operational deletion refusal | This portfolio couldn't be safely deleted. Try again later. If this continues, contact the operator. |
| Private stale route | Portfolio unavailable; offer Portfolios, disclose no retained financial values |

`{name}` is the canonical reviewed name as escaped text; it never supplies
authorization. Errors persist until resolved; outcomes must not rely on a
toast or color alone. Keep existing safe unknown-result recovery: no generic
“OK”, automatic resubmission, implied cancellation after send or new key/target.

## Lifecycle Verification Matrix

| Existing surface/flow | Observable acceptance contract | Source/test anchors |
|---|---|---|
| Create | Named independent strategy receives one starting grant; pending/unknown preserves original payload/key; explicit retry only | PortfolioCreateForm; portfolio-strategies.spec.ts |
| Rename/edit/clear | Authoritative name updates; optional description can be empty/cleared; Cancel discards draft without money changes | PortfolioMetadataForm; strategies spec metadata cases |
| Compare | Stable per-portfolio rows/cards, own cash/baseline/return and honest incomplete values; no pooled amount | PortfoliosPage; strategies spec incomplete/refresh cases |
| Switch | Native selection is draft navigation intent; explicit Open enters immutable selected ID; Back/late responses never retarget an order | PortfolioSwitcher/PortfolioTargetBoundary; strategies/ownership specs |
| Trade/receipt/History | Chosen name/ID remains visible; original unknown trade retry stays original; private deterministic History/references do not cross portfolios | Existing TradePage/StockTradePage/History; ownership and strategies specs |
| Delete/Cancel | Full named terminal consequence review; Cancel sends no deletion; holdings are frozen without liquidation/transfer; siblings remain usable | PortfolioDeleteForm; portfolio-deletion.spec.ts |
| Last deletion/zero | Signed-in empty state with Create; reload/sign-in/Back do not fund or select a replacement | PortfoliosPage; deletion/ownership zero cases |
| Error/private unavailable | Failed discovery is not an empty list; stale/foreign/closed target suppresses finances and offers overview | Target boundary; ownership/deletion error/stale cases |
| Unknown/reload recovery | Immutable original creation/order/deletion identity survives permitted reload; explicit recovery cannot become a sibling/replacement operation | Existing hooks/recovery route; all three specs |

Keep the existing max1440px layout, mobile gutters, table-to-card behavior
below768px, stacked controls at320px and safe-area shell navigation. Long
names/descriptions and large values must remain readable without horizontal
page scrolling. Preserve keyboard order, visible focus, h1 navigation focus,
Cancel focus restoration, linked errors and polite nonduplicated outcomes.
Focused controls remain unobscured as the existing project quality target.
No new overlay, modal, focus trap, motion or interaction is introduced.

## Evidence Reuse and Human Acceptance

- Phase12 actual owner UI and separate native200 outcomes are recorded in
  `12-HUMAN-UAT.md`; Phase13 outcomes are in `13-UAT.md` and `13-18-SUMMARY.md`.
- Phase14 `14-HUMAN-UAT.md` records the owner's2026-11-22 response:
  “i approve ui and 200 zoom”. Accepted R7 ZIP SHA256 is
  `886805a094fad7495ae53539da7ea80d0ddff6c67b1ce0aa0465899a493d32e0`;
  source747d5d7, render digest9b62b226…a7f6. Immutable capture-time flags remain
  unchanged; actual human outcomes live separately in the acceptance record.
- Phase15 must map each lifecycle row to actual existing source/test/receipt
  provenance. Reuse owner outcomes only for unchanged relevant screen content,
  interaction, style and supporting render inputs. Record an explicit source
  comparison; a broad package hash difference alone does not prove visual change.
- Tooling/restore-only changes do not require new screen captures, redesign or
  another owner/native200 question. Do not claim a current full packet match if
  only its unchanged visual subset matches; state that narrower association.
- If a real interaction/copy/layout changes, run only affected UI checks and
  obtain the affected actual owner/zoom result where needed. Do not widen this
  into reapproval of unchanged screens or infer acceptance from silence.
- Reuse valid backend/browser/security/image evidence with explicit unchanged
  input scope under15-CONTEXT/VALIDATION. Fill only demonstrated coverage gaps.
  Do not relabel a failed whole run or inherited component evidence as fresh
  full CI; complete required CI still precedes merge.

## Registry Safety

| Registry | Blocks used | Safety gate |
|---|---|---|
| shadcn official | Existing local Button/Input/Card/Badge consumers only; no new block |2026-11-22: existing config/package/CSS and consumers inspected; no download/install; new-block vetting not applicable |
| Third-party | None |2026-11-22: `components.json.registries` is empty; no third-party block declared; vetting not applicable |

No registry CLI, preset reset, asset/font download or package operation is
authorized by this verification contract.

## Research Provenance and Boundaries

Sources read:15-CONTEXT/RESEARCH; PROJECT/REQUIREMENTS/ROADMAP/STATE; MASTER;
12/13/14 UI contracts and actual acceptance records; frontend component config,
package manifest, CSS, management/target/switcher consumers and existing
strategies/ownership/deletion browser test names. No new framework usage or
library API decision required external documentation.

One local ui-ux-pro-max search on2026-11-22:
`focus not obscured --domain ux -n 3` returned Focus Not Obscured minimum,
enhanced and Focus Appearance guidance. It fits the existing visible/unobscured
focus outcome; this contract preserves the project target and makes no new
standards-certification claim. No design-system generation/persistence, code
change, test/browser execution, provider or production operation occurred.

Keep Phase7 live obligations, issue35 scope/expiry, publication and production
outside this contract. No new asset, chart, product page or owner decision is
needed for PSAFE-04/05/06.

## Checker Sign-Off

- [x] Dimension1 Copywriting: PASS
- [x] Dimension2 Visuals: PASS
- [x] Dimension3 Color: PASS
- [x] Dimension4 Typography: PASS
- [x] Dimension5 Spacing: PASS
- [x] Dimension6 Registry Safety: PASS

**Approval:** independent UI checker passed all six dimensions with zero blockers/warnings on2026-11-22. Existing implemented owner
acceptance remains valid only under the explicit unchanged-surface rules above.
