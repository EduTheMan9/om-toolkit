/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { configDefaults } from "vitest/config";

// Dev runs two servers: Vite (5173) proxies /api to uvicorn (8000),
// so the frontend code can always fetch("/api/...") in dev and prod alike.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
  test: {
    // e2e/ is Playwright's territory; vitest would otherwise match *.spec.ts
    exclude: [...configDefaults.exclude, "e2e/**"],
  },
});
