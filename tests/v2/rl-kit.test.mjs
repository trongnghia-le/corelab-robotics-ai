import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { findPython } from "../../scripts/runtime.mjs";

it("checks the manual RL experiment-core kit against alternative implementations, its sample manifest and named bugs", () => {
  const python = findPython();
  const result = spawnSync(
    python.executable,
    ["-I", "-B", "tests/fixtures/rl_kit.py"],
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
    "5 valid alternatives accepted, 92 injected bugs rejected",
  );
}, 30000);
