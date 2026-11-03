import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  root: "frontend",
  base: "/townlight_code/app/",
  build: {
    outDir: "../townlight_code/frontend_dist",
    emptyOutDir: true
  },
  server: {
    port: 5174
  }
});
