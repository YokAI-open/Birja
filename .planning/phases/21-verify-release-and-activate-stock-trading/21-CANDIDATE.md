# Phase 21 local candidate evidence

## Source and validation status

This receipt records local validation of the v1.4 source. Hosted CI, the
release image and the live stock trade round trip are pending.

| Source | Git commit | Git root tree | Relevant input |
|---|---|---|---|
| Integrated code and tests | `bb81292b143bf8b8f7a91550e59e4fe83812fa72` | `52d32e2d3d33463b402113f354b47f859359f45c` | Application tree `93638e56ad2a02b79dccdae53c26280e5df9b7a8`. Backend test tree `77b770bfd54f4dd83285ccd22c02d6d8ed1784c2`. |
| Guarded catalog browser and frontend | `762629f1105c3688b72fb7a10239f3a992cae088` | `f46c3f2ad4e0f00a2cad1b82999c5586389a449e` | Browser input SHA-256 `dce598fe4c39ee6d0617e2a21ab93f3bf56a2b2560e8b7fb1af8778a41a42674`. Frontend tree `f6de02538bec5408c32e71dc828c9573e431f4e6`. |
| Frontend coverage, lint, typing, formatting and build | `762629f1105c3688b72fb7a10239f3a992cae088` | `f46c3f2ad4e0f00a2cad1b82999c5586389a449e` | Source, lock and build input SHA-256 `0cbd592fe8fc0227935de28bdc318dae7c087235c83bec89d611eb1eeafabda6`. |
| Action-admission regression | `a69ddc9b7b6fd407de179d3b699ba7178f69bd22` | `e6f3800eed9ad4eff557b4b469bf4f54d725ab7e` | Backend tree `0da23cc0d1f5b49402fffe4e271fd7a45a5be941`, `backend/app` tree `93638e56ad2a02b79dccdae53c26280e5df9b7a8`. |

The browser inputs include application source, fixture and spec source,
guarded runner and Compose configuration, and dependency manifests and locks.
Changes confined to other backend test files and planning records preserve
these inputs. Changes to application source require checking the affected
evidence again.

## Guarded catalog browser

`python3 deploy/tests/run-stock-browser.py --suite catalog` exited 0. All
seven cases passed in 132.9 seconds on the committed inputs, with successful
owned resource cleanup. The sanitized runner log SHA-256 is
`29bf08bf11a7ef77668b24c02717fb078a0cf3f44f147d976a0a8a085cbcd40a`
and the browser detail log SHA-256 is
`deb9067fffd87977167546dc0ae2177b3c1168f01eb092fdb4449c30f52d2519`.
The browser uses disposable services, synthetic stock quotes and the normal
sign-in, portfolio and order interfaces.

The local build produced backend manifest digest
`sha256:6edbc6e2d4da20e8a88a465b458a041fbce3fbad7b6b8fe9863fd4ea58eb6282`
and scheduler manifest digest
`sha256:ed14dad0e90fce6de267eb4c35c8eec11bf419d657b95cfa8e8cccc95556c25a`.
Release image publication and scanning remain in hosted CI.

| Journey | Candidate evidence |
|---|---|
| Search and select | Company name, ticker and former alias searches preserve share class and exchange. Keyboard selection issues one stock quote request. Focus reaches the detail heading and returns to the result after going back. |
| Select a portfolio and trade | Switching preserves exact listing and portfolio. The promoted synthetic stock sits outside the initial 20. Buying two shares after a quote changes requires reconfirmation, records $208.25 basis and leaves $9,791.75 cash. Selling two on the bid leaves $9,993.75 and no holding. The scoped API verifies ask and bid execution directly. |
| Receipt and History | Lost confirmation response recovers the original order result. Two fills appear in private History. A second account cannot see the portfolio or trade context. A subsequent listing replacement leaves the original History link tied to the prior issue. |
| Market closed, halt, stale quote | Markets and the ticket show the verified closed mark and countdown. The mark survives an empty cache, expires at the permitted age and leaves order submission unavailable. Synthetic halt and stale responses show specific reasons and omit order controls. The guarded quote fixture crosses the 120-second source age boundary. |
| Mixed holdings | Ordinary dividend and split reconcile the mixed portfolio. Incomplete totals preserve known cash and unaffected holdings, and crypto stays usable during stock provider interruption. |
| Reflow | 390 and 640 pixel viewports meet overflow assertions on the covered paths. Native desktop 200% zoom remains unmeasured for this run. |

See [browser acceptance contract](21-UI-SPEC.md) and
[guarded browser specification](../../../frontend/e2e/stock-catalog.spec.ts).

## Local quality and operations

| Check | Result |
|---|---|
| Frontend lint, typing, formatting, coverage and production build | Exit 0 for each. 1,371 tests across 61 files. 95.18% statements, 92.29% branches, 97.36% functions and 97.16% lines. Build reported the 584.60 kB application chunk warning. |
| Frontend audit policy contract | `node --test deploy/tests/test-frontend-audit.mjs` exited 0. |
| Backend lint, formatting and typing | Ruff lint and formatting passed, with 311 formatted files. Mypy passed with 130 source files. All three pure checks of the critical coverage configuration passed. |
| Action-admission regression | Exit 0. An operator review rolled back, its exact digest applied, and the restricted scheduler consumed the admitted action policy. An incomplete policy and wrong symbol were refused. Test receipt SHA-256 `29a5f49b329fd9b42f5965a0cd45f41faee3221396f7f6d705ef2316aedfd193`. |
| Portable operations contracts | Exit 0 for 113 CI, 44 validation-runner, 19 recovery and 17 image contracts. Deploy compatibility shell contracts exited 0. |
| Recovery rehearsal | Plan 03 bound the cold, upgraded, fresh, retained 0025 and TLS stages to the exact tested archive. Verified original 0023 reopening before writes and same successor recovery after 0026 writes. [Archive, image and per-stage receipts](21-03-SUMMARY.md). |
| Full hosted operations graph and scans | Pending. The local Compose 5.0.0 workstation differs from the supported graph's Compose 5.7.0. The hosted dependency audits, five strict image scans, browser gate and recovery graph remain required. [CI definitions](../../../.github/workflows/ci.yml). |

## Whole backend and independent review

The whole-backend baseline measured 3,909 cases against the `a69ddc9`
backend source and tests. `pytest --cov=app --cov-branch --cov-fail-under=80`
exited 1 in 1:56:11. It reported 3,810 passed, 57 failed, 42 setup errors,
and 93.12% overall coverage. The failed test exit leaves the whole suite
gate open. Baseline log SHA-256
`4d6d93a2e20df71795e21d412326e8e9900307c37b574ed25ba63b9078c686c8`,
coverage database SHA-256
`bfd4c39789b8cc146e68928810d4b79f0804dde687f00cab07243e158bb65618`.

The exact CI critical-module report exited 2 at 97.80%. It measured 100
missing statements and 86 missing branch arcs. Report SHA-256
`7c41b88d6e57c01a6d0f34ff5ee8a7e371cd7dacb1c1fca97713c23624c4109c`.
The coverage requirements remain 80% overall and 100% for the existing
critical module list.

The baseline used a separately named disposable Compose project. Existing
Docker-backed tests expected `birja-test`, causing setup errors. Other
failures identified stale retained schema callers, prepared statements, and
route, History projection and SQL routine inventory assertions. The focused
reruns used the same test images and ports under the Compose project name
defined by CI.

| Serial backend measurement | Exit and observation | Log SHA-256 |
|---|---|---|
| All 99 original failed or errored cases | Exit 1. 97 passed. Both unchanged late-guard status sequence checks needed to account for the existing healthy same-price rebuild. | `937a196eb9e0635a22980973f6f98ffe066a1dfd1d8e9a429969a9d71c5515d9` |
| First 16 case gap and sequence check | Exit 1. 13 passed. Two diagnostic assertions measured the sequence on the bounded retry. One valuation fixture changed a field outside the validated mapping payload. | `46ec325f62ea5b5ff77a4a0cf45997ffd7b768903513753e4f4ce48952eaa5a5` |
| Sequence, valuation and catalog action follow-up | Exit 0. 10 passed. The original two sequence cases passed with an independently committed source change, refusal of the old evidence, one authorized rebuild at the original price and exact one-fill accounting. | `bb0037a2011ff424f7ec7084f84bcb0bf425ec696259b1dfb93df4907b62d228` |
| Action effects and valuation refusal | Exit 0. 14 passed, including three cases that roll back effects when monitoring proof disappears. | `438e2475a9e39490151fc0801dbed99c1ec3cc7f483c078eb8c926f03c8fc44b` |
| Residual stock monitoring | Exit 1. Seven passed. The replay limit fixture used a declared content length and an empty body. | `4f55572221e69fe1c2b0cf918f85a7e3df842e6f4958356d709149b7145a1b09` |
| Replay size and preserved monitoring lease | Exit 0. Passed with a bounded synthetic body one byte over the limit. | `98b4a24a69ef9f4de4086a86b767bdfcea286226858d71ab9d0e0396ed7e608b` |

The final collection has 3,941 cases. The original failed and errored cases
and the 32 newly collected cases have passing focused receipts. Unchanged
cases retain the whole-backend baseline evidence. The aggregate used the
same backend application tree for every measured path and retained the raw
reports from failed invocations. The aggregate coverage database SHA-256 is
`4cdfd6b17fe85b157155b256bfa1359d67bfff5bf64075cc50819182f09506e6`.

- The overall coverage command exited 0 at 94.41%, with log SHA-256
  `f96bcbe8c111759711e3232a559a70ded82939cce397effcbd6cbe6bad519d69`.
- The exact CI critical command exited 0 at 100%, with zero missing
  statements or branches across 6,377 statements and 2,082 branch arcs and
  log SHA-256 `77fedc32cfb593d38a65f8e251936143206ed8920c22d747feccab61c84b2ff0`.

Local qualification uses the whole baseline, passing affected reruns and
unchanged application-byte coverage. There was no fresh whole-suite
invocation on the integrated test tree. The exact hosted whole run, other
hosted acceptance gates and [independent review](21-REVIEW.md) remain
required for this fingerprinted source. The browser and both disposable
backend Compose projects completed their owned resource cleanup.
