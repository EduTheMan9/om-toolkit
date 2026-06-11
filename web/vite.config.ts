import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev runs two servers: Vite (5173) proxies /api to uvicorn (8000),
// so the frontend code can always fetch("/api/...") in dev and prod alike.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:8000" },
  },
});
