import { afterEach, expect, it, vi } from "vitest";
import { mkdtempSync, rmSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { Store } from "../../lib/storage";
import {
  initialize,
  status,
  meta,
  write,
  checkpoint,
  needsAcknowledgement,
  learningData,
  nextSequence,
} from "../../lib/v2/db";
const stores: Store[] = [];
const dirs: string[] = [];
function fresh(file = false) {
  const dir = mkdtempSync(path.join(tmpdir(), "corelab v2 é-"));
  dirs.push(dir);
  const s = new Store(file ? path.join(dir, "data.sqlite") : ":memory:");
  stores.push(s);
  return s;
}
afterEach(() => {
  for (const s of stores.splice(0)) s.close();
  for (const dir of dirs.splice(0))
    rmSync(dir, { recursive: true, force: true });
  vi.unstubAllEnvs();
});
it("creates additive tables and a verified WAL copy without changing legacy state", () => {
  const s = fresh(true),
    before = s.export();
  initialize(s.db);
  expect(status(s.db)).toBe("supported");
  expect(s.read()).toEqual(before.progress);
  expect(s.db.prepare("PRAGMA user_version").get()).toEqual({
    user_version: 2,
  });
  expect(readdirSync(path.join(dirs[0], "v2-recovery"))).toHaveLength(1);
  expect(meta(s.db, "next_event_seq")).toBe("1");
});
it("rolls back metadata and rows together and rejects unsupported schema", () => {
  const s = fresh();
  initialize(s.db);
  const data = learningData(s.db);
  expect(() =>
    write(s.db, () => {
      nextSequence(s.db);
      throw Error("fail");
    }),
  ).toThrow("fail");
  expect(meta(s.db, "next_event_seq")).toBe("1");
  expect(learningData(s.db)).toEqual(data);
  s.db
    .prepare("UPDATE v2_meta SET value='9' WHERE key='sidecar_schema_version'")
    .run();
  expect(() => write(s.db, () => {})).toThrow("Unsupported");
});
it("does not initialize sidecar while the feature is off", () => {
  vi.stubEnv("CORELAB_V2", "0");
  const s = fresh();
  s.update((p) => {
    p.goal = "Robotics";
  });
  expect(status(s.db)).toBe("absent");
});
it("updates checkpoint in the legacy transaction, tracks outside edits and guards old restore", () => {
  const s = fresh();
  initialize(s.db);
  vi.stubEnv("CORELAB_V2", "1");
  s.update((p) => {
    p.goal = "Robotics";
  });
  expect(meta(s.db, "legacy_state_hash")).toBe(checkpoint(s.db).hash);
  const backup = s.export();
  expect(() => s.restore(backup, true)).toThrow("V2 backup");
  vi.stubEnv("CORELAB_V2", "0");
  s.update((p) => {
    p.goal = "Foundations";
  });
  expect(needsAcknowledgement(s.db)).toBe(true);
  vi.stubEnv("CORELAB_V2", "1");
  s.update((p) => {
    p.focusReason = "Returning";
  });
  expect(needsAcknowledgement(s.db)).toBe(true);
  expect(() => write(s.db, () => {})).toThrow("Acknowledge");
});
