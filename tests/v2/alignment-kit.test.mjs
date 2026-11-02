import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { findPython } from "../../scripts/runtime.mjs";

it("checks the manual visual alignment kit against alternative formulations, its sample manifest and named bugs", () => {
  const python = findPython();
  const result = spawnSync(
    python.executable,
    ["-I", "-B", "tests/fixtures/alignment_kit.py"],
    {
      encoding: "utf8",
      timeout: 15000,
      shell: false,
      windowsHide: true,
    },
  );
  expect(result.error).toBeUndefined();
  expect(result.status, result.stdout + result.stderr).toBe(0);
  expect(result.stdout).toContain(
    "10 valid alternatives accepted, 85 injected bugs rejected",
  );
});
