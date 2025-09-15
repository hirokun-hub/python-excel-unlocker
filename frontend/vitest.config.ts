// This file configures the Vitest test runner for the frontend.
// It integrates with Vite, sets up the React plugin, defines the test
// environment (JSDOM to simulate a browser), and specifies the global
// setup file for tests (vitest.setup.ts). It also configures path
// aliases to match the application's tsconfig.json.

import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    exclude: ["**/node_modules/**", "**/dist/**", "**/__tests__/ui/**"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
