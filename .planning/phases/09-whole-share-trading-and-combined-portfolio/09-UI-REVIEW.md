---
phase: 09-whole-share-trading-and-combined-portfolio
status: human_needed
review_mode: sequential-inline
reviewed: 2026-11-12
---

# Phase 9 six-pillar UI audit

Distinct inline audit under gsd-ui-review and ui-ux-pro-max. Not an independent
agent assessment. Baselines:09-UI-SPEC,09-CONTEXT, design-system/birja/MASTER,
actual source and current authenticated disposable-browser screenshots. Local
UX search guidance was applied to confirmation/error recovery; final pass read
accessibility, interaction and performance quick-reference rules. No third-party
UI registry block or new dependency was introduced.

## Scores

| Pillar | Score | Specific finding/evidence |
| --- | --- | --- |
| Copywriting |3/4 | Explicit Buy/Sell/Preview/Confirm/Check result, source and simulation/fee/settlement disclosure. Incomplete headline repeats Known value and the two unavailable return fields read repetitively; cosmetic, values remain safe. |
| Visuals |4/4 | Actual1440preview separates7/5 ticket and confirmation; responsive320card hierarchy is readable. Text-labelled states and original receipt hierarchy; no decorative image dependency. |
| Color |4/4 | Neutral inherited tokens, single inherited portfolio highlight, selected bid/ask blue tint, gain/loss sign+text/icons. No raw ad-hoc color in new components. Master documents text contrast; this is not a new measured blanket contrast certification. |
| Typography |4/4 | Inter, declared13/15/24/32/40px scales, tabular financial figures, wrapping actual64-character catalogue name. All fields render without horizontal page overflow at320/375/768/1024/1440. |
| Spacing |3/4 | Existing4/8/12/16/24/32 rhythm and44px actions retained. Full session timestamps repeat timezone wording and make the narrow ticket tall; no clipped data/control. |
| Experience design |3/4 | Actual keyboard/radio/error/expiry/UNKNOWN/reprice/receipt flows and focused confirm-above-navigation pass. Native200% zoom could not be applied in headless browser; owner check remains mandatory15. |

Score21/24. No task-blocking visual defect observed in inspected evidence.
Human acceptance and native zoom are outstanding gates, not automated passes.

## Actual evidence and limits

Current full canonical run:45passed,1expected production-CSPskip, retries0,
234.6seconds; /tmp/birja-phase09-browser-69b6wynx/browser-all.log.
Owned project cleanup asserts zero containers/networks/volumes. Current images
are /tmp/birja-phase09-ui-review/MANIFEST.json; source hashes in
09-UI-SOURCE-HASHES.json. Visually inspected final1440preview,1440portfolio,
320preview and actual incomplete portfolio. Full-page screenshot fixed-bottom
nav is not a runtime overlap claim: focused Confirm bounding check actually ran.

Native Ctrl+Equal did not change viewport/pixel ratio. Supplementary640px
reflow and legacy CSS zoom captures are not native200% proof. No owner approval
is inferred from screenshots or earlier Phase7/8 acceptance.

Final affected stock suite14passed97.5s with25live application screenshots and
five actual DOM/CSS/font snapshots; source969c301. The generated read-only pages
also pass a separate OFFLINE browser check at1440/375/640, actual AAPL/BTC rows,
zero script/form/link/iframe elements and zero external HTTP requests. An offline
preview was visually inspected against the actual application preview. These
checks establish review-file integrity and reflow, not native200% success.

## Priority follow-ups

1. Complete actual owner ticket/receipt and combined-portfolio acceptance plus
native200% check in15 after final operational gates.
2. Optional copy polish: distinguish the two unavailable return fields and
avoid repeating Known value; no accounting calculation or permission change.
3. Optional timestamp density polish retaining full date, timezone and source.

Loading/error/empty/closed/held/expired states are present, labels connect to
inputs, radio controls support keyboard arrows, focus moves to original receipt
and back to quantity on Trade again; reduced motion and five-width browser
assertions pass. Automated axe/all-WCAG certification is not claimed.
