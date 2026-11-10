import { defineConfig } from "vite";

export default defineConfig({
  build: {
    outDir: "web-dist",
    rollupOptions: {
      input: "astroclock.html",
    },
  },
});