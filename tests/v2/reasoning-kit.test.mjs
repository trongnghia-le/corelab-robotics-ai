import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { findPython } from "../../scripts/runtime.mjs";

it("checks the manual belief-and-reasoning kit against alternative implementations, its sample manifest and named bugs", () => {
  const python = findPython();
  const result = spawnSync(
    python.executable,
    ["-I", "-B", "tests/fixtures/reasoning_kit.py"],
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
    "7 valid alternatives accepted, 80 injected bugs rejected",
  );
});
