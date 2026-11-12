# Phase10 execution contracts

Planning decisions derived from DIV-03/04/05 and HIST-03, inspected Phase8/9
sources and10-RESEARCH. No Phase10 discussion decisions or live permissions
are invented. Dates/rights/admissions remain fail-closed. No dependency change.

## C01 — Immutable accounting

Add0014 after0013. `StockDividendPayment` (`stock_dividend_payments`) is the
immutable `(event_id,user_id)` anchor, unique on that pair. It can represent a
verified initial zero target: no positive-cash CHECK may reject zero. Its ID is
the stable original reference. Persist event/coin/user, revision+entitlement IDs
and fingerprints, saved symbol/name, verified cutoff/rule/unit epoch, eligible
quantity, exact rate, ex/record/payable calendar dates, original rounded amount,
recorded_at and historical cash_after. Composite FKs bind owner/event/revision/
entitlement rather than independently valid but unrelated IDs.

`StockDividendDecision` (`stock_dividend_decisions`) is append-only: payment_id,
user/event, target revision+entitlement identities/fingerprints, previous
decision/application links, desired total, cumulative applied before, proposed
delta when verified, applied_delta, outcome (`applied`,`held_uncertain`,
`held_unaffordable`,`verified_no_change`), fixed reason, recorded_at and saved
terms. Every decision has a unique ID; later decisions link predecessors rather
than UPDATE them. A separate successful application can follow a held decision.
Uniqueness prevents two successful applications for the same exact target
revision/entitlement identity, without making a held attempt permanently consume
that identity. Repeated identical hold observations publish one decision, not an
unbounded new History row per polling cycle. A changed verified revision, cash
condition or reviewed reconciliation can create a linked successor.

Applied target identity includes revision ID and entitlement ID/fingerprints:
A→B→A economic amounts with distinct revisions remain valid. Original payment
and all decisions survive renames, holds, revocations and corrections unchanged.
Runtime UPDATE/DELETE and direct payout-table INSERT are denied; restricted
definer function alone writes. Existing entitlement rows are never backfilled,
rewritten or deleted. Empty-only downgrade refuses before touching populated
financial state. All identities BIGINT GENERATED ALWAYS, money NUMERIC, times
timestamptz; bounded text, finite/range/cent/state/FK/check constraints and actual
owner+recorded_at+ID indexes are explicit. No fake historical events/backfill.

Freeze mixed-query indexes in0014 during plan01, before recovery proof: payment
and decision `(user_id,recorded_at,id)`, entitlement current-work lookup,
payment event/owner uniqueness, decision successful-target and stable held-status
deduplication, plus actual FK/lineage lookup indexes. The split branch reuses
existing owner/sequence indexes or adds its concrete owner/recorded-time index in
0014 now. Plans10/11 consume this schema; they may not edit0014 after plan06.
Any later required schema/index change needs an explicit new migration and full
restricted/TLS/retained proof before its consumers, not an undeclared edit.

For held_uncertain, observed current revision is retained but entitlement ID,
fingerprint, desired total and proposed delta may be null when no current
verified snapshot exists. Conditional constraints require those fields for
applied/verified_no_change and forbid invented verified amounts for uncertainty.
Deduplicate uncertain decisions by `(payment_id,current_revision_fingerprint,
latest_entitlement_identity_or_null,uncertainty_status_identity)` with NULL-safe
uniqueness. Status identity is the stable current economic/action epoch and fixed
hold reason; polling/check timestamps and cash balances are not dedup keys.

## C02 — Exact target and authority

`dividend_rules.py` exports immutable `DividendTarget` and
`evaluate_dividend_target(quantity, rate, cumulative_applied, cash)` with Decimal
arguments. Compute unrounded quantity×rate exactly, then explicit HALF_EVEN cents;
desired target minus cumulative *applied* deltas determines adjustment. Never
round rate/quantity/intermediate products, multiply a rate difference, consult
current Holdings for eligibility, or include held proposals in applied sums.
Python context precision must cover supported NUMERIC ranges. PostgreSQL numeric
round uses different tie behavior: implement explicit half-even numeric logic and
cross-language tie vectors, not round(x,2) as a substitute. Finite/range-check
target, delta and resulting Account.cash; zero targets/deltas are valid. Reject
overflow without writing cash. Never create a second starting grant/reset.

Use latest retained entitlement for owner+event only when tied to the current
revision and independently verified historical cutoff/denomination. A newer held
or cancelled snapshot blocks fallback to old eligible terms. Retained snapshots
from before0014 are discoverable even after sale. Changed cutoffs use existing
verified ownership reconstruction; supported zero entitlement may yield a
verified reversal, whereas cancellation/uncertainty alone never authorizes debit.
Negative delta exceeding locked cash appends held_unaffordable with applied0;
uncertain revised terms append held_uncertain with no invented proposed amount.
Reviewed existing reconciliation restores verified authority; no admin UI or new
financial override is introduced. The bounded worker may then append an applied
successor once. UI keeps the earlier hold truthful and linked to later outcome.

Two distinct work paths are mandatory. Verified-target work derives only from
current verified entitlements. Uncertain-existing-payment work scans existing
payment anchors independently of latest_verified_entitlements, so paidA followed
by held/cancelledB remains discoverable when that helper returns no rows. It
records a linked held_uncertain decision with applied_delta0 and unknown target,
never interprets cancellation as a verified zero/reversal. Before any original
anchor exists, uncertain/cancelled work creates neither payment nor Dividend
event; existing stock hold/disclosure remains the truthful user-visible state.
Only an actually verified supported zero target can create a zero original.

## C03 — Narrow SQL authority and transaction

Migration0014 defines `public.apply_stock_dividend(bigint,bigint,text,text)`:
event_id, entitlement_id, expected_revision_fingerprint,
expected_entitlement_fingerprint. Owner and amount derive from retained rows;
no arbitrary owner/cash/rate/time/JSON-authority argument. Returns immutable
payment_id/decision_id/outcome references. SQL takes stock instrument gate,
then Account FOR UPDATE; all action/stock code retains gate→Account order and
crypto retains Account-only order. Never invert or hold more than one instrument.

SECURITY DEFINER deliberately adds scheduler EXECUTE only. Pin owner to existing
`birja_migrator` (no new login/role/membership/CREATEROLE); evaluate whether its
existing owner privileges are sufficient and keep runtime grants minimal.
Fixed `search_path=pg_catalog,public,pg_temp`, schema-qualified static SQL,
PUBLIC EXECUTE revoked in the creating transaction; no dynamic SQL, network or
caller-controlled object names. Scheduler direct Account.cash UPDATE remains
denied. App gets only required SELECT, not function EXECUTE or payout writes.
All relevant new function/helper signatures, exact normalized bodies, owners,
volatility, security mode, path, ACLs, table/sequence/trigger/column grants enter
exact recovery identity validation. Do not accept a generic function-name match.

After each gate/account/constraint wait reload current revision, latest eligible
entitlement, full action/calendar/durable-accounting admission hashes/generations,
monitor coverage/currentness and persistent uncertainty. Compare advancing
clock_timestamp() in final SQL boundary; payable date is reached only when its
America/New_York calendar day is reached. No open market/fresh trade quote/normal
trading status requirement is added to a verified due dividend. All deferred
constraints and waits occur before final authority guard, then return/commit
without another business query/await. Authority failure rolls back all cash and
History; persist a justified uncertain hold only in a separately revalidated
transaction, never leak partial payment. Original replay reads immutable result
without another cash effect even if current authority is unavailable.

The separate `public.record_stock_dividend_hold(bigint,text)` accepts only an
existing payment_id and expected current revision fingerprint. It derives owner,
event, latest observed entitlement/status and fixed reason internally. It takes
the same instrument→Account lock order and revalidates the same current retained
action/calendar/accounting/display-storage rights and full admission identities
with advancing clock after waits; uncertainty itself does not require a healthy
verified payout target. If rights or expected revision no longer match, refuse
without publishing. It can only append/deduplicate held_uncertain with no target,
no amount and no Account.cash update. PUBLIC/app EXECUTE revoked; scheduler
EXECUTE only. Pin and prove this new definer owner/body/path/signature/ACL exactly
like apply_stock_dividend. No arbitrary owner or proposal amount is accepted.

## C04 — Scheduler and pre-consumer operational gate

`services/dividends.py: process_dividend(db, *, event_id, entitlement_id,
expected_revision_fingerprint, expected_entitlement_fingerprint)` owns one
transaction and typed immutable result; invokes C03 rather than widening grants.
`tasks/dividends.py: run_dividend_cycle` durable keysets retained candidates,
including old entitlements; max100 candidates and max40s per cycle, one attempt
per candidate, no immediate failed financial retry, one transaction per owner.
Backlog cursor wraps between cycles so held work cannot starve other instruments;
Redis lease is optional waste prevention, never correctness. Existing scheduler
supervises this independent loop; exceptions/cancellation never block crypto or
other stock loops. No provider I/O inside locks or new provider transport/settings.
No automatic live activation: existing admissions/disabled gates remain decisive.

`services/dividends.py: record_dividend_hold(db, *, payment_id,
expected_revision_fingerprint)` owns the no-cash transaction invoking the second
C03 function. The cycle merges two bounded durable keysets: verified entitlement
targets and existing paid anchors whose latest revision/entitlement/status is
uncertain/cancelled. Both share the100candidate/40s budget and fair wrap; never
filter the second path through latest_verified_entitlements. Actual regression
must run scheduler→restricted SQL→mixed History: paidA, then held/cancelledB,
one visible held record and unchanged cash; repeat cycle adds no record; existing
reviewed reconciliation yields one applied successor and original unchanged.

Before runtime payout/history consumers run, plans04–06 prove actual0014 exact
recovery from retained encrypted archive, fresh0014/upgraded0013 restricted roles
and verified TLS; SQL financial probes call the real C03 function. Preserve exact
0007–0013 dispatch. Pin all producer/consumer/bootstrap identities, columns,
sequences and function definitions; independently authenticate authority before
reconstructing clone-only ACLs. Restored app/scheduler financial writes remain
quarantined. Final gates repeat whole proof using final current app services and
the *same final archive*, including cutover/rollback and original result replay.
No installed-tool, B2, timer or production action is part of these plans.

## C05 — Mixed History wire and paging

Keep GET /api/v1/trades and cursorv1 exactly compatible. Add authenticated no-store
GET /api/v1/history using limit25(default),1..100, cursor≤512 canonical base64url
strict JSON `{v:2,recorded_at:<UTC microsecond string>,kind_rank:<integer>,
source_id:<canonical positive bigint string>}`; reject unknown/duplicate keys,
invalid kinds/times/noncanonical IDs/encoding. ORDER entire tuple DESC with fixed
ranks trade=4, dividend=3, split=2, dividend_correction=1. Public identity is
`kind:source_id`. SQL applies owner predicate *inside every UNION ALL branch*
before seek/limit+1. No client resort or cross-request frozen snapshot promise.

`EventHistoryPage {items: EventHistoryItem[],next_cursor:string|null}`;
each item has kind,id,recorded_at,asset_type,symbol,name,cash_delta string.
trade adds original side/quantity/exec_price/fee/filled_at and stock source quote
time/IEX attribution from StockFillFacts; crypto preserves established stored
fill values and available metadata. dividend adds payment_reference,eligible_quantity,
rate,credited_amount,cutoff,ex_date,record_date,payable_date,credited_at.
split uses *owner StockOwnershipMovement*+StockSplitApplication and saved ratio,
before/after shares,basis/effective time, cash_delta0. dividend_correction adds
payment_reference,decision_reference,outcome,reason,desired_total nullable,
cumulative_applied_before,proposed_delta nullable,applied_delta,verified terms
when available and `original` owner-bound original Dividend summary. Zero-change
decision is correction, never a second credit; held always applied_delta0 and
cash_delta0. Optional unavailable source fields are explicit null with UI copy,
mandatory fields fail parsing. No arbitrary raw provider messages or HTML.

Original details arrive in bounded owner-scoped linked summary even offpage;
never fetch unbounded pages/foreign owner fallback. Loaded original row can be
focused by stable anchor; otherwise render inline detail with Back to correction.
Publication time orders events; economic dates do not rewrite chronology.
Portfolio value uses Account.cash once, no dividend sum or client credit math.

## C06 — Browser, evidence and completion

Strict tagged wire parser rejects malformed Decimal/date/ID/lineage/discriminator
instead of trusting partial money. Owner+session-epoch infinite query clears old
financial pages immediately and drops late previous-owner results;401 existing
login flow. Retain safe pages on append/refresh failure, prevent duplicate active
append, no optimistic income. Trade completion invalidation reaches new event
History; read-only history refresh invalidates server-authoritative shared cash/
portfolio when new records observed, without deriving a balance.

Use10-UI-SPEC exact table/cards, copy, original-link, no-cash holds, focus/live
region/Load more behavior. No new route/admin UI/filters/chart/payments controls.
Financial browser journeys use real auth/API/PostgreSQL/function/services; only
external evidence fixtures synthetic. Full≥80%backend and exact100%critical
statement+branch lists include every new financial/privacy module in CI, CLAUDE
and test_critical_coverage_config. All5strict image scans include unfixed
HIGH/CRITICAL with no waiver; locked audits/static/frontend/browser/retained
recovery/TLS/rollback pass. Code/security/UI/goal reviews precede human acceptance.
Actual new mixed History and held/correction acceptance plus native200% zoom
are separate owner outcomes; earlier phase approval never stands in for them.
Record source hashes/ZIP/screenshots and honest evidence. No execution or pass
is asserted by planning; publication and live activation remain deferred.
