---
phase: 08-corporate-action-safe-ownership
scope: independent-phase8-local-security-control-review
reviewed: 2026-11-11T17:59:06Z
status: secured_local_controls_external_deferred
asvs_level: 1
asvs_taxonomy: legacy-4.0.3-category-mapping-only
threats_reviewed: 47
threats_closed: 47
threats_open: 0
threats_pending_owner_external: 0
unregistered_flags: 0
local_security_controls_complete: true
external_activation_verified: false
external_activation: deferred_by_owner
---

# Phase8 local security review

## Final explicit Plan13 checkpoint closure

**SECURED:47/47 declared local security-control mitigations closed, zero open
BLOCKER/high findings and zero unregistered WARNING flags.** The owner actually
approved the new Phase8 UI and separately selected live-activation deferral. The
root supplied the exact answers; this reviewer independently read their recorded
dispositions in08-HUMAN-UAT (accepted, commit01ab6d3) and08-ACTIVATION
(deferred-by-owner, commit80a2567), and checked them against Plan13's two blocking
checkpoint requirements. No generic continuation, earlier Phase7 acceptance or
synthetic test result was substituted for the new answers.

| Threat | Category | Disposition/status and actual closure evidence |
| --- | --- | --- |
| T-08-13-01 | Repudiation |mitigate / **CLOSED**:08-HUMAN-UAT records the actual2026-11-11 answer “Approve the Phase 8 UI.” with the new screenshots/source scope. Approval concerns presentation, not an assertion the owner repeated dynamic tests or passed provider/production acceptance. |
| T-08-13-02 | Elevation of privilege |mitigate / **CLOSED control**:08-ACTIVATION records the distinct actual answer “Defer live activation; continue locally (Recommended).” It keeps provider REST/replay/retention/backup rights and practical continuity/latency/limits unverified; live activation and stock execution stay disabled. Any later campaign requires its own concrete reviewed exact scope and authorization. |
| T-08-13-SC | Tampering |mitigate / **CLOSED**: checkpoint changes are records only; reviewed runtime, default-disabled activation, dependency locks and strict local scan gates remain unchanged. Deferral introduces no package, provider call, credentials read, campaign reuse or deployment. |

Closing these **controls** means honest explicit acceptance/disposition and
retained authorization boundaries were verified. It does **not** mean the
deferred live provider gates passed, that permissions were granted, that stock
orders/dividend cash are enabled, or that production deployment is approved.
No ASVS certification or complete live-product readiness is claimed. Independent
goal verification still follows and decides phase-goal achievement separately.

Only this report was updated. No tests, database/browser/Docker/provider/private
configuration/production operations or implementation edits were performed.
Prior44-plus3-pending sections below are retained as dated pre-checkpoint review
history; this explicit closure supersedes their pending disposition counts only.

## Final Plan12 security extension

**SECURED implementation scope:44/44 Plan01–12 mitigation threats verified,
zero open implementation BLOCKER/high findings and zero unregistered WARNING
flags.** Plan13's three human/external disposition entries remain **PENDING**,
not passed, accepted or waived. They are the legitimate next checkpoint and do
not imply an implementation defect or block completion of Plan12 local work.
This is not whole-phase approval, provider permission, deployment approval or
ASVS certification.

This extension rechecked the final client/UI review dispositions, actual final
test/scan receipts, CI critical-list contract and sanitized draft acceptance/
activation packets. Runtime remains unchanged at the reviewed source tree
`0026053`; UI release `0cea8b5`. Client hashes remain API
`3ec74a0f69a7b1cac338954fa18e2efc0dddc29d7a3127b4e902609a618d5e53`,
hook `7befec3b3df07084226d8278def3236a3077965feee2f0d44d04a8f8d6c9143d`,
StockSection `aee6a806a4588c1af653fe84f2e40cecae286a2fa59101369f3c4cb98ef2516d`.
No tests, DB/Docker/browser/provider/production operations, private files or new
dependency accesses were performed by this reviewer. All actual execution below
is executor evidence whose recorded results were read, not reviewer-run proof.

### Additional threat verification

These ten entries extend the original34-threat backend matrix below. Every
entry has disposition **mitigate** and status **CLOSED** for implemented controls.

| Threat | STRIDE category | Actual control/evidence |
| --- | --- | --- |
| T-08-10-01 | Tampering | `api/stocks.ts` exact schema/coherence/UTC instants; `useStocks.ts` independently retains raw action epoch, approved admission generation, server-time and conservative clock maxima across generic denial/cache removal. Old reductions cannot restore independent session/admission facts; both normal and merge paths observe raw facts before redaction. Final08-10-REVIEW at7473df3 is clean. |
| T-08-10-02 | Information disclosure | Full RTT once, nearest-deadline strict equality purge in view/cache, auth lifecycle cleanup and no local storage; incoming equal replies cannot reset elapsed authority. Focused arrival-expiry, same/older reply and remount regressions preserved in08-10 review/summary; full final frontend and browser receipts pass. |
| T-08-10-SC | Tampering | Existing packages/locks unchanged; final dependency audits and all-five-image strict scan evidence below, no gate exclusions. |
| T-08-11-01 | Information disclosure | Fixed public enum copy helper, no private/raw event text, semantic original times, unsafe price/time absence and generic permission redaction. Independent actual screenshot/source review08-UI-REVIEW24/24; final browser verifies denied/malformed/action states. |
| T-08-11-02 | Tampering | Independent corporate-action/session/halt/trading labels, no stock order/resolve controls; exact expiry, persistent hold, compatible recovery, retry/focus and long text/zoom journeys. Actual retry-loss and enlarged-cell-overlap defects were corrected and re-reviewed; no owner acceptance inferred. |
| T-08-11-SC | Tampering | Existing checked-in Card/Button/Badge and fixed local copy helper; components.json third-party registries empty, no dependency or registry installation. |
| T-08-12-01 | Tampering | `test_critical_coverage_config.py` explicitly mirrors all29 modules in CLAUDE/CI and100% threshold. Atomic concurrent account reservations in `test_stock_action_monitoring.py:233`, plus actual-attempt quota denial/low-limit tests in `test_stock_scheduler.py:372–398`; no coverage/security threshold lowered. |
| T-08-12-02 | Tampering | Exact same retained encrypted0007–0012 archive,17 identities, nonempty action/financial rows, operator/split replay and restricted populated/fresh roles/TLS proof; final code/security/UI reviews preserve earlier REDs/fixes and identify interrupted versus final successful runs. |
| T-08-12-03 | Information disclosure | Read08-HUMAN-UAT/08-ACTIVATION drafts: synthetic screenshot/source/receipt links, no secrets/private payloads/actual holdings or production-read claim; no fabricated provider campaign quotas or owner answer. |
| T-08-12-SC | Tampering | Unchanged lockfiles; pip-audit no known vulnerabilities; npm0HIGH/CRITICAL with existing2low/13moderate; actual immutable runtime/builder/node/PostgreSQL/Redis scans each0qualifyingHIGH/CRITICAL including unfixed, strict gate intact. |

### Final local evidence read

| Evidence | Recorded outcome and limits |
| --- | --- |
| `/tmp/birja-phase08-final-backend.log` |1551passed,73warnings,163.92s;99.82% overall with80% gate unchanged. |
| `/tmp/birja-phase08-final-critical.log` |29critical modules,2972statements/978branches,100%. |
| final Ruff/mypy/format receipts |Ruff all checks pass; mypy68sources pass; full format gate preserved. |
| Wave9 frontend/static receipts |429tests/28files,15.68s;98.87% statements/97.29% branches/99.61% functions/99.66% lines; lint/types/Prettier/build pass. |
| `/tmp/birja-phase08-plan12-browser-rw1fffy4/browser-final.log` |31passed,1conditional deployed-CSP skip,130.4s; retries0. CSP test requires explicit deployed URL, and no production browsing was performed to remove that expected skip. Owned project cleanup recorded. |
| `/tmp/birja-phase08-final-native-corrected.log` |77passed,2.36s in hardened nonroot/read-only context using host networking solely for isolated test Redis. Initial incorrect-network failed log is not represented as a pass. Separate final runtime calendar/action smoke uses networknone. |
| final image/CI/recovery contract logs |13image contracts and10CI contracts pass. Initial default10recovery-contract run had3conditional PostgreSQL skips; the explicit guarded `--postgres` follow-up in `/tmp/birja-phase08-final-recovery-postgres-contracts.log` subsequently executed all10 successfully in55.831s. The default skips are historical, not represented as executed in that initial invocation; actual serial retained operations remain separate proof. |
| `/tmp/birja-phase08-final-scans/status.json` |Actual read: oktrue, Trivy0.76.1 pinned scanner, all five target exit_code0/oktrue/qualifying_findings0. Scan database metadata and immutable target/report identities retained. This is a dated scan result, not a future vulnerability guarantee. |
| final pip/npm audit receipts |No known Python dependency vulnerabilities; npm retains15development advisories (2low,13moderate), no HIGH/CRITICAL. No forced upgrades/waivers. |
| final retained archive and TLS proof |Same db27… archive0007–0012 exact recovery315.978s; roles160.138s; populated TLS111.679s and fresh TLS108.760s. Full local proof preserves command/source/cleanup receipts; no production restore or installed-tool replacement. |

### Plan13 disposition remains pending

| Threat | Category | Disposition/status and next evidence |
| --- | --- | --- |
| T-08-13-01 | Repudiation |mitigate / **PENDING**: actual owner response to the new Phase8 presentation and explicit distinct external disposition must be recorded; Phase7 approval or generic continue is not substituted. |
| T-08-13-02 | Elevation of privilege |mitigate / **PENDING**: no activation authorized. Draft explicitly keeps REST/replay/derived/DB/backup rights, actual account limits/history/latency and source identity review unverified, with no call-ready campaign before those facts exist. |
| T-08-13-SC | Tampering |mitigate / **PENDING Plan13 checkpoint**: current locks/default-off source are intact; future concrete activation must recheck current source/configuration/terms without adding unreviewed packages or silently renewing approval. |

Packet wording was subsequently rechecked after its routine readiness update:
08-HUMAN-UAT is awaiting-owner-review and08-ACTIVATION is awaiting-owner-disposition,
both truthfully record local gates passed while owner answers remain pending.
This does not authorize a campaign or change external scope. Their substantive
scope is safe: screenshot-only owner presentation review, actions disabled,
execution disabled, distinct permission purposes, unknown actual limits, no
invented request/byte/duration entitlement, no key disclosure and no automatic
provider contact, payment, agreement, production access or Phase7 campaign reuse.
The stricter internal safety ceilings are explicitly not provider entitlements.

The original backend source matrix/hashes and legacy ASVS4.0.3 category mapping
remain below as historical scope evidence, superseded only in completion counts
by this44-threat extension. Owner/external readiness is intentionally not closed.

## Result and scope

**SECURED for the reviewed backend scope:34/34 declared mitigation threats have
implementation evidence;0 open BLOCKER findings and0 unregistered WARNING flags.**
This is an independent read-only source review, including cross-boundary tracing,
of Plans01–09. It is not a claim that the entire phase, provider activation,
production deployment, latest image scans or pending UI/acceptance gates passed.
Plan10 client source has its separate clean independent08-10-REVIEW; Plan11 UI
is actively being implemented and needs its later final review. Plans10–13's13
threat entries are outside this backend matrix, not silently marked complete.

Read the plan STRIDE registers, source audit, research's explicit ASVS mapping,
summaries, local proof and existing detailed independent reviews. Rechecked actual
schema/grants, admission/rules, adapters, ownership/accounting, monitor/scheduler,
privileged SQL/CLI, recovery and authenticated API/unit-writer source. No tests,
database queries, provider calls, Docker/process operations, production/private
configuration or credentials were accessed. No runtime/source edits or commits
were performed. The executor's tests are documentary evidence, not new tests
executed by this reviewer.

## Threat verification

All entries below have disposition **mitigate** and status **CLOSED** for source
implementation. References identify actual control call sites; prior focused
reviews retain reproduced defects and corrected regression evidence.

| Threat | STRIDE category | Implementation evidence |
| --- | --- | --- |
| T-08-01-01 | Tampering |0011 finite/whole/bounded checks and causal composite FKs; event/revision/application uniqueness; downgrade refuses durable rows at `0011_stock_action_accounting.py:928`; stock quote units remain storage-local. |
| T-08-01-02 | Elevation of privilege |0011 grants and `bootstrap-roles.sql:140–179`: app append-only movement access; scheduler holding UPDATE(quantity) only; immutable six-column fill read; no cash/basis/fill mutations or runtime admission writes. |
| T-08-02-01 | Tampering | `backup-snapshot.py:83,206,228,358,1178`: explicit revision dispatch, schema/row checks and17 sequence states extracted from the actual retained dump; `verify-restore.py:782` checks exact restored facts and next identities. |
| T-08-02-02 | Elevation of privilege | Explicit privileged operator preprovisioning precedes restricted migration; `deploy/tests/ops-fixtures.py` actual restricted role/TLS populated/fresh consumers and parity checks; source grants do not confer CREATEROLE. |
| T-08-03-01 | Tampering | `corporate_action_rules.py:99,180,195,221`: explicit ordinary USD facts, genuine calendar opening, Decimal coefficient/exponent bounds before Fraction, bounded rational ratio and all-owner whole-share/basis plan; uncertainty holds. |
| T-08-03-02 | Elevation of privilege | `stock_admission.py:150`: independently evaluates product/purpose/configured account/server, REST/replay capabilities, exact curated scope and durable accounting/backup retention; default approval false. |
| T-08-04-01 | Tampering | `alpaca_actions.py` strict duplicate-key/Decimal/schema/date/identity parsing, missing versus cancellation distinction, immutable mutation IDs and exact bounded historical terminal witness. |
| T-08-04-02 | Denial of service | `alpaca_actions.py:417,525,778`: shared attempt/page/response/total-byte/deadline budget, finite replay/frame bounds, cursor-loop/conflict refusal and permission/lease checks around awaited work. |
| T-08-04-03 | Information disclosure | Fixed REST/SSE HTTPS origins at `alpaca_actions.py:30–31`, no redirects/content encoding, constant error reasons; unrelated replay payloads discarded rather than retained; no raw credential-bearing driver/provider errors logged. |
| T-08-05-01 | Tampering | `stock_ownership.py:156,363,532`: matched immutable causes, exact before/after basis/quantity and global sequence consistency; historical reconstruction uses strict exclusive cutoff with explicit boundary-unit ordering. |
| T-08-05-02 | Denial of service | `stock_ownership.py:86`: fixed instrument advisory namespace, one instrument per caller transaction, native lock/statement/idle timeouts and deterministic holding order; provider HTTP stays outside financial gates. |
| T-08-05-03 | Repudiation | Native DB wall clock after awaited locks/authority reads, immutable recorded/economic times and journal before/after facts; same-transaction pending-cause checks reject committed orphan adoption. |
| T-08-06-01 | Tampering | `corporate_actions.py:540`: unique economic application, complete all-owner validation before effects, exact quantity-only updates plus immutable journal in caller-owned transaction; final authority guard throws so transaction rolls back. |
| T-08-06-02 | Repudiation | `corporate_actions.py:261`: immutable revisions/observations and mutation identity; original-observation replay checked before pointer changes; divergent reuse, late changes, uncertainty and changed applied economics remain held. |
| T-08-06-03 | Elevation of privilege | Split processor preserves total basis/cash/fills; schema bootstrap grants only scheduler quantity update; app/operator cannot invoke arbitrary financial repair through the resolution function. |
| T-08-07-01 | Tampering | `tasks/stock_actions.py` durable fixed-target REST/replay continuation, complete required segments/known IDs, all20 health publication checks, policy binding and journal/epoch/unit equality; partial work remains reconciling. |
| T-08-07-02 | Denial of service | `tasks/stock_scheduler.py:49` atomic rolling Redis account quota uses actual request hooks including retries; independent bounded cycles/lease tokens; finite interval bisection cannot claim a dense incomplete replay segment complete. |
| T-08-07-03 | Elevation of privilege | `core/config.py:254–288` actions default disabled, bounded settings and required baseline/key validation; scheduler-only credentials and separate current product authority, no enable flag minting permission. |
| T-08-08-01 | Elevation of privilege |0012 fixed SECURITY DEFINER owner/search_path and qualified relations; PUBLIC revoke/operator-only EXECUTE; unsafe runtime/operator transitive membership rejected; protected CLI verifies dedicated NOINHERIT login membership and actual TLS before SET LOCAL ROLE. |
| T-08-08-02 | Tampering | `stock_action_reconciliation.py:179,286` binds evidence digest to the exact admission/calendar row snapshot it validates;0012 rechecks locked full row digests, current expected revision/generation/epoch/units/journal/history and prospective semantics after the instrument gate. No arbitrary override/SQL. |
| T-08-08-03 | Information disclosure | `stock_action_reconciliation.py:69,99,131` protected no-follow0600 bounded JSON/CA descriptors, owner/parent checks, strict keys/depth/nonfinite rejection and fixed keyset inspection; `scripts/stock-actions.py` TLS cadata, hidden parameters and generic errors, success only after commit. |
| T-08-08-04 | Repudiation | Immutable decision/replay identity; `backup-snapshot.py:118–195` independently pinned function definition/owner/ACL/attributes/effective column privileges/sequence rights/memberships; `verify-restore.py:848` fixed allowlisted restoration after hash check in quarantined clone. |
| T-08-09-01 | Tampering | `stocks.py:list_stocks` final bounded READ COMMITTED action/admission/calendar/hold query, followed by fresh UTC and synchronous projection; exact shared resolution applicability, pending canonical boundaries and current units; no await afterward. |
| T-08-09-02 | Information disclosure | Generic epoch0/null facts after denied/mismatched actions/calendar authority; safe fixed enum envelope with no raw evidence/terms/users; `api/v1/stocks.py:21` existing authenticated dependency and no-store response. |
| T-08-09-03 | Tampering | `stock_quotes.py:57,152` shared instrument gate, post-wait rights/time validation, local unit assignment, exact applied boundary/current revision, strictly post-boundary source event, no due unresolved split; source-time monotonic upsert never lowers units. |

The nine supply-chain/configuration entries below are separately registered and
closed for their declared implementation controls. They share existing locks,
configured strict CI scans and no new package/version introduced in Phase8;
final all-image/CI execution remains a Plan12 verification gate.

| Threat | Category | Evidence/status |
| --- | --- | --- |
| T-08-01-SC | Tampering | CLOSED; existing locked dependencies and CI image/security gates preserved. |
| T-08-02-SC | Tampering | CLOSED; recovery uses existing reviewed tooling/crypto, no dependency addition. |
| T-08-03-SC | Tampering | CLOSED; existing Decimal/Fraction/calendar implementation only. |
| T-08-04-SC | Tampering | CLOSED; existing HTTP stack, fixed URLs/bounds, no SDK/package. |
| T-08-05-SC | Tampering | CLOSED; native PostgreSQL transaction/advisory primitives, no new locking package. |
| T-08-06-SC | Tampering | CLOSED; existing SQLAlchemy/models and exact arithmetic, no package. |
| T-08-07-SC | Tampering | CLOSED; existing scheduler/Redis/HTTP stack and disabled defaults. |
| T-08-08-SC | Tampering | CLOSED; existing SQL/TLS/JSON/private CLI/recovery stack and fixed allowlists. |
| T-08-09-SC | Tampering | CLOSED; existing API/quote services, no new schema/grant/package. |

## Cross-boundary conclusions and operational limits

- A successful provider poll cannot clear an independent persistent economic
  hold. Shared SQL applicability requires exact current revision/history and no
  later material uncertainty; routine identical confirmations do not invalidate
  a reviewed disposition. Historical mutation replay returns its immutable
  original facts without rolling the current event pointer backward.
- No stock fill route, dividend cash payment, public corporate-action History,
  reverse-split/merger repair or browser/operator blanket healthy override was
  added. Future stock fills must keep the instrument→account/holding gate order
  and immutable cause append in the same transaction. Pending-cause appends
  conservatively refuse full transaction IDs>=2^32; this documented operational
  limit requires future reviewed support, not guessed epoch reconstruction.
- Durable accounting permission is explicit and distinct from transient quote
  retention. Current disclosure rights/deadlines remain mandatory; expiry cannot
  be repaired by browser timing, renewed fetch timestamps or synthesized units.
- Restricted restore does not grant the migrator CREATEROLE: only the already
  trusted isolated bootstrap connection creates the fixed absent NOLOGIN role,
  after function hash/owner checks. Existing unsafe role attributes/memberships
  are refused, not repaired; clone CONNECT quarantine and cleanup remain.
- Declared new surfaces are mapped: provider REST/SSE and quota→04/07, financial
  journal/accounting→01/05/06, dedicated SQL/CLI/files→08, safe API/unit writer→09.
  No unmapped backend endpoint, authentication mechanism or authority source was
  identified. No accepted/transferred threat disposition was used to hide a gap.

## Verification evidence and pending gates

Executor evidence is recorded in08-LOCAL-PROOF and the individual summaries:
actual retained encrypted archive `db27d99ba3085c6b93fa4fe4a6ea6bd9be5ea38a89f9e5f3620005de9681b874`
proved exact0007–0012 recovery,17 identities,13 authority corruptions and genuine
restricted operator/split replay. Remaining role/TLS lanes passed separately
after the documented fixture correction; no interrupted --all is presented as a
successful complete run. Populated and fresh restricted upgrades/TLS did not use
post-upgrade grant repair. Wave7 full backend receipt reports1551passed/99.82%
overall and29 critical modules100%; this audit did not rerun it.

Local proof also records unchanged-lockfile pip-audit success and npm's retained
low/moderate development advisories with no HIGH/CRITICAL, plus an actual hardened
network-disabled runtime smoke. These do not replace final Plan12 full gates,
actual five-image scans, quota test expansion, fresh review after any runtime
change, Plan11 UI/browser review or Plan13 owner acceptance. Private provider
permission wording, actual live identity/freshness/replay/latency/quota verification
and activation remain separately deferred. This source audit grants none of
those permissions and makes no live-data readiness claim.

## ASVS mapping

Mapping uses **ASVS4.0.3 legacy category names explicitly chosen by the plan**,
Level1-oriented controls only. It is neither exhaustive ASVS verification nor
certification, and does not claim that4.0.3 is the latest release.

| Legacy category | Reviewed control |
| --- | --- |
| V2 Authentication / V3 Session Management | Existing authenticated/no-store stock route; no new public privileged endpoint; client lifecycle separately reviewed. |
| V4 Access Control | Restricted table/column/sequence grants, dedicated operator login and narrow SECURITY DEFINER semantics. |
| V5 Validation | Strict bounded provider/evidence schemas, exact finite arithmetic, identity/date/current-snapshot checks. |
| V6 Cryptography / V9 Communications | Existing verified HTTPS and DB TLS, descriptor-loaded CA and encrypted retained recovery; no custom crypto. |
| V7 Error Handling / V8 Data Protection | Fixed safe reasons and generic CLI errors, no raw credentials/evidence, protected bounded files and denied fact redaction. |
| V10 Malicious Code / V14 Configuration | Existing locks/security scans, bounded defaults, default-disabled actions and independently pinned recovery function authority. |

## Frozen source identities

| Source | SHA-256 |
| --- | --- |
|0011 schema | `ba07623bca2cff4e709971e2157364e417d877b085ff5e4f24dfa3e96fb72af3` |
|0012 resolution | `439a36e6c10c67600d0388c5d1ee11be6425fb4b2c3b71523d6c430928bd8ce0` |
| stock_ownership.py | `08c6d75bac572d2c3a62d15d65efb28a6e9166129668e6bf8e17095de2c064e9` |
| corporate_actions.py | `6be8f49158009d9b1e9c927ec8d88813770085ff51f25d1a43d8ab5f0fdccfc3` |
| tasks/stock_actions.py | `465be3c19d01be2254f3fbd073c2a9b4aeb3e2dbe2986fa261e7c7acf5813399` |
| tasks/stock_scheduler.py | `5c9b255122f4b85ec7c15c5d1f42a458aba8882d2f6bdbe5e53be99dc7b194e2` |
| stock_quotes.py | `0aeee6f1982802c1960c9cc7a83c5181507e9e4950c544c15ba74904f0f2d7e6` |
| stocks.py | `12c2bf3dfe16fa5446342adebe4b5ccae9f858b8a4260258c38b418f973e3fdc` |
| alpaca_actions.py | `e8cb2eb9c5b79eb35918b02327107662f0a9e7a9a52b7eb128082e6caecf3a16` |
| stock_action_reconciliation.py | `3633a7a83febea3bb629c64888ced272080b0eb017a8b228e8274bdd9fe8def9` |
| scripts/stock-actions.py | `fb493fcbd19192ae3a6fadab3df61e1d92e560d552c50efa18faa149263c93db` |
| backup-snapshot.py | `9e24a224718c3aab9c5252185da64a6e44ee6c26c320f2cbcb8b4b12246cf2d4` |
| verify-restore.py | `1aa4337745716237f228e468da6a09202907fffbdd9621e9913a8a8272c08bf6` |

Any changed security-sensitive runtime source requires an affected-scope recheck;
test-only coverage/fixtures may require honest updated proof without reopening
unrelated immutable reviews.
