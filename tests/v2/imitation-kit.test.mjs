import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { findPython } from "../../scripts/runtime.mjs";

it("checks the manual episode QA and imitation kit against alternative implementations, its sample manifest and named bugs", () => {
  const python = findPython();
  const result = spawnSync(
    python.executable,
    ["-I", "-B", "tests/fixtures/imitation_kit.py"],
    {
      encoding: "utf8",
      timeout: 30000,
      shell: false,
      windowsHide: true,
    },
  );
  expect(result.error).toBeUndefined();
  expect(result.status, result.stdout + result.stderr).toBe(0);
  expect(result.stdout).toContain(
    "6 valid alternatives accepted, 89 injected bugs rejected",
  );
});
