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
111 CI and ops contracts. Hosted package installation and recovery are pending.
