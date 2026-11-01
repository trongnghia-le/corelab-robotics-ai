import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { findPython } from "../../scripts/runtime.mjs";
it("accepts valid numerical alternatives and rejects malformed/mutated outputs in manual kit fixtures", () => {
  // Fixed author-owned fixture only; no learner code runs in the application.
  const python = findPython();
  const result = spawnSync(
    python.executable,
    ["-I", "-B", "tests/fixtures/manual_kits.py"],
    {
      encoding: "utf8",
      timeout: 10000,
      shell: false,
      windowsHide: true,
    },
  );
  expect(result.error).toBeUndefined();
  expect(result.status, result.stdout + result.stderr).toBe(0);
  expect(result.stdout).toContain("16 injected bugs rejected");
});
