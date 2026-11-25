---
phase: 19-search-the-nyse-and-nasdaq-catalog
plan: "01"
subsystem: stock-catalog-inventory
tags: [nasdaq, nyse, openfigi, provenance, inventory]
requires:
  - phase: 18-make-simulated-stock-trades-work
    provides: Limited-universe source decision and stock trading boundaries
provides:
  - A deterministic version 1 inventory manifest with per-row provenance and per-venue coverage
  - Paired directory parser, issue classification and bounded resumable mapping
  - Dated source and field-purpose decision for expanded catalog work
affects: [stock-catalog-publication, stock-search, stock-quote-selection]
tech-stack:
  added: []
  patterns: [strict Pydantic manifest, bounded operator inventory, issue-level corroboration]
key-files:
  created:
    - backend/app/services/stock_catalog_sources.py
    - backend/app/services/stock_catalog_classification.py
    - backend/app/tasks/stock_catalog_inventory.py
    - backend/tests/test_stock_catalog_sources.py
    - backend/tests/test_stock_catalog_inventory.py
    - .planning/phases/19-search-the-nyse-and-nasdaq-catalog/19-SOURCE-DECISION.md
  modified: []
key-decisions:
  - "Exact issue-level evidence is required for common or ordinary share admission."
  - "Live mode requires current field-purpose evidence before acquisition."
  - "Reuse fresh normalized classifications for unchanged source rows and recheck changed or expired evidence."
requirements-addressed: [SC-01, SC-02, SC-04]
requirements-completed: []
completed: 2026-11-24
---

# Phase 19 Plan 01 stock inventory summary

The inventory reconciles both listing directories into issue-level outcomes
and gives the publisher a fixture-only candidate until live scope and coverage
can be supported by evidence.

## Delivered

- Strict paired source parsing checks headers, format, size, flags and Eastern
  creation timestamps. The normalized rows preserve venue, distinct source
  symbol namespaces, source hashes and exact row references.
- Common and ordinary shares need corroborated class evidence. Known excluded
  securities and exact duplicates have their own dispositions. Conflicting
  directory rows and missing, ambiguous or reused identity evidence stay
  unresolved. The controlled exception path keys a reviewed issue by exact
  source row, ticker, venue, dated evidence and issue group.
- Live mode checks permitted fields before transport. It uses two fixed
  directory endpoints and bounded anonymous OpenFIGI mapping. Its cursor
  records source digests, fresh normalized outcomes and retry accounting. The
  candidate contains rights references, source timestamps and totals that the
  importer can reconcile independently.

## Verification

- The two focused suites passed all 23 tests against the isolated guarded test
  stack. Ruff and strict mypy passed for the inventory code.
- The fixture produced byte-identical manifests on consecutive runs. Its 5
  rows reconcile to 2 included, 2 excluded, 1 duplicate and 0 unresolved.
  Nasdaq has 1 included, 1 excluded and 1 duplicate. NYSE has 1 included. The
  other venue bucket has 1 excluded.
- The fake-clock mapping tests verify 10 jobs per call, 100 attempts per run,
  20 per rolling minute across restart, Retry-After, failed batch refusal and
  reuse of unchanged unexpired evidence.

## Source disposition

The prior planning samples establish reachability and paired format. The live
field-purpose scope for the Other Exchange-Listed directory and OpenFIGI
classification, exact paired coverage, and expanded Alpaca reference and quote
scope remain open. Live source requests were unnecessary for the fixture path
and none were made during this plan. [Source decision](19-SOURCE-DECISION.md)

## Execution notes

Both planned tasks passed the applicable fixture checks. Live SC-01 acceptance
requires an admitted source and a complete reconciled live manifest. Later
plans own publication, durable instrument identity and interactive search.
The orchestrator owns the task commits and planning state updates.

## Self-check

All expected implementation, test and decision files are present. Focused
verification passed. The orchestrator can record commit hashes after staging
the two tasks.
