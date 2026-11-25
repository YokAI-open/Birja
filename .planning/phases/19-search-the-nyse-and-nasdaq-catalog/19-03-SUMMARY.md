---
phase: 19-search-the-nyse-and-nasdaq-catalog
plan: "03"
completed: 2026-11-24
requirements-addressed: [SC-02, SC-04]
requirements-completed: []
---

# Phase 19 schema admission and encrypted recovery

Revision 0025 is the current application schema. Startup and migration check
its exact objects, ACLs and private default grants. The app and scheduler
can read the catalog. The migrator retains control of writes and the private
provider review reference. Explicit retained 0024 and 0023 consumers retain
their own schema contracts. The 0024 snapshot payload keeps its historical
bytes, while 0025 uses portfolio payload v5 in the v6 recovery archive.

- Current catalogue SHA-256 is `64ae5dbb83bfa0fa764d667a91f09abcf023b39f3e3b032354ce1088c45135a3`.
- Current ACL SHA-256 is `a055778473726ac8321879c4c3a93d2810217a388bf70794b7ca773ada1aaf8f`.
- The focused database sweep passed 172 cases across migration, publishing,
  mapping, exact startup and privileges. The final equivalent constraint
  definitions passed another 17 targeted PostgreSQL cases. Fresh Compose
  startup and staged 0024-to-0025 upgrade passed on the final test image.
- Offline deployment compatibility passed 75 cases and the portfolio
  validation contract suite passed 43 cases. The 0024 compatibility fixture
  uses its historical source. A populated 0025 database refused downgrade.
- The recovery check captured consistent PostgreSQL dumps and snapshots,
  then verified encrypted restic archives in local TLS PostgreSQL clones.
  Both 0024 and 0025 matched their manifests. Existing finance, sequence
  positions and old stock receipts survived, ticker reuse kept separate
  identities, and expired review remained expired. The Redis quote canary
  was absent from the archive and extracted SQL. The 0025 canonical dump
  schema SHA-256 is `ee9de25d015c568f1bfe0a9afd3b618369a101aa376f6f98b5f74f7fa5c9c75f`.
- Stock and portfolio recovery contract checks passed 37 focused cases.
  The v6 package inventory also passed offline with the pinned image. The
  live rollout and historical release matrix remain Phase 21 evidence.
