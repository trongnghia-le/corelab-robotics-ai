import { expect, it } from "vitest";
import { spawnSync } from "node:child_process";
import { mkdtempSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { Store } from "../../lib/storage";
import { initialize, ensureHeadroom } from "../../lib/v2/db";
it("creates and reopens a current maintenance copy in a private path with spaces and Unicode", () => {
  const dir = mkdtempSync(path.join(tmpdir(), "corelab recovery é-")),
    file = path.join(dir, "progress.sqlite");
  const s = new Store(file);
  try {
    initialize(s.db);
    s.update((p) => {
      p.focusReason = "current recovery marker";
    });
    expect(() => ensureHeadroom(s.db, Number.MAX_SAFE_INTEGER)).toThrow(
      "Insufficient free disk",
    );
  } finally {
    s.close();
  }
  try {
    const run = spawnSync(
      process.execPath,
      [
        "--import",
        "tsx",
        "scripts/recovery-v2.ts",
        "--db",
        file,
        "--server-stopped",
      ],
      { encoding: "utf8", timeout: 15000, shell: false, windowsHide: true },
    );
    expect(run.status, run.stderr).toBe(0);
    const names = readdirSync(path.join(dir, "v2-recovery"));
    expect(names).toHaveLength(2);
    const copy = run.stdout
      .split("Verified current SQLite recovery copy: ")[1]
      .split(/\r?\n/)[0];
    const reopened = new Store(copy);
    try {
      expect(reopened.read().focusReason).toBe("current recovery marker");
    } finally {
      reopened.close();
    }
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});
