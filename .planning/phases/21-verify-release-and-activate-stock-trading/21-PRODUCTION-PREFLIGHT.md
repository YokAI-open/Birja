# Phase 21 production preflight proposal

The owner requested working stock trading across the searchable NYSE and
Nasdaq common-share catalog. A deployment with stocks paused and an
original-20 rollout would fall short of that outcome. GitHub published
v0.8.0. Production rollout and expanded live qualification remain open.
[Milestone requirements](../../REQUIREMENTS.md)
· [Live-source qualification](21-LIVE-QUALIFICATION.md)

## Selected release

| Item | Identity |
|---|---|
| Production target | DE189274, `/srv/birja`, project `birja-prod` |
| Last recorded running source and schema | `07d3aa5c627b5ba550aa2d11baa13e2becaf3aa9`, `0023` |
| Published release | `v0.8.0` at `0f4a42f4dfec657314d2feaab1c5a539c69518b8` |
| Released tree | `0eb379b4240d0a28918dffcab0825f12c2c555e7` |
| Expected retained deploy manifest | SHA-256 `672b8680b3d8649a7b3bd4eb56a2aecb618591456f2ba3e685c38ed2de4b55f1` |
| Recovery profile and archive | `deploy-recovery-v7`, payload 6, `0026`, SHA-256 `a32f8c92f66eff8b081538fc4989e282c5da2e2c5320cf9008b315bb34efde5d` |

The expected retained manifest was computed from the 350 tracked files
selected by the released installer. The same commit's six passing checks
and seven-stage recovery receipt are recorded in the
[release CI record](21-RELEASE-CI.md). Shell syntax passed for the installer,
deployment launcher and smoke script.

## Read-only host scope

The owner authorized completing the full rollout and agent-run production
acceptance on November 25, 2026. Use the exact reviewed release, measured
cutover inputs and applicable source evidence for the rollout.

Inspection that day at 19:50 UTC confirmed `07d3aa5` and revision `0023`.
The app, scheduler, PostgreSQL and Redis were healthy. Both runtime
database roles connected with verified TLS 1.3. PostgreSQL reported no
invalid public indexes and a database size of about 11.7 MB.

- The original 20 stocks exist and there are zero stock data admissions.
  Live quotes and actions are disabled. The production scheduler lacks
  the protected Alpaca credential configuration.
- The current database and Redis mounts are the Phase 6 candidates.
  The unmounted predecessors also contain data. Use distinct empty
  candidates and remeasure space after building. About 13.17 GB was free.
- The installed deployment manifest and recovery-v4 files matched their
  recorded hashes. The 03:10 UTC nightly backup succeeded. The guarded
  B2 restore verified that exact `0023` predecessor snapshot in the
  isolated clone at 20:24:56 UTC. All 20 recovery inventory entries are
  in use. Repeat the protected backup and matching restore with the
  final cutover configuration and fenced writers.

The inspection used local metadata and read-only transactions.

## Work remaining for searchable trading

- Publish a current, reconciled NYSE and Nasdaq common-share catalog using
  sources with documented field and use scope. Alpaca's asset master can
  verify active listings and provider identities. Alpaca states that its
  asset API does not classify stocks and ETFs separately. Full coverage
  therefore needs a checked classification source and coverage comparison.
  [Alpaca asset FAQ](https://docs.alpaca.markets/us/v1.4.2/docs/broker-api-faq)
- Make listing verification and trading enrollment practical for the
  full catalog. The released importer stages up to two individually
  approved asset lookups per grant. Financial promotion takes an exact
  catalog ID, listing ID and admission ID. The trade endpoint is read-only
  for a listing without a financial binding, even when a display quote
  exists. Closing this gap requires an operator workflow that can enroll
  verified listings in batches or when selected, within the existing
  allowed scope, quota and identity checks. Retain fresh quotes, reported
  halts and action coverage for the issue before permitting an order.
- Use the exact authorized release, measured candidate volumes and
  verified prechange encrypted restore for the cutover. After protected
  activation, verify the browser can search for an out-of-list name and
  ticker, buy and sell a virtual share, and reconcile cash, holdings and
  History.

The 0026 recovery proof and the bounded live ORCL read remain applicable to
their measured inputs. Two targeted released tests also passed in a
disposable PostgreSQL/Redis stack for the existing AAPL route and reported
halt/expired-evidence rules. Those results do not establish expanded
production readiness. The exact approved cutover must use verified
rollout evidence for whichever release delivers the full outcome.

Before the first candidate writer, the measured original 0023 release and
volumes can be reopened after the rollback checks. After the first writer,
preserve 0026 data and use tested 0026-compatible recovery. The exact
maintenance window, volume selection, capacity, live recovery evidence and
rollback route must be bound to the actual host before asking for cutover
approval. [Production runbook](../../../deploy/RUNBOOK.md)

Phase 21 retains full catalog coverage and the production out-of-list
acceptance requirement.
