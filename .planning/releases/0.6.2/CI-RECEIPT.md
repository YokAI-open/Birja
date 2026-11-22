# Hosted CI qualification

All six required checks passed at candidate `1a9f9e8caa2adca96e202aed176127fcd7291930`:
backend, frontend, image, e2e, ops and ci-pass.

Run: https://github.com/YokAI-open/Birja/actions/runs/45069245874

Backend:3,703 tests passed,122warnings,3493.04seconds. Overall coverage99%;
critical statements and branches100%. Python dependency audit found no known
vulnerabilities. Frontend, browser and five strict image policies pass under
the existing approved issue35 disposition, whose scope/expiry are unchanged.

The seven-stage operations job tested one actual independent recovery archive,
SHA256 `5c7d59ff9b56db17e5e5860ed6fda1c20367b8b7914cb22ee2dadd6fada7e7e2`.
Formal profile verification and all51current payload comparisons pass. The
same bytes were independently downloaded from the published release and verified.
No rebuilt local archive is substituted for that qualification.
