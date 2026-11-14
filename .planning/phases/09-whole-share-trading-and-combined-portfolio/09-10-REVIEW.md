# Plan09-10 review

Separate inline source/threat pass; agents were unavailable with filesystem
capability, so no independent review is claimed. Exact client validators reject
numeric/exponent money, malformed arithmetic/identity/source/time/authority and
unsafe success bodies. Bounded BigInt arithmetic validates server results; it
does not create client financial accounting. Error ambiguity preserves attempts.

Checked immutable receipt replay without current market gates; no automatic
mutation retry, same frozen key/body after unknown, synchronous duplicate-submit
barrier, explicit repricing confirmation and shared-query invalidation. Pending
attempts cannot be edited/abandoned for a new key. Auth lifecycle and query-owner
barriers discard late replies; expiry removes view and cached estimates.

Resolved two observed review regressions in4332c45/11bad97: replaced context
owner left loading forever; changed provider identity retained the old positive
context. Both now preserve draft quantity and remove confirmation/unsafe prices.
20 controller tests plus227 client/discovery tests pass. No open blocker in this
scoped pass. Whole-phase critical coverage and browser review remain14.
