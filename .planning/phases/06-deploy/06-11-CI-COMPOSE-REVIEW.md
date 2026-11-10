---
phase: 06-deploy
reviewed: 2026-11-10T09:00:24Z
depth: standard
diff_base: 38eb25c
review_head: d7f0cf566c21b6c454896fb388ca5375c4e61904
files_reviewed: 2
files_reviewed_list:
  - .github/workflows/ci.yml
  - deploy/tests/test-ci-ops.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# CI Compose retained-Dockerfile correction review

## Narrative Findings (AI reviewer)

No BLOCKER or WARNING findings in the bounded RED b31f3dd / GREEN d7f0cf5
change. Only the operations job's ephemeral tooling installation and its CI
contract change. Production tooling, application source, image pins, retained
deployment source and independent recovery implementation are unchanged.

The operations job installs the exact Compose plugin package version
5.7.0-1~ubuntu.24.04~noble through the existing Docker signed apt source.
Before fixture builds, it verifies the actually selected plugin reports 5.7.0
under the same clean-root environment shape used by recovery commands. A
missing, shadowed or unexpected version fails rather than silently continuing.

The targeted contract checks the package pin, installation argument, actual
version assertion and its placement before fixture builds. It also rejects
the proposed global filesystem-entitlement bypass variable, disabling Bake,
and wildcard filesystem grants in the operations job.

Reviewed the official [Compose 5.7.0 implementation](https://raw.githubusercontent.com/docker/compose/v5.7.0/pkg/compose/build_bake.go):
localBuildPaths includes the resolved Dockerfile path, and bakeArgs emits
individual fs.read permissions for those paths. This supports using that
version for the immutable Dockerfile outside the mutable application context
without globally disabling filesystem checks. The workflow itself introduces
no wildcard filesystem consent.

## Independent validation and limits

Independently ran the new focused contract
`CI.test_ops_pins_compose_with_explicit_retained_dockerfile_consent`: passed.
Reviewed the full bounded workflow/test delta and the official source above.

No Docker tests, private configuration reads, host package changes, commits
or publication were performed by this reviewer. Package availability/hash
verification and the supplied-archive proof are separately performed and
recorded by the root agent; this review does not claim to have independently
verified their results. Local proof completion and updated actual GitHub CI
remain necessary evidence before treating the CI failure as resolved.
