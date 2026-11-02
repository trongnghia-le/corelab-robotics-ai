import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { findPython } from "../../scripts/runtime.mjs";

it("checks the manual odometry kit against alternative exact integrators, high-precision fixtures and named bugs", () => {
  const python = findPython();
  const result = spawnSync(
    python.executable,
    ["-I", "-B", "tests/fixtures/odometry_kit.py"],
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
    "2 valid alternatives accepted, 18 injected bugs rejected",
  );
});
