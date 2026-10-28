import { expect, test } from "@playwright/test";
import { signInNewUser } from "./helpers.js";

test("shows the backend, database and Redis as connected", async ({ page }) => {
  await signInNewUser(page);
  await page.goto("/account");
  await expect(page.getByRole("heading", { name: "System status" })).toBeVisible();

  const services = page.getByRole("list", { name: "Service status" });
  for (const name of ["API", "Database", "Redis"]) {
    await expect(services.getByRole("listitem").filter({ hasText: name })).toContainText(
      "Connected",
      { timeout: 15_000 },
    );
  }
});
