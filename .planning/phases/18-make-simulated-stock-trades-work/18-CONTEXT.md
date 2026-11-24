# Phase 18 context — Make simulated stock trades work

<domain>
Prove an in-session simulated buy and sell with current prices for the existing
20-stock catalog. Catalog expansion begins in Phase 19. This phase uses local
and disposable infrastructure. Phase 21 owns production activation.
</domain>

<decisions>
- D-01. Use on-demand IEX bid/ask data. Keep the source-time limit under 120 seconds and the approved regular session, whole-share quantities, zero stock commission and selected portfolio rules.
- D-02. Use fresh IEX quotes and block halts reported by an official exchange source. The owner accepted that reports can lag or omit a halt, including a market-wide halt. Keep the existing refusal on stale or failed required checks.
- D-03. Use the existing free-account and public-source route. Keep applicable provider use in scope. The owner chose to proceed without contacting Alpaca.
- D-04. Prove a genuine app buy and sell with live prices in a disposable portfolio. Preserve live crypto behavior, exact cash and holdings, repricing, immutable retry receipts, History and existing corporate-action guards.
</decisions>

These decisions come from the v1.4 scope and roadmap approved on November 24,
2026. See [requirements](../../REQUIREMENTS.md), [milestone research](../../research/v1.4/SUMMARY.md)
and the [previous live observations](../../quick/20261124-stock-activation/SUMMARY.md).
