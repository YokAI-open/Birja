// Run only in ephemeral fake-price / console-email CI, never real-email dev/prod.
import { expect, test } from "@playwright/test";
import { signInNewUser } from "./helpers.js";

test("a new user opens their real cash-only portfolio from Markets", async ({ page }) => {
  await signInNewUser(page);
  await expect(page.getByRole("heading", { level: 1, name: "Markets" })).toBeVisible();
  await page.getByRole("link", { name: "Portfolio", exact: true }).click();
  await expect(page).toHaveURL((url) => url.pathname === "/portfolio");
  await expect(page.getByRole("heading", { level: 1, name: "Portfolio" })).toBeVisible();
  await expect(page.getByText("Compared with your $10,000.00 start")).toBeVisible();
  await expect(page.getByRole("region", { name: "Total portfolio value" })).toContainText(
    "$10,000.00",
  );
  await expect(page.getByRole("region", { name: "Cash" })).toContainText("$10,000.00");
  await expect(page.getByText("No market prices needed")).toBeVisible();
});
