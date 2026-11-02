import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { findPython } from "../../scripts/runtime.mjs";

it("checks the manual executive and watchdog kit against alternative formulations, its sample manifest and named bugs", () => {
  const python = findPython();
  for (const flags of [["-I", "-B"], ["-I", "-B", "-O"]]) {
    const result = spawnSync(
      python.executable,
      [...flags, "tests/fixtures/executive_kit.py"],
      {
        encoding: "utf8",
        timeout: 60000,
        shell: false,
        windowsHide: true,
      },
    );
    expect(result.error).toBeUndefined();
    expect(result.status, result.stdout + result.stderr).toBe(0);
    expect(result.stdout).toContain(
      "7 valid alternatives accepted, 108 injected bugs rejected",
    );
  }
}, 150000);
