# Project Retrospective

## Milestone: v1.0 — Birja MVP

**Shipped:** 2026-11-10. **Phases:** 7. **Plans:** 69. **Declared tasks:** 163.

### What Was Built

- One-command local stack and required lint/type/test/image/browser/operations CI.
- Email OTP sign-in, persistent revocable sessions and exactly-once $10,000 accounts.
- Fifteen curated Kraken crypto prices with automatic refresh and visible age.
- Exact atomic market buy/sell, itemized previews, stale-price refusal and idempotent fills.
- Mid-price portfolio performance/allocation and stored paginated trade history.
- Public HTTPS v0.4.0 with Gmail/Outlook acceptance, restricted DB TLS roles and proven encrypted off-server recovery.

### What Worked

- Vertical slices kept a usable app throughout; real PostgreSQL tests covered
  financial concurrency, identity, snapshot consistency and migrations.
- Explicit owner approvals and exact source/artifact checks made release and
  recovery changes reviewable. Independent review caught lock-wait freshness,
  retained routing and TLS startup issues before final acceptance.
- One immutable recovery artifact and actual isolated restores established
  recovery across role/TLS transitions and supported old-application rollback.

### What Was Inefficient

- Phase 6 expanded through image vulnerability remediation, native/UID/collation
  compatibility, CI differences and protected rollout prerequisites. Validate
  those transitions early with a small populated production-shaped fixture.
- Sparse summary metadata and stale state pointers obscured real progress.
  The archive helper counted 29 tasks; declared plan tasks total 163. Treat helper
  output as a starting point and verify counters against source artifacts.
- Repeated exact-artifact changes required new narrow approvals. Stabilize and
  test the final packet before requesting installation/publication checkpoints.

### Patterns Established

- Decimal/string money transport, account-first locking, user-scoped idempotency,
  deterministic seek history and one-statement portfolio snapshots.
- Cancel private queries before identity publication; preserve observed auth
  query and reject late cancelled results.
- Compare exact source/config/snapshot identities, publish restore success only
  after cleanup, and keep uploaded-versus-restored assurance distinct.

### Key Lessons

1. An enabled timer or successful manual backup does not prove a nightly run;
   correlate actual timer/service invocation with verified remote creation.
2. Encrypted backup custody and actual database recoverability are separate.
   Prove both, including free-tier replacement headroom.
3. Scan actual final images with a strict gate; test populated data, index and
   collation transitions before a live rollout.
4. Keep requirements/summary/verification metadata synchronized after each phase,
   while retaining historical evidence and unresolved advisory debt honestly.

### Accepted Follow-ups

W01–W08 and four early validation-record gaps are owner-approved follow-up debt;
see the archived milestone and integration audits. No new cleanup phase is
scheduled and no finding is represented as fixed by documentation archival.

### Cost Observations

Model mix, session count and token/currency totals were not measured reliably.
No numeric cost claim is inferred. Phase 6 rework demonstrates the value of
bounded compatibility/CI rehearsals before requesting live changes.

## Cross-Milestone Trends

Only one milestone is complete; no cross-milestone trend is established yet.

| Milestone | Phases | Plans | Accepted execution evidence |
|---|---|---|---|
| v1.0 MVP | 7 | 69 | Backend 616; frontend 264; browser/ops/image CI; live owner acceptance and exact recovery |
