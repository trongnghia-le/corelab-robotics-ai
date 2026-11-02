import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { findPython } from "../../scripts/runtime.mjs";

it("checks the manual replay-node kit against alternative nodes, shrinkers and test suites, its sample manifest and named bugs", () => {
  const python = findPython();
  for (const flags of [["-I", "-B"], ["-I", "-B", "-O"]]) {
    const result = spawnSync(
      python.executable,
      [...flags, "tests/fixtures/replay_kit.py"],
      {
        encoding: "utf8",
        timeout: 90000,
        shell: false,
        windowsHide: true,
      },
    );
    expect(result.error).toBeUndefined();
    expect(result.status, result.stdout + result.stderr).toBe(0);
    expect(result.stdout).toContain(
      "6 valid alternatives accepted, 74 injected bugs rejected",
    );
  }
}, 240000);
