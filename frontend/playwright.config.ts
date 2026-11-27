import { defineConfig, devices } from "@playwright/test";

// The Compose stack is started outside Playwright (locally and in CI), so no webServer block.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:5173",
    trace: "retain-on-failure",
    // Browser suites use local widget fixtures and do not contact TradingView.
    launchOptions: { args: ["--host-resolver-rules=MAP www.tradingview-widget.com ~NOTFOUND"] },
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
