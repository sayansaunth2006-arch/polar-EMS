import { test } from "@playwright/test";

test("capture dashboard screenshot", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/login");
  await page.getByPlaceholder("operator@polar-ems.demo").fill("operator@polar-ems.demo");
  await page.getByPlaceholder("••••••••").fill("operator123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await page.waitForURL(/\/dashboard/);
  await page.waitForTimeout(1200);
  await page.screenshot({ path: "/tmp/shots/final-dashboard.png", fullPage: true });
});
