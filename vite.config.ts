import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  root: "frontend",
  base: "/civiccode/app/",
  build: {
    outDir: "../civiccode/frontend_dist",
    emptyOutDir: true
  },
  server: {
    port: 5174
  }
});
