# Phase 25 integrated candidate

Local checks passed on November 26, 2026. The remaining Phase 25 work is
publication approval and hosted verification.

| Identity | Value |
|---|---|
| Tested runtime commit | `0087e99b80231e103eb70deceedc830475382b11` |
| Tested runtime tree | `11d0fc74e396126800930963b532be2b4de4b397` |
| Tested backend tree | `a0abf5be7a78b5a5b1a7328199c4d5c4db0f535b` |
| Backend application tree | `f7574a4807f5447664d24202094f03bb7e77f7d0` |
| Approved prototype SHA-256 | `5e361ad60eb0915add082791fd4a8bc2862ec607712b04e00a15d2c53f2b143e` |
| Publication destination | `origin/feature/milestone-v1.5-market-charts`, pull request into `develop` |

The publication checkpoint uses the commit and tree read from the clean
branch after committing this record. Commits after the tested runtime carry
only Phase 25 planning and evidence. The approved feature SHA and the
actual hosted checkout SHA will both be recorded with the hosted result.

## Local evidence

| Check | Result and source binding |
|---|---|
| History API and PostgreSQL | 316 passed in 210.86s. The three critical History modules reached 100% statements and branches (350 statements, 154 branches). Ruff and mypy passed. Log SHA-256 `5ccf82c500d87d511f3ca4461194c8561f88d775945834e209c757caf544a241`. [History backend summary](25-02-SUMMARY.md) |
| Trade, session and market history APIs | 108 guarded cases passed in 121.10s. Git confirms the backend tree and test Compose file are identical between `702249b` and the tested runtime. Log SHA-256 `14f189ef065f881041849e4c31ccef440d448529e3be5dae40ae500d3b4270eb`. |
| Frontend | 1,441 tests across 66 files. 94.58% statement and 92.37% branch coverage. Lint, types, format and production build passed. Log SHA-256 `c063d8df36731570943d27ce17ab7386fb68f1772d484d506ff6af04a1968406`. |
| Chromium and visuals | All 18 selected cases passed in 246.6 seconds using real app routes with disposable data. Six app and approved prototype pairs passed integrity and dimension checks. The test exercised 320px and 200% CSS text enlargement. Browser log SHA-256 `9acd66cf5a22ef05c83ea2021a61a7bbe7e2e50c05a2acc57494d1a719b7041b`. [Browser receipt](25-BROWSER-RECEIPT.md) |
| CI contracts | 115 offline tests passed. The selector dry run returned all seven recovery stages in order. The CI workflow differs in four timing values, including a 65-minute serial allowance and matching UTC horizon. [CI timing summary](25-06-SUMMARY.md) |
| Code review | All identified items were resolved and rechecked. [Code review](25-REVIEW.md) |

FLOW-01, FLOW-02 and FLOW-03 have passing local evidence. FLOW-04 requires
the hosted run and its authenticated recovery receipt.

## Recovery evidence

Phase 24 ran the seven encrypted recovery stages and the receipt verifier
on `74e852d7124b89bdbc5490af04e35118f0f88f62` in 56m 19s. The bound
archive SHA-256 is
`ecbb73237caf9e02b6d7678f1873e09e0e90b83b1d26ef8bf534880bfe1d7046`.
The authenticated status SHA-256 is
`1a98aef2aa50e31197b94d05c5afce4a12cc4b9bf47552f8b9eb4d2aff0bc97b`.
[Phase 24 recovery receipt](../24-compare-portfolio-performance/24-RECOVERY-RECEIPT.md)

The Phase 25 input diff preserves schema 0028, migration bytes, package
locks, Dockerfiles, Compose definitions, recovery tooling and stage graph,
and database role and storage contracts. The application tree differs in
three History modules for optional filters before pagination and a
filter-bound cursor. The guarded tests covered the default mixed and legacy
responses and the new filtered route. The browser-only dividend fixture
extends its synthetic allowlist for COST and KO. The CI changes affect time
budgets and offline contract assertions.

Reuse Phase 24's results for those unchanged recovery inputs and their local
timing. The verified hosted archive and seven authenticated stages must
come from Phase 25's actual CI checkout, including the merge ref when the
workflow runs on a pull request.

## Hosted verification

| Evidence | Status |
|---|---|
| Exact candidate push and pull request | Awaiting approval |
| `backend`, `frontend`, `image`, `e2e`, `ops` and `ci-pass` | Pending hosted run |
| Checked-out source and tree, verified archive and authenticated status | Pending hosted receipt |

Historical feed rights, representative coverage and measured limits stay
open under CHART-04. Release and deployment have their own authorization.
[Phase 23 source qualification](../23-show-historical-market-prices/23-SOURCE-QUALIFICATION.md)
