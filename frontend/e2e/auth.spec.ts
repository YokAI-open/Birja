import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { expect, test } from "@playwright/test";

// frontend/e2e/ -> repo root, where docker-compose.yml lives.
const repoRoot = fileURLToPath(new URL("../../", import.meta.url));

const escapeRegExp = (value: string) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/**
 * Dev email backend prints "DEV EMAIL to=<email> code=<6 digits>" to the backend log.
 * Reading it with a fixed-argv docker call is the only retrieval path: no debug route exists.
 */
async function readCodeFromLogs(email: string): Promise<string> {
  const pattern = new RegExp(`DEV EMAIL to=${escapeRegExp(email)} code=(\\d{6})`, "g");
  const deadline = Date.now() + 20_000;
  while (Date.now() < deadline) {
    const logs = execFileSync(
      "docker",
      ["compose", "logs", "--no-color", "--since", "5m", "backend"],
      {
        cwd: repoRoot,
        encoding: "utf8",
      },
    );
    const last = [...logs.matchAll(pattern)].at(-1);
    if (last?.[1]) {
      return last[1];
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`No sign-in code found in backend logs for ${email}`);
}

test("a new user signs in with an emailed code", async ({ page }) => {
  const email = `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;

  await page.goto("/");
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Send code" }).click();

  const code = await readCodeFromLogs(email);
  await page.getByLabel("6-digit code").fill(code);
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page.getByText("$10,000.00")).toBeVisible();
  await expect(page.getByText(email)).toBeVisible();

  await page.reload();
  await expect(page.getByText("$10,000.00")).toBeVisible();
  await expect(page.getByRole("heading", { name: "System status" })).toBeVisible();
});
