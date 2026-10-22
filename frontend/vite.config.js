import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server on :3000 (the origin the backend's CORS allows).
// /api is proxied to FastAPI, so no CORS or base-URL setup is needed.
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, proxy: { "/api": "http://127.0.0.1:8000" } },
});
