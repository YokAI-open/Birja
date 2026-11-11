---
phase: 08-corporate-action-safe-ownership
scope: independent-backend-security-source-review
reviewed: 2026-11-11
status: secured_backend_scope
asvs_level: 1
asvs_taxonomy: legacy-4.0.3-category-mapping-only
threats_reviewed: 34
threats_closed: 34
threats_open: 0
unregistered_flags: 0
final_phase_security_complete: false
---

# Phase8 backend security review

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
