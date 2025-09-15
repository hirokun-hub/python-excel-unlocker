// This file configures Playwright for end-to-end UI testing.
// For this project, it's set up for a minimal smoke test to ensure
// the main application page loads. More complex tests can be added later.
// It defines the test directory, timeouts, and browser configurations.

import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./__tests__/ui",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",
  use: {
    baseURL: "http://localhost:3000", // Assuming the dev server runs on 3000 for tests
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
  },
});
