# Phase10 local execution evidence

## Current gate — Wave 6 complete, 2026-11-13

Plans 07 and 10 complete through summaries 9fe5560 and 2bd3365. Thin dividend
service: 46 new tests, 198 affected regressions, 100% statement/branch coverage.
History projection/schema: 149 new tests, 235 affected regressions, both modules
100%. Actual mixed PostgreSQL page passes the installed TypeScript parser,
including exact stored 1.5:1 split reduction to 3:2. Missing historical split
company names use the retained ticker; rename cannot rewrite these entries.

The first full suite failed six cases because retained legacy fixtures and new
rollback fixtures reserved the same BIGINT trade ID. Actual regression f1e312e
and fix 6f9af5c use bound owner-specific IDs beyond JavaScript's exact integer
range. Normal/reverse/repeated combined modules each pass 74 tests with the
same database, without deleting rows or weakening constraints. Failed log stays
at /tmp/birja-phase10-wave6-backend.log (2422 passed, six failures, 299.35s).

Final full backend: 2429 passed, 93 existing warnings, 290.58s, 99.87% overall;
/tmp/birja-phase10-wave6-backend-fixed.log. Actual critical report explicitly
includes existing 39 plus dividend_rules, dividends, event_history service and
schema: 43 modules, 4235 statements/1382 branches, zero misses/partials, 100%;
/tmp/birja-phase10-wave6-critical.log. Full Ruff/format (181 files) and Mypy
(85 sources) pass. Actual CI-list expansion and Node 24 pin remain Plan 16,
not claimed implemented by this report.

Plan 06's independent Task 2 review is complete (29f49a4), zero findings;
final summary cccb57a. Its exact archive remains unchanged. No subsequent SQL
authority, schema or recovery source changed. Only owned birja-test runs at
0014. Next: 08 real contention, then 11 API. Whole-phase requirements, final
integration and owner UI/native zoom acceptance remain pending; all live,
production and publication deferrals remain unchanged. Entries below are
historical evidence, with their original intermediate gate statuses preserved.

## Wave1 — completed locally, 2026-11-12

Plans01/03/12 complete; no payout authority/worker/HistoryAPI/UI yet.

- Actual PostgreSQL migration/schema gate112passed16.43s;01summary5c4340d.
- Pure rules68passed0.39s,43statements/16branches100%;03summary603fa08.
- Strict Historyparser62initialpassed; independentreviewWR01 exposed invalid
  correctionfixture. ActualREDf0bf398→fix90cef7a,validbaseline+independentterm
  mutations. Final70focusedpass1.63s,95statements/230branches100%.
- Fullbackend2184passed85warnings300.41s,99.86%overall:
  /tmp/birja-phase10-wave1-backend.log.
- Actualcritical report existing39plusnewdividend_rules:40modules,
  3947statements/1258branches100%,0missing/partial:
  /tmp/birja-phase10-wave1-critical.log. CI's actual module-list expansion remains
  plan16; no claim that documentary inclusion alone has changed CI.
- Fullreviewedfrontend660passed34files,98.49%statements94.87%branches:
  /tmp/birja-phase10-wave1-frontend-reviewed.log.
- FullbackendRuff/format173files/Mypy82sources pass; parserfullTS+scopedESLint/
  Prettierpass. Wavefullfrontendstatic completion recorded below separately.
- IndependentWave1reviewclean0blockers/0warnings afterWR01recheck90cef7a;
  see10-WAVE1-REVIEW. No wholephasereview/acceptance implied.
- Exact C05a wiretypes frozen fromactualparser; backendmustprovecompatible
  exactrationalnormalizationfordecimalstoredsplitratesbeforeconsumers.

AllSQLusesowneddocker-compose.test stackonly; empty0014at01return. No provider
credentials/privatecall/newdependency/production/B2/timer/installedtool/push/
deployment action. Required0014exactretained/TLSproof04–06 remainsblocking
before07/10consumers. All4Phase10requirements remainpending.

FullfrontendESLint/TypeScript/Prettierpassafterreviewfix; formatlog
/tmp/birja-phase10-wave1-frontend-format.log. No new runtimechangeafterfullsuites.

## Wave2 — authority review and integration in progress

Plan02narrowSQLauthoritycommitted576b667; reviewedbugsreproducedinrollback-only
probes(currentcalendarclosurepaymentandchangedOUTsignatureacceptedbybootstrap).
ActualREDedc0af8→fix4de3977,finalsummary6f60ce4.49authority/191affectedtests
pass24.25s. Fullargument/outputmetadataandcurrentclosure/changedhour/session/
horizonguardsareexactlypinned. Independenttargetedrecheck9pass2.45s:
/tmp/birja-phase10-authority-review-recheck.log. Report10-AUTHORITY-REVIEWclean,
0remainingfindings; retainsoriginal1blocker/1warningandprovenance.
Fullbackend2233passed93warnings306.61s,99.86%overall:
/tmp/birja-phase10-wave2-backend.log.40criticalmodules3947statements/1258branches
100%with0missing:/tmp/birja-phase10-wave2-critical.log. NoTLS/archiveconsumer
proofclaimed;04–06stillblockingruntime. All4newfunction/helperidentitiesmustbe
addedtoexactproducer/consumercontracts. No private/production/provideraction.

## Wave3 — exact recovery contracts verified2026-11-13

Plan04completed0c6f11d. Producer9feca5bRED→b6184e3;clone23973adRED→68882db,
additionalmembershipRED1ba1300resolvedinsameGREEN. RealNOINHERITSETROLE
membershipescapeandunsafe6flagsnowrefusedby0014source+cloneboundary;
LOGINexcludedintentionally. All4functionmetadataand26tables19sequences/55FKs
pinned, no arbitrarysourcegrant/definitionrepair. Twelveactualapp/scheduler
financial/directwrite42501denialspassandimplicitPUBLICrightsrevoked.
All0007–0013generatedmanifest/schemaSQLbyteequalvs5925b52.

IndependentrecoveryreviewCR01reproducedfreshmigratorINHERITcreationfailure:
REDff10840→fix03f912d,summary0c6f11d. Actualrestored()emittedSQLnowcreates
NOINHERIT/NOBYPASSRLS;unsafeexistinginheritancerefusesbeforeCREATEDATABASE,
noALTERrepair. Focusedentry2pass2.345s;independentrecheck2pass2.433s:
/tmp/birja-phase10-recovery-review-recheck.log. Reviewreportclean0remaining.
FinalallSQL21/21pass91.538s/zeroskips;offline15pass6explicitSQLskips.
ActualentryroleSQLusedrollbackalias;archive/transportadapted,sofullretained
archiveandTLSareNOTclaimed. OwnedtestDB0014/payments0/decisions0/entitlements0,
no temporarytestroleoractiveDBops. See04SUMMARYforexactlogs/staticchecks.

## Wave4 — restricted SQL and TLS fixtures complete

Plan05commitsf481694/fdd1c2a/summary697a32c. FinalAMDsource/cloneproof36.512s,
ledgerSHA662abb0caaff9069c2761a2298fd19fc99f216928a01d7b16b074936e4291610.
Originalpositive+verifiedzeroand9linkeddecisions, cancel/noeligiblehold,
reviewedsuccessor,realstock-sellaftercutoffandrealcryptodrain/fund,immutable
replay/clonecashandobservedAccount-waitrights/revisionrefusalsallpass.
Predecessor0013entitlementhashunchangedinthefast/retainedpath;TLSbuildsnew
casesafterupgradeandoldconsumers,notclaimedasoldentitlementsurvivalthere.

Rolessegment192.187s/63denials/freshupgradeparitypassed;itsearlierfollowingTLS
failureisretained,notcalledgreen. FinalTLSpairpopulated136.777/fresh133.869s
passallolderconsumersandnewSQL/negativeTLS/isolationcases. Per-laneledgerhashes:
1915b4465bbac99b77407a51b44d709bc39062b9110b122430a5612d437c7f65and
545bdce8fc80bef8deb1fbc6e10d1114aae71d2e532bcee0b0efa8ca596a584c.
Independentlanehashesneednotmatch;source/clonewithinoneproofmatchesexactly.
Restore-safety6/6/scopedsyntax/RuffF/whitespacepass. No opsresourcesleft.
Observedfixturefailures(head0013,validatorrevision,calendarprobedates,SQLalias,
NVDAresolutioncollision,invalidzerodeclaredrate)andcorrectionsinsummary;
noapplicationfinancial/securitygateweakened. Fullretained--allNOTyetexecuted;
06samearchiveproofmandatorybefore07/10runtimeconsumers.

## Wave5 — Plan06 Task1 same-archive preconsumer gate

Completed locally 2026-11-13, checked at10:50UTC. This records Task1 evidence;
Plan06 Task2 independent gate review and the final summary remain separate.
No Phase10 application payout worker or mixed History consumer is claimed.

The first exact retained archive failed its mandatory0014 isolated restore:
`/tmp/birja-backup-test-phase10-preconsumer/recovery.tar`, SHA256
`637516d8ccd487ef2c45ccba395782cba035d21d737abdca2827ffa9a9e7bbc5`,
152320000bytes. It passed0007–0013 but stopped before roles/TLS after459.772s.
The actual fresh-cluster diagnostic identified PostgreSQL's
`role "birja_action_operator" does not exist`: dividend pregrant checks called
the full canonical query before the resolution helper created its fixed role.
The same-server clone had masked this because source roles already existed.
Archive, sidecar and failed report/log remain preserved, never relabelled green:
`/tmp/birja-phase10-06-all.log`, `/tmp/birja-phase10-06-diagnostic.log`,
and the original directory's `gate-report.json`.

Actual RED50eff38 (fresh entry28.134s, one expected failure) → GREEN64f7795
adds only a role-independent pregrant schema/trigger reader. It requires exactly
one trusted resolution SQL fragment before omitting that lookup at this boundary;
it returns only schema/triggers. Complete function metadata, six role flags,
membership and owner authentication still precede reconstruction. Reconstruction
order, full final canonical validation and financial quarantine are unchanged.
The fresh-cluster regression starts with only bootstrap present and uses real
pg_dump/pg_restore. Function/schema tampering and an unsafe existing runtime role
are refused before runtime/operator creation; unsafe flags are not repaired.
Both runtime roles' payout execution produces actual42501. Initial test-draft
query interception/NULL-aggregate handling was corrected before final RED.

Focused fresh/dispatch2/2 passed30.636s; independent repair recheck2/2
passed30.884s with no findings (`10-PREGRANT-REVIEW.md`, root commitd86e759).
Full actual SQL contracts23/23 passed125.294s, zero skips:
`python3 deploy/tests/test-stock-recovery-contracts.py --postgres`, log
`/tmp/birja-phase10-06-sql-green.log`. Syntax, RuffF and whitespace checks pass.

The replacement archive is retained privately outside fixture cleanup:
`/tmp/birja-backup-test-phase10-preconsumer-fixed/recovery.tar` plus `.sha256`.
SHA256 `1faa8277951d0c2a66ac10ffb8b39b5f85372acdacd10b3b3348126c90052cc1`,
152320000bytes, profile`deploy-recovery-v2`, revisions0007–0014, directory0700
and archive/sidecar0600. Its inventory retains the approved restic0.19.1 binary
SHA256`20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639`
and PostgreSQL18.7 amd64 provenance: index`adbf3d8db097696ed6e997b108b51393786be999c04d543502f8959e1bafa8de`,
manifest`42c334e9e4d30cf6f99ac6bbc411910d020b02dfb693604887e9cdc9188e3a48`,
config`4ee05252904571f8901ceb47916108d7da51fc6ecc3edbfa4a161b8b9225051e`.
All11 CORE/unit file bytes were compared directly with the tar before and after
the run; the report retains every hash and fixture/migration/bootstrap identity.
Only the verifier differs from the failed archive, current verifier SHA256
`2a9009e4c6332be4d551cd7b1d503edc376ade24f459d0fa6d02595fbfeb4d4e`.
The old archive's checksum was independently rechecked unchanged after success.

Exact execution command:
`python3 /tmp/birja-phase10-06-fixed-gate.py > /tmp/birja-phase10-06-fixed-all.log 2>&1`.
This wrapper uses the actual canonical all-mode call sequence, with an explicit
retained archive: `ops.roundtrip(archive)`, `ops.roles()`, populated`ops.tls()`,
fresh`ops.tls(fresh_bootstrap=True)`, then asserts equality of TLS authority results.
The literal CLI`--all` was not invoked because it cannot accept a retained archive.
The wrapper and its delegated `/tmp/birja-phase10-06-gate.py` remain available.

| Actual stage | Wrapper elapsed seconds | Result |
| --- | ---: | --- |
| Retained encrypted0007–0014 roundtrip |503.681|Pass|
| Restricted populated/fresh roles |210.330|Pass|
| Populated verify-full TLS |163.830|Pass|
| Fresh-bootstrap verify-full TLS |162.172|Pass|

Full run1047.402s, including archive preparation and final integrity/cleanup.
Retained revisions all prove exact rows/schema/sequences and original source
identity unchanged;0011 rejects9 catalog and17 identity corruptions,0012 rejects13
resolution corruptions,0013 rejects10 execution corruptions with real restored
stock receipt replay/portfolio, and0014 passes installed isolated recovery,
saved decision replay and financial quarantine. Its source/clone ledger SHA256
is`7f06d31ab8315914b282b6d04e0c1c0f5d3f5b84362b721372c2287a5697dfb8`.
Roles pass63 genuine denials and populated/fresh parity. Both TLS lanes exercise
existing stock/crypto/accounting/ownership/operator/calendar/execution consumers
and the new real dividend SQL original/correction/race/deficit/held paths;
bad CA, hostname and plaintext rejection, mount isolation and renewal all pass.
Populated ledger`a690843347c5f04e1461d51b09c7af2a1dead377f03dfe57bdf3871cb85811a3`,
fresh ledger`4808dc6f997969a0a58cfd3f0c79b75d124a555b5c303419415d7547c40dada5`.
Independent datasets need not have identical ledger hashes. No successful
financial effects are mocked; synthetic fixture data use reviewed migrations
and real existing services/new SQL authority, with no provider activation.

Report `/tmp/birja-backup-test-phase10-preconsumer-fixed/gate-report.json` records
all four passes, identical before/after archive/current CORE identities and
zero owned ops/restore containers, volumes or networks. After all probes ended,
the empty isolated`birja-test` stack was also stopped with its own compose file
and volumes. No provider/private production/B2/timer/installed-tool operation,
package/image/lock change, push or deployment occurred. Consumers remain subject
to Task2's distinct review; no canonical phase/requirement state is advanced here.

## Wave5 — initial retained failure and reviewed repair (not a passing gate)

Initial exact archive:
637516d8ccd487ef2c45ccba395782cba035d21d737abdca2827ffa9a9e7bbc5,
152320000 bytes, deploy-recovery-v2, all 11 CORE/unit files matched.
SQL contracts passed21/21/92.804s. Retained0007–0013 passed (including restored
stock replay/portfolio and corruption controls), but0014 failed guard/verification
at459.772s before roles/TLS. Fresh-cluster diagnostic: canonical resolution
lookup referenced absent birja_action_operator before its reconstruction.
Logs:/tmp/birja-phase10-06-all.log and /tmp/birja-phase10-06-diagnostic.log;
old archive/gate-report remain under /tmp/birja-backup-test-phase10-preconsumer.

Actual fresh-cluster RED50eff38 → verifier repair64f7795. The pre-grant helper
requires exactly one trusted resolution fragment and returns only schema/triggers;
full canonical verification and reconstruction order remain unchanged. Genuine
fresh pg_restore positives, function/schema tamper, unsafe roles and42501runtime
quarantine pass. Full SQL23/23/125.294s; independent recheck2/2/30.884s,0findings:
/tmp/birja-phase10-pregrant-review-recheck.log,10-PREGRANT-REVIEW.md.
All diagnostic/SQL resources cleaned. No source application/provider/production
change. Replacement archive/full replay and Task2 review remain pending.
