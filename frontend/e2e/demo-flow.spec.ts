import { test, expect } from "@playwright/test";

/**
 * Critical end-to-end flow: login -> dashboard -> simulation -> what-if.
 * Mirrors the SIH demo workflow described in the project README.
 */

test("operator can log in and see the command-center dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByPlaceholder("operator@polar-ems.demo").fill("operator@polar-ems.demo");
  await page.getByPlaceholder("••••••••").fill("operator123");
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByText("Command Center")).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("heading", { name: "Active Alerts" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "AI Recommendations" })).toBeVisible();
});

test("simulation mode: activating a scenario recalculates the station state", async ({ page }) => {
  await page.goto("/login");
  await page.getByPlaceholder("operator@polar-ems.demo").fill("operator@polar-ems.demo");
  await page.getByPlaceholder("••••••••").fill("operator123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  await page.goto("/simulation");
  await expect(page.getByText("Solar Generation Drop")).toBeVisible({ timeout: 15000 });

  const card = page.locator("div", { hasText: "Solar Generation Drop" }).last();
  await page.getByRole("button", { name: "Activate" }).first().click();

  await expect(page.getByText("Recalculated State")).toBeVisible({ timeout: 15000 });
  await expect(page.getByText("AI Recommendations Under This Scenario")).toBeVisible();
});

test("what-if analysis produces a baseline comparison", async ({ page }) => {
  await page.goto("/login");
  await page.getByPlaceholder("operator@polar-ems.demo").fill("operator@polar-ems.demo");
  await page.getByPlaceholder("••••••••").fill("operator123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  await page.goto("/whatif");
  await page.getByRole("button", { name: /Run What-If Analysis/ }).click();
  await expect(page.getByText("Baseline vs. What-If")).toBeVisible({ timeout: 15000 });
});

test("battery, generator, and loads pages load real backend data", async ({ page }) => {
  await page.goto("/login");
  await page.getByPlaceholder("operator@polar-ems.demo").fill("admin@polar-ems.demo");
  await page.getByPlaceholder("••••••••").fill("admin123");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/dashboard/);

  await page.goto("/battery");
  await expect(page.getByRole("heading", { name: /Battery Management/ })).toBeVisible({ timeout: 15000 });

  await page.goto("/generator");
  await expect(page.getByRole("heading", { name: "Baseline vs. AI-Optimized Dispatch" })).toBeVisible({ timeout: 15000 });

  await page.goto("/loads");
  await expect(page.getByRole("heading", { name: "Priority 1 — Critical" })).toBeVisible({ timeout: 15000 });
});
