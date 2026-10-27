import { expect, test } from "@playwright/test";

test("shows the backend, database and Redis as connected", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "System status" })).toBeVisible();

  const services = page.getByRole("list", { name: "Service status" });
  for (const name of ["API", "Database", "Redis"]) {
    await expect(services.getByRole("listitem").filter({ hasText: name })).toContainText(
      "Connected",
      { timeout: 15_000 },
    );
  }
});
