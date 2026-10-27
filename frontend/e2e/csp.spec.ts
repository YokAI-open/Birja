import { expect, test } from "@playwright/test";

// Runs only against a deployed site: E2E_PROD_URL=https://birja.nist.one npx playwright test e2e/csp.spec.ts
// E2E_HOST_RESOLVER_RULES (e.g. "MAP birja.nist.one 127.0.0.1") lets a loopback rehearsal reach the origin.
const prodUrl = process.env.E2E_PROD_URL;
const resolverRules = process.env.E2E_HOST_RESOLVER_RULES;

if (resolverRules) {
  test.use({ launchOptions: { args: ["--host-resolver-rules=" + resolverRules] } });
}

test("deployed site loads without CSP violations", async ({ page }) => {
  test.skip(!prodUrl, "set E2E_PROD_URL to check a deployed site");

  // Script strings: the e2e tsconfig has no DOM types.
  await page.addInitScript(`
    window.__csp = [];
    document.addEventListener("securitypolicyviolation", (event) => {
      window.__csp.push(event.violatedDirective + " " + event.blockedURI);
    });
  `);

  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error" && message.text().includes("Content Security Policy")) {
      consoleErrors.push(message.text());
    }
  });

  const response = await page.goto(prodUrl as string);
  expect(response?.headers()["content-security-policy"]).toContain("default-src 'self'");

  await expect(page.getByRole("button", { name: "Send code" })).toBeVisible();
  // Typing only: the code is never requested, so no email is sent.
  await page.getByLabel("Email").fill("csp-check@example.com");
  await page.waitForLoadState("networkidle");

  const violations = (await page.evaluate("window.__csp || []")) as string[];
  expect({ violations, consoleErrors }).toEqual({ violations: [], consoleErrors: [] });
});
