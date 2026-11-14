---
phase: 06-deploy
plan: "12"
subsystem: infra
tags: [production, release, tls, recovery, postgres, redis]
requires:
  - phase: 06-deploy
    provides: "Released source, protected routing and exact-source recovery gates"
provides:
  - "Published v0.4.0 and approved merge/back-merge integration"
  - "Live v0.4.0 at46d24c8 with separate migrator/revision0008 and restricted TLS roles"
  - "Preserved original volumes; verified candidate data/collation transition"
  - "Three real B2 backup/exact restore proofs using unchanged independent tools"
  - "Verified origin/public smoke and refreshed encrypted off-server export"
affects: [06-13]
tech-stack:
  added: []
  patterns: [continuous inherited operation lock, candidate-only conversion, post-rollout exact recovery]
key-files:
  created: [.planning/phases/06-deploy/06-ROLLOUT.md, .planning/phases/06-deploy/06-12-MAINTENANCE.md]
  modified: [.planning/STATE.md, .planning/PROJECT.md]
key-decisions:
  - "Owner separately approved publication, merge/back-merge, host preparation and exact live rollout."
  - "Immediate outage/only Birja writers and off-server secret custody explicitly confirmed."
  - "Keep originals untouched; treat app startup as a potential-write boundary preventing stale-volume fallback."
requirements-completed: []
requirements-addressed: [DEPL-01, DEPL-02]
duration: "Multi-session approvals/preparation; live locked operation about10min; outage365.719s"
completed: 2026-11-10
---

# Phase06 Plan12: Recoverable v0.4.0 production rollout

**v0.4.0 is live at birja.nist.one with restricted verified-TLS roles,
revision0008, preserved originals and fresh post-rollout exact B2 recovery.**

## Accomplishments and authorization

Publication boundaries completed individually with explicit owner approval:
PR27 main merge46d24c8, annotated v0.4.0/GitHub release, PR28 develop back-merge
63c9b47. Exact-head source/back-merge CI all six checks passed. Approved preflight,
host prep and off-server archive custody are in their dedicated records. Owner
confirmed window now/only Birja writers, then explicitly approved the full reviewed
06-12-MAINTENANCE packet. No authority was inferred from “continue”.

Reviewed exact source46d24c8591de2207cf219429aac0768962bed4c3 and installed
MANIFEST70e568a8c0f9953926e40de4ed79ec25272b3cdd777e474b3967a09849edb0b2
used unchanged. Continuous inherited shared lock protected final material changes,
recovery, stopped copy, candidate startup, role/migration/deploy and final export.
Originals preserved; candidate-only ownership and REINDEX-before-refresh completed.
All private row/schema/money/sequence invariants and5index-vs-sequential comparisons
passed.3restricted roles and9migrator-owned tables verified before0008 migration;
actual app/scheduler SSL sessions verified afterward. Four services healthy.

## Verification

- Pre-copy snapshot eac31e13efdc0b3dc82beb49076604e5e0952ce7188b19837e93df3d03fef847:
  installed backup, full exact retrieval/restore and source010770/revision0007 gate PASS.
- Post-role snapshot c1e1d90193a8ef42f6f6d099cd2e20e9a5027e8b20c51ba015a8af2b209df766:
  same unchanged tools and exact recovery PASS before app deployment.
- Post-deploy snapshot50008a08ea9dd6041d4dcbcc5de43871324abb5233a2650c58872f799d4f7444:
  actual released46d24c8/revision0008, full exact isolated restore and strict gate PASS.
  First two are historical proofs; one-copy rotation does not retain all three.
- Origin smoke41/41 and public9/9 PASS. Outage365.719s. Original fingerprints
  unchanged, restore container/network/volume cleanup empty, all129retained and
 20independent recovery payload hashes reverified. Shared lock released.
- Refreshed password-encrypted7z:26members/all extracted hashes verified;
  final settings available for owner download, no new secret material generated.
- Required offline checks PASS: backup25tests51.218s (real encrypted local
  rotation included), restore-safety4tests1.371s, CI9tests0.419s. Independent
  closeout review06-12-CLOSEOUT-REVIEW passes0blockers/0warnings, with no
  additional live inspection or operational proof inferred from that review.

## Task commits and artifacts

Reviewed maintenance packet1b83f64 followed earlier approved preparation/custody
records. No runtime source/dependency/image change in this live operation;
operational results and this summary are committed in the closing metadata step.
Public sanitized06-ROLLOUT has exact receipts; private data/digests/runtime logs
and all archive/configuration/credential payloads remain ignored and uncommitted.

## Deviations and limits

No gate weakening, destructive repair, real-data restore or rollback was required.
An initial private script filename shadowed Python stdlib operator; corrected
before any production code ran. Temporary private comparison rows removed after
successful checks. No secret values or real rows exposed to chat/repository.

Requirement IDs remain incomplete: DEPL-01 still needs Plan13 Gmail/Outlook
friend signup/trade acceptance; DEPL-02 still needs the owner-deferred genuine
nightly activation observation. Do not create09SUMMARY/13SUMMARY or claim whole
Phase6 completion. Refreshed export download is offered to update saved config;
confirmed secret/CA custody remains valid because secrets did not change.
