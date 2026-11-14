---
phase: 08-corporate-action-safe-ownership
reviewed: 2026-11-11T16:17:30Z
depth: deep
review_head: 7473df3
files_reviewed: 4
files_reviewed_list:
  - frontend/src/api/stocks.ts
  - frontend/src/hooks/useStocks.ts
  - frontend/src/api/stocks.test.ts
  - frontend/src/hooks/useStocks.test.tsx
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: clean
---

# Plan08-10: Client Safety Review

## Narrative Findings (AI reviewer)

### Final complete ordering re-review at `7473df3`

**Zero active BLOCKER/WARNING findings in the reviewed Plan10 scope.** CR-01 and
CR-02 are resolved. Both accepted paths now observe raw validated epoch,
admission-generation, exact server-time and conservative upper-clock maxima
before local redaction. Normal acceptance does so after auth/staleness checks;
reduction-only merging retains raw maxima without promoting independent cached
facts. Remembering the sanitized payload cannot decrease any maximum.

Traced normal/merged responses, generic0 redaction over higher epochs, hidden
higher held epochs, lower approved generations across denial, current-response
strict server ordering, pre/post-expiry transport reanchoring, categorical
revocations, cache removal/remount and auth reset. Old unsafe envelopes can only
reduce applicable action/quote facts; independent session/admission/status and
transport remain conservative. Upper offset is included once in deadline/age
projection and scheduling. Current recovery requires sufficient epochs/generation
and a newer server observation. Only actual auth identity transition resets the
retained authority lifecycle.

Final hashes:

- api/stocks.ts: `3ec74a0f69a7b1cac338954fa18e2efc0dddc29d7a3127b4e902609a618d5e53`
- hooks/useStocks.ts: `7befec3b3df07084226d8278def3236a3077965feee2f0d44d04a8f8d6c9143d`

Source review is clear for subsequent UI integration. The executor's reported
144-case run is separate evidence; the reviewer performed no tests, runtime
operations or source edits. Historical findings and intermediate dispositions
are retained below.

### Admission maximum re-review at `9242068`

The denial bridge is fixed by an independent auth-scoped maximum approved
admission generation. Lower approved generations cannot restore authority after
unavailable redaction or cache removal/remount, and reduction-only merges preserve
that maximum. All previous categorical/time merge scenarios remain corrected.

**Remaining CR-02 normal-path raw observation loss:** the reduction merge calls
observe(raw), but the ordinary accepted response path still returns
purgeExpired(withAuthorityClock(response)) without first observing raw facts.
Arrival-time permission/review expiry can therefore convert a newly received
action epoch9/admission generation5 to generic0/null before remember sees it.
Neither high-water records the higher raw value; a later lower epoch8/generation4
with a newer server timestamp can pass. Protecting only merged redactions does
not cover local privacy redaction before initial cache publication.

After all stale-response/auth checks, absorb the accepted raw envelope's epoch,
generation, observation-time and conservative clock maxima on the normal path
as well, then purge/project it for cache publication. Add an arrival-RTT-expiry
regression followed by lower healthy epoch/generation with a newer server time;
public generic0/null redaction must remain while internal maxima block revival.
This is the final uncovered branch of the existing CR-02 raw-high-water invariant;
no additional concrete issue was found in the full affected trace pass.

Hook SHA-256: `c902840d4b872911cb3c00bdac14c086592fad0d212969016af65a8ae2d5e076`.
API/parser unchanged. No reviewer tests or runtime operations were performed.

### Raw observation high-water re-review at `44d1fff`

Both `edfc623` losses are resolved: raw observation epoch/time/upper-clock maxima
are retained independently of the sanitized public snapshot, and unavailable's
null generation no longer makes a genuinely newer denial look older. Old action
redactions preserve independent session/admission facts without clock rewind.

**Remaining CR-02 admission-generation bridge:** approved generation5 → generic
unavailable (null generation) → newer-time approved generation4 with sufficient
action epoch. The Guard has no retained approved-admission generation maximum;
both latest/current snapshots now have null generation, so lower-generation
protection compares0 and accepts generation4. The previously observed approved
generation high-water is lost through denial and cache removal/remount, contrary
to retaining the existing admission-generation protection alongside action/time
ordering. Preserve that maximum independently through unavailable redaction,
clear only on actual auth lifecycle change, and prevent a later approved lower
generation from restoring independent authority. Older unsafe redactions may
still remove action facts conservatively.

This is the only remaining concrete finding from the full affected ordering/
merge pass; CR-01 and all previously reported CR-02 paths are resolved. No tests
or runtime operations were performed. Frozen hook SHA-256:
`5790246c7857cc04e707a5b8c2baec1b4f2f3a729e06ef87fe6434c6fb5c13b0`.

### Complete categorical merge re-review at `edfc623`

Retaining a sanitized latest snapshot and merging old action reductions closes
the previously reported old generic response restoring independent categorical
authority. Clock/transport provenance remains intact across cache removal and
remount. Two related CR-02 high-water losses remain in this new merge path:

1. A **newer** unavailable envelope has null admission generation, treated as0.
   Against approved generation5 it takes the lower-generation merge path, keeps
   the previous public server time and never records the denial's newer time.
   Example approved epoch7/T10 → generic unavailable/T20 → approved epoch7/T15:
   T15 passes retained T10 guards and restores authority older than the observed
   T20 denial. The worker independently identified this same edge. Do not compare
   unavailable's null generation as an actual lower approved generation; retain
   the maximum actual incoming observation time independently of merged payload.
2. A higher incoming held epoch is lost when the previous action is already
   noncurrent. Example unknown epoch7/T20 → suspended epoch9/T15 merges the old
   action, so remember still sees epoch7 → current epoch8/T25 incorrectly passes.
   Generic0 privacy redaction may legitimately remain in the public payload,
   but max incoming epoch9 must still enter the internal safety high-water mark.

Separate observation high-water tracking from the display/cache merge: absorb
all validated incoming safety epochs and relevant maximum server times without
reanchoring clock or resurrecting independent facts. Regression tests must cover
both transitions and cache removal/remount; truly newer sufficient-epoch recovery
should remain possible. No additional concrete defect was found in the complete
affected ordering/merge source pass. No tests/runtime operations were performed.

Frozen hook SHA-256:
`3cd3767fc9f00d51eac909cab81e0f9f88193078713105ca64e29372fb6a6b16`.
API/parser remains `3ec74a0f69a7b1cac338954fa18e2efc0dddc29d7a3127b4e902609a618d5e53`.

### Remaining CR-02 re-review at `89c1322`

The monotonic upper-clock/offset closes time-based reanchoring: identical or old
generic responses cannot move the conservative clock behind a consumed close,
review, source-age, action or admission deadline. Offset is carried internally
and added once to projection/age/deadline calculations; measured RTT and original
public timestamps remain intact. CR-01 remains resolved.

**CR-02 remains active for categorical authority revocations, which advancing a
clock cannot preserve.** Suppose a newer generic epoch0 response has session
unknown after calendar permission revocation, with all action facts generic.
A later equal/older generic epoch0 reply can carry sessionopen with the prior
still-future close/review deadlines. The per-stock current-action ordering guard
does not apply. Even with the clock offset, those deadlines have not elapsed, so
the old sessionopen replaces the newer unknown authority. Similarly a cached
admissionunavailable can become old admissionapproved when refetch begins after
the denial: current===initial bypasses the current!==initial protection and
generic action states bypass timestamp ordering. The old required attribution
and independently authorized fields can then reappear.

Keep session/admission ordering/category high-water evidence as well as the clock,
or merge accepted old action-redaction envelopes with the latest independent
facts without promoting them. A newer genuine snapshot may recover; an older
generic action reduction must not restore newer revoked authority. Add newer
generic calendar/admission denial→equal/older generic open/approved regressions
with original deadlines still in the future. No new blocker beyond this remaining
CR-02 dimension was found; no tests/runtime operations were performed.

Frozen SHA-256 identities:

- api/stocks.ts: `3ec74a0f69a7b1cac338954fa18e2efc0dddc29d7a3127b4e902609a618d5e53`
- hooks/useStocks.ts: `b4ea5418725a3e6a203eb66e8c9187c5d13a6949552922effcf15bc825b80c11`

### Targeted re-review at `a289b40`

CR-01 is resolved: quote/session/reason coherence and exact ordered source times
are checked before cache publication; recent claims require the open compatible
regular session and exact age. The hook additionally refuses numeric display
under an unknown session. Dated stale/closed observations remain parseable.

CR-02 is partially resolved. All current-action replies now require a strictly
newer server observation, preventing transport reanchoring both before and after
local expiry. Generic/held replies intentionally bypass this check so they can
reduce action authority. However they can still promote independent session
authority, as detailed below. No reviewer tests or runtime operations occurred.

Frozen SHA-256 identities:

- api/stocks.ts: `c435a4d0c5737fb82be1bccf054207a47a634e54f3ee2e2406f09a2c11f6d5eb`
- hooks/useStocks.ts: `fae6d3394eeaa581909d90013bd7206fbd7a22271a46a41f86c2643131b075d8`

**Remaining CR-02 scenario:** After a cached open session crosses closes_at and
is locally closed, an equal/older generic epoch0 response can carry quoteNULL,
actionunknown, but independently sessionopen and admissionapproved. It bypasses
the per-item ordering condition because its action is not current. Its new
received_at resets elapsed; purgeExpired evaluates against the earlier server
time and installs the session as open again. A safety-reducing action envelope
does not make its other dimensions safe to promote. Keep the prior conservative
session/admission/transport boundary when accepting old redactions, or merge the
independent facts only toward reduced authority. Add a close→old generic/held
reply regression for both cache and rendered session, while retaining generic
redaction of a higher cached action epoch.

Reviewed strict response parsing, exact UTC ordering, full-RTT projection,
authenticated lifecycle/cache guard and nearest-deadline purge against Plan10,
the approved UI contract and backend schema. No reviewer tests, database/provider
calls, runtime/source edits or commits were performed. Executor tests and active
test-only coverage work remain separate evidence.

Frozen runtime SHA-256 identities:

- frontend/src/api/stocks.ts: `f080188248e1c27091d0eba7aceee8e12d9b4fcf5d2c7608a3fc6d560421a637`
- frontend/src/hooks/useStocks.ts: `dab1eab4cbd7221840fd27044e8a10e0e707caceae15e4f17d42277fdbf0e71e`

### CR-01 — BLOCKER, RESOLVED: Strict parser admits contradictory quote/session authority

**File:** `/home/YokaiExchange/frontend/src/api/stocks.ts:207`

**Issue:** Field validation and action/valuation coherence do not establish
quote/session/reason/source-time coherence. A current action with numeric quote
can carry an unknown session with a future valid_until; `projectStocks` then
considers it reviewed and can display numbers. Quotes with `missing` or
`permission_unavailable` reasons also enter the validated cache. Source timestamps
are not ordered against receipt/server time, and a closed session can claim a
recent quote. These envelopes contradict backend authority and the promised
atomic malformed-response rejection.

**Fix:** Validate the complete backend-compatible relationships: no quote for an
unknown session or a missing/permission-denied quote reason; quote source time
must not exceed collected_at, which must not exceed server_now; recent claims
require an open compatible session and exact source-age freshness. Keep dated
permitted last quotes distinct from recent claims. Use exact validated instants
for sub-millisecond comparisons, and add malformed-envelope regressions asserting
rejection before cache publication. Retain conservative hook redaction as defense
in depth.

### CR-02 — BLOCKER, RESOLVED: Same-envelope transport reanchoring restores locally consumed authority

**File:** `/home/YokaiExchange/frontend/src/hooks/useStocks.ts:188`

**Also affected:** response ordering near lines295–325.

**Issue:** Per-stock high-water marks remember only epoch, server time and
whether action.state is noncurrent. Source-age expiry can purge the quote while
action stays current; crossing session close likewise leaves action current.
An equal-epoch/equal-server-time response is then accepted because mark.held is
false. Its new received_at restarts elapsed timing and can restore the expired
quote or reopen the locally closed session using the identical earlier server
authority. The browser has promoted consumed authority without a newer server
observation. The executor independently identified the same issue while preparing
behavioral regressions; this review confirms the source path.

**Fix:** Preserve the conservative transport/authority high-water boundary across
equal or older server observations, covering quote age, session close/review,
admission and action deadlines rather than action.state alone. Merge only in the
direction of reduced authority for equal observations, or retain the earlier
transport anchor so refetch cannot reset elapsed time. Keep generic epoch0
redaction capable of reducing higher cached epochs while retaining their epoch
high-water mark. Add exact source-age/session-close cache and view regressions
for repeated equal replies, plus genuinely newer allowed recovery.
