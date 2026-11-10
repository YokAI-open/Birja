# Phase5 — Source Coverage Audit

2026-10-29: COVERED means planned, not executed. Research supplies current discovery; no new library/architecture choice requires another discovery workflow. No Phase5 CONTEXT exists; no D-XX decisions are invented.

| Source | ID | Required behavior/constraint | Plan/task | Status |
|---|---|---|---|---|
|GOAL|Story|Understand current portfolio performance alongside every past trade|01–08|COVERED|
|GOAL|SC1|Cash,each holding,total at mid,used-price time|01-2,02-1,03|COVERED|
|GOAL|SC2|Total dollar/percent return vs starting10000|01,02-2|COVERED|
|GOAL|SC3|Quantity,fee-inclusive average,value,unrealized $/%,allocation|01-2,02|COVERED|
|GOAL|SC4|Full newest-first fill history,page by page|04,05|COVERED|
|REQ|PORT-01|Cash/holdings/current total|01,02,03,06,07,08|COVERED|
|REQ|PORT-02|Total P/L vs stored start|01,02,03,06,07,08|COVERED|
|REQ|PORT-03|All fee-inclusive position metrics|01,02,03,06,07,08|COVERED|
|REQ|PORT-04|Cash-inclusive allocation|01,02,03,06,07,08|COVERED|
|REQ|PORT-05|Used-price time/freshness|01,03,06,07,08|COVERED|
|REQ|HIST-01|Actual date/coin/side/quantity/price/fee/signed total|04,05,06,07,08|COVERED|
|REQ|HIST-02|Deterministic bounded keyset pagination|04,05,06,07,08|COVERED|
|RESEARCH|R1|One scalar Account→positive Holding→all Coin→optional Price SELECT; no locks/per-position reads; real-PG nonblocking before/after concurrency|01-2,03-2|COVERED|
|RESEARCH|R2|Cash-only/zero/inactive/missing-account invariant; no GET funding/writes|01,03-2|COVERED|
|RESEARCH|R3|Decimal localcontext50/raw intermediates/HALF_EVEN dollars2,average8,percent2/negative zero/wide derived outputs|01-2,02-2|COVERED|
|RESEARCH|R4|Stored starting_cash/completed-roundtrip return/fee basis/zero basis,start,total/dust/huge/tiny/weighted buys,partial sells|01,02|COVERED|
|RESEARCH|R5|Missing price preserves row/known values; totals/P&L/all allocations unavailable; last-known differs from missing|01-2,03|COVERED|
|RESEARCH|R6|Shared119/120/300/301/configured rules/future skew/late clock/oldest timestamp; fresh/aging/stale/unpriced schema/guard/fixture assertions|01-2,03|COVERED|
|RESEARCH|R7|Exact API fields/plain strings/nulls/UTC/bigint IDs/auth/no-store/fixed user predicate|01,04|COVERED|
|RESEARCH|R8|Strict stdlib cursor≤512/version1/exact fields/types/aware microseconds/bigint/structured422|04|COVERED|
|RESEARCH|R9|Limit1..100/default25/limit+1/last-returned cursor/bound tuple/ties/inserts/foreign boundaries no authority|04,05-1|COVERED|
|RESEARCH|R10|Stored cash_delta signed total/inactive history/dust zero/no frozen multi-request snapshot promise|04,07-2|COVERED|
|RESEARCH|R11|New0008 concurrent reversible index/per-migration transactions/immutable0006/0007/populated validity,key order,parity,roundtrip/0007 guard/recovery|05-2,07-3|COVERED|
|RESEARCH|R12|TanStack/apiFetch/signal/guards/30s10s portfolio/focus/unpolled infinite chain|01-2,04-2,05-1|COVERED|
|RESEARCH|R13|Buy/sell/replay awaited invalidation/no optimistic money or duplicate fill|06-1,07-2|COVERED|
|RESEARCH|R14|Cancel/remove private cache before verify/logout me; observed me preserved; A→expired→B late response|06-2|COVERED|
|RESEARCH|R15|Exact allow-list adds only two GETs; auth/markets/account/health/trade preserved|01,04,07|COVERED|
|RESEARCH|R16|CI/CLAUDE identical critical100% lists add portfolio_math,portfolio,history;80% overall;API tests;audits|07|COVERED|
|RESEARCH|R17|ASVS5 L1/high-blocking/STRIDE/no logs/no new crypto,secrets,packages|Every threat_model;07-3|COVERED|
|RESEARCH|R18|CI fake/console e2e; no real-email automation; newly authorized rebuild and human browser review|01-1,04-1,07,08|COVERED|
|RESEARCH|R19|Existing branch/upstream preflight/isolated tests/scoped push,PR,merge,fresh release decision|01-1,07-3,08|COVERED|
|UI-SPEC|U1|Existing tokens/Inter/4sizes2weights/local overrides/one navy highlight/no registry install|01-2,02,04-2|COVERED|
|UI-SPEC|U2|8+4 desktop/2 tablet/1 mobile/full width rows/gutters|02,07-1|COVERED|
|UI-SPEC|U3|Routes/nav/separate Account/mobile56px+safearea/80px inset/Back/direct links/heading focus|01-2,04-2,07-1|COVERED|
|UI-SPEC|U4|All desktop/mobile fields/one accessible representation/semantic row headers/labelled scroll/wrapped full local+UTC times|02-1,03-1,04-2,07-1|COVERED|
|UI-SPEC|U5|Signed gain/loss,neutral rounded-zero,U+2212,N/A zero basis vs missing Unavailable|01-2,02,03-1,04-2|COVERED|
|UI-SPEC|U6|Cash-inclusive text+8px bars/no residual/null vs0/inactive no Trade link|02|COVERED|
|UI-SPEC|U7|Calculated at vs price time/oldest,worst/incomplete precedence/cash-only/full liquidation/last-known/missing|01-2,03|COVERED|
|UI-SPEC|U8|Exact copy/skeleton/loading/initial error+retry/empty Browse markets/background retention+retry/silent ticks/one contextual status|01-2,02-1,03-1,04-2,05-1|COVERED|
|UI-SPEC|U9|Load more/pending/retry/end/any-fetch disabled/retain rows/count status/no jump/end focus/sequential refetch|05-1|COVERED|
|UI-SPEC|U10|44px targets/8px gaps/rings/non-color outcomes/200% zoom/reduced motion/375,768,1024,1440|02-1,03-1,05-1,07-1,08-2|COVERED|
|CONTEXT|None|Existing requirements/research/UI contract authorized; no questionnaire or invented decisions|All plans|COVERED|

Exclusions: charts/snapshots/realized sell P/L/tax lots/filters/export/other assets/reset are explicitly outside this phase. Phase6 retains backups/restore, production role/SSL and friend-inbox checks. Release is conditional on a fresh explicit choice, otherwise skipped. No required source item is missing.

Dependencies:01→02→03→04→05→06→07→08, one plan per wave1–8.06 retains explicit03+05 dependencies. Fixed shared PostgreSQL/Redis fixtures require serial execution: autouse auth-key cleanup can disrupt another suite's sign-in, and migration roundtrips downgrade birja_test to base. Dependencies enforce isolation even with parallelization enabled; no phase test suites or stack teardown overlap. Shared App/router/allow-list/e2e writes also serialize. Research defaults for formulas/response/cursor/page size are binding implementation choices under granted discretion. Initial real slices cross thin layer files atomically to satisfy MVP first-clickable behavior; later tasks refine bounded user capabilities. Every new test has a producer in05-VALIDATION.
