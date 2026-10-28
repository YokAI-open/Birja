import { expect, test } from "@playwright/test";
import { readCodeFromLogs, signInNewUser } from "./helpers.js";

test("a new user signs in, stays signed in, signs out and signs in again", async ({
  page,
  context,
}) => {
  const email = await signInNewUser(page);
  const code = await readCodeFromLogs(email);

  await expect(page.getByRole("heading", { name: "Markets" })).toBeVisible();
  await page.getByRole("link", { name: "Account" }).click();
  await expect(page.getByText("$10,000.00")).toBeVisible();
  await expect(page.getByText(email)).toBeVisible();

  await page.goto("/account");
  await expect(page.getByText("$10,000.00")).toBeVisible();
  await expect(page.getByRole("heading", { name: "System status" })).toBeVisible();

  // Access cookie gone: the app refreshes silently and stays signed in.
  await context.clearCookies({ name: "bj_access" });
  await page.goto("/account");
  await expect(page.getByText("$10,000.00")).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("button", { name: "Send code" })).toBeVisible();
  await page.goto("/account");
  await expect(page.getByRole("button", { name: "Send code" })).toBeVisible();

  // Signing in again never adds cash.
  await page.getByLabel("Email").fill(email);
  await page.getByRole("button", { name: "Send code" }).click();
  const code2 = await readCodeFromLogs(email, code);
  await page.getByLabel("6-digit code").fill(code2);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("$10,000.00")).toBeVisible();
});
