# Phase 13: Create and Compare Independent Strategies — Context

**Recorded:** 2026-11-18.
**Source:** Approved v1.2 requirements/roadmap and the owner's explicit instruction to research, create the required UI contract from Birja's existing design system, then write and check plans. This compiles existing decisions; no new discuss-phase interview is claimed.

<domain>
## Phase Boundary

Deliver the runnable create/name/describe/open/invest/compare journey over Phase12's qualified explicit portfolio ownership. This phase enables additional independent funded portfolios while retaining exact money, authorization, active stock-action effects, safe retry and recovery contracts. Public deletion/freeze activation belongs to Phase14; integrated full lifecycle acceptance belongs to Phase15.

Primary requirements: PMGT-01, PMGT-02, PMGT-06, PFUND-01, PFUND-02, PFIN-01, PFIN-04, PCTX-02, PVIEW-01, PVIEW-02, PSAFE-07.
</domain>

<decisions>
## Implementation Decisions

### Portfolio creation and metadata
- D-01: Up to ten active private portfolios per user. Ten is an active count, not a lifetime limit. New identities may use slots/names freed by retained closed fixtures; public deletion UI/API stays Phase14.
- D-02: Users can set and rename names, trimmed nonblank 1–60 characters with no control characters. Active names must be unique for that owner under a documented case-insensitive normalization rule; other owners may reuse a name. Renaming never changes money/history.
- D-03: Optional plain-text descriptions can be added, viewed, edited or cleared; empty is valid. Existing/initial portfolios begin empty. Descriptions change no finances/history.
- D-04: Each genuinely new identity receives exactly $10,000 cash and its own stored starting baseline once. A brand-new user's initial portfolio remains “My portfolio” with the same single grant; existing finances/baselines are never reset or supplemented.
- D-05: Unknown-result creation retries cannot create a second strategy/repeat a grant. Retry identity/payload stays bound even after the original portfolio closes; an old key cannot recreate it. Sign-in, reads, rename, refresh or metadata edits never grant cash. An intentionally empty set remains empty until explicit creation.

### Independent investing, switching and comparison
- D-06: Multiple same-owner portfolios may own/trade the same crypto or stock with independent cash, quantities and basis; crypto/stocks share cash only within a portfolio. Preserve all Phase12 execution/retry/privacy rules.
- D-07: Active portfolio dividends/corrections derive from its own historical ownership, apply once and remain attributable. Active split effects must work correctly across independent books now; do not postpone active accounting to Phase14.
- D-08: Overview lists all active strategies in stable order, showing name, cash, exact total or known value and dollar/percentage return against each stored baseline. No pooled cross-portfolio wealth total or misleading strategy ranking.
- D-09: Overview and detail share exact valuation/time/completeness semantics. An unvalued holding makes only that strategy incomplete with unavailable overall return; other portfolios remain usable.
- D-10: Opening/switching uses explicit stable portfolio identities. Cached pages/cursors, previews, pending original attempts and late responses remain isolated. A switch cannot retarget an old order or display another book's finances. Existing unavailable-target/privacy refusal remains; public deletion journeys stay Phase14.

### Safety, bounds and delivery
- D-11: Requests/jobs remain bounded; creation reuses appropriate rate/resource controls, count cannot exceed ten under concurrency, shared price polling does not multiply, and existing stock activation/backup-capacity guards remain. Grant/event exactness and owner/active-state authorization are server enforced.
- D-12: Each supported schema/state transition must ship restricted grants/TLS, immutable financial/retry evidence, exact encrypted recovery and supported rollback or explicit refusal. Phase15 is no reason to postpone current-revision safety.
- D-13: Use the existing Birja React/Tailwind/shadcn/TanStack Query design system; retain the accepted existing financial surfaces and define new management/overview UI in a checked UI contract. New UI/native browser zoom acceptance follows actual implementation, not planning.
- D-14: Keep work local on feature/milestone-v1.2. No implementation, new packages/installations, push/merge, live provider campaign, production inspection or deployment is authorized by planning.

### Agent Discretion
- Choose concrete metadata/resource boundaries, idempotency transport and durable journal/grant contracts, consistent lock order, migration sequence and retained source fingerprints after inspecting actual Phase12 code.
- Select a documented technical normalization and plain-text description length bound consistent across API, DB, UI and retry canonicalization; preserve approved name length/empty-description outcomes. Do not treat an implementation choice as a new owner decision.
- Choose overview order, form placement, switcher presentation, retry/error/limit feedback and accessible responsive layout using existing tokens and components; define exact choices in UI-SPEC.
- Use the existing packages. Plan bounded tasks and meaningful isolated concurrency, ownership, once-only funding/event, browser, critical coverage/security/image and recovery tests.
</decisions>

<canonical_refs>
## Canonical References
- /home/YokaiExchange/CLAUDE.md
- /home/YokaiExchange/AGENTS.md
- /home/YokaiExchange/.planning/PROJECT.md
- /home/YokaiExchange/.planning/REQUIREMENTS.md
- /home/YokaiExchange/.planning/ROADMAP.md
- /home/YokaiExchange/.planning/STATE.md
- /home/YokaiExchange/.planning/research/v1.2/SUMMARY.md
- /home/YokaiExchange/.planning/research/v1.2/ARCHITECTURE.md
- /home/YokaiExchange/.planning/research/v1.2/PITFALLS.md
- /home/YokaiExchange/.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-VERIFICATION.md
- /home/YokaiExchange/.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-31-SUMMARY.md
- /home/YokaiExchange/.planning/phases/12-preserve-existing-investing-under-portfolio-ownership/12-ACCEPTED-RISK.md
- /home/YokaiExchange/.planning/DEFERRED.md
- /home/YokaiExchange/design-system/birja/MASTER.md
</canonical_refs>

<deferred>
## Deferred and Accepted Follow-up
- Public terminal deletion, its confirmation/freeze/stale-tab/last-portfolio journey: Phase14. Use retained closed fixtures here to prove creation-slot/name/key semantics.
- Complete create/name/description/compare/switch/delete acceptance and lifecycle recovery: Phase15; current runnable revision proofs still mandatory now.
- Phase7 STOCK-01/02/03, DATA-01, MKT-01 and SAFE-01 remain separate and unverified. November16 campaign is consumed; no repeat/provider calls or activation implied.
- Picomatch advisory remains unresolved owner-accepted risk in issue35 through2026-12-17UTC. Existing exact artifact/source/expiry policies remain; no unrelated HIGH/critical waiver, unsafe fork or unapproved package change.
- Transfers, resets, configurable deposits, cloning, historical charts, sharing/leaderboard/pooled wealth remain outside approved scope.
</deferred>
