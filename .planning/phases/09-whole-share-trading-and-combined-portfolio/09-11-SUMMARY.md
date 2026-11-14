---
phase: 09-whole-share-trading-and-combined-portfolio
plan: "11"
subsystem: stock-ticket
requires: [09-10, 09-12]
provides: [whole-share stock ticket, immutable receipt UI, actual authenticated stock route]
affects: [09-13, 09-14, 09-15]
tech-stack:
  added: []
requirements-completed: []
requirements-supported: [STKTR-01, STKTR-02, STKTR-03, STKTR-05, STKTR-06, MKT-02]
completed: 2026-11-12
---

# Plan09-11: Stock ticket and recorded receipt

Task1 RED5e14d28 observes missing quantity controls, explicit preview/confirmation,
closed editable drafts and receipt semantics. Implemented actual09-10 hook with
neutral native Buy/Sell radios, positive whole-share input/errors, server Buy max/
Sell all drafts, both bid/ask with selected-side text, explicit server preview
and disabled unavailable confirmation. No estimated client totals. Repricing
shows previous/new price and signed cash/difference and needs another click.
Unknown freezes edits and allows explicit same-body/key result resolution after
closure; no fresh price is needed merely to recover an original receipt.

Receipt remains saved original identity/source/times/quantity, fee/cash delta and
historical cash/share-after with source attribution and omitted-fee/immediate-
proceeds disclosure. Success focuses Order filled; Trade again focuses cleared
quantity. Session bounds show actual America/New_York labels; source/fill times
show full local date/zone. Responsive7/5 cards and safe wrapping use MASTER.

Task2 RED4afab8c observes missing discovery links. Authenticated App now mounts
/trade/stocks/:symbol separately before the unchanged crypto route. Eligible
entries say Trade, others View stock; links never authorize fills. Current
independent status replaces coming-later copy. Mounted App/route and legacy
crypto regressions remain. Invalid route syntax gives safe Markets navigation.

Inline review RED1c3ddae exposed receipt_unavailable being misclassified as proof
of no fill. Execution now retains UNKNOWN and its frozen key/body, proven through
actual rendered result checks. Read-only failures keep their separate semantics.
This fixes Plan10 integration without changing wire or backend accounting.

## Verification

Focused6files:152passed6.48s. Full frontend556passed;96.42%statements,
92.40%branches,98.13%functions,97.32%lines. Full lint and TypeScript pass;
scoped Prettier and diff checks pass. These frontend fixtures prove UI/state,
not real financial effects; actual SQL/HTTP is06–08, browser proof follows13.
Critical-path coverage expansion and final source/security/goal review remain14,
actual owner new-UI acceptance15. No provider/production/publication occurred.
