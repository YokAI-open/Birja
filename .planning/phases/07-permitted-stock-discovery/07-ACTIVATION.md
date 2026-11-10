---
phase: 07-permitted-stock-discovery
plan: "14"
checkpoint: 07-14-01
status: awaiting-blocking-human-product-evidence
prepared: 2026-11-10
tasks_completed: 0
live_activation: disabled
private_requests_made: 0
owner_ui_acceptance: pending
---

# Stock discovery activation review and continuation handoff

Plans 01–13 are locally complete. This is the prepared first checkpoint of
Plan 14, not completed external acceptance. No account, credentials, subscription
or applicable Birja usage grant has been verified. No private API request was
made. No admission was imported, data collection enabled or production changed.
The owner-approved calendar dependency installation is a separate, completed
package gate; it does not establish market-data rights.

## Reviewed implementation and actual local proof

Review base is local branch `feature/v1.1-stock-planning`, HEAD
`bafd77cb5646038cbb1035e5aae07dac07cc046a`. Runtime fixes are in
`7fb4bedf1826ddc8d5c2b2a69e6cf557690e287b`; UI correction is `670b221`;
final helper correction is `214560bfb89f59fb74bf12b0d78698eecc3d4123`.
Subsequent fixture-only compatibility correction `f6a556e` and documentation
commits preserve the reviewed application. This packet changes documentation
only. A later source change requires affected tests and review again.

The authoritative detailed receipts and limits are in [07-LOCAL-PROOF.md](07-LOCAL-PROOF.md)
and [07-13-SUMMARY.md](07-13-SUMMARY.md). Recorded actual gates:

| Gate | Result and limit |
| --- | --- |
| Backend | 969 tests; 99.68% overall; all 21 critical modules 100%; Ruff/mypy/pip-audit pass |
| Frontend | 310 tests; lint/types/format pass; no high/critical npm advisories; existing low/moderate development advisories recorded |
| Actual Chromium | 20 passed; one expected deployed-site CSP skip; eleven stock journeys, responsive layouts, keyboard and independent crypto |
| Hardened image | 158 tests; real network-free read-only nonroot calendar/NumPy/pandas smoke |
| Actual scans | All five targets zero HIGH/CRITICAL including unfixed, pinned Trivy 0.76.1; no bypass |
| Recovery/TLS | Actual exact 0007/0008/0009/0010 recovery; genuine persisted calendar evaluator in both restricted verified-TLS successor lanes |
| Compatibility | Actual selected cutover and distinct legacy 0008 old-app rollback; no claim old runtime supports 0010 |
| Independent reviews | Code: zero active findings; security: 47/47 local threats closed; UI: 24/24; original findings and corrections preserved |

These are synthetic isolated proofs. They do not measure the selected account's
real coverage, latency, quote freshness, usage rights or owner visual acceptance.
The isolated proof resources were cleaned; no stack is started for this packet.

| Reviewed file | SHA256 |
| --- | --- |
| backend/uv.lock | 81c8421f541a5a37966bfe5a87f0e642301911ce5ed345b0c49d37a655f73e69 |
| backend/pyproject.toml | 3071054462750bd4297f973d33d685b15d732ba2e3ee2b380c703dadc9db62fd |
| frontend/package-lock.json | 66a61bfba12247c9e11eed0346c07e221105de6c05d23646900681dc51ed51ae |
| backend/Dockerfile | e7fc0740fdf1423f368d688181e582285f967b30c501a8ce99c73b7951a12cf5 |
| frontend/Dockerfile | bca57d17bdcd1e21bac189ecfb3d6051af5524e2f0f834f9399278265bab5be2 |
| deploy/verify-restore.py | 3fa774f49ebdc6885ae20ed0cc098c0edc5e94781900f755eed8891403e5d744 |
| deploy/recovery-bundle.sh | 5fc02321e95ddddc5e96b3d0ce1e3c81a3508c20dd9c1a2e0801c235c3fa05be |

Calendar resolution installed and tested after exact owner approval:
exchange-calendars 4.13.2, numpy 2.5.4, pandas 3.1.1, pyluach 2.3.0,
toolz 1.2.0, tzdata 2026.6, korean-lunar-calendar 0.4.0,
python-dateutil 4.0.0. Source tag resolves to
`dbe38b1f6887434bbdd1a7d2df6ff8f1742a048a`. Unsigned source, absent wheel
attestation and unverified legitimacy protocol remain the explicitly approved
limitations, not clean authenticity findings. Complete added-distribution
metadata fingerprint:
`e46b91fbe9b2d6fc9de6f974163816c14714b70b47b7751cd5bbf8bb24fadbd7`.

| Scanned target | Actual Docker SHA256 identity |
| --- | --- |
| Runtime | 6f17581c24f9442fb83f5a1fdeeed3741eadf87f660168451bd5550bd81c471f |
| Test-builder | 1189c36f9e278b23e2455be753c696a9aa563bdda4b584f086b59f674748a574 |
| Node | e44078913d853de420bdd91a255281140c0265c93c18f5675e5088416d6ff16e |
| PostgreSQL pinned registry digest | f131db66371391e404c80cef7dd40f31b1b54eb264a6cb032925d9a3859f93f4 |
| Redis pinned registry digest | 26bb2dd4412f902f3decd44fba5dfaef4360d97004d44f6cff7f28d6aba19c48 |

Saved configuration digests are separately recorded in LOCAL-PROOF; Docker
engine and saved configuration identities are not interchangeable. The actual
retained isolated recovery archive SHA256 is
`155743d84c3ae2d7ed765dc21245d3050e73f15afd30ce90d0abc47cb969bc9a`.
It was tested locally, not installed into production by this phase.

## Product evidence needed before use

See [the prepared admission procedure](../../../deploy/STOCK-DATA-ADMISSION.md).
Each product has independent access and collection/display/derived/retention
decisions, configured account/server scope and monotonically advancing
administrative generation. Missing evidence keeps that product denied.

| Product | Public/technical evidence already available | Unverified actual evidence and next boundary |
| --- | --- | --- |
| Quotes — required for live discovery | Official latest-quotes interface supports explicit IEX, symbol batches, USD and source timestamps; reviewed Decimal adapter and tests | Applicable account access and rights for Birja authenticated friends, multi-user display, midpoint derivation, storage/recovery, attribution, quota and validity; actual 20-symbol source-age observations |
| Reference — required for verified provider mappings | Seed has 20 SEC-cross-checked symbol/listing candidates; provider assets API documented | Actual stable provider IDs, active USD common-stock identity/listing and IEX coverage; authorized use/storage of returned metadata. Provider ID remains unverified until bounded check |
| Calendar — required for truthful regular-session disclosure | Approved package plus official NYSE/Nasdaq schedule fixtures; genuine bounded authority evaluator | Current official exceptional-closure review and provenance for XNYS/XNAS; actual usage/storage scope; configured review expiry at most 24 hours and coverage within 45 days past/90 future. Package install alone never renews authority |
| Actions — independently disabled | Structured announcement interface researched; revision/correction accounting belongs to later phases | Access, event completeness/revisions, allowed collection/display/derived/storage, quota and expiry must be established before action collection. No action API call requested now; missing action rights do not require enabling this product for read-only discovery |
| Status — independently disabled/unknown | Separate trading-status capability researched; quote/calendar never proves halt-free state | Timely status source, access, usage, freshness and quota unverified. No status call requested now; report status unverified. Must be resolved with Phase 8/9 safety before any stock fill |

For each product proposed for use, retain the following evidence privately and
provide only a sanitized source/reference and relevant scope to the review:

- Existing account/product/subscription and exact endpoint/feed entitlement;
  account and deployment server identifiers, actual hosting location and audience.
- Terms version/date and applicable agreement or provider confirmation; reviewer,
  reviewed-at, effective/expiry dates, revocation conditions and required notices.
- Separate collection, multi-user display, derived-use and storage permissions;
  reviewed fields and exact attribution, including visible **IEX prices**.
- Actual requests/minute, symbols/request, bytes/response and retention limits;
  $0 eligibility and no automatic paid upgrade. A public plan table is not an
  account-specific entitlement or a guaranteed zero-bill policy.
- Purpose-specific denial for anything not approved; no blanket approval of
  future actions/status, no assumption a personal/free key covers friends.

### Storage rights are a prerequisite

Current quote redaction and client expiry control disclosure, not physical
deletion. Live PostgreSQL values, cached/derived metadata, encrypted dumps,
off-server recovery snapshots, retained copies and restored copies all need
rights for their actual retention lifetimes. Existing single-snapshot rotation
does not establish a bounded deletion deadline: collection or backups can stop.

Activation requires verified permission covering all those lifetimes, **or** an
explicitly approved and verified privileged cleanup process satisfying finite
storage terms, including failures/stopped jobs and recoveries. No cleanup job,
DELETE privilege, destructive removal or production operation is authorized
here. Do not import a finite-retention admission and assume redaction fixes
uncovered stored copies. Financial evidence must not be erased to satisfy an
unreviewed policy. Until storage is resolved, collection remains disabled.

## Current public sources checked on 2026-11-10

These public sources support technical guidance; none establishes the owner's
applicable account terms or grants Birja usage rights.

- [Alpaca market-data overview](https://docs.alpaca.markets/us/docs/about-market-data-api):
  Basic includes IEX and is listed free; the 200/minute figure is labelled
  historical API calls, not proof of this account's latest-quote quota.
- [Latest quotes](https://docs.alpaca.markets/us/reference/stocklatestquotes-1):
  batch symbols, feed selection and USD; select `feed=iex` explicitly.
- [Assets documentation](https://docs.alpaca.markets/us/docs/working-with-assets):
  reference identity/asset metadata; active/tradable metadata is not a halt feed.
- [Alpaca terms, Personal and Non-Commercial Usage and Financial Market Information](https://s3.amazonaws.com/files.alpaca.markets/disclosures/library/TermsAndConditions.pdf):
  personal-use restrictions and advance written notice for making a User
  Application available to others require applicable review. Notice alone must
  not be inferred to grant all display, derivation or storage permissions.
  No notice was sent or agreement accepted by this work.
- [NYSE official calendar](https://www.nyse.com/trade/hours-calendars) and
  [Nasdaq official calendar](https://www.nasdaqtrader.com/Trader.aspx?id=Calendar):
  authoritative published schedule inputs; not a guarantee of current emergency
  closure knowledge or permission to retain arbitrary provider content.

Original product/API research remains in [07-RESEARCH.md](07-RESEARCH.md).
The single-asset API-reference URL attempted during preparation was inaccessible
through the public documentation tool; no private API probe replaced it.

## Proposed bounded measurement — NOT authorized or performed

Only after verifiable applicable product/storage evidence is reviewed, obtain
separate explicit approval of this exact measurement and private key placement.
Authorization to test software or install calendar packages is insufficient.

1. Fixed catalogue only: AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA, AVGO,
   AMD, COST, JPM, V, JNJ, PG, KO, XOM, CVX, HD, MCD, DIS.
2. Official account-compatible single-asset reference endpoint, once per symbol:
   maximum 20 GET requests. Confirm exact origin/account environment privately
   from the applicable access record before any request; no host probing or
   live/paper fallback. No account/order/billing request is included.
3. Up to ten GET requests to
   `https://data.alpaca.markets/v2/stocks/quotes/latest`, each containing those
   twenty symbols, `feed=iex`, `currency=USD`, one minute apart, only during a
   currently verified regular session. A sample is not promised to contain a
   recent eligible quote for every stock.
4. **Maximum 30 HTTP attempts total, including every retry**. At most one
   attempt for each reference symbol and each quote sample; set adapter
   `attempts=1`. No redirects, automatic retries, extra symbol lookup, status,
   actions, calendar API, historical backfill or alternate feed. Failures consume
   their slot; no replenishment. Use the lower applicable per-product quota.
5. Per request: at most five seconds total wall time including response reads;
   maximum 262144 response bytes, lowered if terms require less. At most one
   in-flight request; reference pace at most one/second and lower if needed.
   Measurement overall deadline 15 minutes; stop on session close, expiry,
   restrictive generation change, 401/403/429 or any scope/storage violation.
   No automatic reschedule or second session without another explicit scope.
6. Keys stay in a private scheduler-only credential context and never in chat,
   frontend/API settings, command arguments, logs or this packet. Placement and
   endpoint environment are verified without printing values. Do not read `.env`
   or seek keys as part of the present preparation.
7. Store only reviewed/authorized minimum evidence under its applicable lifetime;
   no raw responses or authorization headers in receipts. Record sanitized
   symbol/provider-ID mapping, listing/common-stock/USD/active verification,
   sample counts and source-event/collection times or ages with rejection
   reasons. Missing/stale/previous-session observations remain failures.
8. No app-wide or production activation. Use approved isolated verification
   only; no account/billing/service/timer changes, production/B2 access,
   provider contact, signup, agreements, payment, deployment or publication.

Proposed reference timeout/size/host wrapper and hard aggregate request counter
must be checked by the continuation executor before use; they are not claimed
implemented by writing this packet. The existing quote adapter is reusable with
the tighter single-attempt bounds. No dependency addition is needed.

## Current checkpoint and exact resume path

**07-14-01 remains unresolved; 0/3 Plan 14 tasks complete.** No 07-14 SUMMARY
or HUMAN-UAT acceptance is created. All six whole-phase requirement checkboxes
remain pending. Source and local safety proof are ready; actual permissions,
20 verified provider mappings, source freshness and owner UI acceptance are not.

The simplest next owner step is to say whether an existing Alpaca account and
applicable permission for Birja's multi-user display and retained database/backup
copies already exist, or whether setup/permission guidance is needed. Supply
only sanitized references or public terms URLs, never keys or full private terms.
A generic “approved” cannot create missing provider rights. Do not ask for
measurement authorization until the prerequisites can actually be satisfied.

Continuation executor: verify this packet's preparation commit, collect/review
the scoped product evidence, keep unresolved products denied, then request the
separate exact 30-attempt approval. Only after both requirements are met may
Task 02 perform private measurement and record real results. Then prepare the
isolated local UI environment for Task 03 owner acceptance; automated browser
proof does not replace that acceptance. Stock execution remains disabled through
Phase 8. Provider/payment/deployment/publication actions remain separate.
