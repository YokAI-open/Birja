# Phase 12 — owner-approved picomatch exception

The owner requested on 2026-11-17: “can you create an issue in gh for the future about this and continue without fixing it?”

Issue: https://github.com/YokAI-open/Birja/issues/35 (created). This supersedes the earlier requirement that every HIGH advisory must be resolved before Phase12 can close, for GHSA-fc5q-39xc-vjpf ONLY. It does not authorize a general audit bypass, another advisory exception, installing the rejected fork, publication or deployment.

Keep raw full npm audit output visible. Bind the exception to current manifest SHA256 73cd4f25fb329d7d0711321ee56dd9f07b25426eb9ddb69f3491396c2ccbdb59 and lock SHA256 1461d4f89e875a5b915278e9d39ba413608fa4ff816fab6be6b21e280db5475b. Review expires 2026-12-17 UTC. Reject critical findings, unrelated HIGH findings, invalid reports, broken/unrooted cause graphs and transport failures. Inherited HIGH entries qualify only through the exact accepted advisory; moderate reporting remains unchanged.

Risk assessment: current use is frontend development/build/test tooling; production serves compiled static files. No ordinary user-input path into the matcher was identified; no complete exploitability proof is claimed. Keep development tooling and glob/config inputs trusted. Reassess if exposure changes. This remains an unresolved vulnerability with accepted risk, not clean-audit remediation.

Plans29–31 are revised under this new authorization; previous no_candidate and rejected-fork evidence stays historical. Both owner UI/native200 results and original01–28 remain complete. No new packages or product UI are involved. The validation runner is explicitly in PORTFOLIO_PAYLOAD_V1; changing its audit command requires fresh complete seven-stage recovery at the qualified source. Preserve the old d9da271 archive and receipts, without relabelling them as a new run.
