import { defineConfig } from "vitest/config";
// Kit wrappers spawn Python fixtures (each run bounded by its own spawnSync
// timeout); 5 s per test is too tight on a loaded machine.
export default defineConfig({
  test: {
    include: ["tests/**/*.test.{ts,mjs}"],
    fileParallelism: false,
    testTimeout: 60000,
  },
});
