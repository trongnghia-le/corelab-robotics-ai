import { afterEach, expect, it, vi } from "vitest";
import { Store } from "../../lib/storage";
import {
  initialize,
  learningData,
  meta,
  write,
  revisionToken,
  status,
} from "../../lib/v2/db";
import { exportBackup, preview, restore } from "../../lib/v2/backup";
import { issue, submit } from "../../lib/v2/attempts";
import { family } from "../../lib/v2/content";
const stores: Store[] = [];
function fresh() {
  const s = new Store(":memory:");
  stores.push(s);
  initialize(s.db);
  return s;
}
function restoreHere(s: Store, b = exportBackup(s)) {
  restore(s, b, { ...preview(s, b), confirm: true });
}
afterEach(() => {
  vi.restoreAllMocks();
  stores.splice(0).forEach((s) => s.close());
  vi.unstubAllEnvs();
});
it("preserves every existing epoch across repeated restores and creates one local epoch on the next real learning write", () => {
  const source = fresh(),
    target = fresh();
  issue(source, { purpose: "practice", source: "X11" });
  const b = exportBackup(source),
    existing = b.v2.historyEpochs;
  restoreHere(target, b);
  for (let i = 0; i < 6; i++) restoreHere(target);
  expect(learningData(target.db).v2_history_epochs).toEqual(existing);
  const pending = JSON.parse(meta(target.db, "pending_restore_epoch"));
  expect(pending).toMatchObject({
    reason: "full_restore",
    origin_workspace_id: meta(target.db, "workspace_id"),
  });
  expect(exportBackup(target).v2.historyEpochs).toEqual(existing);
  const opened = issue(target, { purpose: "practice", source: "X10" });
  const rows = learningData(target.db);
  expect(rows.v2_history_epochs).toHaveLength(existing.length + 1);
  expect(rows.v2_history_epochs.slice(0, existing.length)).toEqual(existing);
  expect(rows.v2_history_epochs.at(-1)).toMatchObject(pending);
  expect(rows.v2_attempts.find((a) => a.id === opened.id)?.history_epoch).toBe(
    rows.v2_history_epochs.at(-1)?.id,
  );
  expect(meta(target.db, "pending_restore_epoch")).toBe("");
});
it("does not allocate an epoch for an idempotent retry, no-op transaction or failed learning mutation", () => {
  const s = fresh(),
    opened = issue(s, { purpose: "practice", source: "XB1" });
  const item = family("XB1")!.items.find((i) => i.id === opened.item.id)!;
  const answers = Object.fromEntries(
    item.fields.map((f, i) => [
      String(i),
      f.kind === "choice" ? f.answer : Number(f.answer).toFixed(9),
    ]),
  );
  const submission = { answers, declaredAssistance: 0 };
  submit(s, opened.id, submission);
  restoreHere(s);
  const before = learningData(s.db),
    token = revisionToken(s.db),
    pending = meta(s.db, "pending_restore_epoch");
  submit(s, opened.id, submission);
  write(s.db, () => undefined);
  expect(() =>
    write(s.db, () => {
      throw new Error("failed learning mutation");
    }),
  ).toThrow("failed learning");
  expect(learningData(s.db)).toEqual(before);
  expect(revisionToken(s.db)).toBe(token);
  expect(meta(s.db, "pending_restore_epoch")).toBe(pending);
});
it("allocates a deferred epoch inside a legacy learning update and rolls both back on a failed pre-commit", () => {
  vi.stubEnv("CORELAB_V2", "1");
  const s = fresh();
  restoreHere(s);
  s.update((p) => {
    p.focusReason = "new learning context";
  });
  expect(learningData(s.db).v2_history_epochs).toHaveLength(2);
  expect(meta(s.db, "pending_restore_epoch")).toBe("");
  restoreHere(s);
  const before = learningData(s.db),
    pending = meta(s.db, "pending_restore_epoch");
  const prepare = s.db.prepare.bind(s.db);
  vi.spyOn(s.db, "prepare").mockImplementation((sql) => {
    if (sql.startsWith("SELECT coalesce(sum(length"))
      throw new Error("capacity read failed");
    return prepare(sql);
  });
  expect(() =>
    s.update((p) => {
      p.focusReason = "must roll back";
    }),
  ).toThrow("capacity read failed");
  expect(learningData(s.db)).toEqual(before);
  expect(meta(s.db, "pending_restore_epoch")).toBe(pending);
  expect(s.read().focusReason).toBe("new learning context");
});
it("fails closed on malformed local pending provenance without changing retained history", () => {
  const s = fresh();
  restoreHere(s);
  const original = meta(s.db, "pending_restore_epoch");
  const before = learningData(s.db);
  for (const invalid of [
    "{}",
    '{"reason":"full_restore","reason":"legacy_restore"}',
    JSON.stringify({
      ...JSON.parse(original),
      origin_workspace_id: "00000000-0000-4000-8000-000000000000",
    }),
  ]) {
    s.db
      .prepare("UPDATE v2_meta SET value=? WHERE key='pending_restore_epoch'")
      .run(invalid);
    expect(status(s.db)).toBe("unsupported");
    expect(() => issue(s, { purpose: "practice", source: "X11" })).toThrow(
      "Unsupported",
    );
    expect(learningData(s.db)).toEqual(before);
  }
  s.db
    .prepare("UPDATE v2_meta SET value=? WHERE key='pending_restore_epoch'")
    .run(original);
  expect(status(s.db)).toBe("supported");
});
