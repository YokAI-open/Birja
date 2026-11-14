# Deferred Findings

## Existing npm low-severity advisory chain — 2026-10-30

05-07 `npm audit --audit-level=high` exited 0 and reported three low-severity findings: deepmerge prototype poisoning (GHSA-gcqx-w48m-w2h4), propagated through @shadcn/registry and shadcn. These are existing locked dependencies; Phase 5 changes no packages or locks. npm suggests a breaking shadcn downgrade, which is outside this phase. Track a reviewed dependency update separately. No high or critical dependency finding was reported.

## Existing synthetic JWT test-key warning — 2026-10-30

The full backend suite emits the existing PyJWT InsecureKeyLengthWarning for a synthetic SHA512 test. It also appeared before 05-07 and does not originate from Phase 5 production changes. All tests pass; no real key was inspected or changed. Consider updating that test fixture separately.
