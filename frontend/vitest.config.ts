import path from "path"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    // must stay above the 5s asyncUtilTimeout in setup.ts: a single slow waitFor would
    // otherwise consume the whole default 5s test budget and time out the test instead
    // of failing its assertion.
    testTimeout: 20000,
  },
})
