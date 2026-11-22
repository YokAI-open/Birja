# Phase 14 — Locked Technical Interfaces for Execution

Planning choices, not new owner decisions or implemented behavior. Approved
requirements and14-UI-SPEC take precedence. No Phase14 CONTEXT/D-ID is invented.

## Successor lifecycle and intent authority

New revisions:0021 lifecycle schema expansion;0022 bounded separate data
backfill;0023 closure SQL authority.0015–0020 migration/SQL bytes and historical
fingerprints are immutable.0021/22 are migration-only, never normal runtime
admission. New current revision0023 has31 tables and24 identity sequences:
qualified0020's29/22 plus two identity tables below. Reconcile the exact explicit
inventory from real catalogue before pinning; unexplained extras refuse.

`portfolio_lifecycle_closures`: bigint ALWAYS identity `id`; unique
`portfolio_id`; `user_id`; timestamptz `closed_at`; text `policy_version` fixed
`freeze_at_closure_v1`; finite text `provenance` (`owner_confirmation` or
`retained_boundary`); nullable `confirmation_name` and `intent_id` for retained
boundaries only. Composite ownership references accounts; unique
`(portfolio_id,user_id,closed_at)` is the target for existing
portfolio_stock_closures' new validated composite FK. Use indexed FKs and
immutable guards, no money copies. Account closed_at and lifecycle/per-stock
times agree; all historical stock participation, including sold-out/zero rows,
has exactly one terminal stock boundary. Active roots have no terminal record.

`portfolio_closure_intents`: bigint ALWAYS identity `id`, `user_id`,
`portfolio_id`, UUID `intent_key`, canonical `confirmation_name`,
`policy_version`, finite `outcome` (`closed` or `confirmation_changed`),
timestamptz `recorded_at`. Permanent unique `(user_id,intent_key)`, composite
owned-root FK, immutable row. Lifecycle `intent_id` references the matching
closed outcome and owner/root, using deferred constraints/trigger checks for
atomic circular insertion. A closed replay never rewrites the first intent.
This is internal lifecycle evidence, not financial History. No journal is
created for foreign/missing targets. Never grant general INSERT/UPDATE/DELETE
to app/scheduler on either table or stock closures.

Bound retained intent growth: at most200 new outcome rows per owner per UTC
day, serialized under the same User NO KEY UPDATE lock and counted through an
indexed(user_id,recorded_at,id) query. Same original replay precedes this cap;
syntax/foreign/missing/quota failures create no outcome row. Public requests
also use existing30/min owner and60/min IP attempt primitives with TTL. Quota
refusal is429 closure_quota with wait until next UTCday; it does not resolve a
previous unknown original lacking a durable terminal outcome. No purge of
retained intent evidence is introduced.

0022 creates only provenance=`retained_boundary` lifecycle records for already
closed qualified roots after validating their existing terminal evidence. It
does not fabricate user confirmation/intent keys or alter financial rows,
timestamps, unit epochs or balances. Missing/inconsistent historical evidence
refuses before backfill; no repair-by-guessing. No fake backfill for active roots.

One app-executable, migrator-owned SECURITY DEFINER:
`public.close_portfolio(p_user bigint,p_portfolio bigint,p_key uuid,p_name text,p_policy text)`.
Returns internal `portfolio_id bigint,outcome text,replayed boolean` only; no
caller-supplied boundary/sequence/clock values. Fixed safe search_path and
2s lock/10s statement/30s idle transaction bounds, READ COMMITTED required.
Revoke PUBLIC and scheduler EXECUTE; app gets only this exact signature.

1. Lock existing User FOR NO KEY UPDATE. Permanent same-key intent lookup comes
   before mutable name/cap/active checks; different target/name/policy yields
   `closure_intent_conflict`. Owner/missing is privately unavailable.
2. Already-closed owned root is eligible for closed acknowledgement without
   exposing name, finances or first intent; ordinary reads stay forbidden.
   A closed replay must still pass the sorted historical gate/root acquisition
   below and complete service integrity validation before acknowledgement.
   Only an immutable confirmation_changed replay can return before stock gates;
   no closed replay writes another lifecycle/intent row or skips proof.
3. Discover distinct stock coin IDs from all target movements plus stock
   holdings, sorted numerically; cap to curated supported universe and refuse
   unexplained instruments. Acquire the exact existing advisory namespace
   `hashtextextended('birja.stock.instrument:' || coin_id::text,0)` for all,
   before locking Account FOR UPDATE. Recheck ownership/active state and full
   instrument set. Changed set raises serialization retry; rollback entire
   attempt and retry discovery at most3 times, never acquire missing gates
   while holding root. User NO KEY UPDATE remains compatible with FK KEY SHARE.
4. Compare exact canonical reviewed name under root lock. A mismatch records
   immutable `confirmation_changed` intent, returns that outcome, and commits
   only this nonfinancial refusal journal. Future delayed calls with the same
   key replay this refusal even if the name later changes back. Thus a new
   review uses a new key only after the old intent is terminal. Existing
   immutable terminal refusal solves unknown-request races; active GET alone
   never cancels a pending DELETE.
5. After complete locks and derived histories, sample fresh clock_timestamp().
   Require non-backdated global stock tails/applications and strict advancement
   past existing instrument terminal clocks; equal/backward clocks refuse.
   Insert a closed intent, lifecycle row and each stock closure at that one
   time; global closing_sequence is the whole instrument journal tail and
   unit_epoch is the actual applied epoch at that time. Atomically set closed_at.
   No liquidation, transfer, grant, financial History or causal-record rewrite.
6. Before service commits, verify complete instrument consistency for each
   locked instrument through the shared read-only verifier core. SQL itself
   derives and checks all persisted boundary/ownership inputs; the client cannot
   supply a claimed proof. Any failed complete Python integrity check rolls
   back the SQL result and journal too. Closed replay checks required retained
   lifecycle/stock integrity before acknowledgement. Never acknowledge corrupt
   retained evidence. The SQL transaction is not independently certified by a
   successful HTTP status or merely by having populated a closure table.

`stock_ownership.assert_ownership_consistent` keeps its original one-instrument
guard unchanged. Extract its validation body into a private core; add a narrow
`assert_closure_ownership_consistent` entry that requires this transaction's
closure result, exact instrument membership and actual held advisory-lock
evidence. It cannot be used to append a movement or clear db.info['stock_gate'].
Existing financial entrypoints retain their original guard. Add successor
DB guard(s) and service checks for new movement.recorded_at and split
application.processed_at strictly greater than any prior terminal clock for
that instrument, under the instrument gate. Reject equal/backward time, never
invent later timestamps or rewrite old rows. Test pending split/application
assembly so a transaction's own uncommitted effects remain valid. Existing
writers already resample after locks; do not claim a demonstrated old bug.

### Implemented0023 handoff to Plan03

The actual SQL result has exactly `portfolio_id`, `outcome`, `replayed`.
`outcome` is either `closed` or `confirmation_changed`. A caller consumes that
result only within the originating READ COMMITTED transaction and against its
captured original owner/root/key/name/policy. SQLSTATE40001 means rollback the
whole transaction and rediscover the instrument set, at most three attempts;
no root-locked missing-gate acquisition or new target/body is permitted.

Plan03's service must execute this exact definer itself, capture its transaction
identity/result in private in-memory context, then query the sorted union of
ALL target ownership-movement instruments and stock holdings on the SAME
connection. For `closed`, require exact lifecycle/root/intent and complete
stock-boundary membership, validate actual granted instrument advisory locks
held by this backend in the existing namespace, and run the complete shared
read-only stock verifier core for each member before commit. This includes an
already-closed acknowledgement, regardless of `replayed` or whether its incoming
key is the original terminal key. Crypto-only/empty roots still require complete
universal lifecycle integrity. No boolean/client argument or a previously
returned tuple authorizes the proof entrypoint; only the current service-owned
transaction context does. Do not clear or bypass the financial stock-gate marker.

`confirmation_changed` is a nonfinancial terminal outcome: commit its journal
before exposing the definitive name conflict. An exact original replay may
return this outcome before acquiring stock gates; do not require a successful
financial proof for a result that cannot mutate finances. Other SQL errors roll
back. A proof failure rolls back every newly inserted outcome and closure row.
A commit/response failure remains transport-unknown; an active GET is never
evidence that a previously submitted original cannot still commit. Plan02
contains no HTTP route, application service or temporary successful proof stub.

## API and browser transport

Add `DELETE /api/v2/portfolios/{portfolio_id}`. Authenticated CurrentUser and
CSRF are checked before streamed body parsing. Dedicated strict schema:
`{intent_key: canonical UUIDv4 string, confirmation_name: canonical valid name,
policy_version: "freeze_at_closure_v1"}`; no extra/duplicate keys,8192byte limit,
application/json, IDs canonical decimal strings. Do not overload PATCH's bool.

Success200 is exactly `{portfolio_id: "<original ID>", state: "closed"}` for
both first closure and owned original replay. It contains no name/money/time or
replay distinction. Known committed terminal name refusal409 has only
`detail.code="portfolio_confirmation_changed"`; original immutable-key/body
conflict409 `closure_intent_conflict` never authorizes a new body or target.
Foreign/missing404 `portfolio_unavailable`, auth401/403, bounded format errors
and all responses PRIVATE/no-store. Bound owner/IP attempts using existing
management rate-limit primitives and finite named buckets, no new funding cap.
All contention/corruption/Redis/unknown transport500/503 is private operational
failure,503 Retry-After5. No raw SQL/provider/input/PII logs. Service rolls back
on exceptions. A postcommit serialization/response failure is unknown, not a
promise of rollback. A new auth error after an unknown original does not prove
that the original did not commit.

`PortfolioDeletionIntent` is immutable `{portfolioId,intentKey,confirmationName,
policyVersion}` and `PortfolioDeletionReceipt` exactly `{portfolioId,state:"closed"}`.
Dedicated `portfolioDeletion.ts` transport strictly validates originals,
ack/error shape, content-type, IDs and returned original equality; auth refresh
and CSRF awaits retain captured owner/session/operation. TanStack mutations
have no automatic retry. Terminal name409 is trusted only for the same original
key/body after its durable journal is committed. Clear/replace that marker only
on definitive terminal resolution; all ambiguous responses retain unknown.

Separate sessionStorage key `birja:portfolio-deletion:v1`; one unresolved
owner/tab envelope using existing creation opaque binding/readback discipline,
max16000bytes. Persist original ID/key/name/policy before send; no finances,
tokens/email/receipt. Cannot overwrite unresolved original. Failure refuses
before request. Restore only after current owner authentication; revalidate
same-owner session epoch, ignore old captures; no automatic DELETE on mount or
focus. Explicit Check deletion result replays exactly the original key/body/ID
and may finish that original intent. Another deletion waits; sibling trading
and reads remain independent. Logout/owner change clears private lease.

Hook state: idle/review/persisting/submitting/unknown/checking/terminal_refusal/
closed. Named confirmation freezes reviewed name; metadata rename disables it
until fresh same-ID review. Description-only metadata has no identity effect.
Quarantine original root before network send; unresolved lease lives outside
financial Outlet. Metadata-only recovery route `/portfolios/deletion` plus
overview recovery link is static (no key/name in URL). Ordinary financial routes
never reveal closed retained metadata or finances. Only current request context
may render its captured name; stale route gets generic unavailable/overview.

Identity-only lifecycle invalidation carries no finance/key/name. Revoke target
revision before authoritative refetch, cancel/mask cached rows/cash/previews/
receipts/cursors; late A→B→A/new-session callbacks remain invalid. Known closure
goes to /portfolios, never chooses sibling. Unknown list omission is not success;
active list presence is not cancellation. Unavailable target may retain only the
already-approved unresolved-order boolean, no amount/payload/retry. Normal
other-root trading remains usable throughout.

## Recovery and qualification

### Bootstrap and test-harness ordering (revision1 resolution)

Plan01-task1 owns the minimum finite disposable migration-owner allowlists in
`backend/tests/test_migrations.py` and the session-autouse prerequisite contract
in `conftest.py` BEFORE any successor migration test runs. Prospective0021/22
profiles add exactly the two lifecycle tables/two sequences and their source-owned
guards;0023 adds only the exact final closure/clock authority declared in its
checksum-authenticated SQL. No unqualified union of every known object across
revisions, arbitrary source-derived name wildcard or autouse skip is allowed.
Unexpected objects/owners and a historical schema substituted for current refuse.
The test harness's intermediate profiles support authenticated migration only;
normal runtime0021/22 remains forbidden. Focused01–03 direct migration/authority
tests own explicit historical databases and do not invoke partial-schema app
startup. Separate pytest processes after each new installed revision must both
pass the same finite session prerequisite.

Plan04-task1 owns BOTH independent current-authority implementations:
`backend/app/db/portfolio_bootstrap.py` and
`deploy/db/bootstrap-roles.sql`. The SQL outer finite revision whitelist and a
distinct0023 preflight/reset/grant branch must accept only the exact31-table/
24-sequence complete successor catalogue, sources, functions, triggers, owners
and ACLs. Existing0017/0020 branches/fingerprints stay frozen. No general new
table DML/sequence allocation or scheduler closure EXECUTE; app receives only
the explicitly specified closure signature and read privileges.0021/22 and
unknown revisions receive no runtime grants. Actual fresh/upgraded SQL/Python
bootstrap outputs must have identical normalized catalogue/ACL authority and
matching corruption/mutation-denial negatives before recovery/TLS consumers.

Plan04-task2 owns the successor `install_current_test_grants` adaptation in
test_migrations.py and current runtime bootstrap. Run the focused admission
pytest invocation twice independently after0023 already exists, proving the
session-autouse owner prerequisite and exact current grants work repeatedly.
Plan15 only broadens whole-suite historical fixtures/tail checks after01/04;
it does not introduce these prerequisites late. Its explicit dependencies on
01/04 preserve sequential ownership of test_migrations/conftest.

Keep fixed qualified0020source9527e358bc6953cec7580043703324db194ba396,
complete0017source4b4320b4cc373268a8d598612a563cd5ef199700 and0007–0014
profiles unchanged. New payloadV3/current0023 includes exact31table/24sequence
inventory, lifecycle/intent evidence and new authority/trigger/fingerprint/ACL
inventory. V1/V2 cannot masquerade as V3 through missing/default fields. Restore
V1/V2 with their own source, then explicit authenticated migration; never overlay
current services onto historical fixtures. No-ACL quarantine before regrant,
all service roles denied until exact catalogue/source/lifecycle parity passes.
Selected old-app rollback refuses before switching/loss when0023is unsupported.

Canonical new archive `/tmp/birja-phase14-proof/recovery.tar.gz` must be absent
at campaign start and exclusive to that run. Preserve qualified Phase13archive
SHA6fb79a45ddcb10725b18fc756e71bd555c827a6e61a5a4a0bd2d183096114b92
and prior Phase12/13 archives. Whole security then fresh whole seven-stage
recovery at one frozen source, exact authenticated private image IDs and same
archive guards; source destruction/independent oracle, roles, fresh/upgradedTLS
parity and rollback/refusal remain mandatory. No composite partial pass.
