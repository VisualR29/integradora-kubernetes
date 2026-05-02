import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:3000", // <--- CAMBIA ESTO DE 8080 A 3000
        changeOrigin: true,
      },
    },
  },
});