# Phase 25 integrated candidate

The initial publication found 16 browser failures. The corrected candidate
passed the full browser suite locally and all six hosted jobs on 2026-11-26.
[Successful hosted run](https://github.com/YokAI-open/Birja/actions/runs/45900726488)

| Identity | Value |
|---|---|
| Tested runtime commit | `0087e99b80231e103eb70deceedc830475382b11` |
| Tested runtime tree | `11d0fc74e396126800930963b532be2b4de4b397` |
| Tested backend tree | `a0abf5be7a78b5a5b1a7328199c4d5c4db0f535b` |
| Backend application tree | `f7574a4807f5447664d24202094f03bb7e77f7d0` |
| Approved prototype SHA-256 | `5e361ad60eb0915add082791fd4a8bc2862ec607712b04e00a15d2c53f2b143e` |
| Publication destination | `origin/feature/milestone-v1.5-market-charts`, pull request into `develop` |

The identities above describe the initial local proof. The initial PR
publication and the corrective local candidate have separate identities
below. The new publication checkpoint uses the commit and tree read from
the clean branch after recording the corrective proof.

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

Historical feed rights, representative coverage and measured limits stay
open under CHART-04. Release and deployment have their own authorization.
[Phase 23 source qualification](../23-show-historical-market-prices/23-SOURCE-QUALIFICATION.md)

## First publication

The owner approved the exact candidate `622459e14271e20e357696e106566cf5e6654d3c`
with tree `30abd60e9377f2dbb090620623529a158ec59d37` on November 26, 2026.
The exact push opened [PR #55](https://github.com/YokAI-open/Birja/pull/55)
into `develop`. GitHub tested the merge commit
`bd2753a5e8823ecc8b757f194900bcc39480e060` with tree
`1643b5c3ae49c9f1a4865b5ccee07a9909dad0b2` and first parent
`e0338727633eac041893481d28084b8623ebf80d`. The updated base contributed
four audit and scan files covering retirement of a withdrawn advisory.
[First hosted run](https://github.com/YokAI-open/Birja/actions/runs/45892960908)

The full browser run recorded 97 passes, 16 failures and one expected
deployed-site CSP skip. Six stock tests matched both the chart and live
status. Six portfolio layout tests expected a 48px chooser, while the
approved and measured chooser is 44px. The expired-valuation test still
looked for the previous card layout. Two narrow trade layouts overflowed
with a long unbroken company name. One catalog test selected the old
Markets control before the destination chooser mounted.

The operations job finished the seven authenticated stages in 24m 04s.
The downloaded archive passed the checksum and bundle verification.
The receipt's complete stage sequence, tested commit, tree and backend
image source matched the GitHub checkout. Archive SHA-256
`a1d4ed7412599da160c7d8710de21adf85acd5d002201f912304f5dbedc40080`.
Receipt SHA-256
`175cc7850a7bd1fcd4a0028ddcf1361a9a5bc020923d7e992f281cb61a2cbca6`.
This is recovery evidence from the first checkout. FLOW-04 requires all
six checks and the authenticated receipt on the same successful run.
[Verified artifact](https://github.com/YokAI-open/Birja/actions/runs/45892960908#artifacts)

## Corrective candidate

The repaired runtime commit is
`8fc6ba8ec4f935f4ce18ec29f9800474c14161a7` with tree
`d88aee9905ea1a632d5e250fb0c434d75ce4294e`.
The only application change wraps the trade heading's company text in its
available width. The other changes update the existing stock and portfolio
tests. The exact economic, ownership, freshness, retained order and viewport
checks still run. The independent recheck found no issues with the changes.

Linter, formatting, TypeScript and production build passed. All 1,441
frontend tests passed with 94.56% statement and 92.37% branch coverage.
The exact unfiltered guarded Chromium suite ran 114 cases in 22m 05s.
All 113 runnable cases passed, including the 16 hosted failures. The
deployed-site CSP check kept its expected skip. Container, network and
volume cleanup checks were empty. Browser log SHA-256
`32d5c6535e3a9db3b772b179dfcb21a47354ac70d25c83249dc801df47298071`.
Guard log SHA-256
`3660cd457033031a1b3cf4e43343a20ccdc1c8c244cd99acba0c19a8012c9e7b`.

The owner approved continuation for the exact corrective head. The
fast-forward updated PR #55 with `a3b84647735803cdcc392d2bcaf8141b5a83e64f`.

## Successful hosted candidate

| Evidence | Exact identity |
|---|---|
| Feature commit | `a3b84647735803cdcc392d2bcaf8141b5a83e64f` |
| Feature tree | `51724c2be270bd92020f5afe77e0969823fe9237` |
| Develop parent | `e0338727633eac041893481d28084b8623ebf80d` |
| Actual CI checkout and receipt source | `da8ded9f08afd6e17cf46260ac7a036383dcc3f1` |
| Actual CI tree | `aec41f80d7bfdeebb4a2c08bf497ab685fa77e02` |
| Backend app tree | `f7574a4807f5447664d24202094f03bb7e77f7d0` |
| Backend context SHA-256 | `d1d8e0b8acbaf890747498107f099408244cc1a437e4a1e81137a6a76f1f8b2e` |
| Verified recovery archive SHA-256 | `a1d4ed7412599da160c7d8710de21adf85acd5d002201f912304f5dbedc40080` |
| Verified recovery receipt SHA-256 | `fc91f736333a76b23b1fa6192876df14f98f07978e8412dffea532af72629bb8` |

| Check | Conclusion | Run evidence |
|---|---|---|
| `backend` | Passed | [Job](https://github.com/YokAI-open/Birja/actions/runs/45900726488/job/140185557199) |
| `frontend` | Passed | [Job](https://github.com/YokAI-open/Birja/actions/runs/45900726488/job/140185557034) |
| `image` | Passed | [Job](https://github.com/YokAI-open/Birja/actions/runs/45900726488/job/140185556715) |
| `e2e` | Passed | [Job](https://github.com/YokAI-open/Birja/actions/runs/45900726488/job/140185557011) |
| `ops` | Passed | [Job](https://github.com/YokAI-open/Birja/actions/runs/45900726488/job/140185557047) |
| `ci-pass` | Passed | [Job](https://github.com/YokAI-open/Birja/actions/runs/45900726488/job/140206017333) |

The recovery artifact came from run `45900726488`, attempt
`1`. The workflow finished in 58m 14s and the
serial recovery ran in 25m 04s. The verified stage order was `image-transition`, `retained-roundtrip`, `current0028-cold`, `roles`, `tls-upgraded`, `tls-fresh`, `selected-rollback`.
All seven stages were recorded as authenticated. The checksum, existing
bundle verifier, merge parents, source and tree, backend context, and
current image source binding passed. [Recovery artifact](https://github.com/YokAI-open/Birja/actions/runs/45900726488#artifacts)

CHART-04 live historical data qualification remains open. Candidate
qualification is evidence for the feature branch PR.
