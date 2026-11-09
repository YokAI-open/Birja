# Plan 06-11 task 01: local release 0.4.0 preparation

Prepared on 2026-11-09, from 12:56:03Z through 12:58:22Z (2m19s including
inspection and local verification). This completes only local task 06-11-01.
No 06-11 SUMMARY or phase completion is claimed; task 02 approval is pending.

## Authorization, base and candidate

Owner approved “Merge and prepare 0.4.0”. The parent reverified all six green
required checks at feature head `a7d5dcb01d40a916c9cbf9d6ff51525c70c50833`, actual
run `42618704350`, then merged PR26 with merge commit
`5ebf62b33b190aaf04a48b107a222e906fbf4c99`. The updated integration base includes
Phase 5 merge `8a76a68`; both ancestors were checked locally before preparation.
Feature closeout `0e0a6eb` was already carried into the local release branch.

- Branch: `release-0.4.0`.
- Preparation base: `0e0a6eb`.
- Candidate: `524080f5414b71de336239c008c3ddcecaefd3dc`.
- Task commit: `chore(06-11): Prepare local release 0.4.0 metadata`.
- No release upstream is configured. Two commits ahead of local origin/develop:
  carried closeout `0e0a6eb` and version candidate `524080f`; neither was pushed
  on this release branch by this task.
- Exact diff: four files, five version substitutions, from 0.3.1 to 0.4.0.
  No source, dependency, script, image or runtime configuration changes.

## Locked tooling and unchanged dependencies

Toolchain: uv 0.13.5; existing backend CPython 3.14.9 environment; Node v24.22.1;
npm 11.19.1. No tooling or dependency installation/upgrade was performed.

The initial offline `uv version` relock lacked resolver metadata in the isolated
temporary cache and failed without changing files. Used `uv version 0.4.0
--frozen --project backend`, changed only the corresponding virtual project
version in uv.lock, then validated with `uv sync --locked --offline` and
`uv lock --check --offline`. Both succeeded: 75 resolved records, 73 installed
packages checked. Used npm version 0.4.0 with `--no-git-tag-version`,
`--ignore-scripts`, `--offline` and the frontend prefix.

Parsed each TOML/JSON document before and after, normalized only the selected
project version fields and asserted exact structural equality to base
`0e0a6eb`. All resolved dependencies, constraints, URLs, integrity/artifact
hashes, platform metadata and scripts are unchanged. The proof is reproducible
with `/tmp/birja-release-version-proof.py` while retained locally.

| Inventory | Records | Unchanged canonical SHA-256 |
|---|---:|---|
| Backend locked distributions, excluding virtual project | 74 | `c1aed6af821462b2d8734a0a02dae4bf71f21028b3ba125be631256474a1f9ba` |
| Frontend locked packages, excluding root project | 638 | `223313f0a18c1802af373feb1644f0fb9ed30b6b18c746c406c2777240c0f184` |

| Candidate file | SHA-256 |
|---|---|
| backend/pyproject.toml | `326e66d083d35513b34190fe6e40a4070c5ac17e9e9660175bd0a2cbe7dc7a60` |
| backend/uv.lock | `ac547921306b90d312450b007325a785ebd7799f775e08ad856bcf4f7e0b7954` |
| frontend/package.json | `d7874d9924b8affb37bdfeb3a0a6aa0abb4ad069eae0c98d603d7d55beb25340` |
| frontend/package-lock.json | `66a61bfba12247c9e11eed0346c07e221105de6c05d23646900681dc51ed51ae` |

## Actual local validation

- `git diff --check`: passed.
- `python3 deploy/tests/test-ci-ops.py`: 7 passed in 0.121s.
- `bash deploy/tests/test-backup.sh`: 25 passed in 50.969s. Its actual approved
  restic local encryption/rotation fixture reports zero network requests/bytes;
  only isolated synthetic data was used.
- `bash deploy/tests/test-restore-safety.sh`: 4 passed in 1.249s.
- `uv sync --locked --offline --project backend`: passed, 75 resolved/73 checked.
- `uv lock --check --offline --project backend`: passed.
- Frontend npm lint, typecheck, metadata Prettier check and production build:
  passed. Vite 8.3.5 built successfully in 1.52s; generated outputs are ignored.
- Exact source diff reviewed; task commit contains only the four authorized
  version files and deletes no files.

This is metadata-only preparation, so no new mirror tests or application
RED/GREEN cycle were added. Full DB/application/browser/scanner suites were not
repeated; the fresh approved feature CI is historical evidence for the unchanged
implementation and is not substituted for release CI.

## Boundaries and next gate

No release push, main PR, tag, main merge, back-merge, deploy, production/private
inspection, B2 access, service change or image/recovery rebuild occurred. The
existing installed recovery payload and timer are unaffected; live recovery
freshness was not rechecked here. First calendar backup observation remains
owner-deferred and pending. Preserve the separate release publication approval
and actual exact-head release CI requirements.

Parent-owned STATE and .continue-here edits and preexisting untracked .claude/
were not staged or changed by this task. Evidence is left uncommitted for the
parent's independent review and next checkpoint record.
