# PR31 publication receipt

Published through ed37d69e89d544e03e5b1c5f7c0817a35b1a7799 under explicit
owner “Publish and finish CI” authorization. PR#31 is OPEN/MERGEABLE into develop;
all six required hosted jobs passed in run43588776865 on2026-11-14.
https://github.com/YokAI-open/Birja/pull/31
https://github.com/YokAI-open/Birja/actions/runs/43588776865

The PRdescription records repairs, exact tested head and green hosted result.
Fresh complete serial recovery passed at this head; earlier local qualifications
remain historical. See resolved/pr31-ci-failures.md for receipt/log/archive hashes.
No merge, provider activation or deployment. This receipt is committed locally
without advancing the tested PRhead or triggering redundant CI.

## Historical publication preparation

# PR31 publication preparation

All three hosted failure causes have local reviewed fixes on
`feature/v1.1-stock-planning`. No push, PR edit or merge has been performed.
Code commits: `d855a0f` (verified cold image preparation and OTEL contract),
`a0feb5c` (exact approved DNS lock and image/legacy package contracts).
Supporting local evidence commits: `751afd1`, `0dd227e` and this document's commit.
Use `git log --oneline @{u}..HEAD` for the exact publication range and current
HEAD; the owner must approve publication separately from the package change.

Suggested follow-up text for PR31's existing description:

> Repairs the three hosted CI failures: upgrades only owner-approved
> dnspython2.9.0→2.9.2 for the WKS denial-of-service advisory; authenticates exact
> approved DNS/OTEL records while preserving all other package/calendar artifacts;
> and imports/binds the verified recovery image before cold-run Compose tests.
> Wrong existing aliases and tampered image archives still refuse before import.
>
> Local validation:2557backend tests,99.87%overall and47critical modules100%;
> upstream211tests/71subtests plus explicit advisoryRED/GREEN (31optional/network
> skips);15image/16CI/7selected and real retained-installer contracts;5rebuilt-image
> smoke tests; unrestricted dependency audit and all5strict HIGH/CRITICAL scans
> includingunfixed pass. Original cold-startRED/GREEN and24realPostgreSQL recovery
> tests pass. Complete native/Python inventories show only the approved DNSdelta.
> Independent code/security reviews have0active findings; ownedresources cleaned.
>
> Earlier Phase11 serial recovery evidence remains source-qualified historical
> proof, not a fresh complete campaign at this head. Financial application,
> schema/authority, retainedCORE and frontend bytes are unchanged. Fresh hosted
> CI awaits publication; production/provider/live activation remain separate.

Full raw-log/source/image/cleanup provenance is in `pr31-LOCAL-PROOF.md` and its
private receipt. This draft is prepared only; no external write is authorized.
