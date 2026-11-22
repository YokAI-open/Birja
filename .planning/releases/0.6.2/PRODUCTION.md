# Actual production rollout

Production https://birja.nist.one runs softwarev0.6.2 at main
`7d236e4534e575ceb54441cae1729d34a0b87f4f`, schema0023. Backend and exactly one scheduler are
healthy; nginx serves `/var/www/birja/releases/7d236e4-20261122T220234Z`.
The successful deployment record matches the checkout; pending marker is absent.
Previous publication alone was not a completed rollout.

## Preserved data and guarded compatibility

The original0008→0023 migration had already completed before the permission
refusal. Original accounts/cash/starting baselines, holdings/basis, immutable
trades and ownership associations were compared before and after canonical
bootstrap and again immediately after app startup:unchanged. No financial
repair, new starting-cash grant, liquidation, live restore, volume copy or index
repair occurred; the canonical role normalization is described below.

Both immutable HBA profiles, exact source, exclusive operation lock, stopped
writers, TLS, collation and exact paired inherited permission state were
verified. The unmodified qualified full administrator bootstrap transaction
normalized to canonical0023 permissions. A fresh canonical backup and exact
isolated restore passed BEFORE the supported datastore rebind/startup.
PostgreSQL18.7 and Redis use the original selected live volumes. Prior tools,
release assets and immutable operations profiles remain retained. The new
MANIFEST is `2d16694ea7909d3290d2f6bb89bb728ddf1f3f5da1eed6afd2a602963791f8f8`.

Pre-start canonical snapshot/exact restore:
`0ec815de9eb5dc97f8886b965638e7f552d97852419d1643ad942a53097162b0`.
Its source release truthfully remained the last successful46d24c8 while offline,
with source revision0023. No successful deploy log was fabricated.

After actual successful startup, backup configuration selected the actual main
SHA. Post-rollout snapshot/exact isolated restore:
`eca3812ac617350be6d69f890fd3a5bf50249a57061d645d6e7ec9983322e08e`,
revision0023, source main7d236e4, completed2026-11-22T22:06:18UTC.
Both use qualified recovery bundle5c7d59ff9b56db17e5e5860ed6fda1c20367b8b7914cb22ee2dadd6fada7e7e2.
Existing bounded free-tier policy, timer and credentials are unchanged.

## Operator verification amendment and honest results

The installed immutable smoke script returned40/41:its client-address assertion
still posts to obsolete `/api/v1/auth/verify-code`, which intentionally returns409
without entering OTP verification. This failed result remains retained, not
rewritten as a pass. The current frontend uses `/api/v2/auth/verify-code`.

For actual current-release verification the parent prepared an exact copy with
ONLY that endpoint changed to v2. Independent bounded review found0blockers and
one nonblocking maintained-script follow-up. Bash syntax and exact one-change
comparison pass. No inputs/assertions were expanded or removed, and no product
or immutable installed file was changed. The adapted operator command passed
all41origin checks, including current OTP client-address handling. The unchanged
public command passed9/9. This explicit protocol amendment preserves the full
intended check; it does not claim the historical installed40/41run passed.

All root-private logs/receipts are under
`/tmp/birja-hotfix-0.6.2-production/`. Initial local operator handoff droppedFD9;
the installer refused before mutation. PassingFD9fixed that operator error.
A later synchronization assertion correctly detected refreshed quota observation
fields; only those measured fields differed, policy was verified unchanged,
and actual released identity was synchronized before the post-rollout backup.
Neither refusal was waived or called successful.

## Private recovery export

`/tmp/birja-hotfix-0.6.2-production/birja-offserver-recovery-0.6.2.7z`:
27members,137539901bytes,root-owned0600in0700directory. Includes productionenv,
existing recovery/B2 credentials, roles/bindings/TLS/CA and the qualified public
tool archive. Existing restic password reused. Full extraction/member hashes
verified; temporary plaintext staging removed. Secret archive is never committed
or uploaded to GitHub. Owner can replace the prior off-server export with it.

Stock data and corporate actions are explicitlyfalse in actual running settings.
Stock-status transport remains a separate engineering follow-up. No provider
activation, new dependency, real-data restore or milestone audit/archive occurred.
