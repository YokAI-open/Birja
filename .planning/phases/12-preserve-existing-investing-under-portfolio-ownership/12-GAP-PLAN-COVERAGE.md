# Phase12 gap-closure planning — November17

## Finding and execution boundary

The sole actionable gap is the final truth in12-VERIFICATION.md: current frozen
source must pass the actual complete strict security qualification. Existing
functional implementation, current/retained recovery, independent source
reviews and both owner checks are supported. Plans01–28 remain unchanged.

One bounded planning lookup of the [official reviewed advisory](https://github.com/advisories/GHSA-fc5q-39xc-vjpf)
still shows affected picomatch<=4.0.7 and **no patched version**. Saved registry
evidence in12-DEPENDENCY-REVIEW.md identifies latest4.0.7. No registry refresh,
audit retry, package installation or implementation test ran during planning.
No concrete install candidate is invented.

29–31 define a conditional repair route, not an immediately installable fix:

| Wave | Plan | Dependency | Result |
|---|---|---|---|
|19|29|28, existing qualification evidence|Bounded official candidate/complete-graph review and exact package approval. Stops as no_candidate while no legitimate patch exists.|
|20|30|29 completed with exact approval|Only approved manifest/lock repair, both vulnerable instances addressed, strict audit and complete frontend compatibility plus independent review.|
|21|31|30 successfully audited|Actual complete all-security and one new same-archive serial recovery, then independent final goal verification.|

29 cannot complete on a no_candidate disposition.30/31 cannot execute in that
state. No empty approval request, fake fixed version, downgrade, local fork,
omit-dev audit or weakened gate is planned. A replacement/framework migration
would require a separate concrete scope decision and replan. The audit's
automatic Vitest downgrade suggestion is not a remediation finding.

## Four-source coverage audit

These rows audit the whole preserved plan set; new gap plans supplement01–28.
IDs C01–C10 below are audit-local labels for the ten unnumbered locked decisions
in12-CONTEXT.md; they do not rewrite or invent source decision IDs.

| Source | Item | Plan coverage | Disposition |
|---|---|---|---|
|GOAL|Preserved actual investing with explicit owned portfolio|01–28;29–31 common qualification|Covered; closure remains blocked|
|REQ|PFUND-03 legacy actual money/no regrant|01–04,06–08,12–14,16–18,26–27,31|Covered, unchecked|
|REQ|PFIN-02 scoped unchanged execution|05,08,10–12,15,20–21,26–27,31|Covered, unchecked|
|REQ|PFIN-03 original-root exact retry|01,05,10–11,20–21,24,26–27,31|Covered, unchecked|
|REQ|PCTX-01 visible explicit name|09,14–15,19,22–28,31|Covered, unchecked|
|REQ|PVIEW-03 private root History/originals|14–15,20,22,25–28,31|Covered, unchecked|
|REQ|PSAFE-02 zero/one/many identity/legacy refusal|07–09,15,19,22–23,26–28,31|Covered, unchecked|
|REQ|PSAFE-03 least privilege/TLS/immutable lineage|01–07,11–13,16–18,26–27;29–31 common strict qualification|Covered, unchecked|
|RESEARCH|Compound lineage, finite migration authority and schema admission|01–07,16; retained by31|Covered, no new schema work|
|RESEARCH|Exact-root writers and global journal/terminal reconstruction|08,10–13; retained by31|Covered, no economic change|
|RESEARCH|Identity/API/browser target contracts and privacy|08–09,14–15,19–26; retained by30–31|Covered, no public management feature|
|RESEARCH|Current/retained exact roles/TLS/recovery/source parity|16–18,26–27; fresh31|Covered, not postponed to15|
|RESEARCH|Package legitimacy / strict gates|Original no-new-package scope supplemented explicitly by29–31 candidate review, exact approval and qualification|Covered, no implicit install authorization|
|CONTEXT|C01 existing design, research and checked plans|Existing RESEARCH/UI-SPEC/PATTERNS and01–28; gap plans preserve accepted UI|Covered|
|CONTEXT|C02 original balances/baseline/history, My portfolio, no grant|01–08,12–18,27;31 regression|Covered|
|CONTEXT|C03 explicit owned target/name, no fallback|08–15,19–26;30–31 regression|Covered|
|CONTEXT|C04 execution/fees/freshness/valuation/History and stock gates unchanged|10–15,20–27;30–31 regression|Covered|
|CONTEXT|C05 identity zero/one/many, no recreation/regrant|07–09,15,19,23,26–28;31|Covered|
|CONTEXT|C06 restricted roles/TLS/immutable evidence/Decimal|01–07,11–18,27;31|Covered|
|CONTEXT|C07 each revision exact recovery and honest refusal|04–07,16–18,26–27;31|Covered|
|CONTEXT|C08 future terminal lifecycle coherent in foundation|02–07,12–18,26–27;31 preserves|Covered; public deletion remains14|
|CONTEXT|C09 name/create/description/overview13, deletion14|All plans retain boundary|Covered as explicit exclusion|
|CONTEXT|C10 local-only planning, no provider/prod/install/publication permission|29 approval before any30 install; no runtime/publication in planning|Covered|

No functional requirement is dropped or duplicated as a new implementation
task. Deferred Phase7 live acceptance and Phases13–15 features remain excluded.
The consumed November16 provider campaign is not repeated.

## Validation mapping and scope limits

| Task | Automated evidence | Human/conditional gate |
|---|---|---|
|29-01|Unchanged project manifest/lock plus candidate receipt structural validation|No candidate stops; no assertion of patched behavior|
|29-02|Review/receipt hashes|Exact explicit owner package approval; cannot auto-approve|
|30-01|Full installed tree and unchanged npm audit HIGH|Actual reviewed candidate only; stop on HIGH|
|30-02|Whole existing frontend lint/types/format/coverage/build|Separate code/security review; no source widening|
|31-01|Actual complete unchanged all-security|No assembly of separate diagnostics into pass|
|31-02|Actual complete seven-stage one-archive recovery|Final independent goal verification follows|

Long frontend coverage/build and complete qualification/recovery are explicit
sampling-time exceptions. Existing12-VALIDATION.md remains the historical
01–28 plan matrix; this table supplements it without relabelling old results.
No new product UI is designed, so accepted UI contract and both exact human
responses remain. Dependency/build changes must be disclosed in render-input
provenance; new meaningful appearance changes require actual review evidence.

The package legitimacy addendum and exact artifact hashes are29 execution
outputs, not existing candidate evidence. Before they exist and approval is
recorded,30 is not installation authority. No new requirement or completed
phase is created by this planning document.

## Post-planning deterministic checks

The SDK decision-coverage query passed by skipping: the existing context has
no machine-trackable decision IDs. The ten locked prose decisions are mapped
explicitly above. Legacy gap-analysis reports7/28 covered because it scans the
entire milestone against this phase alone: the21 uncovered IDs are assigned
to Phases13–15, not dropped Phase12 requirements. All seven actual Phase12
IDs are covered; no requirement reassignment or scope expansion is needed.
The existing31-plan dependency graph and new task structure remain checked;
phase status stays blocked despite completed gap planning.

Revision1 adds explicit read_first inputs and verifiable acceptance_criteria to
all six tasks, including conditional receipt/hash checks and actual process
exit/cleanup requirements. It does not alter actions, scope, approval or the
no_candidate stopping boundary.
