import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Node global; declared locally to avoid adding @types/node.
declare const process: { env: Record<string, string | undefined> };
export default defineConfig({
  plugins: [react()],
  server: {
    // API_URL lets a second local API (another port) back this dev server.
    proxy: { "/api": process.env.API_URL ?? "http://127.0.0.1:8008" },
    strictPort: true,
  },
});
