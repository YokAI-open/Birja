---
phase: 12-preserve-existing-investing-under-portfolio-ownership
plan: "31"
task: "12-31-02"
status: passed
verified: 2026-11-17
source_commit: 4b4320b4cc373268a8d598612a563cd5ef199700
source_tree: 9d19e531ca4b2ededf133203ca74a83ff39ba5e7
---

# Phase 12 Exact Recovery Proof

## Plan31 fresh complete recovery — current proof

The actual complete command `python3 deploy/tests/run-portfolio-validation.py
--suite recovery` passed at the same frozen source as the actual complete
security command:2026-11-17T22:08:32.272997Z–22:53:26.964687Z, exit0,
**2694.692seconds**. It ran only after the security process succeeded and
cleaned its owned resources. No campaigns ran concurrently.

One fresh exclusively created archive was authenticated throughout:
`/tmp/birja-phase12-proof/recovery.tar.gz`,196689920bytes, SHA256
**d253bc51b876c7d629ee246ee47bd57274a5d9333e71318e11fcef586cff26be**.
The .gz filename still holds strict uncompressed USTAR; no repackage occurred.
Final actual marker is
`same_archive_final_ci=true sha256=d253bc51b876c7d629ee246ee47bd57274a5d9333e71318e11fcef586cff26be`.

| Serial stage | Actual result |
|---|---|
|Image transition|PASS38.391s; original/clone ownership and collation drift, reindex-before-refresh, logical restore and abort preservation|
|Retained0007–0014 roundtrips|PASS759.875s; exact rows/schema/sequences/identities, stock/dividend saved receipts, corruption refusals and quarantine|
|Current0017 encrypted cold restore|PASS actual declared runtime; source destroyed, separate restore, immutable-before oracle and restricted verified-TLS/quarantine|
|Roles|PASS318.752s plus3.954ssetup;63denials/12input-lock refusals, fresh/populated authority parity|
|Upgraded TLS|PASS273.142s plus13.526ssetup; actual financial consumers, transport refusal, isolation and renewal|
|Fresh TLS|PASS275.741s plus14.919ssetup; same actual consumers, exact upgraded/fresh authority parity at final guard|
|Selected rollback/refusal|PASS real retained deployment, selected0008 actual old-app rollback246.773s, exact original fingerprints; current0014 replay/quarantine, unsupported rollback refusal and failed-attempt rollback to tested source; both cleanup markers|

Current/retained source, archive inventory, CORE/UNITS/PORTFOLIO_PAYLOAD,
immutable image Config/RootFS and final TLS authority parity were enforced
between all seven stages. Source HEAD and all tracked file hashes remained
unchanged. All six exact-owned projects finished with zero containers,
networks and volumes.

Before this campaign, the complete six-file prior proof directory and original
archive94365aff1bbf8558bcc1481a19c10afea8c571801d54cf3ae3b79156f4af03eb
were hash-verified and moved without changing any bytes to
`/tmp/birja-phase12-proof-d9da271-preserved-before-4b4320b/`. Preservation receipt:
`/tmp/phase12-accepted-retry2-previous-recovery-preservation.json`.
The older preserved campaigns and failed attempts are untouched.

Current atomic raw receipts:
`/tmp/phase12-accepted-retry2-recovery-4b4320b.{source.json,result.json,log}`.
Log SHA256`9bf74942a3aaef89c346c2485e867bdfb3338b064241ddcfc2b66b60c7788b24`;
source receipt SHA256`f1686473ba3bbaa3665394dfe567fae5208f5219ba9a852cbb6fec0d82603d08`.
Raw receipt and both old/new archive hashes were independently recomputed by
this executor. This is fresh actual proof, not payload-equivalence substitution.
The accepted picomatch risk stays explicit in security qualification and issue35;
recovery success does not claim a fixed vulnerability or hosted CI/deployment.

## Historical d9da271 post-review complete recovery

The actual whole seven-stage runner passed at the integrated source above,
2026-11-17T17:44:53.463558Z–18:29:50.887311Z, exit0,2697.424seconds.
Zero tracked files changed and HEAD remained unchanged. All six exact owned
projects finished with zero containers/networks/volumes. Final marker:
`same_archive_final_ci=true`.

One exclusively created archive was used throughout:
`/tmp/birja-phase12-proof/recovery.tar.gz`,196689920bytes,
SHA256 `94365aff1bbf8558bcc1481a19c10afea8c571801d54cf3ae3b79156f4af03eb`.
The complete former5a495a9d proof directory, including all image bindings, was
preserved unchanged at
`/tmp/birja-phase12-proof-historical-before-reviewfix-d9da271/`.
No archive was overwritten, repackaged or substituted between stages.

| Serial stage | Actual current result |
|---|---|
| Image transition |PASS40.243s |
| Retained0007–0014 encrypted round trips |PASS765.276s; exact rows/schema/sequences, immutable receipt replay and corruption refusals |
| Current0017 cold restore |PASS actual declared committed Dockerfile runtime; source destroyed, separate restore, immutable before-oracle and quarantine |
| Roles |PASS320.530s plus3.899s setup;63denials,12input/lock rejections, fresh/populated parity |
| Upgraded TLS |PASS273.317s plus12.884s setup; actual financial consumers and negative transport controls |
| Fresh TLS |PASS273.688s plus12.745s setup; same consumers, denials and exact authority parity |
| Selected rollback |PASS real retained deployments, exact finances/identities/original replay, unsupported0014 rollback refusal, tested-source rollback10.652s and both cleanup markers |

Source/archive/current CORE/UNITS, retained matrix and image Config/RootFS guards
were authenticated throughout and at final completion. Current0017 image:
`sha256:df5ca830e42d8169ad195d0008385f98b380e4ada6477dde87484192297de8ff`.
Retained0014 image:
`sha256:5008f0215c779cfd50f19f391bf4384d29c37eb0518baf98909e977986fe2e8f`.
Legacy0008 image:
`sha256:348798855ac2fbeba517c40e96797cccbad65de3f7100fd5c93f3df7f25da840`.
Legacy0007 image:
`sha256:9a8da9ac14d204c87d9173c8f0f3057f56de20cd594edacefdd3ba9e1efa359e`.
Exact source/app/context/Config/RootFS hashes remain in the four private bindings.

Private complete evidence:
`/tmp/phase12-reviewfix-recovery-d9da271.{log,source.json,result.json}`.
LogSHA256 `bb0d57233c55da8517da95ebd8f9647ae31860f76f1d65c086bacfe3a8c774bb`.
A prior separate integrated actual cold-first proof also passed51.501s with
independently packaged private archive; it is not substituted for this whole run.

Recovery is qualified; complete security remains blocked by the unpatched
picomatch HIGH advisory. Separate diagnostic browser/images pass and both
owner checks stay accepted. No phase/requirement completion follows.

## Historical recovery at10121b0

The actual seven-stage recovery runner passed from start to finish using one
new exclusively created archive. This completes the recovery task's automated
proof. Plan27's complete all-security runner subsequently passed at1f8d5a4;
Phase12 remains incomplete pending owner acceptance and final phase reviews.

## Campaign Identity

Command: `python3 deploy/tests/run-portfolio-validation.py --suite recovery`.
The runner received its stripped synthetic environment, without private.env,
provider credentials or production endpoints. Before startup, exact checks found
no competing recovery and zero containers/networks/volumes for the four fixed
test projects. The exclusive fixed proof path did not exist.

| Item | Actual result |
|---|---|
| Source |10121b02db2b2217b868a9bce30c3f77504eadb3 |
| Tree |99405d979af7fad204db4883a2d16b867ecb7158 |
| Started |2026-11-17T13:27:38Z |
| Finished |2026-11-17T14:12:46Z |
| Total measured runtime |2708.086 seconds,45min08sec |
| Exit |0 |
| Archive |/tmp/birja-phase12-proof/recovery.tar.gz |
| SHA256 |5a495a9dc2901cac46bfa82f23ae2daef67323eda05ac08dc44c67272a2b01a4 |
| Archive format/size |Existing strict USTAR,196689920 bytes; filename extension unchanged |
| Final guard |same_archive_final_ci=true |
| Tracked-source comparison |Zero changed files during the complete campaign |

Private local evidence:

- /tmp/phase12-27-whole-recovery-final-second.log — complete stdout/stderr and
  final exit/time/source-unchanged receipt.
- /tmp/phase12-27-whole-recovery-source-10121b0.json — source/tree/start and
  complete tracked-file SHA256 inventory before execution.
- /tmp/birja-phase12-proof/ — the one selected archive, checksum and four
  private immutable image-binding records. Do not overwrite or rebuild it.

## Seven Stages

| Stage | Actual proof |
|---|---|
| Image transition |PASS38.383s: populated PostgreSQL physical clone, actual collation drift, reindex-before-refresh and logical restore; Redis AOF/auth/noeviction/restart/UID clone; originals preserved. |
| Retained0007–0014 round trips |PASS763.603s: actual encrypted backups/retrieval/restores, exact rows/schema/sequences, original identities and retained source; saved stock/dividend receipt replay and private History remain intact. Nine accounting,17 identity,13 resolution-authority and10 execution corruption refusals pass. |
| Current0017 encrypted cold restore |PASS: original inputs and source datastore destroyed before a separate cold server restores; the same immutable pre-backup oracle64a2358d109ae84e797490406ae9712ef6b372428f88ddb485549a5bd7e6122f matches. Active/frozen root lineage, financial journals, legacyNULL/new2 digests, restricted TLS and quarantine pass. |
| Restricted roles |PASS320.990s:63 denied operations, exact fresh/populated accounting and authority parity, operatorNOLOGIN, immutable audit, quantity-only scheduler, valid concurrent0008 index and runtime consumers. Twelve input/lock rejections and unknown-collation refusal precede role changes. |
| Upgraded TLS |PASS275.696s plus13.945s setup: actual accounting/ownership/operator/calendar/execution/stock/dividend consumers, split cutoff and cash reuse, immutable/permission denials; app/scheduler/migrator SSL, badCA/hostname/plaintext refusals, credential isolation and renewal. |
| Fresh TLS |PASS275.691s plus13.481s setup: the same actual consumers and negative controls; the runner's final equality check confirms exact authority parity with the upgraded lane. |
| Selected rollback |PASS: legacy hardening and old-image rollback101.383s; real selected0008 deployment113.682s and old-app rollback21.721s with force-recreation/original-volume/Redis preservation; retained0014 deployment119.468s, exact financial/identity/runtime preservation and original stock/dividend replay. Unsupported old-source rollback refuses with exact state retained; failed-attempt rollback to the tested source passes10.466s and final receipts/finances remain unchanged. |

All stages ran serially. The runner authenticated archive/current packaged bytes,
fixed retained source payloads, source matrix and image content/Config/RootFS
bindings before execution and after every stage. No source overlay, synthetic
commit, retained-code replacement, archive reconstruction or midcampaign
repackaging was used. Stage timing figures are measured printed integration
durations, not a latency claim or a substitute for the complete runtime.

Final immutable image IDs:

- Current0017: sha256:93ba6266e1493b17950f4e7533a1661b2bc452ed1f4b793a9f9cfe596f3fec6d.
- Retained0014: sha256:f577a0624519985455e254247c8efef8506dac94c25f6b1b2bdcc7bfea84ab23.
- Legacy0008: sha256:38e600cb562689d940a4b653ced6e5145096f9e2414fe1fc3b463ae4a741d9d5.
- Legacy0007: sha256:304ffd911dd5ff8df6cb0f2458a371cc27e5e4c855ec5fdca671a15b69d94353.

## Campaign Namespace Repair

The first complete attempt at58baea3 stopped after119.645s at the correct
missing-private-binding refusal. Its newly packaged deterministic archive had
the same SHA as an earlier focused proof, so the old content-only build tag
collided with another campaign's image. The failed proof directory was verified
owned/private/nonsymlink and preserved whole, with every file hash unchanged,
at /tmp/birja-phase12-proof-failed-20261117-58baea3. Its d33ac7db archive was
never overwritten or rebuilt.

Owning12-18 fix10121b0 scopes the mutable build alias to a digest of the
canonical private campaign directory path/device/inode in addition to source
commit and archiveSHA. Same-campaign replay still requires its exact private
binding. Missing-binding, source, image content/Config/RootFS refusals remain.
No existing image tag was deleted, overwritten or adopted to force a pass.

The behavioral regression failed before and passes after the fix: it preserves
the old directory, recreates the same fixed path with identical archive bytes,
requires a different build alias and proves unbound-image refusal remains.
31CI/runner,11selected,5fixture and10recovery contracts pass. A separate actual
Docker proof builds from two private campaign directories containing identical
5a495a9d archives and independently authenticates both images, then replays the
first campaign's binding. Evidence: /tmp/phase12-27-image-namespace-proof.log.
An initial diagnostic assertion incorrectly expected independent valid builds
to share an ID; independent source/Config/RootFS authentication corrected that
oracle. Neither archive nor image identity was substituted.

## Cleanup, UI and Remaining Gates

Both selected cleanup markers are true. Independent host followup confirms zero
containers, networks and volumes for birja-test, birja-ops-test,
birja-portfolio-fixture-test and birja-portfolio-fixture-test-cold. No campaign
test or migration process remains. Only unrelated.claude/ is untracked.

The originalc2238dc8 UI ZIP is historical after the later browser-only repair.
The current combined owner packet is
/tmp/birja-phase12-ui-review-owner-1f8d5a4.zip, SHA256
c87cb4a3eb3feb52c42a37aa60ff69cce66d2ac8e2637847e6a977af1714d55f.
It preserves the full-browser102-artifact packet and a separate12-artifact
capture-only zero/multiple supplement; both match all249 current covered source
hashes. Their original ZIPs and provenance remain intact. Native200% and owner
acceptance are still pending; see12-LOCAL-VERIFICATION/12-HUMAN-UAT.

Comparison to the qualified261f617 backend/frontend prefix confirms no backend
or frontend runtime source/lock changes. Differences are seven e2e/helper files,
recovery fixture/source-dispatch/selected-control tests and planning records.
Those earlier passing suites remain historical source-bound evidence. The actual
complete all-security graph now passes1541.269s at1f8d5a4, without changed source
during execution. Plan28's separate ownerUI/native200% checks and final phase
reviews remain. No requirement or phase completion follows from this task alone.

## Final Executable-Input Equivalence

The whole recovery run remains recorded at10121b0; it is not relabelled as a new
run at another HEAD. Final read-only authenticate() confirms unchanged archive,
packaged/current CORE,UNITS,portfolio payload, fixed retained matrix and actual
image content/Config/RootFS bindings after the final security builds.

Of306 broad backend/deploy/ops-Compose campaign-inventory paths, exactly one
differs: backend/tests/test_portfolio_entitlements.py. Its owning12-13 test-only
repair selects a completed reviewed session, asserts later-split ordering and
adds18 deterministic clock-boundary cases. It changes no runtime, migration,
SQL, Dockerfile, package or lock bytes. The test is not packaged in CORE/UNITS/
portfolio payload or imported by actual recovery programs. The current cold
image copies app, Alembic and alembic.ini, not these tests. Its broad archived
context/source label remains bound to the original tested commit; no new image
is substituted to chase a test-file hash.

Receipt: /tmp/phase12-27-recovery-equivalence-1f8d5a4.json. This explicit scope
retains the complete original recovery qualification without claiming all306
broad hashes are unchanged or silently rebuilding the qualified archive.

All work was local and synthetic: no provider calls, B2/production access,
private production configuration, new dependency, push, merge or deployment.
Phase7's consumed campaign, six pending requirements and OFF admissions remain.
