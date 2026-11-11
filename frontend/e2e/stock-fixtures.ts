export const symbols = [
  "AAPL",
  "MSFT",
  "NVDA",
  "AMZN",
  "GOOGL",
  "META",
  "TSLA",
  "AVGO",
  "AMD",
  "COST",
  "JPM",
  "V",
  "JNJ",
  "PG",
  "KO",
  "XOM",
  "CVX",
  "HD",
  "MCD",
  "DIS",
];
export function stocks({
  state = "approved",
  generation = 1,
  age = 10,
  lifetime = 3600,
  now = "2026-11-10T15:00:00Z",
  close = "2026-11-10T21:00:00Z",
  open = "2026-11-10T14:30:00Z",
}: {
  state?: "approved" | "unavailable";
  generation?: number;
  age?: number;
  lifetime?: number;
  now?: string;
  close?: string;
  open?: string;
} = {}) {
  const stamp = (seconds: number) => new Date(Date.parse(now) + seconds * 1000).toISOString();
  return {
    server_now: now,
    admission: {
      state,
      generation: state === "approved" ? generation : null,
      valid_until: state === "approved" ? stamp(lifetime) : null,
    },
    attribution: {
      label: "IEX prices",
      explanation: "Single venue",
      required_text: "Fixture provider attribution",
    },
    items: symbols.map((symbol, i) => ({
      id: i + 16,
      symbol,
      company_name:
        i === 0
          ? "Apple Inc. Long Company Name for Responsive Layout Verification"
          : "Company " + symbol,
      listing_exchange: i < 10 ? "NASDAQ" : "NYSE",
      currency: "USD",
      quote:
        state === "approved"
          ? {
              bid: "100.00000000",
              ask: "102.00000000",
              mid: "101.00000000",
              event_at: stamp(-age),
              collected_at: stamp(-1),
              source: "alpaca",
              feed: "iex",
              age_seconds: Math.floor(age),
            }
          : null,
      session: {
        state: "open",
        opens_at: open as string | null,
        closes_at: close as string | null,
        next_open_at: null,
        valid_until: stamp(lifetime) as string | null,
        timezone: "America/New_York",
      },
      status: { state: "unknown", observed_at: null, valid_until: null },
      action: (state === "approved"
        ? {
            state: "current",
            reason: "none",
            epoch: 1,
            checked_at: stamp(-1),
            valid_until: stamp(lifetime),
          }
        : {
            state: "unknown",
            reason: "monitor_unavailable",
            epoch: 0,
            checked_at: null,
            valid_until: null,
          }) as {
        state: string;
        reason: string;
        epoch: number;
        checked_at: string | null;
        valid_until: string | null;
      },
      valuation_reason: state === "approved" ? "available" : "action_unavailable",
      execution_enabled: false,
      execution_reason: "phase_disabled",
      quote_reason: state === "approved" ? "recent" : "permission_unavailable",
      session_reason: "open",
      status_reason: "unknown",
    })),
  };
}
