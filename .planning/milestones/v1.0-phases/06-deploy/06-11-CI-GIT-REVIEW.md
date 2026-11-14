---
phase: 06-deploy
reviewed: 2026-11-10T08:34:07Z
depth: standard
diff_base: 77dcd44
review_head: c343f6b957fa1d695d357cd96cc280a69c0efc91
working_tree_included: false
files_reviewed: 2
files_reviewed_list:
  - deploy/tests/selected-cutover.py
  - deploy/tests/test-ci-ops.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# CI synthetic Git environment correction review

## Narrative Findings (AI reviewer)

No BLOCKER or WARNING findings in the bounded correction: committed RED
7d3f8a4 and the working tree fixture-only GIT_CONFIG_NOSYSTEM addition.

The extracted environment transformation requires exactly one existing clean
environment anchor. It adds GIT_CONFIG_NOSYSTEM=1 only to the relocated
synthetic entrypoint, alongside the existing private TMPDIR. Production
entrypoint source is unchanged. This neither trusts arbitrary repository
ownership nor expands Landlock access to runner configuration. Repository
local Git configuration remains active.

The regression executes the actual generated clean-environment block under
the existing Landlock boundary, using a separate denied synthetic system Git
configuration file. Its negative control reproduces Git rev-parse exiting
128 with Permission denied; its positive control executes rev-parse and reads
the repository-local marker. The production-source assertion prevents this
fixture setting silently becoming a production entrypoint change.

## Independent validation and limits

Independently ran `python3 deploy/tests/test-ci-ops.py FixtureGitIsolation -v`:
one test passed in 0.112 seconds. The negative control exited 128 and the
generated environment control exited zero. This was a filesystem-only test;
no Docker tests, private configuration reads, production changes or publication
were performed.

The published GitHub failure reportedly masks Git stderr behind “is not a git
checkout.” This review establishes a reproduced compatible failure mechanism,
not direct proof of that run's precise hidden stderr. Updated actual CI must
still confirm the correction on its runner. Other previously reported CI
successes are outside this review's independent verification scope.

## Final committed delta

Reviewed GREEN c343f6b, including the additional missing-repository negative.
After the generated environment succeeds and reads the local marker, the test
renames its private .git directory and requires the same actual Git invocation
to fail with “not a git repository.” This confirms that bypassing system config
does not bypass the checkout validity requirement. No additional findings.

Independently reran the focused regression against c343f6b: passed in 0.272
seconds, with control exits 128 (denied host config), zero (valid repository),
and one (missing .git). The broader eight-test result and real Docker proof
remain separately recorded by the root agent.
