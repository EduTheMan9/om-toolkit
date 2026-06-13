import { defineConfig } from "@playwright/test";

// Local Windows dev uses the project venv's python; CI (Linux) sets
// PYTHON=python after pip-installing the backend onto the runner's PATH.
const PYTHON = process.env.PYTHON ?? ".venv\\Scripts\\python.exe";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://localhost:5173" },
  webServer: [
    {
      command: `cd .. && ${PYTHON} -m uvicorn api.main:app --port 8000`,
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
