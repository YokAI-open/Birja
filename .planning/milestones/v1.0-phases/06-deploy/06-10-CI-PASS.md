## Current green CI and integration decision —2026-11-09

PR26 https://github.com/YokAI-open/Birja/pull/26 remains OPEN/MERGEABLE into
develop at exact a7d5dcb01d40a916c9cbf9d6ff51525c70c50833.
Actual run42618704350 completedSUCCESS:
https://github.com/YokAI-open/Birja/actions/runs/42618704350.
All six required jobs backend/frontend/image/e2e/ops/ci-pass passed; no required
job skipped. Job logs and raw public reports are preserved in ignored
pr-preparation/passed-ci-* and final-image-reports.

Backend616pass/99.80% overall/100% critical; frontend264pass. Browser10pass,
one expected csp.spec production-only skip because E2E_PROD_URL is absent.
Actual trade.spec buy/sell and full buy->portfolio->history->whole-sell pass,
including375/768/1024/1440 widths. Five raw runtime/builder/Node/Postgres/Redis
reports hash-match successful status records and each contain0HIGH/CRITICAL.
No ignores/waivers or severity changes.

Ops proves pinned29.2.1/clean-root containerd export through unchanged strict
verification. Populated transition34.051s, encrypted recovery62.533s, roles
24.112s/65permission denials, TLS23.141s and actualold rollback96.232s pass.
Old checkout/credentials/Compose/revision unchanged; missing/failed/stale
evidence and bad CA/hostname/plaintext reject; immutable routing/lock and0008
preservation pass. Mandatory cleanup succeeded. No VDS daemon/recovery change.

06-10-02 complete. Next06-10-03 requires explicit Create-a-merge-commit into
develop and separately selects release preparation/version. Suggested0.4.0
is a proposal only; not selected. No merge/release/deploy authority inferred.
Production remains reportedv0.3.1. Exact installed recovery d5fe2059... and
actualB2backup/restore remain dated09November. First genuine nightly observation
is owner-deferred;09/DEPL-02 pending. Phase10/15; no09/10SUMMARY/completion.

This supersedes older publication/CI-pending entries. Final local tracking
edits stay unpushed so greenPRhead remains exacta7d5dcb. Preserve/carry edits
through any approved integration/release; never discard or publish silently.
