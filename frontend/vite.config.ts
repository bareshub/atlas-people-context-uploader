import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, proxy API calls to the FastAPI backend so the frontend can use
// same-origin "/api/..." paths (matching the nginx setup used in production).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
