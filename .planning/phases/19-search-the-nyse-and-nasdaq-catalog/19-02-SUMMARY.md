---
phase: 19-search-the-nyse-and-nasdaq-catalog
plan: "02"
completed: 2026-11-24
requirements-addressed: [SC-01, SC-02, SC-03, SC-04]
requirements-completed: []
---

# Phase 19 durable catalog and provider mapping

Revision 0025 adds catalog generations, immutable securities, listing history,
scoped aliases and reviewed admissions. The operator importer validates a
complete inventory and matches live field scope against current independent
admission records. Publication uses one transaction and an expected-generation
check. A renamed issue retains its ID. A new issue using an old ticker gets
its own ID. Earlier listing versions keep their history.

Selected provider staging verifies the exact provider asset, symbol and venue
against the unchanged listing version. The operator supplies independent
reviewed USD one-share evidence. A single staged run allows up to two
requests under that review. Only normalized evidence can be promoted.

- Lint and strict type checks passed for publisher, importer and provider.
- All 28 mocked mapping tests passed.
- All 13 schema DDL statements matched the ORM PostgreSQL output. The 98
  migration and stock-authority tests and 8 publication tests collected.
- Wave 3 owns running 0025 with the matching grants, startup checks and exact
  restore. Mapping rights and live expanded Alpaca samples remain open.
