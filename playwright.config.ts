import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3217",
    trace: "retain-on-failure",
    permissions: ["clipboard-read", "clipboard-write"],
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run start -- --port 3217",
    url: "http://127.0.0.1:3217",
    reuseExistingServer: false,
    timeout: 60000,
    env: {
      CORELAB_DB_PATH: `.local/e2e-${Date.now()}.sqlite`,
      NEXT_TELEMETRY_DISABLED: "1",
    },
  },
});
