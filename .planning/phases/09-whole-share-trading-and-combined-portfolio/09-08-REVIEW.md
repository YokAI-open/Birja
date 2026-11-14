# Plan09-08 review

Distinct inline source/security pass; agents lacked tools, so no independence
claimed. Scope: actual API router wiring, new private stock routes, saved receipt
refresh and actual HTTP tests; consulted auth/CSRF, schemas and financial service.

Resolved R08-01: new receipt Decimal scales differed from stored replay JSON.
Actual deep HTTP equality failed.77a4001 refreshes BOTH immutable stored objects
before receipt construction, deferred constraints and final authority. No await
was added after final guard. Exact HTTP equality passes, including later split.

Confirmed current-user only, CSRF on both POSTs, bounded schema inputs and path,
private no-store/Vary across errors and success, fixed code/status mapping and
string decimals/IDs. Generic response failure preserves uncertain outcome and
original-key recovery without raw exception details. Actual committed service
is exercised in the fault test. Crypto service math and API remain unchanged.
Main already mounts api_router; adding the child router there is the actual
registration seam, not an omitted main implementation.

No open blocker/high. Final224tests58.92s and additional split1test2.08s; all three
critical consumers253statements/50branches100%; scoped static gates pass.
Frontend, portfolio and complete recovered/security/browser proof remain09–15.
No provider/production/publication change or activation permission inferred.
