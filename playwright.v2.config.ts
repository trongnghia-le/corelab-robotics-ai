import { defineConfig } from "@playwright/test";
import { tmpdir } from "node:os";
import path from "node:path";
import { randomUUID } from "node:crypto";
import base from "./playwright.config";
export default defineConfig({
  ...base,
  testMatch: "**/v2-*.spec.ts",
  testIgnore: [],
  use: { ...base.use, baseURL: "http://127.0.0.1:3218" },
  webServer: {
    command: "npm run start:v2 -- --port 3218",
    url: "http://127.0.0.1:3218",
    reuseExistingServer: false,
    timeout: 60000,
    env: {
      CORELAB_V2: "1",
      CORELAB_DB_PATH: path.join(
        tmpdir(),
        "corelab-v2-e2e-" + randomUUID() + ".sqlite",
      ),
      NEXT_TELEMETRY_DISABLED: "1",
    },
  },
});
