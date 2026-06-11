import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://localhost:5173" },
  webServer: [
    {
      command: "cd .. && .venv\\Scripts\\python.exe -m uvicorn api.main:app --port 8000",
      port: 8000,
      reuseExistingServer: true,
    },
    {
      command: "npm run dev",
      port: 5173,
      reuseExistingServer: true,
    },
  ],
});
