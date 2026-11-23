---
status: verifying
updated: 2026-11-23
---

# PR 41 Hosted Qualification

Hosted CI run 45160029262 tested PR head 5993ae4. Backend, frontend and image
checks passed. Chromium reported 92 passes, one deployed-only CSP skip and
one failure in the real crypto round trip. The ops job timed out during
`apt-get update` before Docker installation or recovery checks.

## Browser Back

The final test waited for the header's Sign out button after clicking
Portfolios. That control already existed on History. An immediate Back could
take place before React committed Portfolios, leaving focus on the navigation
link. The original sequence reproduced this 23 times in 40 local Chromium
trials. Waiting for the intermediate heading to receive focus passed 40
committed Back transitions. The real isolated round trip then passed with the
corrected wait and all original economic and focus assertions.

## Ops setup

Runner-provided mirror requests did not finish before the job limit. The
Docker setup now uses an explicit list of signed HTTPS Ubuntu and Docker
sources, bounded package retries and an 8-minute step timeout. It keeps the
Docker and Compose pins, platform preflight and the complete recovery suite.
Its Bash syntax and APT source selection passed local checks, along with all
111 CI and ops contracts. The hosted ops job passed in 34 minutes 38 seconds
on run 45169702553, including package installation, Docker platform
verification, PostgreSQL recovery, TLS, old-image rollback and staging the
verified recovery tooling.

## Markets keyboard activation

Run 45169702553 passed the real History Back check and reported four failures
opening the BTC trade ticket from Markets at a narrow effective viewport.
The tests set focus on the trade link while the asset-selection focus callback
could still be pending. Local Chromium reproduced lost activation in six of
six trials when the callback ran between focusing the link and pressing Enter.
Waiting for the Bitcoin heading to receive focus passed all six corrected trials.
The affected tests now wait for that heading on narrow viewports and assert
focus on the trade link before pressing Enter. Application code is unchanged.
All nine catalogue and corporate-action cases passed against the isolated
stack in 47 seconds, including the zoom case. Cleanup, TypeScript, ESLint and
touched-file formatting checks passed.
The complete isolated Chromium suite then passed all 93 runnable scenarios
in 18.2 minutes, with one expected deployed-only CSP skip and clean teardown.
The local suite log is at
`/tmp/birja-phase09-browser-ba0j1zsi/browser-all.log`.
