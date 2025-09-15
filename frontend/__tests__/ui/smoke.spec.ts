// This is a basic smoke test for the UI, using Playwright.
// It verifies that the main page of the application loads correctly
// and that the title is as expected. This ensures the Next.js server
// can start and render the initial page without errors.

import { test, expect } from "@playwright/test";

test("has title", async ({ page }) => {
  await page.goto("/");

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Excel Password Remover/);
});
